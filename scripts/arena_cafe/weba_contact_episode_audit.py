"""WEBA T110 physical contact intervals, not inferred order-processing tasks.

Retrospective observational E1 primitive: paired Open -> Close for five
fridge/freezer/cake-display door-contact sensors. One front-door sensor is
shown separately as a non-customer-count control. Tapo KeepOpen is an
observation of the still-open contact, not a new opening or a closure.

All data belong to the already disclosed 20240223, 20240304, 20240308
WEBA shift snapshots and are validated against their original git blobs.
This module neither imputes missing closes, nor infers item retrieval,
coffee prep, barista service, customer arrival, or completion of orders.

The recorded pairs are internally consistent only: missing underlying
Tapo triggers, sensor failure, true contact status or inter-device clocks
have NOT been independently validated. No rate/uptime estimation.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
from statistics import median

from scripts.arena_cafe import weba_instrument_integrity as source_audit
from scripts.arena_cafe import weba_source_readiness as tapo
from scripts.arena_v0_contract import canonical

SCHEMA="igc-weba-t110-contact-observed-pairs/0.1"
CONTACT_CATEGORIES={
    "r_wing_fridge":"STORAGE_FRIDGE",
    "l_wing_fridge":"STORAGE_FRIDGE",
    "freezer":"STORAGE_FREEZER",
    "r_door_cake_display":"STORAGE_CAKE_DISPLAY",
    "l_door_cake_display":"STORAGE_CAKE_DISPLAY",
    "front_door":"ENTRANCE_CONTACT_NON_CUSTOMER_COUNT_CONTROL",
}
STORAGE=tuple(k for k,v in CONTACT_CATEGORIES.items()
              if v!="ENTRANCE_CONTACT_NON_CUSTOMER_COUNT_CONTROL")
ENTRANCE="front_door"
UTC=timezone.utc


def need(ok,tag):
    if not ok:
        raise ValueError(tag)


def contact_events(text):
    """Parse only T110 device names documented in real WEBA setup."""
    audit=tapo.parse_tapo_text(text)
    found={}
    for block in tapo.TAPO_SENSOR_RE.finditer(text):
        model,name,_,stated,raw=block.groups()
        if name not in CONTACT_CATEGORIES:
            continue
        need(model=="T110","WEBA_CONTACT_SENSOR_MODEL_NOT_T110")
        events=[(match.group(1),int(match.group(3)))
                for match in tapo.TAPO_EVENT_RE.finditer(raw)]
        need(all(kind in ("Open","Close","KeepOpen")
                 for kind,_ in events),
             "WEBA_CONTACT_NON_CONTACT_TRIGGER")
        need(int(stated)==len(events),
             "WEBA_CONTACT_TAPO_RESPONSE_COUNT_DIFFERENT")
        need(name not in found,"WEBA_CONTACT_DUPLICATED_DEVICE")
        found[name]=list(reversed(events))
        need(all(a[1]<=b[1] for a,b in zip(
                 found[name],found[name][1:])),
             "WEBA_CONTACT_NOT_CHRONOLOGICAL")
    need(set(found)==set(CONTACT_CATEGORIES),
         "WEBA_CONTACT_INCOMPLETE_SIX_T110_SENSORS")
    need(audit["sensor_count"]==10,
         "WEBA_CONTACT_TOTAL_SOURCE_SENSOR_GROUPS_NOT_TEN")
    return found


def reconstruct(records):
    """Locally defensible paired contact state, never impute missing events.

    An initial Close may be left-censored. An unmatched final Open may be
    right-censored. In both cases DO NOT assign a duration. Unexpected nested
    Open or impossible timestamp order is rejected, not repaired.
    """
    opened=None
    completed=[]
    type_counts=Counter()
    orphan_closes=0
    orphan_keepopen=0
    keeps_inside=0
    for kind,epoch in records:
        need(kind in ("Open","Close","KeepOpen") and type(epoch) is int
             and epoch>=0,"WEBA_CONTACT_INVALID_SOURCE_EVENT")
        type_counts[kind]+=1
        if kind=="Open":
            need(opened is None,"WEBA_CONTACT_NESTED_OPEN_WITHOUT_CLOSE")
            opened=epoch
        elif kind=="Close":
            if opened is None:
                orphan_closes+=1
            else:
                need(epoch>opened,"WEBA_CONTACT_CLOSURE_NOT_AFTER_OPEN")
                completed.append((opened,epoch))
                opened=None
        else:
            if opened is None:
                orphan_keepopen+=1
            else:
                need(epoch>=opened,"WEBA_CONTACT_KEEP_OPEN_BEFORE_OPEN")
                keeps_inside+=1
    return {
        "paired_intervals":completed,
        "event_types":dict(sorted(type_counts.items())),
        "orphan_closes_no_start_known":orphan_closes,
        "orphan_keepopen_without_known_open":orphan_keepopen,
        "keepopen_while_known_open":keeps_inside,
        "unclosed_open_at_snapshot_end":int(opened is not None),
        "unclosed_open_timestamp_internal_only":opened,
        "pair_count":len(completed),
    }


def classify_pair(pair,start,end,export):
    opening,closing=pair
    need(closing>opening and closing<=int(export.timestamp()),
         "WEBA_CONTACT_PAIR_LATER_THAN_EXPORT")
    start_s=int(start.timestamp())
    end_s=int(end.timestamp())
    if closing<=start_s:
        return "BEFORE_SHIFT"
    if opening>=end_s:
        return "AFTER_SHIFT"
    if opening<start_s and closing>=end_s:
        return "SPANS_BOTH_SHIFT_BOUNDARIES"
    if opening<start_s:
        return "CROSSES_SHIFT_START"
    if closing>=end_s:
        return "CROSSES_SHIFT_END"
    return "COMPLETE_WITHIN_DECLARED_SHIFT"


def run_for_shift(name,bounds,source_text):
    start,end=(datetime.fromisoformat(x)
               for x in bounds[
                   "UTC_boundaries_under_UNVERIFIED_local_clock_assumption"])
    export=datetime.fromisoformat(bounds["Tapo"][
        "Tapo_snapshot_time_utc_last"])
    need(start.tzinfo is not None and end.tzinfo is not None
         and export.tzinfo is not None and start<end,
         "WEBA_CONTACT_SHIFT_OR_EXPORT_NOT_VALID")
    records=contact_events(source_text)
    sensor_reports={}
    for nickname,rec in records.items():
        reconstructed=reconstruct(rec)
        categories=Counter(classify_pair(pair,start,end,export)
                           for pair in reconstructed["paired_intervals"])
        complete=[b-a for a,b in reconstructed["paired_intervals"]
                  if classify_pair((a,b),start,end,export)==
                  "COMPLETE_WITHIN_DECLARED_SHIFT"]
        need(sum(categories.values())==reconstructed["pair_count"],
             "WEBA_CONTACT_PAIRS_DISAPPEARED")
        report={
            "sensor_function":nickname,
            "contact_primitive_type":CONTACT_CATEGORIES[nickname],
            "raw_reported_record_count":len(rec),
            "type_counts":reconstructed["event_types"],
            "paired_contact_open_close_intervals_in_snapshot":
                reconstructed["pair_count"],
            "paired_contact_intervals_by_shift_boundary":
                {key:categories.get(key,0) for key in (
                    "BEFORE_SHIFT","COMPLETE_WITHIN_DECLARED_SHIFT",
                    "AFTER_SHIFT","CROSSES_SHIFT_START",
                    "CROSSES_SHIFT_END","SPANS_BOTH_SHIFT_BOUNDARIES")},
            "observed_in_shift_complete_pairs":len(complete),
            "paired_contact_open_seconds_sum_IN_SHIFT_not_workload":
                sum(complete),
            "paired_contact_open_seconds_median_IN_SHIFT_not_service":
                median(complete) if complete else None,
            "paired_contact_open_seconds_max_IN_SHIFT_not_service":
                max(complete) if complete else None,
            "KeepOpen_while_open_retained_NOT_another_open":
                reconstructed["keepopen_while_known_open"],
            "KeepOpen_without_matched_Open":
                reconstructed["orphan_keepopen_without_known_open"],
            "Close_without_matched_Open":
                reconstructed["orphan_closes_no_start_known"],
            "Open_without_matched_Close_snapshot_right_censored":
                reconstructed["unclosed_open_at_snapshot_end"],
            "snapshot_empty_NOT_proof_of_no_real_openings":True,
            "pair_duration_is_contact_state_NOT_task_time":True,
            "pair_is_not_linked_to_order_or_material_retrieval":True,
        }
        need(2*report["paired_contact_open_close_intervals_in_snapshot"]+
             report["Close_without_matched_Open"]+
             report["Open_without_matched_Close_snapshot_right_censored"]+
             report["KeepOpen_while_open_retained_NOT_another_open"]+
             report["KeepOpen_without_matched_Open"] ==
             report["raw_reported_record_count"],
             "WEBA_CONTACT_SOURCE_EVENT_MASS_NOT_CONSERVED")
        sensor_reports[nickname]=report
    storage_summary={
        "five_storage_contact_sensors":list(STORAGE),
        "paired_storage_contact_intervals_in_snapshot":
            sum(sensor_reports[n][
                "paired_contact_open_close_intervals_in_snapshot"]
                for n in STORAGE),
        "paired_storage_contact_intervals_COMPLETE_WITHIN_shift":
            sum(sensor_reports[n][
                "paired_contact_intervals_by_shift_boundary"][
                    "COMPLETE_WITHIN_DECLARED_SHIFT"]
                for n in STORAGE),
        "paired_storage_contact_intervals_BEFORE_shift":
            sum(sensor_reports[n][
                "paired_contact_intervals_by_shift_boundary"][
                    "BEFORE_SHIFT"]
                for n in STORAGE),
        "paired_storage_contact_intervals_AFTER_shift":
            sum(sensor_reports[n][
                "paired_contact_intervals_by_shift_boundary"][
                    "AFTER_SHIFT"]
                for n in STORAGE),
        "storage_contact_open_without_matched_close":
            sum(sensor_reports[n][
                "Open_without_matched_Close_snapshot_right_censored"]
                for n in STORAGE),
        "storage_contact_KeepOpen_total_not_new_openings":
            sum(sensor_reports[n]["type_counts"].get("KeepOpen",0)
                for n in STORAGE),
        "storage_contact_is_not_identified_operator_task":True,
        "storage_contact_intervals_can_overlap_across_doors":True,
        "not_a_full_shift_denominator_or_operator_utilization":True,
    }
    entrance=sensor_reports[ENTRANCE]
    return {
        "shift":name,
        "source_declared_shift_start_and_end_UTC_conditional":
            [start.isoformat(),end.isoformat()],
        "last_Tapo_dump_UTC":export.isoformat(),
        "snapshot_ends_before_declared_shift_end":export<end,
        "source_Tapo_raw_records_all_sensors":
            bounds["Tapo"]["total_events_in_snapshot"],
        "sensor_contact_event_ledger":sensor_reports,
        "storage_contact_summary":storage_summary,
        "front_door_control_pairs_complete_within_shift":
            entrance["observed_in_shift_complete_pairs"],
        "front_door_open_close_is_not_one_customer":True,
        "storage_door_open_close_is_not_one_prepared_drink":True,
        "sensor_status_and_coverage_independently_validated":False,
        "POS_order_ID_to_contact_event_link_validated":False,
        "time_zone_and_POS_Tapo_sync_independently_validated":False,
        "physical_contact_event_confirmed_from_T110_recorded_semantics":True,
        "human_task_instance_or_completion_confirmed":False,
    }


def build(pos,shift_summary,logs):
    source_result=source_audit.build(pos,shift_summary,logs)
    by_shift={}
    for shift in source_audit.SHIFTS:
        by_shift[shift]=run_for_shift(
            shift,source_result["shifts"][shift],
            logs[shift].decode("utf-8"))
    return {
        "schema":SCHEMA,
        "scientific_context":"WEBA_EXTERNAL_REAL_REPEATED_SOURCE_RETROSPECTIVE",
        "data_source_upstream_git_commit":
            source_result["upstream_git_commit"],
        "pinned_source_file_digests":source_result["source_file_digests"],
        "shifts_previously_explored_not_blind":list(source_audit.SHIFTS),
        "primary_observable_type":
            "T110_DOOR_CONTACT_OPEN_CLOSE_EVENT_FROM_LOG",
        "task_inference_gate":
            "NO_UNIQUE_OPERATOR_TASK_OR_ORDER_COMPLETION_OBSERVED",
        "machine_vibration_data_ingested":False,
        "machine_vibration_cycle_or_drink_type_inferred":False,
        "fixed_setup_is_one_worker_shared_across_tasks":True,
        "Tapo_continuity_established":False,
        "POS_and_Tapo_clock_alignment_calibrated":False,
        "source_is_real_but_not_F5_dispatch_finish":True,
        "no_anonymous_order_or_person_identifiers_exported":True,
        "by_shift":by_shift,
        "D_B_M_models_not_modified":True,
        "F5_independent_reserve":"NOT_CREATED",
        "G4":"NOT_RUN","G5":"NOT_RUN",
        "provider_calls":0,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--pos",type=Path,required=True)
    p.add_argument("--shift-summary",type=Path,required=True)
    for shift in source_audit.SHIFTS:
        p.add_argument("--tapo-"+shift[:8],dest=shift,type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    need(not a.out.exists(),"WEBA_CONTACT_REFUSE_OVERWRITE")
    result=build(a.pos.read_bytes(),a.shift_summary.read_bytes(),{
        shift:getattr(a,shift).read_bytes()
        for shift in source_audit.SHIFTS})
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_bytes(canonical(result)+b"\n")
    print(json.dumps({
        "shifts":list(result["by_shift"]),
        "storage_pairs_in_shift":[result["by_shift"][name][
            "storage_contact_summary"][
            "paired_storage_contact_intervals_COMPLETE_WITHIN_shift"]
            for name in source_audit.SHIFTS],
        "unclosed_storage_opens":[result["by_shift"][name][
            "storage_contact_summary"]["storage_contact_open_without_matched_close"]
            for name in source_audit.SHIFTS],
        "G5":result["G5"],
    },sort_keys=True))


if __name__=="__main__":
    main()
