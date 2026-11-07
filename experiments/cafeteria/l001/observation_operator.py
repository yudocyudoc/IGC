"""CAF-L001 joint interval observation operator (arithmetic, not causal inference).

H01 is the video-time origin. Predictions must distinguish H04, H05, H06,
H07. Never relabel continuous cumulative delivery as two physical receipts
without an explicit, verified observable-to-event mapping.
"""
from __future__ import annotations
import math
import numpy as np
from scipy.optimize import linprog
from experiments.cafeteria.l001.reference import (
    NODES, coefficient, constraints, read_metrics
)

SCHEMA = "igc-caf-l001-interval-operator/0.1"
TIMEBASE = "VIDEO_SECONDS_RELATIVE_H01"
EPS = 1e-6

def require(ok, reason):
    if not ok: raise ValueError(reason)

def normalize(bounds):
    require(type(bounds) is dict and set(bounds) == set(NODES),
            "NEED_H04_H05_H06_H07_SEPARATELY")
    parsed = {}
    for n in NODES:
        pair = bounds[n]
        require(type(pair) in (list,tuple) and len(pair)==2
                and all(type(x) in (int,float) and math.isfinite(x) for x in pair),
                "INVALID_EVENT_INTERVAL:"+n)
        lo, hi = map(float,pair)
        require(0<=lo<=hi,"INVALID_EVENT_BOUNDS:"+n)
        parsed[n] = (lo,hi)
    return parsed

def order_matrix():
    rows = []
    for first,last in (("H04","H05"),("H05","H06"),("H06","H07")):
        c=np.zeros(4);c[NODES.index(first)]=1;c[NODES.index(last)]=-1
        rows.append(c)
    return np.asarray(rows),np.zeros(3)

def opt(c,a,b,bounds):
    return linprog(c,A_ub=a,b_ub=b,bounds=bounds,method="highs")

def extrema(c,a,b,bounds):
    low=opt(c,a,b,bounds)
    high=opt(-c,a,b,bounds)
    require(low.success and high.success,"OPERATOR_OPTIMIZATION_FAILED")
    return float(low.fun), float(-high.fun)

def compatibility(event_bounds, *, timebase=TIMEBASE, metrics=None):
    """Joint existential/robust set-valued assessment, never an independent 9-row score."""
    require(timebase==TIMEBASE,"TIMEBASE_NOT_COMPARABLE")
    candidate=normalize(event_bounds)
    metrics=read_metrics() if metrics is None else metrics
    require(set(metrics)=={f"F{i:02d}" for i in range(1,10)},"METRIC_SET_CHANGED")
    bounds=[candidate[n] for n in NODES]
    order_a,order_b=order_matrix()
    if not opt(np.zeros(4),order_a,order_b,bounds).success:
        return {"schema":SCHEMA,"status":"INVALID_MODEL_INTERNAL_ORDER",
                "science_status":"NUMERICAL_DIAGNOSTIC_ONLY",
                "metric_tests":"NOT_RUN","timebase":TIMEBASE}
    obs_a,obs_b=constraints(metrics)
    intersection=opt(np.zeros(4),np.vstack((order_a,obs_a)),
                     np.concatenate((order_b,obs_b)),bounds)
    details={}
    disjoint=[]
    fully_inside=True
    max_violation=0.0
    is_point=all(lo==hi for lo,hi in candidate.values())
    for key,item in sorted(metrics.items()):
        c=coefficient(item)
        lo,hi=extrema(c,order_a,order_b,bounds)
        obs_lo,obs_hi=item["bounds"]
        if hi<obs_lo-EPS or lo>obs_hi+EPS:disjoint.append(key)
        if lo<obs_lo-EPS or hi>obs_hi+EPS:fully_inside=False
        if is_point and key!="F09":
            max_violation=max(max_violation,max(0.0,obs_lo-lo,lo-obs_hi))
        details[key]={"candidate_min":round(lo,7),"candidate_max":round(hi,7),
                      "observed_bounds":[obs_lo,obs_hi],
                      "derived_not_independent":key=="F09"}
    if not intersection.success:
        status="INCOMPATIBLE_JOINT_CONSTRAINTS"
    elif fully_inside:
        status="COMPATIBLE_ROBUST"
    else:
        status="COMPATIBLE_EXISTENTIAL_ONLY"

    # A huge model interval which contains the entire observed feasible
    # region is a non-discriminating prediction, even if it passes existentially.
    full_obs_region_covered=True
    for i,name in enumerate(NODES):
        unit=np.zeros(4);unit[i]=1
        low,high=extrema(unit,obs_a,obs_b,[(None,None)]*4)
        if candidate[name][0]>low+EPS or candidate[name][1]<high-EPS:
            full_obs_region_covered=False
            break
    return {
        "schema":SCHEMA,"status":status,
        "science_status":"NUMERICAL_DIAGNOSTIC_ONLY_NOT_PROSPECTIVE",
        "timebase":TIMEBASE,
        "metric_tests":details,
        "disjoint_metric_ids":disjoint,
        "joint_incompatibility_without_individual_disjoint":
            status=="INCOMPATIBLE_JOINT_CONSTRAINTS" and not disjoint,
        "reference_region_fully_covered_by_candidate":full_obs_region_covered,
        "model_event_intervals":{n:list(v) for n,v in candidate.items()},
        "point_max_violation_F01_F08_video_s":round(max_violation,7) if is_point else None,
        "F09_derived_from_F07_F08":True,
        "no_additive_metric_score":True,
        "physical_clock_certified":False,
        "note":"Intervals are sets of possible event times, not service distributions. "
               "An existential overlap is not a validated prediction; all bounds "
               "share a single lot and F09 is derived from F07/F08."
    }

def native_projection_gate(outputs,common_evidence):
    """Fail-closed mapping audit for all three native, actually available outputs."""
    require(set(outputs)=={"D","B","M"},"MUST_HAVE_THREE_ARMS")
    gates={}
    for arm in ("D","B","M"):
        obj=outputs[arm]
        native,submission=obj["native"],obj["submission"]
        require(submission["arm_id"]==arm
                and submission["evidence_refs"]==[common_evidence["source_snapshot_hash"]],
                "NATIVE_EVIDENCE_OR_ARM_MISMATCH")
        if arm=="D":
            require(native["method"]=="D_GENERIC_CONSERVATIVE_CHAIN_NATIVE"
                    and native["candidate_models_for_L001"]==0,"D_NATIVE_GATE_CHANGED")
            why="D_NO_INDIVIDUAL_RECEIPT_OPERATOR_OR_PARAMETERS"
        elif arm=="B":
            require(native["state"]=="STAGED_NOT_SENT"
                    and native["provider_calls"]==0,"B_NATIVE_GATE_CHANGED")
            why="B_PROVIDER_NOT_RUN_NO_NATIVE_CANDIDATE"
        else:
            require(native["candidate_selection"]=="UNRESOLVED"
                    and native["common_stimulus_translation"]=="NOT_IMPLEMENTED"
                    and not submission["hypothesis_ids"],"M_NATIVE_GATE_CHANGED")
            why="M_ENGINEERING_LIBRARY_NO_EVENT_PROJECTION"
        gates[arm]={
            "arm":arm,"status":"NOT_SCORABLE","reason":why,
            "native_artifact_sha256":submission["native_artifact_sha256"],
            "observable_projection":None,"L001_comparison":"NOT_RUN",
            "native_status":submission["status"]
        }
    return {
        "schema":"igc-caf-l001-three-arm-observation-gate/0.1",
        "shared_source_sha256":common_evidence["source_snapshot_hash"],
        "arms":gates,
        "requires_before_scoring":[
            "NATIVE_ARM_CANDIDATE_SELECTED",
            "VERIFIED_OPENMODELICA_NATIVE_SIMULATION",
            "PHYSICALLY_DEFENDED_H04_H05_H06_H07_PROJECTION",
            "H01_VIDEO_TIMEBASE_MAPPING",
            "CANDIDATE_LOCKED_BEFORE_OBSERVATION_SCORING"
        ],
        "control_fixtures_are_not_arm_predictions":True,
        "provider_calls":0,"modelica_runs":0
    }
