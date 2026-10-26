"""M3 independent world-observation extraction and post-selection adjudication.

Never imports or changes the selector's ranking. The sealed evaluator key is
read only here, after candidate simulations. Hidden truth is in grading/,
while selector CLI has no parameter for grading/ or world simulations.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

from scripts.arena_m3_prepare import (family, CASE_IDS, CONSTRUCTION_TIMES,
    RESERVED_TIMES, CONSTRUCTION_NOISE, RESERVED_NOISE, require)
from scripts.arena_m3_select import model_rows, sample, validate_manifest, validate_case
from scripts.arena_v0_contract import canonical, digest


def extract(folder):
    manifest=json.loads((folder/"candidate-manifest.json").read_text())
    candidates=validate_manifest(manifest)
    truth=json.loads((folder/"grading"/"sealed-source-key.json").read_text())
    require(truth.get("schema")=="igc-m3-sealed-source-labels/0.1"
            and truth.get("not_selector_input") is True
            and len(truth.get("cases",[]))==2,
            "M3_INVALID_SEALED_KEY")
    cfg,classes,paths=family()
    for i,(target,known) in enumerate(zip(truth["cases"],CASE_IDS)):
        require(target["case_id"]==known and target["world_class"]==f"M3W{i:02d}"
                and target["expected_candidate_id"]==f"C{i:02d}"
                and target["source_canonical_sha256"]==candidates[i]["canonical_sha256"],
                "M3_EVALUATOR_KEY_TAMPERED")
        rows=model_rows(folder/"worlds"/f"w{i:02d}_res.csv")
        times=CONSTRUCTION_TIMES+RESERVED_TIMES
        all_delivered=sample(rows,times)
        noisy=[max(0.0,v+n) for v,n in zip(all_delivered,
                    CONSTRUCTION_NOISE+RESERVED_NOISE)]
        construction=[
            {"t":t,"delivered":float(y)} for t,y in zip(CONSTRUCTION_TIMES,noisy[:4])]
        reserved=[
            {"t":t,"delivered":float(y)} for t,y in zip(RESERVED_TIMES,noisy[4:])]
        case={
            "schema":"igc-arena-m3-blind-construction-case/0.1",
            "case_id":known,
            "construction_observations":construction,
            "source_snapshot_hash":"sha256:"+digest(construction)[7:],
            "synthetic_measurement":True,
            "observability":"cumulative_delivered_items",
        }
        validate_case(case)
        (folder/"cases"/(known+".json")).write_bytes(canonical(case)+b"\n")
        (folder/"grading"/(known+"-reserved.json")).write_bytes(canonical({
            "schema":"igc-arena-m3-temporal-reserved/0.1",
            "case_id":known,"reserved_observations":reserved,
            "not_seen_by_selector":True,
            "same_synthetic_run_later_times_not_independent_field":True,
        })+b"\n")
    return {"status":"TWO_CONSTRUCTION_ONLY_CASES_EXTRACTED_FROM_REAL_OMC",
            "construction_points":len(CONSTRUCTION_TIMES),
            "reserved_points":len(RESERVED_TIMES),
            "sealed_key_kept_out_of_selector":True}


def grade(folder):
    truth=json.loads((folder/"grading"/"sealed-source-key.json").read_text())
    manifest=json.loads((folder/"candidate-manifest.json").read_text())
    candidates=validate_manifest(manifest)
    by_id={c["id"]:c for c in candidates}
    audit=[]
    for target in truth["cases"]:
        case_id=target["case_id"]
        decision=json.loads((folder/"cases"/(case_id+"-selection.json")).read_text())
        original=json.loads((folder/"cases"/(case_id+".json")).read_text())
        withheld=json.loads((folder/"grading"/(case_id+"-reserved.json")).read_text())
        validate_case(original)
        require(decision["case_id"]==case_id
                and decision["construction_input_sha256"]==digest(original)
                and decision["manifest_sha256"]==digest(manifest)
                and decision["used_truth_labels"] is False
                and decision["used_reserved_observations"] is False
                and decision["used_cross_arm_information"] is False,
                "M3_SELECTION_WAS_NOT_BLIND")
        require(withheld.get("not_seen_by_selector") is True
                and [x["t"] for x in withheld.get("reserved_observations",[])]==RESERVED_TIMES,
                "M3_NOT_A_RESERVE")
        selected_id=decision["chosen_id"]
        reserve_result=None
        if selected_id is not None:
            require(selected_id in by_id,"M3_FOREIGN_SELECTED_CANDIDATE")
            predicted=sample(model_rows(folder/"candidates"/(selected_id.lower()+"_res.csv")),
                             RESERVED_TIMES)
            measured=[float(x["delivered"]) for x in withheld["reserved_observations"]]
            rmse=math.sqrt(sum((p-o)**2 for p,o in zip(predicted,measured))/len(measured))
            reserve_result={"times":RESERVED_TIMES,"actual":measured,
                            "predicted":predicted,"rmse_items":rmse,
                            "evaluation":"LATER_POINTS_FROM_SAME_SYNTHETIC_RUN",
                            "not_external_real_world_holdout":True}
        audit.append({
            "case_id":case_id,
            "world_source_key":"AVAILABLE_ONLY_TO_POST_SELECTION_GRADER",
            "expected_candidate_id":target["expected_candidate_id"],
            "selected_candidate_id":selected_id,
            "selected_exact_material_path":selected_id==target["expected_candidate_id"],
            "selection_status":decision["status"],
            "construction_scores":{c["id"]:c["rmse_items"]
                                   for c in decision["scored_candidates"]},
            "reserve":reserve_result,
        })
    ids=[x["selected_candidate_id"] for x in audit]
    success=all(x["selected_exact_material_path"]
                and x["selection_status"]=="SELECTED_CONDITIONALLY"
                and x["reserve"] is not None
                and x["reserve"]["rmse_items"]<0.02 for x in audit)
    switched=(len(set(ids))==len(audit))
    result={
        "schema":"igc-arena-m3-structural-recovery-adjudication/0.1",
        "arm_id":"M","method":"FINITE_E1_FAMILY_EVIDENCE_RESPONSE",
        "cases":audit,
        "selection_switches_when_construction_observations_switch":switched,
        "recovery_under_this_closed_synthetic_family":success and switched,
        "not_parameter_fitting":True,"no_rival_arm_information":True,
        "original_E1_composer_untouched":True,
        "fixed_candidates":3,"separately_simulated_worlds":2,
        "technical_status":"G2_PASS_IF_EACH_REAL_CSV_EXISTS_AND_CONSERVES",
        "g3_construction":"DESCRIPTIVE_AND_PREREGISTERED_ABSTENTION_RULE",
        "reserved_status":"TEMPORAL_WITHHELD_IN_SAME_SYNTHETIC_WORLD_ONLY",
        "not_external_validation":True,
        "not_identification_of_unnamed_real_causal_world":True,
    }
    (folder/"grading"/"final-adjudication.json").write_bytes(canonical(result)+b"\n")
    return result


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("command",choices=("extract","grade"))
    ap.add_argument("--dir",required=True,type=Path)
    a=ap.parse_args()
    if a.command=="extract":
        print(json.dumps(extract(a.dir)))
    else:
        outcome=grade(a.dir)
        print(json.dumps({"recovery":outcome["recovery_under_this_closed_synthetic_family"],
                          "switched":outcome["selection_switches_when_construction_observations_switch"],
                          "scores":outcome["cases"]}))


if __name__=="__main__":main()
