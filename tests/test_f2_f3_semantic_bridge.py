import json
import unittest
from pathlib import Path

from scripts.f0_spike import source_and_annotation
from scripts.f2_f3_semantic_bridge import SemanticBridgeError, derive_candidate_proposals


ROOT = Path(__file__).resolve().parents[1]


class F2F3SemanticBridgeTests(unittest.TestCase):
    def setUp(self):
        _, self.annotation = source_and_annotation()
        self.claim = json.loads(
            (ROOT / "data/synthetic/claim.json").read_text(encoding="utf-8")
        )
        self.source = (ROOT / "data/synthetic/source.txt").read_bytes()
        self.proposal_set = json.loads(
            (ROOT / "data/synthetic/f3_candidate_proposals.json").read_text(encoding="utf-8")
        )

    def test_sparql_derives_only_candidates_linked_to_claim_and_crminf_provenance(self):
        result, turtle = derive_candidate_proposals(
            self.annotation, self.claim, self.source, self.proposal_set,
        )
        self.assertEqual(
            [item["candidate_id"] for item in result["proposals"]],
            ["candidate-baseline-orders-001", "candidate-promotion-orders-001"],
        )
        self.assertEqual(result["semantic_evidence"]["query_name"],
                         "claim-to-candidate-support/0.1")
        self.assertFalse(result["semantic_evidence"]["empirical_inference_asserted"])
        self.assertIn("I1_Argumentation", turtle)
        self.assertIn("wasGeneratedBy", turtle)

    def test_mismatched_claim_reference_does_not_reach_sparql_selection(self):
        proposal_set = dict(self.proposal_set, claim_id="different-claim")
        with self.assertRaises(SemanticBridgeError):
            derive_candidate_proposals(
                self.annotation, self.claim, self.source, proposal_set,
            )

    def test_candidate_without_matching_claim_never_enters_atms_proposals(self):
        proposal_set = dict(self.proposal_set)
        proposal_set["proposals"] = [
            dict(self.proposal_set["proposals"][0], claim_id="unrelated-claim")
        ]
        with self.assertRaises(SemanticBridgeError):
            derive_candidate_proposals(
                self.annotation, self.claim, self.source, proposal_set,
            )

    def test_claim_quote_must_resolve_to_source_annotation(self):
        annotation = json.loads(json.dumps(self.annotation))
        annotation["body"]["value"] = "A different claim"
        with self.assertRaises(SemanticBridgeError):
            derive_candidate_proposals(
                annotation, self.claim, self.source, self.proposal_set,
            )


if __name__ == "__main__":
    unittest.main()
