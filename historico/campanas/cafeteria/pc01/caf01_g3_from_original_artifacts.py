#!/usr/bin/env python3
"""CAF-01 G3 three-arm evidence inventory and G4 REFERENCE staging.

No native solver, DES, RK4, provider call, G4 model forecast or reveal.
All inputs must be exact original GitHub scientific artifact files.
D gets 18 frozen RK4 screen rows with only the three preselected native G2
receipts promoted. M gets six original natively conserving E1 construction
classes. Buffalo is G1 materially invalid with no curve.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from caf01_g3 import CONTRACT, inventory, select, digest
from caf01_g4 import forecast as reference_forecast

HERE=Path(__file__).resolve().parent
PUB=HERE/"public_inputs"/"run_40915090599"/"CAF01.json"
PINS={
    "public_CAF01":"727501a3b5b33a63ab5a5d5f0f907d5431d0ee4f0d8b24ffd6f97758d59386fb",
    "d_screen":"e77dbbabc18370104f74c1ee88b86ec3a29d91a2cb3ec30b546a882f4a3675b3",
    "d_native":"5dfde7336db42bd0970a4b5efca2a597d1a173ade583be1a68d7c5ad4fe40f2d",
    "m_native":"537733f53f33fc5b4dd3ea054e54f21013040d28c26bac6ed34f415aed9c51c7",
    "b_original":"338061780ab31dbe7016039fb110420785bd98be285c9d2649c603dac79bc1bf",
    "b_intake":"b9117b760e62aa82b9d9816effda655ea0284068f6e116e7f8c586829ed15e64",
    "b_cafn_receipt":"0a36f57f3666d2b59770c59f02eb5ec528db35bb6b2fcc7cdbd9fe65f64d4915",
    "b_cafn_prompt_audit":"cbea59727a59ae1a11ad7773c6eec7351ab1e9b5c74d0a210648eab77e724f89"
}
SOURCE_RUNS={"DES_construction":40915090599,"D_RK4":40974820126,
             "D_native_postonly":40984572504,"M_native_postonly":41000243810,
             "Buffalo_live":40999646869}

def require(ok, code):
    if not ok: raise ValueError(code)

def load(path,key):
    data=path.read_bytes()
    require(hashlib.sha256(data).hexdigest()==PINS[key],
            "G3_WRONG_SOURCE_BYTES:"+key)
    return json.loads(data)

def sha(path):
    return "sha256:"+hashlib.sha256(path.read_bytes()).hexdigest()

def blocked_row(ident,evid_hash,reason,native_sha=None,g0="BLOCKED",g1="BLOCKED"):
    return {"id":ident,"gates":{"G0":g0,"G1":g1,"G2":"BLOCKED"},
            "construction_delivered":None,
            "native_sha256":native_sha,
            "g2_receipt_sha256":None,"rk4_receipt_sha256":None,
            "balance_max_abs":None,"rk4_native_max_abs_delta":None,
            "block_reason":reason,"candidate_evidence_sha256":evid_hash}

def assemble(pub,d_screen,d_native,m_native,b_native,b_intake,b_cafn,b_prompt):
    contract=json.loads(CONTRACT.read_bytes())
    ev=load(pub,"public_CAF01")
    d=load(d_screen,"d_screen")
    dn=load(d_native,"d_native")
    m=load(m_native,"m_native")
    b=load(b_native,"b_original")
    bi=load(b_intake,"b_intake")
    bn=load(b_cafn,"b_cafn_receipt")
    bp=load(b_prompt,"b_cafn_prompt_audit")
    require(d["case"]=="CAF01" and
            d["actual_RK4_invocations_this_case"]==18 and
            d["native_OpenModelica_simulations"]==0 and
            d["evaluation_truth_read"] is False,
            "G3_D_SCREEN_PROVENANCE_INVALID")
    require(dn["status"]=="ALL_THREE_NATIVE_G2_PASSED"
            and dn["native_construction_simulations_consumed"]==3
            and [x["status"] for x in dn["native_candidates"]]==["PASS"]*3,
            "G3_D_NATIVE_POSTONLY_INVALID")
    require(m["status"]=="ALL_SIX_M_NATIVE_G2_PASS"
            and m["native_construction_simulations_consumed"]==6
            and m["native_g2_pass_count"]==6
            and len(m["native_candidates"])==6,
            "G3_M_NATIVE_POSTONLY_INVALID")
    require(bi["source_native_sha256"]=="sha256:"+PINS["b_original"]
            and bi["reason"]=="DUPLICATED_MATERIAL_FLOW"
            and bi["native_model_returned"] is True
            and bi["native_model_edited"] is False,
            "G3_B_MATERIAL_REJECTION_NOT_ORIGINAL")
    variables=b["model"]["variables"]
    var={v["name"]:v for v in variables}
    accept=var["order acceptance rate"]["name"]
    pending=var["pending orders"]; delivered=var["delivered orders"]
    require(accept in pending["inflows"] and accept in delivered["inflows"]
            and "delivery rate" in pending["outflows"]
            and "delivery rate" in delivered["inflows"],
            "G3_B_DUPLICATION_NOT_PROVED_BY_NATIVE_PORTS")
    require(bn["status"]=="ONE_LIVE_MASKED_DIAGNOSTIC_VALID"
            and bn["diagnosis"]=="PARTIALLY_IDENTIFIABLE_WITH_EXPLICIT_LIMITS"
            and bn["provider_calls_started"]==1
            and bn["model_required"] is False
            and bn["diagnostic_interface"]==
                  "DIRECT_SAME_PROVIDER_NOT_BUFFALO_NATIVE_GENERATOR"
            and bp["observation_times"]==[0,40]
            and bp["no_cross_arm_data"] is True,
            "G3_B_CAFN_DIAGNOSTIC_NOT_ISOLATED")
    rows={}
    eh=digest(ev)
    for item in d["candidate_rows"]:
        require(item["gate"]=={"G0":"PASS","G1":"PASS","G2":"RK4_SCREEN"}
                and item["native_G2_verified"] is False
                and item["balance_value_is_certified_upper_bound"] is True
                and len(item["construction_delivered"])==7,
                "G3_D_RK4_ROW_INVALID")
        ident=item["id"]
        require(ident not in rows,"G3_DUPLICATE_D")
        rows[ident]={
            "id":ident,"gates":dict(item["gate"]),
            "construction_delivered":item["construction_delivered"],
            "native_sha256":item["native_sha256"],
            "g2_receipt_sha256":None,
            "rk4_receipt_sha256":item["rk4_receipt_sha256"],
            "balance_max_abs":item["balance_max_abs"],
            "rk4_native_max_abs_delta":None,
            "block_reason":None,"candidate_evidence_sha256":eh}
    require(len(rows)==18,"G3_WRONG_D_RK4_INVENTORY")
    native_d={}
    for row in dn["native_candidates"]:
        ident=row["id"]
        require(ident in rows and ident not in native_d
                and row["native_source_sha256"]==rows[ident]["native_sha256"]
                and row["rk4_receipt_sha256"]==rows[ident]["rk4_receipt_sha256"]
                and row["balance_max_abs"]<=0.008
                and row["rk4_native_max_abs_delta"]<=0.012,
                "G3_D_NATIVE_NOT_MATCHED_OR_OUTSIDE_BOUNDS")
        receipt=d_native.parent/f"D_G2_{row['ordinal']}_receipt.json"
        require(receipt.is_file()
                and json.loads(receipt.read_bytes())==row,
                "G3_D_INDIVIDUAL_RECEIPT_NOT_MATCHED")
        rows[ident].update(
            gates={"G0":"PASS","G1":"PASS","G2":"PASS"},
            g2_receipt_sha256=sha(receipt),
            balance_max_abs=row["balance_max_abs"],
            rk4_native_max_abs_delta=row["rk4_native_max_abs_delta"])
        native_d[ident]=True
    require(len(native_d)==3 and
            set(native_d)==set(x["candidate_id"] for x in d["D_preliminary_representatives"].values()),
            "G3_D_PRESELECTED_NATIVE_SET_CHANGED")
    for row in m["native_candidates"]:
        ident=row["id"]
        require(ident not in rows
                and row["status"]=="PASS"
                and row["balance_max_abs"]<=0.008
                and len(row["construction_delivered"])==7,
                "G3_M_CANDIDATE_INVALID")
        rfile=m_native.parent/f"M_G2_{row['ordinal']}_receipt.json"
        require(rfile.is_file() and json.loads(rfile.read_bytes())==row,
                "G3_M_INDIVIDUAL_RECEIPT_NOT_MATCHED")
        rows[ident]={
            "id":ident,"gates":{"G0":"PASS","G1":"PASS","G2":"PASS"},
            "construction_delivered":row["construction_delivered"],
            "native_sha256":row["native_model_source_sha256"],
            "g2_receipt_sha256":sha(rfile),
            "rk4_receipt_sha256":None,
            "balance_max_abs":row["balance_max_abs"],
            "rk4_native_max_abs_delta":None,
            "block_reason":None,
            "candidate_evidence_sha256":eh}
    # The B G1 failure is SCIENTIFIC, not "adapter unrelated". Do not
    # invent a construction delivered curve or try to repair native equations.
    rows["B_NATIVE_1"]=blocked_row(
        "B_NATIVE_1",eh,"G1_FAIL_DUPLICATED_MATERIAL_FLOW_2X_ACCEPTANCE",
        native_sha="sha256:"+PINS["b_original"],g0="PASS",g1="FAIL")
    need_ids={x["id"] for x in inventory(contract)}
    require(set(rows)==need_ids and len(rows)==25,"G3_25_ROWS_NOT_COMPLETE")
    ordered=[rows[x["id"]] for x in inventory(contract)]
    decision=select(contract,ev,ordered)
    require(decision["decision"]["B"]["status"]=="NO_VALID_CANDIDATE"
            and decision["decision"]["B"]["winners"]==[]
            and decision["decision"]["D"]["winners_pending_g2"]==[],
            "G3_SELECTION_INVALID_FOR_POSTONLY_GATES")
    refs=reference_forecast(ev,contract)
    require(refs["future_truth_seen"] is False
            and refs["reference_solver_runs"]==0
            and refs["independent_new_world_runs"]==0,
            "G4_REFERENCE_EVALUATION_SPEND_FORBIDDEN")
    audit={
        "schema":"igc-caf01-g3-g4-source-audit/0.1",
        "status":"G3_CONSTRUCTION_SELECTION_AND_G4_REFERENCES_ONLY",
        "artifact_provenance_GitHub_runs":SOURCE_RUNS,
        "original_sha256":{k:"sha256:"+v for k,v in PINS.items()},
        "D_native_G2_passed":3,
        "M_native_G2_passed":6,
        "Buffalo_CAF01_G1":"FAIL_MATERIAL_DUPLICATION_NOT_ADAPTER_ONLY",
        "Buffalo_CAFN_diagnosis":"PARTIALLY_IDENTIFIABLE_WITH_EXPLICIT_LIMITS",
        "Buffalo_CAFN_diagnostic_method":"DIRECT_PROVIDER_NOT_NATIVE_GENERATOR",
        "Buffalo_CAFN_prompt_known_conditions_missing":[
            "INITIAL_STOCKS_ZERO","NO_MATERIAL_LOSSES"
        ],
        "Buffalo_CAFN_unprompted_alternatives_not_valid_under_contract":[
            "PRELOADED_INVENTORY","COMPENSATED_MATERIAL_LOSS"
        ],
        "Buffalo_total_provider_calls_consumed":2,
        "M_native_construction_attempts_consumed":6,
        "D_native_construction_attempts_consumed":3,
        "D_RK4_construction_and_masked_invocations_consumed":36,
        "additional_solvers":0,"additional_providers":0,
        "DES_evaluation_invocations":0,
        "forecast_model_evaluation_simulations":0,
        "new_holdout_pulse_model_forecasts":"NOT_YET_GENERATED",
        "external_immutable_G3_G4_custody":"NOT_YET_ESTABLISHED",
        "evaluation_truth_accessed":False,
        "G4_references_only":True,
        "M_capacity_equivalence":"C72_C100_CONDITIONAL_NOT_EMPIRICALLY_IDENTIFIED",
        "note":"D RK4 non-native rows retain RK4_SCREEN only; asserted upper-bound balance not measured in OMC."
    }
    return ordered,decision,refs,audit

def run(args):
    out=args.out
    require(not out.exists(),"G3_OUTPUT_ALREADY_EXISTS")
    rows,dec,refs,report=assemble(
        args.public,args.d_screen,args.d_native,args.m_native,
        args.b_original,args.b_intake,args.b_cafn,args.b_prompt)
    out.mkdir(parents=True)
    for filename,object in {
        "G3_COMPLETE_INVENTORY.json":rows,
        "G3_CONSTRUCTION_SELECTION.json":dec,
        "G4_PUBLIC_REFERENCE_FORECASTS_UNCUSTODIED.json":refs,
        "G3_G4_PROVENANCE_AND_LIMITATIONS.json":report,
    }.items():
        (out/filename).write_text(json.dumps(
            object,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+"\n",
            encoding="utf-8")
    return dec

def main():
    p=argparse.ArgumentParser()
    for k in ("public","d-screen","d-native","m-native","b-original","b-intake",
              "b-cafn","b-prompt"):
        p.add_argument("--"+k,required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    selection=run(args)
    print(json.dumps({
        "status":"G3_CONSTRUCTION_SELECTION_DONE_G4_REFERENCES_ONLY",
        "selection":selection["decision"],
        "preholdout_locked":False,"evaluation_executed":False},
        ensure_ascii=False,sort_keys=True))

if __name__=="__main__":
    main()
