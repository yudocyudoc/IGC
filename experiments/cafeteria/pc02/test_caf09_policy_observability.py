"""CAF-09: adversarial controls for policy-vs-observability ablation."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import caf07b_umbral_secuencial as b
import caf09_policy_observability as study


SHA = "a" * 40
HEAD_SHA = "b" * 40


class CAF09PolicyAblationTests(unittest.TestCase):
    def test_weak_rule_can_select_even_without_isolated_hypothesis(self):
        # Two classes, two members each. Every hypothesis has an indistinct
        # rival from another class, but TWO interclass pairs are separable.
        rows = [
            {"id": "a0", "decision_class": "A"},
            {"id": "a3", "decision_class": "A"},
            {"id": "b0", "decision_class": "B"},
            {"id": "b3", "decision_class": "B"},
        ]
        vals = {"a0": 0, "a3": 3, "b0": 0, "b3": 3}
        predictions = {
            i: {a["id"]: [v] * len(a["channels"]) for a in b.ACTIONS}
            for i, v in vals.items()
        }
        survivors = list(vals)
        scored = study.candidate_scores(rows, predictions, survivors)
        self.assertTrue(scored)
        self.assertTrue(all(
            x["guaranteed_count"] == 0 and
            x["separated_cross_class_pairs"] == 2 for x in scored))
        self.assertIsNone(study.choose_relaxed(
            rows, predictions, survivors, "ANY_GUARANTEED")["action"])
        self.assertIsNotNone(study.choose_relaxed(
            rows, predictions, survivors, "PAIRWISE_ANY")["action"])
        self.assertTrue(all(x["cost"] <= b.BUDGET - b.FIRST["cost"]
                            for x in scored))

    def test_no_action_after_no_hypotheses_or_only_one_class(self):
        rows = b.bank(True)
        pred = b.precompute(rows)
        for policy in study.POLICIES[1:]:
            self.assertIsNone(
                study.choose_relaxed(rows, pred, [], policy)["action"])
            self.assertIsNone(
                study.choose_relaxed(rows, pred, [rows[0]["id"]], policy)["action"])
        r = study.structural_observability(rows, pred, [999], [999])
        self.assertEqual(r["affordable_candidate_actions"], 0)
        self.assertEqual(r["strict_eligible_actions"], 0)

    def test_original_selector_and_contract_unchanged(self):
        self.assertIs(study.b.choose_second, b.choose_second)
        self.assertIs(study.b.evaluate_case, b.evaluate_case)
        self.assertIs(study.b.update, b.update)
        self.assertEqual(b.BUDGET, 8)
        self.assertEqual(b.TOLERANCE, 1)
        self.assertEqual(b.DIVERGENCE_THRESHOLD, 2)
        self.assertEqual(b.FIRST_ACTION_ID, "delivered_15_t20")
        self.assertEqual(len(b.scenarios()), 11)
        self.assertEqual(len(b.bank(False)), 12)
        self.assertEqual(len(b.bank(True)), 24)

    def test_rule_boundary_is_strictly_gt_two_for_disjoint_bands(self):
        rows = [
            {"id": "a", "decision_class": "A"},
            {"id": "b", "decision_class": "B"},
        ]
        self.assertEqual(study.cross_class_pairs(
            rows, {"a": {"test": [0]}, "b": {"test": [2]}},
            ["a", "b"], "test"), 0)
        self.assertEqual(study.cross_class_pairs(
            rows, {"a": {"test": [0]}, "b": {"test": [3]}},
            ["a", "b"], "test"), 1)

    def test_runs_three_policies_with_unchanged_worlds_and_pre_k2_logs(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root) / "caf09"
            r = study.run(out, SHA, HEAD_SHA)
            self.assertEqual(r["n_worlds"], 11)
            self.assertEqual(r["n_observability_checks"], 22)
            self.assertEqual(r["n_policy_evaluations"], 66)
            self.assertEqual(r["n_paired_differences"], 44)
            self.assertEqual(r["promotion_gate"], study.GATE)
            self.assertFalse(r["deployment_validated"])
            self.assertFalse(r["causal_mechanism_identified"])
            self.assertEqual(len(list(out.glob("01_CHOICE_*.json"))), 66)
            for bank in study.BANKS:
                for pol in study.POLICIES:
                    metric = r["metrics_by_bank_policy"][bank][pol]
                    self.assertEqual(metric["worlds"], 11)
                    self.assertEqual(sum(metric[k] for k in (
                        "correct", "false_single", "wrong_class",
                        "abstain", "model_gap")), 11)
            # STRICT must match CAF-07B frozen #118 benchmark.
            strict12 = r["metrics_by_bank_policy"]["single_only"]["STRICT_ORIGINAL"]
            strict24 = r["metrics_by_bank_policy"]["single_plus_dual"]["STRICT_ORIGINAL"]
            self.assertEqual((strict12["correct"], strict12["false_single"],
                              strict12["abstain"], strict12["model_gap"],
                              strict12["second_measurements"]),
                             (1, 3, 6, 1, 4))
            self.assertEqual((strict24["correct"], strict24["false_single"],
                              strict24["abstain"], strict24["model_gap"],
                              strict24["second_measurements"]),
                             (0, 0, 10, 1, 0))
            for case in r["evaluations"]:
                self.assertLessEqual(case["cost_spent"], 8)
            for pair in r["paired_differences"]:
                self.assertIn(pair["policy"], study.POLICIES[1:])
            manifest = json.loads((out / "04_MANIFIESTO.json").read_text())
            self.assertEqual(manifest["checkout_sha"], SHA)
            self.assertEqual(manifest["pr_head_sha"], HEAD_SHA)
            for name, digest in manifest["files_sha256"].items():
                self.assertEqual(digest, "sha256:" + hashlib.sha256(
                    (out / name).read_bytes()).hexdigest())
            with self.assertRaisesRegex(ValueError, "CAF09_OUTPUT_EXISTS"):
                study.run(out, SHA, HEAD_SHA)


if __name__ == "__main__":
    unittest.main(verbosity=2)
