"""RF-03E: joint observation vectors + loss-time domain sensitivity.

All 6 D grammars, the 450 previous external parameter trials, and known O0
arrival events are preserved. G3 is exploratory; extrapolations t>10 are
conditional STOP-ARRIVALS scenarios, not data or forecasts.

RF146-01: scalar interval overlap does NOT imply joint trajectory overlap.
RF146-02: with no operational upper bound on lossTime, loss structures approach
no-loss structures on finite windows.
RF146-03: each structure's near-optimal MAE set is NOT a common compatibility set.
"""
from __future__ import annotations

import argparse
import json
import math
from itertools import combinations, product
from pathlib import Path
from fractions import Fraction as F

from scripts.arena_v0_contract import canonical, digest
from scripts.arena_cafe.native_handoff import need
from scripts.arena_cafe import g3_construction as g3
from scripts.arena_cafe import g3_observability as rf03d
from scripts.arena_cafe import r2_causal_pos_signal as signal

SCHEMA="igc-arena-g3-joint-measurements-loss-domain/0.1"
DELIVERY_TIMES=(3,5,7,9,12,15,20)
WIP_TIMES=(10,12,15,20)
LOSS_TIMES=(10,12,15,20)
# Intentionally illustrations, not an assertion about POS accuracy.
HYPOTHETICAL_SENSOR_ERRORS=(0.,0.25,0.5,1.)
ILLUSTRATIVE_NUMERICAL_MARGIN=0.15
COMMON_ABSOLUTE_MAX_ERRORS=(0.25,0.5,1.,2.)
LOSS_DOMAIN_SENSITIVITY_MINUTES=(20.,40.,80.,160.,320.,640.,1280.)
# Neither L>20 nor any sensor threshold is part of the original G3 fit.
MEASUREMENT_PLANS={
    "deliveries_3_5":tuple(("delivered_cumulative",t) for t in (3,5)),
    "deliveries_3_5_7_9":tuple(("delivered_cumulative",t)
                             for t in (3,5,7,9)),
    "deliveries_through_15":tuple(("delivered_cumulative",t)
                                  for t in DELIVERY_TIMES if t<=15),
    "deliveries_through_20":tuple(("delivered_cumulative",t)
                                  for t in DELIVERY_TIMES),
    "total_wip_10_12_15_20":tuple(("total_wip",t) for t in WIP_TIMES),
    "loss_10_12_15_20":tuple(("lost_cumulative",t) for t in LOSS_TIMES),
    "deliveries_plus_wip":(
        *(("delivered_cumulative",t) for t in DELIVERY_TIMES),
        *(("total_wip",t) for t in WIP_TIMES),
    ),
}


def _validate_vectors(a,b):
    need(bool(a) and bool(b) and
         all(len(v)==len(a[0]) and len(v)>0 for v in a) and
         all(len(v)==len(a[0]) for v in b) and
         all(all(type(x) in (int,float) and math.isfinite(x)
                 for x in v) for v in list(a)+list(b)),
         "RF03E_BAD_JOINT_VECTORS")
    return len(a[0])


def minimax_joint_distance(a,b):
    """Smallest Linf distance over PAIRS OF WHOLE parameter trajectories.

    Single parameters determine all measured times; no Cartesian mixing of
    independent marginal intervals is permitted.
    """
    _validate_vectors(a,b)
    best=math.inf
    witness=None
    for i,x in enumerate(a):
        for j,y in enumerate(b):
            gap=max(abs(x[k]-y[k]) for k in range(len(x)))
            if gap<best:
                best=gap
                witness=(i,j)
    need(math.isfinite(best) and witness is not None,
         "RF03E_NO_JOINT_CANDIDATES")
    return best,witness


def _vector(trial,plan):
    return tuple(trial["trajectory"][t][name] for name,t in plan)


def _common_absolute_screen(families, ensembles, observed):
    """Sensitivity to absolute common O0 max-error, not a sensor guarantee."""
    records=[]
    for tolerance in COMMON_ABSOLUTE_MAX_ERRORS:
        entries=[]
        for fam in families:
            trials=ensembles[fam["native_structure_sha256"]]["all"]
            count=0
            for t in trials:
                residuals=[abs(t["trajectory"][minute]["delivered_cumulative"]-v)
                           for minute,v in zip(g3.SAMPLES,observed)]
                if max(residuals)<=tolerance:
                    count+=1
            entries.append({"candidate_id":fam["candidate_id"],
                            "n":fam["n"],"loss":fam["loss"],
                            "passing_grid_points":count,
                            "evaluated_grid_points":len(trials)})
        records.append({
            "hypothetical_common_absolute_max_error_orders":tolerance,
            "criterion":"max_over_O0_t2_4_6_8_10_abs(predicted_minus_observed)",
            "families_with_one_or_more_grid_points":sum(
                e["passing_grid_points"]>0 for e in entries),
            "by_family":entries,
        })
    return {"measure":"delivered_cumulative",
            "comparability":"CONDITIONAL_ON_HYPOTHETICAL_ABSOLUTE_ERROR",
            "measurement_error_estimated":False,
            "relative_near_best_is_not_this_absolute_test":True,
            "results":records}


def _joint_panels(families,ensembles):
    comps=[]
    summaries={name:{
        "plan":name,
        "coordinates":[{"measure":m,"time_minutes":t} for m,t in coords],
        "pairs":15,"positive_grid_distance_pairs":0,
        "pairs_exceeding_illustrative_2epsilon_plus_numeric_margin":
            {str(eps):0 for eps in HYPOTHETICAL_SENSOR_ERRORS},
        "min_joint_distance_orders":math.inf,
        "max_joint_distance_orders":0.,
    } for name,coords in MEASUREMENT_PLANS.items()}
    for fa,fb in combinations(families,2):
        ia=ensembles[fa["native_structure_sha256"]]["near"]
        ib=ensembles[fb["native_structure_sha256"]]["near"]
        need(len(ia)==fa["near_best_grid_count"] and
             len(ib)==fb["near_best_grid_count"],
             "RF03E_RELATIVE_NEAR_GRID_DRIFT")
        per={}
        for name,coords in MEASUREMENT_PLANS.items():
            vectors_a=[_vector(t,coords) for t in ia]
            vectors_b=[_vector(t,coords) for t in ib]
            distance,(i,j)=minimax_joint_distance(vectors_a,vectors_b)
            info=summaries[name]
            info["min_joint_distance_orders"]=min(
                info["min_joint_distance_orders"],distance)
            info["max_joint_distance_orders"]=max(
                info["max_joint_distance_orders"],distance)
            if distance>1e-5:
                info["positive_grid_distance_pairs"]+=1
            status={}
            for eps in HYPOTHETICAL_SENSOR_ERRORS:
                # Even a positive GRID distance is not proof of separation
                # across a continuous unbounded parameter domain.
                separated=(distance >
                           2*eps+ILLUSTRATIVE_NUMERICAL_MARGIN)
                if separated:
                    info["pairs_exceeding_illustrative_2epsilon_plus_numeric_margin"][
                        str(eps)]+=1
                status[str(eps)]=(
                    "FINITE_GRID_GAP_EXCEEDS_ILLUSTRATIVE_MARGIN"
                    if separated else "INCONCLUSIVE_ON_THIS_FINITE_GRID")
            # Corresponding scalar interval gap may be zero even though
            # joint vectors are distinct. This is RF146-01's core.
            scalar_gaps=[]
            for measure,t in coords:
                index=coords.index((measure,t))
                l=[v[index] for v in vectors_a]
                r=[v[index] for v in vectors_b]
                scalar_gaps.append(max(0.,min(l)-max(r),min(r)-max(l)))
            need(distance+1e-7>=max(scalar_gaps),
                 "RF03E_JOINT_GAP_SMALLER_THAN_MARGINAL_GAP")
            per[name]={
                "minimum_Linf_joint_distance_orders":round(distance,7),
                "maximum_scalar_interval_gap_over_plan":round(max(scalar_gaps),7),
                "joint_exceeds_max_scalar_gap_by_orders":
                    round(distance-max(scalar_gaps),7),
                "one_witness_parameter_pair":{
                    "a":ia[i]["parameters"],"b":ib[j]["parameters"]},
                "hypothetical_margin_sensitivity":status,
                "does_not_certify_real_world_discrimination":True,
            }
        comps.append({
            "a_id":fa["candidate_id"],"b_id":fb["candidate_id"],
            "a_n":fa["n"],"a_loss":fa["loss"],
            "b_n":fb["n"],"b_loss":fb["loss"],
            "joint_plans":per,
        })
    need(len(comps)==15 and
         all(x["positive_grid_distance_pairs"]<=15 for x in summaries.values()),
         "RF03E_WRONG_PAIR_COUNT")
    for v in summaries.values():
        v["min_joint_distance_orders"]=round(v["min_joint_distance_orders"],7)
        v["max_joint_distance_orders"]=round(v["max_joint_distance_orders"],7)
        v["finite_grid_not_continuous_parameter_set"]=True
        v["error_thresholds_are_hypothetical"]=True
    return comps,list(summaries.values())


def _loss_domain_sensitivity(source, ensembles, families):
    """Controlled same-(capacity,tau) comparisons as lossTime increases.

    This is NOT recalibration of the previous experiment. Baseline retains
    lossTime <=20; extended values are separately labeled stress scenarios.
    """
    segments=source["signal"]["segments"]
    times=[F(x) for x in source["signal"]["event_times_minutes_exact"]]
    width=F(source["signal"]["width_minutes_exact"])
    total_n=source["signal"]["events_count"]
    horizon=rf03d.T_GRID[-1]
    need(horizon==20 and total_n==15,
         "RF03E_UNEXPECTED_INPUT_OR_HORIZON")
    record=[]
    for n in (1,2,3):
        for L in LOSS_DOMAIN_SENSITIVITY_MINUTES:
            delivery_diffs=[]
            wip_diffs=[]
            losses=[]
            for cap,tau in product(g3.CAPACITIES,g3.RESPONSE_TIMES):
                baseline=rf03d.integrate_conditional_horizon(
                    segments,times,width,n,False,cap,tau,
                    g3.NO_LOSS_PLACEHOLDER)
                lossy=rf03d.integrate_conditional_horizon(
                    segments,times,width,n,True,cap,tau,L)
                delivery_diffs.append(max(
                    abs(baseline[t]["delivered_cumulative"]-
                        lossy[t]["delivered_cumulative"])
                    for t in DELIVERY_TIMES))
                wip_diffs.append(max(
                    abs(baseline[t]["total_wip"]-lossy[t]["total_wip"])
                    for t in WIP_TIMES))
                losses.append(lossy[20]["lost_cumulative"])
            bound=total_n*horizon/L
            need(max(losses)<=bound+rf03d.CONSERVATION_TOL and
                 min(losses)>=-1e-5,
                 "RF03E_LOSS_EXCEEDS_CONSERVATIVE_ANALYTIC_BOUND")
            record.append({
                "n":n,
                "loss_time_minutes":L,
                "domain":"ORIGINAL_GRID_BOUNDARY" if L==20. else
                         "EXTENDED_STRESS_NOT_ORIGINAL_GRID",
                "same_cap_response_pairs":len(delivery_diffs),
                "max_joint_delivery_difference_across_same_param_pairs":
                    round(max(delivery_diffs),7),
                "min_joint_delivery_difference_across_same_param_pairs":
                    round(min(delivery_diffs),7),
                "max_joint_wip_difference_across_same_param_pairs":
                    round(max(wip_diffs),7),
                "max_lost_by_20_minutes":round(max(losses),7),
                "conservative_analytic_loss_upper_bound_orders":
                    round(bound,7),
                "same_capacity_and_response_time_not_refitted":True,
            })
    need(len(record)==3*len(LOSS_DOMAIN_SENSITIVITY_MINUTES),
         "RF03E_DOMAIN_SWEEP_INCOMPLETE")
    return {
        "native_D_loss_equation":"lossRate=max(0,s1/lossTime)",
        "model_parameter_limit": "NO_OPERATIONAL_UPPER_BOUND_ESTABLISHED",
        "original_loss_domain_minutes":list(g3.LOSS_TIMES),
        "extended_loss_time_minutes":
            [x for x in LOSS_DOMAIN_SENSITIVITY_MINUTES if x>20],
        "bound_formula":"lost(T) <= N*T/lossTime, N=15,T=20 minutes",
        "meaning":"arbitrarily_weak_loss_as_lossTime_grows",
        "not_an_absolute_fitting_or_sensor_inference":True,
        "results":record,
        "no_loss_variants_preserved":True,
    }


def build(visible,previous_g3):
    need(previous_g3.get("schema")==g3.SCHEMA and
         previous_g3.get("source_snapshot_hash")==
              visible.get("source_snapshot_hash") and
         previous_g3.get("D",{}).get("mode")==
              "ARENA_EXTERNAL_CALIBRATION_EXPLORATORY_NUMERICAL_MIRROR" and
         previous_g3.get("gates",{}).get("A3")=="PARTIAL" and
         previous_g3.get("gates",{}).get("G4")==
              previous_g3.get("gates",{}).get("G5")=="NOT_RUN",
         "RF03E_INVALID_FROZEN_G3_REFERENCE")
    families,source,ensembles=rf03d._fit_models(
        visible,previous_g3["D"],return_ensembles=True)
    need(len(families)==len(ensembles)==6 and
         sum(len(v["all"]) for v in ensembles.values())==450,
         "RF03E_NOT_ORIGINAL_450_GRID")
    comparisons,summaries=_joint_panels(families,ensembles)
    loss_sensitivity=_loss_domain_sensitivity(source,ensembles,families)
    common_abs=_common_absolute_screen(
        families,ensembles,g3.public_observations(visible))
    return {
        "schema":SCHEMA,
        "source_snapshot_hash":visible["source_snapshot_hash"],
        "previous_RF03C_g3_hash":digest(previous_g3),
        "method_source":"ORIGINAL_D_EQUATIONS_EXTERNAL_RK4_MIRROR",
        "prior_RF03D_scalar_result":"VALID_SCALAR_ONLY_NOT_JOINT",
        "method":"KNOWN_O0_CONSTRUCTION_EXPLORATORY_JOINT_VECTORS",
        "joint_distance":"min_over_whole_parameter_trajectory_pairs_max_over_coordinates_abs_difference",
        "subset_policy":"RF03C_RELATIVE_NEAR_BEST_MAE_PLUS_0_25_FOR_JOINT_COMPARISON_ONLY",
        "joint_pairwise":comparisons,
        "joint_plan_summaries":summaries,
        "hypothetical_sensor_absolute_error_orders":
            list(HYPOTHETICAL_SENSOR_ERRORS),
        "illustrative_numerical_margin_orders":
            ILLUSTRATIVE_NUMERICAL_MARGIN,
        "numerical_margin_is_NOT_a_certified_error_bound":True,
        "margin_rule":"distance > 2*sensor_error + illustrative_numerical_margin",
        "common_absolute_compatibility_sensitivity":common_abs,
        "loss_domain_sensitivity":loss_sensitivity,
        "future_times_are_stop-arrival_scenarios_not_observations":True,
        "loss_equals_cancelled_orders_not_proven":True,
        "no_operational_sensor_error_calibration":True,
        "no_parameter_identifiability_or_structural_recovery_claim":True,
        "no_model_selection_or_method_ranking":True,
        "no_DES_OMC_or_provider_calls":True,
        "A3":"PARTIAL","G3":"EXPLORATORY_CONSTRUCTION_ONLY",
        "G4":"NOT_RUN","G5":"NOT_RUN",
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--visible",required=True,type=Path)
    parser.add_argument("--previous-g3",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    need(not args.out.exists(),"RF03E_REFUSE_OVERWRITE")
    visible=json.loads(args.visible.read_text(encoding="utf-8"))
    previous=json.loads(args.previous_g3.read_text(encoding="utf-8"))
    report=build(visible,previous)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_bytes(canonical(report)+b"\n")
    print(json.dumps({
        "pairs":len(report["joint_pairwise"]),
        "plans":len(report["joint_plan_summaries"]),
        "loss_domain_cases":len(report["loss_domain_sensitivity"]["results"]),
        "A3":report["A3"],"G4":report["G4"],"G5":report["G5"],
    },sort_keys=True))


if __name__=="__main__":
    main()
