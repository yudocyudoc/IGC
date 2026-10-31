#!/usr/bin/env python3
"""CAF-08B: compare unchanged CAF-07B selector using DES vs delayed-fluid bank.

The evaluation worlds, tolerances, action set, budget and selection policy are
the SAME objects from CAF-07B. Only candidate response predictions differ.
This is a retrospective, NOT blinded, NOT preregistered, numerical benchmark.
"""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
from statistics import mean

import caf07b_umbral_secuencial as b
import caf08_fluid_des_pilot as fluid

SCHEMA = "igc-caf08b-selector-fluid-bank/0.1"
BASE_REF = "de7dd0002d29bda631c626b868f970bd986be5fe"
PRIMARY_QUANTIZATION = "nearest_integer_half_up"
REFERENCE = "DES"
CHALLENGER = "FLUID_DELAYED_HALF_UP"
PAIR_NAMES = ("single_only", "single_plus_dual")


def require(ok, explanation):
    if not ok:
        raise ValueError(explanation)


def snap_count(x):
    """Predeclared nonnegative fluid count -> integer physical counter.

    NOT a sensor-noise calibration. Never change after seeing test worlds.
    """
    require(isinstance(x, (float, int)) and math.isfinite(x) and x >= -1e-9,
            "CAF08B_INVALID_FLUID_COUNT")
    return int(math.floor(max(x, 0.0) + 0.5))


def measure_vector(snapshot, channels):
    stages = b.STAGES
    result = []
    for field, stage in channels:
        if field == "delivered" and stage is None:
            val = snapshot["delivered"]
        elif stage in stages:
            index = stages.index(stage)
            if field == "waiting":
                val = snapshot["waiting"][index]
            elif field == "stage_stock":
                val = snapshot["waiting"][index] + snapshot["serving"][index]
            else:
                raise ValueError("CAF08B_UNKNOWN_CHANNEL")
        else:
            raise ValueError("CAF08B_UNKNOWN_STAGE")
        result.append(snap_count(val))
    return result


def fluid_predictions(bank_rows, delayed=fluid.delayed_fluid):
    """Use bank physics but NOT bank DES predictions or any evaluator truth.

    Cached by full physical configuration + rate; 10/20/40 are read from
    the same continuous-mass trajectory. CAF-07B labels and channel contracts
    are used unmodified.
    """
    cache = {}
    predictions = {}
    for hyp in bank_rows:
        config = hyp["config"]
        conf_key = json.dumps(config, sort_keys=True)
        def snapshot(rate, minute):
            key = (conf_key, str(rate))
            if key not in cache:
                cache[key] = delayed(config, float(Fraction(rate)),
                                     times=(10, 20, 40))
            return cache[key][minute]
        row = {"baseline": measure_vector(
            snapshot(b.caf07.T0_RATE, b.caf07.T0_MINUTE),
            (("delivered", None),))}
        for action in b.ACTIONS:
            row[action["id"]] = measure_vector(
                snapshot(action["rate"], action["minute"]),
                action["channels"])
        predictions[hyp["id"]] = row
    require(len(predictions) == len(bank_rows),
            "CAF08B_MISSING_FLUID_HYPOTHESIS")
    return predictions


def differences(rows, des_preds, fluid_preds):
    """Describe mismatches at identical hypotheses/actions, not truth accuracy."""
    diffs = []
    by_action = {}
    for hyp in rows:
        ident = hyp["id"]
        for action in ("baseline",) + tuple(a["id"] for a in b.ACTIONS):
            a, c = des_preds[ident][action], fluid_preds[ident][action]
            require(len(a) == len(c) > 0,
                    "CAF08B_SAME_OBSERVATION_OPERATOR_REQUIRED")
            distances = [abs(x-y) for x,y in zip(a,c)]
            diffs.extend(distances)
            by_action.setdefault(action, []).extend(distances)
    return {
        "channel_comparisons": len(diffs),
        "mean_absolute_integer_difference": round(mean(diffs), 5),
        "max_absolute_integer_difference": max(diffs),
        "num_greater_than_tolerance_1": sum(d > 1 for d in diffs),
        "by_action": {
            action: {
                "count": len(values), "mean_abs": round(mean(values), 5),
                "max_abs": max(values), "greater_than_1": sum(v>1 for v in values),
            }
            for action, values in sorted(by_action.items())
        },
    }


def select_one(item, rows, preds, bank_label, output):
    """Delegate every observation, filtering and decision to CAF-07B."""
    return b.evaluate_case(item, rows, preds, bank_label, output)


def compact(result):
    s = result["selection_before_second"]
    final = result["final"]
    return {
        "case": result["case"], "bank": result["bank"],
        "world_type_EVALUATOR_ONLY": result["truth_type_EVALUATOR_ONLY"],
        "truth_class_EVALUATOR_ONLY": result["truth_class_EVALUATOR_ONLY"],
        "initial": result["initial"],
        "first_observation": result["first_observation"],
        "survivors_after_first": result["survivors_after_first"],
        "action": s["action"]["id"] if s["action"] else None,
        "selection_status": s["status"],
        "second_observation": result["second_observation"],
        "final_status": final["status"],
        "final_classes": final["classes"],
        "diagnosis": final["diagnosis_within_bank"],
        "verdict_EVALUATOR_ONLY": result["verdict_EVALUATOR_ONLY"],
        "cost_spent": result["cost_spent"],
    }


def grouped_summary(comparisons):
    result = {}
    for bank_name in PAIR_NAMES:
        result[bank_name] = {}
        for phys in (REFERENCE, CHALLENGER):
            source = [x for x in comparisons
                      if x["bank"] == bank_name and x["model"] == phys]
            group = {}
            for typ in ("single", "double", "unknown-extra"):
                items = [x for x in source
                         if x["world_type_EVALUATOR_ONLY"] == typ]
                group[typ] = {
                    "n": len(items),
                    "verdicts": dict(sorted(Counter(
                        x["verdict_EVALUATOR_ONLY"] for x in items).items())),
                    "selection_statuses": dict(sorted(Counter(
                        x["selection_status"] for x in items).items())),
                    "diagnosed": sum(x["diagnosis"] is not None for x in items),
                    "second_measurements": sum(x["action"] is not None for x in items),
                    "model_gap": sum(x["final_status"] == b.MODEL_GAP for x in items),
                    "false_single": sum(
                        x["verdict_EVALUATOR_ONLY"] == "FALSE_SINGLE_DIAGNOSIS"
                        for x in items),
                }
            result[bank_name][phys] = group
    return result


def run(out, source_commit):
    target = Path(out).resolve()
    require(not target.exists(), "CAF08B_OUTPUT_EXISTS")
    require(isinstance(source_commit, str) and
            b.SOURCE_COMMIT_PATTERN.fullmatch(source_commit),
            "CAF08B_GIT_SHA_REQUIRED")

    rows_by_bank = {name: b.bank(name == "single_plus_dual")
                    for name in PAIR_NAMES}
    predicted = {}
    mismatch = {}
    for name, rows in rows_by_bank.items():
        old = b.precompute(rows)
        new = fluid_predictions(rows)
        predicted[name] = {REFERENCE: old, CHALLENGER: new}
        mismatch[name] = differences(rows, old, new)

    worlds = b.scenarios()  # same 11 hidden-evaluator configurations as #118
    target.mkdir(parents=True, exist_ok=False)
    b.lab.write_new(target, "00_PLAN_ANTES_DE_EVALUAR.json", {
        "schema": SCHEMA, "checkout_sha": source_commit,
        "source_dependency_PR119": BASE_REF,
        "bank_names": list(PAIR_NAMES),
        "bank_hypotheses": rows_by_bank,
        "all_bank_predictions": predicted,
        "worlds_EVALUATOR_ONLY": worlds,
        "tolerance": b.TOLERANCE,
        "quality_threshold_per_class": b.MIN_GUARANTEED_PER_SURVIVING_CLASS,
        "budget": b.BUDGET,
        "fixed_first_action": b.FIRST,
        "action_menu": list(b.ACTIONS),
        "quantization": PRIMARY_QUANTIZATION,
        "same_CAF07B_policy": True,
        "posthoc_known_worlds": True,
        "simulation_not_real_world_evidence": True,
        "selection_evaluator_truth_provided": False,
    })
    comparisons = []
    pairs = []
    for bank_name, rows in rows_by_bank.items():
        for world in worlds:
            outcomes = {}
            for model in (REFERENCE, CHALLENGER):
                # Separate names avoid overwriting the original decision-trace
                # artifacts. b.evaluate_case writes its choice BEFORE second DES.
                raw = select_one(world, rows, predicted[bank_name][model],
                                 bank_name + "_" + model, target)
                result = compact(raw)
                result["bank"] = bank_name
                result["model"] = model
                outcomes[model] = result
                comparisons.append(result)
                require(result["cost_spent"] <= b.BUDGET,
                        "CAF08B_POLICY_BUDGET_EXCEEDED")
            d, f = outcomes[REFERENCE], outcomes[CHALLENGER]
            require(d["initial"] == f["initial"] and
                    d["first_observation"] == f["first_observation"],
                    "CAF08B_NONIDENTICAL_WORLD_DATA")
            pairs.append({
                "bank": bank_name, "case": world["id"],
                "same_initial_and_fixed_first_measurement": True,
                "verdict_changed": d["verdict_EVALUATOR_ONLY"] != f["verdict_EVALUATOR_ONLY"],
                "action_changed": d["action"] != f["action"],
                "diagnosis_changed": d["diagnosis"] != f["diagnosis"],
                "final_status_changed": d["final_status"] != f["final_status"],
                "survivors_changed": d["survivors_after_first"] != f["survivors_after_first"],
                "des_verdict": d["verdict_EVALUATOR_ONLY"],
                "fluid_verdict": f["verdict_EVALUATOR_ONLY"],
            })
    summary = grouped_summary(comparisons)
    output = {
        "schema": SCHEMA, "checkout_sha": source_commit,
        "state": "RETROSPECTIVE_FLUID_BANK_SELECTOR_COMPARISON",
        "evaluator_truth_passed_to_selector": False,
        "selector_implementation_changed": False,
        "sensor_or_tolerance_changed": False,
        "quantization": PRIMARY_QUANTIZATION,
        "same_world_observations_for_paired_banks": True,
        "n_worlds": len(worlds),
        "n_banks": len(rows_by_bank),
        "n_model_arms": 2,
        "n_comparisons": len(comparisons),
        "n_paired_comparisons": len(pairs),
        "predictions_DES_minus_quantized_fluid": mismatch,
        "summary": summary,
        "paired_differences": pairs,
        "evaluations": comparisons,
        "deployment_validated": False,
        "scientific_identifiability_validated": False,
        "promotion_gate": "BLOCKED_RETROSPECTIVE_NOT_BLINDED",
        "limitations": [
            "Both models share physical assumptions and hypothesis configurations",
            "Known worlds from CAF-07B, not held-out preregistration",
            "Rounded continuous mass to integer counts before unmodified +/-1 filter",
            "Mismatch can create MODEL_GAP even if true structure is in finite bank",
            "No timestamps, new observables, real sensor-noise model, or costs",
        ],
    }
    b.lab.write_new(target, "01_RESULTADOS.json", output)
    lines = [
        "# CAF-08B — comparación de bancos DES / fluido retardado",
        "",
        "CI aquí significa reproducibilidad técnica, no éxito científico.",
        "Mismos once mundos DES; misma política, umbral, acciones y tolerancia ±1 de CAF-07B.",
        "La ÚNICA diferencia del selector son curvas del banco (DES / fluido cuantizado).",
        "Fluido continuo: cuantización predeclarada half-up; no se calibra con los mundos.",
        "",
        "## Distancia entre predicciones (tras cuantización, antes de observar mundos)",
        "",
        "| Banco | Canales comparados | MAE de diferencia entera | Diferencia máxima | Diferencias > ±1 |",
        "|---|---:|---:|---:|---:|",
    ]
    for bank_name, diff in mismatch.items():
        lines.append("| " + " | ".join(map(str, (
            bank_name, diff["channel_comparisons"],
            diff["mean_absolute_integer_difference"],
            diff["max_absolute_integer_difference"],
            diff["num_greater_than_tolerance_1"]))) + " |")
    lines += [
        "",
        "## Veredictos por tipo",
        "",
        "| Banco | Motor predictivo | Tipo real | Correctos | Falsos únicos | Brechas | Abstenciones | Diagnósticos | Segundas pruebas |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name in PAIR_NAMES:
        for model in (REFERENCE, CHALLENGER):
            for typ, vals in summary[name][model].items():
                verdicts = vals["verdicts"]
                lines.append("| " + " | ".join(map(str, (
                    name, model, typ,
                    verdicts.get("CORRECT_WITHIN_SIMULATED_WORLD",0),
                    vals["false_single"], vals["model_gap"],
                    verdicts.get("ABSTAIN", 0), vals["diagnosed"],
                    vals["second_measurements"]))) + " |")
    lines += ["", "## Parejas con diferencias en diagnóstico/veredicto",
              "", "| Banco | Mundo | Veredicto DES | Veredicto fluido | Cambia acción | Cambian supervivientes |",
              "|---|---|---|---|---|---|"]
    for row in pairs:
        if any(row[x] for x in ("verdict_changed","diagnosis_changed",
                                "action_changed","survivors_changed",
                                "final_status_changed")):
            lines.append("| " + " | ".join(map(str, (
                row["bank"], row["case"], row["des_verdict"],
                row["fluid_verdict"], row["action_changed"],
                row["survivors_changed"]))) + " |")
    lines += ["", "## Limitación",
              "",
              "La equivalencia entre implementaciones NO demuestra identificación; el",
              "error de aproximación numérica tampoco calibra tolerancia instrumental.",
              "Ninguna tasa de acierto es generalizable: escenarios y banco conocidos.",
              "Las elecciones de segunda prueba quedan guardadas ANTES del DES correspondiente.",
              "La aparición de MODEL_GAP puede ser por discrepancia de aproximación,",
              "no necesariamente evidencia de cuarta etapa o mecanismo ausente.",
              "No se usan timestamps ni se modifica ATMS/M/D/Buffalo.",
              ""]
    b.lab.write_new(target, "02_INFORME.md", "\n".join(lines))
    artifacts = sorted(x.name for x in target.iterdir() if x.is_file())
    b.lab.write_new(target, "03_MANIFIESTO.json", {
        "schema": SCHEMA, "checkout_sha": source_commit,
        "files": {n: "sha256:" + hashlib.sha256(
            (target / n).read_bytes()).hexdigest() for n in artifacts},
        "no_external_custody": True, "exploratory_only": True,
        "scientific_conclusion_not_automatically_validated": True,
    })
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()
    result = run(args.out, args.source_commit)
    print(json.dumps({
        "state": result["state"],
        "n_comparisons": result["n_comparisons"],
        "paired_changed_verdicts": sum(x["verdict_changed"]
                                        for x in result["paired_differences"]),
        "prediction_mismatch_by_bank": {
            name: {key: value for key, value in distance.items()
                   if key != "by_action"}
            for name, distance in
            result["predictions_DES_minus_quantized_fluid"].items()
        },
        "summary": result["summary"],
        "promotion_gate": result["promotion_gate"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
