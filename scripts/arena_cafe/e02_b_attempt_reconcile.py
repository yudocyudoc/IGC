"""Reconcile the TWO actual EV-01 Buffalo live attempts, without generating models.

Consumes immutable GitHub Actions artifact members, not provider secrets or DES.
Archives original evidence identity, corrects status semantics in a separate
interpretation, and appends fact-based temporal evidence to the EXISTING F1a
ledger + ATMS projection. No retries, no new model, no fake second decision.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import zipfile

from scripts.ledger import Ledger
from scripts.arena_atms import events_from_ledger, project
from scripts.arena_v0_contract import canonical

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "igc-e02-b-original-live-attempt-reconciliation/0.1"
RUN_ID = 42319874751
ARTIFACT_IDS = {"O0": 13552064058, "O1": 13552960142}
SOURCE_RECEIPT_SHA256 = {
    "O0": "46eb4dccf0372003b1bd1ce00a5e1909d620046e8dde9d9bc0a996ba0f39da75",
    "O1": "28daea16fabe77a814d0dddbd141a1bb6cea2fe3a4320fcf743409d17e52f437",
}
NO_MODEL = "PROVIDER_TRANSPORT_TIMEOUT_NO_NATIVE_MODEL"


def _sha(data: bytes) -> str:
    return "sha256:" + sha256(data).hexdigest()


def _member(container: Path, path: str) -> bytes:
    if container.is_dir():
        return (container / path).read_bytes()
    with zipfile.ZipFile(container) as archive:
        return archive.read(path)


def _json(container: Path, path: str) -> tuple[dict, bytes]:
    raw = _member(container, path)
    doc = json.loads(raw)
    if not isinstance(doc, dict):
        raise ValueError("NOT_JSON_OBJECT:" + path)
    return doc, raw


def inspect_attempt(condition: str, container: Path) -> dict:
    if condition not in ARTIFACT_IDS:
        raise ValueError("UNKNOWN_CONDITION")
    receipt, receipt_raw = _json(container, "initial/receipt.json")
    result, result_raw = _json(container, "initial/native-engine-result.json")
    outcome, outcome_raw = _json(container, "outcome.json")
    visible, visible_raw = _json(container, "stage-initial/b-visible.json")
    request, request_raw = _json(container, "initial/request-metadata.json")
    exit_status = _member(container, "initial-exit.txt").decode("utf-8").strip()
    revision_status = _member(container, "revision-status.txt").decode("utf-8").strip()

    expected = SOURCE_RECEIPT_SHA256[condition]
    if sha256(receipt_raw).hexdigest() != expected:
        raise ValueError("LIVE_RECEIPT_SHA256_CHANGED:" + condition)
    if not (receipt.get("case_id") == "EV-01" and receipt.get("condition_id") == condition
            and receipt.get("round_kind") == "initial" and receipt.get("mode") == "live"
            and receipt.get("provider_calls") == 1 and receipt.get("proxy_requests") == 1
            and receipt.get("quant_schema_seen") is True
            and receipt.get("model_returned") is False
            and receipt.get("raw_provider_saved") is False
            and receipt.get("http_status") is None
            and receipt.get("provider_finish_reason") is None
            and receipt.get("provider_usage") is None
            and receipt.get("bridge_error") == "The operation was aborted due to timeout"
            and receipt.get("native_error") == "Error: 400 BRIDGE_FAILURE"):
        raise ValueError("NOT_OBSERVED_ORIGINAL_PROVIDER_TIMEOUT:" + condition)
    if result != {"err": "Error: 400 BRIDGE_FAILURE"} or exit_status != "INITIAL_EXIT=NONZERO":
        raise ValueError("FALSE_NATIVE_RESULT_OR_SUCCESS_EXIT:" + condition)
    if (revision_status != "G0_PARENT_INVALID_NO_REVIEW" or
            outcome.get("revision_attempted") is not False or
            outcome.get("provider_calls_counted") != 1 or
            outcome.get("condition") != condition or
            outcome.get("runs", {}).get("initial", {}).get("result_sha256") != receipt.get("result_sha256")):
        raise ValueError("E02_B_ARCHIVED_REVISION_OR_BUDGET_DRIFT:" + condition)
    if (visible.get("observability", {}).get("condition_id") != condition or
            visible.get("source_snapshot_hash") != receipt.get("source_snapshot_hash") or
            visible.get("construction", {}).get("declared_input_reconstruction", {}).get("signal_sha256")
            != receipt.get("arrival_signal_sha256") or
            request.get("request_sha256") != receipt.get("request_sha256") or
            request.get("round_kind") != "initial"):
        raise ValueError("E02_B_SOURCE_OR_EFFECTIVE_REQUEST_IDENTITY_DRIFT:" + condition)
    if receipt.get("status") != "EV01_NATIVE_HORIZON_NOT_COMPARABLE":
        # This *historical, erroneous* label is frozen; repair the runner separately.
        raise ValueError("HISTORICAL_RECEIPT_LABEL_UNEXPECTED:" + condition)
    if not (receipt.get("horizon_matches_case") is False and
            receipt.get("output_horizon_hours") is None):
        raise ValueError("NATIVE_HORIZON_EVIDENCE_UNEXPECTED:" + condition)
    return {
        "condition": condition,
        "run_id": RUN_ID,
        "artifact_id": ARTIFACT_IDS[condition],
        "source_status_verbatim": receipt["status"],
        "normalized_status": NO_MODEL,
        "source_status_is_misleading": True,
        "reason": "TIMEOUT_WITHOUT_PROVIDER_HTTP_RESPONSE_OR_NATIVE_MODEL",
        "provider_attempt_count": 1,
        "provider_billing": "UNKNOWN_NO_PROVIDER_USAGE_RECEIPT",
        "http_status": "NOT_RECEIVED",
        "provider_response_obtained": False,
        "model_returned": False,
        "G0": "NOT_REACHED_NO_NATIVE_MODEL",
        "G1": "NOT_RUN", "G2": "NOT_RUN", "G3": "NOT_RUN",
        "G4": "NOT_RUN", "G5": "NOT_RUN",
        "revision_status": "NOT_ATTEMPTED_NO_VALID_OWN_NATIVE_PARENT",
        "native_second_decision": "NOT_MADE",
        "arrival_signal_sha256": receipt["arrival_signal_sha256"],
        "source_snapshot_hash": receipt["source_snapshot_hash"],
        "request_sha256": receipt["request_sha256"],
        "native_placeholder_not_model_sha256": _sha(result_raw),
        "evidence_member_sha256": {
            "receipt": _sha(receipt_raw),
            "native_error_placeholder": _sha(result_raw),
            "outcome": _sha(outcome_raw),
            "public_stage": _sha(visible_raw),
            "original_request_metadata": _sha(request_raw),
        },
        "raw_provider_response": "ABSENT_TIMEOUT_NOT_FABRICATED",
        "no_retry_performed": True,
    }


def append_attempt_knowledge(ledger: Ledger, result: dict, recorded_at: datetime) -> dict:
    condition = result["condition"]
    case = "E02-B-" + condition
    if recorded_at.tzinfo is None or recorded_at.utcoffset() is None:
        raise ValueError("REPLAY_TIMESTAMP_MUST_HAVE_ZONE")
    t0 = recorded_at.astimezone(timezone.utc)
    t1 = t0 + timedelta(microseconds=1)
    initial = case + ":SOURCE_ATTEMPT_DECLARED"
    fail = case + ":PROVIDER_ATTEMPT_FAILED"
    out = case + ":NO_NATIVE_EVALUABLE"
    artifact_hash = _sha(canonical(result))
    entries = [
        (case + ":ARTIFACT", "EvidenceArtifact", {
            "schema": SCHEMA, "artifact_sha256": artifact_hash, "data": result,
        }, t1, "archive"),
        (initial, "ATMSNode", {
            "kind": "fact", "active": True,
            "claim": "PUBLIC_SOURCE_AND_CASE_ASSIGNED_NOT_MODEL_GENERATED",
            "source_snapshot_hash": result["source_snapshot_hash"],
        }, t0, "source"),
        (fail, "ATMSNode", {
            "kind": "fact", "active": True,
            "claim": "OBSERVED_FAILED_TRANSPORT_ATTEMPT",
            "evidence_artifact_sha256": artifact_hash,
            "receipt_sha256": result["evidence_member_sha256"]["receipt"],
        }, t1, "failed-attempt"),
        (case + ":RULE", "ATMSNode", {
            "kind": "justification", "active": True,
            "antecedents": [fail], "consequent": out, "source_id": fail,
            "evidence_artifact_sha256": artifact_hash,
        }, t1, "no-model-rule"),
        (case + ":KNOWLEDGE", "KnowledgeItem", {
            "kind": "knowledge", "active": True, "node_id": out, "source_id": fail,
            "source_revision": 1,
            "title": "Buffalo " + condition + ": no native model from attempted call",
            "text": "Transport timeout after one real attempt; no HTTP response, no revision",
            "epistemic_status": "ATTEMPT_FAILURE_NOT_METHOD_INABILITY",
            "evidence_artifact_sha256": artifact_hash,
        }, t1, "knowledge"),
    ]
    for entity, typ, payload, when, key in entries:
        stamp = when.isoformat()
        ledger.append_revision(entity_id=entity, entity_type=typ, case_id=case,
            actor_id="arena-e02-b-real-attempt-reconciler",
            idempotency_key=case+":"+key, payload=payload,
            recorded_at=stamp, created_at=stamp, access_policy="lane:B")
    views = []
    for when in (t0, t1):
        stamp = when.isoformat()
        engine, projection = project(
            events_from_ledger(ledger.snapshot(case_id=case, as_known_at=stamp)),
            as_known_at=stamp, lane="B", investigation_id=case)
        views.append({"at": stamp,
            "source_recorded": engine.explain(initial)["supported"],
            "transport_failure_recorded": engine.explain(fail)["supported"],
            "no_native_evaluable": engine.explain(out)["supported"],
            "projection_hash": projection["projection_hash"]})
    if not (views[0]["source_recorded"] and not views[0]["no_native_evaluable"]
            and views[1]["no_native_evaluable"] and views[1]["transport_failure_recorded"]):
        raise ValueError("E02_B_ATTEMPT_TIMELINE_NOT_RECONSTRUCTIBLE")
    return {"case_id": case, "status": "FAILED_ATTEMPT_DOCUMENTED_NO_SECOND_NATIVE_DECISION",
            "recorded_at_semantics": "DETERMINISTIC_REPLAY_INGESTION_TIME_NOT_PROVIDER_EVENT_TIME",
            "artifact_sha256": artifact_hash, "snapshots": views,
            "has_native_model": False, "second_decision_issued": False,
            "record_count": len(entries)}


def reconcile(o0: Path, o1: Path, db: Path, recorded_at: datetime) -> dict:
    data = {c: inspect_attempt(c, path) for c, path in (("O0",o0),("O1",o1))}
    if data["O0"]["arrival_signal_sha256"] != data["O1"]["arrival_signal_sha256"]:
        raise ValueError("B_CAUSAL_STIMULUS_DIFFERENT_ACROSS_O0_O1")
    if data["O0"]["source_snapshot_hash"] == data["O1"]["source_snapshot_hash"]:
        raise ValueError("B_O0_O1_VIEWS_NOT_DISTINCT")
    ledger = Ledger(db, ROOT / "migrations/0001_ledger.sql")
    memory = {c:append_attempt_knowledge(ledger,r,recorded_at)
              for c,r in data.items()}
    return {
        "schema": SCHEMA,
        "source_workflow_run_id": RUN_ID,
        "source_workflow_conclusion": "SUCCESSFUL_ARCHIVAL_OF_UNSUCCESSFUL_NATIVE_ATTEMPTS",
        "experiment_status": "E02_B_TWO_LIVE_ATTEMPTS_FAILED_TRANSPORT_NO_NATIVE_PARENTS",
        "conditions_assigned": 2, "conditions_attempted": 2,
        "native_models_returned": 0, "models_comparable": 0,
        "attempted_provider_calls": 2, "actual_provider_billing": "UNKNOWN",
        "maximum_provider_calls_original_design": 4,
        "revision_calls_attempted": 0,
        "unused_review_slots_not_generic_retry_budget": 2,
        "G0": "NOT_REACHED", "G1": "NOT_RUN", "G2": "NOT_RUN",
        "G3": "NOT_RUN", "G4": "NOT_RUN", "G5": "NOT_RUN",
        "no_automatic_retries": True,
        "no_false_abstention_or_scientific_negation": True,
        "no_new_provider_or_openmodelica_calls_by_this_reconciler": True,
        "original_immutable_artifacts": [
            "https://github.com/yudocyudoc/IGC/actions/runs/42319874751/artifacts/13552064058",
            "https://github.com/yudocyudoc/IGC/actions/runs/42319874751/artifacts/13552960142",
        ],
        "conditions": data, "memory": memory,
    }


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--o0",required=True,type=Path)
    p.add_argument("--o1",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--recorded-at",required=True)
    args=p.parse_args()
    if args.out.exists():
        raise ValueError("E02_B_REFUSE_OVERWRITE")
    args.out.mkdir(parents=True)
    stamp=datetime.fromisoformat(args.recorded_at.replace("Z","+00:00"))
    report=reconcile(args.o0,args.o1,args.out/"ledger.sqlite",stamp)
    (args.out/"reconciliation.json").write_bytes(canonical(report)+b"\n")
    print(json.dumps({"experiment_status":report["experiment_status"],
                      "attempted_provider_calls":report["attempted_provider_calls"],
                      "native_models_returned":0,"revision_calls_attempted":0}))

if __name__=="__main__":
    main()