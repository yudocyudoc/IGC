#!/usr/bin/env python3
"""CAF-01 Buffalo independent FIRST-PROPOSAL request staging.

Two independent inputs, one per authorized call. The CAFN request MUST NOT
contain CAF01's intermediate observations, candidate model, feedback, ranking,
or another arm's work. No provider or native simulator executed here.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

from caf01_g3 import CONTRACT, validate_evidence, digest

HERE=Path(__file__).resolve().parent
PUB=HERE/"public_inputs"/"run_40915090599"
WORLD="sha256:26ca23076a44410bcafc4a7a944a5d5f6c6528dd59c96e7459e43c93a68812ad"
FILES={
  "CAF01":"727501a3b5b33a63ab5a5d5f0f907d5431d0ee4f0d8b24ffd6f97758d59386fb",
  "CAFN":"8112019ffad402ff1f1e0deafa3b4f1786bb37488258d5c7fe16e0404e22d5a1",
}
SPEC={"startTime":0,"stopTime":2/3,"dt":1/120,"timeUnits":"hour","integrationMethod":"Euler"}

def require(ok,code):
    if not ok: raise ValueError(code)

def case_evidence(case,contract,pub=PUB):
    require(case in FILES,"B_UNKNOWN_REQUEST_CASE")
    original=(pub/(case+".json")).read_bytes()
    require(hashlib.sha256(original).hexdigest()==FILES[case],
            "B_PUBLIC_EVIDENCE_BYTES_CHANGED_"+case)
    d=json.loads(original)
    times,_=validate_evidence(d,contract)
    require(d["case"]==case and d["source_snapshot_sha256"]==WORLD
            and times==([0,5,10,15,20,30,40] if case=="CAF01" else [0,40]),
            "B_PUBLIC_MASK_UNEXPECTED")
    return d

def build(case,contract,pub=PUB):
    b=contract["methods"]["B"]
    require(b["candidate_models_max"]==1 and b["provider_calls_max"]==2
            and b["call_count_purpose"]=={
                "CAF01_original_model_proposal":1,
                "CAFN_fresh_masked_diagnosis":1}
            and b["negative_control_no_prior_history"] is True
            and b["negative_control_native_simulations_max"]==0
            and b["CAF_local_specs_proposal"]==SPEC,
            "B_CONTRACT_PROVIDER_SCOPE_DRIFT")
    evidence=case_evidence(case,contract,pub)
    return {
        "schema":"igc-caf01-b-independent-provider-request/0.1",
        "status":"STAGED_NOT_SENT_NO_NATIVE_PROVIDER_RESPONSE",
        "method":"B_BUFFALO_ONLY",
        "request_id":"B_"+case+"_CALL_ONCE",
        "case":case,
        "source_public_snapshot_sha256":WORLD,
        "original_public_evidence_file_sha256":"sha256:"+FILES[case],
        "evidence_semantic_sha256":digest(evidence),
        "public_evidence":evidence,
        "task":{
            "type":"independent_stock_flow_model_proposal",
            "boundary":"accepted_order_equivalents -> delivered",
            "material_unit":"one accepted order equivalent = one delivered item",
            "allowed_loss_or_cancellation":False,
            "initial_pending":0,
            "independent_native_model_max":1,
            "required_native_solver_specs":SPEC,
            "model_output":"Buffalo native model JSON, stock-flow equations and variables, no hand-created repair from other methods",
            "explain_identifiability_limits":True,
            "no_future_evaluation_outcomes":True,
        },
        "isolation":{
            "different_B_request_has_not_been_supplied":True,
            "other_arms_results_unavailable":True,
            "prior_B_native_model_supplied":False,
            "prior_B_provider_feedback_supplied":False,
            "private_world_mechanism_supplied":False,
            "evaluation_truth_supplied":False,
            "negative_case_intermediate_observations_supplied":False,
        },
        "budget":{
            "provider_inferences_from_this_preparation":0,
            "provider_inferences_allowed_in_future_for_this_request":1,
            "automatic_retries_allowed":0,
            "native_simulations_from_this_preparation":0,
            "CAF_N_extra_native_sims_allowed":0,
        },
        "native_adapter":{
            "local_bridge":"caf01_b_local_specs.py",
            "translation":"OFFLINE_ONLY_UNTIL_NATIVE_RESPONSE_AVAILABLE",
            "historical_timing_versus_CAF_timing":"G0_G1_PARITY_UNVERIFIED",
            "native_series_roles":"UNVERIFIED_FOR_ACTUAL_PROVIDER_MODEL",
            "native_G2":"NOT_RUN",
            "provider_model_failure_can_only_be_claimed_after_actual_PROVIDER_RESULT":False,
        },
    }

def generate(out,pub=PUB):
    require(not out.exists(),"B_OUTPUT_EXISTS")
    contract=json.loads(CONTRACT.read_text(encoding="utf-8"))
    # Independent construction: each call receives one case, with no B
    # model/feedback/score from the other case. Do not combine into one
    # provider request.
    requests={case:build(case,contract,pub) for case in ("CAF01","CAFN")}
    require(len(requests["CAFN"]["public_evidence"]["observations"])==2
            and len(requests["CAF01"]["public_evidence"]["observations"])==7,
            "B_NEGATIVE_MASK_LEAK")
    out.mkdir(parents=True,exist_ok=False)
    for case,request in requests.items():
        (out/("B_"+case+"_PROVIDER_REQUEST.json")).write_text(
            json.dumps(request,sort_keys=True,ensure_ascii=False,indent=2)+"\n",
            encoding="utf-8")
    (out/"NOT_SENT.txt").write_text(
        "Both provider requests are only staged locally, not sent. "
        "Send them in independent provider sessions; do not attach either "
        "response or feedback to the other request. No provider calls or "
        "OpenModelica simulations have occurred in this step.\n")
    return requests

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    req=generate(args.out)
    print(json.dumps({"status":"STAGED_NOT_SENT",
      "requests":len(req),
      "CAF01_observations":len(req["CAF01"]["public_evidence"]["observations"]),
      "CAFN_observations":len(req["CAFN"]["public_evidence"]["observations"]),
      "provider_calls":0,"OMC_calls":0}))

if __name__=="__main__":
    main()
