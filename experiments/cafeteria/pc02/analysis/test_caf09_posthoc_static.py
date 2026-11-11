"""Unit controls for CAF-09's posthoc analysis. NO simulation imports."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import unittest

import caf09_posthoc_static as x


class StaticAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(Path(os.environ["CAF09_CANONICAL_PLAN"]).read_text())
        cls.results = json.loads(Path(os.environ["CAF09_CANONICAL_RESULTS"]).read_text())
        cls.report = x.audit(cls.plan, cls.results)

    def test_canonical_run_and_no_new_des(self):
        r = self.report
        self.assertTrue(r["NO_NEW_DES_SIMULATIONS"])
        self.assertEqual(r["canonical_github_actions_run"], 41246972768)
        self.assertEqual(r["recorded_checkout_sha"],
                         "51a97a222633b76ec185466022e690a1d792e3d4")
        self.assertEqual(r["recorded_pr_head_sha"],
                         "6a430e213fa9dd5f707846eaeaed2777d62f5f55")
        self.assertEqual(len(r["per_world"]), 66)
        self.assertEqual(len(r["cross_class_graph_summary"]), 22)

    def test_truth_coverage_denominators_and_partial_classification(self):
        for pol in x.POLICIES:
            b = self.report["coverage_by_bank_and_policy"]["single_plus_dual"][pol]
            self.assertEqual((b["represented_worlds"], b["covered_after_K1"],
                              b["covered_after_final"]), (9, 9, 9))
            self.assertEqual(b["out_of_taxonomy_worlds_NOT_IN_DENOMINATOR"], 2)
            b12 = self.report["coverage_by_bank_and_policy"]["single_only"][pol]
            self.assertEqual((b12["represented_worlds"], b12["covered_after_final"]),
                             (3, 3))
            self.assertEqual(b12["out_of_taxonomy_worlds_NOT_IN_DENOMINATOR"], 8)
        self.assertEqual([
            self.report["coverage_by_bank_and_policy"]["single_plus_dual"][p][
                "unique_class_with_true_label"] for p in x.POLICIES
        ], [0, 1, 1])

    def test_unknown_fourth_stage_is_not_mislabelled_no_coverage(self):
        for r in self.report["per_world"]:
            if r["case"].startswith("UNKNOWN_EXTRA_"):
                self.assertIsNone(r["true_class_covered_EVALUATOR_ONLY"])
                self.assertFalse(r["represented_truth_class_in_catalog"])
        self.assertEqual(sum(r["case"] == "UNKNOWN_EXTRA_70" and
                             r["n_classes_after_K2"] == 0
                             for r in self.report["per_world"]), 6)

    def test_nesting_is_about_eligibility_not_outcome(self):
        self.assertEqual(self.report["nested_action_eligibility_violations"], [])
        # 0/2/4 example: overlapping +/-1 bands are NOT transitive.
        pred = {
            "a": {"probe": [0]},
            "b": {"probe": [2]},
            "c": {"probe": [4]},
        }
        action = {"id": "probe"}
        self.assertFalse(x.distinguish(pred,"a","b",action,2))
        self.assertFalse(x.distinguish(pred,"b","c",action,2))
        self.assertTrue(x.distinguish(pred,"a","c",action,2))

    def test_ambiguous_cross_class_graphs_in_expanded_bank(self):
        rows = [r for r in self.report["cross_class_graph_summary"]
                if r["bank"] == "single_plus_dual"]
        self.assertEqual(len(rows), 11)
        self.assertTrue(all(r["cross_class_pairs_robustly_inseparable_across_entire_menu"] > 0
                            for r in rows if r["case"].startswith(("SINGLE_","DUAL_"))))
        self.assertEqual(next(r for r in rows if r["case"]=="UNKNOWN_EXTRA_70")[
            "cross_class_pairs"], 0)
        self.assertEqual(next(r for r in rows if r["case"]=="SINGLE_102_2")[
            "cross_class_pairs_robustly_inseparable_across_entire_menu"], 24)

    def test_selected_actions_are_concentrated(self):
        for b in x.BANKS:
            for pol in x.POLICIES:
                c=self.report["action_selection_by_bank_and_policy"][b][pol]
                self.assertEqual(sum(c.values()), 11)
                self.assertTrue(set(c).issubset({
                    "NO_MEASUREMENT", "prep_dispatch_15_t20", "prep_dispatch_18_t20"}))
        q = self.report["action_selection_by_bank_and_policy"]["single_plus_dual"]
        self.assertEqual(q["STRICT_ORIGINAL"],{"NO_MEASUREMENT":11})
        self.assertEqual(q["ANY_GUARANTEED"]["NO_MEASUREMENT"],5)
        self.assertEqual(q["PAIRWISE_ANY"]["NO_MEASUREMENT"],1)

    def test_tampered_provenance_or_policy_cannot_pass(self):
        altered=deepcopy(self.results)
        altered["checkout_sha"]="f"*40
        with self.assertRaisesRegex(ValueError, "CAF09_AUDIT_MISMATCHED_CHECKOUT"):
            x.audit(self.plan,altered)
        bad=deepcopy(self.plan)
        bad["tolerance_orders"]=2
        with self.assertRaisesRegex(ValueError, "CAF09_AUDIT_POLICY_CHANGED"):
            x.audit(bad,self.results)

    def test_des_and_selector_not_imported(self):
        import sys
        self.assertNotIn("caf07b_umbral_secuencial",sys.modules)
        self.assertNotIn("caf01_des_engine",sys.modules)
        self.assertNotIn("caf09_policy_observability",sys.modules)
        report=x.render(self.report)
        self.assertIn("no es transitiva",report)
        self.assertIn("9/9",report)


if __name__ == "__main__":
    unittest.main(verbosity=2)
