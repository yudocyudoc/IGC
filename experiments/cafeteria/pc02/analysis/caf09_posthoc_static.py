#!/usr/bin/env python3
"""CAF-09: read-only posthoc audit of canonical GitHub Actions JSON.

NO imports from DES, CAF-07B, or CAF-09 simulator; no event simulations.
The analysis uses *only* previously emitted plan and evaluation records.
"""
from __future__ import annotations

import argparse
from collections import Counter
from itertools import combinations
import json
from pathlib import Path

POLICIES = ("STRICT_ORIGINAL", "ANY_GUARANTEED", "PAIRWISE_ANY")
BANKS = ("single_only", "single_plus_dual")
EXPECTED_RUN_HEAD = "6a430e213fa9dd5f707846eaeaed2777d62f5f55"
EXPECTED_RUN_CHECKOUT = "51a97a222633b76ec185466022e690a1d792e3d4"
EXPECTED_RUN_ID = 41246972768
EXPECTED_ARTIFACT_ID = 13059681294


def need(flag, message):
    if not flag:
        raise ValueError(message)


def in_taxonomy(item):
    return item["world_type_EVALUATOR_ONLY"] == "single" or (
        item["bank"] == "single_plus_dual"
        and item["world_type_EVALUATOR_ONLY"] == "double")


def affordable_actions(plan):
    remaining = plan["cumulative_budget"] - plan["first_action"]["cost"]
    return [x for x in plan["menu"]
            if x["id"] != plan["first_action"]["id"] and
            x["cost"] <= remaining]


def distinguish(predictions, a, b, action, threshold):
    x, y = predictions[a][action["id"]], predictions[b][action["id"]]
    need(len(x) == len(y) > 0, "CAF09_AUDIT_BAD_CHANNELS")
    return any(abs(v - w) > threshold for v, w in zip(x, y))


def structural_graph(plan, bank, after_k1):
    """Edges are NON-separation under all affordable *single* actions.

    Edge relation is symmetric/reflexive but generally NOT TRANSITIVE.
    A graph is correct; equivalence classes/components are NOT claimed.
    """
    rows = plan["banks"][bank]
    labels = {x["id"]: x["decision_class"] for x in rows}
    preds = plan["predictions_precomputed"][bank]
    actions = affordable_actions(plan)
    threshold = plan["robust_cross_class_difference_strictly_greater_than"]
    need(set(after_k1).issubset(labels), "CAF09_AUDIT_UNKNOWN_HYPOTHESIS")
    edges = []
    for left, right in combinations(after_k1, 2):
        if not any(distinguish(preds, left, right, action, threshold)
                   for action in actions):
            edges.append((left, right))
    cross = [list(edge) for edge in edges
             if labels[edge[0]] != labels[edge[1]]]
    total_cross = sum(labels[a] != labels[b] for a, b in combinations(after_k1, 2))
    need(len(cross) <= total_cross, "CAF09_AUDIT_GRAPH_OVERFLOW")
    return {
        "affordable_action_count": len(actions),
        "hypotheses_after_K1": len(after_k1),
        "classes_after_K1": len({labels[k] for k in after_k1}),
        "cross_class_pairs": total_cross,
        "cross_class_pairs_robustly_inseparable_across_entire_menu": len(cross),
        "confounding_edges": cross,
        "interpretation": (
            "Pairs with overlapping +/-1 prediction rectangles for every "
            "affordable action: no uniform robust distinction, not a transitive "
            "partition, not proof of identical physical structure"
        ),
    }


def action_properties(plan, bank, after_k1):
    labels = {x["id"]: x["decision_class"] for x in plan["banks"][bank]}
    pred = plan["predictions_precomputed"][bank]
    threshold = plan["robust_cross_class_difference_strictly_greater_than"]
    options = []
    if len({labels[h] for h in after_k1}) <= 1:
        return options
    for action in affordable_actions(plan):
        isolated = []
        for h in after_k1:
            rivals = [r for r in after_k1 if labels[r] != labels[h]]
            if rivals and all(distinguish(pred, h, r, action, threshold)
                              for r in rivals):
                isolated.append(h)
        pairs = sum(
            labels[a] != labels[b] and distinguish(pred, a, b, action, threshold)
            for a, b in combinations(after_k1, 2))
        classes = {labels[k] for k in after_k1}
        strict = bool(classes) and all(
            any(labels[h] == c for h in isolated) for c in classes)
        options.append({"action": action["id"],
                        "strict_eligible": strict,
                        "any_isolated": bool(isolated),
                        "any_pair": pairs > 0,
                        "isolated_count": len(isolated),
                        "pair_count": pairs})
    return options


def audit(plan, results):
    need(plan["checkout_sha"] == results["checkout_sha"],
         "CAF09_AUDIT_MISMATCHED_CHECKOUT")
    need(plan["pr_head_sha"] == results["pr_head_sha"],
         "CAF09_AUDIT_MISMATCHED_HEAD")
    need(plan["pr_head_sha"] == EXPECTED_RUN_HEAD and
         plan["checkout_sha"] == EXPECTED_RUN_CHECKOUT,
         "CAF09_AUDIT_NOT_CANONICAL_RUN")
    need(plan["tolerance_orders"] == 1 and plan["cumulative_budget"] == 8,
         "CAF09_AUDIT_POLICY_CHANGED")
    need(len(results["evaluations"]) == 66 and len(results["observability_per_world_bank"]) == 22,
         "CAF09_AUDIT_UNEXPECTED_EVALUATION_COUNT")
    need(plan["robust_cross_class_difference_strictly_greater_than"] == 2,
         "CAF09_AUDIT_THRESHOLD_CHANGED")

    index = {}
    for record in results["evaluations"]:
        key = (record["bank"], record["case"], record["policy"])
        need(key not in index, "CAF09_AUDIT_DUPLICATE_EVALUATION")
        index[key] = record
    need(set(x["bank"] for x in index.values()) == set(BANKS),
         "CAF09_AUDIT_BANK_CHANGE")
    need(set(x["policy"] for x in index.values()) == set(POLICIES),
         "CAF09_AUDIT_POLICY_CHANGE")

    worlds = [x["id"] for x in plan["worlds_EVALUATOR_ONLY"]]
    need(len(worlds) == 11, "CAF09_AUDIT_WORLD_CHANGE")
    report = {
        "schema": "igc-caf09-static-posthoc-audit/0.1",
        "canonical_github_actions_run": EXPECTED_RUN_ID,
        "canonical_github_actions_artifact": EXPECTED_ARTIFACT_ID,
        "recorded_checkout_sha": results["checkout_sha"],
        "recorded_pr_head_sha": results["pr_head_sha"],
        "NO_NEW_DES_SIMULATIONS": True,
        "retrospective_known_worlds": True,
        "tolerance_orders": 1,
        "one_conditional_second_measurement_max": True,
        "per_world": [],
        "coverage_by_bank_and_policy": {},
        "action_selection_by_bank_and_policy": {},
        "nested_action_eligibility_violations": [],
        "cross_class_graph_summary": [],
        "promotion_gate": "BLOCKED_RETROSPECTIVE_NOT_STOCHASTIC",
    }
    for bank in BANKS:
        report["coverage_by_bank_and_policy"][bank] = {}
        report["action_selection_by_bank_and_policy"][bank] = {}
        for pol in POLICIES:
            outcomes = []
            for case in worlds:
                key = (bank, case, pol)
                need(key in index, "CAF09_AUDIT_MISSING_EVALUATION")
                x = index[key]
                n = len(x["final_classes"])
                truth = x["truth_class_EVALUATOR_ONLY"]
                represented = in_taxonomy(x)
                if represented:
                    need(truth is not None, "CAF09_AUDIT_BAD_TRUTH")
                row = {
                    "bank": bank, "case": case, "policy": pol,
                    "world_type_EVALUATOR_ONLY": x["world_type_EVALUATOR_ONLY"],
                    "represented_truth_class_in_catalog": represented,
                    "true_class_EVALUATOR_ONLY": truth,
                    "classes_after_K1": x["classes_after_first"],
                    "classes_after_K2": x["final_classes"],
                    "n_classes_after_K1": len(x["classes_after_first"]),
                    "n_classes_after_K2": n,
                    "true_class_covered_EVALUATOR_ONLY":
                        truth in x["final_classes"] if represented else None,
                    "true_class_covered_after_K1_EVALUATOR_ONLY":
                        truth in x["classes_after_first"] if represented else None,
                    "second_action": x["second_action"],
                    "verdict_EVALUATOR_ONLY": x["verdict_EVALUATOR_ONLY"],
                }
                outcomes.append(row)
                report["per_world"].append(row)
            inside = [x for x in outcomes if x["represented_truth_class_in_catalog"]]
            report["coverage_by_bank_and_policy"][bank][pol] = {
                "represented_worlds": len(inside),
                "covered_after_K1": sum(x["true_class_covered_after_K1_EVALUATOR_ONLY"] for x in inside),
                "covered_after_final": sum(x["true_class_covered_EVALUATOR_ONLY"] for x in inside),
                "unique_class_with_true_label": sum(
                    x["n_classes_after_K2"] == 1 and x["true_class_covered_EVALUATOR_ONLY"]
                    for x in inside),
                "out_of_taxonomy_worlds_NOT_IN_DENOMINATOR": 11 - len(inside),
                "note": "Coverage of true decision-class label, NOT exact capacity/parameter coverage",
            }
            report["action_selection_by_bank_and_policy"][bank][pol] = dict(
                sorted(Counter(x["second_action"] or "NO_MEASUREMENT"
                               for x in outcomes).items()))

        for case in worlds:
            pre = index[(bank, case, POLICIES[0])]
            after = pre["survivors_after_first"]
            graph = structural_graph(plan, bank, after)
            graph["bank"] = bank
            graph["case"] = case
            report["cross_class_graph_summary"].append(graph)
            opts = action_properties(plan, bank, after)
            for op in opts:
                if op["strict_eligible"] and not op["any_isolated"]:
                    report["nested_action_eligibility_violations"].append(
                        (bank, case, op["action"], "strict_not_any"))
                if op["any_isolated"] and not op["any_pair"]:
                    report["nested_action_eligibility_violations"].append(
                        (bank, case, op["action"], "any_not_pair"))
    need(not report["nested_action_eligibility_violations"],
         "CAF09_AUDIT_NESTED_LEMMA_VIOLATION")
    # All nine taxonomy-represented worlds in the expanded bank retain their
    # class label for this deterministic run. This is a frozen measurement,
    # NOT a theorem about continuous capacities or noisy observations.
    for pol in POLICIES:
        x = report["coverage_by_bank_and_policy"]["single_plus_dual"][pol]
        need(x["represented_worlds"] == 9 and x["covered_after_final"] == 9,
             "CAF09_AUDIT_UNEXPECTED_CANONICAL_COVERAGE")
    return report


def render(r):
    out = [
        "# CAF-09: auditoría estática de clases supervivientes y confusibilidad",
        "",
        "**Fuente:** GitHub Actions canónica "
        f"[#{EXPECTED_RUN_ID}](https://github.com/yudocyudoc/IGC/actions/runs/{EXPECTED_RUN_ID}). "
        "**No se ejecutó DES:** solo se leyeron plan y 66 resultados.",
        "",
        "**Alcance:** un paso condicional K2, presupuesto 8, tolerancia ±1; "
        "11 mundos retrospectivos conocidos. No es validación externa.",
        "",
        "## Cobertura de clase verdadera (solo mundos representados en catálogo)",
        "",
        "| Banco | Política | Cubierta tras K1 | Cubierta al final | Clases únicas correctas | Fuera de taxonomía (excluidos) |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for bank in BANKS:
        for pol in POLICIES:
            s = r["coverage_by_bank_and_policy"][bank][pol]
            out.append(
                f"| {bank} | {pol} | {s['covered_after_K1']}/{s['represented_worlds']} "
                f"| {s['covered_after_final']}/{s['represented_worlds']} "
                f"| {s['unique_class_with_true_label']}/{s['represented_worlds']} "
                f"| {s['out_of_taxonomy_worlds_NOT_IN_DENOMINATOR']} |")
    out += ["",
            "**9/9 con el banco ampliado no equivale a 9/9 diagnósticos**: "
            "contener una clase correcta entre seis rivales es cobertura, "
            "no identificación. No incluir mundos de cuarta etapa en "
            "denominador de cobertura de clase; su clase no existe en el catálogo.",
            "",
            "## Supervivencia por mundo: banco ampliado (24)",
            "",
            "Clases enumeradas con la nomenclatura original; el orden no indica prioridad.",
            "",
            "| Mundo | Política | K1: n clases | K2: clases restantes | ¿Contiene clase verdadera? | Acción |",
            "|---|---|---:|---|---|---|"]
    for row in r["per_world"]:
        if row["bank"] != "single_plus_dual":
            continue
        covered = ("sí" if row["true_class_covered_EVALUATOR_ONLY"] is True else
                   "no" if row["true_class_covered_EVALUATOR_ONLY"] is False else
                   "N/A: fuera de taxonomía")
        out.append("| " + " | ".join((
            row["case"],row["policy"],str(row["n_classes_after_K1"]),
            ", ".join(row["classes_after_K2"]) or "∅",
            covered,row["second_action"] or "ninguna")) + " |")
    out += ["", "## Confusibilidad robusta en todo el menú asequible",
            "", "No existen **bloques de equivalencia bajo ±1** en general: "
            "la relación «los intervalos se superponen» no es transitiva. "
            "Para un solo canal, 0~2 y 2~4, pero 0 no~4. "
            "Se reporta un **grafo de pares incompatibles con garantía de separación**, "
            "no una partición.",
            "",
            "| Mundo | Pares entre clases | Pares inseparables bajo todas las acciones |",
            "|---|---:|---:|"]
    for row in r["cross_class_graph_summary"]:
        if row["bank"] != "single_plus_dual":
            continue
        out.append(f"| {row['case']} | {row['cross_class_pairs']} "
                   f"| {row['cross_class_pairs_robustly_inseparable_across_entire_menu']} |")
    out += ["", "Un par de clases distintas con diferencias ≤2 en **todos** los "
            "canales y acciones asequibles impide garantizar que ese par sea "
            "distinguible **para todas** las observaciones posibles con errores ±1; "
            "una observación realizada puede sin embargo eliminar una de las hipótesis. "
            "Esto es un límite robusto local del menú, no equivalencia física general. "
            "Evaluar *todas* las acciones por separado no implica que puedan ejecutarse "
            "todas dentro del presupuesto total.",
            "",
            "## Menú efectivo y diferencias entre compuertas",
            ""]
    for bank in BANKS:
        out += [f"**{bank}**"]
        for pol in POLICIES:
            out.append(f"- {pol}: " + ", ".join(
                f"{k}={v}" for k, v in
                r["action_selection_by_bank_and_policy"][bank][pol].items()))
        out.append("")
    out += [
        "## Lemas y cautelas",
        "",
        "1. **Elegibilidad de una acción para ≥2 clases:** estricta ⇒ alguna "
        "hipótesis totalmente aislable ⇒ algún par de clases con bandas "
        "disjuntas. Se verificaron todas las opciones asequibles en el catálogo "
        "sin contraejemplo. **No implica** que la abstención final sea monótona "
        "si dos reglas eligen acciones distintas.",
        "2. **Compuerta versus resultado:** distinguir pares en la tabla de "
        "predicciones no garantiza reducción de clases con la observación real. "
        "Una compuerta es posibilidad estructural; el veredicto depende del "
        "valor observado.",
        "3. **Criterio de certificación** no cambia; cuando el banco omite "
        "cuellos dobles, una clase única de un catálogo incompleto puede ser falsa.",
        "4. **Cobertura 9/9** se mide solo sobre clases estructurales "
        "representadas. No está garantizada con capacidades continuas o error "
        "de modelo. Las capacidades verdaderas de evaluación pueden no existir "
        "como puntos exactos en la cuadrícula de entrenamiento.",
        "5. **Sin simulaciones nuevas ni ajuste de políticas**: la tabla se "
        "extrajo del JSON previo al recibir las revisiones, con resultados "
        "retrospectivos. No usarla como confirmación de una regla elegida después.",
        "",
        f"**Promotion gate:** {r['promotion_gate']}.",
        "",
    ]
    return "\n".join(out)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--plan",type=Path,required=True)
    a.add_argument("--results",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    a.add_argument("--report",type=Path,required=True)
    args=a.parse_args()
    plan=json.loads(args.plan.read_text(encoding="utf-8"))
    data=json.loads(args.results.read_text(encoding="utf-8"))
    result=audit(plan,data)
    need(not args.out.exists() and not args.report.exists(),
         "CAF09_AUDIT_REFUSES_TO_OVERWRITE")
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    args.report.write_text(render(result),encoding="utf-8")
    print(json.dumps({"run":result["canonical_github_actions_run"],
                      "coverage":result["coverage_by_bank_and_policy"],
                      "gate":result["promotion_gate"]},sort_keys=True))


if __name__=="__main__":
    main()
