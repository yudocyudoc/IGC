"""Cue-free B4 construction feedback must never pre-identify the suspect equation."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.arena_b4_blind_feedback import make_blind,validate_blind,SCHEMA

ROOT=Path("artifacts")
NATIVE=ROOT/"b4-parent"/"revision-live"/"native-output.json"
CSV=ROOT/"b4-solver"/"BuffaloNative_3aa200a87a3f_res.csv"
REPORT=ROOT/"b4-solver"/"g3-construction-only.json"
VISIBLE=Path("data/synthetic/arena_b_native_visible.json")


class BlindB4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for p in (NATIVE,CSV,REPORT):
            if not p.exists():raise RuntimeError("MISSING_VERIFIED_SOURCE:"+str(p))
        cls.valid=make_blind(NATIVE,CSV,REPORT,VISIBLE)

    def test_neutral_no_suspect_equation_or_mechanistic_derivation(self):
        v=self.valid
        self.assertEqual(v["schema"],SCHEMA)
        self.assertEqual([x["t_hour"] for x in v["points"]],[0,1,2,4])
        self.assertLess(v["physical_integrity"]["material_balance_max_abs_items"],1e-8)
        string=json.dumps(v).lower()
        for forbidden in ("candidate_mechanism_observation","derived_exact_relation",
           "utilization^2","utilization squared","double counting",
           "nominal_capacity","capacity_utilization","completion_capacity",
           "maximum capacity","upper bound","0.6 items/h","0.75 items/h"):
            with self.subTest(word=forbidden):self.assertNotIn(forbidden,string)
        self.assertTrue(v["scope"]["original_budget_exhausted"])
        self.assertTrue(validate_blind(v))

    def test_only_physical_stocks_flows_and_raw_residuals(self):
        for row in self.valid["points"]:
            self.assertEqual(set(row["stock_flow_state"]),
                             {"pending_work","delivered_work","arrivals","completions"})
            self.assertAlmostEqual(
                row["simulated_delivered_items"]-row["observed_delivered_items"],
                row["residual_simulated_minus_observed_items"],places=8)
            self.assertAlmostEqual(row["stock_flow_state"]["delivered_work"],
                                   row["simulated_delivered_items"],places=8)

    def test_reject_hint_injection_even_as_extra_top_level_or_signal(self):
        for key in ("candidate_mechanism_observation","other_arm_result","holdout"):
            data=copy.deepcopy(self.valid)
            data[key]="completion capacity squared"
            with self.subTest(key=key),self.assertRaises(ValueError):
                validate_blind(data)
        data=copy.deepcopy(self.valid)
        data["points"][1]["stock_flow_state"]["nominal_capacity"]=0.6
        with self.assertRaisesRegex(ValueError,"B4_BLIND_OBSERVATION_FIELDS_CHANGED"):
            validate_blind(data)
        data=copy.deepcopy(self.valid)
        data["experiment"]="utilization^2"
        with self.assertRaisesRegex(ValueError,"B4_BLIND_HINT_OR_INFERRED_MECHANISM_LEAKED"):
            validate_blind(data)

    def test_reject_source_tampering_before_remote_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad=Path(tmp)/"B2.csv"
            bad.write_bytes(CSV.read_bytes()+b" ")
            with self.assertRaisesRegex(ValueError,"SOURCE_BYTES_CHANGED"):
                make_blind(NATIVE,bad,REPORT,VISIBLE)
            bad.write_bytes(NATIVE.read_bytes()+b"\n")
            with self.assertRaisesRegex(ValueError,"SOURCE_BYTES_CHANGED"):
                make_blind(bad,CSV,REPORT,VISIBLE)

    def test_reject_residual_tampering(self):
        changed=copy.deepcopy(self.valid)
        changed["points"][2]["simulated_delivered_items"]+=0.123
        with self.assertRaisesRegex(ValueError,"B4_BLIND_RESIDUAL_TAMPERED"):
            validate_blind(changed)


if __name__=="__main__": unittest.main()
