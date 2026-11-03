"""O1 measurement-operator tests for the O0-compatible F4 physical rivals."""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction as Q
import json
import os
from pathlib import Path
import unittest

from scripts.arena_cafe import f4_o1_preparation_operator as op
from scripts.arena_cafe import f4_rival_bottleneck_witness as f4
from scripts.arena_v0_contract import ArenaContractError


class PurePhysicalOperator(unittest.TestCase):
    def test_00_exact_stage0_completed_count_uses_conservation(self):
        arrivals=tuple(Q(1,5)+Q(2,5)*j for j in range(15))
        for name,service in op.HYPOTHESES:
            with self.subTest(name=name):
                count=op._completed_preparation(
                    f4._config(service),arrivals,Q(10))
                self.assertTrue(0<count<=15)

    def test_01_one_preparation_server_is_not_one_delivery(self):
        arrivals=tuple(Q(1,5)+Q(2,5)*j for j in range(15))
        for name,service in op.HYPOTHESES:
            c=f4._config(service)
            completed=op._completed_preparation(c,arrivals,Q(10))
            delivered=f4._run(c,arrivals)[-1].delivered_cum_orders
            self.assertGreaterEqual(completed,delivered)

    def test_02_exact_stage_service_is_not_estimated_by_delivery_count(self):
        self.assertNotEqual(Q(f4.A_SERVICE[0]),Q(f4.B_SERVICE[0]))
        self.assertEqual(Q(1),Q(f4.A_SERVICE[0]))
        self.assertEqual(Q(3,5),Q(f4.B_SERVICE[0]))


@unittest.skipUnless(
    all(os.environ.get(k) for k in ("F4O1_O0","F4O1_O1","F4O1_WITNESS")),
    "Needs frozen original O0 O1 and F4 development witness")
class KnownO1Comparison(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        read=lambda name:json.loads(Path(os.environ[name]).read_text())
        cls.o0=read("F4O1_O0")
        cls.o1=read("F4O1_O1")
        cls.witness=read("F4O1_WITNESS")
        cls.report=op.build(cls.o0,cls.o1,cls.witness)

    def test_10_S1_not_compatible_with_either_exact_deterministic_rival(self):
        r=self.report
        self.assertEqual(
            "BOTH_KNOWN_F4_RIVALS_EXCLUDED_BY_EXACT_O1_PREPARATION_OPERATOR",
            r["status"])
        self.assertEqual([],r["exact_matches_under_S1"])
        self.assertEqual(9,r["S1_o1_has_n_completed_preparation_services"])
        self.assertEqual("15/17",r["S1_o1_mean_preparation_service_minutes_exact"])
        pairs=r["S1_two_hypothesis_measurement_comparisons"]
        self.assertEqual(2,len(pairs))
        self.assertFalse(any(p["mean_service_matches_exactly"] for p in pairs))
        self.assertEqual(["1","3/5"],
                         [p["model_prep_mean_service_minutes_exact"] for p in pairs])
        self.assertEqual(["2/17","-24/85"],
                         [p["mean_service_residual_minutes_exact"] for p in pairs])

    def test_11_mean_wait_not_fake_scored(self):
        r=self.report
        self.assertEqual("1204/765",
                         r["S1_o1_mean_preparation_wait_minutes_exact_NOT_SCORED"])
        for p in r["S1_two_hypothesis_measurement_comparisons"]:
            self.assertEqual("1204/765",
                             p["observed_wait_minutes_exact_not_scored"])
        self.assertFalse(r["stage_to_real_business_operator_proven"])
        self.assertFalse(r["real_sensor_error_model_estimated"])

    def test_12_no_false_unique_stocks_or_pm_benefit(self):
        r=self.report
        self.assertTrue(r["no_false_single_winner"])
        self.assertTrue(r["need_F4_design_revision_before_claiming_O1_ambiguous"])
        self.assertEqual("NOT_REQUIRED_FOR_THIS_SPECIFIC_PREPARATION_MEASUREMENT",
                         r["PM_incremental_value_from_this_discriminator"])
        self.assertEqual("NOT_ADJUDICATED",r["PM_general_value"])
        self.assertEqual("NOT_RUN",r["PM_with_without_P_ablation"])
        self.assertEqual("PARTIAL",r["A3"])
        self.assertEqual("NOT_RUN",r["G4"])
        self.assertEqual("NOT_RUN",r["G5"])

    def test_13_original_F4_witness_binding_rejects_tampering(self):
        wrong=deepcopy(self.witness)
        wrong["S0_model_baselines"]["PREP_SLOW_A"][
            "service_minutes_exact"]["preparacion"]="1/2"
        with self.assertRaises((ValueError,ArenaContractError)):
            op.build(self.o0,self.o1,wrong)

    def test_14_reject_O1_from_another_visible_world(self):
        wrong=deepcopy(self.o1)
        wrong["observability"]["world_public_id"]="anotherworld"
        with self.assertRaises((ValueError,ArenaContractError)):
            op.build(self.o0,wrong,self.witness)

    def test_15_reject_relabelling_O0_as_O1(self):
        with self.assertRaises((ValueError,ArenaContractError)):
            op.build(self.o0,self.o0,self.witness)

    def test_16_reject_O1_with_changed_service_statistic(self):
        wrong=deepcopy(self.o1)
        wrong["construction"]["physical_observation"][
            "mean_service_minutes_exact"]="1"
        with self.assertRaises((ValueError,ArenaContractError)):
            op.build(self.o0,wrong,self.witness)

if __name__=="__main__":
    unittest.main()
