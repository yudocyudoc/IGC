"""WEBA: shift-bounded source comparison with UNKNOWN sensor coverage.

Uses only the five previously audited, SHA-pinned sources from PR #163.
Original half-hour grid is kept for comparability but intersections with
declared shift start/end are calculated before comparing any events.
Snapshot time is a HARD upper bound on what the exported Tapo history could
have observed; pre-export time remains UNVERIFIED, not "covered".
Never pairs events, calibrates clocks, scores models, or infers inactivity.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from scripts.arena_cafe import weba_instrument_integrity as instrument
from scripts.arena_cafe import weba_source_readiness as source
from scripts.arena_cafe import weba_temporal_windows as old
from scripts.arena_v0_contract import canonical

SCHEMA="igc-weba-shift-bounded-temporal-evidence/0.1"
SENSORS=old.SENSORS
UTC=timezone.utc
HALF_HOUR=timedelta(minutes=30)
WINDOWS_PER_SHIFT=10
WINDOW_FIRST_HOUR_UTC=13
SCORING="NEVER_CAUSAL_NEVER_SENSOR_COVERAGE_CERTIFIED"


def need(condition,code):
    if not condition:
        raise ValueError(code)


def overlap_seconds(a,b,c,d):
    """Length of [a,b) intersection [c,d) in seconds."""
    need(all(x.tzinfo is not None for x in (a,b,c,d)) and a<=b and c<=d,
         "WEBA_BOUNDED_INVALID_INTERVAL")
    return max(0.0,(min(b,d)-max(a,c)).total_seconds())


def _minutes(seconds):
    return round(seconds/60,6)


def pos_receipt_timestamps(raw):
    """Only selected date/shift and order clock; never ID or line-item data."""
    rows,cols=instrument.workbook_values(raw,instrument.REQUIRED_POS_COLS)
    results={key:[] for key in instrument.SHIFTS}
    for row in rows:
        value=lambda field:str(row.get(cols[field],"")).strip()
        day=source._normalize_date(value("order_date"))
        label=value("time_of_day").lower()
        key=(day.replace("-","")+"_"+label) if day else ""
        if key not in results:
            continue
        if not value("order_time"):
            need(False,"WEBA_BOUNDED_SELECTED_SHIFT_POS_CLOCK_MISSING")
        clock=old.parse_pos_clock(value("order_time"))
        day_date=datetime.strptime(day,"%Y-%m-%d").date()
        naive=datetime.combine(day_date,clock)
        primary=naive.replace(tzinfo=old.TZ).astimezone(UTC)
        alternate=naive.replace(tzinfo=UTC)
        results[key].append((primary,alternate))
    return results


def tapo_sensor_timestamps(text):
    """Named environmental sensors only; vendor device IDs never exported."""
    parsed=source.parse_tapo_text(text)
    data={}
    for block in source.TAPO_SENSOR_RE.finditer(text):
        name=block.group(2)
        if name not in SENSORS:
            continue
        events=[
            datetime.fromtimestamp(int(m.group(3)),UTC)
            for m in source.TAPO_EVENT_RE.finditer(block.group(5))
        ]
        data[name]=events
    need(set(data)==set(SENSORS),
         "WEBA_BOUNDED_MISSING_OR_CHANGED_SELECTED_SENSOR")
    need(all(len(data[k])==parsed["returned_records_per_selected_sensor"][k]
             for k in SENSORS),
         "WEBA_BOUNDED_SENSOR_SOURCE_EVENT_COUNT_CHANGED")
    return data


def classify(timestamps,shift_start,shift_end,export_end):
    """Counts only; no assumptions about absence of omitted sensor pulses."""
    out={
        "before_shift":sum(t<shift_start for t in timestamps),
        "inside_shift_pre_export":sum(
            shift_start<=t<shift_end and t<=export_end for t in timestamps),
        "inside_shift_after_export":sum(
            shift_start<=t<shift_end and t>export_end for t in timestamps),
        "after_shift":sum(t>=shift_end for t in timestamps),
    }
    need(sum(out.values())==len(timestamps),
         "WEBA_BOUNDED_CLASSIFICATION_LOSES_EVENTS")
    return out


def binning(timestamps,start,end,shift_start,shift_end):
    """30min cell counts restricted to shift; do not classify silence as idle."""
    return [
        sum(max(start+i*HALF_HOUR,shift_start)<=t<
            min(start+(i+1)*HALF_HOUR,shift_end)
            for t in timestamps)
        for i in range(WINDOWS_PER_SHIFT)
    ]


def shift_report(name,shift_info,log_text,orders):
    utc_start,utc_end=[
        datetime.fromisoformat(t) for t in
        shift_info["UTC_boundaries_under_UNVERIFIED_local_clock_assumption"]]
    export_start=datetime.fromisoformat(
        shift_info["Tapo"]["Tapo_snapshot_time_utc_first"])
    export_end=datetime.fromisoformat(
        shift_info["Tapo"]["Tapo_snapshot_time_utc_last"])
    need(utc_start<utc_end and export_start<=export_end,
         "WEBA_BOUNDED_INVALID_SOURCE_SHIFT_OR_EXPORT_CLOCK")
    date=datetime.strptime(name[:8],"%Y%m%d")
    grid_start=date.replace(hour=WINDOW_FIRST_HOUR_UTC,
                            minute=0,second=0,tzinfo=UTC)
    grid_end=grid_start+WINDOWS_PER_SHIFT*HALF_HOUR
    need(grid_start<utc_start<grid_end and
         grid_start<utc_end<grid_end,
         "WEBA_BOUNDED_EXISTING_GRID_DOES_NOT_CONTAIN_SHIFT")
    sensor=tapo_sensor_timestamps(log_text)
    primary=[x[0] for x in orders]
    alternate=[x[1] for x in orders]
    group_audit=instrument.tapo_log_audit(name,log_text,{
        "interval_for_audit_only":(utc_start,utc_end)})
    need(group_audit["total_events_in_snapshot"]==
         shift_info["Tapo"]["total_events_in_snapshot"],
         "WEBA_BOUNDED_TAPO_SOURCE_AUDIT_CHANGED")
    categories={
        n:classify(series,utc_start,utc_end,export_end)
        for n,series in sensor.items()}
    pos_primary=classify(primary,utc_start,utc_end,export_end)
    pos_alternate=classify(alternate,utc_start,utc_end,export_end)
    # Crucial: 0 before export does NOT demonstrate zero physical activity.
    cells=[]
    for i in range(WINDOWS_PER_SHIFT):
        a=grid_start+i*HALF_HOUR
        b=a+HALF_HOUR
        in_shift=overlap_seconds(a,b,utc_start,utc_end)
        post_export=overlap_seconds(
            a,b,min(utc_end,max(utc_start,export_end)),utc_end)
        pre_export=in_shift-post_export
        need(pre_export>=-1e-7 and post_export>=0 and
             in_shift<=HALF_HOUR.total_seconds(),
             "WEBA_BOUNDED_WINDOW_EXPOSURE_INCONSISTENT")
        counts={n:sum(max(a,utc_start)<=t<min(b,utc_end)
                      for t in sensor[n]) for n in SENSORS}
        pos_count=sum(max(a,utc_start)<=t<min(b,utc_end)
                      for t in primary)
        if in_shift==0:
            status="OUTSIDE_DECLARED_SHIFT_NOT_IN_SAMPLE"
        elif post_export>0:
            status="SHIFT_PARTLY_AFTER_TAPO_EXPORT_CANNOT_OBSERVE_TAIL"
        elif in_shift<HALF_HOUR.total_seconds():
            status="PARTIAL_SHIFT_INTERVAL_UNKNOWN_SENSOR_CONTINUITY"
        else:
            status="FULL_HALF_HOUR_DECLARED_SHIFT_UNKNOWN_SENSOR_CONTINUITY"
        cells.append({
            "utc_window_half_open":[a.isoformat(),b.isoformat()],
            "minutes_inside_declared_shift":_minutes(in_shift),
            "minutes_outside_declared_shift":
                _minutes(HALF_HOUR.total_seconds()-in_shift),
            "minutes_inside_shift_at_or_before_last_Tapo_export_NOT_CERTIFIED":
                _minutes(pre_export),
            "minutes_inside_shift_after_last_Tapo_export_PROVABLY_UNOBSERVED":
                _minutes(post_export),
            "temporal_evidence_status":status,
            "pos_received_orders_inside_declared_shift_Budapest_assumption":
                pos_count,
            "Tapo_source_pulses_inside_declared_shift":{
                n:counts[n] for n in SENSORS},
            "no_sensor_signal_does_NOT_mean_IDLE":True,
        })
    need(abs(sum(c["minutes_inside_declared_shift"] for c in cells)-
             _minutes((utc_end-utc_start).total_seconds()))<0.00002,
         "WEBA_BOUNDED_GRID_MASS_NOT_CONSERVED")
    need(sum(c[
        "pos_received_orders_inside_declared_shift_Budapest_assumption"
        ] for c in cells)==(
            pos_primary["inside_shift_pre_export"]+
            pos_primary["inside_shift_after_export"]),
         "WEBA_BOUNDED_POS_EVENTS_NOT_CONSERVED")
    need(all(sum(c["Tapo_source_pulses_inside_declared_shift"][n]
                 for c in cells)==categories[n]["inside_shift_pre_export"]+
                 categories[n]["inside_shift_after_export"]
             for n in SENSORS),
         "WEBA_BOUNDED_TAPO_EVENTS_NOT_CONSERVED")
    need(all(categories[n]["inside_shift_after_export"]==0 for n in SENSORS),
         "WEBA_BOUNDED_SENSOR_EVENT_AFTER_DUMP_INVALID")
    comparison_cells=[
        c for c in cells
        if c["minutes_inside_declared_shift"]>0 and
           c["pos_received_orders_inside_declared_shift_Budapest_assumption"]==0
           and any(c["Tapo_source_pulses_inside_declared_shift"].values())
    ]
    return {
        "shift":name,
        "declared_UTC_shift_boundaries_under_UNVERIFIED_Budapest_assumption":
            [utc_start.isoformat(),utc_end.isoformat()],
        "snapshot_export_time_range_UTC":
            [export_start.isoformat(),export_end.isoformat()],
        "shift_duration_minutes":_minutes(
            (utc_end-utc_start).total_seconds()),
        "shift_minutes_AFTER_latest_Tapo_export_cannot_have_been_collected":
            _minutes(max(0,(utc_end-max(utc_start,export_end)).total_seconds())),
        "shift_minutes_before_Tapo_export_NOT_a_coverage_claim":
            _minutes(max(0,(min(export_end,utc_end)-utc_start).total_seconds())),
        "Tapo_coverage_continuity_verified":False,
        "POS_cross_device_time_sync_verified":False,
        "POS_original_selected_shift_rows":len(primary),
        "POS_received_orders_Budapest_assumption":pos_primary,
        "POS_received_orders_UTC_as_written_sensitivity":pos_alternate,
        "Tapo_pulses_four_sensors_by_relative_shift_position":categories,
        "Tapo_all_ten_sensor_original_snapshot_count":
            group_audit["total_events_in_snapshot"],
        "count_half_hour_cells_with_some_declared_shift":sum(
            x["minutes_inside_declared_shift"]>0 for x in cells),
        "count_declared_shift_cells_with_Tapo_and_zero_POS":
            len(comparison_cells),
        "cooccurrence_NOT_service_or_customer_identity":True,
        "half_hour_cells":cells,
    }


def build(pos,metadata,logs):
    src_audit=instrument.build(pos,metadata,logs)
    orders=pos_receipt_timestamps(pos)
    out={}
    for shift in instrument.SHIFTS:
        out[shift]=shift_report(
            shift,src_audit["shifts"][shift],logs[shift].decode("utf-8"),
            orders[shift])
    need([out[x]["POS_original_selected_shift_rows"]
          for x in instrument.SHIFTS]==[33,7,15],
         "WEBA_BOUNDED_SOURCE_POS_COUNTS_DRIFT")
    return {
        "schema":SCHEMA,
        "source_audit_schema":src_audit["schema"],
        "source_upstream_commit":src_audit["upstream_git_commit"],
        "source_file_digests":src_audit["source_file_digests"],
        "shifts_in_previously_disclosed_order":list(instrument.SHIFTS),
        "previously_seen_data_NOT_an_independent_blind_reserve":True,
        "time_grid_from_original_PR161":"13:00_TO_18:00_UTC_30MIN",
        "temporal_clipping_to_original_shift_summary":True,
        "assumed_local_time":"Europe/Budapest_UNVERIFIED",
        "POS_timezone_calibrated":False,
        "sensor_continuity_calibrated":False,
        "even_full_shift_window_never_implies_sensor_was_ON":True,
        "post_snapshot_tail_provably_unrecorded_if_export_early":True,
        "no_downtime_estimated_from_motion_gaps":True,
        "no_pos_to_sensor_lag_fitted_or_linked_to_orders":True,
        "no_per_order_service_start_or_finish_inferred":True,
        "no_causal_bottleneck_or_throughput_claim":True,
        "no_physio_or_participant_data":True,
        "source_events_order_ids_device_ids_not_published":True,
        "by_shift":out,
        "D_B_M_unchanged":True,
        "F5_independent_reserve":"NOT_CREATED",
        "G4":"NOT_RUN","G5":"NOT_RUN",
        "provider_calls":0,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--pos",type=Path,required=True)
    p.add_argument("--shift-summary",type=Path,required=True)
    for key in instrument.SHIFTS:
        p.add_argument("--tapo-"+key[:8],dest=key,type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    need(not args.out.exists(),"WEBA_BOUNDED_REFUSE_OVERWRITE")
    result=build(args.pos.read_bytes(),args.shift_summary.read_bytes(),{
        key:getattr(args,key).read_bytes() for key in instrument.SHIFTS})
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_bytes(canonical(result)+b"\n")
    print(json.dumps({
        "shifts":result["shifts_in_previously_disclosed_order"],
        "POS_inside":[result["by_shift"][x][
            "POS_received_orders_Budapest_assumption"]["inside_shift_pre_export"]+
            result["by_shift"][x][
            "POS_received_orders_Budapest_assumption"]["inside_shift_after_export"]
            for x in instrument.SHIFTS],
        "unrecordable_tail_minutes":[
            result["by_shift"][x][
            "shift_minutes_AFTER_latest_Tapo_export_cannot_have_been_collected"]
            for x in instrument.SHIFTS],
        "G5":result["G5"]
    },sort_keys=True))


if __name__=="__main__":
    main()
