"""Pilot-only physical event ingestion for F5 instrumentation readiness.

This is an *evaluator-side* generic, finite-event checker, not a simulator,
parameter fit, new mining engine, or sensor-error calibration algorithm.
It reads events as provided, never creates missing service timestamps.

A complete, same-clock start/end pair can establish elapsed service time.
Events from different clocks are NOT silently aligned. Paired external
timestamps are merely observed differences, NEVER an accuracy bound.

Pilot reports are not fed into O0/O1 producer jobs. Synthetic test fixtures
do not establish real-world sensor precision or empirical causal validity.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import re

from scripts.arena_v0_contract import canonical

SCHEMA="igc-arena-cafe-instrumented-pilot-capture/0.1"
EVENT_FIELDS=("event_id","case_id","visit_id","event_type","stage",
              "resource_id","t_minutes_exact","source","clock_id","sensor_id")
PAIR_FIELDS=("pair_id","primary_event_id","secondary_sensor_id",
             "secondary_clock_id","secondary_t_minutes_exact")
POS={"pedido_creado","pago_confirmado","pedido_entregado"}
PHYSICAL={"etapa_entrada","servicio_inicio","servicio_fin"}
VISIT_ORDER=("etapa_entrada","servicio_inicio","servicio_fin")
TOKEN=re.compile(r"[a-zA-Z0-9_-]{1,96}\Z")


def need(test,code):
    if not test:
        raise ValueError(code)


def exact(value):
    need(type(value) in (str,int,Q),"PILOT_EXACT_STRING_REQUIRED")
    try:
        x=Q(value)
    except (ValueError,ZeroDivisionError):
        raise ValueError("PILOT_BAD_EXACT_TIME") from None
    need(x>=0,"PILOT_NEGATIVE_TIME")
    return x


def _token(s):
    return type(s) is str and TOKEN.fullmatch(s) is not None


def read_rows(path,fields):
    """CSV must be a strict, lossless projection of recorded event fields."""
    with Path(path).open(encoding="utf-8",newline="") as stream:
        reader=csv.DictReader(stream)
        need(tuple(reader.fieldnames or ())==fields,
             "PILOT_CSV_HEADERS_NOT_EXACT")
        rows=list(reader)
    need(all(set(row)==set(fields) and all(
        type(v) is str for v in row.values()) for row in rows),
         "PILOT_CSV_MALFORMED_ROW")
    return rows


def build(events,*,cutoff_minutes_exact,source_context,pairs=()):
    """Events must already be visibly truncated to [0,cutoff).

    This contract refuses post-cutoff events rather than accidentally
    incorporating future knowledge into censoring or availability.
    """
    need(source_context in ("synthetic_fixture","real_pilot_declared"),
         "PILOT_UNDECLARED_ORIGIN")
    cutoff=exact(cutoff_minutes_exact)
    need(cutoff>0 and type(events) in (tuple,list) and events,
         "PILOT_EMPTY_OR_INVALID_CUTOFF")
    need(type(pairs) in (tuple,list),"PILOT_PAIR_INPUT_INVALID")
    parsed={}
    visits=defaultdict(dict)
    cases=defaultdict(dict)
    clock_set=set()
    for row in events:
        need(type(row) is dict and set(row)==set(EVENT_FIELDS),
             "PILOT_EVENT_SCHEMA")
        for key in ("event_id","case_id","clock_id","sensor_id"):
            need(_token(row[key]),"PILOT_PSEUDONYM_OR_INSTRUMENT_ID_INVALID")
        event_id=row["event_id"]
        need(event_id not in parsed,"PILOT_DUPLICATE_EVENT_ID")
        t=exact(row["t_minutes_exact"])
        need(t<cutoff,"PILOT_OUTSIDE_CUTOFF_FUTURE_OR_BOUNDARY")
        kind=row["event_type"]
        need(kind in POS|PHYSICAL,"PILOT_UNKNOWN_EVENT_TYPE")
        if kind in POS:
            need(row["source"]=="pos" and
                 row["visit_id"]==row["stage"]==row["resource_id"]=="",
                 "PILOT_POS_CANNOT_FAKE_STAGE_OR_RESOURCE")
            need(kind not in cases[row["case_id"]],
                 "PILOT_POS_DUPLICATE_LIFECYCLE_EVENT")
            cases[row["case_id"]][kind]=(t,row["clock_id"],event_id)
        else:
            need(row["source"]=="instrumentacion_fisica" and
                 _token(row["visit_id"]) and _token(row["stage"]),
                 "PILOT_ONLY_DIRECT_PHYSICAL_STAGE_EVENTS")
            need((row["resource_id"]=="" if kind=="etapa_entrada" else
                  _token(row["resource_id"])),
                 "PILOT_PHYSICAL_RESOURCE_REQUIRED_ON_SERVICE")
            key=(row["case_id"],row["visit_id"])
            previous=visits[key]
            need(kind not in previous,"PILOT_DUPLICATE_VISIT_BOUNDARY")
            if previous:
                need(all(row["stage"]==v["stage"] for v in previous.values()),
                     "PILOT_VISIT_CHANGED_STAGE")
            previous[kind]=dict(row)
        clock_set.add(row["clock_id"])
        parsed[event_id]=(dict(row),t)
    need(bool(cases),"PILOT_POS_SOURCE_REQUIRED")
    for case,events_of_case in cases.items():
        need("pedido_creado" in events_of_case,
             "PILOT_DELIVERY_OR_PAYMENT_WITHOUT_CREATION")
        if "pedido_entregado" in events_of_case:
            created=events_of_case["pedido_creado"]
            delivered=events_of_case["pedido_entregado"]
            if created[1]==delivered[1]:
                need(created[0]<=delivered[0],
                     "PILOT_DELIVERED_BEFORE_CREATED")
        if "pago_confirmado" in events_of_case:
            pay=events_of_case["pago_confirmado"]
            created=events_of_case["pedido_creado"]
            if created[1]==pay[1]:
                need(created[0]<=pay[0],
                     "PILOT_PAID_BEFORE_CREATED")
    for (case,_),record in visits.items():
        need(case in cases,"PILOT_STAGE_WITHOUT_POS_CREATED_CASE")
        sequence=tuple(kind for kind in VISIT_ORDER if kind in record)
        need(sequence in (
            ("etapa_entrada",),
            ("etapa_entrada","servicio_inicio"),
            ("etapa_entrada","servicio_inicio","servicio_fin")),
            "PILOT_INCOMPLETE_VISIT_INVALID_BOUNDARIES")
        clocks={row["clock_id"] for row in record.values()}
        # Time ordering across independently clocked devices has not been
        # established; neither physical waiting time nor service mean follows.
        if len(clocks)==1:
            timestamps=[exact(record[k]["t_minutes_exact"]) for k in sequence]
            need(all(a<=b for a,b in zip(timestamps,timestamps[1:])),
                 "PILOT_NONMONOTONIC_PHYSICAL_VISIT")
            if "servicio_fin" in record:
                need(timestamps[-1]>timestamps[-2],
                     "PILOT_NONPOSITIVE_SERVICE_TIME")
        if "servicio_fin" in record:
            need(record["servicio_inicio"]["resource_id"]==
                 record["servicio_fin"]["resource_id"],
                 "PILOT_SERVICE_RESOURCE_SWITCH_WITHOUT_TRANSFER_EVENT")
    # A resource may not service two orders concurrently if both physical
    # service boundaries share a clock. No claims about unlogged availability.
    by_resource=defaultdict(list)
    for (case,visit_id),rows in visits.items():
        if "servicio_fin" not in rows:
            continue
        start,end=rows["servicio_inicio"],rows["servicio_fin"]
        if start["clock_id"]!=end["clock_id"]:
            continue
        by_resource[(start["clock_id"],start["resource_id"])].append(
            (exact(start["t_minutes_exact"]),
             exact(end["t_minutes_exact"]),case,visit_id))
    for intervals in by_resource.values():
        ordered=sorted(intervals)
        need(all(left[1]<=right[0] for left,right in
                 zip(ordered,ordered[1:])),
             "PILOT_OVERLAPPING_SERVICE_ON_ONE_RESOURCE")
    pair_seen=set()
    deltas=[]
    pair_clocks=set()
    for pair in pairs:
        need(type(pair) is dict and set(pair)==set(PAIR_FIELDS),
             "PILOT_PAIRED_EVIDENCE_SCHEMA")
        for field in ("pair_id","primary_event_id",
                      "secondary_sensor_id","secondary_clock_id"):
            need(_token(pair[field]),"PILOT_PAIR_ID_INVALID")
        need(pair["pair_id"] not in pair_seen,
             "PILOT_DUPLICATE_PAIR")
        pair_seen.add(pair["pair_id"])
        need(pair["primary_event_id"] in parsed,
             "PILOT_SECONDARY_NOT_BOUND_TO_RECORDED_PRIMARY_EVENT")
        primary,t=parsed[pair["primary_event_id"]]
        need(primary["sensor_id"]!=pair["secondary_sensor_id"],
             "PILOT_SAME_SENSOR_NOT_INDEPENDENT_DUPLICATE")
        secondary=exact(pair["secondary_t_minutes_exact"])
        need(secondary<cutoff,"PILOT_SECONDARY_AFTER_CUTOFF")
        deltas.append(abs(t-secondary))
        pair_clocks.add((primary["clock_id"],pair["secondary_clock_id"]))
    same_clock=len(clock_set)==1
    measures={}
    paths=defaultdict(list)
    for (case,visit_id),events_by_kind in visits.items():
        start=events_by_kind["etapa_entrada"]
        paths[case].append(
            (exact(start["t_minutes_exact"]),visit_id,start["stage"]))
    # A route is observed *entry-event succession*, not causal structure.
    path_counts=Counter(
        tuple(stage for _,_,stage in sorted(path))
        for path in paths.values()
    )
    # All observations are in a common clock only in this branch.
    # A source's self-declaration of clock ID is NOT a metrological certificate.
    if same_clock:
        stages=sorted({r["stage"] for r in
                       events if r["event_type"] in PHYSICAL})
        for stage in stages:
            stage_rows=[r for v in visits.values() for r in [v] if
                        r["etapa_entrada"]["stage"]==stage]
            completed=[v for v in stage_rows if "servicio_fin" in v]
            starts=[v for v in stage_rows if "servicio_inicio" in v]
            service=[exact(v["servicio_fin"]["t_minutes_exact"])-
                     exact(v["servicio_inicio"]["t_minutes_exact"])
                     for v in completed]
            waits=[exact(v["servicio_inicio"]["t_minutes_exact"])-
                   exact(v["etapa_entrada"]["t_minutes_exact"])
                   for v in completed]
            measures[stage]={
                "entered_visits":len(stage_rows),
                "started_services":len(starts),
                "completed_services_pre_cutoff":len(completed),
                "censored_waiting_at_cutoff":len(stage_rows)-len(starts),
                "censored_in_service_at_cutoff":len(starts)-len(completed),
                "mean_service_minutes_exact":
                    str(sum(service,Q(0))/len(service)) if service else None,
                "mean_wait_of_completed_minutes_exact":
                    str(sum(waits,Q(0))/len(waits)) if waits else None,
                "selection":"ONLY_SERVICES_COMPLETED_BEFORE_CUTOFF",
                "same_declared_clock_is_not_verified_accuracy":True,
            }
    n_created=sum("pedido_creado" in r for r in cases.values())
    n_delivered=sum("pedido_entregado" in r for r in cases.values())
    need(n_delivered<=n_created,"PILOT_MORE_DELIVERIES_THAN_CREATIONS")
    return {
        "schema":SCHEMA,
        "source_context_declared_not_independently_verified":source_context,
        "time_window":"[0,cutoff)",
        "cutoff_minutes_exact":str(cutoff),
        "input_event_count":len(events),
        "n_cases_created":n_created,
        "n_delivered_pre_cutoff":n_delivered,
        "n_observed_stage_visits":len(visits),
        "n_distinct_event_clocks":len(clock_set),
        "cross_clock_alignment":"SINGLE_DECLARED_CLOCK_UNVERIFIED"
            if same_clock else "MULTI_CLOCK_ALIGNMENT_NOT_ESTABLISHED",
        "stage_aggregates_status":"DESCRIPTIVE_SAME_DECLARED_CLOCK_ONLY"
            if same_clock and measures else
            "WITHHELD_NO_SHARED_CLOCK_OR_PHYSICAL_EVENTS",
        "stage_completed_only_descriptives":measures,
        "observed_entry_route_variants":{
            "n_variants":len(path_counts),
            "counts":[{"observed_route":list(path),"cases":count}
                      for path,count in sorted(path_counts.items())],
            "not_a_process_causal_discovery":True,
        },
        "paired_observation_status":(
            "PAIRED_RAW_DIFFERENCES_NOT_ERROR_BOUNDS" if deltas
            else "NO_INDEPENDENT_PAIRED_OBSERVATIONS"),
        "paired_observation_count":len(deltas),
        "paired_max_abs_delta_minutes_exact":
            str(max(deltas)) if deltas else None,
        "paired_clock_combinations":len(pair_clocks),
        "paired_differences_cannot_establish_individual_sensor_accuracy":True,
        "physical_clock_accuracy_known":False,
        "clock_resolution_known":False,
        "event_dropout_rate_estimated":False,
        "representative_service_variability_inferred":False,
        "instrumental_error_calibrated":False,
        "empirical_compatibility_tolerance":None,
        "F5_pilot_capture_status":"ENGINEERING_INGEST_ONLY_NOT_CALIBRATION",
        "A3":"PARTIAL","G4":"NOT_RUN","G5":"NOT_RUN",
        "PM_incremental_beyond_B1_B2":"NOT_ASSESSED",
        "no_parameter_grid_or_new_model_or_pm":True,
        "no_provider_calls":True,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--events",type=Path,required=True)
    p.add_argument("--pairs",type=Path)
    p.add_argument("--cutoff",required=True)
    p.add_argument("--source-context",required=True,
                   choices=("synthetic_fixture","real_pilot_declared"))
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    need(not args.out.exists(),"PILOT_REFUSE_OVERWRITE")
    events=read_rows(args.events,EVENT_FIELDS)
    pairs=read_rows(args.pairs,PAIR_FIELDS) if args.pairs else []
    report=build(events,cutoff_minutes_exact=args.cutoff,
                 source_context=args.source_context,pairs=pairs)
    report["input_events_file_sha256"]="sha256:"+hashlib.sha256(
        args.events.read_bytes()).hexdigest()
    report["input_pairs_file_sha256"]=(
        "sha256:"+hashlib.sha256(args.pairs.read_bytes()).hexdigest()
        if args.pairs else None)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_bytes(canonical(report)+b"\n")
    print(json.dumps({
        "status":report["F5_pilot_capture_status"],
        "stage_aggregates":report["stage_aggregates_status"],
        "instrument_error_calibrated":report["instrumental_error_calibrated"],
        "A3":report["A3"],"G4":report["G4"],"G5":report["G5"],
    },sort_keys=True))


if __name__=="__main__":
    main()
