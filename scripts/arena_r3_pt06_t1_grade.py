"""Post-selection audit of R3-T1: evaluator truth disclosed only AFTER scoring."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from scripts.arena_r3_pt06_parametric import CASE_PLAN,guard
from scripts.arena_r3_pt06_evaluate import checked_case
from scripts.arena_v0_contract import canonical,digest


def grade(case,decision,private):
    guard(decision["case_id"]==case["case_id"]==CASE_PLAN["case_id"] and
          decision["case_source_hash"]==case["source_snapshot_hash"] and
          private["construction_case_sha256"]==digest(case) and
          decision["raw_real_solver_csv_checks"]==27 and
          decision["new_solver_calls_by_this_evaluator"]==0 and
          decision["truth_labels_used"] is False and
          decision["reserved_times_used"] is False,
          "R3_T1_INVALID_POST_SELECTION_GRADING_LINEAGE")
    origin=private["world_material_topology"]
    compatible=decision["compatible_material_classes"]
    result={
       "schema":"igc-arena-r3-t1-post-selection-adjudication/0.1",
       "case_id":case["case_id"],
       "world_class_declared_pre_run":origin,
       "world_responseTime_hours_declared_pre_run":private["world_responseTime_hours"],
       "candidate_parameter_grid_excludes_true_world_values":True,
       "frozen_original_m3_status":decision["frozen_m3_original_policy"]["status"],
       "frozen_original_m3_chosen_id":decision["frozen_m3_original_policy"]["chosen_id"],
       "bounded_r3_status":decision["status"],
       "bounded_r3_compatible_material_classes":compatible,
       "world_class_in_compatible_set":origin in compatible,
       "conditional_uniqueness_in_grid":len(compatible)==1 and compatible==[origin],
       "world_csv_sha256":private["original_solver_csv_sha256"],
       "case_sha256":digest(case),
       "decision_sha256":digest(decision),
       "original_E1_world_only":True,
       "world_reserved_times_not_generated":True,
       "new_extra_solver_calls":0,
       "world_label_not_seen_by_selector":True,
       "causal_identification":"NOT_DEMONSTRATED",
       "independent_holdout":"NOT_RUN",
       "interpretation":"R3_FIRST_SYNTHETIC_CASE_ONLY_NOT_GENERALIZABLE"
    }
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    a=p.parse_args()
    root=a.root
    case=json.loads((root/"construction-case.json").read_text())
    decision=json.loads((root/"r3-decision.json").read_text())
    private=json.loads((root/"world-private/provenance.json").read_text())
    result=grade(case,decision,private)
    out=root/"post-selection-adjudication.json"
    guard(not out.exists(),"R3_ALREADY_ADJUDICATED")
    out.write_bytes(canonical(result)+b"\n")
    print(json.dumps({"status":"R3_T1_GRADED_AFTER_SELECTION",
                      "fixed_M3":result["frozen_original_m3_status"],
                      "r3":result["bounded_r3_status"],
                      "matched":result["world_class_in_compatible_set"],
                      "unique":result["conditional_uniqueness_in_grid"]}))
if __name__=="__main__":
    main()
