"""M3 evidence-based structural selector, blind to the generating graphs.

Only accepts (a) the public E1 candidate manifest, (b) construction-only
observations, (c) candidate OMC CSVs. It NEVER reads world CSV, source labels,
or reserve observations. Structural selection != parameter calibration.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
from pathlib import Path

from scripts.arena_m3_prepare import (TRIAL, CONSTRUCTION_TIMES, INPUT_PROFILE,
    CONSTRUCTION_NOISE, RESERVED_TIMES, RESERVED_NOISE, CASE_IDS, require)
from scripts.arena_m_visible_pulse import ROOT, composer, REGISTRY
from scripts.arena_m_visible_verify import get, verify
from scripts.arena_v0_contract import canonical, digest


def model_rows(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))
    require(len(rows)>=70,"M3_INSUFFICIENT_REAL_OMC_ROWS")
    return rows


def sample(rows, times):
    values=[]
    for t in times:
        hit=[r for r in rows if abs(get(r,"time")-t)<1e-7]
        require(len(hit)==1,"M3_MISSING_OR_DUPLICATE_SOLVER_TIME")
        values.append(get(hit[0],"deliveredTotal"))
    return values


def validate_manifest(manifest):
    require(manifest.get("schema")==TRIAL and manifest.get("arm_id")=="M",
            "M3_WRONG_CANDIDATE_MANIFEST")
    require(manifest.get("candidate_simulations")==3
            and manifest.get("world_simulations")==2
            and manifest.get("universe_count")==6
            and manifest.get("observable_equivalence_classes")==3
            and manifest.get("candidate_parameter_fitting") is False
            and manifest.get("upstream_edited") is False
            and manifest.get("stimulus")==INPUT_PROFILE
            and manifest.get("construction_times")==CONSTRUCTION_TIMES
            and manifest.get("reserve_times")==RESERVED_TIMES
            and manifest.get("construction_noise")==CONSTRUCTION_NOISE
            and manifest.get("reserve_noise")==RESERVED_NOISE
            and manifest.get("predeclared_max_best_rmse_items")==0.02
            and manifest.get("predeclared_min_gap_rmse_items")==0.035,
            "M3_PROTOCOL_NOT_PREREGISTERED")
    cfg,classes,_=composer.load_registry(REGISTRY)
    require(manifest.get("registry_sha256")==digest(cfg),"M3_REGISTRY_DRIFT")
    candidates=manifest.get("candidates")
    require(isinstance(candidates,list) and len(candidates)==3,"M3_CANDIDATE_COUNT")
    require([x.get("id") for x in candidates]==["C00","C01","C02"],
            "M3_CANDIDATE_ID_DRIFT")
    for i,c in enumerate(candidates):
        composer.check_graph(c["graph"],cfg,classes)
        require(c["canonical_sha256"]=="sha256:"+composer.canonical(c["graph"]),
                "M3_UNTRUSTED_CANDIDATE_GRAPH")
        require(c["transit_instances"]==i and c["material_queues"]==2+i,
                "M3_PATH_COUNT_DRIFT")
        require(all(x["parameters"]==cfg["roles"][x["role"]]["parameters"]
                    for x in c["graph"]["instances"]), "M3_UNAUTHORIZED_PARAM_CHANGE")
    return candidates


def validate_case(case):
    require(set(case)=={"schema","case_id","construction_observations",
                        "source_snapshot_hash","synthetic_measurement","observability"}
            and case["schema"]=="igc-arena-m3-blind-construction-case/0.1"
            and case["case_id"] in CASE_IDS
            and case["synthetic_measurement"] is True
            and case["observability"]=="cumulative_delivered_items"
            and isinstance(case["source_snapshot_hash"],str)
            and case["source_snapshot_hash"].startswith("sha256:"),
            "M3_CASE_NOT_BLIND_OR_UNRECOGNIZED")
    obs=case["construction_observations"]
    require(isinstance(obs,list) and len(obs)==len(CONSTRUCTION_TIMES)
            and [x.get("t") for x in obs]==CONSTRUCTION_TIMES
            and all(set(x)=={"t","delivered"} and
                    type(x["delivered"]) in (float,int) and
                    math.isfinite(x["delivered"]) and
                    x["delivered"]>=0 for x in obs),
            "M3_INVALID_OBSERVATIONS")
    return [float(x["delivered"]) for x in obs]


def decide(scored, min_gap=0.035,max_best=0.02):
    require(len(scored)==3 and all(math.isfinite(x["rmse_items"]) for x in scored),
            "M3_INVALID_CANDIDATE_SCORES")
    ordered=sorted(scored,key=lambda x:(x["rmse_items"],x["material_queues"],x["id"]))
    best=ordered[0];margin=ordered[1]["rmse_items"]-best["rmse_items"]
    if best["rmse_items"]>max_best:
        return {"status":"ABSTAIN","reason":"ALL_FIXED_E1_STRUCTURES_MISS_CONSTRUCTION_TOLERANCE",
                "chosen_id":None,"margin":margin}
    if margin<min_gap:
        return {"status":"ABSTAIN","reason":"OBSERVATIONS_DO_NOT_DISCRIMINATE_FIXED_E1_PATHS",
                "chosen_id":None,"margin":margin}
    return {"status":"SELECTED_CONDITIONALLY","reason":"LOWEST_CONSTRUCTION_RMSE_WITH_PREREGISTERED_GAP",
            "chosen_id":best["id"],"margin":margin}


def select_case(manifest,case,folder,catalog):
    candidates=validate_manifest(manifest)
    obs=validate_case(case)
    scored=[]
    seen_paths=set()
    for c in candidates:
        path=folder/"candidates"/(c["id"].lower()+"_res.csv")
        rows=model_rows(path)
        # The original M verifier is reused for stock conservation; the M3
        # method is structurally checked against E1 above, so provide a
        # compatibility native wrapper solely to call its unchanged G2 probe.
        visible={"construction":{
            "input_profile":INPUT_PROFILE,
            "observations":case["construction_observations"]}}
        v=verify(rows,visible,{"arm_id":"M",
            "method":"short-e1-one-minimal-molecular-candidate/0.1",
            "graph":c["graph"]},catalog)
        require(v["status"]=="G2_SIMULATED_CONDITIONALLY"
                and v["max_material_balance_residual"]<=0.015,"M3_CANDIDATE_G2_FAILED")
        pred=sample(rows,CONSTRUCTION_TIMES)
        rmse=math.sqrt(sum((p-o)**2 for p,o in zip(pred,obs))/len(obs))
        scored.append({"id":c["id"],"canonical_sha256":c["canonical_sha256"],
                       "material_queues":c["material_queues"],
                       "predicted_construction":pred,"rmse_items":rmse,
                       "max_material_balance":v["max_material_balance_residual"],
                       "actual_solver_samples":v["technical_samples"],
                       "parameters_fitted":False})
        require(c["canonical_sha256"] not in seen_paths,"M3_DUPLICATE_PATH")
        seen_paths.add(c["canonical_sha256"])
    outcome=decide(scored,manifest["predeclared_min_gap_rmse_items"],
                   manifest["predeclared_max_best_rmse_items"])
    return {
        "schema":"igc-arena-m3-evidence-structural-selection/0.1",
        "arm_id":"M","case_id":case["case_id"],
        "construction_input_sha256":digest(case),
        "manifest_sha256":digest(manifest),
        "selection_read_only":"CONSTRUCTION_OBSERVATIONS_AND_CANDIDATE_OMC_TRACES",
        "used_truth_labels":False,"used_reserved_observations":False,
        "used_cross_arm_information":False,
        "method":"ORIGINAL_E1_THREE_FIXED_MATERIAL_TOPOLOGIES_RMSE_WITH_ABSTENTION",
        "status":outcome["status"],"reason":outcome["reason"],
        "chosen_id":outcome["chosen_id"],
        "score_margin_items":outcome["margin"],
        "score_denominator":len(obs),
        "scored_candidates":scored,
        "claim":"FINITE_CATALOG_RECOVERY_ONLY_NOT_REAL_WORLD_STRUCTURE_IDENTIFICATION"
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--case",type=Path,required=True)
    p.add_argument("--csv-root",type=Path,required=True)
    p.add_argument("--catalog",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    require(not a.out.exists(),"M3_SELECTION_OUTPUT_ALREADY_EXISTS")
    # Select module never opens worlds/, grading/, truth or reserved files.
    public=json.loads(a.manifest.read_text())
    case=json.loads(a.case.read_text())
    catalog=json.loads(a.catalog.read_text())
    result=select_case(public,case,a.csv_root,catalog)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_bytes(canonical(result)+b"\n")
    print(json.dumps({"case":result["case_id"],"selection":result["chosen_id"],
                      "status":result["status"],
                      "gap":result["score_margin_items"],
                      "scores":{x["id"]:round(x["rmse_items"],6)
                                for x in result["scored_candidates"]}}))


if __name__=="__main__":main()
