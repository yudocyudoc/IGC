from __future__ import annotations

import copy
import json
import unittest

from scripts.fm_b4_discriminating_analysis import (
    compare_candidates, explain_structure, source_profile,
)
from scripts.compose_molecular_candidates import compose


ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]
PLAN = json.loads((ROOT / "data/synthetic/fm_b4_discriminating_pulse_plan.json").read_text(encoding="utf-8"))
CATALOG = json.loads((ROOT / "data/synthetic/fm_a_structural_candidates.json").read_text(encoding="utf-8"))


class FmB4DiscriminatingAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.plan = copy.deepcopy(PLAN)
        self.composed = compose(self.plan, copy.deepcopy(CATALOG))
        self.audit = source_profile()

    def test_reports_feedback_capacity_delay_and_topology(self):
        cs1 = explain_structure(self.plan, self.composed, "urn:igc:candidate:CS-01", self.audit)
        cs2 = explain_structure(self.plan, self.composed, "urn:igc:candidate:CS-02", self.audit)
        self.assertEqual(cs1["stage_count"], 1)
        self.assertEqual(cs2["stage_count"], 2)
        self.assertEqual(len(cs1["internal_feedback"]), 1)
        self.assertEqual(len(cs2["internal_feedback"]), 2)
        self.assertEqual(cs1["internal_feedback"][0]["type"], "BALANCING")
        self.assertEqual(cs1["declared_capacity_units_per_hour_per_stage"], 2)
        self.assertEqual(cs1["serial_response_time_sum_hours"], 1)
        self.assertEqual(cs2["serial_response_time_sum_hours"], 2)
        self.assertFalse(cs2["cross_molecule_feedback"])
        self.assertTrue(cs2["cross_molecule_graph_is_acyclic"])

    def test_comparison_explains_structure_and_pulse_without_ranking(self):
        profiles = {
            "cs1": {"structural_hash": "s1", "stage_count": 1, "stock_count": 2,
                    "internal_feedback": [{}], "serial_response_time_sum_hours": 1,
                    "cross_molecule_feedback": False},
            "cs2": {"structural_hash": "s2", "stage_count": 2, "stock_count": 3,
                    "internal_feedback": [{}, {}], "serial_response_time_sum_hours": 2,
                    "cross_molecule_feedback": False},
        }
        traces = {
            "cs1": {"time_grid": [0, 2, 16], "delivery_series": [0, 2, 6],
                    "post_pulse_delivery_series": [2, 6], "post_pulse_times": [2, 16],
                    "final_delivery": 6, "delivery_at_pulse_end": 2, "recovery_delivery": 4},
            "cs2": {"time_grid": [0, 2, 16], "delivery_series": [0, 1, 5],
                    "post_pulse_delivery_series": [1, 5], "post_pulse_times": [2, 16],
                    "final_delivery": 5, "delivery_at_pulse_end": 1, "recovery_delivery": 4},
        }
        result = compare_candidates(traces, profiles, self.plan)
        self.assertEqual(result["status"], "DISCRIMINATING_UNDER_SCENARIO")
        self.assertEqual(result["pairwise_comparisons"][0]["structural_delta"]["stage_count"], [1, 2])
        self.assertIn("waiting stock", result["proposed_discriminating_perturbation"]["readouts"][1])
        self.assertFalse(result["ranking_performed"])
        self.assertFalse(result["proposed_discriminating_perturbation"]["optimized_or_empirically_validated"])
        self.assertEqual(result["proposed_discriminating_perturbation"]["amplitude_units_per_hour"], 3)
        self.assertEqual(result["proposed_discriminating_perturbation"]["duration_hours"], 2)

    def test_indistinguishable_pulse_preserves_both_structures(self):
        profiles = {name: {"structural_hash": name, "stage_count": count, "stock_count": count+1,
            "internal_feedback": [{}] * count, "serial_response_time_sum_hours": count,
            "cross_molecule_feedback": False} for name, count in (("a", 1), ("b", 2))}
        trace = {"time_grid": [0, 1], "delivery_series": [0, 3],
                 "post_pulse_delivery_series": [0, 3], "post_pulse_times": [0, 1],
                 "final_delivery": 3, "delivery_at_pulse_end": 0, "recovery_delivery": 3}
        result = compare_candidates({"a": trace, "b": copy.deepcopy(trace)}, profiles, self.plan)
        self.assertEqual(result["status"], "NON_DISCRIMINATING")
        self.assertFalse(result["ranking_performed"])


if __name__ == "__main__":
    unittest.main()
