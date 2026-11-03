"""F4 known-data DEVELOPMENT witness for rival causal bottleneck locations.

NO parameter grid, fitter, PM implementation, new DES engine or G4/G5.

Two deliberately constructed three-stage tandem mechanisms:
  A: prep 1, dispatch 3/5, final 2/5 minutes per job
  B: prep 3/5, dispatch 1, final 2/5 minutes per job

With the same public EV01 arrival times, both match O0 POS cumulative
deliveries exactly at its six checkpoints. Their *internal queues* differ.
The SAME intervention (+1 prep server from t=0, new counterfactual run)
changes output differently. These are public, retrospective DESIGN witnesses
chosen using known O0, NOT recovered truth, scientific identification, or
forecast on a private reserve.

Process mining P is NOT used to invent hidden stages; no FULL or B1/B2 data
enters this builder. F6 is conditional on process variation beyond B1/B2.
"""
from __future__ import annotations

import argparse
from fractions import Fraction as Q
import json
from pathlib import Path

from scripts.arena_physical import des_engine as des
from scripts.arena_cafe.native_handoff import need, validate_a1_visible
from scripts.arena_v0_contract import canonical, digest

SCHEMA="igc-arena-f4-rival-bottleneck-design-witness/0.1"
TIMES=(Q(0),Q(2),Q(4),Q(6),Q(8),Q(10))
# Fixed analytically motivated contrast, not a catalogue or parameter sweep.
STAGES=("preparacion","despacho","transferencia_final")
A_SERVICE=("1","3/5","2/5")
B_SERVICE=("3/5","1","2/5")
ACTION="ADD_ONE_PREPARATION_SERVER_FROM_TIME_ZERO"
PRIMARY_HORIZON_MINUTES=Q(10)
S0_TOLERANCE_ORDERS=0
MIN_COUNTERFACTUAL_DIVERGENCE_ORDERS=3


def _config(times, prep_servers=1):
    need(len(times)==len(STAGES)==3 and
         prep_servers in (1,2),
         "F4_INVALID_CONSTRUCTIVE_WITNESS")
    return {
        "schema":des.SCHEMA,
        "tie_policy":des.TIE_POLICY,
        "stages":[
            {"servers":prep_servers if i==0 else 1,
             "service_minutes":t}
            for i,t in enumerate(times)
        ],
    }


def _run(config, arrivals):
    rows=des.run_toy_engine(config,arrivals,TIMES)
    need(len(rows)==len(TIMES) and
         all(s.accepted_cum_orders==s.delivered_cum_orders+
             s.pending_orders==s.delivered_cum_orders+
             sum(s.stage_waiting)+sum(s.stage_in_service)
             for s in rows),
         "F4_MATERIAL_ACCOUNTING_FAILED")
    return rows


def _outputs(rows):
    return [s.delivered_cum_orders for s in rows]


def _wip(rows):
    return [{
        "time_minutes_exact":str(s.t_min),
        "total_pending_orders":s.pending_orders,
        "waiting_by_physical_stage_EVALUATOR_ONLY":dict(zip(STAGES,s.stage_waiting)),
        "in_service_by_physical_stage_EVALUATOR_ONLY":dict(zip(STAGES,s.stage_in_service)),
    } for s in rows]


def build(o0):
    """O0 only: no private truth, hidden-world parameters or FULL event logs."""
    validate_a1_visible(o0,"O0")
    need(o0["observability"]["cutoff_minutes_exact"]=="10"
         and o0["observability"]["window"]=="[0,cutoff)"
         and "physical_observation" not in o0["construction"]
         and len(o0["construction"]["pos_arrival_events"])==15,
         "F4_NOT_KNOWN_O0_PUBLIC_ONLY")
    series=o0["construction"]["observation_series"]
    need([Q(x["t_minutes_exact"]) for x in series]==list(TIMES),
         "F4_POS_SAMPLE_TIMES_CHANGED")
    observed=[s["delivered_cumulative"] for s in series]
    created=[s["orders_created_cumulative"] for s in series]
    need(all(type(x) is int for x in observed+created)
         and observed==[0,0,2,4,6,8]
         and all(0<=x<=y<=15 for x,y in zip(observed,created)),
         "F4_EV01_PUBLIC_OBSERVATIONS_CHANGED")
    arrivals=tuple(Q(ev["t_minutes_exact"]) for ev in
                   o0["construction"]["pos_arrival_events"])
    need(len(arrivals)==15 and
         all(a<b for a,b in zip(arrivals,arrivals[1:]))
         and all(Q(0)<=t<Q(10) for t in arrivals)
         and [sum(x<t for x in arrivals) for t in TIMES]==created,
         "F4_POS_TIMESTAMPS_NOT_CAUSAL_INPUT")
    baseline={}
    intervention={}
    for name,times in (("PREP_SLOW_A",A_SERVICE),
                       ("DISPATCH_SLOW_B",B_SERVICE)):
        original_cfg=_config(times)
        action_cfg=_config(times,prep_servers=2)
        native=_run(original_cfg,arrivals)
        changed=_run(action_cfg,arrivals)
        need(_outputs(native)==observed,
             "F4_EXACT_POS_COMPATIBILITY_FAILED:"+name)
        baseline[name]={
            "service_minutes_exact":dict(zip(STAGES,times)),
            "servers_by_stage":{stage:1 for stage in STAGES},
            "nominal_capacities_orders_per_hour_exact":{
                stage:str(Q(60)/Q(t)) for stage,t in zip(STAGES,times)},
            "delivered_cumulative":_outputs(native),
            "total_pending_orders":[s.pending_orders for s in native],
            "private_evaluator_stage_states":_wip(native),
            "pos_compatible_at_all_six_times":True,
        }
        intervention[name]={
            "action":ACTION,
            "servers_by_stage":dict(zip(STAGES,(2,1,1))),
            "delivered_cumulative":_outputs(changed),
            "total_pending_orders":[s.pending_orders for s in changed],
            "private_evaluator_stage_states":_wip(changed),
        }
    need(baseline["PREP_SLOW_A"]["delivered_cumulative"]==
         baseline["DISPATCH_SLOW_B"]["delivered_cumulative"]==observed,
         "F4_WITNESS_BASELINES_NOT_OBSERVATIONALLY_EQUIVALENT")
    need(baseline["PREP_SLOW_A"]["service_minutes_exact"]!=
         baseline["DISPATCH_SLOW_B"]["service_minutes_exact"] and
         baseline["PREP_SLOW_A"]["private_evaluator_stage_states"]!=
         baseline["DISPATCH_SLOW_B"]["private_evaluator_stage_states"],
         "F4_RIVALS_NOT_PHYSICALLY_DISTINCT")
    a,b=(intervention[k]["delivered_cumulative"][-1]
         for k in ("PREP_SLOW_A","DISPATCH_SLOW_B"))
    gap=abs(a-b)
    need(gap>=MIN_COUNTERFACTUAL_DIVERGENCE_ORDERS,
         "F4_SAME_ACTION_NOT_DISCRIMINATING")
    need(intervention["PREP_SLOW_A"]["delivered_cumulative"][-1]>
         baseline["PREP_SLOW_A"]["delivered_cumulative"][-1]
         and intervention["DISPATCH_SLOW_B"]["delivered_cumulative"][-1]==
         baseline["DISPATCH_SLOW_B"]["delivered_cumulative"][-1],
         "F4_BOTTLENECK_MECHANISM_ACTION_EFFECT_CONTRADICTED")
    return {
        "schema":SCHEMA,
        "phase":"F4_DEVELOPMENT_CONSTRUCTIVE_WITNESS_NOT_F5",
        "source_snapshot_hash":o0["source_snapshot_hash"],
        "source_visible_sha256":digest(o0),
        "world":"ALTERNATIVE_SYNTHETIC_HYPOTHESES_NOT_TRUE_EV01_CONFIG",
        "initial_evidence":"KNOWN_EV01_O0_POS_ONLY",
        "S0_times_minutes_exact":[str(x) for x in TIMES],
        "S0_observed_delivered_cumulative":observed,
        "S0_observed_created_cumulative":created,
        "observed_sample_convention":"events_strictly_before_sample_t",
        "s0_tolerance_orders":S0_TOLERANCE_ORDERS,
        "fixed_rivals_selected_constructively_not_parameter_grid":True,
        "original_DES_engine_unchanged":True,
        "stage_names_are_hypothetical_not_identified_from_O0":True,
        "rivalling_causal_bottleneck_classes":{
            "PREP_SLOW_A":"PREPARATION_LIMIT_60_PER_H",
            "DISPATCH_SLOW_B":"DISPATCH_LIMIT_60_PER_H",
        },
        "S0_model_baselines":baseline,
        "one_common_intervention":{
            "action":ACTION,
            "meaning":"one additional identical preparation workstation from t=0",
            "action_applied_in_new_counterfactual_runs_from_empty_state":True,
            "not_a_post_cutoff_operational_change":True,
            "same_15_public_order_arrivals":True,
            "business_costs_available":False,
            "physical_space_staff_inventory_feasibility":"NOT_ASSESSED",
        },
        "S0_model_after_action":intervention,
        "primary_endpoint":"DELIVERED_CUMULATIVE_AT_10_MINUTES",
        "a_postaction_delivered_t10":a,
        "b_postaction_delivered_t10":b,
        "absolute_counterfactual_divergence_orders":gap,
        "development_threshold_minimum_gap_orders":
            MIN_COUNTERFACTUAL_DIVERGENCE_ORDERS,
        "counterfactuals_are_simulated_not_observed":True,
        "joint_B0_POS_cannot_disambiguate_rival_location":True,
        "B1_FULL_can_measure_stage_service_but_not_given_to_S0":True,
        "PM_observed_DFG_alone_cannot_prove_bottleneck_causality":True,
        "PM_incremental_over_B1_B2":"NOT_ESTABLISHED",
        "PM_ablation_with_without_P":"NOT_RUN",
        "D_B_M_native_inference_on_this_F4_pair":"NOT_RUN",
        "F5_new_independent_worlds":"NOT_CREATED",
        "G4":"NOT_RUN","G5":"NOT_RUN","A3":"PARTIAL",
        "no_new_DES_or_parameter_grid_or_provider_or_PM":True,
        "preregistered_future_experiment":False,
        "development_witness_is_not_prospective_confirmation":True,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--o0",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    need(not args.out.exists(),"F4_REFUSE_OVERWRITE")
    report=build(json.loads(args.o0.read_text(encoding="utf-8")))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_bytes(canonical(report)+b"\n")
    print(json.dumps({
        "S0_exact":report["S0_model_baselines"]["PREP_SLOW_A"][
            "delivered_cumulative"]==report["S0_observed_delivered_cumulative"],
        "delta_t10":report["absolute_counterfactual_divergence_orders"],
        "phase":report["phase"],"G4":report["G4"],"G5":report["G5"],
    },sort_keys=True))


if __name__=="__main__":
    main()
