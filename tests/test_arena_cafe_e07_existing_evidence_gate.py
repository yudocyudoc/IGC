"""Real F3 historical packet ↔ canonical E02 six-arm ledger: no new PM inference."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_cafe.e07_existing_evidence_gate import adjudicate

ENV = ("E07_ORIGINAL_F3", "E07_CANONICAL_LEDGER", "E07_B_CLOSURE_REPORT")


@unittest.skipUnless(all(os.environ.get(k) for k in ENV),
                     "requires genuine F3/E02-B archived artifacts")
class E07ExistingEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f3 = Path(os.environ[ENV[0]]).read_bytes()
        cls.ledger = Path(os.environ[ENV[1]])
        cls.closure = json.loads(Path(os.environ[ENV[2]]).read_text())
        cls.report = adjudicate(cls.f3, cls.ledger, cls.closure)

    def test_pinned_source_and_same_events_not_remined(self):
        r = self.report
        self.assertEqual(r["status"],
            "E07_NOT_ACTIVATED_NO_INCREMENTAL_VARIATION_IN_EXISTING_EV01")
        self.assertEqual(r["n_cases"], 15)
        self.assertEqual(r["observed_route_variants"], 1)
        self.assertEqual(r["observed_rework_cases"], 0)
        self.assertTrue(r["known_B1_direct_stage_order"])
        self.assertTrue(r["known_B2_resource_periods"])
        self.assertTrue(r["historical_f3_a3_is_not_current_b_status"])
        self.assertEqual(set(r["same_public_events_verified_for_all_three_arms"]),{"O0","O1"})
        self.assertNotEqual(
            r["same_public_events_verified_for_all_three_arms"]["O0"]["public_visible_sha256"],
            r["same_public_events_verified_for_all_three_arms"]["O1"]["public_visible_sha256"])
        self.assertFalse(r["pm_new_execution"])
        self.assertEqual(r["new_B_provider_calls"],0)
        self.assertEqual(r["new_omc_or_des_runs"],0)
        self.assertEqual(r["e06_real_video2_source_fitness"],
            "NOT_EVALUATED_NO_VIDEO2_WINDOWS_IN_THIS_EVIDENCE_PACKAGE")
        self.assertNotIn("full_case_route_counts", r)

    def test_tampered_f3_source_bytes_are_rejected(self):
        with self.assertRaisesRegex(ValueError,"E07_ORIGINAL_F3_BYTES_CHANGED"):
            adjudicate(self.f3+b" ", self.ledger, self.closure)

    def test_cross_condition_source_swap_blocked(self):
        bad=deepcopy(self.closure)
        bad["conditions"]["O0"]["source"]["source_snapshot_hash"]=(
            bad["conditions"]["O1"]["source"]["source_snapshot_hash"])
        with self.assertRaisesRegex(ValueError,"E07_NOT_THE_SAME_O0_O1_EVENTS"):
            adjudicate(self.f3,self.ledger,bad)

    def test_b_current_g1_status_not_replaced_by_old_f3_partial(self):
        bad=deepcopy(self.closure)
        bad["conditions"]["O0"]["memory"]["status"]="NATIVE_NOT_EXECUTED"
        with self.assertRaisesRegex(ValueError,"E07_B_STATUS_INCORRECT"):
            adjudicate(self.f3,self.ledger,bad)

    def test_ledger_source_drift_is_rejected_without_mutating_original(self):
        with TemporaryDirectory() as tmp:
            work=Path(tmp)/"copy.sqlite"
            shutil.copy2(self.ledger,work)
            conn=sqlite3.connect(work)
            try:
                # The original ledger prevents mutation; disable only inside
                # intentionally adversarial *test copy* to model corrupted evidence.
                conn.execute("DROP TRIGGER entity_revisions_no_update")
                entity="E02-D-O0:ARTIFACT:SOURCE"
                row=conn.execute("SELECT payload_json FROM entity_revisions WHERE entity_id=?",(entity,)).fetchone()
                doc=json.loads(row[0])
                doc["data"]["visible_sha256"]="sha256:"+"0"*64
                conn.execute("UPDATE entity_revisions SET payload_json=? WHERE entity_id=?",
                             (json.dumps(doc),entity))
                conn.commit()
            finally:
                conn.close()
            with self.assertRaisesRegex(ValueError,"E07_NOT_THE_SAME_O0_O1_EVENTS"):
                adjudicate(self.f3,work,self.closure)


if __name__ == "__main__":
    unittest.main()