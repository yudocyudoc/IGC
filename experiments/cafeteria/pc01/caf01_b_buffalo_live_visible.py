#!/usr/bin/env python3
"""Strict CAF01 Buffalo visible-input adapter for original UB-IAD SD-AI SDK.

This is a PURE adapter for the authorized CAF01 construction proposal ONLY.
CAFN is a diagnostic with explicit abstention, never passed to native SD-AI's
model-forcing quantitative engine. No model or provider calls in this script.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

from caf01_b_producer_admission import build, SPEC
from caf01_g3 import CONTRACT
from caf01_b_local_specs import bridge
from scripts.arena_b_native_to_modelica import TranslationBlocked

def need(ok,code):
    if not ok: raise ValueError(code)

def visible_for_original_sd_ai(request):
    need(request["case"]=="CAF01"
         and request["task"]["type"]=="independent_stock_flow_model_proposal"
         and request["task"]["native_model_required"] is True
         and request["task"]["required_native_solver_specs"]==SPEC
         and len(request["public_evidence"]["observations"])==7,
         "B_CAF01_ONLY_ONE_NATIVE_MODEL_REQUEST")
    ev=request["public_evidence"]
    need([r["t_min"] for r in ev["observations"]]==[0,5,10,15,20,30,40],
         "B_CAF01_CONSTRUCTION_TIMES_CHANGED")
    question=(
        "Independently propose ONE native Buffalo SD-AI stock-flow model "
        "for the following observed cafeteria construction ONLY. "
        "Boundary: orders accepted -> delivered, units: accepted-order-equivalents "
        "and hours. Loss and cancellation are disallowed, and all initial stocks are zero. "
        "Input: publicly specified pulse 72 orders/hour from t=0 until t=1/3 hour, "
        "then zero; stop at 2/3 hour. Cumulative observed deliveries at "
        "hours [0,1/12,1/6,1/4,1/3,1/2,2/3] are "
        "[0,3,8,13,18,24,24]. "
        "Use exactly model.specs = "
        '{"startTime":0,"stopTime":0.6666666666666666,'
        '"dt":0.008333333333333333,"timeUnits":"hour",'
        '"integrationMethod":"Euler"}. '
        "Maintain the original Buffalo native quantitative model schema. "
        "Do not infer or receive hidden world parameters, other arm output, "
        "evaluation outcomes or any previous Buffalo model. "
        "If the observations do not uniquely identify the mechanism, "
        "describe the limits explicitly rather than claiming causal identification. "
        "Only one model proposal and one provider call are allowed, without retries."
    )
    return {
        "schema":"igc-arena-visible-input/0.1",
        "investigation_id":"CAF01-B-CONSTRUCTION-ONLY",
        "round_id":"CAF01-B-INDEPENDENT-ONE",
        "question":question,
        "source_snapshot_hash":ev["source_snapshot_sha256"],
        "iteration_limit":1,
        "construction":{
            "input_profile":{"kind":"pulse","rate":72,"duration":1/3},
            "observations":[{"t":r["t_min"]/60,"delivered":r["delivered"]}
                            for r in ev["observations"]],
            "known_conditions":[
                "One accepted order equivalent is one item.",
                "Initial accepted, delivered and pending zero; no material losses.",
                "Only public construction outcomes, no evaluation and no causal gold.",
            ],
        },
        "observability":{"stock_unit":"items","time_unit":"hour",
                         "observable":"cumulative_delivered"},
        "resources":{"max_model_proposals":1,"max_llm_calls":1,
                     "max_simulations":0},
    }

def generate(out):
    need(not out.exists(),"B_CAF01_VISIBLE_OUTPUT_EXISTS")
    contract=json.loads(CONTRACT.read_text())
    request=build("CAF01",contract)
    vis=visible_for_original_sd_ai(request)
    out.mkdir(parents=True,exist_ok=False)
    (out/"b-visible.json").write_text(
        json.dumps(vis,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    (out/"b-request.json").write_text(
        json.dumps(request,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    original=(out/"b-visible.json").read_bytes()
    receipt={
        "schema":"igc-caf01-b-visible-staging/0.1",
        "status":"ORIGINAL_BUFFALO_SDK_INPUT_PREPARED_NOT_SENT",
        "native_visible_sha256":"sha256:"+hashlib.sha256(original).hexdigest(),
        "source_public_evidence_sha256":request["original_public_evidence_file_sha256"],
        "source_snapshot_sha256":vis["source_snapshot_hash"],
        "case":"CAF01",
        "CAFN_history_supplied":False,
        "other_arms_supplied":False,
        "evaluation_observations_supplied":False,
        "provider_calls":0,
        "OpenModelica_simulations":0,
    }
    (out/"B_VISIBLE_PREFLIGHT.json").write_text(
        json.dumps(receipt,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    return receipt

def evaluate_native(native_path,out):
    """Report adapter failures as adapter failures, not Buffalo science."""
    out.mkdir(parents=True,exist_ok=False)
    document=json.loads(native_path.read_bytes())
    report={
      "schema":"igc-caf01-b-native-intake-postonly/0.1",
      "source_native_sha256":"sha256:"+hashlib.sha256(native_path.read_bytes()).hexdigest(),
      "case":"CAF01","native_model_returned":isinstance(document.get("model"),dict),
      "native_model_edited":False,"native_simulations":0,
      "evaluation_read":False,
    }
    try:
        contract=json.loads(CONTRACT.read_text())
        name,code,details=bridge(document,contract)
        (out/(name+".mo")).write_text(code)
        report.update(status="OFFLINE_TRANSLATED_G0_G1_UNVERIFIED",
                      modelica_class=name,
                      translation=details)
    except (ValueError,KeyError,TypeError,TranslationBlocked) as exc:
        report.update(status="BLOCKED_NATIVE_ADAPTER_NOT_MODEL_FAILURE",
                      reason_type=type(exc).__name__,reason=str(exc)[:160])
    (out/"B_NATIVE_INTAKE.json").write_text(
        json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("cmd",choices=("prepare","intake"))
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--native",type=Path)
    a=p.parse_args()
    if a.cmd=="prepare":
        print(generate(a.out)["status"])
    else:
        need(a.native is not None,"B_NATIVE_REQUIRED")
        print(evaluate_native(a.native,a.out)["status"])

if __name__=="__main__":
    main()
