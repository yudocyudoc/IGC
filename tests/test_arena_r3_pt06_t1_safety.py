"""R3 T1 consent gate invariants before the real 28 Modelica simulations."""
import json
from pathlib import Path
import tempfile
import unittest

from scripts.arena_r3_pt06_t1_simulate import commands,emit
from scripts.arena_r3_pt06_t1_extract import extract
from scripts.arena_r3_pt06_parametric import CASE_PLAN,plan
from scripts.arena_r3_pt06_evaluate import evaluate_csv,checked_case


class R3T1BudgetSafety(unittest.TestCase):
    def test_single_case_28_and_no_world_reserved_observations(self):
        # Cannot emit outside artifacts/ because Modelica reads with /repo root.
        Path("artifacts").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir="artifacts") as temp:
            name=Path(temp).name
            folder=Path("artifacts")/name/"r3-t1"
            receipt=emit(folder)
            text=commands(folder)
            self.assertEqual(text.count("simulate("),28)
            self.assertEqual(text.count("checkModel("),28)
            self.assertEqual(receipt["authorized_candidate_simulations"],27)
            self.assertEqual(receipt["authorized_world_simulations"],1)
            self.assertEqual(receipt["total_simulation_commands"],28)
            self.assertFalse(receipt["world_reserved_times_generated"])
            self.assertEqual(receipt["provider_calls"],0)
            self.assertEqual(receipt["solver_calls_before_workflow"],0)
            self.assertEqual(text.count("ArenaR3World.R3WorldT1"),2)
            self.assertIn("startTime=0,stopTime=3,numberOfIntervals=120",text)
            self.assertEqual(text.count("startTime=0,stopTime=6,numberOfIntervals=120"),27)
            self.assertIn('fileNamePrefix="artifacts/',text)
            self.assertEqual(json.loads((folder/"solver-budget.json").read_text()),receipt)
            self.assertFalse(list((folder/"candidates").glob("*.csv")))
            self.assertFalse(list((folder/"world-private").glob("*.csv")))
            with self.assertRaisesRegex(ValueError,"R3_OUTPUT_EXISTS"):
                emit(folder)

    def test_disallow_fictional_world_or_candidate_evaluations(self):
        with tempfile.TemporaryDirectory(dir="artifacts") as temp:
            folder=Path("artifacts")/Path(temp).name/"r3-t1"
            emit(folder)
            with self.assertRaisesRegex(ValueError,"R3_T1_REAL_WORLD_SOLVER_CSV_MISSING"):
                extract(folder,Path("experiments/e0/catalog.json"))
            case={
                "schema":"igc-arena-r3-m-construction-only/0.1",
                "case_id":CASE_PLAN["case_id"],
                "observability":"deliveredTotal",
                "public_stimulus":{"kind":"pulse","rate":1.7,"duration":2.0},
                "construction_observations":[{"t":i,"delivered":0.0} for i in range(4)],
                "measurement_bound_status":"NO_INSTRUMENT_BOUND",
                "source_snapshot_hash":"sha256:"+"0"*64,
                "synthetic_case":True
            }
            checked_case(case,plan()[0])
            with self.assertRaisesRegex(ValueError,"R3_CANDIDATE_CSV_MISSING"):
                evaluate_csv(plan()[0],case,folder,json.loads(Path("experiments/e0/catalog.json").read_text()))

if __name__=="__main__":
    unittest.main()
