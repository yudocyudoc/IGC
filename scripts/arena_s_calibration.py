"""Calibrate existing CS-01/CS-02 molecules using construction data only.

FM-B5 RK4 grid search is used for PARAMETER FITTING, not for scored predictions.
The generated composed Modelica source binds separate fitted parameters to each
structure. Evaluation must run the generated Modelica in OpenModelica, after S
selection and before a reserved observation is exposed.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
import math
from pathlib import Path

from .arena_round import hash_obj, exclusive_json, numbers
from .arena_sp_producers import ProviderError
from .compose_molecular_candidates import render_modelica
from .fm_b5_parameter_identifiability import grid_fit, sample_times
from .validate_fm_a_contract import canonical_structure_hash, validate_references

SCHEMA = "igc-arena-s-calibration/0.1"


def check(value: bool, error: str) -> None:
    if not value:
        raise ProviderError(error)


def calibrate(composed: dict, modelica_plan: dict,
              fit_plan: dict, primary: dict) -> tuple[dict, dict, dict]:
    """Returns calibrated structure, evaluation-pulse plan and hashed fit record."""
    check(modelica_plan.get("synthetic") is True
          and modelica_plan.get("empirical_or_causal_claim") is False,
          "CALIBRATION_REQUIRES_SYNTHETIC_MODEL")
    check(primary.get("observable_id") == "delivered"
          and primary.get("unit") == "units",
          "CALIBRATION_OBSERVABLE_MISMATCH")
    allowed={"schema","synthetic","parameter_ranges","calibration",
             "held_out_discrimination","numerics","uncertainty_rule",
             "synthetic_data_generation","note"}
    check(fit_plan.get("schema") == "igc-arena-s-fit-config/0.1"
          and fit_plan.get("synthetic") is True
          and set(fit_plan) <= allowed
          and set(fit_plan.get("synthetic_data_generation",{})) ==
              {"noise_standard_deviation"},
          "FIT_PLAN_MUST_EXCLUDE_GENERATOR_TRUTH")
    calibration = fit_plan["calibration"]
    input_profile = primary.get("input_profile")
    check(isinstance(input_profile, dict)
          and input_profile.get("kind") == "pulse"
          and input_profile.get("initial_stocks_zero") is True
          and type(input_profile.get("amplitude")) in (int,float)
          and type(input_profile.get("duration")) in (int,float)
          and math.isclose(float(input_profile["amplitude"]),
                           float(calibration["input_amplitude"]),rel_tol=0,abs_tol=1e-12)
          and math.isclose(float(input_profile["duration"]),
                           float(calibration["input_duration"]),rel_tol=0,abs_tol=1e-12),
          "CALIBRATION_INPUT_PROFILE_MISMATCH")
    times = numbers(primary["times"])
    observed = numbers(primary["values"])
    expected = sample_times(float(calibration["stop_time"]),
                            float(calibration["observation_interval"]))
    check(len(times) == len(observed) == len(expected)
          and all(abs(x-y) < 1e-9 for x,y in zip(times, expected)),
          "CALIBRATION_TIME_GRID_MISMATCH")
    check(len(composed["candidates"]) == 2
          and {c["id"].rsplit(":",1)[-1] for c in composed["candidates"]} ==
          {"CS-01","CS-02"}, "CALIBRATION_REQUIRES_TWO_STRUCTURES")
    result = deepcopy(composed)
    structures = {s["id"]:s for s in result["structures"]}
    fits={}
    for candidate in result["candidates"]:
        stage_ids = [node for node in structures[candidate["structure_revision_id"]]
                     ["molecule_instances"]
                     if node["molecule_definition_id"] == modelica_plan["roles"]["stage"]]
        stage_count = len(stage_ids)
        check(stage_count in (1,2) and
              candidate["id"].endswith(f"CS-0{stage_count}"),
              "CALIBRATION_STAGE_COUNT_MISMATCH")
        fit = grid_fit(fit_plan,stage_count,times,observed)
        best = fit["best_fit"]
        for stage in stage_ids:
            bindings={binding["parameter_id"]:binding for binding
                      in stage["parameter_bindings"]}
            check(set(bindings) == {"maxThroughput","responseTime"},
                  "CALIBRATION_PARAMETER_BINDINGS_MISMATCH")
            for name in ("maxThroughput","responseTime"):
                bindings[name]["value"]=best[name]
        structure=structures[candidate["structure_revision_id"]]
        structure["structural_hash"]=canonical_structure_hash(structure)
        fits[candidate["id"]]={
            "best_fit":{k:best[k] for k in ("maxThroughput","responseTime","rmse","sse")},
            "uncertainty_set":fit["parameter_uncertainty_set"],
            "compatible_grid_points":fit["approx_95_percent_grid_set_size"],
            "total_grid_points":len(fit["all_grid_points"])}
    validate_references(result)
    # Explicit predeclared discrimination pulse from B5. No future data read.
    pulse = fit_plan["held_out_discrimination"]
    amplitude = float(pulse["input_amplitude"])
    duration = float(pulse["input_duration"])
    stop = float(pulse["stop_time"])
    observation_interval = float(pulse["observation_interval"])
    check(all(math.isfinite(x) and x>0 for x in
              (amplitude,duration,stop,observation_interval))
          and duration < stop, "CALIBRATION_PULSE_INVALID")
    count=round(stop/observation_interval)
    check(count >= 1 and abs(count*observation_interval-stop)<1e-9,
          "CALIBRATION_EVALUATION_GRID_INVALID")
    evaluation_plan=deepcopy(modelica_plan)
    evaluation_plan["external_input"]["value"]=amplitude
    evaluation_plan["external_input"]["profile"]={
        "kind":"pulse","amplitude":amplitude,"offset":0.0,
        "period":2*stop,"width_percent":100*duration/(2*stop),
        "start_time":0.0}
    evaluation_plan["simulation"]={"start_time":0.0,
                                   "stop_time":stop,"intervals":count}
    report={
        "schema":SCHEMA, "status":"PARAMETERS_FITTED_CONSTRUCTION_ONLY",
        "synthetic":True, "parameter_fit_backend":"FM_B5_RK4_GRID",
        "prediction_backend_required":"OPENMODELICA",
        "construction_hash":hash_obj(primary),
        "fit_plan_hash":hash_obj(fit_plan),
        "input_composed_hash":hash_obj(composed),
        "calibrated_composed_hash":hash_obj(result),
        "evaluation_plan_hash":hash_obj(evaluation_plan),
        "fits":fits, "holdout_accessed":False,
        "models_identified_as_truth":False,
        "fitting_is_not_evidence_of_model_truth":True}
    report["report_hash"]=hash_obj(report)
    return result,evaluation_plan,report


def verify_calibration(receipt: dict, base: dict, calibrated: dict,
                       base_plan: dict, eval_plan: dict,
                       fit_plan: dict, primary: dict) -> None:
    check(receipt.get("report_hash") == hash_obj({
        k:v for k,v in receipt.items() if k != "report_hash"}),
        "CALIBRATION_RECEIPT_TAMPERED")
    expected_composed,expected_plan,expected_receipt = calibrate(
        base,base_plan,fit_plan,primary)
    check((expected_composed,expected_plan,expected_receipt) ==
          (calibrated,eval_plan,receipt),
          "CALIBRATION_REPLAY_MISMATCH")


def main() -> None:
    p=argparse.ArgumentParser(description="Fit candidate parameters with construction ONLY")
    for name in ("composed","plan","fit-plan","primary","out-dir"):
        p.add_argument("--"+name,required=True,type=Path)
    args=p.parse_args()
    read=lambda path:json.loads(path.read_text(encoding="utf-8"))
    fitted,plan,report=calibrate(
        read(args.composed), read(args.plan),read(args.fit_plan),
        read(args.primary))
    out=args.out_dir
    out.mkdir(parents=True, exist_ok=False)
    exclusive_json(out/"calibrated-composed.json",fitted)
    exclusive_json(out/"evaluation-plan.json",plan)
    exclusive_json(out/"calibration-receipt.json",report)
    (out/"GeneratedMolecularCandidates.mo").write_text(
        render_modelica(plan,fitted),encoding="utf-8")
    print(json.dumps({"status":report["status"],
                      "report_hash":report["report_hash"]}))


if __name__ == "__main__":
    main()
