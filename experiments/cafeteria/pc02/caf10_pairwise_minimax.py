#!/usr/bin/env python3
"""CAF-10: frozen PAIRWISE_ANY vs exact integer-band minimax on new DES worlds.

Uses CAF-07B/CAF-09 functions and the native CAF-01 DES; never modifies them.
Exploratory retrospective historical singles + novel constructed duals.
"""
from __future__ import annotations

import argparse
from collections import Counter
from itertools import combinations, product
import hashlib
import json
from pathlib import Path

import caf07b_umbral_secuencial as b
import caf09_policy_observability as c9

SCHEMA = "igc-caf10-pairwise-minimax-expanded-bank/0.1"
PROTOCOL_FIRST_COMMIT = "c683d6cbdf7055b7f664b1c7fc64b7e4f0f4eea8"
POLICIES = ("STRICT_ORIGINAL", "PAIRWISE_FROZEN", "MINIMAX_WORST_CLASSES")
GATE = "BLOCKED_SYNTHETIC_SAME_PHYSICS_NO_EXTERNAL_VALIDATION"
DOUBLE_CAPS = (57, 63, 69, 77, 83, 97, 103, 109)
EXTRA_CAPS = (64, 86, 108)
PAIRS = ((0, 1), (0, 2), (1, 2))


def require(ok, msg):
    if not ok:
        raise ValueError(msg)


def worlds():
    result = []
    for cap in range(55, 111):
        for stage in range(3):
            result.append({
                "id": f"H_SINGLE_{cap}_{stage}",
                "cohort": "H_HISTORICAL_168",
                "truth_type": "single",
                "truth_class": b.STAGES[stage],
                "capacity": cap,
                "config": b.make_physical_config((stage,), cap),
            })
    for cap in DOUBLE_CAPS:
        for i, j in PAIRS:
            result.append({
                "id": f"N_DUAL_{cap}_{i}{j}",
                "cohort": "N_NEW_DOUBLE_24",
                "truth_type": "double",
                "truth_class": b.klass([b.STAGES[i], b.STAGES[j]]),
                "capacity": cap,
                "config": b.make_physical_config((i, j), cap),
            })
    for cap in EXTRA_CAPS:
        result.append({
            "id": f"S_EXTRA_{cap}",
            "cohort": "S_EXTRA_UNKNOWN_3",
            "truth_type": "unknown-extra",
            "truth_class": None,
            "capacity": cap,
            "config": b.make_physical_config((), cap, extra=True),
        })
    require(len(result) == 195 and
            len(set(x["id"] for x in result)) == 195,
            "CAF10_WORLD_CONTRACT_BROKEN")
    return result


def affordable():
    return [a for a in b.ACTIONS if a["id"] != b.FIRST_ACTION_ID
            and a["cost"] <= b.BUDGET - b.FIRST["cost"]]


def plausible(prediction, error=1):
    """Exact observable nonnegative integer grid in +/- error rectangle."""
    require(all(type(x) is int and x >= 0 for x in prediction),
            "CAF10_INVALID_COUNT_VECTOR")
    return product(*(range(max(0, k - error), k + error + 1)
                     for k in prediction))


def minimax_outcomes(rows, preds, survivor_ids, action_id):
    """Worst over UNION of each candidate's +/-1 integer observation boxes.

    This is a finite exact enumeration, not sampling or an empirical noise law.
    """
    require(action_id in b.ACTION_BY_ID, "CAF10_UNKNOWN_ACTION")
    ids = tuple(survivor_ids)
    labels = {r["id"]: r["decision_class"] for r in rows}
    require(all(h in labels and h in preds for h in ids),
            "CAF10_UNKNOWN_HYPOTHESIS")
    yset = set()
    for h in ids:
        yset.update(plausible(preds[h][action_id], b.TOLERANCE))
    require(bool(yset), "CAF10_NO_POSSIBLE_OBSERVATION")
    hist_classes, hist_hypos = Counter(), Counter()
    max_classes = max_hypotheses = min_classes = 0
    min_classes = len(ids)
    for y in sorted(yset):
        accepted = [h for h in ids
                    if all(abs(x - p) <= b.TOLERANCE
                           for x, p in zip(y, preds[h][action_id]))]
        require(accepted, "CAF10_OBSERVATION_OUTSIDE_PREDICTION_UNION")
        nc = len({labels[h] for h in accepted})
        nh = len(accepted)
        hist_classes[nc] += 1
        hist_hypos[nh] += 1
        max_classes = max(max_classes, nc)
        max_hypotheses = max(max_hypotheses, nh)
        min_classes = min(min_classes, nc)
    return {
        "distinct_possible_integer_observations": len(yset),
        "worst_surviving_classes": max_classes,
        "worst_surviving_hypotheses": max_hypotheses,
        "best_surviving_classes": min_classes,
        "counts_by_class_cardinality_NONPROBABILISTIC": dict(sorted(hist_classes.items())),
        "no_probability_weights_assigned": True,
    }


def minimax_select(rows, preds, survivors, cache=None):
    labels = b.classes(rows, survivors)
    if not survivors:
        return {"status": b.MODEL_GAP, "action": None,
                "candidate_metrics": [], "rule": "MINIMAX_WORST_CLASSES"}
    if len(labels) == 1:
        return {"status": "STOP_SINGLE_CLASS_WITHIN_BANK", "action": None,
                "candidate_metrics": [], "rule": "MINIMAX_WORST_CLASSES"}
    scored = c9.candidate_scores(rows, preds, survivors)
    rankable = []
    key_surv = tuple(survivors)
    for item in scored:
        if item["separated_cross_class_pairs"] <= 0:
            continue
        key = (key_surv, item["action_id"])
        if cache is not None and key in cache:
            metric = cache[key]
        else:
            metric = minimax_outcomes(rows, preds, survivors, item["action_id"])
            if cache is not None:
                cache[key] = metric
        rankable.append({**item, **metric})
    if not rankable:
        return {"status": "NO_ROBUST_PAIR_FOR_ANY_AFFORDABLE_PROBE",
                "action": None, "candidate_metrics": [],
                "rule": "MINIMAX_WORST_CLASSES"}
    rankable.sort(key=lambda x: (
        x["worst_surviving_classes"],
        x["worst_surviving_hypotheses"],
        x["cost"], x["action_id"]))
    chosen = rankable[0]
    return {
        "status": "MINIMAX_SELECTED",
        "rule": "MINIMAX_WORST_CLASSES",
        "action": b.ACTION_BY_ID[chosen["action_id"]],
        "selected_score": chosen,
        "candidate_metrics": rankable,
        "worst_case_class_reduction_guaranteed":
            len(labels) - chosen["worst_surviving_classes"],
        "no_minimum_improvement_gate": True,
    }


def graph_summary(rows, preds, survivors):
    labels = {r["id"]: r["decision_class"] for r in rows}
    actions = affordable()
    total = indistinguishable = 0
    for h, k in combinations(survivors, 2):
        if labels[h] == labels[k]:
            continue
        total += 1
        if not any(
            any(abs(x - y) > b.DIVERGENCE_THRESHOLD
                for x, y in zip(preds[h][a["id"]], preds[k][a["id"]]))
            for a in actions):
            indistinguishable += 1
    return {"cross_class_pairs": total,
            "no_uniform_robust_separation_any_affordable_action": indistinguishable,
            "NOT_an_equivalence_partition": True,
            "one_conditional_K2_max": True}


def classification(raw, world):
    """Use CAF-09's evaluator formula; compare against b legacy in tests."""
    return c9.classify_evaluator(world, raw)


def normalize_strict(result, world):
    x = c9.normalized_legacy(result, "single_plus_dual")
    return {**x, "cohort": world["cohort"],
            "capacity_EVALUATOR_ONLY": world["capacity"],
            "n_classes_final": len(x["final_classes"]),
            "label_coverage_EVALUATOR_ONLY":
                (world["truth_class"] in x["final_classes"]
                 if world["truth_class"] is not None else None)}


def evaluate_alternative(world, rows, preds, policy, out, cache):
    """Truth/config used only to ask DES for observations, never by selector."""
    baseline = b.read_physical(
        world["config"], b.caf07.T0_RATE, b.caf07.T0_MINUTE,
        (("delivered", None),))
    prior = b.eligible(rows, preds, {"baseline": baseline})
    first = b.read_physical(
        world["config"], b.FIRST["rate"], b.FIRST["minute"],
        b.FIRST["channels"])
    survivors = b.eligible(rows, preds, {b.FIRST_ACTION_ID: first}, prior)
    if policy == "PAIRWISE_FROZEN":
        choice = c9.choose_relaxed(rows, preds, survivors, "PAIRWISE_ANY")
    elif policy == "MINIMAX_WORST_CLASSES":
        choice = minimax_select(rows, preds, survivors, cache=cache)
    else:
        raise ValueError("CAF10_POLICY_NOT_DECLARED")
    b.lab.write_new(out, f"01_CHOICE_{world['id']}_{policy}.json", {
        "schema": SCHEMA, "world_id": world["id"],
        "policy": policy, "K0": baseline, "K1": first,
        "after_K1_hypotheses": survivors,
        "after_K1_classes": b.classes(rows, survivors),
        "decision_before_any_second_DES": choice,
        "second_DES_calls_so_far": 0,
        "world_truth_not_given_to_choice": True,
    })
    measured, cost = None, b.FIRST["cost"]
    if choice["action"]:
        action = choice["action"]
        require(cost + action["cost"] <= b.BUDGET,
                "CAF10_COST_EXCEEDS_BUDGET")
        measured = b.read_physical(
            world["config"], action["rate"], action["minute"],
            action["channels"])
        decision = b.update(rows, preds, survivors,
                            action["id"], measured)
        cost += action["cost"]
    else:
        labels = b.classes(rows, survivors)
        status = b.MODEL_GAP if not survivors else (
            "SINGLE_CLASS_WITHIN_BANK" if len(labels) == 1
            else b.THRESHOLD_FAIL)
        decision = {"status": status, "after": survivors,
                    "classes": labels,
                    "diagnosis_within_bank": labels[0]
                    if len(labels) == 1 else None}
    verdict = classification(decision, world)
    return {
        "case": world["id"], "cohort": world["cohort"],
        "capacity_EVALUATOR_ONLY": world["capacity"],
        "policy": policy,
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
        "n_classes_final": len(decision["classes"]),
        "label_coverage_EVALUATOR_ONLY":
            (world["truth_class"] in decision["classes"]
             if world["truth_class"] is not None else None),
    }


def summary(rows):
    result = {}
    for cohort in ("H_HISTORICAL_168","N_NEW_DOUBLE_24","S_EXTRA_UNKNOWN_3"):
        result[cohort] = {}
        for pol in POLICIES:
            subset = [r for r in rows if r["cohort"] == cohort
                      and r["policy"] == pol]
            verdicts = Counter(x["verdict_EVALUATOR_ONLY"] for x in subset)
            covered = [r for r in subset if r["label_coverage_EVALUATOR_ONLY"] is not None]
            taken = [x for x in subset if x["second_action"] is not None]
            result[cohort][pol] = {
                "n": len(subset),
                "correct": verdicts["CORRECT_WITHIN_SIMULATED_WORLD"],
                "false_single": verdicts["FALSE_SINGLE_DIAGNOSIS"],
                "wrong_class": verdicts["WRONG_CLASS"],
                "abstain": verdicts["ABSTAIN"],
                "model_gap": verdicts["MODEL_GAP"],
                "unique_diagnoses": sum(x["diagnosis"] is not None for x in subset),
                "n_with_second": len(taken),
                "class_reductions": sum(
                    len(x["classes_after_first"]) - len(x["final_classes"])
                    for x in taken),
                "second_actions_reducing_class_count": sum(
                    len(x["final_classes"]) < len(x["classes_after_first"])
                    for x in taken),
                "true_class_covered_numer": sum(x["label_coverage_EVALUATOR_ONLY"]
                                                for x in covered),
                "true_class_covered_denom": len(covered),
                "mean_final_class_count": (
                    round(sum(x["n_classes_final"] for x in subset)/len(subset),4)
                    if subset else None),
                "sum_ordinal_costs": sum(x["cost_spent"] for x in subset),
                "chosen_actions": dict(sorted(Counter(
                    x["second_action"] or "NO_K2" for x in subset).items())),
            }
    return result


def run(out, checkout_sha, head_sha):
    require(b.SOURCE_COMMIT_PATTERN.fullmatch(checkout_sha) is not None
            and b.SOURCE_COMMIT_PATTERN.fullmatch(head_sha) is not None,
            "CAF10_SHA_REQUIRED")
    dest = Path(out).resolve()
    require(not dest.exists(), "CAF10_OUTPUT_EXISTS")
    cohort = worlds()
    bank = b.bank(True)
    require(len(bank) == 24 and b.TOLERANCE == 1 and b.BUDGET == 8
            and b.FIRST_ACTION_ID == "delivered_15_t20"
            and len(cohort) == 195, "CAF10_FROZEN_DOMAIN_CHANGED")
    preds = b.precompute(bank)
    dest.mkdir(parents=True, exist_ok=False)
    b.lab.write_new(dest, "00_FROZEN_PLAN.json", {
        "schema": SCHEMA, "protocol_first_commit": PROTOCOL_FIRST_COMMIT,
        "checkout_sha": checkout_sha, "pr_head_sha": head_sha,
        "evaluator_worlds_EVALUATOR_ONLY": cohort,
        "candidate_bank": bank, "bank_DES_predictions": preds,
        "three_policies": POLICIES,
        "pairwise_uses_original_CAF09_function": True,
        "strict_uses_original_CAF07B_evaluate_case": True,
        "minimax_worst_possible_class_cardinality": True,
        "minimax_all_integer_measurements_in_union_of_plus_minus_one_boxes": True,
        "minimax_gate_requires_at_least_one_robust_interclass_pair": True,
        "minimax_tiebreak": ["worst_classes","worst_hypotheses",
                            "cost","action_id"],
        "menu": list(b.ACTIONS), "initial": b.FIRST,
        "cumulative_budget": b.BUDGET,
        "tolerance": b.TOLERANCE,
        "MAX_ONE_K2": True,
        "new_world_DES_calls_before_plan": 0,
        "historical_168_are_not_held_out": True,
        "novel_24_are_synthetic_not_real_data": True,
        "service_stochasticity_modelled": False,
    })
    evaluations, structural = [], []
    cache = {}
    for world in cohort:
        strict = b.evaluate_case(
            world, bank, preds, "single_plus_dual_STRICT_ORIGINAL", dest)
        normalized = normalize_strict(strict, world)
        evaluations.append(normalized)
        structural.append({
            "case": world["id"], "cohort": world["cohort"],
            "K1_classes": normalized["classes_after_first"],
            **graph_summary(bank, preds, normalized["survivors_after_first"]),
        })
        for pol in POLICIES[1:]:
            item = evaluate_alternative(world, bank, preds, pol, dest, cache)
            require(item["baseline"] == normalized["baseline"] and
                    item["first"] == normalized["first"] and
                    item["survivors_after_first"] ==
                    normalized["survivors_after_first"],
                    "CAF10_UNEQUAL_K0_K1_OR_CANDIDATES")
            evaluations.append(item)
    require(len(evaluations) == 585 and len(structural) == 195,
            "CAF10_WRONG_EVALUATION_COUNT")
    for x in evaluations:
        require(x["cost_spent"] <= b.BUDGET, "CAF10_BAD_ORDINAL_COST")
    report = summary(evaluations)
    result = {
        "schema": SCHEMA, "protocol_first_commit": PROTOCOL_FIRST_COMMIT,
        "checkout_sha": checkout_sha, "pr_head_sha": head_sha,
        "n_worlds": len(cohort),
        "n_evaluations": len(evaluations),
        "n_presaved_choices": 585,
        "n_historical_single": 168,
        "n_novel_double": 24,
        "n_extra_unknown_controls": 3,
        "strict_selector_imported_unchanged": True,
        "pairwise_selector_imported_unchanged": True,
        "certification_bank_always_expanded": True,
        "world_truth_never_passed_to_policy": True,
        "noise_is_bounded_uncertainty_not_empirical_sensor_model": True,
        "promotion_gate": GATE,
        "external_validity_proven": False,
        "interpretation_requires_external_review": True,
        "summary": report,
        "structural_graph_per_world": structural,
        "evaluations": evaluations,
    }
    b.lab.write_new(dest, "02_RESULTADOS.json", result)
    lines = [
        "# CAF-10 — Resultado sintético, pruebas de adquisición y certificación",
        "",
        "No validado: física DES determinista compartida, sin ruido medido,",
        "sin costos económicos calibrados, sin preregistro externo, mundos diseñados.",
        "",
        "| Cohorte | Política | Mundos | K2 | Correctos | Falsos únicos | Otras clases erróneas | Abstenciones | Brechas | Cobertura de etiqueta | Clases finales medias |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for co in report:
        for pol in POLICIES:
            a=report[co][pol]
            lines.append("| " + " | ".join(map(str, (
                co, pol,a["n"],a["n_with_second"],a["correct"],
                a["false_single"],a["wrong_class"],a["abstain"],
                a["model_gap"],
                f'{a["true_class_covered_numer"]}/{a["true_class_covered_denom"]}'
                if a["true_class_covered_denom"] else "N/A",
                a["mean_final_class_count"]
            )))+" |")
    lines += ["",
              "## Interpretación obligatoria",
              "",
              "- 168 cuellos únicos son HISTÓRICOS (#117), 24 dobles son nuevas",
              "configuraciones sintéticas, 3 cuartas etapas son controles.",
              "- Cobertura significa clase verdadera aún presente; NO certeza.",
              "- Menor cantidad de clases no garantiza menor riesgo de falsa etiqueta",
              "ni calidad de una acción de negocio.",
              "- Minimax cuantifica peores casos del modelo + banda ±1 por canal;",
              "NO construye distribución de ruido ni minimiza pérdida económica.",
              "- Grafo no es partición: proximidad dentro de tolerancia no transita.",
              "- Solo una segunda medición asequible con presupuesto ordinal 8.",
              "",
              f"Gate: {GATE}. No fusionar ni promover por CI verde.",
              ""]
    b.lab.write_new(dest, "03_INFORME.md", "\n".join(lines))
    recorded=sorted(x for x in dest.iterdir() if x.is_file())
    b.lab.write_new(dest, "04_MANIFIESTO.json", {
        "schema": SCHEMA, "checkout_sha": checkout_sha,
        "pr_head_sha": head_sha,
        "files_sha256": {
            p.name: "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()
            for p in recorded
        },
        "not_real_world_validated": True,
        "no_overwrites": True,
    })
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--checkout-sha", required=True)
    p.add_argument("--head-sha", required=True)
    args = p.parse_args()
    r = run(args.out,args.checkout_sha,args.head_sha)
    print(json.dumps({
        "n_worlds":r["n_worlds"],"n_evaluations":r["n_evaluations"],
        "summary":r["summary"],"gate":r["promotion_gate"],
    },sort_keys=True,ensure_ascii=False))


if __name__ == "__main__":
    main()
