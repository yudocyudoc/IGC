"""Read-only T2/T3 structural compatibility over archived 27 real R3-T1 CSVs.

No world generator, source parameters, R4 holdout, or D/B evidence is accepted.
Every original candidate CSV is required and re-verified with M's G2 mass
balance before construction errors and original M3 policy are calculated.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path

from scripts.arena_m3_select import model_rows,sample
from scripts.arena_m_visible_verify import verify
from scripts.arena_r3_pt06_parametric import plan,classify,guard
from scripts.arena_r3_pt06_t23_preregister import freeze,ORIGINAL_GRID_SHA,SCHEMA
from scripts.arena_v0_contract import canonical,digest

CASE_SCHEMA="igc-arena-r3-t23-m-construction-only/0.1"

def validate_case(case,protocol):
    guard(type(case) is dict and set(case)=={
        "schema","case_id","observability","public_stimulus",
        "construction_observations","measurement_bound_status",
        "source_snapshot_hash","synthetic_case"},
        "R3_T23_CASE_CONTAINS_TRUTH_OR_RESERVED_DATA")
    guard(case["schema"]==CASE_SCHEMA and case["synthetic_case"] is True
          and case["observability"]=="deliveredTotal"
          and case["measurement_bound_status"]=="NO_INSTRUMENT_BOUND"
          and case["public_stimulus"]=={
             "kind":"pulse","rate":1.7,"duration":2.0},
          "R3_T23_INVALID_CONSTRUCTION_CASE")
    byid={x["case_id"]:x for x in protocol["case_protocols"]}
    guard(case["case_id"] in byid and len(byid)==2,
          "R3_T23_CASE_NOT_PREDECLARED")
    times=byid[case["case_id"]]["public_observation_times_hours"]
    observations=case["construction_observations"]
    guard(type(observations) is list and len(observations)==4 and
          [x.get("t") for x in observations]==times and
          all(type(x) is dict and set(x)=={"t","delivered"} and
              type(x["delivered"]) in (float,int) and
              math.isfinite(x["delivered"]) and x["delivered"]>=0
              for x in observations),
          "R3_T23_CONSTRUCTION_TIMES_CHANGED")
    guard(case["source_snapshot_hash"]==digest(observations),
          "R3_T23_OBSERVATIONS_PROVENANCE_HASH_CHANGED")
    return observations


def archived_candidates(root, protocol, catalog):
    """Validate original immutable T1 package, not a newly fitted candidate set."""
    root=Path(root)
    manifest_expected,pkg_text=plan()
    manifest=json.loads((root/"manifest.json").read_text())
    budget=json.loads((root/"solver-budget.json").read_text())
    guard(manifest==manifest_expected and digest(manifest)==ORIGINAL_GRID_SHA,
          "R3_T23_ORIGINAL_T1_MANIFEST_CHANGED")
    guard((root/"ArenaR3Parametric.mo").read_bytes()==pkg_text.encode(),
          "R3_T23_ORIGINAL_T1_MODELICA_CHANGED")
    guard(budget["authorized_candidate_simulations"]==27 and
          budget["authorized_world_simulations"]==1 and
          budget["total_simulation_commands"]==28 and
          budget["provider_calls"]==0,
          "R3_T23_NOT_AUTHENTIC_T1_PHYSICAL_RUN")
    guard(protocol["archived_candidate_run_id"]==40578550337 and
          protocol["archived_candidate_artifact_id"]==12769310740,
          "R3_T23_CHANGED_ARCHIVE_PROVENANCE")
    guard(len(manifest["candidates"])==27,"R3_T23_CANDIDATE_COUNT_CHANGED")
    rootfiles={p.name for p in (root/"candidates").glob("*_res.csv")}
    expected={c["id"].lower()+"_res.csv" for c in manifest["candidates"]}
    guard(rootfiles==expected,"R3_T23_MISSING_EXTRA_OR_REPLACED_CSV")
    # Physical-only audit with a dummy t>0 observation (required by the
    # unchanged native verifier to define its noninitial RMSE). Neither dummy
    # value nor its descriptive RMSE participates in T2/T3 case scoring.
    verification={"construction":{"input_profile":{"kind":"pulse","rate":1.7,"duration":2.0},
      "observations":[{"t":0,"delivered":0.0},{"t":1,"delivered":0.0}]}}
    all_rows={}
    index=[]
    for candidate in manifest["candidates"]:
        f=root/"candidates"/(candidate["id"].lower()+"_res.csv")
        rows=model_rows(f)
        checked=verify(rows,verification,{
            "arm_id":"M","method":"short-e1-one-minimal-molecular-candidate/0.1",
            "graph":candidate["graph"]},catalog)
        guard(checked["status"]=="G2_SIMULATED_CONDITIONALLY"
              and checked["max_material_balance_residual"]<=0.015
              and checked["g3_construction_status"]==
                  "DESCRIPTIVE_ONLY_NO_INSTRUMENT_BOUND",
              "R3_T23_ARCHIVED_CSV_FAILED_G2")
        all_rows[candidate["id"]]=rows
        index.append({"id":candidate["id"],
          "sha256":"sha256:"+sha256(f.read_bytes()).hexdigest(),
          "max_material_balance_residual":checked["max_material_balance_residual"]})
    return manifest,all_rows,index


def evaluate(protocol,case,root,catalog):
    guard(protocol==freeze()[0] and
          protocol["phase"]=="PREDECLARED_NO_SIMULATION",
          "R3_T23_PROTOCOL_OR_THRESHOLD_DRIFT")
    obs=validate_case(case,protocol)
    manifest,rows_by_id,index=archived_candidates(root,protocol,catalog)
    times=[x["t"] for x in obs]
    values=[x["delivered"] for x in obs]
    sha={x["id"]:x["sha256"] for x in index}
    scores=[]
    for candidate in manifest["candidates"]:
        pred=sample(rows_by_id[candidate["id"]],times)
        rmse=math.sqrt(sum((p-y)**2 for p,y in zip(pred,values))/len(times))
        scores.append({"id":candidate["id"],"rmse_items":rmse,
                       "csv_sha256":sha[candidate["id"]],
                       "g2_status":"G2_SIMULATED_CONDITIONALLY"})
    decision=classify(scores,manifest)
    return {**decision,
       "case_id":case["case_id"],"case_sha256":digest(case),
       "protocol_sha256":digest(protocol),
       "original_candidate_run_id":40578550337,
       "original_candidate_artifact_id":12769310740,
       "original_csvs_reused":27,"new_candidate_solver_calls":0,
       "new_world_solver_calls_by_evaluator":0,
       "original_candidate_csv_index":index,
       "score_input_times_hours":times,
       "synthetic_generator_truth_used":False,
       "future_R4_holdout_accessed":False,
       "conclusion_scope":"FINITE_GRID_AND_PREDECLARED_TIMES_ONLY",
       "predicted_ambiguity_or_incompatibility_not_guaranteed":True}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--protocol",type=Path,required=True)
    p.add_argument("--case",type=Path,required=True)
    p.add_argument("--original-t1-root",type=Path,required=True)
    p.add_argument("--catalog",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    guard(not a.out.exists(),"R3_T23_DECISION_FILE_ALREADY_EXISTS")
    result=evaluate(json.loads(a.protocol.read_text()),
       json.loads(a.case.read_text()),a.original_t1_root,
       json.loads(a.catalog.read_text()))
    a.out.write_bytes(canonical(result)+b"\n")
    print(json.dumps({"status":result["status"],"compatible":result["compatible_material_classes"],
        "original_real_csvs":result["original_csvs_reused"],
        "new_solver_calls":0},sort_keys=True))

if __name__=="__main__":
    main()
