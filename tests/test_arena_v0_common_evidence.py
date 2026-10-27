import copy
import json
import unittest
from pathlib import Path
from scripts.arena_v0_common_evidence import common, adapt, prepare
from scripts.arena_v0_contract import ArenaContractError

ROOT=Path(__file__).resolve().parents[1]
SOURCE=json.loads((ROOT/"data/synthetic/arena_v0_primary_construction.json").read_text())
ASSUMPTIONS=json.loads((ROOT/"data/synthetic/arena_v0_declared_d_assumptions.json").read_text())

class CommonEvidenceTests(unittest.TestCase):
 def test_one_source_and_three_identical_views(self):
  shared,views=common(SOURCE)
  self.assertEqual(len({x["input_hash"] for x in views}),1)
  self.assertEqual(shared["source_snapshot_hash"],prepare(SOURCE)["source_snapshot_hash"])
  self.assertNotEqual(shared["source_snapshot_hash"],"sha256:"+"1"*64)
 def test_d_blocked_without_declared_values(self):
  v=prepare(SOURCE)
  self.assertEqual(v["arms"]["D"]["status"],"BLOCKED")
  self.assertEqual(v["arms"]["M"]["status"],"VISIBLE_INPUT_READY_NOT_GENERATOR_RUN")
  self.assertEqual(v["science_status"],"NOT_RUN")
 def test_declared_assumptions_do_not_mutate_common_evidence(self):
  before=copy.deepcopy(SOURCE)
  out=prepare(SOURCE,ASSUMPTIONS)
  self.assertEqual(SOURCE,before)
  d=out["arms"]["D"]
  self.assertEqual(d["status"],"READY_CONDITIONAL_ASSUMPTIONS")
  self.assertEqual(d["assumption_provenance"],"USER_DECLARED_NOT_OBSERVED")
  self.assertEqual(d["derived_input"]["construction"]["nominal_parameters"]["capacity"],2)
  self.assertEqual(len({x["common_input_hash"] for x in out["arms"].values()}),1)
 def test_negative_tampering_or_invalid_assumptions(self):
  v=copy.deepcopy(SOURCE);v["observations"][2]["t"]=0
  with self.assertRaises(ArenaContractError): common(v)
  with self.assertRaises(ArenaContractError):
   prepare(SOURCE,{"nominal_parameters":{"capacity":-1,"response_time":1,"loss_time":3}})
 def test_no_private_fields(self):
  v=copy.deepcopy(SOURCE);v["gold"]="secret"
  with self.assertRaises(ArenaContractError):common(v)
if __name__=="__main__":unittest.main()
