"""Regression controls for genuine B2 physical-feedback delivery."""
import copy
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from scripts.arena_b_physical_feedback import (
    PARENT_NATIVE_SHA,PARENT_CSV_SHA,PARENT_REPORT_SHA,
    make_feedback,locked
)

ROOT=Path("artifacts")
NATIVE=ROOT/"b-physical-source"/"revision-live"/"native-output.json"
CSV=ROOT/"b-physical-solver"/"BuffaloNative_3aa200a87a3f_res.csv"
REPORT=ROOT/"b-physical-solver"/"g3-construction-only.json"
VISIBLE=Path("data/synthetic/arena_b_native_visible.json")

class PhysicalFeedbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path in (NATIVE,CSV,REPORT):
            if not path.exists(): raise RuntimeError("REQUIRES_REAL_LOCKED_BUFFALO_ARTIFACT:"+str(path))
    def test_diagnostic_is_real_and_own_arm_only(self):
        d=make_feedback(NATIVE,CSV,REPORT,VISIBLE)
        self.assertEqual(d["arm_id"],"B")
        self.assertEqual(d["schema"],"igc-b-own-physical-construction-feedback/0.1")
        self.assertEqual(len(d["observations_and_physical_state"]),4)
        self.assertEqual([x["t_hour"] for x in d["observations_and_physical_state"]],[0,1,2,4])
        self.assertGreater(abs(d["observations_and_physical_state"][-1]
                                  ["residual_simulated_minus_observed_items"]),.3)
        self.assertEqual(d["construction_adequacy"]["g3_status"],"DESCRIPTIVE_ONLY_NOT_CERTIFIED")
        self.assertTrue(d["no_cross_arm_information"])
        self.assertTrue(d["no_holdout_information"])
        self.assertLess(d["physical_invariants"]["euler_mass_balance_max_residual_items"],1e-8)
        self.assertEqual(d["candidate_mechanism_observation"]["epistemic_status"],
                         "ALGEBRAIC_IDENTITY_NOT_PROOF_OF_CAUSAL_ERROR")
        self.assertNotIn("D2fit_",json.dumps(d))
        self.assertNotIn("MolecularArena",json.dumps(d))
        self.assertEqual(d["revision_type"],
                         "SEPARATELY_AUTHORIZED_EXTENSION_AFTER_ORIGINAL_ROUND_BUDGET")
    def test_each_source_is_byte_pinned(self):
        for f,sha in ((NATIVE,PARENT_NATIVE_SHA),(CSV,PARENT_CSV_SHA),(REPORT,PARENT_REPORT_SHA)):
            with self.subTest(f=f):self.assertEqual(hashlib.sha256(locked(f,sha)).hexdigest(),sha)
    def test_changed_csv_and_report_are_rejected_before_any_provider_call(self):
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/"copy.csv"
            target.write_bytes(CSV.read_bytes()+b" ")
            with self.assertRaisesRegex(ValueError,"SOURCE_BYTES_CHANGED"):
                make_feedback(NATIVE,target,REPORT,VISIBLE)
            fake=Path(temp)/"diagnostic.json"
            fake.write_bytes(REPORT.read_bytes()+b" ")
            with self.assertRaisesRegex(ValueError,"SOURCE_BYTES_CHANGED"):
                make_feedback(NATIVE,CSV,fake,VISIBLE)
    def test_crossarm_gold_and_budget_mutations_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            d=json.loads(VISIBLE.read_text())
            d["construction"]["other_arm_result"]={"D":"do not pass"}
            path=Path(temp)/"v.json"
            path.write_text(json.dumps(d))
            with self.assertRaisesRegex(ValueError,"FOREIGN_EVIDENCE_PRESENT"):
                make_feedback(NATIVE,CSV,REPORT,path)
            d=json.loads(VISIBLE.read_text())
            d["resources"]["max_llm_calls"]=3
            path.write_text(json.dumps(d))
            with self.assertRaisesRegex(ValueError,"ORIGINAL_BUDGET_CHANGED"):
                make_feedback(NATIVE,CSV,REPORT,path)

if __name__=="__main__":
    unittest.main()
