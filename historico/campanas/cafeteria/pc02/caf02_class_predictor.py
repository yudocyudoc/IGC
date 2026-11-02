#!/usr/bin/env python3
"""CAF02 preparation: construction-only calibration over C00 observable classes.

NO existing CAF01 holdout is read; NO DES, native solver, provider, secrets,
or independently scored evaluation is executed. No world for CAF02 exists yet.
A proposed policy and a synthetic fixture are NOT a scientific preregistration.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import median

POLICY_SCHEMA = "igc-caf02-class-calibration-policy/0.1"
CONSTRUCTION_SCHEMA = "igc-caf02-construction-public/0.1"
SCHEMA = "igc-caf02-class-forecast-proposal/0.1"
TIMES = (0, 5, 10, 15, 20, 30, 40)
DT_MIN = 0.025
NUMERICAL_ERROR_MAX = 0.005
EXCLUDE_IDS = {"CAF01", "CAFN"}
PROHIBITED_FUTURE_KEYS = {
    "evaluation_observations", "evaluation_delivered", "holdout",
    "future_truth", "evaluation_truth", "private_config", "nonce_hex",
}


class Blocked(ValueError):
    pass


def need(ok, code):
    if not ok:
        raise Blocked(code)


def number(v):
    return type(v) in (int,float) and math.isfinite(v)


def canonical(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=False,
                      separators=(",",":"),allow_nan=False).encode()


def digest(value):
    return "sha256:"+hashlib.sha256(canonical(value)).hexdigest()


def check_exact(value, keys, code):
    need(type(value) is dict and set(value)==set(keys),code)


def check_pulse(p):
    check_exact(p,("rate_per_minute","duration_minutes"),"BAD_PULSE_KEYS")
    need(number(p["rate_per_minute"]) and 0 < p["rate_per_minute"] <= 3
         and p["duration_minutes"] == 20,"BAD_PUBLIC_PULSE")
    return p["rate_per_minute"]


def validate_policy(policy):
    check_exact(policy,(
        "schema","campaign_id","status","construction_pulse",
        "future_public_pulse","response_times_preparation_minutes",
        "response_times_dispatch_minutes","shared_capacities_per_hour",
        "compatibility_mae_allowance_orders",
        "absolute_max_construction_MAE_orders",
        "point_max_envelope_width_orders","operational_basis",
        "future_truth_available","independent_world_custody_verified",
        "independent_forecast_custody_verified",
    ),"POLICY_EXACT_FIELDS_REQUIRED")
    need(policy["schema"]==POLICY_SCHEMA
         and policy["campaign_id"]=="CAF02"
         and policy["status"]=="DRAFT_NOT_OPERATIONALLY_APPROVED"
         and policy["future_truth_available"] is False
         and policy["independent_world_custody_verified"] is False
         and policy["independent_forecast_custody_verified"] is False,
         "NOT_AN_AUTHORIZED_PROSPECTIVE_POLICY")
    construction_rate=check_pulse(policy["construction_pulse"])
    future_rate=check_pulse(policy["future_public_pulse"])
    need(policy["construction_pulse"]["duration_minutes"] ==
         policy["future_public_pulse"]["duration_minutes"] == 20,
         "PULSE_HORIZON_CHANGED")
    p=policy["response_times_preparation_minutes"]
    d=policy["response_times_dispatch_minutes"]
    capacities=policy["shared_capacities_per_hour"]
    need(type(p) is list and type(d) is list and type(capacities) is list
         and 1 <= len(p) <= 20 and 1 <= len(d) <= 20
         and 1 <= len(capacities) <= 12,
         "MISSING_OR_OVERSIZED_PARAMETER_GRID")
    for grid in (p,d,capacities):
        need(all(number(x) and x>0 for x in grid)
             and len(set(grid))==len(grid),"BAD_OR_DUPLICATE_GRID")
    need(all(x>=0.5 and x<=120 for x in p+d)
         and all(5<=x<=240 for x in capacities),
         "OUT_OF_SCOPE_PARAMETER_GRID")
    need(number(policy["compatibility_mae_allowance_orders"])
         and 0<=policy["compatibility_mae_allowance_orders"]<=3
         and number(policy["absolute_max_construction_MAE_orders"])
         and 0<=policy["absolute_max_construction_MAE_orders"]<=10
         and number(policy["point_max_envelope_width_orders"])
         and 0<=policy["point_max_envelope_width_orders"]<=5,
         "INVALID_PROPOSED_THRESHOLDS")
    need(type(policy["operational_basis"]) is dict
         and policy["operational_basis"].get("status") ==
             "NOT_YET_JUSTIFIED"
         and policy["operational_basis"].get("responseTime_interpretation") ==
             "AGGREGATE_STOCK_TO_OUTFLOW_NOT_PER_ORDER_SERVICE_DURATION",
         "OPERATIONAL_BASIS_MUST_REMAIN_OPEN")
    need(len(p)*len(d)*len(capacities)<=2500,"TOO_MANY_CANDIDATES")
    return construction_rate,future_rate


def validate_construction(evidence,policy):
    check_exact(evidence,(
        "schema","campaign_id","world_public_commitment_sha256",
        "public_pulse","observations","data_provenance",
    ),"CONSTRUCTION_EXACT_FIELDS_REQUIRED_NO_FUTURE_TRUTH")
    need(evidence["schema"]==CONSTRUCTION_SCHEMA
         and evidence["campaign_id"]==policy["campaign_id"]
         and evidence["campaign_id"] not in EXCLUDE_IDS
         and evidence["public_pulse"]==policy["construction_pulse"]
         and type(evidence["world_public_commitment_sha256"]) is str
         and len(evidence["world_public_commitment_sha256"])==71
         and evidence["world_public_commitment_sha256"].startswith("sha256:")
         and all(c in "0123456789abcdef" for c in
                 evidence["world_public_commitment_sha256"][7:]),
         "CONSTRUCTION_NEW_WORLD_PROVENANCE_INVALID")
    provenance=evidence["data_provenance"]
    check_exact(provenance,("source_kind","synthetic_fixture","witness_verified"),
                "BAD_CONSTRUCTION_PROVENANCE")
    need(provenance["source_kind"]=="PROPOSED_CONSTRUCTION_PUBLIC_ONLY"
         and provenance["synthetic_fixture"] is True
         and provenance["witness_verified"] is False,
         "ONLY_SYNTHETIC_PREFLIGHT_IS_SUPPORTED_NOT_REAL_WORLD")
    obs=evidence["observations"]
    need(type(obs) is list and len(obs)==len(TIMES),"BAD_OBSERVATIONS_COUNT")
    need(all(type(r) is dict and set(r)=={"t_min","delivered"}
             for r in obs) and [r["t_min"] for r in obs]==list(TIMES),
         "BAD_OBSERVATION_TIMES_OR_FIELDS")
    values=[r["delivered"] for r in obs]
    arrivals=[policy["construction_pulse"]["rate_per_minute"]
              *min(t,20) for t in TIMES]
    need(values[0]==0 and all(type(x) is int and x>=0 for x in values)
         and all(a<=b for a,b in zip(values,values[1:]))
         and all(d<=a+1 for d,a in zip(values,arrivals)),
         "BAD_SYNTHETIC_CONSTRUCTION_PHYSICAL_BOUNDS")
    return values[1:]


def integrate_c00(tau_p,tau_d,cap_per_hour,rate,duration=20,step=DT_MIN):
    """Approximate unchanged E1 C00 molecules with conservative Heun steps.

    Two stages have *independent aggregate response-time parameters*, with
    identical cap. No DES truth and no extra physics. Input is pulse only.
    """
    need(all(number(x) and x>0 for x in
             (tau_p,tau_d,cap_per_hour,rate,duration,step))
         and duration==20
         and abs(40/step-round(40/step))<1e-9
         and abs(duration/step-round(duration/step))<1e-9,
         "BAD_NUMERICAL_DESIGN")
    cap=cap_per_hour/60.0
    p=d=y=0.0
    samples=[]
    indexes={round(t/step):t for t in TIMES[1:]}
    def f(x,z,a):
        op=min(cap,max(0.0,x)/tau_p)
        od=min(cap,max(0.0,z)/tau_d)
        return a-op,op-od,od
    for k in range(1,round(40/step)+1):
        input_rate=rate if (k-1)*step<duration-1e-9 else 0.0
        p1,d1,y1=f(p,d,input_rate)
        p2,d2,y2=f(p+step*p1,d+step*d1,input_rate)
        p+=step*(p1+p2)/2
        d+=step*(d1+d2)/2
        y+=step*(y1+y2)/2
        arrivals=rate*min(k*step,duration)
        need(min(p,d,y)>=-1e-8 and
             abs(p+d+y-arrivals)<1e-6,
             "C00_NATIVE_MATERIAL_BALANCE_FAILED")
        if k in indexes:
            need(y>=-1e-8 and y<=arrivals+1e-8,
                 "C00_IMPOSSIBLE_DELIVERY")
            samples.append(y)
    need(len(samples)==6 and all(a<=b for a,b in zip(samples,samples[1:])),
         "NONMONOTONE_PREDICTION")
    return samples


def construction_only_references(obs,construction_rate,future_rate):
    """Fixed rules from G4, recomputed only with public construction.

    REF-CAF estimates a public effective delivery rate, not a physical DES
    capacity; REF-SCALE proportionally transfers deliveries. No future truth.
    """
    c=[0,*obs]
    eligible=[]
    for i in range(4):
        a,b=TIMES[i:i+2]
        if (construction_rate*a-c[i] > 1
            and construction_rate*b-c[i+1] > 1):
            eligible.append((c[i+1]-c[i])/(b-a))
    ref_caf = None
    if len(eligible)>=2:
        mu=float(median(eligible))
        ref_caf={
            "status":"READY_EMPIRICAL_ONLY_NOT_PHYSICAL_CAPACITY",
            "mu_effective_orders_per_min":mu,
            "predicted_delivered":[min(future_rate*min(t,20),mu*t)
                                   for t in TIMES[1:]],
            "construction_rate_samples":eligible,
        }
    else:
        ref_caf={"status":"ABSTAIN_FEWER_THAN_TWO_SATURATED_CONSTRUCTION_WINDOWS",
                 "predicted_delivered":None,
                 "construction_rate_samples":eligible}
    ref_scale={
        "status":"READY_PROPORTIONALITY_CONTROL",
        "ratio":future_rate/construction_rate,
        "predicted_delivered":[min(future_rate*min(t,20),
                                   future_rate/construction_rate*y)
                               for t,y in zip(TIMES[1:],obs)],
    }
    return {"REF_CAF":ref_caf,"REF_SCALE":ref_scale}


def model_group_key(tau_p,tau_d,cap,construction_rate):
    """Guaranteed equal outputs during construction, not on any future pulse."""
    if cap>=construction_rate*60 - 1e-9:
        return ("NONBINDING_AT_CONSTRUCTION",*sorted((tau_p,tau_d)))
    # Saturation is nonlinear: do not assume exchanging response times is safe.
    return ("POSSIBLY_BINDING",cap,tau_p,tau_d)


def fit(policy,evidence):
    rate,future_rate=validate_policy(policy)
    obs=validate_construction(evidence,policy)
    grid=[]
    for tp in policy["response_times_preparation_minutes"]:
        for td in policy["response_times_dispatch_minutes"]:
            for cap in policy["shared_capacities_per_hour"]:
                preds=integrate_c00(tp,td,cap,rate)
                coarse=integrate_c00(tp,td,cap,rate,step=0.05)
                need(max(abs(a-b) for a,b in zip(preds,coarse))
                     <=NUMERICAL_ERROR_MAX,
                     "C00_CONSTRUCTION_NOT_NUMERICALLY_CONVERGED")
                mae=sum(abs(x-y) for x,y in zip(preds,obs))/6
                grid.append({
                    "tau_preparation_minutes":tp,
                    "tau_dispatch_minutes":td,
                    "capacity_per_hour":cap,
                    "MAE_construction":mae,
                    "construction_delivered":preds,
                    "construction_class_key":model_group_key(tp,td,cap,rate),
                })
    best=min(x["MAE_construction"] for x in grid)
    relative_ceiling=best+policy["compatibility_mae_allowance_orders"]
    absolute_ceiling=policy["absolute_max_construction_MAE_orders"]
    threshold=min(relative_ceiling,absolute_ceiling)
    # Absolute adequacy gate: no candidate survives when even the best
    # model fails to explain construction. Narrow agreement is insufficient.
    compatible=[x for x in grid
                if x["MAE_construction"] <= threshold+1e-12]
    # A class of construction-equivalent variants MUST retain every nominal
    # member before changing the input; some may diverge under future load.
    classes={}
    for member in compatible:
        key=tuple(member["construction_class_key"])
        classes.setdefault(key,[]).append(member)
    class_reports=[]
    all_future_curves=[]
    for key,members in sorted(classes.items(),key=lambda x:str(x[0])):
        ref=members[0]["construction_delivered"]
        if key[0]=="NONBINDING_AT_CONSTRUCTION":
            need(all(max(abs(a-b) for a,b in zip(
                ref,m["construction_delivered"]))<=1e-8
                for m in members),
                "CONSTRUCTION_EQUIVALENCE_INVALID")
        projections=[]
        for m in members:
            future=integrate_c00(
                m["tau_preparation_minutes"],
                m["tau_dispatch_minutes"],m["capacity_per_hour"],
                future_rate)
            projections.append(future)
            all_future_curves.append(future)
        lower=[min(p[i] for p in projections) for i in range(6)]
        upper=[max(p[i] for p in projections) for i in range(6)]
        class_reports.append({
            "construction_equivalence_key":list(key),
            "members":members,
            "future_public_input_member_predictions":projections,
            "future_envelope_min":lower,
            "future_envelope_max":upper,
            "future_max_width_orders":max(b-a for a,b in zip(lower,upper)),
            "internal_stage_parameters_identified":False,
            "class_remains_equivalent_in_future":
                max(b-a for a,b in zip(lower,upper))<=1e-8,
        })
    adequate=bool(compatible)
    low=([min(x[i] for x in all_future_curves) for i in range(6)]
         if adequate else None)
    high=([max(x[i] for x in all_future_curves) for i in range(6)]
          if adequate else None)
    width=(max(b-a for a,b in zip(low,high)) if adequate else None)
    authorized_width=policy["point_max_envelope_width_orders"]
    admissible=adequate and width<=authorized_width
    mid=[(a+b)/2 for a,b in zip(low,high)] if admissible else None
    if not adequate:
        point_status="NO_ADEQUATE_CANDIDATE_ABSTAIN_ALL_FORECASTS"
    elif not admissible:
        point_status="ABSTAIN_POINT_COMPATIBLE_FORECASTS_DIVERGE"
    else:
        point_status="ILLUSTRATIVE_MID_ENVELOPE_NOT_A_SEALED_FORECAST"
    return {
        "schema":SCHEMA,
        "status":"SYNTHETIC_FIXTURE_EXPLORATORY_NO_WORLD_NO_PROSPECTIVE_FORECAST",
        "campaign_id":"CAF02",
        "input_policy_sha256":digest(policy),
        "input_construction_sha256":digest(evidence),
        "construction_only_observed_delivered":obs,
        "future_truth_seen":False,
        "independent_world_custody_verified":False,
        "independent_forecast_custody_verified":False,
        "evaluation_authorized":False,
        "world_DES_invocations":0,
        "Modelica_solver_invocations":0,
        "provider_inferences":0,
        "forecast_model":"UNCHANGED_E1_C00_TWO_BOUNDED_QUEUES",
        "selection_rule":
            "MAE <= MIN(MIN_GRID_MAE + ALLOWANCE, ABSOLUTE_ADEQUACY_CEILING)",
        "construction_best_MAE":best,
        "absolute_construction_adequacy_ceiling_MAE":absolute_ceiling,
        "absolute_construction_adequacy_pass":adequate,
        "construction_compatibility_threshold_MAE":threshold,
        "nominal_grid_candidates":len(grid),
        "nominal_compatible_candidates":len(compatible),
        "construction_equivalent_classes":len(classes),
        "construction_class_details":class_reports,
        "frozen_rule_reference_proposals_construction_only":
            construction_only_references(obs,rate,future_rate),
        "full_compatible_envelope_lower":low,
        "full_compatible_envelope_upper":high,
        "full_compatible_envelope_max_width_orders":width,
        "draft_point_width_threshold_orders":authorized_width,
        "point_status":point_status,
        "illustrative_point_mid_envelope":mid,
        "parameters_identified_as_individual_stage_times":False,
        "predictions_included_not_truth":True,
        "important_warning":
            "CONSTRUCTION_EQUIVALENCE_DOES_NOT_IMPLY_FUTURE_EQUIVALENCE",
        "interpretation":
            "IN_SAMPLE_SYNTHETIC_DRY_RUN_ONLY_NEVER_CLAIM_PROSPECTIVE_VALIDATION",
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--policy",required=True)
    p.add_argument("--construction",required=True)
    p.add_argument("--output-dir",required=True)
    args=p.parse_args()
    out=Path(args.output_dir)
    need(not out.exists(),"OUTPUT_ALREADY_EXISTS")
    policy=json.loads(Path(args.policy).read_bytes())
    construction=json.loads(Path(args.construction).read_bytes())
    report=fit(policy,construction)
    out.mkdir(parents=True)
    data=canonical(report)+b"\n"
    (out/"CLASS_FORECAST_DRY_RUN.json").write_bytes(data)
    (out/"CLASS_FORECAST_DRY_RUN.sha256").write_text(
        hashlib.sha256(data).hexdigest()+"  CLASS_FORECAST_DRY_RUN.json\n")
    print("CAF02_SYNTHETIC_CLASS_CALIBRATION_PASS_NOT_AUTHORIZED")
    print("NOMINAL_COMPATIBLE="+str(report["nominal_compatible_candidates"]))
    print("CONSTRUCTION_EQUIVALENT_CLASSES="+str(
        report["construction_equivalent_classes"]))
    print("ABSOLUTE_ADEQUACY_PASS="+str(report["absolute_construction_adequacy_pass"]))
    print("FUTURE_ENVELOPE_MAX_WIDTH="+str(
        report["full_compatible_envelope_max_width_orders"]))
    print("FUTURE_POINT_STATUS="+report["point_status"])
    print("DES=0 OMC=0 BUFFALO=0 HOLDOUT_TRUTH=NOT_READ")


if __name__=="__main__":
    main()
