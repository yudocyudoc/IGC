"""E00: direct hit bounds and bitemporal evidence revision on existing ledger/ATMS.

Direct hit values are documented transcriptions, NOT independent source verification.
The authoritative raw metric CSV is unmodified. No operational capacity inference.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import numpy as np

from scripts.arena_atms import events_from_ledger, project
from scripts.arena_memory import load_events_from_ledger, retrieve

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "hitos_directos_lineage.json"
NODES = ("H04", "H05", "H06", "H07")
CASE = "CAF_L001"
OLD = "L001:OLD_ANCHOR_INTERPRETATION"
NEW = "L001:REVISED_DIRECT_COTAS"
ANCHOR = "L001:ANNOTATION_ANCHOR_ASSUMPTION"
RULE = "L001:ANCHOR_SUPPORT_RULE"
KNOW = "L001:ANCHOR_KNOWLEDGE"


def load_direct_source(path=SOURCE):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != "igc-caf-l001-direct-hit-lineage/0.1":
        raise ValueError("DIRECT_SOURCE_SCHEMA_CHANGED")
    if data.get("extraction_status") != (
        "TRANSCRIBED_FROM_2026_11_05_PLAN_AND_ROADMAP_PRIMARY_EVENT_FILES_NOT_MOUNTED"
    ):
        raise ValueError("PRIMARY_SOURCE_VERIFICATION_NOT_ESTABLISHED")
    raw = data["hit_intervals_video_s"]
    if set(raw) != {"H01", *NODES}:
        raise ValueError("DIRECT_HIT_SET_CHANGED")
    anchor = float(data["h01_anchor_video_s"])
    if raw["H01"] != [anchor, anchor]:
        raise ValueError("DIRECT_ANCHOR_CHANGED")
    for name in NODES:
        pair = raw[name]
        if (not isinstance(pair,list) or len(pair)!=2 or
            not all(isinstance(x,(int,float)) and not isinstance(x,bool)
                    and np.isfinite(x) for x in pair) or
            not anchor <= pair[0] <= pair[1]):
            raise ValueError("BAD_DIRECT_HIT:"+name)
    if data["raw_metrics_sha256"] != (
        "f45e12578813f75ae6f201e5390f93e39bf115aed2849edd704072f09544fc28"
    ):
        raise ValueError("RAW_METRIC_LINEAGE_CHANGED")
    return data


def relative_direct_bounds(data=None):
    d = data if data is not None else load_direct_source()
    anchor = d["h01_anchor_video_s"]
    return {n: [round(v-anchor, 6) for v in d["hit_intervals_video_s"][n]]
            for n in NODES}


def direct_constraint_rows(data=None):
    """Physical hit bounds intersect differential F01-F09; no imputed time point."""
    raw = relative_direct_bounds(data)
    a, b = [], []
    for i, node in enumerate(NODES):
        lo, hi = raw[node]
        v = np.zeros(len(NODES)); v[i] = 1.0
        a.extend((v, -v)); b.extend((hi, -lo))
    return np.asarray(a), np.asarray(b)


def check_lineage(metrics, data=None):
    d = data if data is not None else load_direct_source()
    if len(d["master_revisions"]) != 2 or set(metrics) != {
        f"F{i:02d}" for i in range(1, 10)
    }:
        raise ValueError("REVISION_OR_METRIC_SET_CHANGED")
    for row in d["master_revisions"]:
        if row["new_metric"] not in ("F01","F08"):
            raise ValueError("WRONG_REVISION_METRIC")
        if row["new_bounds_s_video"] != metrics[row["new_metric"]]["bounds"]:
            raise ValueError("V2_DIRECT_METRIC_DIFFERENCE")
        old = row["old_bounds_s_video"]
        if not old[1] < row["new_bounds_s_video"][0]:
            raise ValueError("V1_V2_REVISION_RELATION_CHANGED")
    from hashlib import sha256
    from .reference import METRICS
    if sha256(METRICS.read_bytes()).hexdigest() != d["raw_metrics_sha256"]:
        raise ValueError("ORIGINAL_CSV_MUTATED")
    return {
        "status":"DOCUMENTED_MASTER_V1_TO_V2_REVISION_NOT_INDEPENDENT_CONTRADICTION",
        "master_v1_sha256":d["master_v1_sha256"],
        "master_v2_sha256":d["master_v2_sha256"],
        "revisions":d["master_revisions"],
        "primary_source_verification":"PENDING_PRIMARY_MASTER_AND_EVENT_EXPORT",
        "H07_relative_H01_video_s":relative_direct_bounds(d)["H07"],
    }


def write_temporal_revision(ledger, initial_time):
    """Record two knowledge revisions at distinct ingestion timestamps (not annotation dates)."""
    if isinstance(initial_time, str):
        t0 = datetime.fromisoformat(initial_time.replace("Z","+00:00"))
    else:
        t0 = initial_time
    if t0.tzinfo is None:
        raise ValueError("TIMEZONE_REQUIRED")
    t1 = t0 + timedelta(microseconds=1)
    stamps = [t.astimezone(timezone.utc).isoformat() for t in (t0,t1)]
    source=load_direct_source()
    revisions=[
        (ANCHOR, "ATMSNode", {
            "kind":"assumption","active":True,
            "assumption_type":"DOCUMENTED_ANNOTATION_PROVENANCE_NOT_VERIFIED_VISUALLY",
            "source_sha256":[source["master_v1_sha256"],source["master_v2_sha256"]],
        }, stamps[0], "anchor-source"),
        (RULE, "ATMSNode", {
            "kind":"justification","active":True,"antecedents":[ANCHOR],
            "consequent":OLD,"source_id":ANCHOR,
        }, stamps[0], "rule-v1"),
        (KNOW, "KnowledgeItem", {
            "kind":"knowledge","active":True,"node_id":OLD,"source_id":ANCHOR,
            "title":"L001 H07 old anchor interpretation",
            "text":"H07 old witness 48.585 documented before correction",
            "source_revision":1,"epistemic_status":"INSTRUMENTAL_REVIEW_PENDING",
        }, stamps[0], "knowledge-v1"),
        (RULE, "ATMSNode", {
            "kind":"justification","active":True,"antecedents":[ANCHOR],
            "consequent":NEW,"source_id":ANCHOR,
        }, stamps[1], "rule-v2"),
        (KNOW, "KnowledgeItem", {
            "kind":"knowledge","active":True,"node_id":NEW,"source_id":ANCHOR,
            "title":"L001 H07 revised anchor bounds",
            "text":"H07 48.986 to 49.988 seconds video, transcription awaiting primary export",
            "source_revision":2,"epistemic_status":"DOCUMENTARY_TRANSCRIPTION_NOT_VISUAL_VERIFICATION",
        }, stamps[1], "knowledge-v2")
    ]
    for entity,typ,payload,stamp,key in revisions:
        ledger.append_revision(
            entity_id=entity,entity_type=typ,case_id=CASE,
            actor_id="arena-e00-lineage-correction",
            idempotency_key="E00:"+key,payload=payload,
            recorded_at=stamp,created_at=stamp,
            access_policy="construction-visible")
    snapshots=[]
    for stamp in stamps:
        rows=ledger.snapshot(case_id=CASE,as_known_at=stamp)
        eng, proj=project(events_from_ledger(rows),as_known_at=stamp,lane="D",
                          investigation_id=CASE)
        kn, ev=load_events_from_ledger(Path(ledger.db_path),CASE,stamp)
        r=retrieve(investigation_id=CASE,lane="D",as_known_at=stamp,
                   query="L001 H07 anchor",knowledge_records=kn,atms_events=ev)
        snapshots.append({
            "as_known_at":stamp,
            "old_supported":eng.explain(OLD)["supported"],
            "new_supported":eng.explain(NEW)["supported"],
            "knowledge_node":r["items"][0]["node_id"] if len(r["items"])==1 else None,
            "projection_hash":proj["projection_hash"],
        })
    if [(x["old_supported"],x["new_supported"],x["knowledge_node"]) for x in snapshots] != [
        (True,False,OLD),(False,True,NEW)
    ]:
        raise AssertionError("E00_TEMPORAL_REVISION_NOT_RECONSTRUCTIBLE")
    return {"schema":"igc-arena-e00-temporal-revision/0.1",
            "status":"LINEAGE_REVISION_REPLAYED_PRIMARY_SOURCE_PENDING",
            "time_semantics":"RECORDED_FOR_REPRODUCTION_NOT_ORIGINAL_ANNOTATION_TIMES",
            "snapshots":snapshots,"new_ledger_revisions":len(revisions),
            "truth_status":"NOT_DETERMINED_BY_ATMS"}
