"""PT04 tests against the actual, archived R1 dossier from PT01."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest

from scripts.arena_r2_memory_first_cut import ingest, load_dossier, snapshot
from scripts.ledger import Ledger
from scripts.arena_r2_memory_first_cut import MIGRATION
from scripts.arena_atms import project, events_from_ledger

DOSSIER=os.environ.get("ARENA_R2_PT01_DIR")
BEFORE="2026-10-27T15:00:00Z"
AFTER="2026-10-27T15:01:00Z"

@unittest.skipUnless(DOSSIER,"Use original PT01 artifact, not synthetic model bytes")
class LedgerR2PT04(unittest.TestCase):
    def test_reconstruct_temporal_views_and_isolation(self):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/"igc.sqlite"
            answer=ingest(db,DOSSIER,BEFORE,AFTER)
            case=answer["case_id"]
            self.assertEqual(answer["second_decisions"],0)
            self.assertFalse(answer["feedback_delivered"])
            self.assertEqual(answer["provider_calls"],0)
            before=snapshot(db,case,BEFORE,"B")
            after=snapshot(db,case,AFTER,"B")
            self.assertGreater(len(after["visible_entities"]),len(before["visible_entities"]))
            self.assertNotIn("r2-packet-prepared", " ".join(before["visible_entities"]))
            self.assertIn("r2-packet-prepared", " ".join(after["visible_entities"]))
            for lane in ("D","M","B"):
                view=snapshot(db,case,AFTER,lane)
                names=" ".join(view["visible_entities"])
                for foreign in ({"D","B","M"}-{lane}):
                    self.assertNotIn(":"+foreign+":",names)
                self.assertIn(":COMMON:source",names)
                self.assertIn(":"+lane+":r2-packet-prepared",names)
            self.assertNotIn(":B:r1-native-and-log",
                             " ".join(snapshot(db,case,AFTER,"D")["visible_entities"]))

    def test_alternative_support_and_epistemic_limit(self):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/"igc.sqlite"
            case=ingest(db,DOSSIER,BEFORE,AFTER)["case_id"]
            original=Ledger(db,MIGRATION).snapshot(case_id=case,as_known_at=AFTER)
            engine,_=project(events_from_ledger(original),as_known_at=AFTER,
                             lane="B",investigation_id=case)
            claim="arena:r2:"+case+":B:original-proposal-received"
            before=engine.explain(claim)
            self.assertTrue(before["supported"])
            self.assertEqual(len(before["minimal_environments"]),2)
            self.assertEqual(engine.what_if(
                disable_assumptions=["arena:r2:"+case+":B:native-receipt"]
                )["canonical_mutated"],False)
            altered=engine.what_if(disable_assumptions=[
                "arena:r2:"+case+":B:native-receipt"])
            self.assertTrue(altered["changed_nodes"][claim]["after"])
            self.assertEqual(len(altered["changed_nodes"][claim]["after"]),1)
            self.assertEqual(engine.explain(claim),before)
            self.assertEqual(snapshot(db,case,BEFORE,"B")["truth_status"],
                             "NOT_DETERMINED_BY_ATMS")

    def test_parent_and_d_m_abstention_are_not_mutated(self):
        m,v,p,n=load_dossier(DOSSIER)
        self.assertEqual(len(p["D"]["r1_candidates"]),6)
        self.assertEqual(len(p["M"]["r1_candidates"]),3)
        self.assertIsNone(p["M"]["chosen_parent"])
        self.assertEqual(p["M"]["r1_decision"]["status"],"ABSTAIN")
        self.assertEqual(p["B"]["g3"],"NOT_COMPUTABLE")
        with tempfile.TemporaryDirectory() as td:
            copydir=Path(td)/"changed"
            copydir.mkdir()
            for filename in ("manifest.json","b-visible.json","b-own-feedback.json",
                             "d-own-state.json","m-own-state.json","b-parent-native.json"):
                (copydir/filename).write_bytes((Path(DOSSIER)/filename).read_bytes())
            parent=copydir/"b-parent-native.json"
            parent.write_bytes(parent.read_bytes()+b" ")
            with self.assertRaisesRegex(ValueError,"R2_PARENT_BYTES_DIFFER"):
                load_dossier(copydir)

if __name__=="__main__":
    unittest.main()
