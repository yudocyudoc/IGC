"""CT-03 B public preparation shares the four observation cuts, not hidden truth."""
import unittest
from scripts.arena_cafe.ct03_b_visible import view
from scripts.arena_cafe.ct03_m_construction_diagnostic import OBS_SCHEMA

SRC="sha256:"+"a"*64


class BuffaloVisibleTests(unittest.TestCase):
    def visible(self):
        return {"schema":OBS_SCHEMA,"source_snapshot_hash":SRC,
            "world_public_id":"W1","condition_id":"C0",
            "time_unit":"hours","observable":"cumulative_delivered",
            "observations":[{"time":t,"delivered":v}
                            for t,v in ((0,0),(1,.1),(2,.2),(4,.4))]}
    def test_common_source_and_only_construction(self):
        out=view(self.visible(),world="W1",round_kind="initial")
        self.assertEqual(out["case_id"],"CT-03")
        self.assertEqual(out["construction"]["input"]["pulse_rate"],1.7)
        self.assertEqual(out["observability"]["construction_times_hours"],[0,1,2,4])
        self.assertNotIn("future",str(out).lower())
        self.assertNotIn("truth",str(out).lower())

    def test_reject_future_and_cross_world(self):
        x=self.visible();x["observations"][3]["time"]=8
        with self.assertRaises(ValueError):
            view(x,world="W1",round_kind="initial")
        with self.assertRaisesRegex(ValueError,"CT02_M_WRONG_CONSTRUCTION_SCOPE"):
            view(self.visible(),world="W2",round_kind="initial")

if __name__=="__main__":
    unittest.main()
