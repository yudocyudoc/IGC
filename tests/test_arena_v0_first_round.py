import copy
import json
import unittest
from pathlib import Path
from scripts.arena_v0_first_round import run
from scripts.arena_v0_contract import digest
R=Path(__file__).resolve().parents[1]
S=json.loads((R/"data/synthetic/arena_v0_primary_construction.json").read_text())
A=json.loads((R/"data/synthetic/arena_v0_declared_d_assumptions.json").read_text())
class FirstRound(unittest.TestCase):
 def test_real_native_methods_with_honest_blocking(self):
  original=copy.deepcopy(S)
  x=run(S,A)
  self.assertEqual(S,original)
  self.assertEqual(x["provider_calls"],0)
  self.assertEqual(x["solver_calls"],0)
  self.assertEqual(x["arms"]["B"]["status"],"BLOCKED")
  self.assertEqual(x["arms"]["D"]["status"],"NATIVE_CANDIDATES_GENERATED_NOT_SIMULATED")
  self.assertGreater(len(x["arms"]["D"]["native"]["candidates"]),0)
  self.assertEqual(x["arms"]["M"]["status"],"PARTIAL_ENGINEERING_ENUMERATION_ONLY")
  self.assertEqual(x["arms"]["M"]["submission"]["hypothesis_ids"],[])
  self.assertEqual(x["holdout"],"NOT_ACCESSED")
  self.assertEqual(len({a["source_input_hash"] for a in x["arms"].values()}),1)
  self.assertEqual(digest(x),digest(run(S,A)))
 def test_without_nominal_assumptions_d_blocks_not_borrow_m(self):
  x=run(S)
  self.assertEqual(x["arms"]["D"]["status"],"BLOCKED")
  self.assertEqual(x["arms"]["B"]["status"],"BLOCKED")
  self.assertEqual(x["arms"]["M"]["status"],"PARTIAL_ENGINEERING_ENUMERATION_ONLY")
 def test_no_ranking_no_false_success(self):
  x=run(S,A)
  self.assertEqual(x["cross_arm_ranking"],"NOT_RUN")
  self.assertEqual(x["empirical_status"],"NOT_EVALUATED")
  self.assertNotIn("G3_PASS",json.dumps(x))
if __name__=="__main__":unittest.main()
