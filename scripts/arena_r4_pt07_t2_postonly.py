"""Reproduce PT-07 R4 T2 locked physical inference from authentic archived bytes.

No OpenModelica calls, no new forecasts, no optimization and no world data
before locked forecast integrity checks. The generator identity is opened
only after the scored immutable R4/REF decision is recomputed.
"""
from __future__ import annotations
import argparse,json
from hashlib import sha256
from pathlib import Path
from scripts.arena_r4_pt07_t2_collect import extract
from scripts.arena_r4_pt07_t2_score import score_verified_lock
from scripts.arena_r4_pt07_t2_adjudicate import adjudicate,CERT
from scripts.arena_r4_pt07_t2_one_world import SHA,prepare
from scripts.arena_r3_pt06_t23_preregister import freeze,guard
from scripts.arena_v0_contract import canonical,digest

def sha(path):return "sha256:"+sha256(Path(path).read_bytes()).hexdigest()

def audit(root,prior,lock,catalog):
    root,prior,lock=map(Path,(root,prior,lock))
    cert=json.loads(Path(CERT).read_text())
    locked=lock/"forecast-lock.json"
    guard(sha(locked)==SHA==cert["frozen_forecast_file_sha256"] and
          (lock/"forecast-lock.sha256").read_text().strip()==SHA and
          cert["chosen_observation_time_hours"]==1,
          "R4_POSTONLY_IMMUTABLE_FORECAST_NOT_ORIGINAL")
    native=root/"one-world.mos"
    budget=json.loads((root/"budget.json").read_text())
    guard(native.read_text().count("simulate(")==1 and
          budget["world_simulate_max"]==1 and
          budget["candidate_simulate_max"]==0 and
          budget["provider_inference_max"]==0 and
          budget["automatic_retry_max"]==0 and
          sha(native)==budget["solver_program_sha256"],
          "R4_POSTONLY_ONE_SIMULATE_BUDGET_CHANGED")
    guard(len(list(root.rglob("*_res.csv")))==1,
          "R4_POSTONLY_EXTRA_PHYSICAL_SOLVER_CSV")
    # Physical G2 and historic T2 generator exact identity replay.
    reconstructed_obs,reconstructed_private=extract(root,prior,lock,catalog)
    obsfile=root/"one-new-physical-observation.json"
    guard(json.loads(obsfile.read_text())==reconstructed_obs and
          reconstructed_obs["time_hours"]==1 and
          reconstructed_obs["forecast_lock_file_sha256"]==SHA,
          "R4_POSTONLY_NEW_PHYSICAL_OBSERVATION_CHANGED")
    privfile=root/"new-world/source-provenance-PRIVATE.json"
    guard(json.loads(privfile.read_text())==reconstructed_private,
          "R4_POSTONLY_WORLD_PROVENANCE_CHANGED")
    # Recompute read-only decision BEFORE viewing private generator truth.
    recalculated=score_verified_lock(locked,lock/"forecast-lock.sha256",obsfile,CERT)
    scoringfile=root/"locked-scoring-result.json"
    guard(json.loads(scoringfile.read_text())==recalculated,
          "R4_POSTONLY_LOCKED_SCORING_RESULT_CHANGED")
    post=adjudicate(root,lock)
    guard(json.loads((root/"post-selection-adjudication.json").read_text())==post,
          "R4_POSTONLY_GRADING_AFTER_SELECTION_CHANGED")
    guard(recalculated["structures_before"]==["C00","C01","C02"] and
          recalculated["structures_after"]==["C01"] and
          recalculated["structural_result"]=="ONE_STRUCTURE_SURVIVES_CONDITIONALLY" and
          recalculated["forecast_beats_REF_in_abs_error"] is True and
          post["unique_generating_structure_if_any"] is True,
          "R4_POSTONLY_ORIGINAL_RESULT_DRIFT")
    return {
       "schema":"igc-arena-r4-a-t2-one-physical-original-postonly-audit/0.1",
       "original_real_world_actions_run":40618493022,
       "frozen_original_forecast_sha256":SHA,
       "native_solver_command_sha256":sha(native),
       "native_generator_model_sha256":sha(root/"ArenaR3T23Worlds-ORIGINAL.mo"),
       "new_physical_csv_sha256":reconstructed_obs["physical_solver_csv_sha256"],
       "original_observation_file_sha256":sha(obsfile),
       "original_scoring_file_sha256":sha(scoringfile),
       "original_postselection_file_sha256":sha(root/"post-selection-adjudication.json"),
       "original_T2_early_replay_max_abs_delta":reconstructed_private["early_four_points_max_abs_delta_items"],
       "G2_residual":reconstructed_private["maximum_material_balance_residual_items"],
       "locked_evaluation":recalculated,
       "synthetic_adjudication":post,
       "extra_solver_calls_this_audit":0,
       "extra_provider_calls_this_audit":0,
       "new_parameter_fits_this_audit":0,
       "independent_external_holdout":"NOT_ESTABLISHED",
       "status":"R4_T2_REAL_PROSPECTIVE_RESULT_REPRODUCED_POSTONLY"}

def main():
    p=argparse.ArgumentParser()
    for name in ("root","original-t23","lock","catalog","out"):
        p.add_argument("--"+name,required=True,type=Path)
    a=p.parse_args()
    guard(not a.out.exists(),"R4_POSTONLY_OUTPUT_ALREADY_EXISTS")
    r=audit(a.root,a.original_t23,a.lock,json.loads(a.catalog.read_text()))
    a.out.write_bytes(canonical(r)+b"\n")
    print(json.dumps({"status":r["status"],
       "observation":r["locked_evaluation"]["new_world_delivered_items"],
       "survivors":r["locked_evaluation"]["surviving_structure_classes"],
       "surviving_configurations":len(r["locked_evaluation"]["surviving_candidate_ids"]),
       "absolute_R4_error":r["locked_evaluation"]["prediction_point_abs_error_items"],
       "absolute_REF_error":r["locked_evaluation"]["REF_abs_error_items"],
       "solver_calls_in_audit":0},sort_keys=True))
if __name__=="__main__":
    main()
