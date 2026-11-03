"""A2/F2: evaluator-only B0/B1/B2 physical controls, never a fourth Arena arm.

The known EV-01 synthetic generator and CAF-01 DES are private evaluator-side
sources. B0 uses POS; B1/B2 require FULL physical instrumentation and an explicit
availability assumption. A sustained 150/h run is a DIFFERENT control from
the fifteen-order EV-01 trace. All counts and durations use Fraction.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path

from scripts.arena_cafe import ev01
from scripts.arena_cafe import diagnosis as operational
from scripts.arena_physical import des_engine as des
from scripts import arena_event_observability as obs
from scripts.arena_v0_contract import canonical, digest

SCHEMA="igc-cafe-f2-b0-b1-b2-physical-controls/0.1"
WINDOW=(Q(0),Q(30))
STRESS_WINDOW=(Q(30),Q(90))
STRESS_END=Q(120)
STRESS_RATE=Q(5,2)
KINDS=frozenset({"etapa_entrada","servicio_inicio","servicio_fin"})
ACTIVE_POLICY={"active_kinds":["PROCESSING"],
               "unobserved_activities":["CLEANING","SETUP","BREAKDOWN","BLOCKING"],
               "do_not_infer_active_from_administrative_timestamp":True}


def need(ok,code):
    if not ok:
        raise ValueError(code)


def _exact(v):
    need(type(v) in (str,int,Q),"F2_BAD_EXACT_TIME")
    try:
        value=Q(v)
    except (ValueError,ZeroDivisionError):
        raise ValueError("F2_BAD_EXACT_TIME") from None
    need(value>=0,"F2_NEGATIVE_TIME")
    return value


def _serialize(q):
    return str(q)


def b0_public(pos,snapshots):
    """Counts and work-in-process only: no stage/service/resource exposure."""
    need(len(pos)==45 and all(
        "stage" not in item and "resource_id" not in item for item in pos),
        "F2_B0_REQUIRES_POS_ONLY")
    rows=[]
    created={r["case_id"]:_exact(r["t_minutes_exact"]) for r in pos
             if r["event_type"]=="pedido_creado"}
    delivered={r["case_id"]:_exact(r["t_minutes_exact"]) for r in pos
               if r["event_type"]=="pedido_entregado"}
    need(len(created)==len(delivered)==15 and set(created)==set(delivered),
         "F2_B0_UNBALANCED_LIFECYCLE")
    for check in snapshots:
        t=_exact(check["time"])
        arrivals=sum(x<=t for x in created.values())
        exits=sum(x<=t for x in delivered.values())
        need((arrivals,exits)==(check["accepted"],check["delivered"]),
             "F2_B0_INDEPENDENT_CHECKPOINT_MISMATCH")
        need(arrivals-exits==check["pending"] and exits<=arrivals,
             "F2_B0_MATERIAL_NOT_CONSERVED")
        rows.append({"time_minutes_exact":str(t),
                     "orders_created_cumulative":arrivals,
                     "delivered_cumulative":exits,
                     "work_in_process_orders":arrivals-exits})
    return {"status":"B0_POS_MATERIAL_BALANCE_PASS","n_orders":15,
            "checkpoints":rows,
            "latent_stages_from_POS":"NOT_IDENTIFIABLE",
            "resource_activity_from_POS":"NOT_OBSERVED"}


def b1_physical(full,stage_servers):
    """Independent original diagnosis on genuinely FULL data, never POS/KDS."""
    need(len(full)==225 and all("source" in x for x in full),
         "F2_B1_FULL_EVENT_INSTRUMENTATION_REQUIRED")
    # original analyze_view rejects incomplete cases, invalid stage order and
    # overlapping resources before any physical reference is constructed.
    validated=obs.analyze_view(full,"FULL",ev01.STAGES)
    report=operational.diagnosis(full,stage_servers)
    need(report["cycle_balances_passed"]==15
         and len(validated["cases"])==15,
         "F2_B1_CASE_STAGE_BALANCE_FAILED")
    stage_counts={}
    for stage in ev01.STAGES:
        intervals=[]
        for r in full:
            if r.get("stage")==stage and r["event_type"] in KINDS:
                intervals.append(r)
        need(len(intervals)==45,"F2_B1_STAGE_EVENT_COUNT_MISMATCH")
        stage_counts[stage]={
            "entrances":sum(x["event_type"]=="etapa_entrada" for x in intervals),
            "starts":sum(x["event_type"]=="servicio_inicio" for x in intervals),
            "completions":sum(x["event_type"]=="servicio_fin" for x in intervals)}
        need(set(stage_counts[stage].values())=={15},"F2_B1_STAGE_MASS_MISMATCH")
    return {"status":"B1_DIRECT_FULL_INSTRUMENTATION_PASS",
            "case_cycle_balances":15,"stage_event_balances":stage_counts,
            "operational_diagnosis":report,
            "evidence_source":"FULL_DIRECT_INSTRUMENTATION_EVALUATOR_ONLY",
            "not_observable_from_POS_or_KDS":True,
            "ranked_waiting_is_not_causal_bottleneck":True}


def aggregate_activity(available_ids,processing_ids,unknown_ids=()):
    """Three-valued physical aggregation; never ALL true for empty available."""
    available_ids=set(available_ids)
    processing_ids=set(processing_ids)
    unknown_ids=set(unknown_ids)
    need(processing_ids.isdisjoint(unknown_ids),
         "F2_RESOURCE_ACTIVE_AND_UNKNOWN_COLLISION")
    if not available_ids and not unknown_ids:
        need(not processing_ids,"F2_RESOURCE_ACTIVITY_WITHOUT_AVAILABILITY")
        return "NO_AVAILABLE_RESOURCES","NO_AVAILABLE_RESOURCES"
    need(processing_ids<=available_ids or
         bool(unknown_ids),"F2_RESOURCE_PROCESSING_NOT_AVAILABLE")
    if unknown_ids:
        any_active=True if processing_ids else "UNKNOWN"
        all_active=False if available_ids-processing_ids-unknown_ids else "UNKNOWN"
        return any_active,all_active
    return bool(processing_ids),len(processing_ids)==len(available_ids)


def resource_periods(full,resources,horizon,*,available=None):
    """B2 continuous [0,horizon) physical periods from exact start/finish IDs.

    available=None means NO availability telemetry; unoccupied => UNKNOWN.
    available={} means explicitly no resources available (not vacuous ALL).
    If available is supplied, each value is a list of half-open windows.
    """
    end=_exact(horizon)
    need(end>0,"F2_RESOURCE_BAD_HORIZON")
    need(type(resources) is dict and resources,
         "F2_RESOURCE_DECLARATION_REQUIRED")
    declared=set()
    for stage,ids in resources.items():
        need(type(stage) is str and type(ids) is list and ids
             and all(type(i) is str and i.startswith(stage+"-r") for i in ids)
             and len(set(ids))==len(ids),"F2_RESOURCE_BAD_DECLARATION")
        need(not declared.intersection(ids),"F2_RESOURCE_MULTISTAGE_ID_COLLISION")
        declared.update(ids)
    if available is not None:
        need(type(available) is dict and set(available)==declared,
             "F2_RESOURCE_AVAILABILITY_INCOMPLETE")
        for rid,windows in available.items():
            need(type(windows) is list,"F2_RESOURCE_AVAILABILITY_BAD_WINDOWS")
            times=[(_exact(a),_exact(b)) for a,b in windows]
            need(all(0<=a<b<=end for a,b in times)
                 and all(b<=c for (_,b),(c,_) in zip(times,times[1:])),
                 "F2_RESOURCE_AVAILABILITY_OVERLAP")
    else:
        times=None
    begins={}
    ends={}
    queue_changes=defaultdict(lambda:defaultdict(int))
    counted=defaultdict(lambda:{"etapa_entrada":0,
                                "servicio_inicio":0,"servicio_fin":0})
    for row in full:
        stage=row.get("stage")
        kind=row.get("event_type")
        if kind not in KINDS:
            continue
        need(stage in resources,"F2_RESOURCE_UNDECLARED_STAGE")
        t=_exact(row["t_minutes_exact"])
        need(t<=end,"F2_RESOURCE_EVENT_AFTER_HORIZON")
        need(row.get("source")=="instrumentacion_fisica",
             "F2_ADMINISTRATIVE_NOT_PHYSICAL_TELEMETRY")
        case=row["case_id"]
        counted[stage][kind]+=1
        if kind=="etapa_entrada":
            queue_changes[stage][t]+=1
        elif kind=="servicio_inicio":
            rid=row.get("resource_id")
            need(rid in resources[stage],"F2_RESOURCE_ID_NOT_FROM_PHYSICAL_SOURCE")
            key=(stage,case)
            need(key not in begins,"F2_RESOURCE_DUPLICATE_START")
            begins[key]=(t,rid)
            queue_changes[stage][t]-=1
        else:
            rid=row.get("resource_id")
            need(rid in resources[stage],"F2_RESOURCE_ID_NOT_FROM_PHYSICAL_SOURCE")
            key=(stage,case)
            need(key not in ends,"F2_RESOURCE_DUPLICATE_FINISH")
            ends[key]=(t,rid)
    need(set(begins)==set(ends) and begins,"F2_RESOURCE_INCOMPLETE_SERVICE_INTERVAL")
    busy=defaultdict(list)
    all_times={Q(0),end}
    for key,(t,rid) in begins.items():
        stop,finish_rid=ends[key]
        need(finish_rid==rid and t<stop,"F2_RESOURCE_MISMATCHED_INTERVAL")
        busy[rid].append((t,stop,key[1]))
        all_times.update((t,stop))
    for rid in declared:
        intervals=sorted(busy[rid])
        need(all(b<=c for (a,b,_),(c,d,_) in zip(intervals,intervals[1:])),
             "F2_RESOURCE_OVERLAPPED_SERVICES")
    for stage,changes in queue_changes.items():
        n=0
        for t in sorted(changes):
            n+=changes[t]
            need(n>=0,"F2_RESOURCE_NEGATIVE_QUEUE")
            all_times.add(t)
        need(n==0,"F2_RESOURCE_UNDRAINED_QUEUE")
    for stage in resources:
        need(set(counted[stage].values())=={15},
             "F2_RESOURCE_STAGE_INCOMPLETE")
    if available is not None:
        for windows in available.values():
            for a,b in windows:
                all_times.update((_exact(a),_exact(b)))
    time_grid=sorted(all_times)
    per_resource={rid:defaultdict(lambda:Q(0)) for rid in declared}
    segments=[]
    status_durations=defaultdict(lambda:defaultdict(lambda:Q(0)))
    for left,right in zip(time_grid,time_grid[1:]):
        if left==right:continue
        duration=right-left
        rows={"start_minutes_exact":str(left),"end_minutes_exact":str(right),
              "by_stage":{}}
        for stage,ids in resources.items():
            waiting=sum(change for t,change in queue_changes[stage].items()
                        if t<=left)
            need(waiting>=0,"F2_RESOURCE_NEGATIVE_QUEUE")
            processing={rid for rid in ids if any(
                a<=left<b for a,b,_ in busy[rid])}
            # Availability is explicit: an uninstrumented server must not
            # automatically become IDLE_AVAILABLE or STARVED.
            stage_states={}
            available_ids=set()
            unknown_ids=set()
            for rid in ids:
                if available is None:
                    state="PROCESSING" if rid in processing else "UNKNOWN"
                    if rid in processing:
                        # An observed physical service proves this resource
                        # was available DURING service, not that idle peers
                        # were available throughout the window.
                        available_ids.add(rid)
                    else:
                        unknown_ids.add(rid)
                else:
                    avail=any(_exact(a)<=left<_exact(b) for a,b in available[rid])
                    if rid in processing:
                        need(avail,"F2_RESOURCE_PROCESSING_WHILE_UNAVAILABLE")
                    if not avail:
                        state="NOT_AVAILABLE"
                    else:
                        available_ids.add(rid)
                        if rid in processing:
                            state="PROCESSING"
                        elif waiting==0:
                            state="STARVED"
                        else:
                            state="IDLE_AVAILABLE"
                stage_states[rid]=state
                per_resource[rid][state]+=duration
            any_state,all_state=aggregate_activity(
                available_ids,processing,unknown_ids)
            status_durations[stage][str(all_state)]+=duration
            rows["by_stage"][stage]={
                "waiting_orders":waiting,
                "available_resources":len(available_ids) if available is not None else None,
                "processing_resources":len(processing),
                "resource_states":stage_states,
                "ANY_ACTIVE":any_state,"ALL_ACTIVE":all_state,
                "aggregate_is_descriptive_not_causal_bottleneck":True}
        segments.append(rows)
    for rid,states in per_resource.items():
        need(sum(states.values(),Q(0))==end,"F2_RESOURCE_GAP_IN_COVERAGE")
    return {"status":"B2_EXACT_RESOURCE_PERIODS_PASS",
            "time_window":"[0,horizon)",
            "horizon_minutes_exact":str(end),
            "availability_source":("DECLARED_SYNTHETIC_24_7_OR_WINDOWS" if
                                   available is not None else "NO_AVAILABILITY_TELEMETRY"),
            "ACTIVE_definition":ACTIVE_POLICY,
            "resource_total_minutes":{rid:{k:str(v) for k,v in sorted(states.items())}
                                      for rid,states in sorted(per_resource.items())},
            "ALL_ACTIVE_duration_minutes_by_stage":{
                stage:dict(sorted((status,str(minutes)) for status,minutes in d.items()))
                for stage,d in sorted(status_durations.items())},
            "segments":segments,
            "unseen_activities_not_inferred":True,
            "no_finite_buffer_or_blocked_after_service_in_original_DES":True,
            "bottleneck_causal_discovery":"NOT_ESTABLISHED"}


def ceiling(config):
    spec=des.validate_private_config(config)
    return min(n*Q(60)/t for n,t in spec)


def sustained():
    """New separate synthetic 150/h, [30,90] control; NO EV-01 outcome reuse."""
    base=ev01.config()
    proposals={
        "base":{},
        "plus_one_preparation":{1:1},
        "plus_one_cashier":{0:1},
        "plus_one_preparation_and_dispatch":{1:1,2:1}}
    expected={"base":Q(68),"plus_one_preparation":Q(86),
              "plus_one_cashier":Q(68),
              "plus_one_preparation_and_dispatch":Q(120)}
    arrivals=des.half_open_arrivals(str(STRESS_RATE),str(STRESS_END))
    need(len(arrivals)==300,"F2_SUSTAINED_DEMAND_DRIFT")
    observations=(Q(0),*STRESS_WINDOW,STRESS_END)
    scenarios={}
    for name,changes in proposals.items():
        config={**base,"stages":[dict(x) for x in base["stages"]]}
        for index,extra in changes.items():
            config["stages"][index]["servers"]+=extra
        cap=ceiling(config)
        need(cap==expected[name],"F2_WRONG_ANALYTIC_CEILING")
        snap=des.run_toy_engine(config,arrivals,observations)
        before,after=snap[1],snap[2]
        new_entries=after.accepted_cum_orders-before.accepted_cum_orders
        exits=after.delivered_cum_orders-before.delivered_cum_orders
        need(before.pending_orders+new_entries-exits==after.pending_orders,
             "F2_SUSTAINED_MASS_BALANCE")
        theoretical=cap*(STRESS_WINDOW[1]-STRESS_WINDOW[0])/60
        scenarios[name]={
            "servers_by_stage":[x["servers"] for x in config["stages"]],
            "analytic_ceiling_orders_per_hour_exact":str(cap),
            "t0_minutes_exact":str(STRESS_WINDOW[0]),
            "t1_minutes_exact":str(STRESS_WINDOW[1]),
            "counter_interval":"(t0,t1]",
            "initial_pending_at_t0":before.pending_orders,
            "new_arrivals_in_interval":new_entries,
            "delivered_in_interval":exits,
            "pending_at_t1":after.pending_orders,
            "nominal_ceiling_orders_over_interval_exact":str(theoretical),
            "finite_window_count_minus_nominal_ceiling_exact":str(Q(exits)-theoretical),
            "finite_difference_is_phase_and_transient_sensitive":True,
            "demand_exceeds_ceiling":STRESS_RATE*60>cap,
            "stable_stationary_WIP_claim":False}
    return {"status":"F2_SEPARATE_SUSTAINED_CONTROL_COMPLETED",
            "demand_orders_per_hour_exact":str(STRESS_RATE*60),
            "arrival_window":"[0,120) minutes, 300 NEW synthetic orders",
            "measurement_window":"(30,90] minutes",
            "tie_policy":des.TIE_POLICY,
            "initial_conditions":"EMPTY_SYSTEM_AT_T0_ZERO; NONZERO_WIP_AT_30",
            "phase_tolerance":"FINITE_CEILING_RESIDUAL_REPORTED_NO_EXACT_EQUALITY_ASSUMED",
            "counterfactual_measured_costs":"NOT_AVAILABLE",
            "workstation_space_inventory_feasibility":"NOT_ASSESSED",
            "scenarios":scenarios}


def build():
    raw,snapshots=ev01.trace_generator()
    native_parity=ev01.verify_des_parity(snapshots)
    views={name:obs.project_events(raw,name) for name in obs.VIEWS}
    need({name:len(v) for name,v in views.items()}==
         {"POS":45,"POS_KDS":75,"FULL":225},
         "F2_VIEW_EVENT_COUNTS")
    declared={stage:[f"{stage}-r{i+1}" for i in range(n)]
              for stage,(n,_) in zip(ev01.STAGES,ev01.SPEC)}
    observed_resources={r["resource_id"] for r in views["FULL"]
                        if r["event_type"]=="servicio_inicio"}
    need(observed_resources<=set(x for values in declared.values() for x in values),
         "F2_RESOURCE_IDS_NOT_EVALUATOR_EV01")
    known_available={rid:[("0","30")] for ids in declared.values() for rid in ids}
    b0=b0_public(views["POS"],snapshots)
    b1=b1_physical(views["FULL"],{s:n for s,(n,_) in zip(ev01.STAGES,ev01.SPEC)})
    b2=resource_periods(views["FULL"],declared,"30",available=known_available)
    stress=sustained()
    return {"schema":SCHEMA,"case":"EV01_KNOWN_SYNTHETIC_CONTROL",
            "regression":{"n_orders":15,"events_POS":45,
                          "events_POS_KDS":75,"events_FULL":225,
                          "independent_DES_parity":native_parity["status"],
                          "checkpoints":len(snapshots)},
            "B0":b0,"B1":b1,"B2":b2,
            "separate_sustained_control":stress,
            "data_access":"EVALUATOR_SIDE_FULL_NEVER_TO_O0_O1_PRODUCERS",
            "new_engine_implemented":False,
            "causal_bottleneck_discovery":"NOT_ESTABLISHED",
            "real_business_validated":False,
            "RESOURCE-01":"ENGINEERING_ONLY",
            "F2":"ENGINEERING_CONTROL_NOT_SCIENTIFIC_IDENTIFICATION"}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    need(not a.out.exists(),"F2_REFUSE_OVERWRITE")
    result=build()
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_bytes(canonical(result)+b"\n")
    print(json.dumps({"status":result["F2"],
                      "ev01_orders":result["regression"]["n_orders"],
                      "sustained_arrivals":300,
                      "ceilings":{k:v["analytic_ceiling_orders_per_hour_exact"]
                                  for k,v in result["separate_sustained_control"]["scenarios"].items()}}))


if __name__=="__main__":
    main()
