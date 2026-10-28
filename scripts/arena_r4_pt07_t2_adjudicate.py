"""R4 PT-07 post-only adjudication; scoring precedes private world identity."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from scripts.arena_r4_pt07_t2_score import score_verified_lock
from scripts.arena_r4_pt07_t2_forecast import guard
from scripts.arena_v0_contract import canonical,digest

CERT="data/diagnostics/ARENA_R4_PT07_T2_FROZEN_FORECAST_CERTIFICATE_20261027.json"

def evaluate_to_file(root,lock):
    root,lock=Path(root),Path(lock)
    dst=root/"locked-scoring-result.json"
    guard(not dst.exists(),"R4_PHYSICAL_SCORE_ALREADY_EXISTS")
    result=score_verified_lock(lock/"forecast-lock.json",
        lock/"forecast-lock.sha256",root/"one-new-physical-observation.json",CERT)
    dst.write_bytes(canonical(result)+b"\n")
    return result

def adjudicate(root,lock):
    root,lock=Path(root),Path(lock)
    scored_file=root/"locked-scoring-result.json"
    guard(scored_file.exists(),"R4_WORLD_TRUTH_CANNOT_BE_OPENED_BEFORE_SCORING")
    earlier=json.loads(scored_file.read_text())
    replay=score_verified_lock(lock/"forecast-lock.json",
        lock/"forecast-lock.sha256",root/"one-new-physical-observation.json",CERT)
    guard(earlier==replay,"R4_SCORE_NOT_REPRODUCIBLE_AFTER_LOCK")
    private=json.loads((root/"new-world/source-provenance-PRIVATE.json").read_text())
    case=json.loads((root/"one-new-physical-observation.json").read_text())
    guard(private["new_physical_observation_sha256"]==digest(case) and
          private["physical_G2"]=="G2_SIMULATED_CONDITIONALLY"
          and private["world_time_after_1h_not_simulated"] is True and
          private["synthetic_generating_class_REVEAL_AFTER_SCORING"]=="C01",
          "R4_SOURCE_INTEGRITY_OR_SEPARATE_ADJUDICATION_FAILED")
    true_label=private["synthetic_generating_class_REVEAL_AFTER_SCORING"]
    surviving=earlier["surviving_structure_classes"]
    result={
       "schema":"igc-arena-r4-pt07-t2-post-selection-synthetic-adjudication/0.1",
       "case_id":case["case_id"],
       "locked_score_sha256":digest(earlier),
       "source_revealed_ONLY_AFTER_selection":true_label,
       "generating_structure_retained":true_label in surviving,
       "unique_generating_structure_if_any":surviving==[true_label],
       "prior_structure_count":len(earlier["structures_before"]),
       "posterior_structure_count":len(surviving),
       "predictive_outcome":earlier["structural_result"],
       "R3_policy_unchanged":True,
       "new_parameter_fit_calls":0,
       "new_provider_calls":0,
       "external_independence":"NONE_SYNTHETIC_SHARED_FAMILY",
       "causal_identification":"NOT_ESTABLISHED"}
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--lock",type=Path,required=True)
    p.add_argument("--phase",choices=("score","adjudicate"),required=True)
    a=p.parse_args()
    if a.phase=="score":
        result=evaluate_to_file(a.root,a.lock)
        print(json.dumps({"phase":"SCORED_WITHOUT_GENERATOR_TRUTH",
          "status":result["structural_result"],
          "structures_after":result["structures_after"],
          "error_items":result["prediction_point_abs_error_items"],
          "REF_error_items":result["REF_abs_error_items"]},sort_keys=True))
    else:
        out=a.root/"post-selection-adjudication.json"
        guard(not out.exists(),"R4_POST_SELECTION_ADJUDICATION_ALREADY_EXISTS")
        result=adjudicate(a.root,a.lock)
        out.write_bytes(canonical(result)+b"\n")
        print(json.dumps({"phase":"SYNTHETIC_TRUTH_REVEALED_AFTER_SCORING",**result},sort_keys=True))

if __name__=="__main__":
    main()
