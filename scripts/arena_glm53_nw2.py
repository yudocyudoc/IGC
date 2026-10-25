"""One-shot GLM-5.3 new-world Arena integration with existing verified modules.

Actions:
  prepare: construction -> calibration -> exact S request (zero inference)
  pre-solver: authenticated connector response -> ATMS seal -> S/D Modelica
  post-solver: verify actual S/D solver traces -> submissions -> PredictionLock
The reserved observation is NOT in this module. Scoring is a separate phase.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .arena_round import canonical, exclusive_json, hash_obj, prepare, verify_lock
from .arena_sp_producers import build_requests, parse_s_response, ProviderError, _validate_schedule
from .arena_sp_capture import usage_of
from .arena_s_calibration import calibrate, verify_calibration
from .arena_s_real import ORIGIN, SCHEMA as CAPTURE_SCHEMA, seal_s_only, verify_s_only_seal
from .arena_sp_simulation import prepare_s, verify_s
from .arena_s_submission import s_submission, s_abstention, s_g3_disposition
from .arena_s_pilot_enumeration import prepare_enumeration, enumeration_submission
from .arena_s_pilot_lock import build_lock
from .compose_molecular_candidates import compose

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data/synthetic"
MODEL="@cf/zai-org/glm-5.3-flash"
RUN_REF="glm53-nw2-actual-connected-api-ONE-call"


def read(path:Path)->dict:
    return json.loads(path.read_text(encoding="utf-8"))


def inputs()->tuple:
    spec=read(DATA/"arena_glm53_nw2_spec.json")
    primary=read(DATA/"arena_glm53_nw2_primary.json")
    catalog=read(DATA/"arena_glm53_nw2_catalog.json")
    supports=read(DATA/"arena_s_pilot_supports.json")
    fit=read(DATA/"arena_s_pilot_fit_config.json")
    plan=read(DATA/"fm_b3_dynamic_plan.json")
    plan["candidates"]=plan["candidates"][:2]
    composed=compose(plan,read(DATA/"fm_a_structural_candidates.json"))
    return spec,primary,catalog,supports,fit,plan,composed


def requested_package(views:dict,spec:dict,catalog:dict)->dict:
    pkg=build_requests(views,spec,catalog)
    first=pkg["requests"][0]
    if first["endpoint"]!=MODEL:
        raise ProviderError("NW2_GLM53_ENDPOINT_NOT_LOCKED")
    body=first["body"]
    body.pop("chat_template_kwargs",None)
    body["reasoning_effort"]="low"
    body["max_completion_tokens"]=1400
    first["body_hash"]=hash_obj(body)
    pkg["manifest"]["requests_hash"]=hash_obj(pkg["requests"])
    _validate_schedule(pkg)
    return pkg


def prep(out:Path)->None:
    out.mkdir(parents=True,exist_ok=False)
    spec,primary,catalog,supports,fit,plan,base=inputs()
    views=prepare(spec,primary)
    fitted,eval_plan,fit_receipt=calibrate(base,plan,fit,primary)
    pkg=requested_package(views,spec,catalog)
    for key,value in (("spec",spec),("primary",primary),("catalog",catalog),
       ("supports",supports),("fit-config",fit),("base-plan",plan),
       ("base-composed",base),("fitted-composed",fitted),
       ("evaluation-plan",eval_plan),("calibration-receipt",fit_receipt),
       ("package",pkg)):
        exclusive_json(out/(key+".json"),value)
    (out/"views").mkdir()
    for lane,view in views.items():
        exclusive_json(out/"views"/(lane+".json"),view)
    (out/"calibration").mkdir()
    from .arena_s_pilot_physics import composer_bytes
    (out/"calibration/GeneratedMolecularCandidates.mo").write_bytes(
        composer_bytes(eval_plan,fitted))
    first=pkg["requests"][0]
    print("NW2_REQUEST_JSON="+json.dumps(first["body"],sort_keys=True,
                                         ensure_ascii=False,separators=(",",":")))
    print("NW2_REQUEST_SHA256="+first["body_hash"])
    print("NW2_PREPARED_NO_INFERENCE="+hash_obj(pkg))


def captured(out:Path)->None:
    pkg=read(out/"package.json")
    catalog=read(out/"catalog.json")
    response=read(DATA/"arena_glm53_nw2_response.json")
    if not response.get("success") or response.get("status")!=200:
        raise ProviderError("NW2_PROVIDER_RESPONSE_NOT_SUCCESSFUL")
    if response.get("result",{}).get("model")!=MODEL:
        raise ProviderError("NW2_RESPONSE_MODEL_MISMATCH")
    draft=parse_s_response(pkg,response,catalog)
    req=pkg["requests"][0]
    receipt={
        "schema":CAPTURE_SCHEMA,"run_ref":RUN_REF,
        "capture_method":"CLOUDFLARE_CONNECTED_API","mock":False,
        "requests_hash":pkg["manifest"]["requests_hash"],
        "catalog_hash":hash_obj(catalog),"view_hash":req["view_hash"],
        "request_body_hash":req["body_hash"],
        "response_hash":hash_obj(response),"parsed_s_hash":hash_obj(draft),
        "calls_completed":1,"retries":0,
        "duration_ms":None,"duration_status":"NOT_OBSERVED",
        "usage":usage_of(response),"independent_attestation":False,
        "empirical_causality":"NOT_PROVEN"}
    receipt["receipt_hash"]=hash_obj(receipt)
    (out/"S-archive").mkdir()
    for key,val in (("response",response),("s-draft",draft),("receipt",receipt)):
        exclusive_json(out/"S-archive"/(key+".json"),val)
    views={"S":read(out/"views/S.json")}
    fitted=read(out/"fitted-composed.json")
    supports=read(out/"supports.json")
    fit_receipt=read(out/"calibration-receipt.json")
    seal=seal_s_only(pkg,catalog,views,fitted,supports,response,draft,receipt,
                     calibration=fit_receipt)
    if seal["origin"]!=ORIGIN:
        raise ProviderError("NW2_CONNECTOR_RESPONSE_MUST_NOT_BE_MOCK")
    verify_s_only_seal(seal,pkg,catalog,views,fitted,supports,
                       response,draft,receipt,calibration=fit_receipt)
    exclusive_json(out/"S-seal.json",seal)
    eval_plan=read(out/"evaluation-plan.json")
    if seal["S"]["selection"]:
        prepare_s(seal,draft,pkg,catalog,views,fitted,supports,eval_plan,
                  out/"S",s_capture={"response":response,"draft":draft,
                                    "receipt":receipt},calibration=fit_receipt)
    prepare_enumeration(read(out/"base-composed.json"),fitted,
                        read(out/"base-plan.json"),eval_plan,supports,
                        read(out/"fit-config.json"),read(out/"primary.json"),
                        fit_receipt,out/"D")
    print("NW2_ATMS_SEALED="+seal["handoff_hash"])
    print("NW2_GLM53_ORIGINAL_SELECTION="+json.dumps(seal["S"]["selection"]))


def finish(out:Path)->None:
    spec=read(out/"spec.json")
    primary=read(out/"primary.json")
    views={"S":read(out/"views/S.json"),"D":read(out/"views/D.json")}
    pkg=read(out/"package.json")
    catalog=read(out/"catalog.json")
    supports=read(out/"supports.json")
    base=read(out/"base-composed.json")
    fitted=read(out/"fitted-composed.json")
    base_plan=read(out/"base-plan.json")
    eval_plan=read(out/"evaluation-plan.json")
    fit=read(out/"fit-config.json")
    calibration=read(out/"calibration-receipt.json")
    archive=out/"S-archive"
    response=read(archive/"response.json")
    draft=read(archive/"s-draft.json")
    receipt=read(archive/"receipt.json")
    seal=read(out/"S-seal.json")
    common=dict(seal=seal,package=pkg,catalog=catalog,views={"S":views["S"]},
       composed=fitted,supports=supports,response=response,draft=draft,
       receipt=receipt,calibration=calibration,base_composed=base,
       base_plan=base_plan,evaluation_plan=eval_plan,fit_plan=fit,
       human_minutes=0)
    g3=s_g3_disposition(seal,calibration)
    if seal["S"]["selection"]:
        manifest=read(out/"S/s-execution-plan.json")
        verified=verify_s(manifest,seal,fitted,eval_plan,out/"S",
                          out/"S/openmodelica.log",
                          composer_file=out/"calibration/GeneratedMolecularCandidates.mo")
        exclusive_json(out/"S-verified.json",verified)
        args=dict(manifest=manifest,verified_report=verified,
                  simulation_dir=out/"S",log=out/"S/openmodelica.log",
                  composer_file=out/"calibration/GeneratedMolecularCandidates.mo")
    else:
        args={}
    if g3["retained_candidate_ids"]:
        s=s_submission(**common,**args)
    else:
        s=s_abstention(**common,**args)
    d=enumeration_submission(
        manifest=read(out/"D/enumeration-plan.json"),
        base_composed=base,composed=fitted,base_plan=base_plan,plan=eval_plan,
        fit_plan=fit,supports=supports,fit_receipt=calibration,
        primary=primary,view=views["D"],out=out/"D",log=out/"D/openmodelica.log",
        human_minutes=0,
        composer_file=out/"calibration/GeneratedMolecularCandidates.mo")
    exclusive_json(out/"S-submission.json",s)
    exclusive_json(out/"D-submission.json",d)
    _,_,locked=build_lock(spec,primary,s,d,run_ref=RUN_REF)
    verify_lock(locked)
    (out/"locked").mkdir()
    exclusive_json(out/"locked/prediction-lock.json",locked)
    # The lock is printed into the completed job log for a separate frozen
    # GitHub commit. The holdout remains inaccessible in this command.
    print("NW2_LOCK_HASH="+locked["lock_hash"])
    print("NW2_LOCK_JSON="+canonical(locked).decode("utf-8"))
    print("NW2_LOCK_VALID_NO_HOLDOUT=YES")
    print("NW2_S_STATUS="+s["status"]+";D_STATUS="+d["status"])


def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=("prepare","pre-solver","post-solver"))
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    {"prepare":prep,"pre-solver":captured,"post-solver":finish}[args.action](args.out)


if __name__=="__main__":
    main()
