#!/usr/bin/env python3
"""M native G2 synthetic preparer/verifier tests; NO OMC or model integration."""
import csv
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from caf01_m_g2_six_native import (
    prepare,verify,audit_csv,require_github_one_shot, BOUND_MASS
)

class TestMNativeG2Six(unittest.TestCase):
    def synthetic(self,folder,fail=None):
        manifest=prepare(folder)
        for item in manifest["six_predeclared_members"]:
            n=item["ordinal"]
            (folder/f"M_G2_{n}.attempt").write_text("INVOCATION_STARTED\n")
            (folder/f"M_G2_{n}.exit_code").write_text("1\n" if n==fail else "0\n")
            (folder/f"M_G2_{n}.log").write_text("native fictional solver log\n")
            (folder/f"M_G2_{n}.console.txt").write_text("stdout\n")
            with (folder/item["expected_csv"]).open("w",newline="") as fp:
                w=csv.DictWriter(fp,fieldnames=["time","inTransit","deliveredTotal"])
                w.writeheader()
                for i in range(81):
                    t=i/120
                    w.writerow({"time":t,"inTransit":72*min(t,1/3),
                                "deliveredTotal":0})
        return manifest

    def test_prepare_six_exact_preselected_sources_no_solvers(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/"M"
            p=prepare(folder)
            self.assertEqual(len(p["six_predeclared_members"]),6)
            self.assertEqual([(x["structure"],x["capacity"]) for x in p["six_predeclared_members"]],
                             [(s,c) for s in ("C00","C01","C02") for c in (20,72)])
            self.assertEqual(p["native_invocations_at_prepare"],0)
            self.assertFalse(p["evaluation_observations_read"])
            self.assertFalse(p["D_or_B_results_read"])
            self.assertEqual(len(list(folder.glob("M_G2_*.mos"))),6)
            for n in range(1,7):
                script=(folder/f"M_G2_{n}.mos").read_text()
                self.assertEqual(script.count("simulate("),1)
                self.assertEqual(script.count("checkModel("),1)
                self.assertNotIn("stopTime=8",script)
            with self.assertRaisesRegex(ValueError,"M_G2_OUTPUT_EXISTS"):
                prepare(folder)

    def test_synthetic_six_pass_with_csv_and_individual_receipts(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/"M"
            self.synthetic(folder)
            r=verify(folder)
            self.assertEqual(r["status"],"ALL_SIX_M_NATIVE_G2_PASS")
            self.assertEqual(r["native_construction_simulations_consumed"],6)
            self.assertTrue(all(x["balance_max_abs"]<1e-8 for x in r["native_candidates"]))
            self.assertEqual(len(list(folder.glob("M_G2_*_receipt.json"))),6)

    def test_synthetic_failure_preserves_all_receipts(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/"M"
            self.synthetic(folder,fail=2)
            r=verify(folder)
            self.assertEqual(r["status"],"PARTIAL_M_NATIVE_G2")
            self.assertEqual([x["status"] for x in r["native_candidates"]],
                             ["PASS","FAIL","PASS","PASS","PASS","PASS"])
            self.assertEqual(r["native_construction_simulations_consumed"],6)
            self.assertEqual(r["native_candidates"][1]["reason_code"],
                             "M_G2_NATIVE_SOLVER_EXIT_NONZERO_OR_MISSING")
            self.assertEqual(len(list(folder.glob("M_G2_*_receipt.json"))),6)
            self.assertTrue((folder/"M_G2_AGGREGATE.json").is_file())

    def test_balance_fails_independent_of_delivered_fit(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/"M"
            self.synthetic(folder)
            p=folder/"M_G2_3_res.csv"
            with p.open("w",newline="") as fp:
                w=csv.DictWriter(fp,fieldnames=["time","inTransit","deliveredTotal"])
                w.writeheader()
                for i in range(81):
                    t=i/120
                    w.writerow({"time":t,"inTransit":72*min(t,1/3)+1,
                                "deliveredTotal":0})
            r=verify(folder)
            self.assertEqual(r["native_candidates"][2]["status"],"FAIL")
            self.assertEqual(r["native_candidates"][2]["reason_code"],
                             "M_G2_NATIVE_MASS_BALANCE_FAILED")
            self.assertEqual(r["native_candidates"][0]["status"],"PASS")

    def test_only_first_manual_main_dispatch(self):
        good={"GITHUB_ACTIONS":"true","GITHUB_REF":"refs/heads/main",
              "GITHUB_EVENT_NAME":"workflow_dispatch",
              "GITHUB_REPOSITORY":"yudocyudoc/IGC",
              "GITHUB_RUN_NUMBER":"1","GITHUB_RUN_ATTEMPT":"1"}
        with patch.dict(os.environ,good,clear=True):
            require_github_one_shot()
        for k,v in (("GITHUB_REF","refs/heads/test"),("GITHUB_RUN_ATTEMPT","2"),
                    ("GITHUB_RUN_NUMBER","2"),("GITHUB_EVENT_NAME","pull_request")):
            with patch.dict(os.environ,{**good,k:v},clear=True):
                with self.assertRaisesRegex(ValueError,"M_G2_FIRST_MANUAL_MAIN_RUN_ONLY"):
                    require_github_one_shot()

if __name__=="__main__":
    unittest.main()
