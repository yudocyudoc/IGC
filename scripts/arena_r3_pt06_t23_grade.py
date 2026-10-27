"""R3 PT-06 / STR-03: post-selection grading of two real worlds.

This is only invoked AFTER both original M3 + R3 decisions have been saved.
The two protected generator labels are never inputs to the selectors.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from scripts.arena_r3_pt06_t23_preregister import freeze,guard
from scripts.arena_r3_pt06_t23_evaluate import validate_case
from scripts.arena_v0_contract import canonical,digest

SCHEMA="igc-arena-r3-t23-physical-adjudication/0.1"

def grade(root):
    root=Path(root)
    protocol,_,_=freeze()
    guard(json.loads((root/"protocol.json").read_text())==protocol,
          "R3_T23_PROTOCOL_CHANGED_DURING_GRADING")
    sealed=json.loads((root/"researcher-private/provenance-sealed.json").read_text())
    guard(sealed["not_selector_input"] is True and len(sealed["worlds"])==2,
          "R3_T23_PRIVATE_WORLD_PROVENANCE_MISSING")
    outputs=[]
    for i in (2,3):
        case=json.loads((root/f"t{i}-construction-only.json").read_text())
        decision=json.loads((root/f"t{i}-decision.json").read_text())
        truth=sealed["worlds"][i-2]
        validate_case(case,protocol)
        guard(case["case_id"]==decision["case_id"]==truth["case_id"] and
              decision["case_sha256"]==truth["case_sha256"]==digest(case)
              and decision["original_candidate_run_id"]==40578550337
              and decision["original_csvs_reused"]==27 and
              decision["new_candidate_solver_calls"]==0 and
              decision["new_world_solver_calls_by_evaluator"]==0 and
              decision["synthetic_generator_truth_used"] is False and
              decision["future_R4_holdout_accessed"] is False,
              "R3_T23_SELECTION_PROVENANCE_INVALID")
        compatible=decision["compatible_material_classes"]
        origin=truth["true_world_material_class"]
        outputs.append({
          "case_id":case["case_id"],
          "case_sha256":digest(case),
          "predeclared_question":protocol["case_protocols"][i-2]["question"],
          "actual_source_structure_REVEALED_AFTER_SELECTION":origin,
          "actual_source_parameter_changes_REVEALED_AFTER_SELECTION":
              truth["true_world_changed_response_times"],
          "world_csv_sha256":truth["actual_solver_csv_sha256"],
          "world_physical_G2":truth["physical_G2"],
          "world_max_material_balance_residual":truth["material_balance_max"],
          "observations":case["construction_observations"],
          "original_M3_status":decision["frozen_m3_original_policy"]["status"],
          "original_M3_reason":decision["frozen_m3_original_policy"]["reason"],
          "original_M3_parent":decision["frozen_m3_original_policy"]["chosen_id"],
          "R3_grid_decision":decision["status"],
          "R3_compatible_structures":compatible,
          "R3_per_structure_best":decision["per_structure_best"],
          "source_structure_in_compatible_set":origin in compatible,
          "observational_ambiguity_in_grid":len(compatible)>=2,
          "finite_grid_incompatibility":len(compatible)==0,
          "truth_not_used_for_selection":True,
          "generalized_structure_identification":"NOT_ESTABLISHED"
        })
    return {"schema":SCHEMA,
            "protocol_sha256":digest(protocol),
            "physical_worlds":2,
            "reused_original_candidate_G2_CSVs":27,
            "candidate_simulations_in_this_experiment":0,
            "new_provider_calls":0,
            "R4_holdout":"NOT_ACCESSED",
            "cases":outputs,
            "epistemic_limit":"ONLY_FINITE_GRID_AND_DECLARED_OBSERVATION_WINDOWS"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    a=p.parse_args()
    dst=a.root/"post-selection-adjudication.json"
    guard(not dst.exists(),"R3_T23_ALREADY_GRADED")
    out=grade(a.root)
    dst.write_bytes(canonical(out)+b"\n")
    for x in out["cases"]:
        print(json.dumps({"case_id":x["case_id"],
          "fixed_M3":x["original_M3_status"],
          "R3":x["R3_grid_decision"],
          "compatible":x["R3_compatible_structures"],
          "minima":x["R3_per_structure_best"]},sort_keys=True))

if __name__=="__main__":
    main()
