"""F4 evaluator-only B2 processing-period reference versus intervention sensitivity.

No extra D/B/M arm, no PM, no new physical engine. Uses the original CAF-01
DES snapshots and the already established F4 FIFO downstream-swap worlds.
Reconstructs their deterministic service *intervals* via the same FIFO
recurrences, checks them against DES state snapshots, cross-checks the
reference EV01 FULL telemetry, and passes physical events through existing B2.

APM here means a STRICTLY LIMITED "longest uninterrupted PROCESSING period
per resource" proxy. B2 labels non-processing intervals UNKNOWN without
availability telemetry. Setup, repair, blocking, starvation, and availability
are NOT measured; this is not the full active-period method nor causal truth.

The observed action is an adverse +1/2 min service stress at dispatch from t0,
not a feasible intervention recommendation. Everything is known-synthetic
development evaluator truth, never an O0/O1 arm input or blind G5 reserve.
"""
from __future__ import annotations

import argparse
import json
from fractions import Fraction as Q
from pathlib import Path

from scripts.arena_cafe import ev01, f2_physical_controls as b2
from scripts.arena_cafe import f4_latent_downstream_symmetry as symmetry
from scripts.arena_cafe.native_handoff import need, validate_a1_visible
from scripts.arena_physical import des_engine as des
from scripts import arena_event_observability as obs
from scripts.arena_v0_contract import canonical, digest

SCHEMA="igc-cafe-f4-b2-processing-period-action-reference/0.1"
HORIZON=Q(30)
CHECKPOINTS=symmetry.CHECKPOINTS+(HORIZON,)
STAGES=ev01.STAGES
KEYS=symmetry.BASELINE_KEYS
ACTION=symmetry.ACTION
ACTION_MINUTES=symmetry.ADDITIONAL_WORK_MINUTES


def analytic_intervals(config,arrivals):
    """One deterministic FCFS schedule, independent of DES's event heap.

    Reconstructs resource intervals for *evaluating* existing worlds, not
    fitting a model. The existing DES is checked separately at all snapshots.
    """
    stages=des.validate_private_config(config)
    need(len(stages)==len(STAGES) and len(arrivals)==15 and
         all(a<b for a,b in zip(arrivals,arrivals[1:])),
         "F4APM_UNSUPPORTED_KNOWN_EV01_SCHEDULE")
    previous=tuple(Q(a) for a in arrivals)
    intervals={}
    for stage,(servers,work) in zip(STAGES,stages):
        free=[Q(0) for _ in range(servers)]
        events=[]
        ends=[]
        for i,enter in enumerate(previous):
            resource=min(range(servers),key=lambda j:(free[j],j))
            start=max(enter,free[resource])
            end=start+work
            need(enter<=start<end,
                 "F4APM_NONPHYSICAL_FCFS_INTERVAL")
            free[resource]=end
            ends.append(end)
            events.append({
                "case_id":f"O{i:03d}",
                "stage":stage,
                "resource_id":f"{stage}-r{resource+1}",
                "entry":enter,"start":start,"finish":end,
            })
        need(all(a<=b for a,b in zip(ends,ends[1:])),
             "F4APM_ORDER_OVERTAKE_NOT_SUPPORTED")
        intervals[stage]=events
        previous=tuple(ends)
    return intervals


def physical_event_rows(intervals):
    """The B2 stage-event interface, for the synthetic evaluator ONLY."""
    events=[]
    for stage in STAGES:
        for visit in intervals[stage]:
            for kind,at in (("etapa_entrada",visit["entry"]),
                            ("servicio_inicio",visit["start"]),
                            ("servicio_fin",visit["finish"])):
                events.append({
                    "case_id":visit["case_id"],
                    "stage":stage,
                    "event_type":kind,
                    "t_minutes_exact":str(at),
                    "resource_id":visit["resource_id"] if
                        kind!="etapa_entrada" else None,
                    "source":"instrumentacion_fisica",
                })
    need(len(events)==15*3*len(STAGES),
         "F4APM_PHYSICAL_EVENT_COUNT_DRIFT")
    return events


def verify_des_snapshots(config,arrivals,intervals):
    """Independently reconcile analytic FCFS intervals and original DES."""
    snapshots=des.run_toy_engine(config,arrivals,CHECKPOINTS)
    need(len(snapshots)==len(CHECKPOINTS),
         "F4APM_DES_CHECKPOINTS_INCOMPLETE")
    for snap in snapshots:
        t=snap.t_min
        accepted=sum(a<=t for a in arrivals)
        delivered=sum(v["finish"]<=t for v in intervals[STAGES[-1]])
        waits=tuple(sum(v["entry"]<=t<v["start"]
                        for v in intervals[stage]) for stage in STAGES)
        running=tuple(sum(v["start"]<=t<v["finish"]
                          for v in intervals[stage]) for stage in STAGES)
        need(accepted==snap.accepted_cum_orders and
             delivered==snap.delivered_cum_orders and
             waits==snap.stage_waiting and
             running==snap.stage_in_service and
             accepted==delivered+sum(waits)+sum(running),
             "F4APM_ANALYTIC_SERVICE_STATE_NOT_ORIGINAL_DES")
    return snapshots


def verify_original_full(intervals):
    """Original EV01 independently generated physical FULL, world A only."""
    raw,snapshots=ev01.trace_generator()
    ev01.verify_des_parity(snapshots)
    full=obs.project_events(raw,"FULL")
    expected={(row["case_id"],row["stage"],row["event_type"]):
              (Q(row["t_minutes_exact"]),row.get("resource_id"))
              for row in full if row["event_type"] in
              ("etapa_entrada","servicio_inicio","servicio_fin")}
    actual={(row["case_id"],row["stage"],row["event_type"]):
            (Q(row["t_minutes_exact"]),row["resource_id"])
            for row in physical_event_rows(intervals)}
    need(len(expected)==len(actual)==180 and expected==actual,
         "F4APM_REFERENCE_FULL_SOURCE_NOT_REPRODUCED")
    return True


def per_resource_processing_periods(b2_result,resources):
    """Merge adjacent B2 PROCESSING intervals per physical server.

    A [t0,t1) processing span joins the next if t1==t2 with no inactive
    interval. UNKNOWN outside service is not reclassified as idle/available.
    """
    need(b2_result["status"]=="B2_EXACT_RESOURCE_PERIODS_PASS" and
         b2_result["availability_source"]=="NO_AVAILABILITY_TELEMETRY" and
         Q(b2_result["horizon_minutes_exact"])==HORIZON,
         "F4APM_B2_WITHOUT_PERMITTED_PROCESSING_PROVENANCE")
    result={}
    for stage,ids in resources.items():
        longest=Q(0)
        total=Q(0)
        episodes=0
        by_resource={}
        for rid in ids:
            starts=None
            last=None
            runs=[]
            spent=Q(0)
            for segment in b2_result["segments"]:
                left=Q(segment["start_minutes_exact"])
                right=Q(segment["end_minutes_exact"])
                need(left<right and (last is None or left==last),
                     "F4APM_B2_NONCONTIGUOUS_TIMELINE")
                last=right
                state=segment["by_stage"][stage]["resource_states"][rid]
                need(state in ("PROCESSING","UNKNOWN"),
                     "F4APM_B2_INVENTED_AVAILABILITY_STATE")
                if state=="PROCESSING":
                    spent+=right-left
                    if starts is None:
                        starts=left
                elif starts is not None:
                    runs.append((starts,left))
                    starts=None
            need(last==HORIZON,"F4APM_B2_HORIZON_NOT_COVERED")
            if starts is not None:
                runs.append((starts,HORIZON))
            need(all(a<b for a,b in runs) and
                 sum((b-a for a,b in runs),Q(0))==spent,
                 "F4APM_B2_PROCESSING_EPISODE_MISMATCH")
            expected=b2_result["resource_total_minutes"][rid]
            need(spent==Q(expected.get("PROCESSING","0")),
                 "F4APM_B2_RESOURCE_TOTAL_MISMATCH")
            max_length=max((b-a for a,b in runs),default=Q(0))
            longest=max(longest,max_length)
            total+=spent
            episodes+=len(runs)
            by_resource[rid]={
                "longest_processing_minutes_exact":str(max_length),
                "total_processing_minutes_exact":str(spent),
                "processing_episode_count":len(runs),
                "nonprocessing_is_NOT_MEASURED_AS_IDLE":True,
            }
        result[stage]={
            "longest_resource_processing_minutes_exact":str(longest),
            "total_resource_processing_minutes_exact":str(total),
            "processing_episode_count":episodes,
            "individual_resources":by_resource,
            "multiple_servers_not_merged_into_a_fictitious_single_machine":
                len(ids)>1,
        }
    ranking=sorted(result,key=lambda s:
                   (-Q(result[s]["longest_resource_processing_minutes_exact"]),
                    s))
    # The period reducer can be tested on a subset of physical resources;
    # the full four-stage coverage invariant belongs to the caller that
    # compares the known F4 worlds, not to this per-resource helper.
    need(len(ranking)==len(resources) and
         bool(ranking) and set(ranking).issubset(STAGES),
         "F4APM_STAGE_RANKING_INCOMPLETE")
    return {
        "proxy":"LONGEST_UNINTERRUPTED_OBSERVED_PROCESSING_PER_RESOURCE",
        "not_full_active_period_method":True,
        "missing_states":["SETUP","CLEANING","BREAKDOWN","BLOCKING",
                          "AVAILABILITY_WHEN_NOT_PROCESSING"],
        "idle_and_available_are_not_inferred_from_silence":True,
        "horizon_minutes_exact":str(HORIZON),
        "winner_under_processing_only_proxy":ranking[0],
        "ranked_stages_by_longest_processing":ranking,
        "stages":result,
        "not_causal_bottleneck_truth":True,
    }


def measured_world(config,arrivals,*,original_source=False):
    intervals=analytic_intervals(config,arrivals)
    snaps=verify_des_snapshots(config,arrivals,intervals)
    if original_source:
        verify_original_full(intervals)
    events=physical_event_rows(intervals)
    resources={stage:[f"{stage}-r{i+1}" for i in range(n)]
               for stage,(n,_) in
               zip(STAGES,des.validate_private_config(config))}
    need(set(resources)==set(STAGES) and
         all(resources[stage] for stage in STAGES),
         "F4APM_STAGE_RANKING_INCOMPLETE")
    periods=b2.resource_periods(events,resources,HORIZON,
                                available=None)
    apm=per_resource_processing_periods(periods,resources)
    counts={str(s.t_min):s.delivered_cum_orders for s in snaps}
    return {
        "apm":apm,
        "deliveries_at_t10":counts["10"],
        "counts_checkpoints":counts,
        "B2_processing_periods_verified":True,
        "B2_no_availability_telemetry":True,
        "DES_and_independent_analytic_states_match_all_checkpoints":True,
        "original_EV01_FULL_parity":True if original_source
                                 else "NOT_ORIGINAL_WORLD",
    }


def build(o0,o1):
    """F4 known-truth development only; no method access to FULL or DES."""
    validate_a1_visible(o0,"O0")
    validate_a1_visible(o1,"O1")
    reference=symmetry.build(o0,o1)
    need(reference["original_O0_and_O1_compatible_for_BOTH_mechanisms"] and
         reference["proof"]["all_15_exact_terminal_delivery_times_identical"],
         "F4APM_ORIGINAL_PAIR_NOT_OBSERVATIONALLY_EQUIVALENT")
    arrivals=tuple(Q(x["t_minutes_exact"]) for x in
                   o0["construction"]["pos_arrival_events"])
    a,b=symmetry.private_pair()
    baselines={}
    after={}
    for key,config in zip(KEYS,(a,b)):
        baselines[key]=measured_world(config,arrivals,
                                     original_source=(key==KEYS[0]))
        after[key]=measured_world(symmetry.stressed(config),arrivals)
    need(all(baselines[k]["deliveries_at_t10"]==8 for k in KEYS) and
         {k:after[k]["deliveries_at_t10"] for k in KEYS}==
           reference["counterfactual_delivered_at_t10"]==
           {KEYS[0]:6,KEYS[1]:8},
         "F4APM_ACTION_EFFECT_NOT_CONFIRMED_BY_DES")
    winner=lambda world:world["apm"]["winner_under_processing_only_proxy"]
    need([winner(baselines[k]) for k in KEYS]==
         ["preparacion","preparacion"] and
         [winner(after[k]) for k in KEYS]==
         ["despacho","preparacion"],
         "F4APM_PROCESSING_PROXY_NOT_EXPECTED_FOR_KNOWN_PAIR")
    return {
        "schema":SCHEMA,
        "phase":"F4_KNOWN_EVALUATOR_DEVELOPMENT_NOT_INDEPENDENT_F5",
        "source_o0_hash":o0["source_snapshot_hash"],
        "source_o1_hash":o1["source_snapshot_hash"],
        "original_symmetry_report_hash":digest(reference),
        "same_O0_O1_public_evidence_for_both_known_worlds":True,
        "all_15_baseline_terminal_timestamps_identical":True,
        "baseline_processing_proxy":{
            k:baselines[k]["apm"] for k in KEYS},
        "after_common_stress_processing_proxy":{
            k:after[k]["apm"] for k in KEYS},
        "baseline_processing_winners":{
            k:winner(baselines[k]) for k in KEYS},
        "stressed_processing_winners":{
            k:winner(after[k]) for k in KEYS},
        "reference_action":ACTION,
        "action_kind":"COMMON_ADVERSE_WORKLOAD_STRESS_NOT_BUSINESS_RECOMMENDATION",
        "same_action_only_dispatch_plus_minutes_exact":str(ACTION_MINUTES),
        "action_operational_feasibility_and_cost":"NOT_ASSESSED",
        "baseline_deliveries_t10":{
            k:baselines[k]["deliveries_at_t10"] for k in KEYS},
        "stressed_deliveries_t10":{
            k:after[k]["deliveries_at_t10"] for k in KEYS},
        "difference_stress_minus_baseline":{
            k:after[k]["deliveries_at_t10"]-
              baselines[k]["deliveries_at_t10"] for k in KEYS},
        "same_synthetic_worlds_as_PR152":True,
        "B2_source":"SYNTHETIC_EVALUATOR_INSTRUMENTATION_NO_INDEPENDENT_SENSOR",
        "B2_no_availability_telemetry":True,
        "active_period_proxy_scope":
            "PROCESSING_ONLY_NOT_FULL_APM_OR_CAUSAL_ORACLE",
        "counterfactual_effects_are_conditional_on_original_DES":True,
        "B2_and_DES_evidence_only_on_evaluator_side":True,
        "not_blind_O0_O1_inference_by_D_B_M":True,
        "not_a_new_fourth_arm":True,
        "no_new_model_family_grid_or_DES_engine":True,
        "A3":"PARTIAL","G4":"NOT_RUN","G5":"NOT_RUN",
        "F5_independent_reserve":"NOT_CREATED",
        "P_PM14":"NOT_TRIGGERED",
        "provider_calls":0,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--o0",type=Path,required=True)
    p.add_argument("--o1",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    need(not args.out.exists(),"F4APM_REFUSE_OVERWRITE")
    o0=json.loads(args.o0.read_text(encoding="utf-8"))
    o1=json.loads(args.o1.read_text(encoding="utf-8"))
    report=build(o0,o1)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_bytes(canonical(report)+b"\n")
    print(json.dumps({
        "baseline_proxy":report["baseline_processing_winners"],
        "stress_proxy":report["stressed_processing_winners"],
        "effects":report["difference_stress_minus_baseline"],
        "G5":report["G5"],
    },sort_keys=True))


if __name__=="__main__":
    main()
