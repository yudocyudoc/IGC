"""D2 revised Modelica regression tests against authentic archived D-only results."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.arena_d2_revised_g2 import ROOT, read_parent, build, verify_lineage, assess_real_csv

DATA=json.loads((ROOT/"data/synthetic/arena_d_v01_visible.json").read_text())
PROTOCOL=json.loads((ROOT/"data/synthetic/arena_d_v1_screen_protocol.json").read_text())
PARENT=ROOT/"artifacts/d2-parent"


class RevisedD2ModelicaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (PARENT/"d2-revision.json").exists():
            raise RuntimeError("D2_TEST_REQUIRES_VERIFIED_ORIGINAL_D_ONLY_ARCHIVE")
        cls.original=read_parent(PARENT)

    def test_emits_six_real_revisions_and_preserves_own_support(self):
        manifest,sources,commands=build(DATA,PROTOCOL,*self.original)
        self.assertEqual(len(sources),6)
        self.assertEqual(len(manifest["candidates"]),6)
        self.assertEqual(manifest["current_support"],self.original[0]["current_support"])
        self.assertEqual(len(manifest["current_support"]),1)
        self.assertTrue(manifest["not_evaluator_world"])
        self.assertNotIn("D2IndependentWorld",commands)
        self.assertTrue(all("parameter Real capacity" in x for x in sources.values()))
        self.assertEqual({x["modelica_class"] for x in manifest["candidates"]},
                         {k.removesuffix(".mo") for k in sources})
        from scripts.arena_d_v01 import generate
        by_id={c["id"]:c for c in generate(DATA)["candidates"]}
        for result in manifest["candidates"]:
            c=by_id[result["candidate_id"]]
            self.assertEqual(result["structure_hash"],c["structure_hash"])
            source=sources[result["modelica_class"]+".mo"]
            self.assertIn("parameter Real responseTime = "+format(
                result["d2_parameters"]["response_time"],".12g")+";",source)
            self.assertNotIn("if probe==",source)
            self.assertNotIn("short",source.lower())

    def test_altered_parameter_or_structure_cannot_pass_lineage(self):
        original=list(self.original)
        fake=copy.deepcopy(original[0])
        fake["report"]["results"][0]["revised_best_parameters"]["response_time"]=999
        # Recompute the trace hash to probe the semantic gate, not only the
        # earlier tamper-evident event hash gate.
        from scripts.arena_v0_contract import digest
        fake["d2_trace_event"]["payload_hash"]=digest(fake["report"])
        fake["d2_trace_event"]["event_hash"]=digest({
            k:v for k,v in fake["d2_trace_event"].items() if k!="event_hash"})
        original[0]=fake
        with self.assertRaisesRegex(ValueError,"D2_PARAMETER_OUTSIDE_GRID"):
            verify_lineage(DATA,PROTOCOL,*original)
        original=list(self.original)
        fake=copy.deepcopy(original[0])
        fake["report"]["results"][0]["structure_changed"]=True
        fake["d2_trace_event"]["payload_hash"]=digest(fake["report"])
        fake["d2_trace_event"]["event_hash"]=digest({
            k:v for k,v in fake["d2_trace_event"].items() if k!="event_hash"})
        original[0]=fake
        with self.assertRaisesRegex(ValueError,"D2_UNAUTHORIZED_STRUCTURE_OR_PARAMETER"):
            verify_lineage(DATA,PROTOCOL,*original)

    def test_rejects_rival_artifacts_and_revision_claims(self):
        original=list(self.original)
        fake=copy.deepcopy(original[0])
        fake["report"]["arm_id"]="B"
        original[0]=fake
        with self.assertRaisesRegex(ValueError,"INVALID_D2_REPORT"):
            build(DATA,PROTOCOL,*original)
        original=list(self.original)
        fake=copy.deepcopy(original[2])
        fake["other_arm_result"]={"M":"adversarial"}
        # An extra foreign field must fail even when its hash is reattached
        # to a hand-edited report; the original trial contract remains strict.
        from scripts.arena_v0_contract import digest
        original[0]=copy.deepcopy(original[0])
        original[0]["report"]["trial_hash"]=digest(fake)
        original[0]["d2_trace_event"]["payload_hash"]=digest(original[0]["report"])
        original[0]["d2_trace_event"]["event_hash"]=digest({
            k:v for k,v in original[0]["d2_trace_event"].items() if k!="event_hash"})
        original[2]=fake
        from scripts.arena_d_atms_bridge import BridgeError
        with self.assertRaises(BridgeError):
            build(DATA,PROTOCOL,*original)

    def test_parent_blob_gate_tampering(self):
        import shutil
        from scripts.arena_d2_revised_g2 import PARENT_FILE_SHA256
        with tempfile.TemporaryDirectory() as temp:
            tmp=Path(temp)
            for name in PARENT_FILE_SHA256:
                shutil.copyfile(PARENT/name,tmp/name)
            with (tmp/"screen.json").open("ab") as f:
                f.write(b" ")
            with self.assertRaisesRegex(ValueError,"D2_PARENT_BYTES_CHANGED:screen.json"):
                read_parent(tmp)

    def test_d2_reviser_does_not_read_evaluator_world(self):
        manifest,source,commands=build(DATA,PROTOCOL,*self.original)
        self.assertNotIn("D2IndependentWorld",json.dumps(manifest))
        self.assertNotIn("D2IndependentWorld",str(source))
        self.assertEqual(manifest["g2_status"],"AWAITING_REAL_MODELICA")


if __name__=="__main__":
    unittest.main()
