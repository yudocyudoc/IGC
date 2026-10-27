"""PT-04: materialize archived R1 and prepared R2 in the existing ledger/ATMS.

This is an administrative import, NOT a R2 revision or delivery of feedback.
No AI call, simulation, or new scientific observation is made.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from scripts.arena_atms import project, events_from_ledger
from scripts.arena_v0_contract import digest
from scripts.arena_r1_buffalo_postonly import ORIGINAL_NATIVE_SHA, SHARED_SOURCE
from scripts.ledger import Ledger

MIGRATION = Path(__file__).resolve().parents[1] / "migrations/0001_ledger.sql"
SCHEMA = "igc-arena-r2-pt04-ledger-cut/0.1"


def require(test, reason):
    if not test:
        raise ValueError(reason)


def load_dossier(folder):
    root = Path(folder)
    read = lambda f: json.loads((root / f).read_text())
    manifest = read("manifest.json")
    visible = read("b-visible.json")
    packets = {"B": read("b-own-feedback.json"),
               "D": read("d-own-state.json"),
               "M": read("m-own-state.json")}
    raw = (root / "b-parent-native.json").read_bytes()
    require(sha256(raw).hexdigest() == ORIGINAL_NATIVE_SHA,
            "R2_PARENT_BYTES_DIFFER")
    require(manifest["source_snapshot_hash"] == visible["source_snapshot_hash"] ==
            SHARED_SOURCE and manifest["r1_method_attempts"] == {"D": 6, "B": 1, "M": 3},
            "R2_SOURCE_OR_ATTEMPTS_DIFFER")
    require(manifest["r2_revision"] == "NOT_INFERRED" and
            manifest["producer_calls"] == manifest["solver_calls"] == 0,
            "R2_SECOND_DECISION_ALREADY_ASSERTED")
    require(manifest["method_private_hashes"] == {
        "B_feedback": digest(packets["B"]), "D_own": digest(packets["D"]),
        "M_own": digest(packets["M"])}, "R2_PACKET_HASHES_DIFFER")
    require(packets["B"]["has_solver_trajectory"] is False and
            packets["B"]["g3"] == "NOT_COMPUTABLE" and
            packets["D"]["r2_decision"] == "PENDING_NOT_FABRICATED" and
            packets["M"]["r2_decision"] == "PENDING_NOT_FABRICATED" and
            packets["M"]["chosen_parent"] is None and
            packets["M"]["r1_decision"]["status"] == "ABSTAIN",
            "R2_STATE_CANNOT_BE_INVENTED")
    return manifest, visible, packets, json.loads(raw)


def snapshot(db, case_id, at, lane):
    require(lane in ("D", "B", "M"), "R2_INVALID_LANE")
    revisions = Ledger(db, MIGRATION).snapshot(case_id=case_id, as_known_at=at)
    visible = [r for r in revisions if r.access_policy in
               ("construction-visible", "lane:" + lane)]
    engine, manifest = project(events_from_ledger(visible),
                               as_known_at=at, lane=lane,
                               investigation_id=case_id)
    return {"lane": lane, "as_known_at": at,
            "visible_entities": sorted(r.entity_id for r in visible),
            "atms": manifest, "logical": engine.to_report(),
            "truth_status": "NOT_DETERMINED_BY_ATMS"}


def ingest(db, folder, before, after):
    from scripts.arena_atms import _utc
    require(_utc(after) > _utc(before), "R2_INCORRECT_TIME_ORDER")
    manifest, visible, packets, native = load_dossier(folder)
    case = manifest["investigation_id"]
    ledger = Ledger(db, MIGRATION)
    def put(lane, key, kind, body, when):
        entity = "arena:r2:" + case + ":" + lane + ":" + key
        payload = {"kind": kind, "active": True, "source_id": SHARED_SOURCE,
                   "phase": "R1_ARCHIVED" if when == before
                   else "R2_PREPARED_NOT_DELIVERED", **body}
        ledger.append_revision(
            entity_id=entity, entity_type="ArenaR2Evidence", case_id=case,
            actor_id="arena:r2:pt04", idempotency_key=entity + ":" + digest(payload),
            payload=payload, recorded_at=when, created_at=when,
            access_policy="construction-visible" if lane == "COMMON"
            else "lane:" + lane)
        return entity
    common = put("COMMON", "source", "fact", {
        "observations": visible["construction"]["observations"],
        "source_snapshot_hash": SHARED_SOURCE}, before)
    for lane in ("D", "M"):
        put(lane, "r1-state", "archive", {"own_state": packets[lane]}, before)
    put("B", "r1-native-and-log", "archive", {
        "native": native, "own_feedback": packets["B"],
        "parent_bytes_sha256": manifest["b_parent_native_bytes_sha256"]}, before)
    b1 = put("B", "native-receipt", "assumption", {
        "source_id": manifest["b_parent_native_bytes_sha256"]}, before)
    b2 = put("B", "provider-receipt", "assumption", {
        "source_id": manifest["b_raw_provider_reply_bytes_sha256"]}, before)
    put("B", "build-failed", "fact", {
        "status": "G1_NEGATIVE_NO_G2_OR_G3",
        "source_id": manifest["b_original_log_bytes_sha256"]}, before)
    claim = "arena:r2:" + case + ":B:original-proposal-received"
    for key, premise in (("native-proof", b1), ("provider-proof", b2)):
        put("B", key, "justification", {
            "antecedents": [premise, common], "consequent": claim,
            "epistemic_status": "SUBMISSION_ONLY_NOT_EMPIRICAL_FIT"}, before)
    for lane in ("D", "B", "M"):
        put(lane, "r2-packet-prepared", "fact", {
            "packet_sha256": manifest["method_private_hashes"][
                "B_feedback" if lane == "B" else lane + "_own"],
            "status": "NOT_SENT_NO_SECOND_DECISION"}, after)
    earlier = snapshot(db, case, before, "B")
    later = snapshot(db, case, after, "B")
    key = "arena:r2:" + case + ":B:r2-packet-prepared"
    require(claim in earlier["logical"]["labels"] and
            key not in earlier["logical"]["labels"] and
            key in later["logical"]["labels"],
            "R2_TEMPORAL_PROJECTION_DID_NOT_CHANGE")
    return {"schema": SCHEMA, "case_id": case,
            "r1_import_time": before, "r2_preparation_time": after,
            "initially_supported_submission": claim,
            "before": earlier, "after": later,
            "feedback_delivered": False, "second_decisions": 0,
            "provider_calls": 0}
