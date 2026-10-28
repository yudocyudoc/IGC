#!/usr/bin/env python3
import copy
import json
import unittest
from pathlib import Path
from caf01_m_equivalence import certificate, CONTRACT


class TestMCapacityCertificate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(Path(CONTRACT).read_text(encoding="utf-8"))

    def test_real_grid(self):
        result = certificate(self.contract)
        self.assertEqual(result["inactive_capacities"], [72, 100])
        self.assertEqual(result["max_proportional_release_items_per_hour"], 60)
        self.assertEqual(result["nominal_configurations"], 9)
        self.assertEqual(result["within_structure_upper_bound_classes"], 6)
        self.assertEqual(len([x for x in result["classes"] if x["kind"] == "proven_inactive_capacity"]), 3)

    def test_no_cross_structure_merge(self):
        result = certificate(self.contract)
        self.assertEqual({x["structure"] for x in result["classes"]}, {"C00", "C01", "C02"})
        self.assertTrue(all(len(x["capacidades"]) <= 2 for x in result["classes"]))

    def test_nonempty_initial_is_not_certifiable(self):
        c = copy.deepcopy(self.contract)
        c["boundary"]["initial_pending"] = 100
        with self.assertRaisesRegex(ValueError, "NO_CERTIFICATE"):
            certificate(c)

    def test_losses_are_not_certifiable(self):
        c = copy.deepcopy(self.contract)
        c["boundary"]["losses_allowed"] = True
        with self.assertRaisesRegex(ValueError, "NO_CERTIFICATE"):
            certificate(c)

    def test_pulse_change_fails_closed(self):
        c = copy.deepcopy(self.contract)
        c["worlds"][1]["arrival"]["rate"] = 2
        with self.assertRaisesRegex(ValueError, "NO_CERTIFICATE"):
            certificate(c)

    def test_response_time_change_fails_closed(self):
        c = copy.deepcopy(self.contract)
        c["methods"]["M"]["frozen_response_time_hours"]["dispatch"] = 0.25
        with self.assertRaisesRegex(ValueError, "NO_CERTIFICATE"):
            certificate(c)

    def test_grid_changed_recomputes_when_shape_preserved(self):
        c = copy.deepcopy(self.contract)
        c["methods"]["M"]["proposed_bounded_capacity_grid_items_per_hour"] = [20, 40, 100]
        result = certificate(c)
        self.assertEqual(result["inactive_capacities"], [100])
        self.assertEqual(result["within_structure_upper_bound_classes"], 9)


if __name__ == "__main__":
    unittest.main()
