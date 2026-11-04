"""WEBA one-shift, real-source, time-window co-occurrence audit (NOT model inference).

The same pinned original POS workbook and Tapo snapshot used by F5 #160.
No access to original customer identities, physiological sensors, or case
to machine/zone linkage in the aggregate output.

A priori descriptive grid is fixed in UTC [2024-02-23 13:00, 18:00)
at 30-minute resolution. One primary clock interpretation ASSUMES POS
order_time denotes Europe/Budapest local wall time. Explicit UTC-as-written
sensitivity is reported separately, never chosen for best correlation.
No temporal alignment is certified, no completion events are inferred,
and external time-window co-occurrence is NOT causal relationship.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from scripts.arena_cafe import weba_source_readiness as src
from scripts.arena_v0_contract import canonical

SCHEMA="igc-weba-pos-tapo-fixed-windows/0.1"
SENSORS=("front_door","front_door_m","zone_1","zone_2")
SHIFT_DATE=date(2024,2,23)
TZ=ZoneInfo("Europe/Budapest")
UTC=timezone.utc
START=datetime(2024,2,23,13,0,tzinfo=UTC)
END=datetime(2024,2,23,18,0,tzinfo=UTC)
WINDOW=timedelta(minutes=30)
BINS=tuple(START+i*WINDOW for i in range(11))


def need(ok,code):
    if not ok:
        raise ValueError(code)


def parse_pos_clock(value):
    """Conservative clock-only parser: no invented seconds or day rollover."""
    s=str(value).strip()
    need(bool(s),"WEBA_TEMPORAL_POS_CLOCK_MISSING")
    for fmt in ("%H:%M:%S.%f","%H:%M:%S","%H:%M",
                "%I:%M:%S %p","%I:%M %p"):
        try:
            return datetime.strptime(s,fmt).time()
        except ValueError:
            pass
    # Excel numeric time-of-day in [0,1). If an integer Excel datetime
    # serial is present it must be validated against the separate date.
    try:
        n=Decimal(s)
    except InvalidOperation:
        need(False,"WEBA_TEMPORAL_POS_CLOCK_UNRECOGNIZED")
    need(n.is_finite() and Decimal(0)<=n<Decimal(1),
         "WEBA_TEMPORAL_POS_CLOCK_NUMERIC_OUTSIDE_DAY")
    us=int((n*Decimal(86400000000)).to_integral_value())
    need(0<=us<86400000000,"WEBA_TEMPORAL_POS_CLOCK_ROUNDING_OVERFLOW")
    return (datetime.min+timedelta(microseconds=us)).time()


def pos_shift_clock_times(workbook_bytes):
    """Read only the previously disclosed 33 timestamped POS rows."""
    rows=src._xlsx_rows(workbook_bytes)
    headers=None
    start=None
    for i,row in enumerate(rows[:15]):
        map_={str(v).strip().lower():j for j,v in row.items()}
        if {"order_id","order_date","order_time","time_of_day"}.issubset(map_):
            headers=map_; start=i+1
            break
    need(headers is not None,"WEBA_TEMPORAL_POS_HEADERS_NOT_FOUND")
    selected=[]
    for row in rows[start:]:
        value=lambda k:str(row.get(headers[k],"")).strip()
        if (src._normalize_date(value("order_date"))==SHIFT_DATE.isoformat()
            and value("time_of_day").lower()=="evening"):
            selected.append(parse_pos_clock(value("order_time")))
    need(len(selected)==33,"WEBA_TEMPORAL_POS_33_ORDERS_CHANGED")
    # Time-of-day values are ephemeral; no order ID/time is returned in report.
    return selected


def raw_sensor_times(text):
    """Parse exact Tapo event clocks, rechecking the original parser first."""
    audit=src.parse_tapo_text(text)
    by_name={}
    for m in src.TAPO_SENSOR_RE.finditer(text):
        nickname=m.group(2)
        if nickname not in SENSORS:
            continue
        events=list(src.TAPO_EVENT_RE.finditer(m.group(5)))
        by_name[nickname]=tuple(
            (hit.group(1),datetime.fromtimestamp(int(hit.group(3)),UTC))
            for hit in events)
    need(set(by_name)==set(SENSORS),"WEBA_TEMPORAL_SENSORS_MISSING")
    counts=audit["returned_records_per_selected_sensor"]
    need(all(len(by_name[name])==counts[name] for name in SENSORS),
         "WEBA_TEMPORAL_SENSOR_COUNT_DOES_NOT_MATCH_SOURCE_AUDIT")
    return by_name,audit


def window_index(instant):
    need(instant.tzinfo is not None,"WEBA_TEMPORAL_NAIVE_INSTANT")
    if not START<=instant<END:
        return None
    return int((instant-START)//WINDOW)


def from_pos_clock(local_clock,*,interpretation):
    naive=datetime.combine(SHIFT_DATE,local_clock)
    if interpretation=="BUDAPEST_LOCAL_ASSUMPTION":
        return naive.replace(tzinfo=TZ).astimezone(UTC)
    need(interpretation=="UTC_AS_WRITTEN_SENSITIVITY",
         "WEBA_TEMPORAL_UNAPPROVED_CLOCK_INTERPRETATION")
    return naive.replace(tzinfo=UTC)


def _bins(times):
    counts=[0]*10
    outside=0
    for moment in times:
        i=window_index(moment)
        if i is None:
            outside+=1
        else:
            counts[i]+=1
    return counts,outside


def compare(workbook,tapo):
    base=src.build(workbook,tapo)
    pos_clocks=pos_shift_clock_times(workbook)
    sensors,log_audit=raw_sensor_times(tapo.decode("utf-8"))
    assert len(BINS)==11
    need(START.astimezone(TZ).utcoffset()==timedelta(hours=1),
         "WEBA_TEMPORAL_EXPECTED_BUDAPEST_WINTER_OFFSET_CHANGED")
    need(len(pos_clocks)==base["pos"][
        "selected_shift_rows_with_order_time"]==33,
        "WEBA_TEMPORAL_SOURCE_POS_COUNT_MISMATCH")
    primary=[from_pos_clock(t,interpretation="BUDAPEST_LOCAL_ASSUMPTION")
             for t in pos_clocks]
    alternate=[from_pos_clock(t,interpretation="UTC_AS_WRITTEN_SENSITIVITY")
               for t in pos_clocks]
    main_counts,main_out=_bins(primary)
    alt_counts,alt_out=_bins(alternate)
    sensor_counts={}
    outside={}
    selected_counts={}
    for name,events in sensors.items():
        result,n_out=_bins([when for _,when in events])
        sensor_counts[name]=result
        outside[name]=n_out
        selected_counts[name]=len(events)
    need(all(sum(sensor_counts[s])+outside[s]==selected_counts[s]
             for s in SENSORS),"WEBA_TEMPORAL_SENSOR_EVENTS_NOT_CONSERVED")
    need(sum(main_counts)+main_out==33 and
         sum(alt_counts)+alt_out==33,
         "WEBA_TEMPORAL_POS_EVENTS_NOT_CONSERVED")

    # Co-presence in a bin is the strongest permitted purely descriptive
    # claim. No lag fitting, pairing, arrival detection, or causal scoring.
    coactive={
        k:sum(p>0 and q>0 for p,q in zip(main_counts,sensor_counts[k]))
        for k in SENSORS
    }
    bins=[]
    for i in range(10):
        bins.append({
            "utc_half_open":[BINS[i].isoformat(),BINS[i+1].isoformat()],
            "pos_orders_assuming_Budapest_local_clock":main_counts[i],
            "tapo_front_door_contact_events":sensor_counts["front_door"][i],
            "tapo_front_door_motion_events":sensor_counts["front_door_m"][i],
            "tapo_zone_1_motion_events":sensor_counts["zone_1"][i],
            "tapo_zone_2_motion_events":sensor_counts["zone_2"][i],
        })
    return {
        "schema":SCHEMA,
        "study":"WEBA_REAL_EXPLORATORY_DEVELOPMENT_ONE_PREINSPECTED_SHIFT",
        "source_audit_schema":base["schema"],
        "upstream_git_commit":base["upstream_git_commit"],
        "pos_sha256":base["source_files_verified_by_git_blob_sha1_and_sha256"]["pos"]["sha256"],
        "tapo_sha256":base["source_files_verified_by_git_blob_sha1_and_sha256"]["tapo"]["sha256"],
        "sample_shift":src.SHIFT_ID,
        "data_previously_seen_not_blind":True,
        "window_minutes":30,
        "window_rule":"FIXED_UTC_HALF_OPEN_13_TO_18_SAME_DAY",
        "number_of_bins":10,
        "assumed_pos_clock_zone":"Europe/Budapest",
        "POS_clock_timezone_from_raw_metadata_certified":False,
        "Tapo_source_clock":"UNIX_EPOCH_SECONDS_UTC",
        "cross_clock_offset_calibrated":False,
        "pos_orders_selected":33,
        "pos_orders_in_primary_windows":sum(main_counts),
        "pos_orders_outside_primary_windows":main_out,
        "pos_orders_in_UTC_as_written_sensitivity_windows":sum(alt_counts),
        "pos_orders_outside_UTC_as_written_sensitivity_windows":alt_out,
        "sensor_selected_event_totals":selected_counts,
        "sensor_outside_fixed_windows":outside,
        "sensor_rows_per_window_with_pos_assumed_local":bins,
        "bins_with_both_pos_and_sensor_pulse_assuming_local":coactive,
        "no_single_time_offset_optimized_for_correspondence":True,
        "no_pos_order_tapo_event_pairing_attempted":True,
        "no_causality_or_service_event_inferred":True,
        "sensor_snapshots_not_known_complete":True,
        "coactivity_is_not_customer_or_order_identification":True,
        "no_case_id_device_id_or_individual_event_times_in_output":True,
        "health_participant_wearable_data_not_read":True,
        "D_B_M_unchanged":True,
        "G4":"NOT_RUN","G5":"NOT_RUN","F5_reserve":"NOT_CREATED",
        "provider_calls":0,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--pos",required=True,type=Path)
    p.add_argument("--tapo",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    need(not a.out.exists(),"WEBA_TEMPORAL_REFUSE_OVERWRITE")
    report=compare(a.pos.read_bytes(),a.tapo.read_bytes())
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_bytes(canonical(report)+b"\n")
    print(json.dumps({
        "shift_pos":report["pos_orders_selected"],
        "local_assumption_in_grid":report["pos_orders_in_primary_windows"],
        "UTC_as_written_in_grid":report["pos_orders_in_UTC_as_written_sensitivity_windows"],
        "G5":report["G5"],
    },sort_keys=True))


if __name__=="__main__":
    main()
