"""R3 PT-06 future evaluator for 27 real candidate CSVs (zero solver invocation).

Accept ONLY construction measurements and original E1 G2-verified candidate
series. Never ingest generator graph, truth label, reserve times or D/B models.
No candidate CSV exists in this preflight; R3 scoring is not claimed yet.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
import math
from pathlib import Path

from scripts.arena_m3_select import model_rows,sample
from scripts.arena_m_visible_verify import verify
from scripts.arena_r3_pt06_parametric import (
    SCHEMA,PACKAGE,CONSTRUCTION_TOLERANCE,classify,plan,guard)
from scripts.arena_v0_contract import canonical,digest

CASE_SCHEMA="igc-arena-r3-m-construction-only/0.1"

def checked_case(data,manifest):
    guard(isinstance(data,dict) and set(data)=={
        "schema","case_id","observability","public_stimulus","construction_observations",
        "measurement_bound_status","source_snapshot_hash","synthetic_case"},
        "R3_CASE_CONTAINS_TRUTH_OR_HOLDOUT")
    guard(data["schema"]==CASE_SCHEMA and
          data["case_id"]=="R3-T1-SHIFTED-REPRESENTABLE" and
          data["synthetic_case"] is True and
          data["observability"]=="deliveredTotal" and
          data["measurement_bound_status"]=="NO_INSTRUMENT_BOUND",
          "R3_CASE_NOT_FIRST_CONSTRUCTION_ONLY")
    guard(data["public_stimulus"]=={
        "kind":"pulse","rate":1.7,"duration":2.0},
        "R3_STIMULUS_NOT_PREREGISTERED")
    obs=data["construction_observations"]
    guard(isinstance(obs,list) and len(obs)==4 and
          [x.get("t") for x in obs]==[0,1,2,3] and
          all(set(x)=={"t","delivered"} and
              type(x["delivered"]) in (int,float) and
              math.isfinite(x["delivered"]) and x["delivered"]>=0
              for x in obs),
          "R3_CONSTRUCTION_TIMES_OR_VALUES_CHANGED")
    guard(isinstance(data["source_snapshot_hash"],str) and
          data["source_snapshot_hash"].startswith("sha256:"),
          "R3_SOURCE_HASH_MISSING")
    return obs


def evaluate_csv(manifest,case,csv_root,catalog):
    # Validate entire preregistration, not just a method flag.
    declared,expected_package=plan()
    guard(manifest==declared,"R3_UNDECLARED_SEARCH_OR_CANDIDATE_CHANGE")
    obs=checked_case(case,manifest)
    csv_root=Path(csv_root)
    package=csv_root/(PACKAGE+".mo")
    guard(package.is_file() and package.read_bytes()==expected_package.encode(),
          "R3_REPLAY_PACKAGE_BYTES_CHANGED")
    visible={"construction":{"input_profile":{"kind":"pulse","rate":1.7,"duration":2.0},
                             "observations":obs}}
    measured=[x["delivered"] for x in obs]
    scores=[]
    for c in manifest["candidates"]:
        ident=c["id"].lower()
        # Only class prefix chosen by pinned .mos protocol; no path from case input.
        path=csv_root/"candidates"/(ident+"_res.csv")
        guard(path.is_file(),"R3_CANDIDATE_CSV_MISSING:"+ident)
        rows=model_rows(path)
        check=verify(rows,visible,{"arm_id":"M",
            "method":"short-e1-one-minimal-molecular-candidate/0.1",
            "graph":c["graph"]},catalog)
        guard(check["status"]=="G2_SIMULATED_CONDITIONALLY" and
              check["max_material_balance_residual"]<=0.015 and
              check["g3_construction_status"]=="DESCRIPTIVE_ONLY_NO_INSTRUMENT_BOUND",
              "R3_REAL_G2_MATERIAL_CHECK_FAILED")
        preds=sample(rows,[x["t"] for x in obs])
        rmse=math.sqrt(sum((p-o)**2 for p,o in zip(preds,measured))/len(obs))
        scores.append({"id":c["id"],"rmse_items":rmse,
                       "csv_sha256":"sha256:"+sha256(path.read_bytes()).hexdigest(),
                       "g2_status":check["status"]})
    decision=classify(scores,manifest)
    return {**decision,"case_id":case["case_id"],"case_source_hash":case["source_snapshot_hash"],
            "manifest_sha256":digest(manifest),
            "source_kind":"FOUR_CONSTRUCTION_OBSERVATIONS_ONLY",
            "raw_real_solver_csv_checks":len(scores),
            "new_solver_calls_by_this_evaluator":0,
            "truth_labels_used":False,"reserved_times_used":False,
            "claim":"BOUNDED_FINITE_GRID_COMPATIBILITY_NOT_UNIVERSAL_IDENTIFICATION"}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--case",type=Path,required=True)
    p.add_argument("--csv-root",type=Path,required=True)
    p.add_argument("--catalog",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    guard(not a.out.exists(),"R3_EXISTING_EVALUATION_REPORT")
    result=evaluate_csv(json.loads(a.manifest.read_text()),json.loads(a.case.read_text()),
                        a.csv_root,json.loads(a.catalog.read_text()))
    a.out.write_bytes(canonical(result)+b"\n")
    print(json.dumps({"status":result["status"],"compatible":result["compatible_material_classes"],
                      "solver_csv_verified":result["raw_real_solver_csv_checks"],
                      "new_evaluator_solver_calls":0}))

if __name__=="__main__":
    main()
