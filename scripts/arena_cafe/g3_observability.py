"""RF-03D: diagnostic observability of six native D structures.

Reuses only the PUBLIC O0 construction observations and the external, disclosed
G3 parameter grid. Every prediction beyond 10min is a CONDITIONAL SCENARIO:
exactly the 15 known arrivals, right-sided half-minute kernel including its
deferred tail, and NO NEW ARRIVALS afterwards. No prospective evidence, no
actual delivery outcomes after 10, and no recovery claim.

The purpose is to find observational distinctions between *sets* of models
that already approximate O0, not to select a better-fitting winner.
"""
from __future__ import annotations

import argparse
from fractions import Fraction as F
from itertools import combinations, product
import json
import math
from pathlib import Path

from scripts.arena_v0_contract import canonical, digest
from scripts.arena_cafe.native_handoff import need
from scripts.arena_cafe import g3_construction as g3
from scripts.arena_cafe import r2_causal_pos_signal as signal
from scripts.arena_cafe import r2_observational_contracts as r2

SCHEMA = "igc-arena-g3-d-observability-diagnostic/0.1"
T_GRID = tuple(range(0, 21))  # internal diagnostic, minutes
CONSTRUCTION_TIMES = g3.SAMPLES
PROPOSED_DELIVERY_TIMES = (3, 5, 7, 9, 12, 15, 20)
PROPOSED_STOCK_TIMES = (10, 12, 15, 20)
MEASURES = ("delivered_cumulative", "total_wip", "lost_cumulative")
CONSERVATION_TOL = 0.02
COMPARE_BEST_MAE_TOL = 0.0001


def integrate_conditional_horizon(segments, event_times, width,
                                  n, has_loss, capacity, response_time,
                                  loss_time, *, times=T_GRID, dt=g3.DT):
    """Integrate D's native equations via the validated EXTERNAL RK4 mirror.

    Preserve the rate in the original event kernel's post-cutoff tail, then
    impose zero new orders. Neither DES nor OpenModelica is invoked.
    """
    need(tuple(times) == tuple(sorted(set(times))) and
         times[0] == 0 and times[-1] == 20 and
         set(CONSTRUCTION_TIMES).issubset(times),
         "G3D_INVALID_DIAGNOSTIC_TIME_GRID")
    need(n in (1, 2, 3) and type(has_loss) is bool and
         all(type(x) in (int, float) and math.isfinite(x) and x > 0
             for x in (capacity, response_time, loss_time, dt)),
         "G3D_INVALID_NATIVE_STRUCTURE_OR_PARAMETERS")
    anchors = {F(t) for t in times}
    anchors.update([F(0), F(20)])
    for seg in segments:
        for k in ("start_minutes_exact", "end_minutes_exact"):
            x = F(seg[k])
            if F(0) <= x <= F(20):
                anchors.add(x)
    points = sorted(anchors)
    stock = [0.] * (n + 2)
    readings = {0: _snapshot(stock, 0., n)}
    max_mass_residual = 0.
    for a, b in zip(points, points[1:]):
        matching = [s for s in segments
                    if F(s["start_minutes_exact"]) <= a <
                    F(s["end_minutes_exact"])]
        need(len(matching) <= 1, "G3D_SIGNAL_INTERVAL_OVERLAP")
        rate = float(F(matching[0]["rate_orders_per_minute_exact"])) if matching else 0.
        steps = math.ceil(float(b - a) / dt)
        step = float(b - a) / steps
        for _ in range(steps):
            stock = g3._rk4(stock, step, rate, capacity,
                            response_time, loss_time, has_loss)
        if b.denominator == 1 and int(b) in times:
            time = int(b)
            consumed = float(signal.event_mass_until(
                event_times, width, b))
            snap = _snapshot(stock, consumed, n)
            max_mass_residual = max(max_mass_residual, abs(
                snap["input_mass"] - snap["delivered_cumulative"] -
                snap["total_wip"] - snap["lost_cumulative"]))
            readings[time] = snap
    need(set(readings) == set(times),
         "G3D_MISSING_CONDITIONAL_SAMPLES")
    need(max_mass_residual <= CONSERVATION_TOL and
         all(min(r["delivered_cumulative"],r["total_wip"],
                 r["lost_cumulative"]) >= -1e-5
             for r in readings.values()),
         "G3D_MASS_BALANCE_OR_NEGATIVE_MATERIAL")
    need(all(readings[b]["delivered_cumulative"] + 1e-6 >=
                 readings[a]["delivered_cumulative"]
             for a,b in zip(times,times[1:])),
         "G3D_NONMONOTONE_DELIVERIES")
    return readings


def _snapshot(stock, input_mass, n):
    return {
        "delivered_cumulative": stock[n],
        "total_wip": sum(stock[:n]),
        "lost_cumulative": stock[n+1],
        "input_mass": input_mass,
    }


def _envelope(rows, measure, time):
    vals = [r["trajectory"][time][measure] for r in rows]
    return {"min": round(min(vals),6), "max": round(max(vals),6)}


def _gap(left, right):
    # Separation of two closed prediction intervals; 0 if they overlap.
    return round(max(0., left["min"] - right["max"],
                     right["min"] - left["max"]), 6)


def _fit_models(visible, expected):
    """Enumerate full disclosed G3 search space and check previous G3 results."""
    y=g3.public_observations(visible)
    r2.original_source_checks()
    original=r2.d_pos_contract(visible,"O0",resources={
        "max_stocks":3, "allow_loss":True, "max_candidates":6,
        "max_simulations":0,
    })
    need(original["candidate_count"]==6,
         "G3D_ORIGINAL_NATIVE_D_UNIVERSE_CHANGED")
    s=signal.from_visible(visible,"O0")
    segments=s["signal"]["segments"]
    times=[F(x) for x in s["signal"]["event_times_minutes_exact"]]
    width=F(s["signal"]["width_minutes_exact"])
    outputs=[]
    best_from_previous={
        x["native_structure_sha256"]:x for x in expected["candidates"]
    }
    need(len(best_from_previous)==6 and
         expected["sample_times_minutes"]==list(CONSTRUCTION_TIMES) and
         expected["observed_deliveries"]==y and
         expected["width_minutes_exact"]==str(width) and
         expected["near_best_mae_delta_orders"]==g3.NEAR_BEST_MAE_DELTA,
         "G3D_FROZEN_G3_CONSTRUCTION_REPORT_MISMATCH")
    cap,resp,loss=(expected["grid"][name] for name in
                   ("capacity","response_time","loss_time"))
    need(cap==list(g3.CAPACITIES) and
         resp==list(g3.RESPONSE_TIMES) and loss==list(g3.LOSS_TIMES),
         "G3D_CHANGED_G3_PARAMETER_GRID")
    for structure in original["candidates"]:
        n=len(structure["structure"]["stocks"])
        has_loss=structure["structure"]["loss"]
        candidates=[]
        for capacity,response_time,loss_time in product(
                cap,resp,loss if has_loss else
                (g3.NO_LOSS_PLACEHOLDER,)):
            trajectory=integrate_conditional_horizon(
                segments,times,width,n,has_loss,
                capacity,response_time,loss_time)
            mae=sum(abs(trajectory[t]["delivered_cumulative"]-v)
                    for t,v in zip(CONSTRUCTION_TIMES,y))/len(y)
            candidates.append({
                "mae":mae,
                "parameters":{
                    "capacity":capacity,"response_time":response_time,
                    "loss_time":(loss_time if has_loss else
                                 "INACTIVE_NO_LOSS_TOPOLOGY"),
                },
                "trajectory":trajectory,
            })
        candidates.sort(key=lambda x:(x["mae"],
             x["parameters"]["capacity"],
             x["parameters"]["response_time"],
             str(x["parameters"]["loss_time"])))
        winner=candidates[0]
        prior=best_from_previous.get(structure["structure_hash"])
        need(prior is not None and
             len(candidates)==prior["external_grid_evaluations"] and
             abs(winner["mae"]-prior["best_in_grid"]["mae"]) <
                 COMPARE_BEST_MAE_TOL and
             winner["parameters"]==prior["best_in_grid"]["params"],
             "G3D_RECONSTRUCTED_G3_BEST_DRIFT")
        near=[x for x in candidates
              if x["mae"] <= winner["mae"]+g3.NEAR_BEST_MAE_DELTA]
        need(len(near)==prior["near_best_grid_count"],
             "G3D_NEAR_BEST_SET_DRIFT")
        outputs.append({
            "candidate_id":structure["id"],
            "native_structure_sha256":structure["structure_hash"],
            "n":n,"loss":has_loss,
            "all_grid_combinations":len(candidates),
            "best_MAE_from_known_O0":round(winner["mae"],8),
            "best_parameters_external_not_D_native":winner["parameters"],
            "near_best_grid_count":len(near),
            "best_trajectory":winner["trajectory"],
            "prediction_bands":{
                measure:{str(t):_envelope(near,measure,t)
                         for t in (PROPOSED_DELIVERY_TIMES
                                   if measure=="delivered_cumulative"
                                   else PROPOSED_STOCK_TIMES)}
                for measure in MEASURES
            },
            "near_best_set_is_not_a_confidence_interval":True,
        })
    return outputs,s


def _pairwise_representational_gaps(rows):
    comparisons=[]
    opportunities={f"{measure}@{t}":{
        "measure":measure,"time_minutes":t,
        "separated_family_pairs":0,
        "total_family_pairs":15,
        "max_nonoverlap_orders":0.,
        "interpretation":"PARAMETER_GRID_DIAGNOSTIC_NOT_STATISTICAL_POWER",
    } for measure in MEASURES
      for t in (PROPOSED_DELIVERY_TIMES
                if measure=="delivered_cumulative"
                else PROPOSED_STOCK_TIMES)}
    for a,b in combinations(rows,2):
        per=[]
        for key,entry in opportunities.items():
            measure=entry["measure"]; t=str(entry["time_minutes"])
            gap=_gap(a["prediction_bands"][measure][t],
                     b["prediction_bands"][measure][t])
            if gap>0:
                entry["separated_family_pairs"]+=1
                entry["max_nonoverlap_orders"]=max(
                    entry["max_nonoverlap_orders"],gap)
            per.append({"measurement":key,
                        "gap_between_near_best_envelopes":gap})
        comparisons.append({
            "a_id":a["candidate_id"],"b_id":b["candidate_id"],
            "a_n":a["n"],"a_loss":a["loss"],
            "b_n":b["n"],"b_loss":b["loss"],
            "possible_discrimination_by_measure":per,
        })
    need(len(comparisons)==15,"G3D_NOT_ALL_PAIRWISE_FAMILIES")
    return comparisons,sorted(
        opportunities.values(),
        key=lambda v:(-v["separated_family_pairs"],
                      -v["max_nonoverlap_orders"],
                      v["measure"],v["time_minutes"]))


def build(visible, frozen_g3):
    need(frozen_g3.get("schema")==g3.SCHEMA and
         frozen_g3.get("D",{}).get("mode")==
             "ARENA_EXTERNAL_CALIBRATION_EXPLORATORY_NUMERICAL_MIRROR" and
         frozen_g3.get("source_snapshot_hash")==
             visible.get("source_snapshot_hash") and
         frozen_g3.get("gates",{}).get("A3")=="PARTIAL" and
         frozen_g3.get("gates",{}).get("G4")==
             frozen_g3.get("gates",{}).get("G5")=="NOT_RUN",
         "G3D_FROZEN_G3_SCOPE_UNTRUSTWORTHY")
    families,source=_fit_models(visible,frozen_g3["D"])
    pairwise,opportunities=_pairwise_representational_gaps(families)
    def is_separated(pair, measurement):
        return any(x["measurement"]==measurement and
                   x["gap_between_near_best_envelopes"]>0
                   for x in pair["possible_discrimination_by_measure"])
    cross_loss=[p for p in pairwise if p["a_loss"]!=p["b_loss"]]
    within_loss=[p for p in pairwise if p["a_loss"]==p["b_loss"]]
    need(len(cross_loss)==9 and len(within_loss)==6,
         "G3D_WRONG_LOSS_SUBFAMILY_PAIR_COUNT")
    for item in opportunities:
        key=f'{item["measure"]}@{item["time_minutes"]}'
        item["separated_cross_loss_pairs"]=sum(
            is_separated(p,key) for p in cross_loss)
        item["separated_within_loss_group_pairs"]=sum(
            is_separated(p,key) for p in within_loss)
        need(item["separated_cross_loss_pairs"]+
             item["separated_within_loss_group_pairs"]==
             item["separated_family_pairs"],
             "G3D_PAIR_GROUP_CLASSIFICATION_DRIFT")
    return {
        "schema":SCHEMA,"source_snapshot_hash":visible["source_snapshot_hash"],
        "parent_G3_sha256":digest(frozen_g3),
        "task":"DESIGN_ONLY_AFTER_KNOWN_O0_CONSTRUCTION",
        "input_type":"15_KNOWN_POS_ARRIVALS_RIGHT_RECTANGULAR_HALF_MINUTE",
        "post_cutoff_input_policy":
            "ONLY_FROZEN_PRE_CUTOFF_EVENT_TAIL_THEN_ZERO_NEW_ARRIVALS",
        "after_cutoff_outcomes_observed":False,
        "future_numbers_are_conditional_scenarios_not_forecasts":True,
        "conditional_horizon_minutes":20,
        "construction_observation_times_minutes":list(CONSTRUCTION_TIMES),
        "measures_with_model_equations":{
            "delivered_cumulative":"NATIVE_D_DELIVERED",
            "total_wip":"SUM_ALL_NATIVE_D_STOCKS_REQUIRES_NEW_EXTERNAL_MEASUREMENT",
            "lost_cumulative":"NATIVE_D_LOST_NOT_YET_MAPPED_TO_BUSINESS_CANCELLATIONS",
        },
        "observability_caveats":{
            "O0_delivered_only_cannot_directly_observe_internal_stages":True,
            "O1_completed_preparation_aggregates_not_independent_experiment":True,
            "no_role_mapping_from_generic_D_stocks_to_real_prep":True,
            "fractional_continuous_lost_is_not_integer_cancelled_orders":True,
            "wip_plus_delivered_plus_lost_equals_input_mass":True,
            "timepoints_one_world_not_independent_replicas":True,
            "parameter_envelopes_are_descriptive_not_confidence_intervals":True,
        },
        "families":families,
        "pairwise_near_best_parameter_envelope_gaps":pairwise,
        "measurement_opportunities":opportunities,
        "subfamily_diagnosis":{
            "pairs_with_different_loss_assumption":len(cross_loss),
            "pairs_with_same_loss_assumption_but_different_stock_count":len(within_loss),
            "new_measurements_may_separate_loss_subfamilies_not_stock_count":True,
            "known_O0_does_not_identify_true_stock_count":True,
            "separation_is_conditional_on_near_best_grid_and_stop_scenario":True,
        },
        "measurement_classes_to_consider":[
            "RECORD_CUMULATIVE_DELIVERIES_DURING_KNOWN_ARRIVAL_PAUSE",
            "DIRECTLY_COUNT_TOTAL_ORDERS_PHYSICALLY_IN_PROCESS",
            "SEPARATELY_LOG_REAL_CANCELLATIONS_OR_LOSSES_WITH_OPERATIONAL_DEFINITION",
            "INSTRUMENT_DISTINCT_REAL_QUEUES_ONLY_IF_STAGE_TO_STOCK_MAPPING_EVIDENCED",
        ],
        "no_measurement_discrimination_claim":True,
        "no_scientific_winner":True,
        "no_new_DES_or_OMC_or_provider":True,
        "G3":"EXPLORATORY_IDENTIFIABILITY_DIAGNOSTIC_ONLY",
        "G4":"NOT_RUN","G5":"NOT_RUN","A3":"PARTIAL",
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--visible",type=Path,required=True)
    parser.add_argument("--previous-g3",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    need(not args.out.exists(),"G3D_REFUSE_OVERWRITE")
    visible=json.loads(args.visible.read_text(encoding="utf-8"))
    frozen=json.loads(args.previous_g3.read_text(encoding="utf-8"))
    doc=build(visible,frozen)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_bytes(canonical(doc)+b"\n")
    print(json.dumps({
        "families":len(doc["families"]),
        "pairwise":len(doc["pairwise_near_best_parameter_envelope_gaps"]),
        "opportunities":len(doc["measurement_opportunities"]),
        "G3":doc["G3"],"G4":doc["G4"],"G5":doc["G5"],
    },sort_keys=True))


if __name__=="__main__":
    main()
