#!/usr/bin/env python3
"""ARENA EV-02. Fail-closed CSV event ingestion with source semantics.

No model, simulation, process-mining or network imports. Pseudonyms derived
from a caller-owned secret are NOT a substitute for privacy/legal safeguards.
Administrative timestamps are NEVER silently promoted to physical service.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from io import StringIO
from typing import Mapping

SCHEMA="igc-arena-ev02-operational-records/0.1"
GATE="BLOCKED_SYNTHETIC_EXTERNAL_FORMAT_NO_REAL_POS_KDS_CRM_DATA_OR_CLOCK_VALIDATION"
FIELDS_COMMON=frozenset(("event_id","action","occurred_at","clock_id"))
ACTION_MAP={
    "pos_export_v1":{
        "created":"order_created","paid":"payment_recorded",
        "handed_off":"delivery_recorded"},
    "kds_export_v1":{
        "prep_started":"preparation_started_admin",
        "prep_done":"preparation_completed_admin"},
    "crm_export_v1":{
        "created":"lead_created","qualified":"lead_qualified",
        "demo_requested":"demo_requested","demo_booked":"demo_booked",
        "lost":"lead_lost"},
}
ENTITY_FIELD={"pos_export_v1":"order_id","kds_export_v1":"order_id",
              "crm_export_v1":"lead_id"}
SEMAN="administrative_milestone"
QUALITY_MAX_ROWS=10000


def need(ok,code):
    if not ok:
        raise ValueError(code)


@dataclass(frozen=True)
class SourceSpec:
    profile:str
    source_system:str
    case_namespace:str
    clock_id:str
    clock_status:str
    timestamp_accuracy_ms:int|None
    evidence_ref:str

    def __post_init__(self):
        need(self.profile in ACTION_MAP,"EV02_UNKNOWN_SOURCE_PROFILE")
        need(all(isinstance(x,str) and x and len(x)<=160 for x in (
            self.source_system,self.case_namespace,self.clock_id,
            self.evidence_ref)),"EV02_SOURCE_PROVENANCE_REQUIRED")
        need(self.clock_status in ("verified_utc_sync","unverified"),
             "EV02_BAD_CLOCK_STATUS")
        need(self.timestamp_accuracy_ms is None or
             (type(self.timestamp_accuracy_ms) is int
              and self.timestamp_accuracy_ms>=0),
             "EV02_BAD_CLOCK_ACCURACY")
        if self.clock_status=="verified_utc_sync":
            need(self.timestamp_accuracy_ms is not None,
                 "EV02_VERIFIED_CLOCK_REQUIRES_ACCURACY")

    @property
    def declared_clock_reliable(self):
        return (self.clock_status=="verified_utc_sync" and
                self.timestamp_accuracy_ms is not None and
                self.timestamp_accuracy_ms<=1)


def required_columns(profile):
    need(profile in ACTION_MAP,"EV02_UNKNOWN_SOURCE_PROFILE")
    return FIELDS_COMMON|{ENTITY_FIELD[profile]}


def validate_secret(secret):
    need(type(secret) is bytes and len(secret)>=32,
         "EV02_PRIVATE_PSEUDONYM_SECRET_REQUIRED")


def pseudonym(secret,*parts):
    validate_secret(secret)
    msg=b"IGC_EV02_PSEUDONYM\x00"+secret+b"\x00"+
        b"\x00".join(str(x).encode("utf-8") for x in parts)
    return "p_"+sha256(msg).hexdigest()[:32]


def parse_timestamp(raw):
    need(isinstance(raw,str) and "T" in raw and len(raw)>=20,
         "EV02_TIMESTAMP_NOT_EXPLICIT_ISO")
    # Python fromisoformat will validate calendar dates, offsets and seconds.
    try:
        value=datetime.fromisoformat(raw[:-1]+"+00:00" if raw.endswith("Z") else raw)
    except ValueError as exc:
        raise ValueError("EV02_INVALID_TIMESTAMP") from exc
    need(value.tzinfo is not None and value.utcoffset() is not None,
         "EV02_TIMESTAMP_HAS_NO_UTC_OFFSET")
    return value.astimezone(timezone.utc)


def utc_iso(value):
    return value.isoformat(timespec="microseconds").replace("+00:00","Z")


def ingest_csv(body,spec,secret):
    """Strict schema, row-level quarantine, no raw identifiers in results."""
    validate_secret(secret)
    need(isinstance(body,str) and bool(body.strip()),"EV02_EMPTY_FILE")
    need(isinstance(spec,SourceSpec),"EV02_UNDECLARED_SOURCE")
    source_digest="sha256:"+sha256(body.encode("utf-8")).hexdigest()
    reader=csv.DictReader(StringIO(body,newline=""))
    headers=reader.fieldnames
    need(headers is not None and len(set(headers))==len(headers) and
         set(headers)==required_columns(spec.profile),
         "EV02_FILE_SCHEMA_REJECTED")
    accepted=[]
    quarantined=[]
    seen=set()
    for row_idx,row in enumerate(reader,start=2):
        need(row_idx<=QUALITY_MAX_ROWS+1,"EV02_FILE_ROW_BUDGET")
        reason=None
        if None in row or set(row)!=set(headers):
            reason="ROW_FIELD_COUNT_MISMATCH"
        elif any(v is None for v in row.values()):
            reason="ROW_MISSING_FIELD"
        elif not all(isinstance(v,str) and v.strip()
                     for v in row.values()):
            reason="ROW_EMPTY_REQUIRED_FIELD"
        elif row["clock_id"]!=spec.clock_id:
            reason="ROW_UNDECLARED_CLOCK"
        elif row["action"] not in ACTION_MAP[spec.profile]:
            reason="ROW_UNMAPPED_ACTION"
        elif row["event_id"] in seen:
            reason="ROW_DUPLICATE_EVENT_ID"
        else:
            try:
                dt=parse_timestamp(row["occurred_at"])
            except ValueError as exc:
                reason=str(exc)
        # Duplicated IDs are rejected even if the first instance is invalid
        # so the data source cannot launder one ID by changing its payload.
        if isinstance(row.get("event_id"),str) and row["event_id"]:
            seen.add(row["event_id"])
        if reason is not None:
            quarantined.append({"row_number":row_idx,"code":reason,
                                "source_profile":spec.profile})
            continue
        accepted.append({
            "schema":SCHEMA,
            "source_profile":spec.profile,
            "source_system":spec.source_system,
            "source_digest":source_digest,
            "evidence_ref":spec.evidence_ref,
            "case_namespace":spec.case_namespace,
            "case_ref":pseudonym(secret,"case",spec.case_namespace,
                                 row[ENTITY_FIELD[spec.profile]]),
            "source_record_ref":pseudonym(secret,"record",spec.source_system,
                                         spec.profile,row["event_id"]),
            "activity":ACTION_MAP[spec.profile][row["action"]],
            "event_semantics":SEMAN,
            "timestamp_raw":row["occurred_at"],
            "observed_at_utc":utc_iso(dt),
            "clock_id":spec.clock_id,
            "clock_status_declared":spec.clock_status,
            "clock_accuracy_ms_declared":spec.timestamp_accuracy_ms,
            "actual_physical_instant_verified":False,
            "clock_validation_independently_verified":False,
            "time_precision":"microseconds_or_lower_as_recorded",
        })
    accepted.sort(key=lambda x:(
        x["case_ref"],x["observed_at_utc"],x["source_system"],
        x["source_record_ref"]))
    return {
        "schema":SCHEMA,"profile":spec.profile,
        "source_system":spec.source_system,
        "source_digest":source_digest,
        "case_namespace":spec.case_namespace,
        "clock_status_declared":spec.clock_status,
        "clock_accuracy_ms_declared":spec.timestamp_accuracy_ms,
        "evidence_ref":spec.evidence_ref,
        "events":accepted,"quarantine":quarantined,
        "n_accepted":len(accepted),"n_quarantined":len(quarantined),
        "data_is_not_physically_validated":True,
        "no_raw_identifier_fields_retained":True,
    }


def single(events,activity):
    hits=[x for x in events if x["activity"]==activity]
    if len(hits)!=1:
        return None
    return parse_timestamp(hits[0]["observed_at_utc"])


def iso_duration_seconds(a,z):
    from decimal import Decimal
    dt=z-a
    need(dt.total_seconds()>=0,"EV02_INVALID_NEGATIVE_DURATION")
    return str(Decimal(dt.days*86400+dt.seconds)+Decimal(dt.microseconds)/Decimal(1000000))


def summarize_cases(batches):
    """Labels only intervals from actual recorded endpoints, never hidden work.

    Cross-source intervals require EXPLICIT trusted and accurate clock
    attestations. Matching UTC offsets alone never establish synchronization.
    """
    need(isinstance(batches,(tuple,list)) and 1<=len(batches)<=3,
         "EV02_BAD_BATCH_SET")
    profile_names=[b["profile"] for b in batches]
    need(len(set(profile_names))==len(profile_names),
         "EV02_DUPLICATE_SOURCE_PROFILE")
    events=[ev for batch in batches for ev in batch["events"]]
    by_case={}
    for x in events:
        by_case.setdefault((x["case_namespace"],x["case_ref"]),[]).append(x)
    specs={b["profile"]:b for b in batches}
    output=[]
    for (namespace,case),rows in sorted(by_case.items()):
        activities=[x["activity"] for x in rows]
        kind="crm" if namespace.startswith("crm:") else "order"
        result={
            "case_namespace":namespace,"case_ref":case,
            "n_recorded_events":len(rows),
            "case_kind_declared":kind,
            "activities_recorded":sorted(activities),
            "physical_queue_wait_identified":False,
            "physical_service_time_identified":False,
            "hidden_stage_inferred":False,
            "case_quality_flags":[],
        }
        if kind=="crm":
            result.update({
                "cycle_status":"NOT_APPLICABLE_TO_CRM_ORDER_CYCLE",
                "admin_interval_status":"NOT_A_PHYSICAL_SERVICE_INTERVAL",
                "cross_source_status":"NOT_APPLICABLE",
            })
        else:
            created=single(rows,"order_created")
            paid=single(rows,"payment_recorded")
            delivered=single(rows,"delivery_recorded")
            prep_start=single(rows,"preparation_started_admin")
            prep_end=single(rows,"preparation_completed_admin")
            if created is None or paid is None or delivered is None:
                result["cycle_status"]="UNRESOLVED_INCOMPLETE_LIFECYCLE"
                result["case_quality_flags"].append("MISSING_OR_DUPLICATE_POS_MILESTONE")
            elif not(created<=paid<=delivered):
                result["cycle_status"]="BLOCKED_INCONSISTENT_POS_TIME"
                result["case_quality_flags"].append("INVALID_POS_ORDER")
            else:
                result["cycle_status"]="RECORDED_ADMIN_CYCLE_NOT_PHYSICAL_SOJOURN"
                result["pos_admin_cycle_seconds"]=iso_duration_seconds(created,delivered)
            if prep_start is None or prep_end is None:
                result["admin_interval_status"]="UNRESOLVED_MISSING_KDS_PAIR"
            elif prep_end<prep_start:
                result["admin_interval_status"]="BLOCKED_INCONSISTENT_KDS_TIME"
                result["case_quality_flags"].append("INVALID_KDS_ORDER")
            else:
                result["admin_interval_status"]="RECORDED_KDS_CLICK_INTERVAL_NOT_PHYSICAL_SERVICE"
                result["kds_click_interval_seconds"]=iso_duration_seconds(prep_start,prep_end)
            pos=specs.get("pos_export_v1")
            kds=specs.get("kds_export_v1")
            reliable=bool(pos and kds and
                 pos["clock_status_declared"]=="verified_utc_sync" and
                 kds["clock_status_declared"]=="verified_utc_sync" and
                 pos["clock_accuracy_ms_declared"] is not None and
                 kds["clock_accuracy_ms_declared"] is not None and
                 pos["clock_accuracy_ms_declared"]<=1 and
                 kds["clock_accuracy_ms_declared"]<=1 and
                 pos["case_namespace"]==kds["case_namespace"])
            if not reliable:
                result["cross_source_status"]="CROSS_SOURCE_TEMPORAL_COMPARISON_BLOCKED"
            elif None in (created,delivered,prep_start,prep_end) or not(
                    created<=prep_start<=prep_end<=delivered):
                result["cross_source_status"]="BLOCKED_INCONSISTENT_OR_MISSING_EVENT_CHAIN"
                result["case_quality_flags"].append("CROSS_SOURCE_EVENT_CHAIN_INVALID")
            elif result["cycle_status"].startswith("BLOCKED") or (
                    result["admin_interval_status"].startswith("BLOCKED")):
                result["cross_source_status"]="BLOCKED_INCONSISTENT_OR_MISSING_EVENT_CHAIN"
            else:
                result["cross_source_status"]="RECORDED_CROSS_SOURCE_ELAPSED_NOT_PHYSICAL_SERVICE"
                result["prep_click_end_to_delivery_click_seconds"]=iso_duration_seconds(
                    prep_end,delivered)
                result["cross_source_clock_assurance"]="DECLARED_ONLY_NOT_INDEPENDENTLY_VALIDATED"
        output.append(result)
    return {
        "schema":SCHEMA,
        "n_cases":len(output),
        "n_recorded_events":len(events),
        "n_quarantined":sum(b["n_quarantined"] for b in batches),
        "cases":output,
        "no_mechanism_discovery_from_click_timestamps":True,
        "no_timing_claims_from_unsupported_endpoints":True,
        "gate":GATE,
    }
