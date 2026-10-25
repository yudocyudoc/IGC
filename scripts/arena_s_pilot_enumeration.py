"""Enumerate calibrated CS-01 and CS-02 independently of the S proposal.

The baseline sees only primary construction and the public model catalogue.
It receives no S selection, draft or S simulation output. The same calibrated
models and pulse plan can then be simulated by OpenModelica in a separate folder.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .arena_round import (SCHEMA as ROUND_SCHEMA, hash_obj, exclusive_json,
                          validate_submission)
from .arena_sp_producers import ProviderError
from .fm_b2_atms_candidate_reasoning import apply_supports
from .fm_b3_dynamic_evaluation import (
    render_evaluation_modelica,render_openmodelica_script,
    assess_trace,result_prefix,class_name,digest as file_digest
)
from .arena_s_calibration import verify_calibration

PACKAGE = "ArenaEnumeratedDynamics"
SCHEMA = "igc-arena-enumeration/0.1"


def require(test:bool, message:str)->None:
    if not test:
        raise ProviderError(message)


def prepare_enumeration(base_composed:dict, composed:dict,
                        base_plan:dict, plan:dict, supports:dict,
                        fit_plan:dict, primary:dict, fit_receipt:dict,
                        out:Path)->dict:
    verify_calibration(fit_receipt,base_composed,composed,base_plan,
                       plan,fit_plan,primary)
    selection=apply_supports(composed,supports)
    expected={item["id"] for item in composed["candidates"]}
    allowed={item["candidate_id"] for item in selection["selected"]}
    require(allowed==expected and len(expected)==2
            and not selection["rejected"],"ENUMERATION_MUST_RETAIN_BOTH")
    require({item["id"] for item in plan["candidates"]}==expected,
            "ENUMERATION_PLAN_CANDIDATE_MISMATCH")
    out.mkdir(parents=True,exist_ok=False)
    mo=out/(PACKAGE+".mo")
    mos=out/"run-enumeration.mos"
    mo.write_text(render_evaluation_modelica(plan,composed,selection,
                                              package_name=PACKAGE),encoding="utf-8")
    mos.write_text(render_openmodelica_script(plan,composed,selection,
                                               package_name=PACKAGE),encoding="utf-8")
    record={
        "schema":SCHEMA,"status":"ENUMERATION_PREPARED_NOT_EXECUTED",
        "synthetic":True,"empirical_truth_evaluated":False,
        "composed_hash":hash_obj(composed),
        "plan_hash":hash_obj(plan),
        "supports_hash":hash_obj(supports),
        "fit_receipt_hash":hash_obj(fit_receipt),
        "selection_hash":hash_obj(selection),
        "candidate_ids":sorted(expected),
        "modelica_hash":file_digest(mo),"mos_hash":file_digest(mos)}
    record["record_hash"]=hash_obj(record)
    exclusive_json(out/"enumeration-plan.json",record)
    return record


def enumeration_submission(*, manifest:dict,base_composed:dict,composed:dict,
                           base_plan:dict,plan:dict,fit_plan:dict,
                           supports:dict,fit_receipt:dict,primary:dict,view:dict,
                           out:Path,log:Path,human_minutes:float)->dict:
    require(manifest.get("record_hash")==hash_obj({
        k:v for k,v in manifest.items() if k!="record_hash"}),
        "ENUMERATION_MANIFEST_TAMPERED")
    require(manifest.get("status")=="ENUMERATION_PREPARED_NOT_EXECUTED"
            and manifest.get("composed_hash")==hash_obj(composed)
            and manifest.get("plan_hash")==hash_obj(plan)
            and manifest.get("supports_hash")==hash_obj(supports)
            and manifest.get("fit_receipt_hash")==hash_obj(fit_receipt)
            and manifest.get("candidate_ids")==sorted(
                candidate["id"] for candidate in composed["candidates"]),
            "ENUMERATION_DEPENDENCY_MISMATCH")
    require(file_digest(out/(PACKAGE+".mo"))==manifest["modelica_hash"]
            and file_digest(out/"run-enumeration.mos")==manifest["mos_hash"],
            "ENUMERATION_SOLVER_INPUT_TAMPERED")
    require(hash_obj(primary)==hash_obj(view["primary"]),
            "ENUMERATION_CONSTRUCTION_VIEW_MISMATCH")
    verify_calibration(fit_receipt,base_composed,composed,base_plan,
                       plan,fit_plan,primary)
    selection=apply_supports(composed,supports)
    require(hash_obj(selection)==manifest["selection_hash"]
            and not selection["rejected"],"ENUMERATION_SUPPORTS_CHANGED")
    require(view.get("lane")=="D"
            and type(human_minutes) in (int,float)
            and human_minutes>=0,"ENUMERATION_VIEW_OR_TIME_INVALID")
    log_text=log.read_text(encoding="utf-8",errors="replace")
    require(not any(x in log_text for x in ("Error:","Failed to load","not found")),
            "ENUMERATION_OPENMODELICA_LOG_ERROR")
    structures={s["id"]:s for s in composed["structures"]}
    candidates={c["id"]:c for c in composed["candidates"]}
    proposals=[]
    for candidate_id in manifest["candidate_ids"]:
        marker=f"Check of {PACKAGE}.{class_name(candidate_id)} completed successfully"
        require(marker in log_text,"ENUMERATION_MODELICA_CHECKMODEL_FAILED")
        candidate=candidates[candidate_id]
        structure=structures[candidate["structure_revision_id"]]
        stage_ids=[m["id"] for m in structure["molecule_instances"]
                   if m["molecule_definition_id"]==plan["roles"]["stage"]]
        path=out/(result_prefix(candidate_id)+"_res.csv")
        trace=assess_trace(path,stage_ids,float(plan["simulation"]["start_time"]),
                           float(plan["simulation"]["stop_time"]),
                           int(plan["simulation"]["intervals"]))
        predictions=[]
        for target in view["target_times"]:
            found=[v for t,v in zip(trace["times"],trace["delivered_series"])
                   if abs(t-float(target))<=1e-6]
            require(bool(found),"ENUMERATION_MISSING_TARGET_TIME")
            predictions.append(found[-1])
        proposals.append({
            "candidate_id":candidate_id,"kind":"calibrated_enumeration_modelica",
            "mechanism":"Enumerated fixed structural alternative fit to same construction",
            "predictions":predictions,"trace_sha256":file_digest(path),
            "fit_receipt_hash":fit_receipt["report_hash"]})
    response={
        "schema":ROUND_SCHEMA,"round_id":view["round_id"],"lane":"D",
        "view_hash":view["view_hash"],"status":"SUBMITTED",
        "producer":"two-structure-calibrated-enumeration-v0",
        "proposals":proposals,
        "unknowns":["Enumerating a catalogue is not free topology discovery"],
        "objections":[],
        "cost":{"llm_calls":0,"tokens":0,"simulations":len(proposals),
                "human_minutes":human_minutes,"retries":0},
        "cost_note":"Solver and measured operator effort; no LLM calls.",
        "source_manifest_hash":manifest["record_hash"],
        "openmodelica_log_sha256":file_digest(log)}
    validate_submission(response,view)
    return response


def main():
    p=argparse.ArgumentParser(description="Independent fixed-catalogue enumeration")
    actions=p.add_subparsers(dest="action",required=True)
    for name in ("prepare","submit"):
        sub=actions.add_parser(name)
        for key in ("base-composed","composed","base-plan","plan",
                    "fit-plan","supports","fit-receipt","primary","out"):
            sub.add_argument("--"+key,required=True,type=Path)
        if name=="submit":
            for key in ("view","log"):
                sub.add_argument("--"+key,required=True,type=Path)
            sub.add_argument("--human-minutes",required=True,type=float)
    args=p.parse_args()
    read=lambda path:json.loads(path.read_text(encoding="utf-8"))
    common=dict(base_composed=read(args.base_composed),composed=read(args.composed),
        base_plan=read(args.base_plan),plan=read(args.plan),
        fit_plan=read(args.fit_plan),supports=read(args.supports),
        fit_receipt=read(args.fit_receipt))
    if args.action=="prepare":
        report=prepare_enumeration(**common,primary=read(args.primary),out=args.out)
    else:
        report=enumeration_submission(**common,primary=read(args.primary),
            view=read(args.view),
            manifest=read(args.out/"enumeration-plan.json"),out=args.out,
            log=args.log,human_minutes=args.human_minutes)
        exclusive_json(args.out/"enumeration-submission.json",report)
    print(json.dumps({"status":report.get("status","ENUMERATION_LANE_READY"),
                      "hash":hash_obj(report)}))


if __name__=="__main__":
    main()
