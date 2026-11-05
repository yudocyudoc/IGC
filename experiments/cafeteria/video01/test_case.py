"""Tests: genuine 3-arm boundary, observed visual floors, no inferred POS flows."""
import csv
from pathlib import Path
import shutil
import tempfile
import unittest

from experiments.cafeteria.video01.run import (
    DATA, SOURCES, construction, execute
)
from scripts.arena_v0_contract import assert_same_evidence, arm_view
from scripts.arena_atms import ATMS, Rule

class CV01Tests(unittest.TestCase):
    def test_four_observations_are_visual_only(self):
        p, views = construction()
        self.assertEqual(len(p["construction"]["facts"]), 4)
        self.assertEqual([q["arm_id"] for q in views], ["D", "B", "M"])
        assert_same_evidence(views)
        self.assertFalse(p["observability"]["physical_clock_verified"])
        self.assertNotIn("observations", p["construction"])
        self.assertEqual(p["resources"]["buffalo_provider_calls_allowed"], 0)

    def test_validated_three_native_paths(self):
        r, common, outputs, memory = execute()
        self.assertEqual(set(outputs), {"D", "B", "M"})
        self.assertEqual(r["arm_statuses"], {"D":"PARTIAL","B":"BLOCKED","M":"PARTIAL"})
        self.assertEqual(r["native_hypotheses_selected"], 0)
        self.assertEqual(r["provider_calls"], 0)
        self.assertEqual(r["modelica_runs"], 0)
        self.assertTrue(r["M_native_engineering_graphs_enumerated"] >= 1)
        self.assertEqual(outputs["B"]["native"]["provider_result"], None)
        self.assertEqual(outputs["D"]["native"]["simulation"], "NOT_RUN")
        self.assertFalse(outputs["B"]["native"]["other_arm_outputs_included"])
        self.assertTrue(all(q["submission"]["hypothesis_ids"] == [] for q in outputs.values()))

    def test_atms_does_not_upgrade_assumption_to_fact(self):
        _, _, _, atms = execute()
        self.assertEqual(atms["observed_local_lower_bound"]["minimal_environments"], [[]])
        self.assertEqual(
            atms["conditional_buffer_claim"]["minimal_environments"],
            [["A_REGION_REPRESENTS_COMPLETE_SERVICE_BUFFER"]])
        self.assertIn("not empirical truth", atms["note"])

    def test_tamper_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for name in SOURCES:
                p=root/name
                p.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(DATA/name,p)
            p=root/SOURCES[0]
            s=p.read_text(encoding="utf-8-sig")
            self.assertIn("2888,3,",s)
            p.write_text(s.replace("2888,3,","2888,0,",1),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"P031_THREE_VISIBLE_NOT_SUPPORTED"):
                construction(root)

    def test_artifacts_and_ledger(self):
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td)/"result"
            r, _, _, _=execute(out=dest)
            self.assertEqual(r["local_ledger_revisions"], 3)
            self.assertTrue((dest/"case_ledger.sqlite").is_file())
            self.assertEqual(len(list(dest.glob("*_native_and_submission.json"))),3)
            self.assertTrue((dest/"atms_support.json").is_file())

if __name__=="__main__":
    unittest.main()
