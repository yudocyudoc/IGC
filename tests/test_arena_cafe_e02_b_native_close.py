"""Reconcile real native and G1 vintage events into frozen 6-case ATMS ledger.

No inference, solver, network, hidden holdout or manual model edit in these tests.
"""
from __future__ import annotations

from hashlib import sha256
import os
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_cafe.e02_b_native_close import combine, inspect, PINNED, KNOWLEDGE_TIMES
from scripts.ledger import Ledger
from scripts.arena_atms import events_from_ledger, project


class GenuineNativeTemporalClosure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        keys=("B_CLOSURE_BASELINE","B_CLOSURE_O0","B_CLOSURE_O1",
              "B_CLOSURE_G1_OLD","B_CLOSURE_G1_NEW")
        if not all(os.getenv(k) for k in keys):
            raise unittest.SkipTest("immutable original E02/D/M + original Buffalo native/G1 archives required")
        cls.paths=[Path(os.environ[k]) for k in keys]
        if not all(p.exists() for p in cls.paths):
            raise ValueError("PINNED_E02_EVIDENCE_UNAVAILABLE")
        cls.baseline,cls.o0,cls.o1,cls.old,cls.corrected=cls.paths

    def test_original_archive_identity_native_and_g1_both_conditions(self):
        a=inspect("O0",self.o0,self.old,self.corrected)
        b=inspect("O1",self.o1,self.old,self.corrected)
        self.assertEqual([a["native_variables"],b["native_variables"]],[6,8])
        self.assertEqual([a["G1_v01_issue_count"],b["G1_v01_issue_count"]],[11,2])
        self.assertEqual([a["G1_v02_issue_count"],b["G1_v02_issue_count"]],[3,3])
        self.assertEqual([a["single_point_non_lookup_markers"],b["single_point_non_lookup_markers"]],[5,0])
        self.assertEqual(a["shared_kernel_sha256"],b["shared_kernel_sha256"])
        self.assertNotEqual(a["source_snapshot_hash"],b["source_snapshot_hash"])
        self.assertNotEqual(a["raw_native_object_serialization_sha256"],b["raw_native_object_serialization_sha256"])
        self.assertTrue(all(x["native_revision_calls"]==0 for x in (a,b)))

    def test_temporal_append_only_old_cut_unchanged_and_no_cross_arm_leak(self):
        historical=(self.baseline/"combined_ledger.sqlite").read_bytes()
        self.assertEqual(sha256(historical).hexdigest(), PINNED["baseline"]["combined_ledger.sqlite"])
        with TemporaryDirectory() as work:
            out=Path(work)/"closure"
            report=combine(*self.paths,out)
            self.assertEqual(report["total_e02_b_provider_attempts"],4)
            self.assertEqual(report["new_provider_calls"],report["new_omc_runs"])
            self.assertEqual(report["new_provider_calls"],0)
            self.assertEqual(report["original_b_native_revision_decisions"],0)
            self.assertEqual(report["G2"],report["G3"])
            self.assertEqual(report["G2"],"NOT_RUN")
            self.assertTrue(report["old_three_arm_report_is_historical_not_rewritten"])
            self.assertEqual((self.baseline/"combined_ledger.sqlite").read_bytes(),historical)
            db=Ledger(out/"combined_ledger_v2.sqlite",Path(__file__).resolve().parents[1]/"migrations/0001_ledger.sql")
            for c in ("O0","O1"):
                case="E02-B-"+c
                cuts=report["conditions"][c]["memory"]["snapshots"]
                self.assertEqual([q["current_knowledge_revision"] for q in cuts],[1,2,3,4])
                self.assertEqual([q["no_native_currently_supported"] for q in cuts],[True,False,False,False])
                self.assertEqual([q["native_available"] for q in cuts],[False,True,True,True])
                self.assertEqual([q["g2_blocked_current_native"] for q in cuts],[False,False,False,True])
                self.assertEqual([q["failed_transport_fact_still_supported"] for q in cuts],[True,True,True,True])
                self.assertEqual(report["conditions"][c]["memory"]["new_revisions_appended"],12)
                for cut in report["b_prior_timeout_temporal_projections_preserved"][case]:
                    _,p=project(events_from_ledger(db.snapshot(case_id=case,as_known_at=cut["as_known_at"])),
                          as_known_at=cut["as_known_at"],lane="B",investigation_id=case)
                    self.assertEqual(p["projection_hash"],cut["projection_hash"])
                snap=db.snapshot(case_id=case,as_known_at=KNOWLEDGE_TIMES["g1_new"])
                self.assertEqual(len(snap),13)
                self.assertEqual(next(x for x in snap if x.entity_id==case+":RULE").revision,2)
                self.assertTrue(all(db.verify_integrity(entity_id=x.entity_id,revision=x.revision) for x in snap))
            for case,old in report["dm_temporal_projections_preserved"].items():
                _,p=project(events_from_ledger(db.snapshot(case_id=case,as_known_at=old["as_known_at"])),
                          as_known_at=old["as_known_at"],lane=case.split("-")[1],investigation_id=case)
                self.assertEqual(p["projection_hash"],old["projection_hash"])
            with self.assertRaisesRegex(ValueError,"REFUSE_OVERWRITE"):
                combine(*self.paths,out)

    def test_mutated_provider_receipt_rejected_without_writing_any_ledger(self):
        with TemporaryDirectory() as work:
            damaged=Path(work)/"O0"
            shutil.copytree(self.o0,damaged)
            p=damaged/"initial/receipt.json"
            p.write_bytes(p.read_bytes()+b" ")
            with self.assertRaisesRegex(ValueError,"PINNED_MEMBER_CHANGED"):
                inspect("O0",damaged,self.old,self.corrected)
            with self.assertRaisesRegex(ValueError,"PINNED_MEMBER_CHANGED"):
                combine(self.baseline,damaged,self.o1,self.old,self.corrected,Path(work)/"not-made")
            self.assertFalse((Path(work)/"not-made").exists())

    def test_cross_condition_model_rejected_before_memory_append(self):
        with self.assertRaisesRegex(ValueError,"PINNED_MEMBER_CHANGED"):
            inspect("O0",self.o1,self.old,self.corrected)

    def test_altered_corrected_g1_fails_closed_not_new_native(self):
        with TemporaryDirectory() as work:
            damaged=Path(work)/"corrected"
            shutil.copytree(self.corrected,damaged)
            p=damaged/"O1/g1-diagnostic.json"
            p.write_bytes(p.read_bytes()+b" ")
            with self.assertRaisesRegex(ValueError,"PINNED_MEMBER_CHANGED"):
                inspect("O1",self.o1,self.old,damaged)


if __name__=="__main__": unittest.main()