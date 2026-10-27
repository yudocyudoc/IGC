import json
import unittest
from pathlib import Path
from copy import deepcopy

from scripts.arena_r1_buffalo_initial import build, MAX_CALLS, MAX_OUTPUT_TOKENS
from scripts.arena_v0_common_evidence import prepare
from scripts.arena_v0_contract import digest

ROOT=Path(__file__).resolve().parents[1]
SOURCE=json.loads((ROOT/"data/synthetic/arena_v0_primary_construction.json").read_text())

class R1NativeBuffaloInput(unittest.TestCase):
    def test_same_source_no_rivals(self):
        original=deepcopy(SOURCE)
        v=build(SOURCE)
        p=prepare(SOURCE)
        self.assertEqual(SOURCE,original)
        self.assertEqual(v["source_snapshot_hash"],p["source_snapshot_hash"])
        self.assertEqual(v["construction"]["observations"],SOURCE["observations"])
        self.assertEqual(v["construction"]["input_profile"],SOURCE["input_profile"])
        self.assertEqual(v["resources"]["max_llm_calls"],1)
        self.assertEqual(MAX_CALLS,1)
        self.assertEqual(MAX_OUTPUT_TOKENS,7000)
        self.assertEqual(digest(v),digest(build(SOURCE)))
        txt=json.dumps(v).lower()
        for forbidden in ("c00","c01","c02","dstockflow","best_rmse",
                          "0.150205","0.316560","utilization squared",
                          "generator is", "holdout.csv"):
            self.assertNotIn(forbidden,txt)
        self.assertIn("dt=0.125",v["question"])
    def test_hidden_fields_are_blocked(self):
        s=deepcopy(SOURCE)
        s["holdout"]={"future":8}
        with self.assertRaises(Exception):
            build(s)

if __name__=="__main__":
    unittest.main()
