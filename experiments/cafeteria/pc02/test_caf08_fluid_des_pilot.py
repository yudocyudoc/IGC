"""CAF-08 falsifiable controls: passive equivalence, intervention, balances, convergence.

Run against the actual repository CAF-01 engine, not a local transcription.
"""
import unittest

from caf08_fluid_des_pilot import (
    configuration, des_read, delayed_fluid, simple_fluid, worlds, run
)
from experiments.cafeteria.pc01 import caf01_des_engine as des


class FluidDESReviewTests(unittest.TestCase):
    def test_native_des_import(self):
        self.assertTrue(
            des.__file__.replace("\\", "/").endswith(
                "experiments/cafeteria/pc01/caf01_des_engine.py"),
            des.__file__
        )

    def test_passive_pair_indistinguishable_for_declared_observations(self):
        a, b = configuration((0,), 75), configuration((0, 1), 75)
        for rate, minute in ((1.2, 10), (1.5, 20), (1.8, 20)):
            with self.subTest(rate=rate, minute=minute):
                self.assertEqual(simple_fluid(a, rate, minute),
                                 simple_fluid(b, rate, minute))
                da, db = des_read(a, rate, minute), des_read(b, rate, minute)
                self.assertEqual(da["delivered"], db["delivered"])
                self.assertEqual(da["waiting"], db["waiting"])

    def test_prep_only_intervention_distinguishes_and_late_read_erases(self):
        a = configuration((0,), 75)
        b = configuration((0, 1), 75)
        a_new = configuration((0,), 105)
        b_new = configuration((1,), 75)
        b_new["stages"][0] = {"servers": 1, "service_minutes": "4/7"}
        self.assertEqual(simple_fluid(a_new, 1.5, 20)["delivered"], 30)
        self.assertEqual(simple_fluid(b_new, 1.5, 20)["delivered"], 25)
        self.assertEqual(des_read(a, 1.5, 20)["delivered"], 22)
        self.assertEqual(des_read(b, 1.5, 20)["delivered"], 22)
        self.assertEqual(des_read(a_new, 1.5, 20)["delivered"], 26)
        self.assertEqual(des_read(b_new, 1.5, 20)["delivered"], 22)
        self.assertEqual(des_read(b_new, 1.5, 20)["waiting"], [0, 5, 0])
        self.assertEqual(des_read(a_new, 1.5, 40)["delivered"], 30)
        self.assertEqual(des_read(b_new, 1.5, 40)["delivered"], 30)

    def test_conservation_all_eleven_worlds(self):
        for case, _kind, cfg in worlds():
            for rate, minute in ((1.2, 10), (1.5, 20), (1.8, 20), (1.5, 40)):
                with self.subTest(case=case, rate=rate, minute=minute):
                    observed = des_read(cfg, rate, minute)
                    self.assertEqual(observed["accepted"],
                                     observed["delivered"] + observed["pending"])
                    self.assertEqual(observed["pending"],
                                     sum(observed["waiting"]) + sum(observed["serving"]))
                    fluid = delayed_fluid(cfg, rate)[minute]
                    self.assertAlmostEqual(fluid["accepted"],
                                           fluid["delivered"] + fluid["pending"], places=5)
                    self.assertAlmostEqual(fluid["pending"],
                                           sum(fluid["waiting"]) + sum(fluid["serving"]), places=5)
                    self.assertTrue(all(v >= -1e-8 for v in
                                        fluid["waiting"] + fluid["serving"]))
                    self.assertTrue(all(v <= stage["servers"] + 1e-7
                                        for v, stage in zip(fluid["serving"], cfg["stages"])))

    def test_fluid_time_step_refinement(self):
        # Convergence test is not calibration to DES.
        for limited, cap in (((0,), 75), ((0, 1), 75), ((1, 2), 55)):
            cfg = configuration(limited, cap)
            coarse = delayed_fluid(cfg, 1.5, dt=0.01)
            fine = delayed_fluid(cfg, 1.5, dt=0.0025)
            for minute in (10, 20, 40):
                with self.subTest(limited=limited, cap=cap, minute=minute):
                    self.assertLess(abs(coarse[minute]["delivered"] -
                                        fine[minute]["delivered"]), 0.03)

    def test_error_denominators_and_sign_are_explicit(self):
        data = run()
        summary = data["summary"]
        self.assertEqual(summary["signed_error_convention"], "DES_MINUS_FLUID")
        self.assertEqual(summary["n_during_pulse"], 33)
        self.assertEqual(summary["n_after_pulse"], 11)
        self.assertAlmostEqual(summary["lagged_during_pulse"]["mae"], 0.3711, places=4)
        self.assertAlmostEqual(summary["lagged"]["mae"], 0.2783, places=4)
        self.assertEqual(summary["lagged_after_pulse"]["mae"], 0.0)
        self.assertEqual(summary["zero_lag"]["bias"], -3.3586)
        self.assertEqual(summary["lagged_during_pulse"]["max_abs"], 0.5833)
        for row in data["comparisons"]:
            if row["minute"] == 40:
                self.assertAlmostEqual(
                    row["difference_delivered_des_minus_lagged"], 0.0, places=6)

    def test_local_baseline_is_reproduced_not_claimed_validated(self):
        data = run()
        self.assertEqual(data["summary"]["n_worlds"], 11)
        self.assertEqual(data["summary"]["n_observation_rows"], 44)
        # Frozen exploratory values from an unverified local DES transcription.
        # The native module may disconfirm them; do NOT update to make CI green.
        self.assertAlmostEqual(data["summary"]["zero_lag"]["mae"], 3.3586, places=4)
        self.assertAlmostEqual(data["summary"]["lagged"]["mae"], 0.2783, places=4)
        self.assertFalse(data["truth_only_in_evaluator"])
        self.assertTrue(data["experimental_only"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
