#!/usr/bin/env python3
"""CAF02 G2 correspondence *plan*, no native Modelica execution.

Selects 12 named M cases and 3 named D cases BEFORE independent K0.
Computes expected surrogate curves on the single public K0 pulse. These
are NOT OpenModelica results. An actual OMC process must use the identical
stock graph, parameter values, units, start state and half-open pulse, and
submit full source/hash, solver/CSV traces and budget receipt independently.

One rate does NOT establish parity on K1/K2 or across all 182 candidates.
"""
import json
import hashlib
import math
from pathlib import Path
import caf02_structural_k0k1k2 as m
import caf02_d_k0k1k2_adapter as d

TIMES=(5,10,15,20,30,40)
CRITERION="MAX_ABS_DELIVERED_DIFFERENCE_LE_0_05_ORDERS_ON_6_PUBLIC_K0_TIMES"
MAX_ORDERS_DELTA=.05


def fixed_cases():
    cases=[]
    for fam,entries in (
        ("C00",[(1,1,72,None),(1,3,100,None),(3,1,72,None),
                (3,3,100,None),(1.5,2,72,None),(2,1.5,100,None)]),
        ("C01",[(1,1,72,.25),(1,1,100,1),(1,3,72,6),
                (3,1,100,.25),(3,3,72,1),(2,1.5,100,6)])
    ):
        for tp,td,cap,transit in entries:
            cases.append({"id":f"M_{fam}_{len(cases)+1:02d}",
                          "arm":"M","structure":fam,
                          "preparation_tau_minutes":tp,
                          "dispatch_tau_minutes":td,
                          "capacity_orders_per_hour":cap,
                          "transit_tau_minutes":transit,
                          "transit_capacity_orders_per_hour":100})
    for stocks,cap,tau in ((1,72,1),(2,72,3),(3,100,6)):
        cases.append({"id":f"D_{stocks}_{cap}_{tau}",
                      "arm":"D","structure":f"D{stocks}",
                      "stocks":stocks,"capacity_orders_per_hour":cap,
                      "shared_response_time_minutes":tau,
                      "loss":False})
    return cases


def plan(policy):
    d.parse_policy(policy)
    assert policy["k0"]["public_arrival_pulse"]=={
        "rate_per_minute":1.2,"duration_minutes":20}
    assert policy["resource_ceiling"]["native_G2_verification_max_proposed"]==12
    assert policy["d_method"]["budget"][
        "OpenModelica_candidate_calls_max_proposed"]==3
    cases=fixed_cases()
    assert len([x for x in cases if x["arm"]=="M"])==12
    assert len([x for x in cases if x["arm"]=="D"])==3
    rows=[]
    for row in cases:
        if row["arm"]=="M":
            y=m.curve(m.params(
                row["structure"],
                row["preparation_tau_minutes"],
                row["dispatch_tau_minutes"],
                row["capacity_orders_per_hour"],
                row["transit_tau_minutes"]),1.2)
        else:
            y=d.predicted(
                row["stocks"],row["capacity_orders_per_hour"],
                row["shared_response_time_minutes"],1.2,TIMES)
        rows.append({**row,"public_K0_pulse_rate_per_minute":1.2,
                     "public_K0_pulse_duration_minutes":20,
                     "zero_initial_stocks":True,
                     "native_time_unit":"hours",
                     "comparison_times_minutes":list(TIMES),
                     "comparison_times_hours":[t/60 for t in TIMES],
                     "reference_curve_from_surrogate_not_OMC":list(y),
                     "native_OMC_result":None,
                     "native_full_source_sha256":None,
                     "native_solver_budget_receipt":None,
                     "native_verified":False})
    payload={
        "schema":"igc-caf02-g2-native-correspondence-plan/0.1",
        "state":"PLAN_ONLY_NO_OMC_EXECUTION_NO_PARITY_VERIFIED",
        "policy_sha256":"sha256:"+hashlib.sha256(
            (json.dumps(policy,sort_keys=True,separators=(",",":"),
                        allow_nan=False)+"\n").encode()).hexdigest(),
        "predeclared_comparison_criterion":CRITERION,
        "difference_bound_orders":MAX_ORDERS_DELTA,
        "bound_status":"PROPOSED_NOT_A_CERTIFIED_GLOBAL_SOLVER_ERROR",
        "pulse_scope":"PUBLIC_K0_ONLY_DOES_NOT_CERTIFY_K1_K2",
        "model_identity_requirement":"NATIVE_TOPOLOGY_PARAMETER_UNITS_PULSE_AND_SOURCE_MUST_MATCH_CASE",
        "native_result_missing_is_failure_to_verify_not_a_PASS":True,
        "M_modelica_synthesis":"NOT_PREPARED",
        "D_modelica_synthesis":"NOT_PREPARED",
        "OpenModelica_invocations":0,
        "private_DES_runs":0,
        "K2_truth_read":False,
        "cases":rows,
    }
    return payload


def evaluate_offline_submitted_trace(case,native_time_hours,native_delivered,
                                     *, source_hash=None,
                                     actual_native_receipt=None):
    """Numerical trace comparison is NOT full native source/custody verification.

    Zero attempts / fabricated CSVs cannot be used to claim actual native G2.
    """
    if not (type(native_time_hours) is list
            and len(native_time_hours)==6
            and all(type(x) in (int,float) and math.isfinite(x)
                    for x in native_time_hours)
            and all(abs(a-b)<1e-8 for a,b in
                    zip(native_time_hours,[t/60 for t in TIMES]))):
        raise ValueError("G2_NATIVE_SAMPLE_TIMES_OR_UNITS_DO_NOT_MATCH")
    if not (type(native_delivered) is list and len(native_delivered)==6
            and all(type(x) in (int,float) and math.isfinite(x)
                    and x>=0 for x in native_delivered)
            and all(x<=y+1e-9 for x,y in
                    zip(native_delivered,native_delivered[1:]))
            and all(y<=1.2*min(t,20)+1e-8
                    for y,t in zip(native_delivered,TIMES))):
        raise ValueError("G2_NATIVE_TRACE_PHYSICAL_OR_NUMERICAL_INVALID")
    err=max(abs(y-z) for y,z in zip(
        native_delivered,case["reference_curve_from_surrogate_not_OMC"]))
    return {"max_abs_difference_orders":err,
            "numeric_trace_within_proposed_tolerance":err<=MAX_ORDERS_DELTA,
            "real_native_modelica_source_verified":False,
            "native_execution_independently_verified":False,
            "full_G2_certification":False,
            "source_hash_submitted_not_verified":source_hash,
            "execution_receipt_submitted_not_verified":actual_native_receipt}


if __name__=="__main__":
    print(json.dumps({"status":"CAF02_G2_PLAN_NOT_OMC",
                      "case_count":len(fixed_cases()),
                      "native_calls":0},sort_keys=True))
