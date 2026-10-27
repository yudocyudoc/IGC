import json
import unittest
from copy import deepcopy
from pathlib import Path
from scripts.arena_m_short_e1 import prepare, E1, ROOT
from scripts.arena_v0_contract import arm_view, validate_submission, digest, ArenaContractError

VISIBLE=json.loads((ROOT/"data/synthetic/arena_m_v0_visible.json").read_text())

class TestMShortE1(unittest.TestCase):
    def test_base_is_original_six_engineering_candidates_no_selected_hypothesis(self):
        native, submission, event=prepare(VISIBLE,E1/"registry.base.json")
        self.assertEqual(native["candidate_count"],6)
        self.assertEqual(len({x["canonical_sha256"] for x in native["candidate_graphs"]}),6)
        self.assertEqual(submission["status"],"PARTIAL")
        self.assertEqual(submission["hypothesis_ids"],[])
        self.assertEqual(native["candidate_selection"],"UNRESOLVED")
        self.assertEqual(native["common_stimulus_translation"],"NOT_IMPLEMENTED")
        self.assertEqual(submission["native_artifact_sha256"],digest(native))
        validate_submission(arm_view(VISIBLE,"M"),submission)
        self.assertEqual(event["event_type"],"ABSTENTION_RECORDED")

    def test_extended_is_original_fifteen_not_new_causal_worlds(self):
        base,_,_=prepare(VISIBLE,E1/"registry.base.json")
        ext, sub,_=prepare(VISIBLE,E1/"registry.extended.json")
        self.assertEqual(ext["candidate_count"],15)
        self.assertEqual(len({x["canonical_sha256"] for x in ext["candidate_graphs"]}),15)
        a={x["canonical_sha256"] for x in base["candidate_graphs"]}
        b={x["canonical_sha256"] for x in ext["candidate_graphs"]}
        self.assertTrue(a.issubset(b))
        self.assertEqual(len(b-a),9)
        self.assertEqual(sub["hypothesis_ids"],[])

    def test_no_other_arm_or_holdout_content_can_enter(self):
        for forbidden in ("holdout","other_arm_result","gold","truth_structure"):
            changed=deepcopy(VISIBLE)
            changed["construction"][forbidden]={"mechanism":"not allowed"}
            with self.assertRaises(ArenaContractError):
                prepare(changed,E1/"registry.base.json")

    def test_external_registry_may_not_be_injected(self):
        with self.assertRaisesRegex(ValueError,"UNVERIFIED_M_REGISTRY"):
            prepare(VISIBLE,ROOT/"data/synthetic/arena_m_v0_visible.json")

    def test_visible_input_exactly_matches_first_buffalo_public_snapshot(self):
        # Git blob hash of the same visible file used by independent Buffalo B.
        import hashlib
        blob=(ROOT/"data/synthetic/arena_m_v0_visible.json").read_bytes()
        sha=hashlib.sha1(b"blob "+str(len(blob)).encode()+b"\0"+blob).hexdigest()
        self.assertEqual(sha,"94fb9e853d1fd0f5623d759fb7b8408756eacf0c")

if __name__=="__main__":
    unittest.main()
