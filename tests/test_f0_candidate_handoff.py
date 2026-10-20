from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from scripts.f0_candidate_handoff import HandoffError, render_model, validate_candidate


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = json.loads((ROOT / "data/synthetic/system_model_candidate.json").read_text(encoding="utf-8"))
CLAIM = json.loads((ROOT / "data/synthetic/claim.json").read_text(encoding="utf-8"))
SOURCE = (ROOT / "data/synthetic/source.txt").read_text(encoding="utf-8")


class CandidateHandoffTests(unittest.TestCase):
    def test_candidate_resolves_source_claim_mechanism_and_assumptions(self):
        evidence = validate_candidate(CANDIDATE, CLAIM, SOURCE)
        self.assertEqual(evidence["source_claim_id"], CLAIM["claim_id"])
        self.assertEqual(evidence["quote"], CLAIM["quote"])
        self.assertEqual(evidence["quote_end"] - evidence["quote_start"], len(CLAIM["quote"]))

    def test_candidate_with_missing_flow_unit_is_rejected(self):
        candidate = copy.deepcopy(CANDIDATE)
        candidate["structure"]["inflow"].pop("unit")
        with self.assertRaisesRegex(HandoffError, "unit"):
            validate_candidate(candidate, CLAIM, SOURCE)

    def test_candidate_with_broken_assumption_reference_is_rejected(self):
        candidate = copy.deepcopy(CANDIDATE)
        candidate["structure"]["outflow"]["assumption_id"] = "assumption-missing"
        with self.assertRaisesRegex(HandoffError, "undeclared assumption"):
            validate_candidate(candidate, CLAIM, SOURCE)

    def test_mechanism_with_broken_claim_reference_is_rejected(self):
        candidate = copy.deepcopy(CANDIDATE)
        candidate["mechanism_hypothesis"]["claim_id"] = "claim-missing"
        with self.assertRaisesRegex(HandoffError, "reference"):
            validate_candidate(candidate, CLAIM, SOURCE)

    def test_flow_with_mismatched_parameter_name_is_rejected(self):
        candidate = copy.deepcopy(CANDIDATE)
        candidate["assumptions"][0]["parameter"] = "completionRate"
        with self.assertRaisesRegex(HandoffError, "parameter/unit"):
            validate_candidate(candidate, CLAIM, SOURCE)

    def test_parameter_change_changes_generated_model(self):
        candidate = copy.deepcopy(CANDIDATE)
        base = render_model(candidate, "CandidateBase")
        candidate["assumptions"][0]["value"] += 1
        changed = render_model(candidate, "CandidatePerturbed")
        self.assertNotEqual(base, changed)
        self.assertIn("arrivalRate = 3", base)
        self.assertIn("arrivalRate = 4", changed)


if __name__ == "__main__":
    unittest.main()
