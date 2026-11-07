"""CT-02 feedback must be retrieved before the *own* policy call, offline."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_v0_contract import digest
from scripts.arena_cafe.ct_feedback_bridge import (
    make_context, record_feedback, recover_feedback, retract_feedback,
    own_m_decision, d_fixed_decision, b_review_envelope, persist_disposition,
)


TIME = datetime(2026, 11, 7, 12, 0, tzinfo=timezone.utc)
SRC = "sha256:" + "a" * 64
CLASSES = {"bounded-queue": {"parameters": {"responseTime": {"min": 0.1, "max": 5.0}}}}


def parent():
    return {"instances": [
        {"id": "p", "role": "preparation", "class_id": "bounded-queue",
         "parameters": {"responseTime": 0.5}},
        {"id": "d", "role": "dispatch", "class_id": "bounded-queue",
         "parameters": {"responseTime": 0.5}},
    ]}


def context(arm="M", condition="C0", world="W1"):
    return make_context(experiment="CT03", world=world, round_id="R0",
                        arm=arm, condition=condition, source_hash=SRC)


def diag(ctx, sha, a=0.2, b=0.3):
    return {"arm": ctx["arm"], "condition": ctx["condition"],
            "source_hash": ctx["source_hash"], "parent_hash": sha,
            "evidence": "G3", "trace_sha256": "sha256:" + "b" * 64,
            "own_evidence_only": True, "no_future_truth": True,
            "observations": [{"time": 2.0, "residual": a},
                             {"time": 4.0, "residual": b}]}


class CT02Test(unittest.TestCase):
    def test_m2_real_policy_receives_supported_feedback_before_deciding(self):
        with TemporaryDirectory() as tmp:
            db = Path(tmp) / "ledger.sqlite"
            ctx, graph = context(), parent()
            record_feedback(db, ctx, parent_hash=digest(graph),
                            diagnostic=diag(ctx, digest(graph)), recorded_at=TIME.isoformat())
            out = own_m_decision(db, ctx, parent_graph=graph,
                                 as_known_at=(TIME + timedelta(seconds=1)).isoformat(),
                                 classes=CLASSES)
            self.assertEqual(out["status"], "REVISED")
            self.assertEqual(len(out["parameter_edits"]), 2)
            self.assertEqual(out["new_model"]["instances"][0]["parameters"]["responseTime"], 1.0)
            self.assertEqual(out["provider_calls"], 0)
            self.assertIn("projection_hash", out["retrieved_before_policy"])

    def test_incompatible_signs_do_not_invent_revision(self):
        with TemporaryDirectory() as tmp:
            db = Path(tmp) / "ledger.sqlite"
            ctx, graph = context(), parent()
            record_feedback(db, ctx, parent_hash=digest(graph),
                            diagnostic=diag(ctx, digest(graph), a=-0.2, b=0.3),
                            recorded_at=TIME.isoformat())
            out = own_m_decision(db, ctx, parent_graph=graph,
                                 as_known_at=(TIME + timedelta(seconds=1)).isoformat(),
                                 classes=CLASSES)
            self.assertEqual(out["status"], "RATIFIED")
            self.assertIsNone(out["new_model"])

    def test_cross_case_parent_and_retraction_are_fail_closed(self):
        with TemporaryDirectory() as tmp:
            db = Path(tmp) / "ledger.sqlite"
            ctx, graph = context(), parent()
            record_feedback(db, ctx, parent_hash=digest(graph),
                            diagnostic=diag(ctx, digest(graph)), recorded_at=TIME.isoformat())
            when = (TIME + timedelta(seconds=1)).isoformat()
            with self.assertRaisesRegex(ValueError, "CT02_NO_CURRENT_FEEDBACK"):
                recover_feedback(db, context(condition="C1"),
                                 parent_hash=digest(graph), as_known_at=when)
            with self.assertRaisesRegex(ValueError, "CT02_NO_CURRENT_FEEDBACK"):
                recover_feedback(db, context(arm="D"),
                                 parent_hash=digest(graph), as_known_at=when)
            with self.assertRaisesRegex(ValueError, "CT02_WITHDRAWN_OR_MISMATCHED_FEEDBACK"):
                recover_feedback(db, ctx, parent_hash="sha256:" + "c" * 64,
                                 as_known_at=when)
            retract_feedback(db, ctx, at=(TIME + timedelta(seconds=2)).isoformat())
            with self.assertRaisesRegex(ValueError, "CT02_WITHDRAWN_OR_MISMATCHED_FEEDBACK"):
                recover_feedback(db, ctx, parent_hash=digest(graph),
                                 as_known_at=(TIME + timedelta(seconds=3)).isoformat())
            old = recover_feedback(db, ctx, parent_hash=digest(graph), as_known_at=when)
            self.assertEqual(old["source"], "LEDGER_ATMS_RETRIEVAL_BEFORE_POLICY")

    def test_d_fixed_and_b_dry_envelope_stay_separate(self):
        with TemporaryDirectory() as tmp:
            db = Path(tmp) / "ledger.sqlite"
            ctx = context(arm="D")
            model_sha = "sha256:" + "d" * 64
            record_feedback(db, ctx, parent_hash=model_sha,
                            diagnostic=diag(ctx, model_sha), recorded_at=TIME.isoformat())
            when = (TIME + timedelta(seconds=1)).isoformat()
            disposition = d_fixed_decision(db, ctx, parent_hash=model_sha, as_known_at=when)
            self.assertEqual(disposition["d2"], "NOT_APPLICABLE_MISSING_RESET_TRIAL")
            self.assertFalse(disposition["model_revision"])
            bctx = context(arm="B")
            self.assertEqual(b_review_envelope(db, bctx, original_native=None,
                             as_known_at=when)["status"], "NOT_EXECUTED_NO_AUTHENTIC_PARENT")


    def test_disposition_supported_only_while_feedback_is_current(self):
        from scripts.ledger import Ledger
        from scripts.arena_atms import project, events_from_ledger
        from scripts.arena_cafe.ct_feedback_bridge import MIGRATION
        with TemporaryDirectory() as tmp:
            db = Path(tmp) / "ledger.sqlite"
            ctx, graph = context(), parent()
            record_feedback(db, ctx, parent_hash=digest(graph),
                            diagnostic=diag(ctx, digest(graph)), recorded_at=TIME.isoformat())
            decision = own_m_decision(db, ctx, parent_graph=graph,
                                     as_known_at=(TIME + timedelta(seconds=1)).isoformat(),
                                     classes=CLASSES)
            cut = (TIME + timedelta(seconds=2)).isoformat()
            saved = persist_disposition(db, ctx, decision=decision, recorded_at=cut)
            self.assertEqual(saved["model_change_count"], 1)
            ledger = Ledger(db, MIGRATION)
            old, _ = project(events_from_ledger(ledger.snapshot(
                case_id=ctx["case_id"], as_known_at=cut)), as_known_at=cut,
                lane="M", investigation_id=ctx["case_id"])
            target = ctx["case_id"] + ":DECISION"
            self.assertTrue(old.explain(target)["supported"])
            retract_feedback(db, ctx, at=(TIME + timedelta(seconds=3)).isoformat())
            later = (TIME + timedelta(seconds=4)).isoformat()
            new, _ = project(events_from_ledger(ledger.snapshot(
                case_id=ctx["case_id"], as_known_at=later)), as_known_at=later,
                lane="M", investigation_id=ctx["case_id"])
            self.assertFalse(new.explain(target)["supported"])
            self.assertTrue(old.explain(target)["supported"])

    def test_b_requires_original_model_shape_and_initial_receipt(self):
        with TemporaryDirectory() as tmp:
            db = Path(tmp) / "ledger.sqlite"
            ctx = context(arm="B")
            payload = {"model": {"variables": [], "relationships": []}}
            self.assertEqual(b_review_envelope(db, ctx, original_native=payload,
                as_known_at=(TIME + timedelta(seconds=1)).isoformat())["status"],
                "NOT_EXECUTED_UNAUTHENTICATED_B_NATIVE_OR_RECEIPT")


    def test_b_native_receipt_to_supported_own_review_packet_no_provider(self):
        from scripts.arena_cafe.e02_b_feedback import _model_sha
        with TemporaryDirectory() as tmp:
            db = Path(tmp) / "ledger.sqlite"
            ctx = context(arm="B")
            original = {"model": {"specs": {"startTime": 0, "stopTime": 8,
                           "dt": .125, "integrationMethod": "Euler"},
                           "variables": [], "relationships": []}}
            parent_sha = _model_sha(original)
            record_feedback(db, ctx, parent_hash=parent_sha,
                            diagnostic=diag(ctx, parent_sha),
                            recorded_at=TIME.isoformat())
            receipt = {"case_id": "CT-03", "world_public_id": "W1",
                "condition_id": "C0", "round_kind": "initial",
                "source_snapshot_hash": SRC, "mode": "live", "provider_calls": 1,
                "proxy_requests": 1, "model_returned": True,
                "result_sha256": parent_sha,
                "status": "ORIGINAL_ENGINE_LIVE_OUTPUT_RETURNED",
                "horizon_matches_case": True, "output_horizon_hours": 8,
                "upstream_source_modified": False,
                "upstream_sha": "5199f7b45f3a7ae4a773cb0dd8542940aabe9edc",
                "transport": "CLOUDFLARE_WORKERS_AI_DIRECT_REST_JSON_SCHEMA"}
            later = (TIME + timedelta(seconds=1)).isoformat()
            result = b_review_envelope(db, ctx, original_native=original,
                                       authenticated_receipt=receipt, as_known_at=later)
            self.assertEqual(result["status"],
                "READY_NOT_SENT_RECEIPT_REQUIRES_EXTERNAL_BYTE_VERIFICATION")
            self.assertIs(result["currentModel"], original["model"])
            self.assertEqual(result["revision_feedback_packet"]["parent_result_sha256"],
                             parent_sha)
            self.assertEqual(result["revision_feedback_packet"]["source_snapshot_hash"], SRC)
            self.assertEqual(result["provider_calls"], 0)
            bad = {**receipt, "world_public_id": "W2"}
            self.assertEqual(b_review_envelope(db, ctx, original_native=original,
                      authenticated_receipt=bad, as_known_at=later)["status"],
                      "NOT_EXECUTED_UNAUTHENTICATED_B_NATIVE_OR_RECEIPT")
            altered = {"model": {**original["model"], "specs": {"stopTime": 6}}}
            self.assertEqual(b_review_envelope(db, ctx, original_native=altered,
                      authenticated_receipt=receipt, as_known_at=later)["status"],
                      "NOT_EXECUTED_UNAUTHENTICATED_B_NATIVE_OR_RECEIPT")


if __name__ == "__main__":
    unittest.main()
