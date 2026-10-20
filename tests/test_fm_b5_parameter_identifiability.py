from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.fm_b5_parameter_identifiability import run, simulate, values


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/synthetic/fm_b5_identifiability_plan.json"
PLAN = json.loads(PLAN_PATH.read_text(encoding="utf-8"))


class FmB5ParameterIdentifiabilityTests(unittest.TestCase):
    def test_parameter_ranges_are_explicit_and_include_synthetic_truth(self):
        self.assertEqual(values(PLAN["parameter_ranges"]["maxThroughput"]),
                         [1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4])
        for parameter, value in PLAN["synthetic_data_generation"]["truth_parameters"].items():
            bounds = PLAN["parameter_ranges"][parameter]
            self.assertLessEqual(bounds["minimum"], value)
            self.assertGreaterEqual(bounds["maximum"], value)

    def test_synthetic_fit_and_held_out_pulse_are_separate_and_reproducible(self):
        with tempfile.TemporaryDirectory() as directory:
            first = run(PLAN_PATH, Path(directory) / "one")
            second = run(PLAN_PATH, Path(directory) / "two")
            self.assertIn(first["discrimination_result"], {
                "DISTINGUISHED_ON_HELD_OUT_PULSE", "NOT_DISTINGUISHED_ON_HELD_OUT_PULSE"})
            self.assertFalse(first["structure_of_data_split"]["parameter_fitting_used_held_out_pulse"])
            self.assertFalse(first["structure_of_data_split"]["held_out_data_used_for_selection_or_fitting"])
            self.assertTrue(first["structure_of_data_split"]["independent_noise_seeds"])
            self.assertEqual(first["held_out_pulse_evaluation"]["rmse_by_structure"],
                             second["held_out_pulse_evaluation"]["rmse_by_structure"])
            log_bf = first["held_out_pulse_evaluation"]["log_bayes_factor_CS02_over_CS01"]
            threshold = PLAN["discrimination_rule"]["minimum_absolute_held_out_log_bayes_factor"]
            expected = abs(log_bf) >= threshold
            self.assertEqual(first["discrimination_result"] == "DISTINGUISHED_ON_HELD_OUT_PULSE", expected)

    def test_simulated_cumulative_deliveries_are_finite_and_non_decreasing(self):
        result = simulate(2, 1.8, 0.8, 3.0, 2.0, 16.0, 0.5, 0.01)
        self.assertEqual(len(result), 33)
        self.assertTrue(all(value >= 0 for value in result))
        self.assertTrue(all(right >= left for left, right in zip(result, result[1:])))


if __name__ == "__main__":
    unittest.main()
