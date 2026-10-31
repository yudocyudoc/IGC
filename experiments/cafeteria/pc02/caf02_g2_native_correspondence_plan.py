#!/usr/bin/env python3
"""CAF02 bounded OpenModelica correspondence PLAN -- never runs native models.

Twelve M and three D cases are selected without new-world evidence. K0 and
the two predeclared K1 pulses are used as input profiles, with empty resets.
Several K1 probes deliberately exceed capacity 72/100 orders/hour. A
high-capacity mathematical shadow is computed ONLY to demonstrate that the
capacity limiter changes the tested curve (a witness, NOT a native run).

Real OMC parity still requires separately pinned source, matching graph,
pulse, units, solver CSV and budget receipt. Neither this manifest nor copied
surrogate curves can certify native execution, any K2 result or all grid cases.
"""
import json
import hashlib
import math
import caf02_structural_k0k1k2 as m
import caf02_d_k0k1k2_adapter as d

TIMES=(5,10,15,20,30,40)
CRITERION="MAX_ABS_DELIVERED_DIFFERENCE_LE_0_05_ORDERS_ON_6_SAMPLES_PER_DECLARED_PUBLIC_PULSE"
MAX_ORDERS_DELTA=.05
HIGH_CAPACITY_SHADOW_PER_HOUR=1000000


def fixed_cases():
    """12 M + 3 D, without new topologies, parameters or added G2 attempts.

    The public stress pulse K1_C (108/h) challenges 100/h; K1_B (90/h)
    challenges 72/h. K0 (72/h) remains a nonbinding control.
    """
    cases=[]
    for fam,entries in (
        ("C00",[(1,1,72,None,"K0"),
                (1,3,100,None,"K1_C"),
                (3,1,72,None,"K1_B"),
                (3,3,100,None,"K1_C"),
                (1.5,2,72,None,"K1_C"),
                (2,1.5,100,None,"K1_C")]),
        ("C01",[(1,1,72,.25,"K0"),
                (1,1,100,1,"K1_C"),
                (1,3,72,6,"K1_B"),
                (3,1,100,.25,"K1_C"),
                (3,3,72,1,"K1_C"),
                (2,1.5,100,6,"K1_C")])
    ):
        for tp,td,cap,transit,probe in entries:
            cases.append({"id":f"M_{fam}_{len(cases)+1:02d}",
                          "arm":"M","structure":fam,
                          "preparation_tau_minutes":tp,
                          "dispatch_tau_minutes":td,
                          "capacity_orders_per_hour":cap,
                          "transit_tau_minutes":transit,
                          "transit_capacity_orders_per_hour":100,
                          "public_probe":probe})
    for stocks,cap,tau,probe in ((1,72,1,"K1_B"),
                                 (2,72,3,"K1_C"),
                                 (3,100,1,"K1_C")):
        cases.append({"id":f"D_{stocks}_{cap}_{tau}",
                      "arm":"D","structure":f"D{stocks}",
                      "stocks":stocks,"capacity_orders_per_hour":cap,
                      "shared_response_time_minutes":tau,
                      "loss":False,"public_probe":probe})
    return cases


def prescribed_public_pulses(policy):
    k0=policy["k0"]["public_arrival_pulse"]
    menu=policy["k1"]["menu"]
    if (k0!={"rate_per_minute":1.2,"duration_minutes":20}
        or [(x["rate_per_minute"],x["t_min"],x["duration_minutes"])
            for x in menu]!=[(1.,10,20),(1.5,20,20),(1.8,30,20)]):
        raise ValueError("G2_PUBLIC_PULSES_CHANGED")
    return {
        "K0":{"rate_per_minute":1.2,"duration_minutes":20},
        "K1_B":{"rate_per_minute":1.5,"duration_minutes":20},
        "K1_C":{"rate_per_minute":1.8,"duration_minutes":20},
    }


def surrogate_case(case,rate,capacity_override=None):
    cap=(case["capacity_orders_per_hour"] if capacity_override is None
         else capacity_override)
    if case["arm"]=="M":
        return list(m.curve(m.params(
            case["structure"],
            case["preparation_tau_minutes"],
            case["dispatch_tau_minutes"],
            cap,
            case["transit_tau_minutes"]),rate))
    return list(d.predicted(
        case["stocks"],cap,case["shared_response_time_minutes"],
        rate,TIMES))


def plan(policy):
    d.parse_policy(policy)
    if (policy["resource_ceiling"]["native_G2_verification_max_proposed"]!=12
        or policy["d_method"]["budget"][
            "OpenModelica_candidate_calls_max_proposed"]!=3):
        raise ValueError("G2_NATIVE_BUDGET_CHANGED")
    public=prescribed_public_pulses(policy)
    cases=fixed_cases()
    if (len([x for x in cases if x["arm"]=="M"])!=12
        or len([x for x in cases if x["arm"]=="D"])!=3):
        raise ValueError("G2_CASE_BUDGET_CHANGED")
    rows=[]
    for case in cases:
        pulse=public[case["public_probe"]]
        rate=pulse["rate_per_minute"]
        expected=surrogate_case(case,rate)
        uncapped_shadow=surrogate_case(
            case,rate,capacity_override=HIGH_CAPACITY_SHADOW_PER_HOUR)
        gap=max(abs(a-b) for a,b in zip(expected,uncapped_shadow))
        rows.append({
            **case,
            "public_probe_rate_per_minute":rate,
            "public_probe_duration_minutes":pulse["duration_minutes"],
            "public_probe_input_orders_per_hour":60*rate,
            "input_above_shared_capacity":60*rate>
                 case["capacity_orders_per_hour"],
            "zero_initial_stocks":True,
            "native_time_unit":"hours",
            "comparison_times_minutes":list(TIMES),
            "comparison_times_hours":[t/60 for t in TIMES],
            "reference_curve_from_surrogate_not_OMC":expected,
            "uncapped_shadow_is_surrogate_only":True,
            "capacity_clamp_shadow_gap_max_orders":gap,
            "capacity_clamp_observably_changes_output":gap>0.25,
            "native_OMC_result":None,
            "native_full_source_sha256":None,
            "native_solver_budget_receipt":None,
            "native_verified":False,
        })
    # An input > a nominal capacity is insufficient on its own: we must
    # demonstrate the clamp affects at least one sampled observable in each
    # grammar, BEFORE any native invocation or external K0 observation.
    for family in ("C00","C01","D1","D2","D3"):
        if not any(x["structure"]==family
                   and x["capacity_clamp_observably_changes_output"]
                   for x in rows):
            raise ValueError("G2_NO_ACTIVE_CAPACITY_WITNESS_"+family)
    payload={
        "schema":"igc-caf02-g2-native-correspondence-plan/0.2",
        "state":"PLAN_ONLY_NO_OMC_EXECUTION_NO_PARITY_VERIFIED",
        "policy_sha256":"sha256:"+hashlib.sha256(
            (json.dumps(policy,sort_keys=True,separators=(",",":"),
                        allow_nan=False)+"\n").encode()).hexdigest(),
        "predeclared_comparison_criterion":CRITERION,
        "difference_bound_orders":MAX_ORDERS_DELTA,
        "bound_status":"PROPOSED_NOT_A_CERTIFIED_GLOBAL_SOLVER_ERROR",
        "pulse_scope":"PUBLIC_K0_AND_K1_STRESS_ONLY_NOT_K2_OR_FULL_GRID",
        "public_pulses_used":public,
        "case_counts":{"M":12,"D":3,"total":15},
        "capacity_witness_by_structure":{
            fam:max(x["capacity_clamp_shadow_gap_max_orders"]
                    for x in rows if x["structure"]==fam)
            for fam in ("C00","C01","D1","D2","D3")},
        "high_capacity_shadow_purpose":"SURROGATE_CAPACITY_LIMB_ACTIVATION_DIAGNOSTIC_ONLY",
        "high_capacity_shadow_is_not_native_or_extra_G2_case":True,
        "model_identity_requirement":"NATIVE_TOPOLOGY_PARAMETERS_UNITS_PULSE_SOURCE_AND_RESET_MATCH_CASE",
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
                                     *,source_hash=None,
                                     actual_native_receipt=None):
    """Numerical trace comparison NOT verification of real native execution."""
    if not (type(native_time_hours) is list
            and len(native_time_hours)==6
            and all(type(x) in (int,float) and math.isfinite(x)
                    for x in native_time_hours)
            and all(abs(a-b)<1e-8 for a,b in
                    zip(native_time_hours,[t/60 for t in TIMES]))):
        raise ValueError("G2_NATIVE_SAMPLE_TIMES_OR_UNITS_DO_NOT_MATCH")
    rate=case["public_probe_rate_per_minute"]
    duration=case["public_probe_duration_minutes"]
    if not (type(native_delivered) is list and len(native_delivered)==6
            and all(type(x) in (int,float) and math.isfinite(x)
                    and x>=0 for x in native_delivered)
            and all(x<=y+1e-9 for x,y in
                    zip(native_delivered,native_delivered[1:]))
            and all(y<=rate*min(t,duration)+1e-8
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
    print(json.dumps({"status":"CAF02_G2_CAPACITY_STRESS_PLAN_NOT_OMC",
                      "case_count":len(fixed_cases()),
                      "native_calls":0},sort_keys=True))
