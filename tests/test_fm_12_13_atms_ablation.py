from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.fm_12_13_atms_ablation import atms_labels, direct_filter, rule_closure, run


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/synthetic/fm_12_13_ablation_plan.json"
PLAN = json.loads(PLAN_PATH.read_text(encoding="utf-8"))


class Fm1213AtmsAblationTests(unittest.TestCase):
    def test_s0_simple_filter_and_atms_agree(self):
        s0 = PLAN["scenarios"][0]
        expected = s0["expected_labels"]
        self.assertEqual(direct_filter(s0), expected)
        self.assertEqual(atms_labels(s0), expected)
        self.assertEqual(rule_closure(s0), expected)

    def test_s1_nogood_removes_one_path_and_alternative_survives(self):
        s1 = PLAN["scenarios"][1]
        labels = atms_labels(s1)
        self.assertEqual(labels, s1["expected_labels"])
        self.assertEqual(labels["candidate-cs01"], [["evidence-b", "mechanism", "route-b"]])
        self.assertEqual(rule_closure(s1), labels)

    def test_llm_tasks_are_separate_from_method_and_report_no_model_evaluation(self):
        with tempfile.TemporaryDirectory() as directory:
            report = run(PLAN_PATH, Path(directory))
            self.assertEqual(report["overall_atms_value_added"], "NOT_DEMONSTRATED")
            self.assertTrue(all(item["atms_value_added"] == "NOT_DEMONSTRATED"
                                for item in report["scenarios"].values()))
            self.assertEqual(report["llm_interface"]["answer_quality"],
                             "NOT_EVALUATED_NO_MODEL_PROVIDER_CONFIGURED")
            self.assertTrue(report["llm_interface"]["context_packets_generated"])
            tasks = json.loads((Path(directory) / "llm-evaluation-tasks.json").read_text(encoding="utf-8"))
            self.assertEqual(len(tasks["tasks"]), 3)
            self.assertEqual(len(tasks["paired_contexts"]), 3)


if __name__ == "__main__":
    unittest.main()
