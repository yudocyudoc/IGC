"""F4/F5 readiness: exact non-grid minimum allowances and unresolved obligations."""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction as Q
import json
import os
from pathlib import Path
import unittest

from scripts.arena_cafe import f4_discriminate_readiness as m
from scripts.arena_v0_contract import ArenaContractError


class SymbolicBounds(unittest.TestCase):
    def test_00_exact_original_F4_observation_thresholds(self):
        self.assertEqual((Q(0),Q(2,17)),
                         m.required_absolute_allowance((9,"1"),(9,"15/17")))
        self.assertEqual((Q(6),Q(24,85)),
                         m.required_absolute_allowance((15,"3/5"),(9,"15/17")))

    def test_01_equality_at_required_threshold_is_not_proof_of_truth(self):
        a=(Q(0),Q(2,17));b=(Q(6),Q(24,85))
        self.assertFalse(m.sufficient_to_not_exclude_given_allowances(
            a,Q(0),Q(2,17)-Q(1,1700)))
        self.assertTrue(m.sufficient_to_not_exclude_given_allowances(
            a,Q(0),Q(2,17)))
        self.assertFalse(m.sufficient_to_not_exclude_given_allowances(
            b,Q(5),Q(24,85)))
        self.assertFalse(m.sufficient_to_not_exclude_given_allowances(
            b,Q(6),Q(24,85)-Q(1,8500)))
        self.assertTrue(m.sufficient_to_not_exclude_given_allowances(
            b,Q(6),Q(24,85)))

    def test_02_reject_negative_or_fractional_count_observation(self):
        for predicted,obs in ((("-1","1"),("9","1")),
                              (("1/2","1"),("9","1")),
                              (("9","-1"),("9","1"))):
            with self.subTest(p=predicted),self.assertRaises(
                    (ValueError,ArenaContractError)):
                m.required_absolute_allowance(predicted,obs)
        with self.assertRaises((ValueError,ArenaContractError)):
            m.sufficient_to_not_exclude_given_allowances(
                (Q(0),Q(1)),"-1","0")

    def test_03_refuse_float_as_implicit_sensor_precision(self):
        with self.assertRaises((ValueError,ArenaContractError)):
            m.sufficient_to_not_exclude_given_allowances(
                (Q(0),Q(2,17)),0.,Q(2,17))


@unittest.skipUnless(all(os.environ.get(k) for k in
                      ("DISC01_O0","DISC01_O1","DISC01_WITNESS","DISC01_HJ")),
                     "Requires frozen original A1 O0/O1 and F4 witness/O1 H_j")
class FrozenEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def load(name):
            return json.loads(Path(os.environ[name]).read_text(encoding="utf-8"))
        cls.o0=load("DISC01_O0")
        cls.o1=load("DISC01_O1")
        cls.f4=load("DISC01_WITNESS")
        cls.hj=load("DISC01_HJ")
        cls.out=m.build(cls.o0,cls.o1,cls.f4,cls.hj)

    def test_10_all_fixed_hypotheses_require_nonzero_discrepancies(self):
        x=self.out
        rows={v["candidate_id"]:v for v in
              x["necessary_allowances_for_each_FIXED_hypothesis"]}
        self.assertEqual({
            "PREP_SLOW_A":{"n":"0","time":"2/17"},
            "DISPATCH_SLOW_B":{"n":"6","time":"24/85"}
        },{k:{"n":v["count_error_required_to_avoid_exclusion_orders_exact"],
                "time":v["mean_service_discrepancy_required_minutes_exact"]}
           for k,v in rows.items()})
        self.assertEqual({
            "count_orders_exact":"6",
            "mean_service_minutes_exact":"24/85"
        },{k:v for k,v in
            x["coordinatewise_allowance_needed_to_avoid_excluding_BOTH_FIXED_hypotheses"].items()})
        self.assertEqual("2/17",
            x["necessary_allowance_to_avoid_excluding_at_least_one_FIXED_hypothesis"][
             "mean_service_minutes_exact"])
        self.assertEqual(6,x["development_only_counterfactual_gap_orders"])

    def test_11_no_groundless_sensor_precision_or_admission(self):
        x=self.out
        self.assertTrue(x["no_empirical_allowance_chosen"])
        self.assertTrue(x["no_inferred_sensor_error_from_deterministic_residuals"])
        self.assertTrue(x["no_inferred_model_variability_from_a_single_15_order_trace"])
        self.assertTrue(x["exact_condition_has_no_survivors"])
        self.assertTrue(x["finite_two_hypothesis_model_gap_not_universal_infeasibility"])
        self.assertFalse(x["not_yet_a_pre_registered_test"] is False)
        self.assertEqual("NOT_READY",x["F5_readiness"])

    def test_12_same_information_PM_and_F3_still_pending(self):
        x=self.out
        self.assertEqual("SAME_RAW_LOGS_AND_SENSORS_WITH_WITHOUT_P_PER_ARM",
                         x["PM_comparison"])
        self.assertEqual("NOT_RUN",x["PM_attribution_or_ablation"])
        self.assertTrue(x["no_model_selection_no_parameter_grid_no_new_world"])
        self.assertTrue(x["no_DES_PM4Py_OMC_or_provider_calls"])
        self.assertEqual("PARTIAL",x["A3"])
        self.assertEqual("NOT_RUN",x["G4"])
        self.assertEqual("NOT_RUN",x["G5"])
        self.assertIn("F3_THREE_AUTHENTIC_METHODS",
                      [z["id"] for z in x["F5_readiness_blockers"]])
        self.assertIn("OBSERVATIONAL_ERROR_BUDGET",
                      [z["id"] for z in x["F5_readiness_blockers"]])

    def test_13_do_not_accept_tampered_prior_O1_report(self):
        tamper=deepcopy(self.hj)
        tamper["S1_two_hypothesis_measurement_comparisons"][0][
            "model_prep_completed_services_before_cutoff"]=999
        with self.assertRaises((ValueError,ArenaContractError)):
            m.build(self.o0,self.o1,self.f4,tamper)

    def test_14_do_not_accept_prior_O1_report_of_different_world(self):
        tamper=deepcopy(self.hj)
        tamper["source_o1_snapshot_hash"]="0"*64
        with self.assertRaises((ValueError,ArenaContractError)):
            m.build(self.o0,self.o1,self.f4,tamper)

    def test_15_do_not_accept_relabelled_other_condition(self):
        with self.assertRaises((ValueError,ArenaContractError)):
            m.build(self.o0,self.o0,self.f4,self.hj)

    def test_16_no_fake_F5_from_modified_F4(self):
        tamper=deepcopy(self.f4)
        tamper["F5_new_independent_worlds"]="CREATED"
        with self.assertRaises((ValueError,ArenaContractError)):
            m.build(self.o0,self.o1,tamper,self.hj)


if __name__=="__main__":
    unittest.main()
