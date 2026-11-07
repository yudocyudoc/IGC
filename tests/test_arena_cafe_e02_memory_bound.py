"""F171-03: evidence-bound bitemporal ATMS, real retraction, isolation."""
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_cafe.continuity_round import _memory, retract_e02_diagnostic
from scripts.arena_atms import project, events_from_ledger
from scripts.ledger import Ledger

ROOT=Path(__file__).resolve().parents[1]
ZERO_SHA="sha256:"+"b"*64
STAMP=datetime(2026,11,6,16,0,0,tzinfo=timezone.utc)


def example(arm="D",condition="O0"):
    candidates=["native_"+str(i) for i in range(6)]
    diagnostics=[{
        "candidate":c,
        "diagnostic":{
            "status":"DESCRIPTIVE_ONLY_NOT_COMPATIBILITY",
            "residuals":[0,0,0,0,0,i],
            "native_csv_sha256":"sha256:"+format(i+1,"064x"),
            "RMSE":i/10.0,
        }
    } for i,c in enumerate(candidates)]
    feedback={"own_diagnostic_by_candidate":diagnostics,
              "rival_outputs_visible":False,
              "physical_private_des_visible":False,
              "epsilon_model":"UNDEFENDED_NO_PASS_OR_FAIL"}
    decision={
        "author":"EXPLICIT_EXPERIMENTAL_POLICY_NOT_ORIGINAL_ENUMERATOR",
        "private_feedback":feedback,
        "first_decision":{"candidate_ids":candidates},
        "second_decision":{"candidate_ids":candidates,
                           "status":"RATIFY_UNRESOLVED_FULL_SET_WITH_EXPLICIT_LIMITS"}
    }
    return {
        "source":{"condition":condition,"source_snapshot_hash":ZERO_SHA,
                  "visible_sha256":"sha256:"+"c"*64},
        "native":{"arm":arm,"manifest_sha256":"sha256:"+"d"*64,
                  "G2":"HISTORICAL_AUTHENTIC_REAL_OMC_VERIFIED",
                  "candidate_ids":candidates,
                  "verified_g2_traces":{
                      c:diagnostics[i]["diagnostic"]["native_csv_sha256"]
                      for i,c in enumerate(candidates)}},
        "diagnostics":diagnostics,"feedback":feedback,"decision":decision,
    }


class BoundMemoryTest(unittest.TestCase):
    def ledger(self,root):
        return Ledger(Path(root)/"test.sqlite",ROOT/"migrations/0001_ledger.sql")

    def test_missing_report_rejected_not_same_generic_snapshots(self):
        with TemporaryDirectory() as tmp:
            l=self.ledger(tmp)
            with self.assertRaisesRegex(ValueError,"E02_MISSING_OR_INVALID_EVIDENCE_RECORD"):
                _memory(l,"D","O0",None,STAMP)
            self.assertEqual(l.snapshot(case_id="E02-D-O0",
                              as_known_at=(STAMP+timedelta(seconds=1)).isoformat()),[])

    def test_diagnostic_change_alters_provenance_and_dependencies_even_if_decision_same(self):
        with TemporaryDirectory() as x,TemporaryDirectory() as y:
            r1=example()
            r2=deepcopy(r1)
            r2["diagnostics"][0]["diagnostic"]["residuals"][-1]=10.0
            r2["feedback"]["own_diagnostic_by_candidate"]=r2["diagnostics"]
            r2["decision"]["private_feedback"]=r2["feedback"]
            a=_memory(self.ledger(x),"D","O0",r1,STAMP)
            b=_memory(self.ledger(y),"D","O0",r2,STAMP)
            self.assertNotEqual(a["artifact_sha256"]["diagnostics"],
                                b["artifact_sha256"]["diagnostics"])
            self.assertNotEqual(a["support_node_ids"]["diagnostics"],
                                b["support_node_ids"]["diagnostics"])
            self.assertNotEqual(a["cuts"][1]["projection_hash"],
                                b["cuts"][1]["projection_hash"])
            self.assertEqual(a["cuts"][0]["projection_hash"],
                             b["cuts"][0]["projection_hash"])
            self.assertTrue(a["diagnostic_removal_changes_only_dependent_conclusions"])

    def test_append_only_diagnostic_retraction_removes_only_dependent_support(self):
        with TemporaryDirectory() as tmp:
            ledger=self.ledger(tmp)
            a=_memory(ledger,"D","O0",example(),STAMP)
            _memory(ledger,"M","O1",example("M","O1"),STAMP)
            diag=a["support_node_ids"]["diagnostics"]
            pre=(STAMP+timedelta(microseconds=1)).isoformat()
            later=STAMP+timedelta(seconds=1)
            prior=ledger.snapshot(case_id="E02-D-O0",as_known_at=pre)
            outcome=retract_e02_diagnostic(ledger,"D","O0",diag,later)
            self.assertFalse(outcome["revised_supported"])
            old,_=project(events_from_ledger(prior),as_known_at=pre,
                          lane="D",investigation_id="E02-D-O0")
            self.assertTrue(old.explain("E02-D-O0:RETAINED_AMBIGUITY")["supported"])
            newest=ledger.snapshot(case_id="E02-D-O0",as_known_at=later.isoformat())
            new,_=project(events_from_ledger(newest),as_known_at=later.isoformat(),
                          lane="D",investigation_id="E02-D-O0")
            self.assertFalse(new.explain("E02-D-O0:RETAINED_AMBIGUITY")["supported"])
            self.assertTrue(new.explain(a["support_node_ids"]["source"])["supported"])
            self.assertTrue(new.explain(a["support_node_ids"]["native"])["supported"])
            other=ledger.snapshot(case_id="E02-M-O1",as_known_at=later.isoformat())
            m,_=project(events_from_ledger(other),as_known_at=later.isoformat(),
                        lane="M",investigation_id="E02-M-O1")
            self.assertTrue(m.explain("E02-M-O1:RETAINED_AMBIGUITY")["supported"])
            self.assertEqual(len(prior),len(newest))
            self.assertNotEqual(
                next(x.integrity_hash for x in prior if x.entity_id==diag),
                next(x.integrity_hash for x in newest if x.entity_id==diag))

    def test_unattributed_feedback_or_cross_case_ignored(self):
        with TemporaryDirectory() as tmp:
            ledger=self.ledger(tmp)
            record=example()
            record["feedback"]["own_diagnostic_by_candidate"]=[]
            with self.assertRaisesRegex(ValueError,"E02_FEEDBACK_OR_DECISION_NOT_CAUSED"):
                _memory(ledger,"D","O0",record,STAMP)


if __name__=="__main__":
    unittest.main()
