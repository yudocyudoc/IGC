"""PT06 closure tests use actual archived OpenModelica artifacts, not mocks."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from scripts.arena_r3_pt06_consolidate import (
    inspect,close,persist,SCHEMA,EXPECTED,ADMIN_CUTS,T1_CASE,T2_CASE,T3_CASE
)
from scripts.arena_r2_memory_first_cut import snapshot,MIGRATION
from scripts.ledger import Ledger

ROOT1=os.getenv("ARENA_R3_T1_ORIGINAL_DIR")
ROOT23=os.getenv("ARENA_R3_T23_ORIGINAL_DIR")
CATALOG="experiments/e0/catalog.json"

@unittest.skipUnless(ROOT1 and ROOT23,"Authentic archived E1 CSVs required")
class RealR3Consolidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=inspect(ROOT1,ROOT23,CATALOG)

    def test_all_original_decisions_reproduced_no_new_physics(self):
        r=self.result
        self.assertEqual(r["schema"],SCHEMA)
        self.assertEqual([x["case_id"] for x in r["cases"]],
                         [T1_CASE,T2_CASE,T3_CASE])
        self.assertEqual(r["solver_calls_in_consolidation"],0)
        self.assertEqual(r["provider_calls_in_consolidation"],0)
        self.assertEqual(r["R4_holdout"],"NOT_ACCESSED")
        self.assertEqual(r["T2_T3_candidate_CSV_reused"],27)
        self.assertEqual(r["T1_candidate_simulations_historical"],27)
        self.assertEqual(r["new_world_simulations_historical"],3)
        for c in r["cases"]:
            expect=EXPECTED[c["case_id"]]
            self.assertEqual(c["original_M3"]["status"],"ABSTAIN")
            self.assertEqual(c["R3_grid"]["status"],expect["outcome"])
            self.assertEqual(c["R3_grid"]["compatible"],expect["compatible"])
            self.assertEqual(c["synthetic_source_after_selection_REVIEWER_ONLY"],
                             expect["source"])
            self.assertEqual(len(c["construction_observations"]),4)
            self.assertEqual(c["world_G2_status"],"G2_SIMULATED_CONDITIONALLY")
            self.assertLess(c["world_max_balance_residual_items"],1e-7)

    def test_f1a_atms_before_after_counterfactual_lanes_and_private_truth(self):
        with tempfile.TemporaryDirectory() as td:
            database=Path(td)/"pt06.sqlite"
            r=copy.deepcopy(self.result)
            memories=persist(database,r)
            self.assertEqual(len(memories["case_receipts"]),3)
            self.assertTrue(memories["no_cross_arm_sharing"])
            self.assertFalse(memories["ATMS_truth_guarantee"])
            ledger=Ledger(database,MIGRATION)
            for x in memories["case_receipts"]:
                case=x["case_id"]
                self.assertEqual(x["before_M_visible"],0)
                self.assertGreaterEqual(x["after_M_visible"],7)
                self.assertTrue(x["policy_what_if"]["R3_support_removed"])
                self.assertTrue(x["policy_what_if"]["frozen_M3_support_remains"])
                self.assertTrue(x["synthetic_truth_hidden_from_M"])
                self.assertTrue(x["D_B_unchanged"])
                m=snapshot(database,case,x["administrative_replay_time"],"M")
                d=snapshot(database,case,x["administrative_replay_time"],"D")
                b=snapshot(database,case,x["administrative_replay_time"],"B")
                self.assertEqual(d["visible_entities"],[])
                self.assertEqual(b["visible_entities"],[])
                self.assertNotIn("source-truth-after-grading",
                                 " ".join(m["visible_entities"]))
                self.assertEqual(len(m["logical"]["labels"]),8)  # 4 premises, 2 decision/physics facts, 2 derived claims
                all_revisions=ledger.snapshot(case_id=case,as_known_at=ADMIN_CUTS[4])
                secret=[v for v in all_revisions if
                        v.entity_id.endswith("source-truth-after-grading")]
                self.assertEqual(len(secret),1)
                self.assertEqual(secret[0].access_policy,"case-private")
            for lane in ("D","B","M"):
                hidden=snapshot(database,"ARENA-R3-PT06-CONSOLIDATION",
                                ADMIN_CUTS[4],lane)
                self.assertEqual(hidden["visible_entities"],[])

    def test_cross_case_responses_are_scoped_not_transferred(self):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/"db.sqlite"
            persist(db,self.result)
            t1=snapshot(db,T1_CASE,ADMIN_CUTS[4],"M")
            t2=snapshot(db,T2_CASE,ADMIN_CUTS[4],"M")
            t3=snapshot(db,T3_CASE,ADMIN_CUTS[4],"M")
            self.assertNotEqual(t1["visible_entities"],t2["visible_entities"])
            for current,other in ((t1,T2_CASE),(t2,T3_CASE),(t3,T1_CASE)):
                self.assertFalse(any(other in v for v in current["visible_entities"]))

if __name__=="__main__":
    unittest.main()
