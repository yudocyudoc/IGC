"""Tests for the existing verified FM-B3 -> Arena D prediction lock adapter."""
import csv
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest

from scripts.arena_b3_lock import build
from scripts.arena_round import RoundError, verify_lock
from test_arena_round import fixture


class B3LockTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.spec, self.primary, _ = fixture()
        candidate_metrics = {}
        for index, candidate in enumerate(("CS-01", "CS-02")):
            path = self.root / f"b3-{candidate.lower().replace('-', '_')}_res.csv"
            with path.open("w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=["time", "delivered"])
                writer.writeheader()
                for time in range(6):
                    writer.writerow({"time": time, "delivered": time * (index + 1)})
            candidate_metrics["urn:igc:candidate:" + candidate] = {
                "csv_sha256": "sha256:" + sha256(path.read_bytes()).hexdigest()}
        self.report = {
            "status": "B3_MOLECULAR_DYNAMICS_PASS_SYNTHETIC",
            "empirical_or_causal_claim": False, "explanatory_adequacy_evaluated": False,
            "candidate_disposition": {
                "retained_and_simulated": list(candidate_metrics),
                "rejected_and_not_simulated": ["urn:igc:candidate:CS-03"],
                "simulated_count": 2},
            "dynamic_coherence": {
                "all_admissible_candidates_pass": True,
                "candidate_metrics": candidate_metrics}}

    def tearDown(self):
        self.tmp.cleanup()

    def test_verified_simulated_candidates_lock_with_b0(self):
        views, submissions, lock = build(
            self.spec, self.primary, self.report, self.root, run_ref="actions/test")
        verify_lock(lock)
        self.assertEqual(submissions["D"]["proposals"][0]["predictions"], [3.0, 4.0, 5.0])
        self.assertEqual(submissions["D"]["proposals"][1]["predictions"], [6.0, 8.0, 10.0])
        self.assertEqual(submissions["S"]["status"], "NOT_IMPLEMENTED")
        self.assertNotIn("CS-03", str(submissions["D"]))
        self.assertEqual(lock["evaluation_status"], "LOCKED_NOT_EVALUATED")

    def test_tampered_simulation_csv_rejected(self):
        path = self.root / "b3-cs_01_res.csv"
        path.write_text(path.read_text() + "6,999\n")
        with self.assertRaisesRegex(RoundError, "digest mismatch"):
            build(self.spec, self.primary, self.report, self.root, run_ref="actions/test")

    def test_missing_simulation_time_rejected(self):
        self.spec["target_times"] = [3, 4, 5.5]
        with self.assertRaisesRegex(RoundError, "target evaluation grid"):
            build(self.spec, self.primary, self.report, self.root, run_ref="actions/test")

    def test_rejected_candidate_must_not_be_simulated(self):
        self.report["candidate_disposition"]["rejected_and_not_simulated"] = [
            "urn:igc:candidate:CS-02"]
        with self.assertRaisesRegex(RoundError, "overlap"):
            build(self.spec, self.primary, self.report, self.root, run_ref="actions/test")

    def test_b3_must_have_passed_independent_coherence(self):
        self.report["dynamic_coherence"]["all_admissible_candidates_pass"] = False
        with self.assertRaisesRegex(RoundError, "consistency"):
            build(self.spec, self.primary, self.report, self.root, run_ref="actions/test")


if __name__ == "__main__":
    unittest.main()
