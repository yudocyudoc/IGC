"""PT03: independent own-policy ratification; no second physical model invented."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest

from scripts.arena_r2_dm_decisions import own_decisions, persist
from scripts.arena_r2_memory_first_cut import ingest, snapshot
from scripts.arena_atms import events_from_ledger, project
from scripts.arena_r2_memory_first_cut import MIGRATION
from scripts.ledger import Ledger

DOSSIER=os.environ.get("ARENA_R2_PT01_DIR")
BEFORE="2026-10-27T15:00:00Z"
PREPARED="2026-10-27T15:01:00Z"
DECIDED="2026-10-27T15:02:00Z"

@unittest.skipUnless(DOSSIER,"Original PT01 artifact required; no mock native result")
class PT03RealR1OwnPolicies(unittest.TestCase):
    def test_d_and_m_own_dispositions(self):
        r=own_decisions(DOSSIER)
        self.assertEqual(r["d"]["decision"],"RATIFY_SIX_ALTERNATIVES")
        self.assertEqual(r["m"]["decision"],"RATIFY_ABSTENTION")
        self.assertEqual(len(r["d"]["hypothesis_ids_retained"]),6)
        self.assertIsNone(r["d"]["chosen_parent"])
        self.assertIsNone(r["m"]["chosen_parent"])
        self.assertEqual(r["m"]["underlying_native_status"],"ABSTAIN")
        self.assertEqual(r["m"]["native_reason"],
                         "ALL_FIXED_E1_STRUCTURES_MISS_CONSTRUCTION_TOLERANCE")
        self.assertGreater(r["m"]["best_rmse_items"],r["m"]["predeclared_max_best_rmse_items"])
        self.assertEqual(r["new_provider_calls"],r["new_solver_runs"])
        self.assertEqual(r["new_provider_calls"],0)
        for lane in ("d","m"):
            self.assertFalse(r[lane]["new_observations"])
            self.assertFalse(r[lane]["structural_change"])
            self.assertFalse(r[lane]["parameter_change"])
        self.assertEqual(r,own_decisions(DOSSIER))

    def test_no_truth_choice_or_peer_data_leaks(self):
        r=own_decisions(DOSSIER)
        for lane,other in (("d","C01"),("m","D-")):
            text=json.dumps(r[lane])
            self.assertNotIn(other,text)
            self.assertNotIn("congestion_multiplier",text)
        self.assertNotIn("G2_PASS",r["b"])

    def test_append_and_before_after_with_b_unchanged(self):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/"r2.sqlite"
            init=ingest(db,DOSSIER,BEFORE,PREPARED)
            decisions=own_decisions(DOSSIER)
            record=persist(db,DOSSIER,decisions,prior_cut=PREPARED,recorded_at=DECIDED)
            self.assertEqual(record["decisions"]["D"],"RATIFY_SIX_ALTERNATIVES")
            self.assertEqual(record["decisions"]["M"],"RATIFY_ABSTENTION")
            self.assertEqual(record["decisions"]["B"],"PENDING")
            self.assertTrue(record["b_view_unchanged"])
            case=init["case_id"]
            for lane in ("D","M"):
                before=snapshot(db,case,PREPARED,lane)
                after=snapshot(db,case,DECIDED,lane)
                claim="arena:r2:"+case+":"+lane+":r2-own-decision-supported"
                self.assertNotIn(claim,before["logical"]["labels"])
                self.assertIn(claim,after["logical"]["labels"])
                self.assertIn("r2-own-decision", " ".join(after["visible_entities"]))
                forbidden=":M:" if lane=="D" else ":D:"
                self.assertNotIn(forbidden," ".join(after["visible_entities"]))
                revisions=Ledger(db,MIGRATION).snapshot(case_id=case,as_known_at=DECIDED)
                engine,_=project(events_from_ledger(revisions),as_known_at=DECIDED,
                                 lane=lane,investigation_id=case)
                self.assertTrue(engine.explain(claim)["supported"])
                prior_explain=engine.explain(claim)
                model=engine.what_if(disable_assumptions=[
                    "arena:r2:"+case+":"+lane+":r2-policy-applied"])
                self.assertEqual(model["changed_nodes"][claim]["after"],[])
                self.assertEqual(engine.explain(claim),prior_explain)
            # Re-ingesting same exact decision is idempotent: no new revision.
            again=persist(db,DOSSIER,decisions,prior_cut=PREPARED,recorded_at=DECIDED)
            self.assertEqual(again["decisions"],record["decisions"])

    def test_modified_evaluation_denied_before_persistence(self):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/"r2.sqlite"
            ingest(db,DOSSIER,BEFORE,PREPARED)
            decisions=own_decisions(DOSSIER)
            for wrong in ("wrong_source","fake_m_selection","fake_d_reduction"):
                edited=copy.deepcopy(decisions)
                if wrong=="wrong_source":
                    edited["source_snapshot_hash"]="sha256:"+"f"*64
                elif wrong=="fake_m_selection":
                    edited["m"]["chosen_parent"]="C01"
                else:
                    edited["d"]["hypothesis_ids_retained"]=["D-FAKE"]
                with self.assertRaisesRegex(ValueError,"R2_DECISIONS_ALTERED"):
                    persist(db,DOSSIER,edited,prior_cut=PREPARED,recorded_at=DECIDED)
            with self.assertRaisesRegex(ValueError,"R2_DECISION_MUST_FOLLOW"):
                persist(db,DOSSIER,decisions,prior_cut=DECIDED,recorded_at=PREPARED)

if __name__=="__main__":
    unittest.main()
