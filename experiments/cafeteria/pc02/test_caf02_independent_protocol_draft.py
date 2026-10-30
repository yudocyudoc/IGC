#!/usr/bin/env python3
"""Offline CAF02 scoring contract regressions, NO evaluation truth source."""
import json
import unittest
from pathlib import Path

import caf02_k2_set_scoring as k
import caf02_numerical_margin_preflight as n

BASE=Path(__file__).resolve().parent
POLICY=BASE/"CAF02_INDEPENDENT_K0K1K2_POLICY_PROPOSAL_2026-10-30.json"


def family(curve,spread=0.0):
    return {"C00":{"lower":[y-spread for y in curve],
                   "upper":[y+spread for y in curve],
                   "candidate_count":1},
            "C01":None}


def empty():
    return {"C00":None,"C01":None}


class ProposedIndependentScoringTests(unittest.TestCase):
    def test_singleton_loss_is_MAE(self):
        t=[1,2,3,4,5,6]
        p=[2,2,4,4,6,6]
        report=k.summarize_envelope(p,p,t)
        self.assertEqual(report["status"],"POINT_ELIGIBLE")
        self.assertAlmostEqual(report["set_loss_mean"],sum(
            abs(a-b) for a,b in zip(p,t))/6)
        self.assertEqual(report["point_MAE"],report["set_loss_mean"])

    def test_wide_interval_penalized_even_when_truth_covered(self):
        truth=[4,6,8,10,12,14]
        lower=[v-3 for v in truth]
        upper=[v+3 for v in truth]
        report=k.summarize_envelope(lower,upper,truth)
        self.assertEqual(report["coverage_count"],6)
        self.assertEqual(report["set_loss_mean"],3)
        self.assertEqual(report["status"],"SET_ONLY_POINT_ABSTENTION")
        self.assertIsNone(report["point_MAE"])

    def test_missed_interval_penalized(self):
        y=[3,5,7,9,11,13]
        lower=[0,2,4,6,8,10]
        upper=[1,3,5,7,9,11]
        v=k.summarize_envelope(lower,upper,y)
        self.assertAlmostEqual(v["set_loss_mean"],2.5)
        self.assertEqual(v["coverage_count"],0)

    def test_no_prediction_abstains_and_cannot_win(self):
        t=[1,2,3,4,5,6]
        r=k.adjudicate(empty(),family(t),t,t,t)
        self.assertEqual(r["status"],"NOT_PAIRED_ABSTENTION")
        self.assertIsNone(r["paired_set_loss_gain_orders"])
        self.assertIsNone(r["revision_predictive_improvement_pass"])
        self.assertIsNone(r["K0"]["set_loss_mean"])
        self.assertEqual(r["REF_CAF"]["set_loss_mean"],0)

    def test_revision_gain_paired_and_references_separate(self):
        y=[1,2,3,4,5,6]
        old=[2,3,4,5,6,7]
        result=k.adjudicate(family(old),family(y),old,old,y)
        self.assertEqual(result["status"],"PAIRED")
        self.assertAlmostEqual(result["paired_set_loss_gain_orders"],1)
        self.assertTrue(result["revision_predictive_improvement_pass"])
        self.assertEqual(result["REF_CAF"]["set_loss_mean"],1)
        self.assertEqual(result["REF_SCALE"]["set_loss_mean"],1)

    def test_identical_K0_K1_is_no_revision_gain(self):
        y=[1,2,3,4,5,6]
        prior=family([2,3,4,5,6,7])
        result=k.adjudicate(prior,prior,y,y,y)
        self.assertAlmostEqual(result["paired_set_loss_gain_orders"],0)
        self.assertFalse(result["revision_predictive_improvement_pass"])

    def test_no_invalid_envelope_or_unreal_delivery_series(self):
        y=[1,2,3,4,5,6]
        with self.assertRaises(k.InvalidK2Score):
            k.summarize_envelope(y,[0,1,2,3,4,5],y)
        with self.assertRaises(k.InvalidK2Score):
            k.summarize_envelope([1,1,0,1,1,1],y,y)

    def test_proposed_policy_is_preexecution_and_rules_match(self):
        x=json.loads(POLICY.read_text(encoding="utf-8"))
        self.assertEqual(x["status"],
                         "DRAFT_FOR_REVIEW_NOT_FROZEN_NOT_AUTHORIZED")
        self.assertTrue(x["no_world_runs_authorized"])
        self.assertEqual(x["k0"]["delivered_observation_times_minutes"],[5,10])
        self.assertEqual(x["k1"]["effective_revision_tolerance_orders"],
                         x["k1"]["absolute_residual_tolerance_orders"]+
                         x["k1"]["numerical_allowance_orders"])
        self.assertEqual(x["k2"]["point_eligibility_max_width_orders"],2)
        self.assertEqual(x["k2"]["set_loss_definition"],
                         "MEAN_6_OF_HALF_ENVELOPE_WIDTH_PLUS_DISTANCE_TO_INTERVAL")
        self.assertEqual(x["resource_ceiling"]["world_DES"]["total_max"],3)
        self.assertEqual(x["candidate_parameters"]["total_nominal_grid_count_C00"],32)
        self.assertEqual(x["candidate_parameters"]["total_nominal_grid_count_C01"],96)
        self.assertEqual(len(x["k1"]["menu"]),3)
        self.assertEqual(x["resource_ceiling"]["selected_K1_candidate_forecasts_max"],
                         128*3)
        self.assertEqual(x["resource_ceiling"]["K2_prior_and_posterior_candidate_forecasts_max"],
                         128*2)
        self.assertEqual(x["resource_ceiling"]["total_candidate_trajectory_calculations_upper_bound"],
                         128+384+256)
        self.assertEqual(x["custody"]["G5_world_source_and_private_parameters_before_K0"],
                         "REQUIRED_EXTERNAL_WITNESS")

    def test_numerical_input_guard_rejects_non_draft(self):
        x=json.loads(POLICY.read_text(encoding="utf-8"))
        x["status"]="AUTHORIZED"
        with self.assertRaises(AssertionError):
            n.inspect(x)


if __name__=="__main__":
    unittest.main()
