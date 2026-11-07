"""F172-10/11 regression: B provider attempts and native G0 horizon.

Fixtures are synthetic; these tests do NOT invoke Buffalo, OpenModelica
or a future-truth custodian. Preserve every B candidate in the 13 slots.
"""
from __future__ import annotations
import copy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_v0_contract import digest
from scripts.arena_cafe.e02_b_feedback import _model_sha
from scripts.arena_cafe.ct03_b_lock_projection import (
    project, project_invalid_horizon_initial
)
from scripts.arena_cafe.ct03_assemble_entries import assemble
from scripts.arena_cafe.ct03_prospective_lock import validate_row,seal
from test_arena_ct03_b_own_feedback import public,fixture as b_fixture
from test_arena_ct03_b_lock_projection import prepare_fixture,review_receipt
from test_arena_ct03_assemble_entries import fixture as dm_fixture
from test_arena_ct03_producer_freeze_handoff import commitment

def invalid(native,receipt,round_kind="initial",packet=None):
    model=copy.deepcopy(native)
    model["model"]["specs"]["stopTime"]=10
    r={**receipt,
       "round_kind":round_kind,
       "model_returned":True,
       "provider_calls":1,
       "proxy_requests":1,
       "status":"CT03_NATIVE_HORIZON_MISMATCH",
       "horizon_matches_case":False,
       "output_horizon_hours":10,
       "result_sha256":_model_sha(model)}
    if round_kind=="revision":
        r["parent_native_sha256"]=receipt["result_sha256"]
        r["own_feedback_sha256"]=digest(packet)
    return model,r

def failed_review(receipt,packet,posts):
    return {
        **receipt,
        "round_kind":"revision",
        "status":("CT03_PROVIDER_ATTEMPT_NO_NATIVE"
                  if posts else "CT03_PREPROVIDER_NO_NATIVE"),
        "model_returned":False,
        "native_model_available":False,
        "provider_calls":posts,
        "proxy_requests":posts,
        "provider_calls_attempted":posts,
        "parent_native_sha256":receipt["result_sha256"],
        "own_feedback_sha256":digest(packet),
        "result_sha256":None
    }

class BuffaloFailedRunnerLifecycleTests(unittest.TestCase):
    def _original(self,root):
        native,receipt,plan,feedback,packet,physical=prepare_fixture(root)
        return (native,receipt,plan,feedback,packet,physical)

    def test_second_post_consumed_without_native_is_retained_not_falsely_unattempted(self):
        with TemporaryDirectory(dir=".") as tmp:
            root=Path(tmp).relative_to(Path.cwd())
            native,receipt,plan,g1,packet,physical=self._original(root)
            second=failed_review(receipt,packet,1)
            r=project(original_native=native,initial_receipt=receipt,
                      construction=public(),b_feedback=g1,packet=packet,
                      initial_plan=plan,initial_physical=physical,
                      revision_receipt=second)
            self.assertTrue(r["second_B_provider_post_observed"])
            self.assertEqual(r["second_B_provider_receipt_sha256"],digest(second))
            self.assertIn("SECOND_PROVIDER_POST_NO_NATIVE",r["revision_stop_or_disposition"])
            self.assertEqual(r["row"]["decision"]["status"],"NOT_EXECUTED")
            self.assertEqual(r["row"]["initial"],r["row"]["final"])
            self.assertIsNone(r["row"]["decision"]["new_model_sha256"])
            self.assertEqual(r["row"]["initial"]["status"],"PREDICTED")

    def test_preprovider_failure_is_zero_provider_posts_but_keeps_second_receipt(self):
        with TemporaryDirectory(dir=".") as tmp:
            root=Path(tmp).relative_to(Path.cwd())
            native,receipt,plan,g1,packet,physical=self._original(root)
            second=failed_review(receipt,packet,0)
            r=project(original_native=native,initial_receipt=receipt,
                      construction=public(),b_feedback=g1,packet=packet,
                      initial_plan=plan,initial_physical=physical,
                      revision_receipt=second)
            self.assertFalse(r["second_B_provider_post_observed"])
            self.assertEqual(r["second_B_provider_receipt_sha256"],digest(second))
            self.assertIn("BEFORE_PROVIDER_POST",r["revision_stop_or_disposition"])
            self.assertEqual(r["row"]["final"],r["row"]["initial"])

    def test_initial_wrong_horizon_is_g0_native_not_no_native_and_all_13_survive(self):
        native,receipt=b_fixture()
        native,receipt=invalid(native,receipt)
        result=project_invalid_horizon_initial(native,receipt,public())
        state=result["row"]["initial"]
        self.assertEqual(state["status"],"G0_REJECTED")
        self.assertEqual(state["native_sha256"],receipt["result_sha256"])
        self.assertEqual(state["receipt_sha256"],digest(receipt))
        self.assertIsNone(state["forecast"])
        self.assertEqual(state,result["row"]["final"])
        self.assertFalse(result["second_B_provider_post_observed"])
        self.assertEqual(result["row"]["decision"]["status"],"NOT_EXECUTED")
        with TemporaryDirectory(dir=".") as tmp:
            dm,b,d,m=dm_fixture(Path(tmp).relative_to(Path.cwd()))
            entries=assemble(dm,result,public(),d,m)
            self.assertEqual(len(entries["rows"]),13)
            self.assertEqual(seal(public(),commitment(),d,m,entries)["candidate_count"],13)

    def test_revised_wrong_horizon_keeps_initial_and_revision_native_failed(self):
        with TemporaryDirectory(dir=".") as tmp:
            root=Path(tmp).relative_to(Path.cwd())
            native,receipt,plan,g1,packet,physical=self._original(root)
            revised,second=invalid(native,receipt,"revision",packet)
            r=project(original_native=native,initial_receipt=receipt,
                      construction=public(),b_feedback=g1,packet=packet,
                      initial_plan=plan,initial_physical=physical,
                      revision_native=revised,revision_receipt=second)
            self.assertEqual(r["row"]["initial"]["status"],"PREDICTED")
            self.assertEqual(r["row"]["final"]["status"],"G0_REJECTED")
            self.assertEqual(r["row"]["final"]["native_sha256"],second["result_sha256"])
            self.assertIsNone(r["row"]["final"]["forecast"])
            self.assertEqual(r["row"]["decision"]["status"],"REVISED")
            self.assertTrue(r["second_B_provider_post_observed"])
            self.assertEqual(r["second_B_provider_receipt_sha256"],digest(second))
            self.assertEqual(r["row"]["decision"]["feedback_hash"],g1["own_diagnostic_sha256"])
            (root/"dm").mkdir()
            dm,b,d,m=dm_fixture(root/"dm")
            entries=assemble(dm,r,public(),d,m)
            self.assertEqual(len(entries["rows"]),13)
            self.assertEqual(seal(public(),commitment(),d,m,entries)["candidate_count"],13)

    def test_wrong_parent_source_or_status_still_stops_both_failed_paths(self):
        with TemporaryDirectory(dir=".") as tmp:
            root=Path(tmp).relative_to(Path.cwd())
            native,receipt,plan,g1,packet,physical=self._original(root)
            args=dict(original_native=native,initial_receipt=receipt,
                      construction=public(),b_feedback=g1,packet=packet,
                      initial_plan=plan,initial_physical=physical)
            failed=failed_review(receipt,packet,1)
            for key,value in (
                ("world_public_id","OTHER_WORLD"),
                ("parent_native_sha256","sha256:"+"f"*64),
                ("own_feedback_sha256","sha256:"+"f"*64),
                ("upstream_source_modified",True),
                ("status","ORIGINAL_ENGINE_LIVE_OUTPUT_RETURNED")):
                with self.assertRaises(ValueError):
                    project(**args,revision_receipt={**failed,key:value})
            model,bad=invalid(native,receipt,"revision",packet)
            for key,value in (
                ("world_public_id","OTHER_WORLD"),
                ("parent_native_sha256","sha256:"+"e"*64),
                ("result_sha256","sha256:"+"e"*64),
                ("output_horizon_hours",8),
                ("provider_calls",0)):
                with self.assertRaises(ValueError):
                    project(**args,revision_native=model,
                            revision_receipt={**bad,key:value})
            model,initial=invalid(native,receipt)
            for key,value in (
                ("result_sha256","sha256:"+"f"*64),
                ("horizon_matches_case",True),
                ("world_public_id","OTHER_WORLD")):
                with self.assertRaises(ValueError):
                    project_invalid_horizon_initial(
                        model,{**initial,key:value},public())

if __name__=="__main__":
    unittest.main()
