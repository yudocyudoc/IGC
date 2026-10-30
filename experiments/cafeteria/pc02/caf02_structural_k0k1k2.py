#!/usr/bin/env python3
"""CAF-02 structural discrimination/revision design, SYNTHETIC/READ-ONLY ONLY.

Existing E1 material families: C00 preparation->dispatch->receipt and C01
preparation->dispatch->transit->receipt. No new molecule or physical law.
This is only a numerical surrogate for investigating whether the *available*
observables could separate CALIBRATED rivals; no native G2 claim.

K0 construction (limited observations) -> choose K1 evidence design before
seeing its response -> K1 update -> seal both K0/K1 future proposals -> K2
independent adjudication remains NOT AUTHORIZED and NOT EXECUTED.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from caf02_class_predictor import Blocked, need, number, canonical

T_VALUES=(5,10,15,20,30,40)
DURATION=20.0
HORIZON=40.0
STEP=.05
FAMILIES=("C00","C01")
HERE=Path(__file__).resolve().parent
E1=HERE.parents[1]/"e1"/"registry.base.json"


def verify_existing_repertoire():
    """Pin conceptual topology to the actual E1 role registry, not a new model."""
    data=json.loads(E1.read_text(encoding="utf-8"))
    roles=data["roles"]
    need(roles["preparation"]["class_id"]=="bounded-queue"
         and roles["dispatch"]["class_id"]=="bounded-queue"
         and roles["transit"]["class_id"]=="bounded-queue"
         and roles["receipt"]["class_id"]=="delivery-counter"
         and roles["source"]["class_id"]=="accepted-source"
         and data["new_classes"] == []
         and data["mandatory_roles"] == [
             "source","preparation","dispatch","receipt"],
         "E1_MOLECULE_REPERTOIRE_CHANGED")
    return {
        "C00":["preparation","dispatch"],
        "C01":["preparation","dispatch","transit"],
        "source":"experiments/e1/registry.base.json",
        "registry_file_sha256":"sha256:"+hashlib.sha256(E1.read_bytes()).hexdigest(),
    }


def simulate(family,tau_p,tau_d,shared_cap_per_hour,
             tau_transit,rate,duration=DURATION,step=STEP):
    """E1 BoundedQueue release=min(capacity, stock/tau), no source DES.

    Transit cap fixed at 100/h matching registered E1 default. Stage stocks
    are conserved. C01 tau transit is explicit separate parameter.
    """
    need(family in FAMILIES,"UNREGISTERED_STRUCTURE")
    need(all(number(x) and x>0 for x in
             (tau_p,tau_d,shared_cap_per_hour,tau_transit,rate,step))
         and duration==20 and 40/step==round(40/step),
         "INVALID_SYNTHETIC_DESIGN_INPUT")
    n=2 if family=="C00" else 3
    tau=[tau_p,tau_d]+([tau_transit] if n==3 else [])
    cap=[shared_cap_per_hour/60]*2+([100/60] if n==3 else [])
    stocks=[0.0]*n
    delivered=0.0
    sampled={}
    def rhs(s,incoming):
        releases=[min(ci,max(0.0,x)/ti)
                  for x,ti,ci in zip(s,tau,cap)]
        inflows=[incoming]+releases[:-1]
        return [a-b for a,b in zip(inflows,releases)],releases[-1]
    for j in range(1,round(HORIZON/step)+1):
        t0=(j-1)*step
        incoming=rate if t0<duration-1e-8 else 0.0
        a,b=rhs(stocks,incoming)
        predictor=[x+step*dx for x,dx in zip(stocks,a)]
        c,d=rhs(predictor,incoming)
        stocks=[x+step*(dx+dz)/2
                for x,dx,dz in zip(stocks,a,c)]
        delivered+=step*(b+d)/2
        accepted=rate*min(j*step,duration)
        need(min(*stocks,delivered)>-1e-7
             and abs(sum(stocks)+delivered-accepted)<1e-6,
             "STRUCTURAL_SURROGATE_MATERIAL_BALANCE")
        minute=j*step
        if any(abs(minute-t)<step/100 for t in T_VALUES):
            sampled[int(round(minute))]=delivered
    need(set(sampled)==set(T_VALUES),"STRUCTURAL_SURROGATE_MISSING_TIMES")
    return [sampled[t] for t in T_VALUES]


def params(family,p,d,c,transit):
    return {"structure":family,"tau_preparation_minutes":p,
            "tau_dispatch_minutes":d,"capacity_per_hour":c,
            "tau_transit_minutes":transit if family=="C01" else None}


def curve(m,rate):
    return simulate(m["structure"],m["tau_preparation_minutes"],
                    m["tau_dispatch_minutes"],m["capacity_per_hour"],
                    m["tau_transit_minutes"] or 1,rate)


def k0_calibrate(observed,rate,times_indices,parameter_grid,
                 absolute_max_mae,relative_allowance):
    """Same ranges and scoring budget for both rivals.

    Exploratory rule: adequacy per family first; relative proximity *within*
    family; do not let a bad family survive just for being its own best.
    """
    verify_existing_repertoire()
    need(type(observed) is list and len(observed)==6
         and all(number(x) for x in observed)
         and type(times_indices) is list
         and 1<=len(times_indices)<=5
         and len(set(times_indices))==len(times_indices)
         and all(type(i) is int and 0<=i<6 for i in times_indices)
         and number(rate) and 0<rate<=3
         and number(absolute_max_mae) and 0<=absolute_max_mae<=10
         and number(relative_allowance) and 0<=relative_allowance<=3,
         "INVALID_K0_EXPLORATORY_POLICY")
    # Same tau/preparation and tau/dispatch/cap grid for both. C01's
    # additional transit tau is declared and never leaked from a DES.
    need(set(parameter_grid)=={"preparation_tau","dispatch_tau",
                               "shared_cap","transit_tau"},
         "K0_GRID_FIELDS_CHANGED")
    for values in parameter_grid.values():
        need(type(values) is list and 1<=len(values)<=12
             and len(set(values))==len(values)
             and all(number(v) and v>0 for v in values),
             "INVALID_K0_PARAM_GRID")
    universe=[]
    for family in FAMILIES:
        for p in parameter_grid["preparation_tau"]:
            for d in parameter_grid["dispatch_tau"]:
                for c in parameter_grid["shared_cap"]:
                    for transit in (parameter_grid["transit_tau"]
                                    if family=="C01" else [None]):
                        m=params(family,p,d,c,transit)
                        y=curve(m,rate)
                        error=sum(abs(y[i]-observed[i])
                                  for i in times_indices)/len(times_indices)
                        universe.append({**m,"k0_mae":error,
                                         "k0_delivered":y})
    result={}
    for family in FAMILIES:
        rows=[x for x in universe if x["structure"]==family]
        best=min(x["k0_mae"] for x in rows)
        cutoff=min(absolute_max_mae,best+relative_allowance)
        remaining=[x for x in rows if x["k0_mae"] <= cutoff+1e-12]
        result[family]={
            "best_k0_mae":best,
            "passes_absolute_adequacy":best<=absolute_max_mae+1e-12,
            "eligible":remaining,
            "all_evaluated":len(rows),
            "absolute_max_mae":absolute_max_mae,
        }
    return result


def observable_envelope(rows,rate,t_index):
    need(rows and 0<=t_index<6,"NO_CANDIDATES_FOR_ENVELOPE")
    vals=[curve(m,rate)[t_index] for m in rows]
    return min(vals),max(vals)


def expanded_interval_separation(a, b, residual_tolerance, numerical_guard):
    """Disjointness of entire K0 family prediction intervals after K1 error.

    Both families receive the same permitted absolute residual and numerical
    allowance. A raw gap <= 2*(residual+numerical) cannot guarantee a unique
    K1 classification. This is a conservative operational allowance, not an
    independently certified global integration-error bound.
    """
    need(all(number(v) for v in (*a, *b, residual_tolerance, numerical_guard))
         and a[0]<=a[1] and b[0]<=b[1]
         and residual_tolerance>=0 and numerical_guard>=0,
         "BAD_K1_EXPANDED_INTERVAL_INPUT")
    error=residual_tolerance+numerical_guard
    expanded_a=(a[0]-error,a[1]+error)
    expanded_b=(b[0]-error,b[1]+error)
    raw_gap=max(0.0,a[0]-b[1],b[0]-a[1])
    expanded_gap=max(0.0,expanded_a[0]-expanded_b[1],
                         expanded_b[0]-expanded_a[1])
    return {"raw_gap_orders":raw_gap,
            "expanded_gap_orders":expanded_gap,
            "expanded_C00_interval":list(expanded_a),
            "expanded_C01_interval":list(expanded_b),
            "per_family_total_residual_tolerance_orders":error}


def select_k1_measurement(k0, menu, minimum_robust_gap,
                          absolute_residual_max, numerical_guard_orders):
    """Precommit K1 menu and the EXACT tolerance used for its later revision.

    Comparisons use *entire calibrated parameter sets* and expanded
    intervals. No K1 measurement or result is read at selection time.
    """
    need(set(k0)==set(FAMILIES),"TWO_EXPLICIT_RIVALS_REQUIRED")
    need(type(menu) is list and 1<=len(menu)<=10
         and all(number(v) and 0<=v<=10 for v in
                 (minimum_robust_gap,absolute_residual_max,
                  numerical_guard_orders)),
         "INVALID_K1_TOLERANCE_OR_MENU")
    candidates=[]
    policy={
        "minimum_expanded_nonoverlap_gap_orders":minimum_robust_gap,
        "absolute_residual_max_orders":absolute_residual_max,
        "numerical_guard_orders":numerical_guard_orders,
        "effective_revision_tolerance_orders":
            absolute_residual_max+numerical_guard_orders,
    }
    if any(not k0[f]["eligible"] for f in FAMILIES):
        return {"status":"K0_NO_TWO_ADEQUATE_STRUCTURES",
                "proposed_measurement":None,"all_menu_scores":[],
                "precommitted_policy":policy,
                "evidence_result_read":False}
    for option in menu:
        need(type(option) is dict and
             set(option)=={"rate_per_minute","t_min"}
             and number(option["rate_per_minute"])
             and 0<option["rate_per_minute"]<=3
             and type(option["t_min"]) is int
             and option["t_min"] in T_VALUES,
             "INVALID_K1_OBSERVABLE")
        i=T_VALUES.index(option["t_min"])
        intervals={f:observable_envelope(
            k0[f]["eligible"],option["rate_per_minute"],i)
            for f in FAMILIES}
        a,bb=intervals["C00"],intervals["C01"]
        separation=expanded_interval_separation(
            a,bb,absolute_residual_max,numerical_guard_orders)
        candidates.append({
            "measurement":option,
            "k0_calibrated_C00_interval":list(a),
            "k0_calibrated_C01_interval":list(bb),
            "raw_nonoverlap_gap_orders":separation["raw_gap_orders"],
            "robust_nonoverlap_gap_orders":separation["expanded_gap_orders"],
            "expanded_C00_interval":separation["expanded_C00_interval"],
            "expanded_C01_interval":separation["expanded_C01_interval"],
        })
    selected=max(enumerate(candidates),
                 key=lambda item:(item[1]["robust_nonoverlap_gap_orders"],
                                  -item[0]))[1]
    # Boundary contact is ambiguity, even if minimum_robust_gap=0.
    possible=(selected["robust_nonoverlap_gap_orders"]>0
              and selected["robust_nonoverlap_gap_orders"]+1e-10>=
                  minimum_robust_gap)
    return {
        "status":("K1_DESIGN_HAS_PREDICTED_ROBUST_SEPARATION"
                  if possible else "K1_MENU_CANNOT_ROBUSTLY_DISCRIMINATE"),
        "proposed_measurement":
            selected["measurement"] if possible else None,
        "best_candidate_even_if_nonseparating":selected["measurement"],
        "all_menu_scores":candidates,
        "precommitted_policy":policy,
        "evidence_result_read":False,
        "only_this_single_observable_tested":True,
    }


def k1_revise(k0,preselected,evidence,absolute_residual_max):
    """Revise after one PRESELECTED K1 result; no after-the-fact menu change."""
    policy=preselected.get("precommitted_policy",{})
    need(type(policy) is dict
         and number(policy.get("absolute_residual_max_orders"))
         and number(policy.get("numerical_guard_orders"))
         and policy["absolute_residual_max_orders"]==absolute_residual_max
         and preselected["status"]=="K1_DESIGN_HAS_PREDICTED_ROBUST_SEPARATION"
         and preselected["proposed_measurement"] is not None
         and set(evidence)=={"rate_per_minute","t_min","delivered"}
         and {k:evidence[k] for k in ("rate_per_minute","t_min")}
             ==preselected["proposed_measurement"]
         and number(evidence["delivered"]) and evidence["delivered"]>=0
         and evidence["delivered"] <=
             evidence["rate_per_minute"]*min(evidence["t_min"],20)+1e-8
         and number(absolute_residual_max) and absolute_residual_max>=0,
         "K1_NOT_PRECOMMITTED_OR_EVIDENCE_INVALID")
    i=T_VALUES.index(evidence["t_min"])
    effective_tolerance=(
        policy["absolute_residual_max_orders"]+
        policy["numerical_guard_orders"])
    updated={}
    for f in FAMILIES:
        old=k0[f]["eligible"]
        kept=[]
        for m in old:
            pred=curve(m,evidence["rate_per_minute"])[i]
            if abs(pred-evidence["delivered"])<=effective_tolerance+1e-12:
                kept.append(m)
        updated[f]={"kept":kept,"count_before":len(old),
                    "count_after":len(kept)}
    survivors=[f for f in FAMILIES if updated[f]["kept"]]
    return {
        "status":("STRUCTURAL_REVISION_ONE_FAMILY_REMAINS"
                  if len(survivors)==1
                  else "K1_BOTH_FAMILIES_REMAIN"
                  if len(survivors)==2
                  else "K1_NO_COMPATIBLE_FAMILY"),
        "updated":updated,
        "K1_observation":evidence,
        "used_exact_precommitted_policy":policy,
        "effective_residual_tolerance_orders":effective_tolerance,
        "surviving_families":survivors,
        "revision_type":("EPISTEMIC_RESTRICTION_OF_EXISTING_HYPOTHESES"
                         if len(survivors)<2 else "NO_STRUCTURAL_EXCLUSION"),
        "new_architecture_created":False,
    }


def prepare_k2_comparison(k0,k1,k2_public_rate):
    """Lock K0 and K1 proposals before ANY K2 outcomes. No K2 scoring."""
    need(number(k2_public_rate) and 0<k2_public_rate<=3
         and set(k0)==set(FAMILIES)
         and set(k1["updated"])==set(FAMILIES),"K2_PREP_INVALID")
    def envelope(rows):
        if not rows:return None
        ys=[curve(m,k2_public_rate) for m in rows]
        return {"lower":[min(y[i] for y in ys) for i in range(6)],
                "upper":[max(y[i] for y in ys) for i in range(6)],
                "candidate_count":len(rows)}
    return {
        "status":"ILLUSTRATIVE_PRE_K2_PACKAGE_NO_CUSTODY_NO_EVALUATION",
        "K0_frozen":{f:envelope(k0[f]["eligible"]) for f in FAMILIES},
        "K1_frozen":{f:envelope(k1["updated"][f]["kept"]) for f in FAMILIES},
        "K1_revision_status":k1["status"],
        "K2_public_rate":k2_public_rate,
        "K2_truth_included":False,
        "external_custody_verified":False,
        "K2_DES_runs":0,
        "no_structural_recovery_claim":True,
    }


def main():
    # Deliberately no CLI to consume a real case. Explicit toy checks live
    # in the tests; independent K0/K1/K2 execution is NOT implemented.
    verify_existing_repertoire()
    print("CAF02_EXISTING_C00_C01_REPERTOIRE_VERIFIED")
    print("CAF02_K0_K1_K2_DECISION_MODULE_ONLY_NO_DES_NO_K2_TRUTH")


if __name__=="__main__":
    main()
