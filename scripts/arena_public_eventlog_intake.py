#!/usr/bin/env python3
"""ARENA EV03 — streaming public/authorized XES audit.

This module audits externally produced *recorded* events, not physical
mechanisms. Case IDs, activities, resources, traces and raw data never escape
the parser. Uses defusedxml for safe XML streaming.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import gzip
from hashlib import sha256
from pathlib import Path

from defusedxml import ElementTree as SafeET

SCHEMA="igc-arena-ev03-public-event-log-audit/0.1"
GATE="BLOCKED_REAL_BUSINESS_INSTRUMENTATION_AND_PHYSICAL_SEMANTICS_NOT_VALIDATED"
MAX_COMPRESSED_BYTES=64*1024*1024
MAX_DECOMPRESSED_BYTES=512*1024*1024
MAX_EVENTS=500000
MAX_CASES=30000
MAX_DISTINCT_ACTIVITIES=3000
REQUIRED_SOURCE_DOCUMENTATION=(
    "source_authorization_and_purpose",
    "retention_and_deletion_policy",
    "event_semantics_dictionary",
    "case_identity_linkage_provenance",
    "timestamp_zone_resolution_and_clock_status",
    "personal_data_minimization_plan",
    "physical_event_mapping_validation",
)


def require(ok,code):
    if not ok: raise ValueError(code)


def local_name(tag):
    return str(tag).rsplit("}",1)[-1]


def parse_aware(raw):
    require(type(raw) is str and "T" in raw,
            "EV03_TIMESTAMP_MALFORMED")
    try:
        dt=datetime.fromisoformat(
            raw[:-1]+"+00:00" if raw.endswith("Z") else raw)
    except ValueError as e:
        raise ValueError("EV03_TIMESTAMP_MALFORMED") from e
    require(dt.tzinfo is not None and dt.utcoffset() is not None,
            "EV03_TIMESTAMP_NO_OFFSET")
    return dt.astimezone(timezone.utc)


def file_sha256(path):
    h=sha256()
    with open(path,"rb") as src:
        for chunk in iter(lambda:src.read(1024*1024),b""):
            h.update(chunk)
    return "sha256:"+h.hexdigest()


class LimitedReader:
    def __init__(self,underlying,byte_limit):
        self.stream=underlying
        self.bytes=0
        self.limit=byte_limit
    def read(self,size=-1):
        # XML iterparse should use bounded reads. Always refuse reads that
        # would conceal more than the declared cap.
        if size is None or size<0:
            size=min(65536,self.limit-self.bytes+1)
        if self.bytes>=self.limit:
            chunk=self.stream.read(1)
            require(not chunk,"EV03_DECOMPRESSED_BYTE_LIMIT")
            return chunk
        chunk=self.stream.read(min(size,self.limit-self.bytes+1))
        self.bytes+=len(chunk)
        require(self.bytes<=self.limit,"EV03_DECOMPRESSED_BYTE_LIMIT")
        return chunk


def audit_xes_file(filename,origin,compressed_limit=MAX_COMPRESSED_BYTES,
                   plain_limit=MAX_DECOMPRESSED_BYTES):
    """Memory-bounded XES/XES.gz parser; only aggregated quality metadata exits.

    Timestamp start/complete in the source is NOT proof of physical service.
    Raw XES is never copied or exported; integrity digest binds received bytes.
    """
    path=Path(filename)
    require(path.is_file() and path.stat().st_size>0,"EV03_SOURCE_FILE_MISSING")
    require(path.suffix in (".xes",".gz") and
            (path.suffix!=".gz" or path.name.endswith(".xes.gz")),
            "EV03_UNSUPPORTED_SOURCE_EXTENSION")
    require(0<path.stat().st_size<=compressed_limit,"EV03_COMPRESSED_BYTE_LIMIT")
    require(isinstance(origin,str) and origin.startswith("https://")
            and len(origin)<=1024,"EV03_SOURCE_PROVENANCE_REQUIRED")
    digest=file_sha256(path)
    values={
        "n_traces":0,"n_events":0,"events_with_activity":0,
        "events_with_valid_aware_timestamp":0,"events_missing_activity":0,
        "events_missing_timestamp":0,"events_bad_timestamp":0,
        "events_without_timezone":0,"events_with_resource_field":0,
        "events_with_lifecycle":0,"cases_with_missing_or_invalid_event_timestamp":0,
        "cases_with_recorded_timestamp_reverse_order":0,
        "cases_with_two_or_more_valid_times":0,
        "cases_with_complete_recorded_timestamps":0,
        "cases_with_observed_first_last_span":0,
    }
    lifecycle=Counter()
    distinct_activities=set()
    case_event_count=0
    case_valid_times=0
    case_bad_times=0
    case_reverse=False
    previous=None
    first=None
    last=None

    # DTD and external entities forbidden by defusedxml, even far into file.
    with path.open("rb") as raw:
        source=gzip.GzipFile(fileobj=raw,mode="rb") if path.name.endswith(".gz") else raw
        stream=LimitedReader(source,plain_limit)
        try:
            for action,element in SafeET.iterparse(
                stream,events=("end",),
                forbid_dtd=True,forbid_entities=True,forbid_external=True,
            ):
                label=local_name(element.tag)
                if label=="event":
                    values["n_events"]+=1
                    require(values["n_events"]<=MAX_EVENTS,"EV03_EVENT_LIMIT")
                    case_event_count+=1
                    attrs={}
                    for child in element:
                        if local_name(child.tag) in ("string","date","int","float","boolean"):
                            key=child.attrib.get("key")
                            if key in ("concept:name","time:timestamp",
                                       "lifecycle:transition","org:resource"):
                                attrs[key]=child.attrib.get("value")
                    activity=attrs.get("concept:name")
                    if activity:
                        values["events_with_activity"]+=1
                        distinct_activities.add(activity)
                        require(len(distinct_activities)<=MAX_DISTINCT_ACTIVITIES,
                                "EV03_DISTINCT_ACTIVITY_LIMIT")
                    else:
                        values["events_missing_activity"]+=1
                    if attrs.get("org:resource"):
                        values["events_with_resource_field"]+=1
                    life=attrs.get("lifecycle:transition")
                    if life:
                        values["events_with_lifecycle"]+=1
                        tag=life.upper()
                        lifecycle[tag if tag in ("START","COMPLETE","SCHEDULE") else
                                  "OTHER_DECLARED"]+=1
                    time=attrs.get("time:timestamp")
                    if not time:
                        values["events_missing_timestamp"]+=1
                        case_bad_times+=1
                    else:
                        try:
                            dt=parse_aware(time)
                        except ValueError as exc:
                            if str(exc)=="EV03_TIMESTAMP_NO_OFFSET":
                                values["events_without_timezone"]+=1
                            else:
                                values["events_bad_timestamp"]+=1
                            case_bad_times+=1
                        else:
                            values["events_with_valid_aware_timestamp"]+=1
                            case_valid_times+=1
                            if previous is not None and dt<previous:
                                case_reverse=True
                            previous=dt
                            first=dt if first is None else first
                            last=dt
                    element.clear()
                elif label=="trace":
                    values["n_traces"]+=1
                    require(values["n_traces"]<=MAX_CASES,"EV03_TRACE_LIMIT")
                    if case_bad_times:
                        values["cases_with_missing_or_invalid_event_timestamp"]+=1
                    if case_reverse:
                        values["cases_with_recorded_timestamp_reverse_order"]+=1
                    if case_valid_times>=2:
                        values["cases_with_two_or_more_valid_times"]+=1
                    if case_event_count>=2 and case_bad_times==0:
                        values["cases_with_complete_recorded_timestamps"]+=1
                        if not case_reverse:
                            values["cases_with_observed_first_last_span"]+=1
                    case_event_count=case_valid_times=case_bad_times=0
                    case_reverse=False
                    previous=first=last=None
                    element.clear()
        finally:
            if source is not raw:
                source.close()
    require(values["n_traces"]>0 and values["n_events"]>0,
            "EV03_EMPTY_LOG")
    require(case_event_count==0,"EV03_EVENTS_OUTSIDE_TRACES")
    require(values["events_with_valid_aware_timestamp"]+
            values["events_missing_timestamp"]+
            values["events_bad_timestamp"]+
            values["events_without_timezone"]==values["n_events"],
            "EV03_TIMESTAMP_ACCOUNTING")
    return {
        "schema":SCHEMA,"source_documented_url":origin,
        "received_file_sha256":digest,
        "received_file_size_bytes":path.stat().st_size,
        "received_xml_bytes_bounded_by":plain_limit,
        "summary":values,
        "n_distinct_activities":len(distinct_activities),
        "lifecycle_count_by_coarse_tag":dict(sorted(lifecycle.items())),
        "real_event_log_does_not_validate_physical_service":True,
        "event_resource_values_not_exported":True,
        "case_ids_and_activity_labels_not_exported":True,
        "case_cycle_is_not_physical_service_duration":True,
        "can_infer_hidden_stages":False,
        "can_estimate_cafe_capacity":False,
        "observed_first_last_span_is_not_total_process_duration":True,
        "source_integrity_level":"SOURCE_VERSION_PINNED_BYTES_NOT_PRECOMMITTED",
        "status":"PUBLIC_OPERATIONAL_EVENTLOG_SCHEMA_AUDITED_NOT_PHYSICAL_VALIDATED",
        "gate":GATE,
    }


def readiness_gate(documentation):
    """Portable intake contract; NEVER infer authorization from a downloaded log."""
    require(isinstance(documentation,dict),"EV03_DOCUMENTATION_REQUIRED")
    statuses={}
    for key in REQUIRED_SOURCE_DOCUMENTATION:
        v=documentation.get(key)
        statuses[key]=(
            "DOCUMENTED_UNVERIFIED" if isinstance(v,str) and
            len(v.strip())>=12 else "MISSING_OR_INADEQUATE"
        )
    return {
        "required":statuses,
        "all_fields_supplied":all(v=="DOCUMENTED_UNVERIFIED"
                                  for v in statuses.values()),
        "physical_service_inference_authorized":False,
        "data_use_authorization_independently_verified":False,
        "clock_independently_validated":False,
        "next_gate":"INDEPENDENT_REVIEW_OF_SOURCE_AND_CLOCK_REQUIRED",
    }
