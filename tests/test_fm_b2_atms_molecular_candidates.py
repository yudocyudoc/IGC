from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from scripts.compose_molecular_candidates import compose
from scripts.fm_b2_atms_candidate_reasoning import MolecularAtmsError, apply_supports
from scripts.verify_fm_b2_atms_selection import verify_selection


ROOT = Path(__file__).resolve().parents[1]
PLAN = json.loads((ROOT / "data/synthetic/fm_b_serial_chain_plan.json").read_text(encoding="utf-8"))
CATALOG = json.loads((ROOT / "data/synthetic/fm_a_structural_candidates.json").read_text(encoding="utf-8"))
SUPPORTS = json.loads((ROOT / "data/synthetic/fm_b2_candidate_supports.json").read_text(encoding="utf-8"))


class FmB2AtmsMolecularCandidateTests(unittest.TestCase):
    def setUp(self):
        self.composed = compose(copy.deepcopy(PLAN), copy.deepcopy(CATALOG))

    def test_alternatives_coexist_and_one_justification_can_be_pruned(self):
        result = apply_supports(self.composed, SUPPORTS)
        self.assertEqual([item["candidate_id"] for item in result["selected"]],
                         ["urn:igc:candidate:CS-01", "urn:igc:candidate:CS-02"])
        cs01 = result["selected"][0]
        self.assertEqual(cs01["minimal_supporting_environments"], [[
            "urn:igc:assumption:CS-01-mechanism", "urn:igc:assumption:CS-01-route-b"
        ]])
        self.assertEqual(len(result["selected"][1]["minimal_supporting_environments"]), 2)
        self.assertEqual(result["rejected"], [])

    def test_candidate_with_all_support_environments_in_nogoods_is_rejected(self):
        support_plan = copy.deepcopy(SUPPORTS)
        support_plan["nogoods"].extend([
            ["urn:igc:assumption:CS-01-mechanism", "urn:igc:assumption:CS-01-route-b"],
            ["urn:igc:assumption:CS-02-mechanism", "urn:igc:assumption:CS-02-route-a"],
            ["urn:igc:assumption:CS-02-mechanism", "urn:igc:assumption:CS-02-route-b"],
        ])
        result = apply_supports(self.composed, support_plan)
        self.assertEqual([item["candidate_id"] for item in result["selected"]], [])
        self.assertEqual([item["candidate_id"] for item in result["rejected"]],
                         ["urn:igc:candidate:CS-01", "urn:igc:candidate:CS-02"])

    def test_unknown_assumption_reference_fails_closed(self):
        support_plan = copy.deepcopy(SUPPORTS)
        support_plan["justifications"][0]["antecedent_ids"][0] = "urn:igc:assumption:missing"
        with self.assertRaisesRegex(MolecularAtmsError, "invalid antecedents"):
            apply_supports(self.composed, support_plan)

    def test_support_plan_must_cover_exactly_the_composed_candidates(self):
        support_plan = copy.deepcopy(SUPPORTS)
        support_plan["justifications"] = [item for item in support_plan["justifications"]
                                           if item["candidate_id"] != "urn:igc:candidate:CS-02"]
        with self.assertRaisesRegex(MolecularAtmsError, "coverage mismatch"):
            apply_supports(self.composed, support_plan)

    def test_independent_verifier_reconstructs_labels_and_structure_links(self):
        result = apply_supports(self.composed, SUPPORTS)
        verify_selection(self.composed, SUPPORTS, result)
        self.assertEqual([item["structural_hash"] for item in result["selected"]],
                         [item["structural_hash"] for item in self.composed["structures"]])
        changed = copy.deepcopy(result)
        changed["selected"][0]["minimal_supporting_environments"] = []
        with self.assertRaisesRegex(ValueError, "label reconstruction mismatch"):
            verify_selection(self.composed, SUPPORTS, changed)

    def test_independent_verifier_rejects_collapsed_topologies(self):
        composed = copy.deepcopy(self.composed)
        composed["structures"][1]["structural_hash"] = composed["structures"][0]["structural_hash"]
        result = apply_supports(composed, SUPPORTS)
        with self.assertRaisesRegex(ValueError, "structurally distinct"):
            verify_selection(composed, SUPPORTS, result)


if __name__ == "__main__":
    unittest.main()
