"""Pre-call, no-network checks for SD System A/B diagnostic."""
import copy
import json
import unittest
from scripts.arena_sd_system_ab_v1 import MANIFEST, build, parse, ORDER, IDS

class SDABTests(unittest.TestCase):
    def setUp(self):
        self.good={"selected_candidate_ids":sorted(IDS),
                   "rationale":"Both are potentially plausible without distinct transient data.",
                   "falsifier":"A controlled experiment can measure the early cumulative trace.",
                   "unknowns":["Noise may mask distinctions."],
                   "next_test":"Reset and measure at 0.25, 0.5, 1 and 2 hours."}

    def test_two_world_paired_identical_input(self):
        manifest, req=build()
        self.assertEqual([(r["case_id"],r["variant"]) for r in req],ORDER)
        self.assertEqual(manifest["retries"],0)
        for world in ("WA","WB"):
            same=[r for r in req if r["case_id"]==world]
            self.assertEqual(len(same),2)
            self.assertEqual(same[0]["user_hash"],same[1]["user_hash"])
            self.assertEqual(same[0]["body"]["messages"][1],same[1]["body"]["messages"][1])
            self.assertNotEqual(same[0]["body"]["messages"][0],same[1]["body"]["messages"][0])

    def test_model_config_identical(self):
        _,req=build()
        for r in req:
            body=r["body"]
            self.assertEqual(body["temperature"],0)
            self.assertEqual(body["reasoning_effort"],"low")
            self.assertEqual(body["max_completion_tokens"],4096)
            self.assertEqual([m["role"] for m in body["messages"]],["system","user"])

    def test_five_field_parser(self):
        self.assertEqual(parse(json.dumps(self.good)),self.good)
        empty=copy.deepcopy(self.good)
        empty["selected_candidate_ids"]=[]
        self.assertEqual(parse(json.dumps(empty)),empty)

    def test_reject_bad_candidates_and_schemas(self):
        for invalid in ("", "{", json.dumps(dict(self.good, selected_candidate_ids=["unknown"])),
                        json.dumps(dict(self.good, unknowns="not list")),
                        json.dumps(dict(self.good, rationale="")),
                        json.dumps(dict(self.good, selected_candidate_ids=[*sorted(IDS),*sorted(IDS)]))):
            with self.subTest(invalid=invalid[:40]):
                with self.assertRaises(ValueError):
                    parse(invalid)

    def test_frozen_baseline_text(self):
        man=json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertIn("not asserting truth",man["baseline_system"])
        self.assertTrue(man["truth_commitment"].startswith("sha256:"))
        self.assertEqual(len(man["truth_commitment"]),71)

if __name__=="__main__":
    unittest.main()
