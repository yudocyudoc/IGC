"""WEBA instrument integrity audit: Tapo coverage limits and POS clock provenance.

Runs on FIVE frozen external files: original POS workbook, original shift
metadata workbook, and Tapo logs of 20240223_evening, 20240304_evening,
20240308_evening. All sources pinned by Git blob sha1 + size, no participant
records or physiology. Does NOT infer absence of activity from sensor silence,
detect missing events from gaps in vendor IDs, or calibrate POS/Tapo clocks.
Never outputs raw order times, case/device identifiers or Tapo event logs.

Caution: agreement between Tapo TriggerLogsResult.sum and the returned
array only tests internal response consistency, NOT historical completeness.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
import argparse
import hashlib
import json
import re
from pathlib import Path
from io import BytesIO
from zipfile import ZipFile
import xml.etree.ElementTree as ET

from scripts.arena_cafe import weba_source_readiness as source
from scripts.arena_cafe import weba_temporal_windows as clocks
from scripts.arena_cafe import weba_two_shift_replication as replication
from scripts.arena_v0_contract import canonical

SCHEMA="igc-weba-tapo-history-pos-clock-provenance-audit/0.1"
STUDY_SAME_GIT_COMMIT=source.UPSTREAM_COMMIT
SHIFTS=("20240223_evening","20240304_evening","20240308_evening")
META_FILE={
    "path":"B.shift_data/shift_summary.xlsx",
    "bytes":13721,
    "git_blob_sha1":"a8a717c0f0b8292297a71328c2bc6dfc90b6fa82",
}
LOG_FILES={
    source.SHIFT_ID:{
        "bytes":source.SOURCE_FILES["tapo"]["size_bytes"],
        "git_blob_sha1":source.SOURCE_FILES["tapo"]["git_blob_sha1"],
    },
    **{s["name"]:{
        "bytes":s["log_size"],"git_blob_sha1":s["log_blob"]
    } for s in replication.SHIFTS},
}
UTC=timezone.utc
MAIN="{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
DUMP_RE=re.compile(r"(?m)^[\ufeff \t]*(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d+Z)")
EXPLICIT_ZONE_RE=re.compile(r"(?:Z|[+-]\d{2}:\d{2})$",re.I)
REQUIRED_SHIFT_COLS={"shift_date","time_of_day","start_time","end_time"}
REQUIRED_POS_COLS={"order_date","time_of_day","order_time","order_id"}


def need(condition,code):
    if not condition:
        raise ValueError(code)


def _blob(raw,expected,tag):
    need(type(raw) is bytes and len(raw)==expected["bytes"],
         "WEBA_AUDIT_"+tag+"_SIZE_CHANGED")
    sha=hashlib.sha1(f"blob {len(raw)}\0".encode()+raw).hexdigest()
    need(sha==expected["git_blob_sha1"],
         "WEBA_AUDIT_"+tag+"_GIT_BLOB_CHANGED")
    return {
        "bytes":len(raw),
        "git_blob_sha1":sha,
        "sha256":"sha256:"+hashlib.sha256(raw).hexdigest(),
    }


def verify_inputs(pos,shifts,logs):
    ref=source.verify_pinned("pos",pos)
    md=_blob(shifts,META_FILE,"SHIFT_METADATA")
    need(type(logs) is dict and set(logs)==set(SHIFTS),
         "WEBA_AUDIT_SHIFT_SELECTION_CHANGED")
    l={k:_blob(v,LOG_FILES[k],"TAPO") for k,v in logs.items()}
    return {"POS":ref,"SHIFT_METADATA":md,"TAPO_LOGS":l}


def workbook_values(data,required):
    rows=source._xlsx_rows(data)
    headers=None
    for i,row in enumerate(rows[:15]):
        candidate={str(v).strip().lower():col
                   for col,v in row.items() if str(v).strip()}
        if required.issubset(candidate):
            headers=candidate
            break
    need(headers is not None,
         "WEBA_AUDIT_WORKBOOK_HEADERS_MISSING")
    return rows[i+1:],headers


def excel_cell_type_counts(data,field,required):
    """OOXML cell t-attribute audit only; no record-level cells exposed."""
    rows,head=workbook_values(data,required)
    target_col=head[field]
    with ZipFile(BytesIO(data)) as z:
        tree=ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    counts=Counter()
    target_cells=0
    for row in tree.iter(MAIN+"row"):
        for cell in row.findall(MAIN+"c"):
            address=cell.attrib.get("r","")
            prefix=re.match(r"^[A-Z]+",address)
            if prefix is None:
                continue
            number=0
            for letter in prefix.group():
                number=number*26+ord(letter)-64
            if number==target_col and cell.find(MAIN+"v") is not None or (
               number==target_col and cell.find(MAIN+"is") is not None):
                target_cells+=1
                counts[cell.attrib.get("t","n_or_default")]+=1
    # Counts include header row, so do not equate them with 588 orders.
    return {"all_including_header":target_cells,
            "cell_storage_types_including_header":dict(sorted(counts.items()))}


def pos_clock_audit(pos):
    rows,cols=workbook_values(pos,REQUIRED_POS_COLS)
    raw_clock=[str(r.get(cols["order_time"],"")).strip() for r in rows
               if any(str(v).strip() for v in r.values())]
    valid=0
    missing=0
    rejected=0
    explicit_offset=0
    am_pm=0
    date_encoding=Counter()
    for row in rows:
        if not any(str(v).strip() for v in row.values()):
            continue
        date=str(row.get(cols["order_date"],"")).strip()
        if re.fullmatch(r"\d{8}",date):
            date_encoding["YYYYMMDD_8_DIGITS"]+=1
        elif date:
            date_encoding["OTHER_NONEMPTY"]+=1
        else:
            date_encoding["BLANK"]+=1
    for val in raw_clock:
        if not val:
            missing+=1
            continue
        if EXPLICIT_ZONE_RE.search(val):
            explicit_offset+=1
        if re.search(r"\b(?:AM|PM)\b",val,re.I):
            am_pm+=1
        try:
            clocks.parse_pos_clock(val)
            valid+=1
        except ValueError:
            rejected+=1
    return {
        "nonempty_order_rows":len(raw_clock),
        "parseable_order_time_as_wall_clock":valid,
        "blank_order_time":missing,
        "unparseable_order_time":rejected,
        "order_time_with_explicit_timezone_offset_or_Z":explicit_offset,
        "order_time_values_with_AM_PM_marker":am_pm,
        "order_date_raw_encoding_counts":dict(date_encoding),
        "order_time_OOXML_cells":excel_cell_type_counts(
            pos,"order_time",REQUIRED_POS_COLS),
        "POS_time_provenance":"ORDER_RECEIPT_CLOCK_FROM_POS_PER_ARTICLE",
        "POS_is_physical_arrival_time":False,
        "timezone_present_in_individual_order_time_values":explicit_offset>0,
        "timezone_certified_by_source":False,
        "UTC_offset_or_drift_calibrated_against_Tapo":False,
        "no_raw_POS_times_or_order_ids_exported":True,
    }


def _shift_metadata_clock(raw):
    """Use HHhMM only for shift metadata, never reinterpret POS times."""
    m=re.fullmatch(r"([01]?\d|2[0-3])h([0-5]\d)",raw.strip())
    if m:
        return datetime.strptime(raw.strip(),"%Hh%M").time(),"HHhMM"
    return clocks.parse_pos_clock(raw),"STANDARD_WALL_CLOCK"


def shift_boundaries(summary):
    """Only shift date, label and clock fields (skip participant IDs)."""
    rows,cols=workbook_values(summary,REQUIRED_SHIFT_COLS)
    selected={}
    counts=Counter()
    for row in rows:
        if not any(str(v).strip() for v in row.values()):
            continue
        counts["nonempty_rows"]+=1
        val=lambda k:str(row.get(cols[k],"")).strip()
        day=source._normalize_date(val("shift_date"))
        label=val("time_of_day").lower()
        name=day.replace("-","")+"_"+label if day else ""
        if name not in SHIFTS:
            continue
        need(name not in selected,"WEBA_AUDIT_DUPLICATE_SHIFT_METADATA")
        start,start_fmt=_shift_metadata_clock(val("start_time"))
        end,end_fmt=_shift_metadata_clock(val("end_time"))
        need(start<end,"WEBA_AUDIT_SHIFT_CLOCK_CROSSES_DAY_OR_INVALID")
        day_dt=datetime.strptime(day,"%Y-%m-%d")
        initial=datetime.combine(day_dt.date(),start).replace(
            tzinfo=clocks.TZ).astimezone(UTC)
        final=datetime.combine(day_dt.date(),end).replace(
            tzinfo=clocks.TZ).astimezone(UTC)
        need(initial<final,"WEBA_AUDIT_SHIFT_INTERVAL_INVALID")
        selected[name]={
            "metadata_shift_start_local_wall_clock":start.isoformat(),
            "metadata_shift_end_local_wall_clock":end.isoformat(),
            "start_clock_original_format":start_fmt,
            "end_clock_original_format":end_fmt,
            "shift_start_utc_under_Budapest_assumption":initial.isoformat(),
            "shift_end_utc_under_Budapest_assumption":final.isoformat(),
            "interval_for_audit_only":(initial,final),
        }
    need(set(selected)==set(SHIFTS),
         "WEBA_AUDIT_SELECTED_SHIFT_METADATA_ABSENT")
    return selected,counts["nonempty_rows"]


def tapo_log_audit(shift,text,bounds):
    """Read ten snapshot responses, not a continuous or complete log."""
    source_report=source.parse_tapo_text(text)
    dump_stamps=[datetime.fromisoformat(x.replace("Z","+00:00"))
                 for x in DUMP_RE.findall(text)]
    need(dump_stamps and all(x.tzinfo is not None for x in dump_stamps),
         "WEBA_AUDIT_TAPO_DUMP_CLOCK_MISSING")
    # One "last 50" response per sensor in these frozen log files.
    blocks=list(source.TAPO_SENSOR_RE.finditer(text))
    need(len(blocks)==source_report["sensor_count"]==10,
         "WEBA_AUDIT_TAPO_BLOCK_COUNT_CHANGED")
    start,end=bounds["interval_for_audit_only"]
    sensor_rows={}
    total=0
    over50=0
    before=within=after=0
    all_times=[]
    for m in blocks:
        name=m.group(2)
        matches=list(source.TAPO_EVENT_RE.finditer(m.group(5)))
        events=[(x.group(1),int(x.group(2)),int(x.group(3)))
                for x in matches]
        times=[datetime.fromtimestamp(t,UTC) for _,_,t in events]
        ids=[number for _,number,_ in events]
        need(len(ids)==len(set(ids)),
             "WEBA_AUDIT_DUPLICATE_VENDOR_IDS")
        need(all(a>=b for a,b in zip(times,times[1:])),
             "WEBA_AUDIT_NONREVERSE_CHRONOLOGICAL_TAPO")
        need(int(m.group(4))==len(events),
             "WEBA_AUDIT_REPORTED_RESPONSE_COUNT_DIFFERS")
        total+=len(events)
        if len(events)>50:
            over50+=1
        earlier=sum(t<start for t in times)
        inside=sum(start<=t<end for t in times)
        later=sum(t>=end for t in times)
        before+=earlier;within+=inside;after+=later
        all_times.extend(times)
        max_silence=max((int((a-b).total_seconds())
                        for a,b in zip(times,times[1:])),default=None)
        # Gaps between device IDs are NOT a count of dropped events:
        # IDs can have different internal semantics.
        nonunit=sum(a-b!=1 for a,b in zip(ids,ids[1:]))
        sensor_rows[name]={
            "events_returned":len(events),
            "reported_sum_equals_returned_records":True,
            "response_contains_more_than_label_last_50":len(events)>50,
            "first_event_utc":min(times).isoformat() if times else None,
            "last_event_utc":max(times).isoformat() if times else None,
            "events_before_assumed_shift_boundary":earlier,
            "events_inside_assumed_shift_boundary":inside,
            "events_after_assumed_shift_boundary":later,
            "max_gap_between_RECORDS_seconds_NOT_OUTAGE":max_silence,
            "nonunit_vendor_id_steps_NOT_MISSING_EVENT_COUNT":nonunit,
            "no_vendor_id_duplicate_in_this_snapshot":True,
            "no_heartbeat_continuous_coverage_proven":True,
        }
    need(total==source_report["total_returned_tapo_events"] and
         before+within+after==total,"WEBA_AUDIT_TAPO_EVENT_MASS_LOST")
    need(all(t<=max(dump_stamps) for t in all_times),
         "WEBA_AUDIT_EVENT_LATER_THAN_EXPORT")
    return {
        "Tapo_source_text_has_UTF8_BOM_or_indented_log_lines":
            text.startswith("\ufeff") or any(x.startswith(" ") for x in text.splitlines()[:3]),
        "Tapo_snapshot_time_utc_first":min(dump_stamps).isoformat(),
        "Tapo_snapshot_time_utc_last":max(dump_stamps).isoformat(),
        "Tapo_earliest_recorded_event_utc":min(all_times).isoformat(),
        "Tapo_latest_recorded_event_utc":max(all_times).isoformat(),
        "source_log_contains_ONE_query_per_sensor":True,
        "source_text_says_last_50_but_response_may_contain_more":True,
        "sensors_over_50_returned_records":over50,
        "sensor_group_count":len(blocks),
        "total_events_in_snapshot":total,
        "events_before_assumed_recording_shift":before,
        "events_inside_assumed_recording_shift":within,
        "events_after_assumed_recording_shift":after,
        "per_sensor_summary":sensor_rows,
        "snapshot_consistency_passed":True,
        "not_verified_capture_completeness":True,
        "vendor_ID_gaps_not_interpretable_as_missing_count":True,
        "lack_of_pulses_not_a_proof_of_sensor_availability":True,
        "Tapo_event_clock_calibrated_against_POS":False,
    }


def build(pos,shift_summary,logs):
    verified=verify_inputs(pos,shift_summary,logs)
    pos_observation=pos_clock_audit(pos)
    bounds,n_meta=shift_boundaries(shift_summary)
    shift_reports={}
    for shift in SHIFTS:
        b=bounds[shift]
        shift_reports[shift]={
            "start_clock_local":b["metadata_shift_start_local_wall_clock"],
            "end_clock_local":b["metadata_shift_end_local_wall_clock"],
            "source_shift_start_clock_encoding":b["start_clock_original_format"],
            "source_shift_end_clock_encoding":b["end_clock_original_format"],
            "UTC_boundaries_under_UNVERIFIED_local_clock_assumption":[
                b["shift_start_utc_under_Budapest_assumption"],
                b["shift_end_utc_under_Budapest_assumption"]],
            "Tapo":tapo_log_audit(shift,logs[shift].decode("utf-8"),b),
        }
    return {
        "schema":SCHEMA,
        "source_WEBA_scientific_data_doi":"10.1038/s41597-024-04348-z",
        "upstream_git_commit":STUDY_SAME_GIT_COMMIT,
        "shift_selection":list(SHIFTS),
        "source_file_digests":verified,
        "source_analyzed_after_all_3_shifts_previously_inspected":True,
        "not_a_blind_or_prospective_validation":True,
        "POS":pos_observation,
        "shift_metadata_workbook_nonempty_rows":n_meta,
        "shift_metadata_time_fields_used_without_participant_columns":True,
        "source_article_table9_documents_order_time_as_12h_clock_not_timezone":True,
        "source_article_order_date_format_differs_from_raw_YYYYMMDD":True,
        "Tapo_logs_are_retrospective_single_snapshot_not_live_heartbeat":True,
        "Tapo_continuous_service_coverage_ESTABLISHED":False,
        "POS_and_Tapo_synchronized_ESTABLISHED":False,
        "shift_and_event_clocks_assumed_not_calibrated":True,
        "no_per_order_service_finish_or_customer_arrival_reconstructed":True,
        "no_individual_order_sensor_or_participant_identifiers_exported":True,
        "no_patient_heart_rate_wearable_questionnaires_loaded":True,
        "shifts":shift_reports,
        "D_B_M_unchanged":True,
        "F5_independent_reserve":"NOT_CREATED",
        "G4":"NOT_RUN","G5":"NOT_RUN",
        "provider_calls":0,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--pos",required=True,type=Path)
    p.add_argument("--shift-summary",required=True,type=Path)
    p.add_argument("--tapo-20240223",required=True,type=Path)
    p.add_argument("--tapo-20240304",required=True,type=Path)
    p.add_argument("--tapo-20240308",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    need(not args.out.exists(),"WEBA_AUDIT_REFUSE_OVERWRITE")
    res=build(args.pos.read_bytes(),args.shift_summary.read_bytes(),{
        "20240223_evening":args.tapo_20240223.read_bytes(),
        "20240304_evening":args.tapo_20240304.read_bytes(),
        "20240308_evening":args.tapo_20240308.read_bytes(),
    })
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_bytes(canonical(res)+b"\n")
    print(json.dumps({
        "Tapo_total":[res["shifts"][s]["Tapo"]["total_events_in_snapshot"]
                      for s in SHIFTS],
        "events_outside_shift_before":[
            res["shifts"][s]["Tapo"]["events_before_assumed_recording_shift"]
            for s in SHIFTS],
        "POS_timezone_verified":res["POS_and_Tapo_synchronized_ESTABLISHED"],
        "G5":res["G5"],
    },sort_keys=True))


if __name__=="__main__":
    main()
