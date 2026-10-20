import json
import unittest
from pathlib import Path

from scripts.f3_candidate_selection import CandidateSelectionError, select_candidates


ROOT = Path(__file__).resolve().parents[1]


class F3CandidateSelectionTests(unittest.TestCase):
    def setUp(self):
        self.base = json.loads(
            (ROOT / "data/synthetic/system_model_candidate.json").read_text(encoding="utf-8")
        )
        self.proposal_set = json.loads(
            (ROOT / "data/synthetic/f3_candidate_proposals.json").read_text(encoding="utf-8")
        )

    def test_nogood_changes_candidate_that_reaches_handoff(self):
        result = select_candidates(
            self.base, self.proposal_set["proposals"],
            self.proposal_set["assumptions"], self.proposal_set["nogoods"],
        )
        self.assertEqual(
            [item["candidate"]["candidate_id"] for item in result["selected"]],
            ["candidate-promotion-orders-001"],
        )
        self.assertEqual(result["rejected"][0]["candidate_id"], "candidate-baseline-orders-001")
        selected = result["selected"][0]["candidate"]
        arrival = next(item for item in selected["assumptions"]
                       if item["id"] == "assumption-arrival-rate-001")
        self.assertEqual(arrival["value"], 4)
        self.assertEqual(selected["atms_selection"]["minimal_supporting_environments"],
                         [["mechanism-promotion", "rate-promotion"]])
        self.assertFalse(result["production_engine_selected"])

    def test_compatible_candidates_coexist_without_nogood(self):
        result = select_candidates(
            self.base, self.proposal_set["proposals"], self.proposal_set["assumptions"], [],
        )
        self.assertEqual(len(result["selected"]), 2)
        self.assertEqual(
            [item["candidate"]["candidate_id"] for item in result["selected"]],
            ["candidate-baseline-orders-001", "candidate-promotion-orders-001"],
        )

    def test_unknown_assumption_reference_fails_closed(self):
        proposals = [dict(self.proposal_set["proposals"][0], assumption_ids=["unregistered"])]
        with self.assertRaises(CandidateSelectionError):
            select_candidates(self.base, proposals, self.proposal_set["assumptions"], [])

    def test_invalid_parameter_override_fails_closed(self):
        proposals = [dict(self.proposal_set["proposals"][0],
                          parameter_values={"assumption-arrival-rate-001": -1})]
        with self.assertRaises(CandidateSelectionError):
            select_candidates(self.base, proposals, self.proposal_set["assumptions"], [])


if __name__ == "__main__":
    unittest.main()
