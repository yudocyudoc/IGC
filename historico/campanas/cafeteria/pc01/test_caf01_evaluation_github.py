#!/usr/bin/env python3
"""Only fabricated numbers and mocks. Never invokes the reserved DES world."""
import os
import unittest
from fractions import Fraction
from types import SimpleNamespace
from unittest.mock import patch
import caf01_evaluation_github as ev


def toy_snapshots():
    a = ev.EXPECTED_ACCEPTED
    d = (0, 1, 4, 7, 11, 16, 20)
    return tuple(SimpleNamespace(
        t_min=Fraction(t), accepted_cum_orders=x,
        delivered_cum_orders=y, pending_orders=x-y,
        stage_waiting=(x-y,), stage_in_service=(0,))
        for t, x, y in zip(ev.TIMES, a, d))


def fake_bundle():
    return {
        "g3_lock": {
            "arm_forecasts": {
                "D": {"status": "ABSTAIN_POINT_PARAMETER_UNIDENTIFIABLE",
                      "prediction": None},
                "M": {"status": "CONDITIONAL_POINT_FORECAST_NOT_STRUCTURAL_ID",
                      "prediction": [1, 4, 7, 11, 16, 20]},
                "B": {"status": "NO_VALID_CANDIDATE", "prediction": None},
            }
        },
        "references": {"references": {
            "REF_CAF": {"predicted_delivered": [1, 2, 5, 9, 12, 14]},
            "REF_SCALE": {"predicted_delivered": [2, 6, 9, 13, 20, 25]},
        }}
    }


class EvaluationTests(unittest.TestCase):
    def test_physical_snapshot_valid(self):
        delivered, rows = ev.validate_physical_snapshots(toy_snapshots())
        self.assertEqual(delivered, [1, 4, 7, 11, 16, 20])
        self.assertEqual(rows[-1]["accepted_cum_orders"], 30)

    def test_negative_balance_rejected(self):
        s = list(toy_snapshots())
        s[2] = SimpleNamespace(**{**vars(s[2]), "pending_orders": 100})
        with self.assertRaisesRegex(ev.EvaluationBlocked, "PHYSICAL"):
            ev.validate_physical_snapshots(s)

    def test_future_overdelivery_rejected(self):
        s = list(toy_snapshots())
        s[4] = SimpleNamespace(**{**vars(s[4]), "delivered_cum_orders": 31})
        with self.assertRaises(ev.EvaluationBlocked):
            ev.validate_physical_snapshots(s)

    def test_scoring_excludes_d_and_buffalo(self):
        observed = [1, 4, 7, 11, 16, 20]
        score = ev.score_locked(fake_bundle(), observed)
        self.assertEqual(set(score["scores"]), {"M", "REF-CAF", "REF-SCALE"})
        self.assertEqual(score["scores"]["M"]["MAE_delivered_orders"], 0)
        self.assertIsNone(score["D"]["competitive_MAE"])
        self.assertIsNone(score["Buffalo"]["competitive_MAE"])
        self.assertTrue(score["comparisons"]["REF-CAF"]["at_least_one_order_gain"])

    def test_reference_abstention_kept(self):
        pkg = fake_bundle()
        pkg["references"]["references"]["REF_CAF"]["predicted_delivered"] = None
        score = ev.score_locked(pkg, [1, 4, 7, 11, 16, 20])
        self.assertNotIn("REF-CAF", score["scores"])
        self.assertEqual(score["comparisons"]["REF-CAF"]["status"],
                         "REFERENCE_ABSTAINED_NO_COMPARISON")

    def test_no_dispatch_without_explicit_waiver(self):
        env = {
            "GITHUB_ACTIONS": "true",
            "GITHUB_REPOSITORY": "yudocyudoc/IGC",
            "GITHUB_REF": "refs/heads/main",
            "GITHUB_EVENT_NAME": "workflow_dispatch",
            "GITHUB_RUN_NUMBER": "1",
            "GITHUB_RUN_ATTEMPT": "1",
            "CAF01_EVAL_CONFIRMATION": ev.CONFIRM,
            "CAF01_G5_WAIVER": "INVALID",
        }
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaisesRegex(ev.EvaluationBlocked, "WAIVER"):
                ev.github_one_shot_guard()
            os.environ["CAF01_G5_WAIVER"] = ev.WAIVER
            ev.github_one_shot_guard()
            os.environ["GITHUB_RUN_ATTEMPT"] = "2"
            with self.assertRaises(ev.EvaluationBlocked):
                ev.github_one_shot_guard()

    def test_preflight_contract_never_calls_des(self):
        with patch.object(ev, "run_toy_engine", side_effect=AssertionError("DES FORBIDDEN")):
            # Synthetic suite exercises validation/scoring only, without a
            # package from a real secret or DES invocation.
            ev.validate_physical_snapshots(toy_snapshots())
            ev.score_locked(fake_bundle(), [1, 4, 7, 11, 16, 20])


if __name__ == "__main__":
    unittest.main()
