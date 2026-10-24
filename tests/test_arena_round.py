"""Adversarial round protocol: B0, isolation, budgets, LOCK, reserve consumption."""
import copy
from pathlib import Path
import tempfile
import unittest

from scripts.arena_round import (
    RoundError, LANES, b0_submission, evaluate_once, hash_obj, lock_round,
    prepare, score_locked, exclusive_json, verify_lock, validate_submission
)


def fixture():
    budgets = {lane: dict(llm_calls=4, tokens=4000, simulations=8,
                          human_minutes=30, retries=0) for lane in LANES}
    spec = dict(schema="igc-arena-round/0.1", synthetic=True,
                investigation_id="INV-QUEUE-01", round_id="ROUND-01",
                question="One queue stage or two?", observable_id="delivered",
                as_known_at="2026-10-24T09:00:00Z", allowed_lanes=list(LANES),
                target_times=[3, 4, 5],
                observability=dict(kind="observed", unit="orders",
                                   instrument="synthetic cumulative counter"),
                evaluation_metric="RMSE", blindness_claim="NOT_ESTABLISHED",
                max_retries=0, budgets=budgets)
    primary = dict(investigation_id=spec["investigation_id"],
                   observable_id="delivered", unit="orders",
                   times=[0, 1, 2], values=[0, 2, 4], sources=["synthetic:obs-01"])
    reserve = dict(round_id=spec["round_id"], observable_id="delivered",
                   unit="orders", reserve_id="RESERVE-01",
                   times=[3, 4, 5], values=[5, 7, 9])
    return spec, primary, reserve


def submissions(views, spec):
    b0 = b0_submission(views["B0"], spec)
    d = dict(schema=spec["schema"], round_id=spec["round_id"], lane="D",
             view_hash=views["D"]["view_hash"], status="SUBMITTED",
             producer="molecular-v0",
             proposals=[dict(candidate_id="CS-01", kind="structure", mechanism="one stage",
                             predictions=[4.8, 7.3, 9.2]),
                        dict(candidate_id="CS-02", kind="structure", mechanism="two stages",
                             predictions=[5.1, 7.1, 8.9])],
             unknowns=["Not identified from primary data"], objections=[],
             cost=dict(llm_calls=0, tokens=0, simulations=2,
                       human_minutes=3, retries=0))
    def absent(lane):
        return dict(schema=spec["schema"], round_id=spec["round_id"], lane=lane,
                    view_hash=views[lane]["view_hash"],
                    status="NOT_IMPLEMENTED" if lane == "S" else "ABSTAINED",
                    producer="unavailable", proposals=[],
                    unknowns=["Independent assessment not supplied"], objections=[],
                    cost=dict(llm_calls=0, tokens=0, simulations=0,
                              human_minutes=0, retries=0))
    return {"B0": b0, "D": d, "S": absent("S"), "P": absent("P")}


class ArenaRoundTests(unittest.TestCase):
    def setUp(self):
        self.spec, self.primary, self.reserve = fixture()
        self.views = prepare(self.spec, self.primary)
        self.subs = submissions(self.views, self.spec)

    def lock(self):
        return lock_round(self.spec, self.views, self.subs, run_ref="actions/test-only")

    def test_same_primary_and_b0_is_not_enriched(self):
        self.assertEqual(set(self.views), set(LANES))
        for lane in LANES:
            self.assertEqual(self.views[lane]["primary_hash"], hash_obj(self.primary))
        self.assertIsNone(self.views["B0"]["retrieval"])
        self.assertEqual(self.subs["B0"]["proposals"][0]["predictions"], [4, 4, 4])
        validate_submission(self.subs["B0"], self.views["B0"])

    def test_views_isolated_no_holdout_or_cross_submission(self):
        self.assertEqual(len({v["view_hash"] for v in self.views.values()}), 4)
        self.assertNotIn("submissions", str(self.views))
        self.assertNotIn("RESERVE-01", str(self.views))

    def test_lock_preserves_abstentions(self):
        lock = self.lock()
        verify_lock(lock)
        self.assertEqual(lock["evaluation_status"], "LOCKED_NOT_EVALUATED")
        self.assertEqual(lock["submissions"]["S"]["status"], "NOT_IMPLEMENTED")
        self.assertEqual(lock["blindness"], "NOT_ESTABLISHED")

    def test_manipulated_baseline_rejected(self):
        self.subs["B0"]["proposals"][0]["predictions"][0] = 999
        with self.assertRaisesRegex(RoundError, "baseline is not"):
            self.lock()

    def test_view_hash_substitution_rejected(self):
        self.views["D"]["view_hash"] = "sha256:spoof"
        self.subs["D"]["view_hash"] = "sha256:spoof"
        with self.assertRaisesRegex(RoundError, "view tampered"):
            self.lock()

    def test_locked_prediction_tampering_rejected(self):
        lock = self.lock()
        lock["submissions"]["D"]["proposals"][0]["predictions"][0] = 999
        with self.assertRaisesRegex(RoundError, "LOCK_TAMPERED"):
            verify_lock(lock)

    def test_gold_in_constructor_rejected(self):
        for location in ("spec", "primary"):
            spec, primary, _ = fixture()
            (spec if location == "spec" else primary)["gold"] = "CS-02"
            with self.assertRaisesRegex(RoundError, "hidden/reserved"):
                prepare(spec, primary)

    def test_cross_lane_retrieval_rejected(self):
        bundle = {"lane": "S", "investigation_id": self.spec["investigation_id"],
                  "as_known_at": "2026-10-24T09:00:00+00:00", "holdout_accessed": False}
        with self.assertRaisesRegex(RoundError, "wrong lane"):
            prepare(self.spec, self.primary, {"D": bundle})

    def test_retrieval_that_saw_reserve_rejected(self):
        bundle = {"lane": "D", "investigation_id": self.spec["investigation_id"],
                  "as_known_at": "2026-10-24T09:00:00+00:00", "holdout_accessed": True}
        with self.assertRaisesRegex(RoundError, "reserved evidence"):
            prepare(self.spec, self.primary, {"D": bundle})

    def test_budget_cap_enforced(self):
        bad = copy.deepcopy(self.subs["D"])
        bad["cost"]["tokens"] = 9999
        with self.assertRaisesRegex(RoundError, "budget exceeded"):
            validate_submission(bad, self.views["D"])

    def test_p_cannot_assert_topology_predictions(self):
        bad = copy.deepcopy(self.subs["P"])
        bad["status"] = "SUBMITTED"
        bad["proposals"] = [{"candidate_id": "P-1", "kind": "parameter_proposal",
                             "predictions": [1, 2, 3]}]
        with self.assertRaisesRegex(RoundError, "not a structural"):
            validate_submission(bad, self.views["P"])

    def test_construction_data_must_precede_evaluation(self):
        self.primary["times"][-1] = 3
        with self.assertRaisesRegex(RoundError, "overlaps"):
            prepare(self.spec, self.primary)

    def test_evaluator_scores_b0_and_d_without_claiming_blindness(self):
        result = score_locked(self.lock(), self.reserve, custodian_ref="tester")
        self.assertEqual(result["metric"], "RMSE")
        self.assertEqual(result["scores"]["S"]["status"], "NOT_IMPLEMENTED")
        self.assertEqual(result["scores"]["P"]["status"], "ABSTAINED")
        self.assertGreater(result["scores"]["B0"]["candidates"][0]["rmse"], 0)
        self.assertEqual(result["blindness"], "NOT_ESTABLISHED_BY_SOFTWARE")
        self.assertNotIn("values", result)

    def test_wrong_reserve_grid_rejected(self):
        reserve = copy.deepcopy(self.reserve)
        reserve["times"] = [3, 4, 6]
        with self.assertRaisesRegex(RoundError, "grid mismatch"):
            score_locked(self.lock(), reserve, custodian_ref="tester")

    def test_same_reserve_consumed_only_once_locally(self):
        with tempfile.TemporaryDirectory() as directory:
            lock = self.lock()
            first = evaluate_once(lock, self.reserve, Path(directory), custodian_ref="tester")
            self.assertEqual(first["consumption"], "HOLDOUT_CONSUMED_FOR_THIS_ROUND")
            with self.assertRaisesRegex(RoundError, "IMMUTABLE_ARTIFACT_EXISTS"):
                evaluate_once(lock, self.reserve, Path(directory), custodian_ref="tester")

    def test_lock_output_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lock.json"
            exclusive_json(path, self.lock())
            with self.assertRaisesRegex(RoundError, "IMMUTABLE_ARTIFACT_EXISTS"):
                exclusive_json(path, self.lock())

    def test_nan_and_inf_predictions_rejected(self):
        for value in (float("nan"), float("inf")):
            bad = copy.deepcopy(self.subs["D"])
            bad["proposals"][0]["predictions"][1] = value
            with self.assertRaisesRegex(RoundError, "finite numbers"):
                validate_submission(bad, self.views["D"])

    def test_spec_change_after_views_rejected(self):
        spec = copy.deepcopy(self.spec)
        spec["budgets"]["D"]["simulations"] = 9
        with self.assertRaisesRegex(RoundError, "spec changed"):
            lock_round(spec, self.views, self.subs, run_ref="test")


if __name__ == "__main__":
    unittest.main()
