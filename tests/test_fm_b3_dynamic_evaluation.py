from __future__ import annotations

import copy
import csv
import json
from pathlib import Path
import tempfile
import unittest

from scripts.compose_molecular_candidates import compose
from scripts.fm_b2_atms_candidate_reasoning import apply_supports
from scripts.fm_b3_dynamic_evaluation import (
    DynamicEvaluationError,
    assess_trace,
    evaluate_comparison,
    render_evaluation_modelica,
    render_openmodelica_script,
    validate_scenario,
)
from scripts.verify_fm_b2_atms_selection import verify_selection


ROOT = Path(__file__).resolve().parents[1]
PLAN = json.loads((ROOT / "data/synthetic/fm_b3_dynamic_plan.json").read_text(encoding="utf-8"))
CATALOG = json.loads((ROOT / "data/synthetic/fm_a_structural_candidates.json").read_text(encoding="utf-8"))
SUPPORTS = json.loads((ROOT / "data/synthetic/fm_b3_dynamic_supports.json").read_text(encoding="utf-8"))


class FmB3DynamicEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.plan = copy.deepcopy(PLAN)
        self.composed = compose(copy.deepcopy(self.plan), copy.deepcopy(CATALOG))
        self.selection = apply_supports(self.composed, copy.deepcopy(SUPPORTS))
        self.composition_report = {"plan_id": self.plan["id"]}

    def test_atms_retains_two_structures_and_rejects_third(self):
        verify_selection(self.composed, SUPPORTS, self.selection)
        validate_scenario(self.plan, self.composition_report, self.composed, self.selection)
        self.assertEqual([item["candidate_id"] for item in self.selection["selected"]], [
            "urn:igc:candidate:CS-01", "urn:igc:candidate:CS-02"
        ])
        self.assertEqual([item["candidate_id"] for item in self.selection["rejected"]], [
            "urn:igc:candidate:CS-03"
        ])

    def test_openmodelica_runs_all_and_only_admissible_candidates(self):
        modelica = render_evaluation_modelica(self.plan, self.composed, self.selection)
        mos = render_openmodelica_script(self.plan, self.composed, self.selection)
        self.assertIn("queueBalanceError_stage1", modelica)
        self.assertIn("systemBalanceError = acceptedTotal - systemInventory", modelica)
        self.assertIn("simulate(B3MolecularDynamics.Evaluate_CS_01,", mos)
        self.assertIn("simulate(B3MolecularDynamics.Evaluate_CS_02,", mos)
        self.assertNotIn("simulate(B3MolecularDynamics.Evaluate_CS_03,", mos)

    def _trace(self, path: Path, corrupt: str | None = None):
        fields = ["time", "delivered", "acceptedTotal", "systemInventory", "systemBalanceError",
                  "terminalBalanceError", "terminalArrivals", "waiting_stage0", "cumulativeArrivals_stage0",
                  "cumulativeCompletions_stage0", "queueBalanceError_stage0"]
        rows = []
        for time, delivered, accepted, waiting in ((0, 0, 0, 0), (5, 10, 15, 5), (10, 20, 30, 10)):
            row = {
                "time": time,
                "delivered": delivered,
                "acceptedTotal": accepted,
                "systemInventory": delivered + waiting,
                "systemBalanceError": 0,
                "terminalBalanceError": 0,
                "terminalArrivals": delivered,
                "waiting_stage0": waiting,
                "cumulativeArrivals_stage0": accepted,
                "cumulativeCompletions_stage0": delivered,
                "queueBalanceError_stage0": 0,
            }
            if corrupt == "accepted_total" and time == 10:
                row["acceptedTotal"] = accepted + 0.1
            if corrupt == "queue_input" and time == 10:
                row["cumulativeArrivals_stage0"] = accepted + 0.1
            if corrupt == "negative_stock" and time == 5:
                row["waiting_stage0"] = -1
            rows.append(row)
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        return assess_trace(path, ["stage0"], 0, 10, 1)

    def test_accepts_coherent_stock_flow_trajectory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            metrics = self._trace(Path(temp_dir) / "trace.csv")
        self.assertEqual(metrics["final_delivered"], 20)
        self.assertEqual(metrics["final_system_inventory"], 30)
        self.assertEqual(metrics["max_abs_independent_global_balance_error"], 0)

    def test_rejects_conservation_error_and_negative_stock(self):
        for corruption, expected in (("accepted_total", "independently reconstructed global stock-flow conservation"),
                                     ("queue_input", "independently reconstructed queue stock-flow balance"),
                                     ("negative_stock", "negative queue stock")):
            with self.subTest(corruption=corruption), tempfile.TemporaryDirectory() as temp_dir:
                with self.assertRaisesRegex(DynamicEvaluationError, expected):
                    self._trace(Path(temp_dir) / "trace.csv", corruption)

    def test_accepts_repeated_event_timestamps_but_rejects_time_reversal(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "trace.csv"
            fields = ["time", "delivered", "acceptedTotal", "systemInventory", "systemBalanceError",
                      "terminalBalanceError", "terminalArrivals", "waiting_stage0", "cumulativeArrivals_stage0",
                      "cumulativeCompletions_stage0", "queueBalanceError_stage0"]
            rows = [
                {"time": 0, "delivered": 0, "acceptedTotal": 0, "systemInventory": 0,
                 "systemBalanceError": 0, "terminalBalanceError": 0, "terminalArrivals": 0,
                 "waiting_stage0": 0, "cumulativeArrivals_stage0": 0, "cumulativeCompletions_stage0": 0,
                 "queueBalanceError_stage0": 0},
                {"time": 0, "delivered": 0, "acceptedTotal": 0, "systemInventory": 0,
                 "systemBalanceError": 0, "terminalBalanceError": 0, "terminalArrivals": 0,
                 "waiting_stage0": 0, "cumulativeArrivals_stage0": 0, "cumulativeCompletions_stage0": 0,
                 "queueBalanceError_stage0": 0},
                {"time": 10, "delivered": 20, "acceptedTotal": 30, "systemInventory": 30,
                 "systemBalanceError": 0, "terminalBalanceError": 0, "terminalArrivals": 20,
                 "waiting_stage0": 10, "cumulativeArrivals_stage0": 30, "cumulativeCompletions_stage0": 20,
                 "queueBalanceError_stage0": 0},
            ]
            with path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            metrics = assess_trace(path, ["stage0"], 0, 10, 1)
            self.assertEqual(metrics["samples"], 3)
            self.assertEqual(metrics["repeated_timestamp_count"], 1)
            self.assertEqual(metrics["repeated_timestamp_events"][0]["time"], 0)
            rows[1]["time"] = -1
            with path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaisesRegex(DynamicEvaluationError, "time cannot move backwards"):
                assess_trace(path, ["stage0"], 0, 10, 1)

    def test_event_samples_may_extend_csv_but_cannot_replace_planned_grid(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "event-trace.csv"
            fields = ["time", "delivered", "acceptedTotal", "systemInventory", "systemBalanceError",
                      "terminalBalanceError", "terminalArrivals", "waiting_stage0", "cumulativeArrivals_stage0",
                      "cumulativeCompletions_stage0", "queueBalanceError_stage0"]
            rows = []
            for time, delivered, accepted, waiting in ((0, 0, 0, 0), (2.5, 5, 7.5, 2.5),
                                                       (5, 10, 15, 5), (10, 20, 30, 10)):
                rows.append({"time": time, "delivered": delivered, "acceptedTotal": accepted,
                    "systemInventory": delivered + waiting, "systemBalanceError": 0,
                    "terminalBalanceError": 0, "terminalArrivals": delivered,
                    "waiting_stage0": waiting, "cumulativeArrivals_stage0": accepted,
                    "cumulativeCompletions_stage0": delivered, "queueBalanceError_stage0": 0})
            with path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            metrics = assess_trace(path, ["stage0"], 0, 10, 1, allow_extra_event_samples=True)
            self.assertEqual(metrics["samples"], 4)
            with self.assertRaisesRegex(DynamicEvaluationError, "expected exactly 3 samples"):
                assess_trace(path, ["stage0"], 0, 10, 1)
            rows[2].update({"time": 7.5, "delivered": 15, "acceptedTotal": 22.5,
                            "systemInventory": 22.5, "terminalArrivals": 15,
                            "waiting_stage0": 7.5, "cumulativeArrivals_stage0": 22.5,
                            "cumulativeCompletions_stage0": 15})
            with path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaisesRegex(DynamicEvaluationError, "planned time grid"):
                assess_trace(path, ["stage0"], 0, 10, 2, allow_extra_event_samples=True)

    def test_comparison_requires_distinct_dynamic_behavior(self):
        common = {"times": [0, 1], "delivered_series": [0, 2]}
        result = evaluate_comparison({"a": common, "b": {"times": [0, 1], "delivered_series": [0, 3]}},
                                     {"a": "hash-a", "b": "hash-b"})
        self.assertFalse(result["ranking_performed"])
        self.assertEqual(result["status"], "DISCRIMINATING_UNDER_SCENARIO")
        self.assertEqual(result["pairwise_comparisons"][0]["max_abs_delivered_difference"], 1)
        equivalent = evaluate_comparison({"a": common, "b": copy.deepcopy(common)},
                                         {"a": "hash-a", "b": "hash-b"})
        self.assertEqual(equivalent["status"], "NON_DISCRIMINATING")
        self.assertEqual(equivalent["pairwise_comparisons"][0]["dynamic_relation"], "NON_DISCRIMINATING")
        self.assertIsNotNone(equivalent["pairwise_comparisons"][0]["next_step"])


if __name__ == "__main__":
    unittest.main()
