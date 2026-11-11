#!/usr/bin/env python3
"""Posthoc K0 pruning diagnostic: verifies original PR110 outputs untouched."""
import json
from unittest import TestCase,main
from unittest.mock import patch

import caf02_k0_poda_posthoc as diag
import caf02_lab_exploratorio as lab
from experiments.cafeteria.pc01 import caf01_des_engine as des


class PruningTest(TestCase):
    def test_replay_without_any_des_call_and_original_scores_exact(self):
        previous_policy=lab.d.POLICY.read_bytes()
        with patch.object(des,"run_toy_engine",side_effect=AssertionError(
            "DES must never run for posthoc reuse")):
            r=diag.run_diagnostic()
        self.assertEqual(lab.d.POLICY.read_bytes(),previous_policy)
        self.assertTrue(r["no_new_DES_simulations"])
        self.assertEqual(r["unique_K0_K1_signatures"],3)
        self.assertEqual([x["world"] for x in r["worlds"]],list("ABCDE"))
        self.assertTrue(r["no_change_to_official_policy_or_K1_choice"])
        self.assertTrue(r["counterfactual_absolute_K0_only"])
        for row in r["worlds"]:
            self.assertEqual(row["reused_K1_measurement"],
                             {"rate_per_minute":1.5,"t_min":20})
            for arm in ("M","D"):
                x=row[arm]
                n0=sum(x["original_K0_count_by_family"].values())
                na=sum(x["absolute_only_K0_count_by_family"].values())
                self.assertGreaterEqual(na,n0)
                n1=sum(x["original_K1_count_by_family"].values())
                nb=sum(x["absolute_only_K1_count_by_family"].values())
                self.assertGreaterEqual(nb,n1)
                self.assertEqual(nb-n1,x["extra_K1_survivors"])
        # Do not count repeated B/C/D outputs as independent evidence.
        for dup in (2,3):
            for arm in ("M","D"):
                self.assertEqual(r["worlds"][1][arm],r["worlds"][dup][arm])

    def test_astra_rejected_C01_indeed_survives_both_absolute_limits(self):
        w=diag.run_diagnostic()["A_C01_candidate_case"]
        self.assertEqual(w["family"],"C01")
        self.assertEqual(w["candidate_parameters"]["capacity_per_hour"],72)
        self.assertAlmostEqual(w["K0_mae"],.80891,places=4)
        self.assertAlmostEqual(w["C01_relative_K0_cutoff"],.59866,places=4)
        self.assertAlmostEqual(w["predicted_K1_deliveries"],21.42433,places=4)
        self.assertAlmostEqual(w["K1_abs_residual"],.57567,places=4)
        self.assertTrue(w["rejected_only_by_original_K0_relative_pruning"])
        self.assertTrue(w["would_survive_both_absolute_limits"])

    def test_report_says_posthoc_and_does_not_reassign_K1(self):
        value=diag.run_diagnostic()
        report=diag.markdown(value)
        self.assertIn("post hoc",report)
        self.assertIn("NO rediseñado",report)
        self.assertIn("B/C/D",report)
        csv=diag.csv_summary(value)
        self.assertEqual(len(csv.splitlines()),11)


if __name__=="__main__":main()
