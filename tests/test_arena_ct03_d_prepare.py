"""CT-03 original D grammar, no artificial construction data or new solver."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_cafe.ct03_d_prepare import original_six, prepare, bind_authentic_construction
from scripts.arena_cafe.ct03_public import OBS_SCHEMA
from scripts.arena_cafe.ct_feedback_bridge import make_context

SRC = "sha256:"+"a"*64


def construction():
    return {"schema":OBS_SCHEMA,"source_snapshot_hash":SRC,
            "world_public_id":"W1","condition_id":"C0",
            "time_unit":"hours","observable":"cumulative_delivered",
            "observations":[{"time":t,"delivered":d}
                            for t,d in ((0,0),(1,.1),(2,.2),(4,.4))]}


def scope():
    return make_context(experiment="CT03",world="W1",round_id="R0",
                        arm="D",condition="C0",source_hash=SRC)


class OriginalDTest(unittest.TestCase):
    def test_six_original_renderer_models_and_euler_script(self):
        rows, sources = original_six()
        self.assertEqual(len(rows),6)
        self.assertEqual([len(r["structure"]["stocks"]) for r in rows],[1,1,2,2,3,3])
        self.assertEqual([r["structure"]["loss"] for r in rows],[False,True]*3)
        self.assertTrue(all("der(delivered)" in model for model in sources))
        with TemporaryDirectory() as tmp:
            out=Path(tmp)/"prepared"
            m=prepare(out)
            self.assertEqual(m["executed_new_omc"],0)
            self.assertEqual(m["D2"],"NOT_APPLICABLE_MISSING_RESET_TRIAL")
            script=(out/"simulate.mos").read_text()
            self.assertEqual(script.count("simulate("),6)
            self.assertEqual(script.count('method="euler"'),6)
            self.assertEqual(script.count("numberOfIntervals=64"),6)
            self.assertFalse(m["construction_observations_read"])

    def test_actual_public_cuts_use_original_generate_and_no_fit(self):
        with TemporaryDirectory() as tmp:
            m=prepare(Path(tmp)/"prepared")
            result=bind_authentic_construction(construction(),scope(),m)
            self.assertEqual(result["candidate_ids"],[c["id"] for c in m["candidates"]])
            self.assertEqual(result["new_omc"],0)
            self.assertEqual(result["D2"],"NOT_APPLICABLE_MISSING_RESET_TRIAL")

    def test_no_future_truth_and_wrong_world_rejected(self):
        with TemporaryDirectory() as tmp:
            m=prepare(Path(tmp)/"prepared")
            x=construction()
            x["observations"].append({"time":6,"delivered":1.9})
            with self.assertRaisesRegex(ValueError,"FOUR_CONSTRUCTION_CUTS_REQUIRED"):
                bind_authentic_construction(x,scope(),m)
            x=construction()
            x["world_public_id"]="W2"
            with self.assertRaisesRegex(ValueError,"WRONG_CONSTRUCTION_SCOPE"):
                bind_authentic_construction(x,scope(),m)


if __name__=="__main__":
    unittest.main()
