"""RF-03E Astra checks: joint observations, real marginal counterexample, loss domain."""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction as F
import json
import os
from pathlib import Path
import unittest

from scripts.arena_cafe import g3_joint_identification as joint
from scripts.arena_cafe import g3_observability as old
from scripts.arena_cafe import r2_causal_pos_signal as signal
from scripts.arena_v0_contract import ArenaContractError


class JointMathematics(unittest.TestCase):
    def test_00_Astra_counterexample_scalar_overlap_joint_separated(self):
        a=[(1.,2.),(2.,3.)]
        b=[(1.,3.),(2.,2.)]
        for axis in (0,1):
            self.assertEqual(0.,old._gap(
                {"min":min(x[axis] for x in a),
                 "max":max(x[axis] for x in a)},
                {"min":min(x[axis] for x in b),
                 "max":max(x[axis] for x in b)}))
        dist,witness=joint.minimax_joint_distance(a,b)
        self.assertEqual(1.,dist)
        self.assertTrue(0<=witness[0]<2 and 0<=witness[1]<2)

    def test_01_whole_parameter_vector_not_coordinate_stitching(self):
        a=[(0.,10.),(10.,0.)]
        b=[(0.,0.),(10.,10.)]
        self.assertEqual(10.,joint.minimax_joint_distance(a,b)[0])

    def test_02_identical_joint_trajectories_are_not_separated(self):
        a=[(0.,1.,2.),(1.,2.,3.)]
        b=[(5.,6.,7.),(1.,2.,3.)]
        self.assertEqual(0.,joint.minimax_joint_distance(a,b)[0])

    def test_03_reject_bad_or_mismatched_vectors(self):
        cases=[([],[(1.,2.)]), ([(1.,2.)],[(1.,)]),
               ([(1.,float("nan"))],[(1.,2.)]),
               ([(1.,2.)],[])]
        for a,b in cases:
            with self.subTest(a=a,b=b),self.assertRaises(ArenaContractError):
                joint.minimax_joint_distance(a,b)

    def test_04_weak_loss_limit_at_matched_parameters(self):
        event_times=[F(i) for i in range(10)]
        policy=signal._signal(event_times,F(10),F(1))
        segs=policy["segments"]
        without=old.integrate_conditional_horizon(
            segs,event_times,F(1),2,False,1.2,0.7,8.1)
        close=old.integrate_conditional_horizon(
            segs,event_times,F(1),2,True,1.2,0.7,1280.)
        far=old.integrate_conditional_horizon(
            segs,event_times,F(1),2,True,1.2,0.7,20.)
        near_gap=max(abs(without[t]["delivered_cumulative"]-
                         close[t]["delivered_cumulative"])
                     for t in joint.DELIVERY_TIMES)
        far_gap=max(abs(without[t]["delivered_cumulative"]-
                        far[t]["delivered_cumulative"])
                    for t in joint.DELIVERY_TIMES)
        self.assertLess(near_gap,far_gap)
        self.assertLess(close[20]["lost_cumulative"],
                        len(event_times)*20/1280+0.02)


@unittest.skipUnless(os.environ.get("G3_PUBLIC_DIR") and
                     os.environ.get("G3_FROZEN_GRID"),
                     "Requires frozen A1 public O0 and prior RF-03C result")
class JointFrozenO0(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.visible=json.loads((Path(os.environ["G3_PUBLIC_DIR"]) /
                                "O0_VISIBLE.json").read_text())
        cls.previous=json.loads(Path(os.environ["G3_FROZEN_GRID"]).read_text())
        cls.r=joint.build(cls.visible,cls.previous)

    def test_10_15_pairs_seven_joint_plans(self):
        r=self.r
        self.assertEqual(15,len(r["joint_pairwise"]))
        self.assertEqual(7,len(r["joint_plan_summaries"]))
        self.assertEqual(21,len(r["loss_domain_sensitivity"]["results"]))
        self.assertEqual(4,len(r["hypothetical_sensor_absolute_error_orders"]))
        self.assertEqual(set(joint.MEASUREMENT_PLANS),
            {x["plan"] for x in r["joint_plan_summaries"]})
        self.assertTrue(all(p["pairs"]==15 for p in r["joint_plan_summaries"]))

    def test_11_joint_additional_coordinates_cannot_reduce_minimax_distance(self):
        for pair in self.r["joint_pairwise"]:
            d=lambda key:pair["joint_plans"][key][
                "minimum_Linf_joint_distance_orders"]
            self.assertLessEqual(d("deliveries_3_5"),
                                 d("deliveries_3_5_7_9")+1e-6)
            self.assertLessEqual(d("deliveries_3_5_7_9"),
                                 d("deliveries_through_15")+1e-6)
            self.assertLessEqual(d("deliveries_through_15"),
                                 d("deliveries_through_20")+1e-6)
            self.assertLessEqual(d("deliveries_through_20"),
                                 d("deliveries_plus_wip")+1e-6)

    def test_12_common_absolute_screens_are_global_not_per_structure_best(self):
        seq=self.r["common_absolute_compatibility_sensitivity"]["results"]
        self.assertEqual(list(joint.COMMON_ABSOLUTE_MAX_ERRORS),
                         [x["hypothetical_common_absolute_max_error_orders"]
                          for x in seq])
        for i in range(1,len(seq)):
            for prev,new in zip(seq[i-1]["by_family"],seq[i]["by_family"]):
                self.assertEqual(prev["candidate_id"],new["candidate_id"])
                self.assertLessEqual(prev["passing_grid_points"],
                                     new["passing_grid_points"])
        self.assertTrue(self.r["common_absolute_compatibility_sensitivity"][
            "measurement_error_estimated"] is False)

    def test_13_loss_time_domain_original_vs_stress_explicit(self):
        x=self.r["loss_domain_sensitivity"]
        self.assertEqual("NO_OPERATIONAL_UPPER_BOUND_ESTABLISHED",
                         x["model_parameter_limit"])
        self.assertEqual(list(joint.LOSS_DOMAIN_SENSITIVITY_MINUTES[1:]),
                         x["extended_loss_time_minutes"])
        for row in x["results"]:
            self.assertEqual(25,row["same_cap_response_pairs"])
            self.assertLessEqual(row["max_lost_by_20_minutes"],
                                 row["conservative_analytic_loss_upper_bound_orders"]+0.02)
        for n in (1,2,3):
            a=next(x for x in x["results"]
                   if x["n"]==n and x["loss_time_minutes"]==20)
            b=next(x for x in x["results"]
                   if x["n"]==n and x["loss_time_minutes"]==1280)
            self.assertLess(b["max_joint_delivery_difference_across_same_param_pairs"],
                            a["max_joint_delivery_difference_across_same_param_pairs"])

    def test_14_no_blind_prospective_OR_scientific_pass(self):
        r=self.r
        self.assertTrue(r["future_times_are_stop-arrival_scenarios_not_observations"])
        self.assertTrue(r["no_parameter_identifiability_or_structural_recovery_claim"])
        self.assertTrue(r["numerical_margin_is_NOT_a_certified_error_bound"])
        self.assertTrue(r["no_operational_sensor_error_calibration"])
        self.assertEqual("PARTIAL",r["A3"])
        self.assertEqual("NOT_RUN",r["G4"])
        self.assertEqual("NOT_RUN",r["G5"])

    def test_15_mutated_previous_G3_is_rejected(self):
        wrong=deepcopy(self.previous)
        wrong["D"]["candidates"][0]["best_in_grid"]["mae"]+=0.5
        with self.assertRaises(ArenaContractError):
            joint.build(self.visible,wrong)


if __name__=="__main__":
    unittest.main()
