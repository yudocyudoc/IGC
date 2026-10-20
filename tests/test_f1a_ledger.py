from __future__ import annotations

from pathlib import Path
import json
import sqlite3
import tempfile
import unittest

from scripts.ledger import IdempotencyConflict, Ledger, LedgerError


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "migrations" / "0001_ledger.sql"
T0 = "2026-01-01T00:00:00Z"
T1 = "2026-01-02T00:00:00Z"
T2 = "2026-01-03T00:00:00Z"
T3 = "2026-01-04T00:00:00Z"


class LedgerTests(unittest.TestCase):
    def test_linkml_source_contract_declares_required_identity_and_time_slots(self):
        schema = json.loads((ROOT / "schema" / "source" / "igc.yaml").read_text(encoding="utf-8"))
        self.assertEqual(schema["name"], "igc")
        slots = schema["slots"]
        for required in ("id", "entity_type", "schema_version", "case_id", "created_at",
                         "created_by", "recorded_at", "source_event_id", "revision",
                         "access_policy", "integrity_hash", "valid_from", "valid_to"):
            self.assertIn(required, slots)
        self.assertIn("ClaimOccurrence", schema["classes"])
        self.assertIn("Proposition", schema["classes"])

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "ledger.sqlite"
        self.ledger = Ledger(self.db, MIGRATION)

    def record(self, **overrides):
        values = {
            "entity_id": "urn:igc:claim:c1",
            "entity_type": "ClaimOccurrence",
            "case_id": "urn:igc:case:c1",
            "actor_id": "urn:igc:actor:researcher",
            "idempotency_key": "cmd-1",
            "payload": {"text": "El sistema podría estar lento.", "modality": "possible"},
            "recorded_at": T1,
            "created_at": T1,
            "valid_from": T0,
        }
        values.update(overrides)
        return self.ledger.append_revision(**values)

    def test_as_known_at_preserves_later_correction(self):
        original = self.record()
        correction = self.record(
            idempotency_key="cmd-2",
            payload={"text": "El sistema es lento.", "modality": "asserted"},
            recorded_at=T3,
        )
        before = self.ledger.snapshot(case_id="urn:igc:case:c1", as_known_at=T2)
        after = self.ledger.snapshot(case_id="urn:igc:case:c1", as_known_at=T3)
        self.assertEqual([(x.revision, x.payload["modality"]) for x in before], [(1, "possible")])
        self.assertEqual([(x.revision, x.payload["modality"]) for x in after], [(2, "asserted")])
        self.assertEqual(correction.supersedes_revision, original.revision)

    def test_valid_time_filter_is_independent_of_system_cut(self):
        self.record(valid_from=T0, valid_to=T2)
        during = self.ledger.snapshot(
            case_id="urn:igc:case:c1", as_known_at=T1, valid_during=(T0, T1)
        )
        after = self.ledger.snapshot(
            case_id="urn:igc:case:c1", as_known_at=T1, valid_during=(T2, T3)
        )
        self.assertEqual(len(during), 1)
        self.assertEqual(len(after), 0)

    def test_idempotent_replay_returns_same_revision(self):
        first = self.record()
        replay = self.record()
        self.assertEqual(first.event_id, replay.event_id)
        self.assertEqual(first.integrity_hash, replay.integrity_hash)

    def test_idempotency_key_cannot_alias_a_different_command(self):
        self.record()
        with self.assertRaises(IdempotencyConflict):
            self.record(payload={"text": "distinto"}, recorded_at=T2)

    def test_system_timestamps_must_be_timezone_aware(self):
        with self.assertRaises(LedgerError):
            self.record(recorded_at="2026-01-02T00:00:00")

    def test_invalid_validity_window_is_rejected_before_commit(self):
        with self.assertRaises(LedgerError):
            self.record(valid_from=T2, valid_to=T1)
        self.assertEqual(self.ledger.snapshot(case_id="urn:igc:case:c1", as_known_at=T3), [])

    def test_entity_case_scope_is_immutable(self):
        self.record()
        with self.assertRaises(LedgerError):
            self.record(
                idempotency_key="cmd-other-case",
                case_id="urn:igc:case:other",
                recorded_at=T2,
            )
        self.assertEqual(len(self.ledger.snapshot(case_id="urn:igc:case:c1", as_known_at=T3)), 1)

    def test_canonical_tables_are_append_only(self):
        self.record()
        with sqlite3.connect(self.db) as connection:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    "UPDATE ledger_events SET event_type = 'rewritten'"
                )


if __name__ == "__main__":
    unittest.main()
