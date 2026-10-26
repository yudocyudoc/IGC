"""M2 negatives and parent replay. All data used belong to the original M1 run."""
from __future__ import annotations
import copy
import json
import unittest
from pathlib import Path

from scripts.arena_m2_feedback import (
    ROOT, read_parent, revise, own_policy, preflight_parent, PARENT_SOURCE_SHA
)
from scripts.arena_v0_contract import digest, validate_submission, arm_view

VISIBLE=json.loads((ROOT/"data/synthetic/arena_m_v0_visible.json").read_text())
CATALOG=json.loads((ROOT/"experiments/e0/catalog.json").read_text())
PARENT_DIR=ROOT/"artifacts"/"m1-parent"


class TestM2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (PARENT_DIR/"m-visible_res.csv").exists():
            raise RuntimeError("M2_TEST_REQUIRES_AUTHENTIC_M1_ARTIFACT_REPLAY")
        cls.parent=read_parent(PARENT_DIR)

    def test_exact_parent_and_single_revision(self):
        result,abstained=revise(VISIBLE,*self.parent,CATALOG)
        self.assertIsNone(abstained)
        self.assertEqual(result["status"],"PROPOSED")
        native=result["native"];sub=result["submission"]
        self.assertEqual(native["arm_id"],"M")
        self.assertEqual(native["canonical_graph_sha256"],self.parent[0]["canonical_graph_sha256"])
        self.assertEqual(native["parent_native_hash"],digest(self.parent[0]))
        self.assertEqual(native["candidate_universe_count"],1)
        self.assertEqual(sub["iteration"],1)
        self.assertEqual(sub["parent_revision_id"],self.parent[1]["hypothesis_ids"][0]+":r0")
        self.assertEqual(len(sub["hypothesis_ids"]),1)
        self.assertEqual(len(native["parameter_edits"]),2)
        self.assertEqual({x["before"] for x in native["parameter_edits"]},{0.5})
        self.assertEqual({x["after"] for x in native["parameter_edits"]},{1.0})
        self.assertEqual({x["parameter"] for x in native["parameter_edits"]},{"responseTime"})
        self.assertIn("responseTime=1.0",result["modelica"])
        self.assertIn("maxThroughput=20",result["modelica"])
        self.assertNotIn("der(",result["modelica"])
        self.assertEqual(result["feedback"]["arm_id"],"M")
        self.assertEqual(result["events"][0]["event_type"],"FEEDBACK_DELIVERED")
        self.assertEqual(result["events"][1]["event_type"],"HYPOTHESIS_REVISED")
        self.assertEqual(result["events"][0]["previous_event_hash"],self.parent[2]["event_hash"])
        self.assertEqual(result["events"][1]["previous_event_hash"],result["events"][0]["event_hash"])
        validate_submission(arm_view(VISIBLE,"M"),sub)

    def test_m1_parent_report_tampering_fails(self):
        copyreport=copy.deepcopy(self.parent[3])
        copyreport["observations"][2]["simulated"]=-1.0
        with self.assertRaisesRegex(ValueError,"M1_REPORT_TAMPERED"):
            preflight_parent(VISIBLE,*self.parent[:3],copyreport,self.parent[4],CATALOG)

    def test_parent_graph_replaced_with_other_arm_is_blocked(self):
        fake=copy.deepcopy(self.parent[0])
        fake["arm_id"]="B"
        with self.assertRaisesRegex(ValueError,"M1_PARENT_NOT_IDENTICAL"):
            revise(VISIBLE,fake,*self.parent[1:],CATALOG)

    def test_invalid_iteration_budget_is_blocked(self):
        fake=copy.deepcopy(VISIBLE)
        fake["resources"]["max_simulations"]=1
        with self.assertRaisesRegex(ValueError,"M2_REQUIRES_EXACT"):
            revise(fake,*self.parent,CATALOG)

    def test_no_new_model_when_residual_signs_conflict(self):
        from scripts.arena_m_visible_pulse import composer,REGISTRY
        _,classes,_=composer.load_registry(REGISTRY)
        modified=copy.deepcopy(self.parent[3])
        modified["observations"][2]["residual"]=-0.2
        result,reason=own_policy(modified,self.parent[0]["graph"],classes)
        self.assertIsNone(result)
        self.assertEqual(reason,"NO_CONSISTENT_LATE_OVERSHOOT_OVER_THRESHOLD")

    def test_source_artifact_hash_gate_detects_bytes_not_json_only(self):
        import tempfile
        from shutil import copyfile
        with tempfile.TemporaryDirectory() as root:
            for fname in PARENT_SOURCE_SHA:
                copyfile(PARENT_DIR/fname,Path(root)/fname)
            with (Path(root)/"native-graph.json").open("ab") as f:
                f.write(b" ")
            with self.assertRaisesRegex(ValueError,"PARENT_M1_ARTIFACT_BYTES_CHANGED"):
                read_parent(Path(root))


if __name__=="__main__":
    unittest.main()
