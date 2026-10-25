"""No network. Contract tests for the one-call GitHub diagnostic adapter."""
import json
import unittest
from pathlib import Path

from scripts.arena_glm53_github_probe import parse_selection, validate_request

ROOT = Path(__file__).resolve().parents[1]


class Glm53GithubProbeTests(unittest.TestCase):
    def setUp(self):
        self.good = {
            "selected_candidate_ids": ["urn:igc:candidate:CS-01"],
            "rationale": "Construction does not identify the number of stages.",
            "falsifier": "Dense observations after an independent reset.",
            "unknowns": ["Instrument noise"],
            "next_test": "Collect the early-time transient."
        }

    def test_exact_precommitted_prompt(self):
        pkg = json.loads((ROOT/"data/diagnostics/glm53_nw2_config_probe_request.json").read_text())
        body = validate_request(pkg)
        self.assertEqual([x["role"] for x in body["messages"]], ["system", "user"])
        self.assertEqual(body["temperature"], 0)
        self.assertEqual(body["reasoning_effort"], "low")
        self.assertEqual(body["max_completion_tokens"], 4096)

    def test_valid_selection_and_fence(self):
        self.assertEqual(parse_selection(json.dumps(self.good)), self.good)
        self.assertEqual(parse_selection("```json\n" + json.dumps(self.good) + "\n```"), self.good)

    def test_empty_invalid_duplicate_unknown(self):
        for value in ("", " ", "```json invalid```", "{"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_selection(value)
        for invalid in (["urn:igc:candidate:CS-03"], ["urn:igc:candidate:CS-01"]*2):
            bad = dict(self.good, selected_candidate_ids=invalid)
            with self.subTest(selected=invalid), self.assertRaises(ValueError):
                parse_selection(json.dumps(bad))

    def test_valid_abstention(self):
        self.assertEqual(parse_selection(json.dumps(dict(self.good, selected_candidate_ids=[])))
                         ["selected_candidate_ids"], [])

    def test_unexplained_abstention_rejected(self):
        bad = dict(self.good, selected_candidate_ids=[], rationale="")
        with self.assertRaises(ValueError):
            parse_selection(json.dumps(bad))


if __name__ == "__main__":
    unittest.main()
