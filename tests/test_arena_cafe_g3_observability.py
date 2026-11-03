"""Tests of RF-03D: observational diagnosis, no invented evidence."""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction as F
import json
import os
from pathlib import Path
import unittest

from scripts.arena_cafe import g3_observability as obs
from scripts.arena_cafe import r2_causal_pos_signal as signal
from scripts.arena_v0_contract import ArenaContractError


class PurePhysicalDiagnostics(unittest.TestCase):
    def test_00_conditional_stop_no_loss_mass_conserves(self):
        times=[F(i) for i in range(10)]
        policy=signal._signal(times,F(10),F(1))
        d=obs.integrate_conditional_horizon(
            policy["segments"],times,F(1),
            1,False,10.,1.,8.1)
        self.assertEqual(set(d),set(range(21)))
        self.assertAlmostEqual(10.,d[10]["input_mass"],places=6)
        self.assertAlmostEqual(10.,d[20]["input_mass"],places=6)
        self.assertAlmostEqual(0.,d[20]["lost_cumulative"],places=6)
        self.assertAlmostEqual(10.,
            d[20]["total_wip"]+d[20]["delivered_cumulative"],delta=0.02)

    def test_01_conditional_stop_with_loss_accounts_mass(self):
        times=[F(i) for i in range(10)]
        policy=signal._signal(times,F(10),F(1))
        d=obs.integrate_conditional_horizon(
            policy["segments"],times,F(1),
            2,True,1.5,1.4,2.)
        self.assertGreater(d[20]["lost_cumulative"],0.1)
        self.assertAlmostEqual(10.,
            d[20]["total_wip"]+d[20]["delivered_cumulative"]+
            d[20]["lost_cumulative"],delta=0.02)
        self.assertTrue(all(d[t]["delivered_cumulative"]>=0
                            for t in d))

    def test_02_envelope_gap_only_when_nonoverlapping(self):
        self.assertEqual(0.,obs._gap(
            {"min":1.,"max":3.},{"min":2.,"max":4.}))
        self.assertEqual(1.,obs._gap(
            {"min":1.,"max":3.},{"min":4.,"max":5.}))

    def test_03_reject_bad_params(self):
        times=[F(i) for i in range(10)]
        policy=signal._signal(times,F(10),F(1))
        for cap in (0,-1,float("nan")):
            with self.subTest(cap=cap),self.assertRaises(ArenaContractError):
                obs.integrate_conditional_horizon(
                    policy["segments"],times,F(1),
                    1,False,cap,1.,2.)


@unittest.skipUnless(os.environ.get("G3_PUBLIC_DIR") and
                     os.environ.get("G3_FROZEN_GRID"),
                     "Requires frozen public O0 and previous RF-03C grid")
class IdentifiabilityO0(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.visible=json.loads((Path(os.environ["G3_PUBLIC_DIR"]) /
                                "O0_VISIBLE.json").read_text())
        cls.prior=json.loads(Path(os.environ["G3_FROZEN_GRID"]).read_text())
        cls.report=obs.build(cls.visible,cls.prior)

    def test_10_all_original_structures_preserved(self):
        r=self.report
        self.assertEqual(6,len(r["families"]))
        self.assertEqual(15,len(r["pairwise_near_best_parameter_envelope_gaps"]))
        self.assertEqual(15,len(r["measurement_opportunities"]))
        self.assertEqual(450,sum(x["all_grid_combinations"]
                                 for x in r["families"]))
        self.assertEqual([25,125,25,125,25,125],
                         [x["all_grid_combinations"]
                          for x in r["families"]])
        self.assertEqual(3,sum(x["loss"] for x in r["families"]))
        self.assertEqual(6,len({x["native_structure_sha256"]
                                for x in r["families"]}))

    def test_11_near_best_envelopes_contain_best(self):
        for f in self.report["families"]:
            self.assertGreaterEqual(f["near_best_grid_count"],1)
            for measure in obs.MEASURES:
                for t,b in f["prediction_bands"][measure].items():
                    val=f["best_trajectory"][int(t)][measure]
                    self.assertLessEqual(b["min"]-val,1e-5)
                    self.assertLessEqual(val-b["max"],1e-5)
            if not f["loss"]:
                self.assertAlmostEqual(0.,
                    f["best_trajectory"][20]["lost_cumulative"],delta=1e-8)

    def test_12_prospective_scenario_not_observed_data(self):
        r=self.report
        self.assertFalse(r["after_cutoff_outcomes_observed"])
        self.assertTrue(r["future_numbers_are_conditional_scenarios_not_forecasts"])
        self.assertEqual("NOT_RUN",r["G4"])
        self.assertEqual("NOT_RUN",r["G5"])
        self.assertEqual("PARTIAL",r["A3"])
        self.assertTrue(r["no_scientific_winner"])
        self.assertTrue(r["observability_caveats"]
                        ["O1_completed_preparation_aggregates_not_independent_experiment"])
        for f in r["families"]:
            self.assertAlmostEqual(15.,
                f["best_trajectory"][20]["input_mass"],delta=1e-7)

    def test_125_loss_distinction_does_not_identify_stock_count(self):
        r=self.report
        group=r["subfamily_diagnosis"]
        self.assertEqual(9,group["pairs_with_different_loss_assumption"])
        self.assertEqual(6,group[
            "pairs_with_same_loss_assumption_but_different_stock_count"])
        for measure,time,expected in (
            ("lost_cumulative",10,9),
            ("delivered_cumulative",20,9),
            ("total_wip",15,8),
            ("delivered_cumulative",15,0),
        ):
            panel=next(x for x in r["measurement_opportunities"]
                       if x["measure"]==measure and
                          x["time_minutes"]==time)
            self.assertEqual(expected,panel["separated_cross_loss_pairs"])
            self.assertEqual(0,panel["separated_within_loss_group_pairs"])
        self.assertTrue(group["known_O0_does_not_identify_true_stock_count"])

    def test_13_tampered_previous_grid_is_rejected(self):
        bad=deepcopy(self.prior)
        bad["D"]["candidates"][0]["best_in_grid"]["mae"]+=0.5
        with self.assertRaises(ArenaContractError):
            obs.build(self.visible,bad)

    def test_14_O1_not_silent_replacement_for_O0(self):
        bad=deepcopy(self.visible)
        bad["observability"]["condition_id"]="O1"
        with self.assertRaises(ArenaContractError):
            obs.build(bad,self.prior)


if __name__=="__main__":
    unittest.main()
