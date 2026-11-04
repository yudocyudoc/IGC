"""F4 structural non-identifiability: commute two downstream FIFO service stages.

KNOWN SYNTHETIC EV-01 EVALUATOR ONLY. The original EV01 private configuration
and original DES engine are reused; no B/D/M worker receives the config or
private trace. This is a development counterexample, NOT an independent G5.

For two successive single-server, constant-service FIFO stations with
unlimited waiting, the departure operator F_a commutes with F_b. Exchanging
a,b preserves *all* terminal departure times, not just a sample-grid fit.
Unchanged prefix stages also preserve preparation-only O1 in both worlds.

A COMMON stress intervention adding 1/2 minute of work at stage "despacho"
breaks that symmetry: it exposes different latent downstream capacities.
It is NOT a proposed business improvement, instrumental accuracy claim,
new DES engine, process mining attribution, or native D/B/M inference.
"""
from __future__ import annotations

import argparse
from fractions import Fraction as Q
import json
from pathlib import Path

from scripts.arena_cafe import ev01
from scripts.arena_cafe.native_handoff import need, validate_a1_visible
from scripts.arena_physical import des_engine as des
from scripts.arena_v0_contract import canonical,digest

SCHEMA="igc-arena-f4-latent-downstream-structural-symmetry/0.1"
CHECKPOINTS=tuple(Q(n) for n in (0,2,4,6,8,10,12,16,20))
STAGES=ev01.STAGES
BASELINE_KEYS=("REFERENCE_EV01_WORLD_A","SWAPPED_DOWNSTREAM_WORLD_B")
ACTION_STAGE="despacho"
ADDITIONAL_WORK_MINUTES=Q(1,2)
ACTION="ADD_30_SECONDS_SERVICE_WORK_PER_ORDER_AT_DISPATCH_FROM_T0"


def one_server_departures(arrivals, service):
    """Verification recurrence, not a simulation generator or fitter."""
    duration=des.quantity(service)
    need(duration>0,"F4SYM_INVALID_SERVICE")
    prev=Q(0)
    departures=[]
    starts=[]
    for t in arrivals:
        start=max(Q(t),prev)
        prev=start+duration
        starts.append(start)
        departures.append(prev)
    return tuple(starts),tuple(departures)


def n_server_fixed_departures(arrivals, servers, service):
    """Independent exact FIFO prefix verifier for the existing DES."""
    need(type(servers) is int and 1<=servers<=20,
         "F4SYM_INVALID_SERVERS")
    availability=[Q(0)]*servers
    departures=[]
    for t in arrivals:
        slot=min(range(servers),key=lambda i:(availability[i],i))
        end=max(Q(t),availability[slot])+Q(service)
        availability[slot]=end
        departures.append(end)
    need(all(a<=b for a,b in zip(departures,departures[1:])),
         "F4SYM_PREFIX_OVERTAKE_UNSUPPORTED")
    return tuple(departures)


def private_pair():
    """Design-time evaluator private truth; never given to producers."""
    origin=ev01.config()
    spec=des.validate_private_config(origin)
    need(len(spec)==4 and STAGES==(
        "caja","preparacion","despacho","transferencia_final")
        and spec[0][0]==2 and
        all(n==1 for n,_ in spec[1:])
        and spec[2][1]!=spec[3][1],
        "F4SYM_ORIGINAL_PRIVATE_PHYSICS_DRIFT")
    swapped={
        "schema":origin["schema"],
        "tie_policy":origin["tie_policy"],
        "stages":[dict(s) for s in origin["stages"]],
    }
    swapped["stages"][2]["service_minutes"] = str(spec[3][1])
    swapped["stages"][3]["service_minutes"] = str(spec[2][1])
    need(des.validate_private_config(swapped)[0:2]==spec[0:2] and
         des.validate_private_config(swapped)[2][1]==spec[3][1] and
         des.validate_private_config(swapped)[3][1]==spec[2][1],
         "F4SYM_PREFIX_CHANGED_OR_NOT_EXACT_SWAP")
    return origin,swapped


def stressed(config):
    copy={
        "schema":config["schema"],
        "tie_policy":config["tie_policy"],
        "stages":[dict(s) for s in config["stages"]],
    }
    copy["stages"][2]["service_minutes"]=str(
        Q(copy["stages"][2]["service_minutes"])+ADDITIONAL_WORK_MINUTES)
    need(des.validate_private_config(copy)[2][0]==1 and
         all(x==y for i,(x,y) in enumerate(zip(
             config["stages"],copy["stages"])) if i!=2),
         "F4SYM_ACTION_NOT_IDENTICAL_OR_LOCAL")
    return copy


def projection(snapshots):
    return [{
       "t_minutes_exact":str(s.t_min),
       "created_cumulative":s.accepted_cum_orders,
       "delivered_cumulative":s.delivered_cum_orders,
       "pending_total":s.pending_orders,
       # Evaluator-only stock distribution: never producer input.
       "stage_wip_evaluator_only":dict(zip(STAGES,(
           w+i for w,i in zip(s.stage_waiting,s.stage_in_service)))),
    } for s in snapshots]


def proof_certificate(arrivals,pair,o1):
    ref,alternative=pair
    p1=des.validate_private_config(ref)
    p2=des.validate_private_config(alternative)
    caja=n_server_fixed_departures(arrivals,p1[0][0],p1[0][1])
    prep_start,prep_end=one_server_departures(caja,p1[1][1])
    # A and B have the SAME input to both final stages, and exactly
    # one deterministic FIFO server at each. Exchanging them commutes.
    _,after_a=one_server_departures(prep_end,p1[2][1])
    _,delivered_a=one_server_departures(after_a,p1[3][1])
    _,after_b=one_server_departures(prep_end,p2[2][1])
    _,delivered_b=one_server_departures(after_b,p2[3][1])
    need(delivered_a==delivered_b and len(delivered_a)==15,
         "F4SYM_EXACT_ALL_DELIVERY_TIMES_NOT_IDENTICAL")
    cutoff=Q(o1["observability"]["cutoff_minutes_exact"])
    completed=[i for i,t in enumerate(prep_end) if t<cutoff]
    need(completed,"F4SYM_EMPTY_PREP_BEFORE_CUTOFF")
    observed=o1["construction"]["physical_observation"]
    n=len(completed)
    wait=sum((prep_start[i]-caja[i] for i in completed),Q(0))/n
    service=sum((prep_end[i]-prep_start[i] for i in completed),Q(0))/n
    need(
        observed["n_completed_stage_services"]==n and
        Q(observed["mean_wait_minutes_exact"])==wait and
        Q(observed["mean_service_minutes_exact"])==service,
        "F4SYM_O1_PREPARATION_OPERATOR_NOT_MATCHED")
    return {
        "all_15_exact_terminal_delivery_times_identical":True,
        "all_preparation_start_finish_times_identical":True,
        "total_terminal_events_verified":len(delivered_a),
        "preparation_completed_pre_cutoff":n,
        "mean_preparation_wait_minutes_exact":str(wait),
        "mean_preparation_service_minutes_exact":str(service),
        # Do not output evaluator-only arrival->per-case stage timestamps.
        "timestamp_sequences_evaluator_only_not_exported":True,
        "commutation_claim_scope":
            "TWO_SINGLE_SERVER_CONSTANT_SERVICE_FCFS_UNLIMITED_BUFFER_STAGES",
    }


def build(o0,o1):
    validate_a1_visible(o0,"O0")
    validate_a1_visible(o1,"O1")
    need(o0["observability"]["world_public_id"]==
         o1["observability"]["world_public_id"] and
         o0["observability"]["cutoff_minutes_exact"]==
         o1["observability"]["cutoff_minutes_exact"]=="10" and
         o0["construction"]["pos_arrival_events"]==
         o1["construction"]["pos_arrival_events"] and
         o0["construction"]["observation_series"]==
         o1["construction"]["observation_series"],
         "F4SYM_DIFFERENT_SOURCE_WORLDS_OR_CONDITIONS")
    arrivals=tuple(Q(r["t_minutes_exact"]) for r in
                   o0["construction"]["pos_arrival_events"])
    need(len(arrivals)==15 and arrivals==des.half_open_arrivals("5/2",6),
         "F4SYM_PUBLIC_ARRIVALS_NOT_ORIGINAL_EV01")
    origin,alternative=private_pair()
    pair=(origin,alternative)
    analytic=proof_certificate(arrivals,pair,o1)
    baseline={}
    intervention={}
    for key,config in zip(BASELINE_KEYS,pair):
        base=des.run_toy_engine(config,arrivals,CHECKPOINTS)
        change=des.run_toy_engine(stressed(config),arrivals,CHECKPOINTS)
        need(all(s.accepted_cum_orders==s.delivered_cum_orders+
                 s.pending_orders==s.delivered_cum_orders+
                 sum(s.stage_waiting)+sum(s.stage_in_service)
                 for s in base+change),
             "F4SYM_PHYSICAL_CONSERVATION_FAILED")
        baseline[key]=projection(base)
        intervention[key]=projection(change)
    need(baseline[BASELINE_KEYS[0]]!=baseline[BASELINE_KEYS[1]],
         "F4SYM_INTERNAL_WIP_SHOULD_DIFFER")
    baseline_terminal=[
        [x["delivered_cumulative"] for x in baseline[key]]
        for key in BASELINE_KEYS
    ]
    need(baseline_terminal[0]==baseline_terminal[1],
         "F4SYM_BASELINE_TERMINAL_MISMATCH")
    wanted=[r["delivered_cumulative"] for r in
            o0["construction"]["observation_series"]]
    sample=[x["delivered_cumulative"] for x in baseline[BASELINE_KEYS[0]]
            if Q(x["t_minutes_exact"])<=Q(10)]
    need(sample==wanted==[0,0,2,4,6,8],
         "F4SYM_NOT_REAL_O0_OBSERVATIONAL_EQUIVALENCE")
    by_key={key:intervention[key] for key in BASELINE_KEYS}
    at_10={
        key:next(x["delivered_cumulative"] for x in by_key[key]
                 if x["t_minutes_exact"]=="10")
        for key in BASELINE_KEYS
    }
    need(at_10=={BASELINE_KEYS[0]:6,BASELINE_KEYS[1]:8},
         "F4SYM_COMMON_ACTION_LOST_LATENT_DIVERGENCE")
    return {
        "schema":SCHEMA,
        "phase":"F4_KNOWN_EVALUATOR_DEVELOPMENT_NOT_INDEPENDENT_F5",
        "origin":"EV01_KNOWN_SYNTHETIC_EVALUATOR_PRIVATE_CONFIGURATION",
        "world_public_id":o0["observability"]["world_public_id"],
        "source_o0_hash":o0["source_snapshot_hash"],
        "source_o1_hash":o1["source_snapshot_hash"],
        "original_O0_and_O1_compatible_for_BOTH_mechanisms":True,
        "same_physical_evidence_before_intervention":True,
        "construction":"SWAP_TWO_DOWNSTREAM_SINGLE_SERVER_SERVICE_DURATIONS",
        "swap_proven_for_all_arrival_schedules_under_declared_assumptions":True,
        "proof":analytic,
        "both_baselines_delivered_cumulative_at_O0_times":wanted,
        "original_O1_preparation_aggregate":{
            "n_completed_stage_services":analytic["preparation_completed_pre_cutoff"],
            "mean_service_minutes_exact":analytic["mean_preparation_service_minutes_exact"],
            "mean_wait_minutes_exact":analytic["mean_preparation_wait_minutes_exact"],
        },
        "underlying_mechanisms":{
            "A":"ORIGINAL_EV01_EVALUATOR_REFERENCE",
            "B":"SAME_UPSTREAM_SWAP_DOWNSTREAM_SERVICE_DURATIONS",
        },
        "same_active_baseline_bottleneck_in_both":"PREPARACION",
        "ambiguous_latent_downstream_constraint":True,
        "intervention":{
            "action":ACTION,
            "stage":"despacho",
            "added_service_minutes_exact":str(ADDITIONAL_WORK_MINUTES),
            "same_absolute_change_from_t0_both_worlds":True,
            "new_empty_initial_state_same_15_arrivals":True,
            "operational_feasibility_and_cost":"NOT_ASSESSED",
            "not_a_business_improvement_proposal":True,
        },
        "counterfactual_delivered_at_t10":at_10,
        "absolute_counterfactual_gap_orders_t10":abs(
            at_10[BASELINE_KEYS[0]]-at_10[BASELINE_KEYS[1]]),
        "counterfactual_curves_by_time":{
            key:[{"t":x["t_minutes_exact"],
                  "delivered_cumulative":x["delivered_cumulative"]}
                 for x in intervention[key]]
            for key in BASELINE_KEYS},
        "internal_stage_wip_is_evaluator_only":True,
        "stage_paths_same_in_both_no_process_route_variation":True,
        "P_DFG_not_causal_identification":True,
        "PM_incremental_over_B1_B2":"NOT_DEMONSTRATED",
        "D_B_M_native_inference_on_this_design":"NOT_RUN",
        "F5_independent_reserve":"NOT_CREATED",
        "A3":"PARTIAL","G4":"NOT_RUN","G5":"NOT_RUN",
        "no_parameter_grid_or_fitter_or_new_DES_engine":True,
        "no_live_provider_no_PM4Py_no_OMC":True,
        "not_an_independent_test":True,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--o0",type=Path,required=True)
    p.add_argument("--o1",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    need(not a.out.exists(),"F4SYM_REFUSE_OVERWRITE")
    load=lambda path:json.loads(path.read_text(encoding="utf-8"))
    report=build(load(a.o0),load(a.o1))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_bytes(canonical(report)+b"\n")
    print(json.dumps({
        "status":report["phase"],
        "O0_O1_compatible":report[
            "original_O0_and_O1_compatible_for_BOTH_mechanisms"],
        "exact_terminal_times":report["proof"][
            "all_15_exact_terminal_delivery_times_identical"],
        "counterfactual_gap":report["absolute_counterfactual_gap_orders_t10"],
        "G4":report["G4"],"G5":report["G5"],
    },sort_keys=True))


if __name__=="__main__":
    main()
