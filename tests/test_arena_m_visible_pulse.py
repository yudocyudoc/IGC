"""Arena M visible-pulse gates; no provider, no gold, no B/D model."""
import unittest
from copy import deepcopy
import json
from scripts.arena_m_visible_pulse import build, choose_one, stimulus_only_replace, ROOT
from scripts.arena_v0_contract import digest, arm_view, validate_submission, ArenaContractError

VISIBLE=json.loads((ROOT/"data/synthetic/arena_m_v0_visible.json").read_text())

class MolecularCommonPulseTests(unittest.TestCase):
    def test_one_molecular_candidate_selected_with_no_observational_ranking(self):
        name,modelica,native,submission,event,receipt=build(VISIBLE)
        self.assertEqual(native["candidate_universe_count"],6)
        self.assertEqual(len(submission["hypothesis_ids"]),1)
        self.assertEqual(submission["status"],"PROPOSED")
        self.assertFalse(native["selection_used_construction_observations"])
        self.assertEqual(event["event_type"],"HYPOTHESIS_PROPOSED")
        self.assertIn("MolecularArena_",name)
        self.assertEqual(submission["native_artifact_sha256"],digest(native))
        validate_submission(arm_view(VISIBLE,"M"),submission)
        self.assertIn("if time < 2 then 1.7 else 0",modelica)
        self.assertIn("IGCMolecules.BoundedQueue",modelica)
        self.assertNotIn("der(",modelica)
        self.assertFalse(receipt["wrapper_source_edited"])
        self.assertEqual(receipt["number_models_proposed"],1)
        self.assertEqual(receipt["number_simulations_planned"],1)
        self.assertEqual(receipt["g2_status"],"NOT_RUN_BY_GENERATOR")

    def test_cannot_choose_graph_using_observations(self):
        changed=deepcopy(VISIBLE)
        changed["construction"]["observations"][1]["delivered"]=99999
        one=build(VISIBLE)[2]["canonical_graph_sha256"]
        two=build(changed)[2]["canonical_graph_sha256"]
        self.assertEqual(one,two)

    def test_fails_on_secret_or_crossarm_references(self):
        for forbidden in ("gold","holdout","other_arm_result"):
            changed=deepcopy(VISIBLE)
            changed["construction"][forbidden]="secret"
            with self.assertRaises(ArenaContractError):build(changed)

    def test_no_arbitrary_unit_conversion_or_unsupported_stimulus(self):
        changed=deepcopy(VISIBLE)
        changed["observability"]["time_unit"]="days"
        with self.assertRaisesRegex(ValueError,"SEMANTIC_OBSERVABLE_MAPPING_NOT_ESTABLISHED"):
            build(changed)
        changed=deepcopy(VISIBLE)
        changed["construction"]["input_profile"]["kind"]="sinusoid"
        with self.assertRaisesRegex(ValueError,"UNSUPPORTED_PUBLIC_INPUT_PROFILE"):
            build(changed)

    def test_upstream_stimulus_drift_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"UPSTREAM_E1_STIMULUS_INTERFACE_CHANGED"):
            stimulus_only_replace("something else",1.7,2)

    def test_budget_enforced(self):
        changed=deepcopy(VISIBLE)
        changed["resources"]["max_model_proposals"]=0
        with self.assertRaisesRegex(ValueError,"NO_M_ARM_RESOURCE_BUDGET"):
            build(changed)

if __name__=="__main__":
    unittest.main()
