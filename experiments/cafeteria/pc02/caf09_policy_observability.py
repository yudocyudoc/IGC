#!/usr/bin/env python3
"""CAF-09: isolate the effect of CAF-07B's second-measurement policy.

The DES, observation operators, candidate physical banks, uncertainty band,
first measurement, budget and final decision rule are not modified.
Known CAF-07B worlds -> retrospective exploratory contrasts ONLY.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import caf07b_umbral_secuencial as b


SCHEMA = "igc-caf09-policy-observability-ablation/0.1"
POLICIES = ("STRICT_ORIGINAL", "ANY_GUARANTEED", "PAIRWISE_ANY")
BANKS = ("single_only", "single_plus_dual")
GATE = "BLOCKED_RETROSPECTIVE_KNOWN_WORLDS"


def verify(condition, code):
    if not condition:
        raise ValueError(code)


def cross_class_pairs(bank_rows, predictions, survivors, action_id):
    """Number of cross-class hypothesis pairs with nonoverlapping +/-1 bands.

    A separated pair does not imply either hypothesis is isolated from *all*
    alternatives. This is a structural property of the bank prediction
    table, NOT an estimate of probability or information gain.
    """
    labels = {row["id"]: row["decision_class"] for row in bank_rows}
    num = 0
    for i, a in enumerate(survivors):
        for c in survivors[i + 1:]:
            if labels[a] == labels[c]:
                continue
            x, y = predictions[a][action_id], predictions[c][action_id]
            verify(len(x) == len(y) > 0, "CAF09_CHANNEL_MISMATCH")
            if any(abs(v - w) > b.DIVERGENCE_THRESHOLD
                   for v, w in zip(x, y)):
                num += 1
    return num


def candidate_scores(bank_rows, predictions, survivors):
    """All affordable unused second actions, pre-observation, no truth input."""
    left = b.BUDGET - b.FIRST["cost"]
    choices = []
    for action in b.ACTIONS:
        if action["id"] == b.FIRST_ACTION_ID or action["cost"] > left:
            continue
        guarantee = b.guarantee(
            bank_rows, predictions, survivors, (action["id"],))
        pairs = cross_class_pairs(
            bank_rows, predictions, survivors, action["id"])
        choices.append({
            "action_id": action["id"], "cost": action["cost"],
            "guaranteed_count": guarantee["total_guaranteed"],
            "all_classes_meet_minimum":
                guarantee["all_classes_meet_minimum"],
            "guaranteed_by_class": guarantee["by_class"],
            "separated_cross_class_pairs": pairs,
        })
    return choices


def choose_relaxed(bank_rows, predictions, survivors, policy):
    verify(policy in POLICIES[1:], "CAF09_INVALID_ALTERNATIVE_POLICY")
    labels = b.classes(bank_rows, survivors)
    if not survivors:
        return {"policy": policy, "status": b.MODEL_GAP,
                "action": None, "candidates": [],
                "reason": "NO_COMPATIBLE_HYPOTHESES"}
    if len(labels) == 1:
        return {"policy": policy, "status": "STOP_SINGLE_CLASS_WITHIN_BANK",
                "action": None, "candidates": [],
                "reason": "CLASS_ALREADY_UNIQUE_WITHIN_BANK"}

    candidates = candidate_scores(bank_rows, predictions, survivors)
    if policy == "ANY_GUARANTEED":
        permitted = [x for x in candidates if x["guaranteed_count"] > 0]
        rank = lambda x: (
            -x["guaranteed_count"],
            -x["separated_cross_class_pairs"],
            x["cost"], x["action_id"])
    else:
        permitted = [x for x in candidates
                     if x["separated_cross_class_pairs"] > 0]
        rank = lambda x: (
            -x["separated_cross_class_pairs"],
            x["cost"], x["action_id"])

    if not permitted:
        return {
            "policy": policy, "status": "NO_ELIGIBLE_PARTIAL_ACTION",
            "action": None, "candidates": candidates,
            "reason": "NO_ACTION_SATISFIES_THIS_EXPLORATORY_WEAK_RULE"}
    selected = min(permitted, key=rank)
    return {
        "policy": policy, "status": "PARTIAL_ACTION_SELECTED",
        "action": b.ACTION_BY_ID[selected["action_id"]],
        "candidates": candidates,
        "selected_score": selected,
        "reason": "EXPLORATORY_MEASUREMENT_NOT_A_DIAGNOSIS",
    }


def classify_evaluator(world, decision):
    """World truth enters ONLY after selection and any second observation."""
    diagnosis = decision["diagnosis_within_bank"]
    if diagnosis is None:
        return "MODEL_GAP" if decision["status"] == b.MODEL_GAP else "ABSTAIN"
    if diagnosis == world["truth_class"]:
        return "CORRECT_WITHIN_SIMULATED_WORLD"
    if world["truth_type"] in ("double", "unknown-extra") and "+" not in diagnosis:
        return "FALSE_SINGLE_DIAGNOSIS"
    return "WRONG_CLASS"


def normalized_legacy(legacy, bank_name):
    selection = legacy["selection_before_second"]
    return {
        "case": legacy["case"],
        "bank": bank_name,
        "policy": POLICIES[0],
        "world_type_EVALUATOR_ONLY": legacy["truth_type_EVALUATOR_ONLY"],
        "truth_class_EVALUATOR_ONLY": legacy["truth_class_EVALUATOR_ONLY"],
        "baseline": legacy["initial"],
        "first": legacy["first_observation"],
        "survivors_after_first": legacy["survivors_after_first"],
        "classes_after_first": selection["classes"],
        "second_action": selection["action"]["id"] if selection["action"] else None,
        "selection_status": selection["status"],
        "second_observation": legacy["second_observation"],
        "final_status": legacy["final"]["status"],
        "final_classes": legacy["final"]["classes"],
        "survivors_final": legacy["final"]["after"],
        "diagnosis": legacy["final"]["diagnosis_within_bank"],
        "verdict_EVALUATOR_ONLY": legacy["verdict_EVALUATOR_ONLY"],
        "cost_spent": legacy["cost_spent"],
    }


def evaluate_alt(world, bank_name, rows, prediction, policy, destination):
    """Decision selection never sees world.config/truth; evaluator runs DES."""
    baseline = b.read_physical(
        world["config"], b.caf07.T0_RATE, b.caf07.T0_MINUTE,
        (("delivered", None),))
    survivors0 = b.eligible(rows, prediction, {"baseline": baseline})
    first = b.read_physical(
        world["config"], b.FIRST["rate"], b.FIRST["minute"],
        b.FIRST["channels"])
    survivors = b.eligible(
        rows, prediction, {b.FIRST_ACTION_ID: first}, survivors0)

    # Only bank rows, candidate predictions and observed-survivor IDs flow
    # into the policy. The world.config was used solely by the physical reader.
    choice = choose_relaxed(rows, prediction, survivors, policy)
    b.lab.write_new(destination, (
        "01_CHOICE_" + world["id"] + "_" + bank_name + "_" + policy + ".json"), {
            "schema": SCHEMA, "case_id": world["id"],
            "bank": bank_name, "policy": policy,
            "baseline": baseline, "first": first,
            "survivors_after_first": survivors,
            "classes_after_first": b.classes(rows, survivors),
            "scores_before_K2": choice,
            "selected_next_measurement": choice["action"],
            "before_second_DES": True, "second_DES_calls_so_far": 0,
            "evaluator_truth_not_passed_to_selector": True,
        })

    measured = None
    cost = b.FIRST["cost"]
    if choice["action"] is not None:
        action = choice["action"]
        verify(cost + action["cost"] <= b.BUDGET,
               "CAF09_BUDGET_EXCEEDED")
        measured = b.read_physical(
            world["config"], action["rate"],
            action["minute"], action["channels"])
        decision = b.update(
            rows, prediction, survivors, action["id"], measured)
        cost += action["cost"]
    else:
        labels = b.classes(rows, survivors)
        status = (b.MODEL_GAP if not survivors else
                  "SINGLE_CLASS_WITHIN_BANK" if len(labels) == 1 else
                  b.THRESHOLD_FAIL)
        decision = {
            "status": status, "after": survivors,
            "classes": labels,
            "diagnosis_within_bank": labels[0] if len(labels) == 1 else None,
        }
    verdict = classify_evaluator(world, decision)
    return {
        "case": world["id"], "bank": bank_name, "policy": policy,
        "world_type_EVALUATOR_ONLY": world["truth_type"],
        "truth_class_EVALUATOR_ONLY": world["truth_class"],
        "baseline": baseline, "first": first,
        "survivors_after_first": survivors,
        "classes_after_first": b.classes(rows, survivors),
        "second_action": choice["action"]["id"] if choice["action"] else None,
        "selection_status": choice["status"],
        "second_observation": measured,
        "final_status": decision["status"],
        "final_classes": decision["classes"],
        "survivors_final": decision["after"],
        "diagnosis": decision["diagnosis_within_bank"],
        "verdict_EVALUATOR_ONLY": verdict,
        "cost_spent": cost,
    }


def structural_observability(rows, predictions, baseline, first):
    """Per-measurement observability report: NO physical-world truth passed."""
    survivors0 = b.eligible(rows, predictions, {"baseline": baseline})
    survivors = b.eligible(
        rows, predictions, {b.FIRST_ACTION_ID: first}, survivors0)
    labels = b.classes(rows, survivors)
    candidates = candidate_scores(rows, predictions, survivors)
    strict_candidates = [x for x in candidates if x["all_classes_meet_minimum"]]
    partial = [x for x in candidates if x["guaranteed_count"] > 0]
    pairwise = [x for x in candidates if x["separated_cross_class_pairs"] > 0]
    return {
        "surviving_hypotheses_after_K1": len(survivors),
        "surviving_classes_after_K1": len(labels),
        "classes": labels,
        "affordable_candidate_actions": len(candidates),
        "strict_eligible_actions": len(strict_candidates),
        "actions_isolating_at_least_one_hypothesis": len(partial),
        "actions_separating_at_least_one_cross_class_pair": len(pairwise),
        "maximum_isolatable_hypotheses": max(
            (x["guaranteed_count"] for x in candidates), default=0),
        "maximum_separable_cross_class_pairs": max(
            (x["separated_cross_class_pairs"] for x in candidates), default=0),
        "all_candidate_scores": candidates,
    }


def summarize(evaluations):
    group = {}
    for bank in BANKS:
        group[bank] = {}
        for policy in POLICIES:
            items = [x for x in evaluations
                     if x["bank"] == bank and x["policy"] == policy]
            counts = Counter(x["verdict_EVALUATOR_ONLY"] for x in items)
            group[bank][policy] = {
                "worlds": len(items),
                "correct": counts["CORRECT_WITHIN_SIMULATED_WORLD"],
                "false_single": counts["FALSE_SINGLE_DIAGNOSIS"],
                "wrong_class": counts["WRONG_CLASS"],
                "abstain": counts["ABSTAIN"],
                "model_gap": counts["MODEL_GAP"],
                "second_measurements": sum(x["second_action"] is not None
                                           for x in items),
                "reductions_in_survivor_count": sum(
                    len(x["survivors_final"]) < len(x["survivors_after_first"])
                    for x in items if x["second_action"] is not None),
                "reductions_in_class_count": sum(
                    len(x["final_classes"]) < len(x["classes_after_first"])
                    for x in items if x["second_action"] is not None),
                "by_physical_structure": {
                    typ: dict(Counter(
                        x["verdict_EVALUATOR_ONLY"] for x in items
                        if x["world_type_EVALUATOR_ONLY"] == typ))
                    for typ in ("single", "double", "unknown-extra")
                },
            }
    return group


def compare_to_strict(rows):
    pairs = []
    for bank in BANKS:
        for case in sorted({x["case"] for x in rows}):
            strict = next(x for x in rows
                          if x["bank"] == bank and x["case"] == case
                          and x["policy"] == "STRICT_ORIGINAL")
            for policy in POLICIES[1:]:
                other = next(x for x in rows
                             if x["bank"] == bank and x["case"] == case
                             and x["policy"] == policy)
                verify(other["baseline"] == strict["baseline"]
                       and other["first"] == strict["first"],
                       "CAF09_OBSERVATION_PARITY_FAILED")
                pairs.append({
                    "bank": bank, "case": case, "policy": policy,
                    "selected_when_strict_abstained":
                        strict["second_action"] is None and
                        other["second_action"] is not None,
                    "action_changed":
                        strict["second_action"] != other["second_action"],
                    "verdict_changed":
                        strict["verdict_EVALUATOR_ONLY"] !=
                        other["verdict_EVALUATOR_ONLY"],
                    "strict_verdict": strict["verdict_EVALUATOR_ONLY"],
                    "other_verdict": other["verdict_EVALUATOR_ONLY"],
                    "hypotheses_removed_by_second":
                        len(other["survivors_after_first"]) -
                        len(other["survivors_final"])
                        if other["second_action"] else 0,
                    "classes_removed_by_second":
                        len(other["classes_after_first"]) -
                        len(other["final_classes"])
                        if other["second_action"] else 0,
                })
    return pairs


def run(out, checkout_sha, head_sha):
    verify(isinstance(checkout_sha, str)
           and b.SOURCE_COMMIT_PATTERN.fullmatch(checkout_sha),
           "CAF09_BAD_CHECKOUT_SHA")
    verify(isinstance(head_sha, str)
           and b.SOURCE_COMMIT_PATTERN.fullmatch(head_sha),
           "CAF09_BAD_HEAD_SHA")
    destination = Path(out).resolve()
    verify(not destination.exists(), "CAF09_OUTPUT_EXISTS")
    rows_by_bank = {
        "single_only": b.bank(False),
        "single_plus_dual": b.bank(True),
    }
    preds = {name: b.precompute(rows)
             for name, rows in rows_by_bank.items()}
    worlds = b.scenarios()
    verify(len(worlds) == 11, "CAF09_WRONG_WORLD_COUNT")
    destination.mkdir(parents=True, exist_ok=False)

    frozen = {
        "schema": SCHEMA, "checkout_sha": checkout_sha,
        "pr_head_sha": head_sha,
        "synthetic_pr_merge_sha_may_differ_from_head": True,
        "worlds_EVALUATOR_ONLY": worlds,
        "banks": rows_by_bank, "predictions_precomputed": preds,
        "policies": list(POLICIES),
        "menu": list(b.ACTIONS),
        "first_action": b.FIRST, "tolerance_orders": b.TOLERANCE,
        "robust_cross_class_difference_strictly_greater_than":
            b.DIVERGENCE_THRESHOLD,
        "cumulative_budget": b.BUDGET,
        "retrospective_known_worlds": True,
        "physical_DES_not_modified": True,
        "selector_does_not_receive_world_truth": True,
    }
    b.lab.write_new(destination, "00_PLAN_PRE_EVALUACION.json", frozen)
    results = []
    obs = []
    for name in BANKS:
        for world in worlds:
            strict = b.evaluate_case(
                world, rows_by_bank[name], preds[name],
                name + "_STRICT_ORIGINAL", destination)
            standard = normalized_legacy(strict, name)
            results.append(standard)
            obs.append({
                "bank": name, "case": world["id"],
                **structural_observability(rows_by_bank[name], preds[name],
                                          standard["baseline"], standard["first"]),
            })
            for policy in POLICIES[1:]:
                item = evaluate_alt(
                    world, name, rows_by_bank[name], preds[name],
                    policy, destination)
                verify(item["baseline"] == standard["baseline"]
                       and item["first"] == standard["first"],
                       "CAF09_NONIDENTICAL_K0_K1")
                results.append(item)
    verify(len(results) == 66 and len(obs) == 22,
           "CAF09_WRONG_OUTPUT_COUNTS")
    pairs = compare_to_strict(results)
    verify(len(pairs) == 44, "CAF09_WRONG_PAIR_COUNT")
    metrics = summarize(results)
    outdata = {
        "schema": SCHEMA, "checkout_sha": checkout_sha,
        "pr_head_sha": head_sha,
        "known_worlds_no_blinding": True,
        "selector_alternatives_policy_only": True,
        "same_physical_sensors_first_read": True,
        "same_bank_DES_predictions": True,
        "same_final_within_bank_diagnosis_logic": True,
        "n_worlds": len(worlds), "n_observability_checks": len(obs),
        "n_policy_evaluations": len(results), "n_paired_differences": len(pairs),
        "metrics_by_bank_policy": metrics,
        "observability_per_world_bank": obs,
        "evaluations": results,
        "paired_differences": pairs,
        "promotion_gate": GATE, "deployment_validated": False,
        "causal_mechanism_identified": False,
    }
    b.lab.write_new(destination, "02_RESULTADOS.json", outdata)
    report = [
        "# CAF-09 — Resultado retrospectivo de política vs observabilidad",
        "",
        "**Sin promoción.** Todos los mundos son conocidos; igualdad de",
        "observables dentro de este menú no equivale a equivalencia física.",
        "",
        "## Diagnóstico y actividad",
        "",
        "| Banco | Política | Correctos | Falsos únicos | Otras clases erróneas | Abstenciones | MODEL_GAP | Segundas | Eliminan hipótesis | Eliminan clases |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for bank in BANKS:
        for policy in POLICIES:
            m = metrics[bank][policy]
            report.append("| " + " | ".join(map(str, (
                bank, policy, m["correct"], m["false_single"],
                m["wrong_class"], m["abstain"], m["model_gap"],
                m["second_measurements"],
                m["reductions_in_survivor_count"],
                m["reductions_in_class_count"],
            ))) + " |")
    report += [
        "", "## Bloqueo estructural en menú ampliado (K1)",
        "", "| Mundo | Hipótesis | Clases | Acciones estrictas | Acciones alguna hipótesis aislable | Acciones algún par separable | Máx. hipótesis aislables | Máx. pares separables |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for o in obs:
        if o["bank"] != "single_plus_dual":
            continue
        report.append("| " + " | ".join(map(str, (
            o["case"], o["surviving_hypotheses_after_K1"],
            o["surviving_classes_after_K1"],
            o["strict_eligible_actions"],
            o["actions_isolating_at_least_one_hypothesis"],
            o["actions_separating_at_least_one_cross_class_pair"],
            o["maximum_isolatable_hypotheses"],
            o["maximum_separable_cross_class_pairs"],
        ))) + " |")
    report += [
        "", "## Precaución epistemológica",
        "",
        "- Toda selección parcial es hipotética; no hay costos reales ni control fuera de banco.",
        "- Una acción que distingue algún par puede no aislar ninguna hipótesis/clase.",
        "- Un diagnóstico dentro de banco puede ser falso si falta el mecanismo real.",
        "- Las acciones son ensayos DES reiniciados; no son una sola trayectoria operativa.",
        "- Los observables ya disponibles no se enriquecen; no se modela servicio aleatorio.",
        "- La prueba de robustez a perturbaciones de modelos será otro PR, si se autoriza.",
        "",
        "**Promotion gate:** " + GATE,
        "",
    ]
    b.lab.write_new(destination, "03_INFORME.md", "\n".join(report))
    snapshots = sorted(
        p for p in destination.iterdir()
        if p.is_file())
    manifest = {
        "schema": SCHEMA, "checkout_sha": checkout_sha,
        "pr_head_sha": head_sha,
        "artifacts_written_before_second_measurement": True,
        "files_sha256": {
            f.name: "sha256:" + hashlib.sha256(f.read_bytes()).hexdigest()
            for f in snapshots
        },
        "retrospective_not_independently_validated": True,
    }
    b.lab.write_new(destination, "04_MANIFIESTO.json", manifest)
    return outdata


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--checkout-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    args = parser.parse_args()
    r = run(args.out, args.checkout_sha, args.head_sha)
    print(json.dumps({
        "policy_metrics": r["metrics_by_bank_policy"],
        "n_evaluations": r["n_policy_evaluations"],
        "promotion_gate": r["promotion_gate"],
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
