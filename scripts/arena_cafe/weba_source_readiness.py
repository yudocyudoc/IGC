"""WEBA first REAL, external-source readiness audit: POS + one Tapo log.

This is intentionally not an F5 service-finish observation operator.
Inputs: *only* pinned orders_summary.xlsx and one pinned 3.logs.txt from
the public WEBA study. Excludes participant data, HR, questionnaires,
wearable acceleration, and coffee-machine raw signal. No inferred client
arrival, case-level station activity, physical completion or shared clock.

The report is aggregate-only and cannot pass G4/G5 or authorize O2.
Upstream data is downloaded at CI runtime, pinned by Git blob SHA-1 and
size; never committed or uploaded as an artifact.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
import argparse
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

from scripts.arena_v0_contract import canonical

SCHEMA="igc-weba-real-source-pos-tapo-audit/0.1"
UPSTREAM_REPO="Department-of-System-Engineering/datasets_WEBA"
UPSTREAM_COMMIT="d6841669e544579547c94b7ce1e8613bbd6b3a39"
SHIFT_ID="20240223_evening"
SOURCE_FILES={
    "pos":{
        "path":"B.shift_data/orders_summary.xlsx",
        "size_bytes":58322,
        "git_blob_sha1":"a7f10b818402884255a3f6390da59b34a4ccdec2",
    },
    "tapo":{
        "path":f"B.shift_data/{SHIFT_ID}/3.logs.txt",
        "size_bytes":45209,
        "git_blob_sha1":"dc98f6b68eeebf7544d1981e825e3fb26129face",
    },
}
EXPECTED_SENSORS=("front_door","front_door_m","zone_1","zone_2")
TAPO_SENSOR_RE=re.compile(
    r"Found (T\d{3}) child device with nickname: ([A-Za-z0-9_-]+),"
    r"[^\n]*?last 50 trigger logs: TriggerLogsResult"
    r" \{ start_id: (\d+), sum: (\d+), logs: \[([^\n]*?)\] \}"
)
TAPO_EVENT_RE=re.compile(
    r"\b(Open|Close|KeepOpen|Motion) \{ id: (\d+), timestamp: (\d+) \}"
)
MAIN="{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def need(ok,code):
    if not ok:
        raise ValueError(code)


def verify_pinned(name,bytes_):
    need(name in SOURCE_FILES and type(bytes_) is bytes,
         "WEBA_UNAUTHORIZED_SOURCE")
    meta=SOURCE_FILES[name]
    sha=hashlib.sha1(
        f"blob {len(bytes_)}\0".encode("ascii")+bytes_).hexdigest()
    need(len(bytes_)==meta["size_bytes"] and
         sha==meta["git_blob_sha1"],
         "WEBA_SOURCE_NOT_PINNED_GIT_BLOB")
    return {
        "upstream_path":meta["path"],
        "git_blob_sha1":sha,
        "sha256":"sha256:"+hashlib.sha256(bytes_).hexdigest(),
        "bytes":len(bytes_),
    }


def parse_tapo_text(text):
    """Parse ALL Tapo variants (including KeepOpen), retain no device IDs."""
    need(type(text) is str and
         "TriggerLogsResult" in text,
         "WEBA_TAPO_NOT_RAW_SENSOR_LOG")
    blocks=list(TAPO_SENSOR_RE.finditer(text))
    declared=text.count("last 50 trigger logs: TriggerLogsResult")
    need(bool(blocks) and len(blocks)==declared,
         "WEBA_TAPO_SENSOR_BLOCK_PARSE_INCOMPLETE")
    seen=set()
    aggregated=[]
    earliest=[]
    latest=[]
    for m in blocks:
        model,nickname,_,stated_count,raw=m.groups()
        need(nickname not in seen,"WEBA_TAPO_DUPLICATED_SENSOR")
        seen.add(nickname)
        matches=list(TAPO_EVENT_RE.finditer(raw))
        unparsed=TAPO_EVENT_RE.sub("",raw).strip(" ,\t\r")
        need(not unparsed,"WEBA_TAPO_UNPARSED_EVENT_TYPE")
        ev=[(kind,int(event_id),int(timestamp))
            for kind,event_id,timestamp in
            (hit.groups() for hit in matches)]
        need(len(ev)==len(set(x[1] for x in ev)),
             "WEBA_TAPO_DUPLICATE_EVENT_ID_IN_SENSOR_BLOCK")
        need(all(a[2]>=b[2] for a,b in zip(ev,ev[1:])),
             "WEBA_TAPO_TIMESTAMP_ORDER_UNEXPECTED")
        counts=dict(sorted(Counter(x[0] for x in ev).items()))
        if ev:
            earliest.append(min(x[2] for x in ev))
            latest.append(max(x[2] for x in ev))
        aggregated.append({
            "sensor_nickname":nickname,
            "sensor_model":model,
            "event_type_counts":counts,
            "returned_event_records":len(ev),
            "tapo_reported_sum":int(stated_count),
            "returned_equals_reported_sum":len(ev)==int(stated_count),
            "not_a_customer_count":True,
            "not_an_order_completion_event":True,
        })
    names=set(seen)
    need(set(EXPECTED_SENSORS).issubset(names),
         "WEBA_EXPECTED_AREAS_NOT_PRESENT")
    need(bool(earliest),"WEBA_NO_SENSOR_EVENTS")
    # UTC clock rendered only at aggregate level; POS clock is independent.
    to_utc=lambda t:datetime.fromtimestamp(t,timezone.utc).isoformat()
    total=sum(r["returned_event_records"] for r in aggregated)
    returns={r["sensor_nickname"]:r["returned_event_records"]
             for r in aggregated}
    return {
        "source_format":"TAPO_H100_HISTORICAL_TRIGGER_LOG_SNAPSHOT",
        "sensor_groups":aggregated,
        "sensor_count":len(aggregated),
        "total_returned_tapo_events":total,
        "returned_records_per_selected_sensor":{
            k:returns[k] for k in EXPECTED_SENSORS},
        "keepopen_events_retained":sum(
            x["event_type_counts"].get("KeepOpen",0)
            for x in aggregated),
        "earliest_sensor_event_utc":to_utc(min(earliest)),
        "latest_sensor_event_utc":to_utc(max(latest)),
        "source_log_contains_hub_snapshot_not_pos_events":True,
        "tapo_sensor_event_is_not_customer_arrival":True,
        "zone_motion_is_not_per_order_processing":True,
        "no_per_order_dispatch_finished_event_found":True,
        "tapo_returned_sum_not_independently_coverage_certified":True,
    }


def _cell_text(cell,shared):
    typ=cell.attrib.get("t","")
    if typ=="inlineStr":
        return "".join(n.text or "" for n in
                       cell.findall(".//"+MAIN+"t"))
    v=cell.find(MAIN+"v")
    raw= v.text if v is not None and v.text is not None else ""
    if typ=="s":
        try:
            return shared[int(raw)]
        except (ValueError,IndexError):
            raise ValueError("WEBA_POS_SHARED_STRING_INVALID") from None
    return raw


def _xlsx_rows(bytes_):
    """Minimal read-only XLSX ZIP/XML decoder; never reformats workbook."""
    from io import BytesIO
    with ZipFile(BytesIO(bytes_)) as z:
        names=set(z.namelist())
        need("xl/worksheets/sheet1.xml" in names,
             "WEBA_POS_MISSING_FIRST_WORKSHEET")
        shared=[]
        if "xl/sharedStrings.xml" in names:
            root=ET.fromstring(z.read("xl/sharedStrings.xml"))
            for entry in root.findall(MAIN+"si"):
                shared.append("".join(
                    x.text or "" for x in entry.iter(MAIN+"t")))
        root=ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
        rows=[]
        for row in root.iter(MAIN+"row"):
            mapping={}
            for c in row.findall(MAIN+"c"):
                ref=c.attrib.get("r","")
                letters=re.match(r"^[A-Z]+",ref)
                need(letters is not None,"WEBA_POS_CELL_REFERENCE_MALFORMED")
                n=0
                for ch in letters.group():
                    n=n*26+ord(ch)-64
                need(n not in mapping,"WEBA_POS_DUPLICATE_CELL")
                mapping[n]=_cell_text(c,shared)
            if mapping:
                rows.append(mapping)
        need(bool(rows),"WEBA_POS_NO_WORKSHEET_ROWS")
        return rows


def _normalize_date(s):
    if not s:
        return None
    s=s.strip()
    for fmt in ("%d/%m/%Y","%Y-%m-%d","%d-%m-%Y",
                "%Y/%m/%d","%m/%d/%Y"):
        try:
            return datetime.strptime(s,fmt).date().isoformat()
        except ValueError:
            pass
    try:
        n=float(s)
        if n>30000 and n<100000:
            return (datetime(1899,12,30)+timedelta(days=n)).date().isoformat()
    except ValueError:
        pass
    return None


def inspect_pos_xlsx(bytes_):
    """Only headers, counts and timestamp availability; no orders released."""
    rows=_xlsx_rows(bytes_)
    header_index=None
    for i,row in enumerate(rows[:15]):
        vals=[str(x).strip().lower() for x in row.values()]
        if "order_id" in vals and "order_time" in vals:
            header_index=i
            break
    need(header_index is not None,"WEBA_POS_EXPECTED_HEADERS_NOT_FOUND")
    header=rows[header_index]
    columns={str(v).strip().lower():index
             for index,v in header.items() if str(v).strip()}
    need({"order_id","order_time","order_date","time_of_day"}.issubset(
         set(columns)),"WEBA_POS_REQUIRED_COLUMNS_MISSING")
    records=rows[header_index+1:]
    valid=[r for r in records if
           any(str(v).strip() for v in r.values())]
    def val(r,key):
        return str(r.get(columns[key],"")).strip()
    known_time=[r for r in valid if val(r,"order_time")]
    day=[r for r in valid if
         _normalize_date(val(r,"order_date"))=="2024-02-23"]
    target=[r for r in day if
            val(r,"time_of_day").lower()=="evening"]
    timestamped=[r for r in target if val(r,"order_time")]
    # Do not release order ID, item detail, price, customer or raw timestamps.
    return {
        "first_worksheet_headers":sorted(columns.keys()),
        "source_has_order_id_field":True,
        "total_nonempty_order_rows":len(valid),
        "rows_with_nonempty_order_time":len(known_time),
        "rows_without_order_time":len(valid)-len(known_time),
        "rows_matching_selected_day":len(day),
        "rows_matching_selected_evening_shift":len(target),
        "selected_shift_rows_with_order_time":len(timestamped),
        "selected_shift_rows_without_order_time":len(target)-len(timestamped),
        "date_normalization_policy":"KNOWN_DMY_OR_YMD_STRINGS_OR_EXCEL_SERIAL",
        "order_time_values_not_exported":True,
        "pos_order_timestamp_is_NOT_physical_customer_arrival":True,
        "no_order_id_or_items_or_financial_values_exported":True,
    }


def build(pos_bytes,tapo_bytes):
    provenance={
        "pos":verify_pinned("pos",pos_bytes),
        "tapo":verify_pinned("tapo",tapo_bytes),
    }
    pos=inspect_pos_xlsx(pos_bytes)
    sensor=parse_tapo_text(tapo_bytes.decode("utf-8"))
    usable=pos["selected_shift_rows_with_order_time"]>0
    return {
        "schema":SCHEMA,
        "study":"WEBA_REAL_BUDAPEST_COFFEE_SHOP_55_SHIFTS",
        "study_doi":"10.1038/s41597-024-04348-z",
        "study_figshare_doi":"10.6084/m9.figshare.27186516.v3",
        "upstream_git_repo":UPSTREAM_REPO,
        "upstream_git_commit":UPSTREAM_COMMIT,
        "source_files_verified_by_git_blob_sha1_and_sha256":provenance,
        "sample_shift":SHIFT_ID,
        "sample_is_previously_inspected_DEVELOPMENT":True,
        "source_contains_real_external_measurement":True,
        "pos":pos,
        "tapo":sensor,
        "same_shift_pos_tapo_basic_presence_check":{
            "pos_timestamps_for_selected_shift_present":usable,
            "tapo_named_zones_present":True,
            "cross_clock_alignment_established":False,
            "customer_door_events_linked_to_order_ids":False,
            "machine_episodes_extracted":False,
            "physical_stage_completion_per_order_identified":False,
        },
        "raw_source_records_not_published":True,
        "participant_health_wearables_or_questionnaires_not_ingested":True,
        "device_identifiers_mac_ip_ssid_not_exported":True,
        "no_customer_arrival_or_preparation_dispatch_events_fabricated":True,
        "source_snapshot_does_NOT_establish_sensor_completeness":True,
        "eligible_as_independent_F5_dispatch_service_finish":"NO",
        "future_O2_authorized":"NO",
        "G4":"NOT_RUN","G5":"NOT_RUN","F5_reserve":"NOT_CREATED",
        "D_B_M_unchanged":True,
        "provider_calls":0,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--pos",required=True,type=Path)
    p.add_argument("--tapo",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    need(not args.out.exists(),"WEBA_REFUSE_REPORT_OVERWRITE")
    report=build(args.pos.read_bytes(),args.tapo.read_bytes())
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_bytes(canonical(report)+b"\n")
    print(json.dumps({
        "pos_rows":report["pos"]["total_nonempty_order_rows"],
        "selected_shift_timestamped_pos":report["pos"][
            "selected_shift_rows_with_order_time"],
        "tapo_sensors":report["tapo"]["sensor_count"],
        "tapo_events":report["tapo"]["total_returned_tapo_events"],
        "F5":report["F5_reserve"],
    },sort_keys=True))


if __name__=="__main__":
    main()
