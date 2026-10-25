"""No provider calls, no scientific score: contract and isolation only."""
import unittest
from copy import deepcopy
from scripts.arena_v0_contract import (
    ArenaContractError, ARMS, INPUT_SCHEMA, SUBMISSION_SCHEMA,
    arm_view, assert_same_evidence, digest, validate_submission,
    feedback_to_own_arm, trace_event,
)

class ArenaV0ContractTests(unittest.TestCase):
    def setUp(self):
        self.source={"schema":INPUT_SCHEMA,"investigation_id":"INV-TEST", "round_id":"R0",
                     "question":"Which queue system explains cumulative deliveries?",
                     "source_snapshot_hash":"sha256:"+"3"*64,"iteration_limit":2,
                     "construction":{"source_id":"public-fixture","values":[0,1,2]},
                     "observability":{"delivered":"cumulative units"},
                     "resources":{"max_calls":1,"max_simulations":2}}
        self.views={a:arm_view(self.source,a) for a in ARMS}

    def submission(self,arm="D", iteration=0, parent=None):
        return {"schema":SUBMISSION_SCHEMA,"arm_id":arm,"round_id":"R0",
                "iteration":iteration,"parent_revision_id":parent,
                "native_artifact_sha256":"sha256:"+"a"*64,
                "method_version":"deterministic-v0" if arm=="D" else "other-native-v0",
                "hypothesis_ids":[f"{arm}-H1"],"status":"PROPOSED",
                "unknowns":[],"assumption_ids":["A1"],"evidence_refs":["public-fixture"],"notes":""}

    def test_arms_get_identical_primary_evidence_without_mutation(self):
        assert_same_evidence(list(self.views.values()))
        self.assertEqual(len({v["input_hash"] for v in self.views.values()}),1)
        self.views["D"]["input"]["construction"]["values"].append(99)
        self.assertEqual(self.views["B"]["input"]["construction"]["values"],[0,1,2])
        with self.assertRaises(ArenaContractError):
            assert_same_evidence(list(self.views.values()))

    def test_fourth_arm_is_staged_not_enabled(self):
        with self.assertRaisesRegex(ArenaContractError,"ARM_NOT_ACTIVE"):
            arm_view(self.source,"C")

    def test_reserved_data_must_not_enter_visible_packet(self):
        for key in ("gold","holdout","truth_structure","reserved_observations", "other_arm_result"):
            data=deepcopy(self.source)
            data["construction"][key]="sensitive"
            with self.subTest(key=key),self.assertRaises(ArenaContractError):
                arm_view(data,"D")

    def test_submission_is_method_native_not_auto_modelica_verified(self):
        item=self.submission()
        sha=validate_submission(self.views["D"],item)
        self.assertTrue(sha.startswith("sha256:"))
        item["status"]="EXECUTABLE"
        with self.assertRaisesRegex(ArenaContractError,"UNVERIFIED"):
            validate_submission(self.views["D"],item)

    def test_reject_cross_arm_or_future_peers_and_forged_results(self):
        bad=self.submission("B")
        with self.assertRaisesRegex(ArenaContractError,"CROSS_ARM"):
            validate_submission(self.views["D"],bad)
        bad=self.submission()
        bad["other_arm_submission"]={"B":"H2"}
        with self.assertRaises(ArenaContractError):
            validate_submission(self.views["D"],bad)

    def test_iteration_revision_links(self):
        with self.assertRaisesRegex(ArenaContractError,"BROKEN_REVISION"):
            validate_submission(self.views["D"],self.submission(iteration=1))
        self.assertTrue(validate_submission(self.views["D"],self.submission(iteration=1,parent="D-R0-H1")))
        with self.assertRaisesRegex(ArenaContractError,"ITERATION_OUT"):
            validate_submission(self.views["D"],self.submission(iteration=2,parent="D-R1"))

    def test_feedback_is_only_own_source_with_gate_and_hashes(self):
        sub=self.submission()
        sh=validate_submission(self.views["D"],sub)
        diags=[{"gate":"G2","status":"PARTIAL","details":"capacity saturation",
                "source_artifact_hash":"sha256:"+"9"*64}]
        feedback=feedback_to_own_arm(self.views["D"],sub,submission_hash=sh,technical_diagnostics=diags)
        self.assertEqual(feedback["arm_id"],"D")
        self.assertNotIn("other_arm_result",str(feedback))
        diags[0]["other_arm_result"]="B-model"
        with self.assertRaisesRegex(ArenaContractError,"INVALID_DIAGNOSTIC"):
            feedback_to_own_arm(self.views["D"],sub,submission_hash=sh,technical_diagnostics=diags)

    def test_event_envelope_has_immutable_hash_chain(self):
        first=trace_event(arm_id="D",round_id="R0",event_type="HYPOTHESIS_PROPOSED",
                          iteration=0,source_hash=self.views["D"]["input_hash"],
                          payload_hash=digest(self.submission()))
        second=trace_event(arm_id="D",round_id="R0",event_type="FEEDBACK_DELIVERED",
                           iteration=0,source_hash=first["source_hash"],
                           payload_hash=digest({"diagnostic":"G2"}),
                           previous_event_hash=first["event_hash"])
        self.assertEqual(second["previous_event_hash"],first["event_hash"])
        self.assertNotEqual(second["event_hash"],first["event_hash"])

if __name__=="__main__": unittest.main()
