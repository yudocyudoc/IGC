"""Before one-time authorization: source lock and native one-call physical program."""
import json
import os
from pathlib import Path
import tempfile
import unittest

from scripts.arena_r4_pt07_t2_one_world import prepare,SHA
from scripts.arena_r4_pt07_t2_collect import extract
from scripts.arena_r4_pt07_t2_adjudicate import adjudicate,evaluate_to_file
from scripts.arena_r4_pt07_t2_score import score_verified_lock

LOCK=os.environ.get("ARENA_R4_ORIGINAL_LOCK_DIR")
ORIGINAL_T23=os.environ.get("ARENA_R4_ORIGINAL_T23_DIR")

@unittest.skipUnless(LOCK and ORIGINAL_T23,
                     "Real archived T2 and forecast lock required")
class RealPreflight(unittest.TestCase):
    def test_one_original_world_only_no_recreated_C00_C01_C02_candidates(self):
        Path("artifacts").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir="artifacts") as tmp:
            folder=Path("artifacts")/Path(tmp).name/"r4"
            budget=prepare(LOCK,folder)
            program=(folder/"one-world.mos").read_text()
            model=(folder/"ArenaR3T23Worlds-ORIGINAL.mo").read_bytes()
            self.assertEqual(budget["forecast_lock_sha256"],SHA)
            self.assertEqual(budget["world_simulate_max"],1)
            self.assertEqual(budget["candidate_simulate_max"],0)
            self.assertEqual(budget["provider_inference_max"],0)
            self.assertEqual(budget["automatic_retry_max"],0)
            self.assertEqual(program.count("simulate("),1)
            self.assertEqual(program.count("checkModel("),1)
            self.assertIn('loadFile("/repo/',program)
            self.assertIn("ArenaR3T23Worlds.R3T2World",program)
            self.assertNotIn("simulate(ArenaR3T23Worlds.R3T3World",program)
            self.assertIn("stopTime=1,numberOfIntervals=800",program)
            self.assertEqual(model,Path(ORIGINAL_T23,"ArenaR3T23Worlds-NOT-SIMULATED.mo").read_bytes())
            self.assertFalse(list(folder.rglob("*_res.csv")))
            with self.assertRaisesRegex(ValueError,"R4_ONE_WORLD_OUTPUT_ALREADY_EXISTS"):
                prepare(LOCK,folder)
            with self.assertRaisesRegex(ValueError,"R4_T2_REAL_FRESH_OR_ORIGINAL_CSV_MISSING"):
                extract(folder,ORIGINAL_T23,LOCK,
                        json.loads(Path("experiments/e0/catalog.json").read_text()))
            with self.assertRaises((FileNotFoundError,ValueError)):
                evaluate_to_file(folder,LOCK)
            with self.assertRaisesRegex(ValueError,"R4_WORLD_TRUTH_CANNOT_BE_OPENED_BEFORE_SCORING"):
                adjudicate(folder,LOCK)
            self.assertEqual(json.loads((folder/"budget.json").read_text()),budget)

if __name__=="__main__":
    unittest.main()
