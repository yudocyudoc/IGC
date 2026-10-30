#!/usr/bin/env python3
"""CAF02 D adapter: finite-grid calibration -> shared-pulse K1 revision -> K2 sets.

REUSES D's original 1..3 stock no-loss grammar and RK4 from
scripts.arena_d_v1_screen.integrate, including its exact pulse boundary.
A separate CAF02 adapter is needed because original D2 mandates exactly the
same pulse as K0. D receives the one K1 selected by M; its preference is
diagnostic only, never affects which trial the world executes.

This is an offline model pipeline, not the DES, ATMS persisted ledger,
native OpenModelica G2 certification or an independent prospective result.
CAF01 is untouched. No read of holdout/G5 secrets/provider/model truth.
"""
from __future__ import annotations
from functools import lru_cache
from pathlib import Path
import hashlib
import json
import math
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from scripts.arena_d_v1_screen import integrate
from scripts.arena_d_v01 import topology
from scripts.arena_v0_contract import digest
import caf02_structural_k0k1k2 as m

POLICY=Path(__file__).with_name(
    "CAF02_INDEPENDENT_K0K1K2_POLICY_PROPOSAL_2026-10-30.json")
TIMES=(5,10,15,20,30,40)


class DBlocked(ValueError):
    pass


def check(ok,reason):
    if not ok:raise DBlocked(reason)


def finite(v):
    return type(v) in (float,int) and math.isfinite(v)


def parse_policy(policy):
    check(type(policy) is dict
          and policy.get("status")=="DRAFT_FOR_REVIEW_NOT_FROZEN_NOT_AUTHORIZED"
          and policy.get("no_world_runs_authorized") is True
          and policy.get("scope",{}).get("primary") ==
              "M_AND_D_PARALLEL_K0_K1_K2_EXISTING_GRAMMARS",
          "D_NOT_A_VALID_AUTHORIZED_SCIENTIFIC_POLICY")
    d=policy.get("d_method")
    check(type(d) is dict
          and d["source_integrator"]=="scripts/arena_d_v1_screen.py:integrate"
          and d["available_structures"]==["D1","D2","D3"]
          and d["loss"] is False
          and d["post_K1_rule"] ==
              "FILTER_ONLY_K0_COMPATIBLE_CANDIDATES_USING_EXACT_K1_SELECTED_PULSE_AND_RESIDUAL_WITHOUT_REFITTING_GRID"
          and d["use_common_preselected_M_K1_option"] is True
          and d["native_parity_status"]=="NOT_VERIFIED_FOR_NEW_GRID",
          "D_GRAMMAR_OR_POLICY_CHANGED")
    cap=d["capacity_items_per_hour"]
    tau=d["shared_response_time_minutes"]
    check(type(cap) is list and type(tau) is list and
          cap==[48,72,100] and tau==[1,1.5,2,3,6,10]
          and d["max_candidates_K0"]==3*len(cap)*len(tau)==54
          and d["budget"]["K0_integrations_max"]==54,
          "D_GRID_BUDGET_MISMATCH")
    check(d["K0_absolute_mae_orders"]==
          policy["k0"]["model_adequacy_absolute_MAE_orders"]
          and d["K0_relative_to_family_best_mae_orders"]==
          policy["k0"]["model_adequacy_relative_to_family_best_MAE_orders"]
          and d["K1_effective_tolerance_orders"]==
          policy["k1"]["effective_revision_tolerance_orders"],
          "D_M_UNEQUAL_SCIENTIFIC_ADMISSIBILITY_POLICY")
    check(policy["k0"]["delivered_observation_times_minutes"]==[5,10]
          and policy["k2"]["delivered_scored_times_minutes"]==list(TIMES)
          and policy["boundary"]["no_loss"] is True
          and policy["boundary"]["reset_each_cut"] is True
          and d["numeric_solver_step_hours"]==1/1200,
          "D_UNEXPECTED_OBSERVATIONS_OR_BOUNDARY")
    check([o["rate_per_minute"] for o in policy["k1"]["menu"]]==[1,1.5,1.8]
          and [o["t_min"] for o in policy["k1"]["menu"]]==[10,20,30],
          "D_K1_MENU_CHANGED")
    return d


def candidate_id(stocks,capacity,tau_min):
    return f"D{stocks}_C{capacity}_T{format(tau_min,'g')}"


@lru_cache(maxsize=2000)
def predicted(stocks, capacity_per_hour, response_time_minutes,
              pulse_rate_per_min, sample_minutes):
    """Literal D RK4, unit conversion minutes -> hours and orders/min -> h."""
    check(stocks in (1,2,3) and type(stocks) is int
          and all(finite(v) and v>0 for v in
                  (capacity_per_hour,response_time_minutes,pulse_rate_per_min))
          and type(sample_minutes) is tuple
          and len(sample_minutes)>0
          and all(finite(t) and 0<t<=40 for t in sample_minutes)
          and all(a<b for a,b in zip(sample_minutes,sample_minutes[1:])),
          "D_RK4_BAD_PULSE_OR_PARAMETERS")
    params={"capacity":capacity_per_hour,
            "response_time":response_time_minutes/60,
            "loss_time":1.0}
    pulse={"rate":pulse_rate_per_min*60,"duration":20/60}
    times=[t/60 for t in sample_minutes]
    values=integrate(stocks,False,params,pulse,times,1/1200)
    check(len(values)==len(times) and
          all(-1e-8<=y<=pulse_rate_per_min*min(t,20)+1e-7
              for y,t in zip(values,sample_minutes)) and
          all(x<=y+1e-8 for x,y in zip(values,values[1:])),
          "D_PREDICTION_BREAKS_PUBLIC_MATERIAL_CONSERVATION")
    return tuple(max(0.,x) for x in values)


def parse_observed_k0(obs,policy):
    check(type(obs) is list and len(obs)==2
          and all(type(row) is dict and set(row)=={"t_min","delivered"}
                  for row in obs)
          and [row["t_min"] for row in obs]==[5,10],
          "D_K0_MUST_BE_TWO_PUBLIC_TIMES")
    values=[row["delivered"] for row in obs]
    rate=policy["k0"]["public_arrival_pulse"]["rate_per_minute"]
    check(all(finite(y) and y>=0 for y in values)
          and values[0]<=values[1]
          and all(v<=rate*t+1e-8 for v,t in zip(values,(5,10))),
          "D_K0_PHYSICALLY_IMPOSSIBLE_OBSERVATION")
    return values


def calibrate_k0(observed,policy):
    d=parse_policy(policy)
    ys=parse_observed_k0(observed,policy)
    rate=policy["k0"]["public_arrival_pulse"]["rate_per_minute"]
    results={f"D{n}":[] for n in range(1,4)}
    for stocks in range(1,4):
        for cap in d["capacity_items_per_hour"]:
            for tau in d["shared_response_time_minutes"]:
                y=predicted(stocks,cap,tau,rate,(5,10))
                mae=sum(abs(a-b) for a,b in zip(y,ys))/2
                results[f"D{stocks}"].append({
                    "id":candidate_id(stocks,cap,tau),
                    "stocks":stocks,"loss":False,
                    "capacity_per_hour":cap,
                    "shared_response_time_minutes":tau,
                    "structure_hash":digest(topology(stocks,False)),
                    "K0_predicted_delivered":list(y),
                    "K0_mae_orders":mae,
                })
    survivors={}
    counts={}
    for fam,rows in results.items():
        best=min(x["K0_mae_orders"] for x in rows)
        cutoff=min(d["K0_absolute_mae_orders"],
                   best+d["K0_relative_to_family_best_mae_orders"])
        survivors[fam]=[r for r in rows
                        if r["K0_mae_orders"]<=cutoff+1e-12]
        counts[fam]={"evaluated":len(rows),"surviving":len(survivors[fam]),
                     "best_K0_MAE":best,"absolute_ceiling":d["K0_absolute_mae_orders"]}
    check(sum(x["evaluated"] for x in counts.values())==54,
          "D_EVALUATION_BUDGET_OVERRUN")
    return {
        "schema":"igc-caf02-D-K0-compatible-sets/0.1",
        "status":"OFFLINE_D_RK4_GRID_ONLY_NOT_NATIVE_G2",
        "method":"LEGACY_D_GRAMMAR_SHARED_RESPONSE_TIME_NO_LOSS",
        "input_K0":observed,
        "policy_sha256":digest(policy),
        "family_counts":counts,
        "compatible":survivors,
        "candidate_evaluations":54,
        "parameter_identifiable":False,
        "individual_candidate_selection_forced":False,
        "native_G2_verified":False,
        "K2_truth_seen":False,
    }


def all_survivors(k0):
    return [row for fam in ("D1","D2","D3") for row in k0["compatible"][fam]]


def family_envelope(rows,rate,times=TIMES):
    if not rows:return None
    predictions=[predicted(r["stocks"],r["capacity_per_hour"],
                           r["shared_response_time_minutes"],rate,tuple(times))
                 for r in rows]
    return {
        "lower":[min(y[i] for y in predictions) for i in range(len(times))],
        "upper":[max(y[i] for y in predictions) for i in range(len(times))],
        "member_ids":[r["id"] for r in rows],
        "candidate_count":len(rows),
    }


def diagnostic_k1_preference(k0,policy):
    """D's advisory ranking, NOT the executed trial and not a selector veto."""
    d=parse_policy(policy)
    options=policy["k1"]["menu"]
    scores=[]
    for o in options:
        envelopes={fam:family_envelope(
            k0["compatible"][fam],o["rate_per_minute"],(o["t_min"],))
            for fam in ("D1","D2","D3")}
        vals=[(v["lower"][0],v["upper"][0])
              for v in envelopes.values() if v is not None]
        diameter=max((b for a,b in vals),default=0)-min(
            (a for a,b in vals),default=0)
        scores.append({"rate_per_minute":o["rate_per_minute"],
                       "t_min":o["t_min"],
                       "overall_uncertainty_span_orders":diameter,
                       "family_envelopes":envelopes})
    best=max(enumerate(scores),key=lambda q:
             (q[1]["overall_uncertainty_span_orders"],-q[0]))[1]
    return {
        "status":"D_ADVISORY_ONLY_UNCERTAINTY_SPAN_NOT_ROBUST_STRUCTURE_DISCRIMINATION",
        "suggested_measurement":{"rate_per_minute":best["rate_per_minute"],
                                 "t_min":best["t_min"]},
        "options":scores,
        "does_not_override_M_common_selection":True,
    }


def validate_common_decision(decision,policy):
    check(type(decision) is dict
          and decision.get("status") in (
              "K1_DESIGN_HAS_PREDICTED_ROBUST_SEPARATION",
              "K1_MENU_CANNOT_ROBUSTLY_DISCRIMINATE",
              "K0_NO_TWO_ADEQUATE_STRUCTURES"
          )
          and "proposed_measurement" in decision
          and type(decision.get("precommitted_policy")) is dict,
          "D_COMMON_K1_DECISION_MISSING_OR_WRONG")
    p=decision["precommitted_policy"]
    check(p.get("absolute_residual_max_orders")==
              policy["k1"]["absolute_residual_tolerance_orders"]
          and p.get("numerical_guard_orders")==
              policy["k1"]["numerical_allowance_orders"]
          and p.get("minimum_expanded_nonoverlap_gap_orders")==
              policy["k1"]["minimum_positive_expanded_gap_orders"]
          and p.get("effective_revision_tolerance_orders")==
              policy["k1"]["effective_revision_tolerance_orders"],
          "D_K1_SELECTION_AND_REVISION_TOLERANCE_DRIFT")
    choice=decision["proposed_measurement"]
    if decision["status"]!="K1_DESIGN_HAS_PREDICTED_ROBUST_SEPARATION":
        check(choice is None,"D_NONDISCRIMINATING_M_HAS_NO_K1")
        return None
    check(type(choice) is dict and set(choice)=={"rate_per_minute","t_min"}
          and any((x["rate_per_minute"],x["t_min"])==
                  (choice["rate_per_minute"],choice["t_min"])
                  for x in policy["k1"]["menu"]),
          "D_NOT_COMMON_PREDECLARED_K1_MENU_OPTION")
    return choice


def revise_k1(k0,common_selection,evidence,policy):
    d=parse_policy(policy)
    check(k0["policy_sha256"]==digest(policy),"D_K0_K1_POLICY_CHANGED")
    choice=validate_common_decision(common_selection,policy)
    # A no-K1 decision is not a permission to ask D's own question.
    if choice is None:
        check(evidence is None,"D_K1_EVIDENCE_INJECTED_WITHOUT_SELECTION")
        return {
            "status":"K1_NOT_EXECUTED_COMMON_DESIGN_INCONCLUSIVE",
            "compatible":k0["compatible"],
            "family_counts_after":{f:len(v) for f,v in k0["compatible"].items()},
            "K1_evidence_used":False,"revision_kind":"NONE",
            "source_preselected_measurement":None,
            "K2_truth_seen":False,
        }
    check(type(evidence) is dict
          and set(evidence)=={"rate_per_minute","t_min","delivered"}
          and (evidence["rate_per_minute"],evidence["t_min"])==
              (choice["rate_per_minute"],choice["t_min"])
          and finite(evidence["delivered"]) and evidence["delivered"]>=0
          and evidence["delivered"] <=
              choice["rate_per_minute"]*min(choice["t_min"],20)+1e-8,
          "D_K1_NEW_PULSE_NOT_PRESELECTED_OR_PHYSICALLY_IMPOSSIBLE")
    out={}
    for fam,rows in k0["compatible"].items():
        out[fam]=[]
        for row in rows:
            predicted_y=predicted(row["stocks"],row["capacity_per_hour"],
                                  row["shared_response_time_minutes"],
                                  choice["rate_per_minute"],(choice["t_min"],))[0]
            if (abs(predicted_y-evidence["delivered"]) <=
                    d["K1_effective_tolerance_orders"]+1e-12):
                out[fam].append(row)
    remaining=sum(bool(v) for v in out.values())
    return {
        "status":("K1_NO_COMPATIBLE_D_FAMILY" if remaining==0
                  else "K1_ONE_D_FAMILY_REMAINS" if remaining==1
                  else "K1_MULTIPLE_D_FAMILIES_REMAIN"),
        "compatible":out,
        "family_counts_after":{f:len(v) for f,v in out.items()},
        "K1_evidence_used":True,
        "K1_evidence":evidence,
        "revision_kind":"K0_HYPOTHESIS_SUPPORT_RESTRICTED_NOT_TOPOLOGY_GENERATION",
        "source_preselected_measurement":choice,
        "ATMS_persisted":False,
        "ATMS_logical_support_proposed":[
            "DCOMPATIBLE:"+r["id"] for v in out.values() for r in v],
        "K2_truth_seen":False,
    }


def prepare_k2(k0,k1,policy):
    d=parse_policy(policy)
    check(k0["policy_sha256"]==digest(policy)
          and set(k1["compatible"])=={"D1","D2","D3"},
          "D_K2_WRONG_PARENT_OR_POLICY")
    rate=policy["k2"]["future_public_pulse"]["rate_per_minute"]
    prior={f:family_envelope(rows,rate)
           for f,rows in k0["compatible"].items()}
    revised={f:family_envelope(rows,rate)
             for f,rows in k1["compatible"].items()}
    def overall(xs):
        active=[v for v in xs.values() if v is not None]
        if not active:return None
        return {
            "lower":[min(v["lower"][i] for v in active) for i in range(6)],
            "upper":[max(v["upper"][i] for v in active) for i in range(6)],
            "candidate_count":sum(v["candidate_count"] for v in active),
        }
    a,b=overall(prior),overall(revised)
    check(k1["K1_evidence_used"] or a==b,
          "D_NO_K1_MUST_NOT_CHANGE_FORECAST")
    return {
        "status":"D_K0_K1_FORECAST_SETS_READY_FOR_EXTERNAL_SEAL_NOT_SEALED",
        "K0_families":prior,"K1_families":revised,
        "K0_union":a,"K1_union":b,
        "K0_point_eligibility_max_width_orders":
            policy["k2"]["point_eligibility_max_width_orders"],
        "K1_revision_kind":k1["revision_kind"],
        "K2_truth_included":False,
        "G4_external_witness_verified":False,
        "D_native_G2_verified":False,
        "world_DES_runs":0,
        "provider_calls":0,
    }
