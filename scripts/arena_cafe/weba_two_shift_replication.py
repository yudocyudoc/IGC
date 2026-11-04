"""WEBA two chronological, metadata-selected evening-shift external replication.

Sources frozen prior to raw event inspection in docs/arena_cafe/f5/04_*.
No hypothesis-pair fitting, POS↔Tapo link, or G5 independence claim.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path

from scripts.arena_cafe import weba_source_readiness as src
from scripts.arena_cafe import weba_temporal_windows as windows
from scripts.arena_v0_contract import canonical

SCHEMA="igc-weba-two-evening-shifts-window-replication/0.1"
UPSTREAM_COMMIT=src.UPSTREAM_COMMIT
REFERENCE_ORIGINAL_POS=src.SOURCE_FILES["pos"]
SHIFTS=(
    {"name":"20240304_evening","date":"2024-03-04",
     "log_size":44186,
     "log_blob":"e9059ae926717492a29dd8a4ac5743fcfc7f4f39"},
    {"name":"20240308_evening","date":"2024-03-08",
     "log_size":44237,
     "log_blob":"9b4eab54a3a31696970f7221aee42fc4448fb9a1"},
)
SENSORS=windows.SENSORS
UTC=timezone.utc
START_HOUR_UTC=13
WINDOW_MINUTES=30
N_BINS=10


def need(ok,code):
    if not ok:
        raise ValueError(code)


def verify_sources(pos_bytes,logs):
    """Reject changed bytes; no 'latest' data and no participant files."""
    src.verify_pinned("pos",pos_bytes)
    need(type(logs) is dict and set(logs)=={
        s["name"] for s in SHIFTS},
        "WEBA_REPL_SELECTION_NOT_PREDECLARED")
    verified={}
    for shift in SHIFTS:
        raw=logs[shift["name"]]
        need(type(raw) is bytes,"WEBA_REPL_LOG_MISSING")
        sha=hashlib.sha1(
            f"blob {len(raw)}\0".encode("ascii")+raw).hexdigest()
        need(len(raw)==shift["log_size"] and sha==shift["log_blob"],
             "WEBA_REPL_SOURCE_HASH_OR_SIZE_CHANGED")
        verified[shift["name"]]={
            "git_blob_sha1":sha,
            "sha256":"sha256:"+hashlib.sha256(raw).hexdigest(),
            "bytes":len(raw),
        }
    return verified


def pos_time_fields(workbook):
    """Read dates and clocks only; never return order IDs or prices."""
    rows=src._xlsx_rows(workbook)
    header=None
    for i,row in enumerate(rows[:15]):
        fields={str(v).strip().lower():j for j,v in row.items()}
        if {"order_id","order_date","order_time","time_of_day"}.issubset(fields):
            header=fields
            data=rows[i+1:]
            break
    need(header is not None,"WEBA_REPL_POS_HEADERS_INCOMPLETE")
    selected={}
    for shift in SHIFTS:
        selected[shift["name"]]={"clocks":[],"missing":0,"total":0}
    for row in data:
        val=lambda k:str(row.get(header[k],"")).strip()
        date=src._normalize_date(val("order_date"))
        label=val("time_of_day").lower()
        for shift in SHIFTS:
            if date==shift["date"] and label=="evening":
                found=selected[shift["name"]]
                found["total"]+=1
                if val("order_time"):
                    found["clocks"].append(
                        windows.parse_pos_clock(val("order_time")))
                else:
                    found["missing"]+=1
                break
    return selected


def index_for(moment,initial,*,width=WINDOW_MINUTES,count=N_BINS):
    """Half-open fixed bins, never reorder/round event times."""
    need(moment.tzinfo is not None and initial.tzinfo is not None,
         "WEBA_REPL_NAIVE_TIMESTAMP")
    end=initial+timedelta(minutes=width*count)
    if not initial<=moment<end:
        return None
    return int((moment-initial)//timedelta(minutes=width))


def histogram(moments,initial):
    result=[0]*N_BINS
    outside=0
    for moment in moments:
        index=index_for(moment,initial)
        if index is None:
            outside+=1
        else:
            result[index]+=1
    need(sum(result)+outside==len(moments),
         "WEBA_REPL_EVENT_COUNT_LOST")
    return result,outside


def characterize_shift(shift,clocks,log):
    """Different source clocks: an ASSUMPTION plus a parallel sensitivity."""
    day=datetime.strptime(shift["date"],"%Y-%m-%d").date()
    start=datetime(day.year,day.month,day.day,START_HOUR_UTC,tzinfo=UTC)
    need(start.astimezone(windows.TZ).utcoffset()==timedelta(hours=1),
         "WEBA_REPL_BUDAPEST_OFFSET_NOT_PREDECLARED")
    primary=[]
    alternate=[]
    for clock in clocks["clocks"]:
        naive=datetime.combine(day,clock)
        primary.append(naive.replace(tzinfo=windows.TZ).astimezone(UTC))
        alternate.append(naive.replace(tzinfo=UTC))
    pos_bins,pos_out=histogram(primary,start)
    utc_bins,utc_out=histogram(alternate,start)
    need(sum(pos_bins)+pos_out+clocks["missing"]==clocks["total"],
         "WEBA_REPL_POS_SUBSET_NOT_CONSERVED")
    sensor_events,source_audit=windows.raw_sensor_times(log.decode("utf-8"))
    sensors={}
    outside={}
    coactivity={}
    zero_pos={}
    for name in SENSORS:
        sensor_bins,sensor_out=histogram(
            (t for _,t in sensor_events[name]),start)
        sensors[name]=sensor_bins
        outside[name]=sensor_out
        need(sum(sensor_bins)+sensor_out==len(sensor_events[name]),
             "WEBA_REPL_SENSOR_SUBSET_NOT_CONSERVED")
        coactivity[name]=sum(p>0 and q>0
                             for p,q in zip(pos_bins,sensor_bins))
        zero_pos[name]=sum(q for p,q in zip(pos_bins,sensor_bins)
                           if p==0)
    zero_pos_bins=sum(
        pos_bins[i]==0 and any(sensors[n][i]>0 for n in SENSORS)
        for i in range(N_BINS))
    return {
        "shift":shift["name"],
        "date":shift["date"],
        "pos_rows_in_shift":clocks["total"],
        "pos_clock_values_available":len(clocks["clocks"]),
        "pos_rows_without_clock":clocks["missing"],
        "pos_local_assumption_in_windows":sum(pos_bins),
        "pos_local_assumption_outside_windows":pos_out,
        "pos_UTC_as_written_sensitivity_in_windows":sum(utc_bins),
        "pos_UTC_as_written_sensitivity_outside_windows":utc_out,
        "tapo_sensor_groups":source_audit["sensor_count"],
        "tapo_total_returned_all_sensor_groups":
            source_audit["total_returned_tapo_events"],
        "tapo_selected_sensors_total_events":{
            n:len(sensor_events[n]) for n in SENSORS},
        "tapo_selected_sensors_outside_windows":outside,
        "bins_with_POS_orders":sum(v>0 for v in pos_bins),
        "bins_with_both_pos_and_sensor_pulses":coactivity,
        "bins_with_sensor_pulses_but_zero_pos_orders":zero_pos_bins,
        "sensor_pulses_in_zero_pos_order_bins":zero_pos,
        "half_hour_windows":[{
            "utc_half_open":[
                (start+timedelta(minutes=i*WINDOW_MINUTES)).isoformat(),
                (start+timedelta(minutes=(i+1)*WINDOW_MINUTES)).isoformat()],
            "POS_under_Budapest_assumption":pos_bins[i],
            "sensors":{name:sensors[name][i] for name in SENSORS},
        } for i in range(N_BINS)],
        "tapo_snapshot_full_shift_coverage_proven":False,
        "pos_tapo_independent_clock_calibration_proven":False,
        "case_to_sensor_event_link_proven":False,
        "sensor_event_as_customer_arrival_or_service_finish":False,
    }


def build(pos_bytes,log_bytes_by_shift):
    verified=verify_sources(pos_bytes,log_bytes_by_shift)
    pos=pos_time_fields(pos_bytes)
    results=[characterize_shift(shift,pos[shift["name"]],
                                log_bytes_by_shift[shift["name"]])
             for shift in SHIFTS]
    need(len(results)==2,"WEBA_REPL_SHIFT_NOT_PRESERVED")
    return {
        "schema":SCHEMA,
        "selection_rule":"FIRST_TWO_EXISTING_EVENING_TAPO_LOG_SHIFTS_AFTER_20240223",
        "selection_precommitted_before_READING_TEST_SHIFT_LOGS":True,
        "selection_based_on_metadata_not_POS_event_counts":True,
        "already_inspected_development_shift":"20240223_evening",
        "not_G5_blind_independent_sample":True,
        "upstream_commit":UPSTREAM_COMMIT,
        "pos_input_git_blob_sha1":REFERENCE_ORIGINAL_POS["git_blob_sha1"],
        "source_log_hashes":verified,
        "fixed_window_UTC_start":"13:00",
        "fixed_window_UTC_end":"18:00",
        "fixed_window_minutes":WINDOW_MINUTES,
        "fixed_window_half_open":True,
        "pos_clock_assumed_zone_not_verified":"Europe/Budapest",
        "UTC_as_written_alternative_not_selected_by_fit":True,
        "no_time_shift_or_lag_optimized":True,
        "no_Poisson_or_service_rate_fitted":True,
        "sensor_pulses_not_order_or_service_observations":True,
        "no_raw_person_order_device_or_event_identifiers_exported":True,
        "no_machine_acceleration_or_health_measurements_read":True,
        "source_same_business_as_development_not_independent_business":True,
        "results":results,
        "scientific_identification":"NOT_ESTABLISHED",
        "G4":"NOT_RUN","G5":"NOT_RUN","F5_independent_reserve":"NOT_CREATED",
        "D_B_M_unchanged":True,
        "provider_calls":0,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--pos",required=True,type=Path)
    p.add_argument("--log-20240304",required=True,type=Path)
    p.add_argument("--log-20240308",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    need(not args.out.exists(),"WEBA_REPL_REFUSE_OVERWRITE")
    result=build(args.pos.read_bytes(),{
        SHIFTS[0]["name"]:args.log_20240304.read_bytes(),
        SHIFTS[1]["name"]:args.log_20240308.read_bytes(),
    })
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_bytes(canonical(result)+b"\n")
    print(json.dumps({
        "shifts":[x["shift"] for x in result["results"]],
        "POS_counts":[x["pos_clock_values_available"] for x in result["results"]],
        "Tapo_counts":[x["tapo_total_returned_all_sensor_groups"]
                       for x in result["results"]],
        "G5":result["G5"],
    },sort_keys=True))


if __name__=="__main__":
    main()
