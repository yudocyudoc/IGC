"""CT-01 original-method source and applicability checks, offline only."""
import json
import unittest
from scripts.arena_cafe.ct_capabilities import load_index, applicability


class HistoricalCapabilitiesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_index()

    def test_four_source_blobs_and_remote_metadata(self):
        self.assertEqual(len(self.data["capabilities"]), 4)
        for x in self.data["capabilities"]:
            self.assertTrue(x["artifacts"])
            self.assertEqual(len(x["source_git_blob"]), 40)

    def test_d2_rejects_ev01_and_ct03_without_reset_trial(self):
        res = applicability("D2", {"d1_parent_authenticated": True}, self.data)
        self.assertEqual(res["status"], "NOT_APPLICABLE_MISSING_RESET_TRIAL")
        self.assertFalse(res["artifact_internal_bytes_verified"])

    def test_m2_requires_own_parent_and_hourly_late_points(self):
        self.assertEqual(applicability("M2", {}, self.data)["status"], "NOT_APPLICABLE_MISSING_OWN_PARENT")
        self.assertEqual(applicability("M2", {"own_parent_authenticated": True,
            "observation_times_h": [0, 1, 2]}, self.data)["status"], "NOT_APPLICABLE_MISSING_LATE_OBSERVATIONS")
        self.assertIn("NEW_CASE", applicability("M2", {"own_parent_authenticated": True,
            "observation_times_h": [0, 1, 2, 4]}, self.data)["status"])

    def test_b5_and_r4_not_reused_as_current_predictions(self):
        for method in ("B5", "R4"):
            self.assertTrue(applicability(method, {}, self.data)["status"].startswith("HISTORICAL"))


if __name__ == "__main__":
    unittest.main()
