"""Persist D0→D1 research history to F1a ledger; project ATMS, never generate hypotheses.

This adapter records original D artifacts, justifications, physical conflicts and
temporal retractions. Scientific compatibility remains conditional on declared
instrument error and FINITE parameter-grid assumptions, never causal truth.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.arena_v0_contract import (
    INPUT_SCHEMA, digest, validate_visible_input, validate_submission, arm_view,
)
from scripts.arena_atms import project, ATMSError
from scripts.ledger import Ledger
from scripts.arena_d_v01 import generate, modelica, verify_csv
from scripts.arena_d_v1_screen import assess, compare_omc_csv

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "migrations/0001_ledger.sql"
SCHEMA = "igc-arena-d-atms-bridge/0.1"
POLICY = "lane:D"
TIMESTAMP = "2026-10-25T18:00:00-06:00"


class BridgeError(ValueError):
    pass


def check(cond, code):
    if not cond:
        raise BridgeError(code)


def checked_trace(event):
    check(isinstance(event, dict) and set(event) == {
        "schema", "arm_id", "round_id", "event_type", "iteration", "source_hash",
        "payload_hash", "previous_event_hash", "event_hash",
    }, "MALFORMED_D_TRACE")
    check(event["arm_id"] == "D" and event["schema"] == "igc-arena-trace-event/0.1",
          "FOREIGN_TRACE")
    check(event["event_hash"] == digest({k: v for k, v in event.items()
                                        if k != "event_hash"}), "TAMPERED_TRACE")
    return event


def event_id(case_id, round_id, item):
    check(isinstance(item, str) and bool(item), "BAD_ITEM_ID")
    return f"arena:{case_id}:{round_id}:D:{item}"


def _store(ledger, *, case_id, round_id, recorded_at, entity_type, key, payload):
    ident = event_id(case_id, round_id, key)
    return ledger.append_revision(
        entity_id=ident, entity_type=entity_type, case_id=case_id,
        actor_id="arena:D:bridge", idempotency_key=ident + ":" + digest(payload),
        payload=payload, recorded_at=recorded_at, created_at=recorded_at,
        access_policy=POLICY)


def validated_bundle(data, protocol, d0, d1):
    check(data.get("schema") == INPUT_SCHEMA, "NOT_ARENA_INPUT")
    validate_visible_input(data)
    original = generate(data)
    screen = json.loads((d1 / "screen.json").read_text())
    check(screen == assess(data, protocol), "SCREEN_NOT_REPRODUCIBLE")
    check(screen["input_hash"] == original["input_hash"] and
          screen["protocol_hash"] == digest(protocol), "WRONG_INPUT_OR_PROTOCOL")
    candidates = json.loads((d0 / "candidates.json").read_text())
    check(candidates["schema"] == original["schema"] and
          candidates["input_hash"] == original["input_hash"], "D0_BUNDLE_MISMATCH")
    check([x["id"] for x in candidates["candidates"]] ==
          [x["id"] for x in original["candidates"]], "D0_GENERATOR_IDS_CHANGED")
    for c in candidates["candidates"]:
        expected = next(x for x in original["candidates"] if x["id"] == c["id"])
        check(c["structure"] == expected["structure"] and
              c["structure_hash"] == expected["structure_hash"],
              "D0_GENERATOR_STRUCTURE_CHANGED")
        source = (d0 / c["modelica_file"]).read_bytes()
        from hashlib import sha256
        check(c["modelica_sha256"] == "sha256:" + sha256(source).hexdigest(),
              "D0_MODELICA_HASH_FAIL")
    sub = json.loads((d0 / "submission.json").read_text())
    check(sub["native_artifact_sha256"] == digest(candidates) and
          sub["hypothesis_ids"] == [c["id"] for c in candidates["candidates"]],
          "D0_SUBMISSION_MISMATCH")
    validate_submission(arm_view(data, "D"), sub)
    d0event = checked_trace(json.loads((d0 / "memory-event.json").read_text()))
    check(d0event["source_hash"] == original["input_hash"] and
          d0event["round_id"] == data["round_id"] and
          d0event["event_type"] == "HYPOTHESIS_PROPOSED" and
          d0event["previous_event_hash"] is None and
          d0event["payload_hash"] == digest(candidates), "D0_TRACE_CONTENT_MISMATCH")
    chain = json.loads((d1 / "memory-events.json").read_text())
    check(isinstance(chain, list) and len(chain) == 2 and chain[0] == d0event,
          "BROKEN_D0_D1_ANCESTRY")
    d1event = checked_trace(chain[1])
    check(d1event["event_type"] == "SIMULATION_REPORTED" and
          d1event["round_id"] == data["round_id"] and
          d1event["source_hash"] == d0event["source_hash"] and
          d1event["previous_event_hash"] == d0event["event_hash"] and
          d1event["payload_hash"] == digest(screen), "D1_TRACE_CONTENT_MISMATCH")
    by_id = {c["id"]: c for c in candidates["candidates"]}
    check(len(by_id) == len(candidates["candidates"]) == len(screen["results"]),
          "CANDIDATE_COUNT_MISMATCH")
    g2 = []
    for r in screen["results"]:
        check(r["candidate_id"] in by_id and
              r["structure_hash"] == by_id[r["candidate_id"]]["structure_hash"],
              "D1_UNKNOWN_HYPOTHESIS")
        source_name = "Dfit_" + r["structure_hash"][7:19]
        csv = d1 / (source_name + "_res.csv")
        model = d1 / (source_name + ".mo")
        check(csv.is_file() and model.is_file(), "MISSING_G2_ARTIFACT")
        native = dict(by_id[r["candidate_id"]])
        native["nominal_parameters"] = dict(r["best_grid"]["parameters"])
        raw_class = "DStockFlow_" + r["structure_hash"][7:19]
        expected_model = modelica(native, data["construction"]["input_profile"]).replace(
            "model " + raw_class, "model " + source_name).replace(
            "end " + raw_class + ";", "end " + source_name + ";")
        check(model.read_text(encoding="utf-8") == expected_model,
              "G2_MODELICA_SOURCE_TAMPERED")
        expected_times = [x["t"] for x in data["construction"]["observations"]]
        predicted = r["best_grid"]["predicted"]
        parity = compare_omc_csv(csv, list(zip(expected_times, predicted)), atol=.012)
        conservation = verify_csv(csv, r["stocks"],
                                  data["construction"]["input_profile"])
        g2.append({"candidate_id": r["candidate_id"],
                   "model_hash": _file_sha(model),
                   "csv_sha256": _file_sha(csv), "parity": parity,
                   "conservation": conservation})
    return original, candidates, sub, screen, [d0event, d1event], g2


def _file_sha(path):
    from hashlib import sha256
    return "sha256:" + sha256(path.read_bytes()).hexdigest()


def _logical_record(*, kind, id, case_id, source_id, **extras):
    return {"kind": kind, "id": id, "active": True, "source_id": source_id,
            "epistemic_status": "CONDITIONAL_NOT_CAUSAL_TRUTH", **extras}


def ingest(*, db, data, protocol, d0, d1, recorded_at=None):
    original, candidates, sub, screen, chain, g2 = validated_bundle(
        data, protocol, Path(d0), Path(d1))
    if recorded_at is None:
        recorded_at = datetime.now(timezone.utc).isoformat()
    check(isinstance(recorded_at, str) and datetime.fromisoformat(
          recorded_at.replace("Z", "+00:00")).tzinfo is not None,
          "MISSING_TIMEZONE")
    case_id = data["investigation_id"]
    round_id = data["round_id"]
    ledger = Ledger(db, MIGRATION)
    stored = []
    # Authoritative artifacts are preserved; no fabricated result or history.
    for key, entity_type, payload in [
        ("d0:bundle", "ArenaDNativeBundle", candidates),
        ("d0:submission", "ArenaDSubmission", sub),
        ("d1:screen", "ArenaDScreen", screen),
        ("d1:g2-proof", "ArenaDG2Proof", {"kind": "verification", "results": g2}),
    ]:
        stored.append(_store(ledger, case_id=case_id, round_id=round_id,
                             recorded_at=recorded_at, entity_type=entity_type,
                             key=key, payload=payload))
    for index, item in enumerate(chain):
        stored.append(_store(ledger, case_id=case_id, round_id=round_id,
                             recorded_at=recorded_at, entity_type="ArenaTraceEnvelope",
                             key=f"trace:{index}:{item['event_hash'][7:19]}",
                             payload={"kind": "trace", **item}))
    atms_items = []
    source = chain[0]["event_hash"]
    obs = "DOBS:" + original["input_hash"][7:19]
    instr = "DINSTR:" + digest(protocol)[7:19]
    grid = "DGRID:" + digest(protocol)[7:19]
    for name, src in ((obs, source), (instr, chain[1]["event_hash"]),
                      (grid, chain[1]["event_hash"])):
        atms_items.append(_logical_record(kind="assumption", id=name,
                                          case_id=case_id, source_id=src))
    for c in candidates["candidates"]:
        cid = c["id"]
        atom = "DSTRUCT:" + cid
        atms_items.append(_logical_record(kind="assumption", id=atom,
                                         case_id=case_id, source_id=source,
                                         candidate_id=cid))
    for r in screen["results"]:
        if r["status"] != "GRID_COMPATIBLE_NOT_IDENTIFIED":
            continue
        cid = r["candidate_id"]
        atms_items.append(_logical_record(
            kind="justification", id="DWITNESS:" + cid,
            case_id=case_id, source_id=chain[1]["event_hash"],
            antecedents=["DSTRUCT:" + cid, obs, instr, grid],
            consequent="DCOMPATIBLE:" + cid,
            explanation="Finite-grid witness under declared observational uncertainty only"))
    if screen["physical_bound_issues"]:
        # Jointly incompatible: this reported instrument bound AND these readings.
        # Does not imply which element of that conjunction is wrong.
        atms_items.append(_logical_record(
            kind="nogood", id="DOBS-INSTRUMENT-CONFLICT:" + screen["protocol_hash"][7:19],
            case_id=case_id, source_id=chain[1]["event_hash"],
            assumption_ids=[obs, instr],
            explanation="Observed values incompatible with stated bound and this family"))
    for item in atms_items:
        stored.append(_store(ledger, case_id=case_id, round_id=round_id,
                             recorded_at=recorded_at, entity_type="ArenaATMSNode",
                             key="logic:" + item["id"], payload=item))
    return {"schema": SCHEMA, "status": "D0_D1_LEDGER_ATMS_INGESTED",
            "investigation_id": case_id, "round_id": round_id,
            "stored_revisions": len(stored), "logical_items": len(atms_items),
            "source_events": [e["event_hash"] for e in chain],
            "projection": snapshot(db=db, case_id=case_id, round_id=round_id,
                                   as_known_at=recorded_at)}


def snapshot(*, db, case_id, round_id, as_known_at):
    ledger = Ledger(db, MIGRATION)
    revisions = ledger.snapshot(case_id=case_id, as_known_at=as_known_at)
    # F1a case scope + D lane access; never project B or M.
    allowed = [r for r in revisions
               if r.access_policy == POLICY and
               r.entity_id.startswith(f"arena:{case_id}:{round_id}:D:")]
    events = []
    for revision in allowed:
        if revision.entity_type != "ArenaATMSNode":
            continue
        item = dict(revision.payload)
        check(revision.entity_id == event_id(case_id, round_id, "logic:" + str(item.get("id"))),
              "LOGICAL_ID_ENTITY_MISMATCH")
        item.update(recorded_at=revision.recorded_at,
                    access_policy=revision.access_policy,
                    investigation_id=revision.case_id)
        events.append(item)
    engine, manifest = project(events, as_known_at=as_known_at,
                               lane="D", investigation_id=case_id)
    compatible = sorted(n for n in engine.labels if n.startswith("DCOMPATIBLE:")
                        and engine.explain(n)["supported"])
    return {"schema": SCHEMA, "investigation_id": case_id, "round_id": round_id,
            "as_known_at": as_known_at,
            "atms": manifest, "logical_state": engine.to_report(),
            "conditionally_supported": compatible,
            "truth_status": "NOT_DETERMINED_BY_ATMS",
            "revisions_visible": len(allowed)}


def retract_assumption(*, db, case_id, round_id, assumption_id, as_known_at,
                       recorded_at, reason):
    """Append a logical retraction; never erase historical evidence."""
    check(isinstance(reason, str) and len(reason) >= 8, "MISSING_RETRACTION_REASON")
    ledger = Ledger(db, MIGRATION)
    ident = event_id(case_id, round_id, "logic:" + assumption_id)
    records = ledger.snapshot(case_id=case_id, as_known_at=as_known_at)
    existing = next((r for r in records if r.entity_id == ident and
                     r.access_policy == POLICY and
                     r.entity_type == "ArenaATMSNode"), None)
    check(existing is not None and existing.payload.get("kind") == "assumption",
          "UNKNOWN_D_ASSUMPTION")
    check(existing.payload.get("active") is True, "ALREADY_RETRACTED")
    check(datetime.fromisoformat(recorded_at.replace("Z", "+00:00")) >
          datetime.fromisoformat(as_known_at.replace("Z", "+00:00")),
          "RETRACTION_MUST_BE_LATER")
    replacement = {**existing.payload, "active": False,
                   "retraction_reason": reason,
                   "prior_revision_hash": existing.integrity_hash}
    new = _store(ledger, case_id=case_id, round_id=round_id,
                 recorded_at=recorded_at, entity_type="ArenaATMSNode",
                 key="logic:" + assumption_id, payload=replacement)
    return {"entity_id": ident, "revision": new.revision,
            "retracted_at": new.recorded_at,
            "state_before": snapshot(db=db, case_id=case_id,
                                     round_id=round_id, as_known_at=as_known_at),
            "state_after": snapshot(db=db, case_id=case_id,
                                    round_id=round_id, as_known_at=recorded_at)}


def main():
    ap = argparse.ArgumentParser(description="D own-arm F1a/ATMS memory bridge")
    ap.add_argument("command", choices=["ingest", "snapshot"])
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--input", type=Path)
    ap.add_argument("--protocol", type=Path)
    ap.add_argument("--d0", type=Path)
    ap.add_argument("--d1", type=Path)
    ap.add_argument("--case")
    ap.add_argument("--round")
    ap.add_argument("--as-known-at", default=TIMESTAMP)
    ap.add_argument("--recorded-at", default=None)
    args = ap.parse_args()
    if args.command == "ingest":
        check(all(x is not None for x in (args.input,args.protocol,args.d0,args.d1)),
              "MISSING_INGEST_ARGUMENTS")
        result = ingest(db=args.db,
                        data=json.loads(args.input.read_text()),
                        protocol=json.loads(args.protocol.read_text()),
                        d0=args.d0, d1=args.d1, recorded_at=args.recorded_at)
    else:
        check(bool(args.case) and bool(args.round), "MISSING_SNAPSHOT_SCOPE")
        result = snapshot(db=args.db, case_id=args.case,
                          round_id=args.round, as_known_at=args.as_known_at)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
