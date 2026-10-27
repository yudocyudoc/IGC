"""R1 after-the-fact scientific G1 diagnosis of the ONE native Buffalo model.

No model repairs, no renewed provider calls, no new world data. A green
translation/checkModel is not evidence that a DAE is well-determined.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
import re
from pathlib import Path
from scripts.arena_v0_contract import canonical, digest

SCHEMA="igc-arena-r1-native-structural-negative/0.1"
ORIGINAL_NATIVE_SHA="8097496d8033bfe8b5a93eeb7d391f7c98f6bb315bdfb9e63f62b6910b437eac"
SHARED_SOURCE="sha256:562204e3c4509718f8e9ce55d407477edc97bb4cbbcfc266ed50ca3777bd3c92"


def require(ok,code):
    if not ok:raise ValueError(code)


def norm(name):
    return name.replace(" ","_")


def diagnose(native):
    variables=native["model"]["variables"]
    require(len(variables)==17,"R1_B_WRONG_ORIGIN_VARIABLE_COUNT")
    byname={norm(v["name"]):v for v in variables}
    require(len(byname)==len(variables),"R1_B_DUPLICATED_VARIABLE_NAME")
    aliases={}
    for name,v in byname.items():
        if v.get("type")=="variable":
            expr=str(v.get("equation","")).strip()
            if re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*",expr) and expr in byname:
                aliases[name]=expr
    pairs=[]
    for a,b in aliases.items():
        if aliases.get(b)==a and a<=b:
            pairs.append([a,b])
    require(pairs,"R1_B_EXPECTED_UNDETERMINED_NATIVE_CYCLE_NOT_FOUND")
    if ["congestion_multiplier","product_of_capacity_effects"] not in pairs:
        raise ValueError("R1_B_SPECIFIC_CYCLE_CHANGED")
    flow=byname["completion_rate"]["equation"]
    cap=byname["capacity_constrained_throughput"]
    require(cap["type"]=="variable","R1_B_CAPACITY_DIAGNOSTIC_DRIFT")
    require("capacity_constrained_throughput" not in flow,
            "R1_B_CAPACITY_ALREADY_CONNECTED")
    references=[name for name,v in byname.items() if name!="capacity_constrained_throughput"
                and "capacity_constrained_throughput" in str(v.get("equation",""))]
    require(not references,"R1_B_CAPACITY_ALREADY_USED")
    pulse=byname["pulse_gate"]["equation"]
    require("time_active_end - TIME" in pulse and "/ 1" in pulse,
            "R1_B_PULSE_GATE_EXPRESSION_CHANGED")
    return {
        "schema":SCHEMA,
        "arm_id":"B",
        "g0":"TRANSLATED_CONDITIONALLY_NATIVE_BYTES_UNCHANGED",
        "g1_status":"FAIL_UNANCHORED_ALGEBRAIC_IDENTITY",
        "mathematical_underdetermination":[{
            "variables":pair,
            "equations":[f"{pair[0]} = {pair[1]}",
                         f"{pair[1]} = {pair[0]}"],
            "failure":"TWO_EQUATIONS_HAVE_RANK_ONE_FOR_THESE_TWO_ALGEBRAIC_VARIABLES",
            "not_a_determined_dynamic_feedback_loop":True
        } for pair in pairs],
        "unused_claimed_capacity_mechanism":{
            "variable":"capacity_constrained_throughput",
            "equation":cap["equation"],
            "completion_flow_equation":flow,
            "status":"NO_PATH_FROM_THIS_CAPACITY_AUXILIARY_TO_COMPLETION_FLOW"
        },
        "pulse_shape_discrepancy":{
            "native_expression":pulse,
            "time_hour":1.5,
            "native_gate_at_t_1_5_given_end_t_2":0.5,
            "ideal_rectangular_gate_before_t_2":1,
            "interpretation":"NATIVE_GATE_HAS_A_LINEAR_TAPER_DURING_THE_LAST_HOUR",
            "not_a_new_solver_observation":True
        },
        "g2_status":"FAILED_TO_BUILD_ORIGINAL_MODEL_NOT_PHYSICALLY_EVALUATED",
        "g3_status":"NOT_COMPUTABLE_WITHOUT_NATIVE_SOLVER_SERIES",
        "holdout":"NOT_ACCESSED",
        "no_native_edits":True,
        "no_new_provider_calls":True,
        "scientific_interpretation":"FIRST_BUFFALO_PROPOSAL_IS_UNDERDETERMINED_NOT_ARCHITECTURE_FAILURE"
    }


def postonly(native_path,previous_report_path):
    raw=Path(native_path).read_bytes()
    require(sha256(raw).hexdigest()==ORIGINAL_NATIVE_SHA,
            "R1_B_POSTONLY_NATIVE_BYTES_CHANGED")
    old=json.loads(Path(previous_report_path).read_text())
    require(old["source_snapshot_hash"]==SHARED_SOURCE and
            old["B"]["initial_native_sha256"]=="sha256:"+ORIGINAL_NATIVE_SHA and
            old["B"]["provider"]["provider_calls_started"]==1 and
            len(old["D"]["candidates"])==6 and len(old["M"]["candidates"])==3,
            "R1_B_POSTONLY_FOREIGN_SOURCE")
    d=diagnose(json.loads(raw))
    current=json.loads(json.dumps(old))
    current["schema"]="igc-arena-r1-initial-adjudicated/0.1"
    current["status"]="R1_INITIAL_THREE_ARMS_ATTEMPTED_B_G1_NEGATIVE"
    current["B"]["g1"]=d
    current["B"]["status"]="G1_UNDETERMINED_NATIVE_G2_NO_TRAJECTORY"
    current["B"]["g2"]="FAILED_TO_BUILD_NO_PHYSICAL_SERIES"
    current["B"]["g3"]="NOT_COMPUTABLE"
    current["B"]["g1_postonly_native_sha256"]="sha256:"+ORIGINAL_NATIVE_SHA
    current["scope"]="INITIAL_R1_ATTEMPTS_CLOSED_NOT_THREE_G2_SUCCESSES"
    current["next"]="R2_OWN_ARM_FEEDBACK_ON_ACTUAL_NEGATIVE_WITHOUT_EQUATION_HINTS"
    current["human_claims"]=[
        "D_M_G2_ONLY_B_FAILS_G1",
        "NO_COMMON_WINNER",
        "NO_INDEPENDENT_HOLDOUT",
        "DO_NOT_AUTOMATICALLY_RETRY_OR_REPAIR_B",
    ]
    return current


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--native",type=Path,required=True)
    p.add_argument("--old-report",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    require(not a.out.exists(),"R1_B_ADJUDICATION_OUTPUT_EXISTS")
    report=postonly(a.native,a.old_report)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_bytes(canonical(report)+b"\n")
    print(json.dumps({"status":report["status"],
                      "g1":report["B"]["g1"]["g1_status"],
                      "cost_usd_estimate":report["B"]["provider"]["cost_usd_estimate"],
                      "output_sha256":digest(report)}))


if __name__=="__main__":
    main()
