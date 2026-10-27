"""Two authorized-world workflow gate safety: zero solver in CI preflight."""
import json
from pathlib import Path
import tempfile
import unittest

from scripts.arena_r3_pt06_t23_preregister import freeze
from scripts.arena_r3_pt06_t23_worlds import prepare
from scripts.arena_r3_pt06_t23_grade import grade
from scripts.arena_v0_contract import digest

HASH="sha256:50cd8313a1a41cfca43391e105948c929122599b04ae70a375e255cd026b6064"

class T23AuthorizedGateSafety(unittest.TestCase):
    def test_exact_budget_and_unmodified_frozen_protocol(self):
        self.assertEqual(digest(freeze()[0]),HASH)
        Path("artifacts").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir="artifacts") as d:
            root=Path("artifacts")/Path(d).name/"t23"
            budget=prepare(root)
            text=(root/"two-worlds-NOT-RUN.mos").read_text()
            self.assertEqual(text.count("simulate("),2)
            self.assertEqual(text.count("checkModel("),2)
            self.assertIn("stopTime=0.15",text)
            self.assertIn("stopTime=3,",text)
            self.assertEqual(budget["world_simulations_max"],2)
            self.assertEqual(budget["candidate_simulations_max"],0)
            self.assertEqual(budget["new_solver_calls_now"],0)
            self.assertNotIn("R3C00P",text)
            self.assertNotIn("R3C01P",text)
            self.assertNotIn("R3C02P",text)
            self.assertFalse(list(root.rglob("*_res.csv")))
            with self.assertRaises((FileNotFoundError,ValueError)):
                grade(root)

    def test_post_selection_never_use_truth_as_input(self):
        # Must have BOTH public decisions and authenticated private source CSV
        # before the research-world identity can be revealed.
        Path("artifacts").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir="artifacts") as d:
            root=Path("artifacts")/Path(d).name/"t23"
            prepare(root)
            (root/"t2-construction-only.json").write_text("{}")
            with self.assertRaises((FileNotFoundError,KeyError,ValueError)):
                grade(root)

if __name__=="__main__":
    unittest.main()
