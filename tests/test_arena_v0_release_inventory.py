"""Offline release-inventory invariants; this is NOT a V0.1 model test."""
from pathlib import Path
import json
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"data/arena/v0.1-integration-sources.json"
DOC=ROOT/"docs/ARENA_V0_1_INTEGRACION_Y_VERSIONES_2026-10-26.md"

class VersionAndLineageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=json.loads(MANIFEST.read_text())

    def test_lineage_is_explicit_and_reconstructible(self):
        m=self.m
        self.assertEqual(m["schema"],"igc-arena-v0.1-source-inventory/0.1")
        self.assertEqual(m["source_main"]["sha_at_open"],
            "d216a9dd49a200209f90bc740bc28e6df4ad7022")
        self.assertEqual(m["source_main"]["merged_p0_pr"],22)
        self.assertEqual(m["governing_plan"],
          "docs/ARENA_IGC_ATMS_PLAN_IMPLEMENTACION_V1_3_2026-10-25.md")
        self.assertTrue((ROOT/m["governing_plan"]).is_file())
        self.assertTrue(DOC.is_file())

    def test_releases_not_declared_before_gate(self):
        m=self.m
        self.assertEqual(m["target_release"]["status"],"NOT_RELEASED")
        self.assertEqual(m["target_release"]["planned_tag"],"v0.1.0")
        self.assertEqual(m["target_release"]["p0_retrospective_tag"]["status"],"NOT_CREATED")
        self.assertEqual(set(m["release_gates"]),
           {"INT-"+str(n).zfill(2) for n in range(1,10)})
        self.assertTrue(all(x=="NOT_RUN" for x in m["release_gates"].values()))
        self.assertTrue(m["target_release"]["tag_requires_main_and_green_ci"])

    def test_three_separate_methods_not_four(self):
        tracks=self.m["source_tracks"]
        self.assertEqual([t["arm"] for t in tracks],["D","B","M"])
        self.assertEqual(len(set(t["scope"] for t in tracks)),3)
        for t in tracks:
            self.assertEqual(t["promotion"],"SELECTIVE_PORT_REQUIRED")
            self.assertEqual(t["ci_status"],"NOT_RETESTED_ON_INTEGRATION")
            self.assertEqual(t["candidate_prs"],sorted(set(t["candidate_prs"])))
            self.assertGreaterEqual(len(t["candidate_heads"]),2)
            for item in t["candidate_heads"]:
                self.assertIn(item["pr"],t["candidate_prs"])
                self.assertRegex(item["sha"],r"^[0-9a-f]{40}$")

    def test_old_experiments_must_not_become_v0_runtime(self):
        name_map={t["name"]:t for t in self.m["supporting_tracks"]}
        self.assertEqual(name_map["CLEF_EXPERIMENT"]["status"],
                         "HISTORICAL_ONLY_NOT_V0")
        self.assertEqual(name_map["B2_B3_LOW_INPUT_EXPERIMENT"]["status"],
                         "HISTORICAL_ONLY_NOT_RUNTIME")
        self.assertEqual(name_map["D_M_FROZEN_PULSE_EXPERIMENT"]["status"],
                         "HISTORICAL_ONLY_NOT_RUNTIME")
        self.assertEqual(name_map["ATMS_ITERATION_MEMORY"]["status"],
                         "SELECTIVE_PORT_REQUIRED")
        self.assertEqual(name_map["ATMS_ITERATION_MEMORY"]["required_for"],"V0.1")

    def test_no_false_positive_v0_readiness_from_metadata(self):
        m=self.m
        self.assertTrue(any(x!="PASS" for x in m["release_gates"].values()))
        self.assertNotIn("READY_FOR_RELEASE",json.dumps(m))
        self.assertNotIn("MERGED_TO_MAIN",json.dumps(m))

if __name__=="__main__":unittest.main()
