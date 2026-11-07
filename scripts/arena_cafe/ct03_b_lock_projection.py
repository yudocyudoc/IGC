"""CT-03: project the ORIGINAL Buffalo provider+physical lifecycle into slot 13.

No solver, provider, private world or prediction fabrication. A live original
native can be G1/observable-blocked, physically predicted or an explicitly
documented no-native failure. A B review is an actual second Engine.generate
(currentModel) response with own-feedback binding; an unchanged native is
RATIFIED, a changed native requires separately checked revised G1/OMC output.
No revision attempt is never silently called RATIFIED.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from scripts.arena_v0_contract import canonical,digest
from scripts.arena_cafe.ct03_b_own_feedback import validate as validate_initial
from scripts.arena_cafe.ct03_b_physical_prepare import (
    SCHEMA as PLAN_SCHEMA, validate_revision_live
)
from scripts.arena_cafe.ct03_b_physical_result import (
    SCHEMA as PHYSICAL_SCHEMA,CUMULATIVE_MONOTONIC_EPS_ITEMS
)
from scripts.arena_cafe.ct03_b_physical_outcome import (
    SCHEMA as FAILURE_SCHEMA,STATUS as FAILURE_STATUS,G2_CHECK_FAILURES
)
from scripts.arena_cafe.ct03_prospective_lock import validate_row,sha
from scripts.arena_cafe.e02_b_feedback import _model_sha
from scripts.arena_cafe.ct_feedback_bridge import require

SCHEMA="igc-ct03-b-own-original-thirteenth-lock-row/1.0"
STOP_REASONS=frozenset({
    "B_ORIGINAL_NATIVE_G1_OR_OBSERVABLE_BLOCKED_STOP",
    "B_PROVIDER_REVISION_NOT_AVAILABLE_STOP",
    "B_BATCH_STOP_RULE_OR_BUDGET_EXHAUSTED",
})

def _state(native_sha,plan,physical,receipt):
    require(type(plan) is dict and plan.get("schema")==PLAN_SCHEMA and
            plan.get("native_result_sha256")==native_sha and
            plan.get("native_result_bytes_bound") is True and
            plan.get("reserved_truth_read") is False and
            plan.get("model_repair_performed") is False,
            "CT03_B_LOCK_ORIGINAL_PHYSICAL_PLAN_MISMATCH")
    status=plan["status"]
    if status in ("B_NATIVE_G1_TRANSLATION_BLOCKED_NO_OMC",
                  "B_OBSERVABLE_UNRESOLVED_NO_OMC"):
        require(physical is None and plan["observation_operator"] is None and
                plan["blocked_reason"] and plan["script_sha256"] is None,
                "CT03_B_LOCK_BLOCKED_NATIVE_MUST_NOT_HAVE_SOLVER")
        return {
            "status":"G1_BLOCKED","native_sha256":native_sha,
            "trace_sha256":None,
            "receipt_sha256":digest({
                "native_provider_receipt":digest(receipt),
                "original_G1_or_observable_plan":digest(plan)
            }),"forecast":None
        }
    # A consumed physical attempt may fail after the original native was
    # returned. Preserve its own attempted-run receipt; no trace or forecast.
    if type(physical) is dict and physical.get("status")==FAILURE_STATUS:
        require(status=="B_NATIVE_PHYSICAL_PLANNED_NO_OMC" and
                physical.get("schema")==FAILURE_SCHEMA and
                physical.get("world_public_id")==plan["world_public_id"] and
                physical.get("source_snapshot_hash")==plan["source_snapshot_hash"] and
                physical.get("round_kind")==plan["round_kind"] and
                physical.get("parent_native_sha256")==native_sha and
                physical.get("native_modelica_sha256")==
                    plan["translated_modelica_sha256"] and
                physical.get("script_sha256")==plan["script_sha256"] and
                physical.get("observation_operator")==plan["observation_operator"] and
                sha(physical.get("attempt_record_sha256")) and
                sha(physical.get("solver_log_sha256")) and
                (physical.get("csv_sha256") is None or
                 sha(physical["csv_sha256"])) and
                type(physical.get("github_code_sha")) is str and
                len(physical["github_code_sha"])==40 and
                all(c in "0123456789abcdef" for c in
                    physical["github_code_sha"]) and
                type(physical.get("github_run_id")) is str and
                physical["github_run_id"].isdigit() and
                physical.get("attempted") is True and
                physical.get("forecast") is None and
                physical.get("reserved_truth_read") is False and
                physical.get("independent_solver_execution_proven") is False and
                physical.get("no_provider_or_solver_call_by_collector") is True and
                type(physical.get("omc_exit_code")) is int and
                0<=physical["omc_exit_code"]<=255 and
                ((physical["omc_exit_code"]>0 and
                  physical.get("failure_class")=="OMC_EXIT_NONZERO" and
                  physical.get("failure_reason")==
                    "OMC_EXIT_NONZERO:"+str(physical["omc_exit_code"])) or
                 (physical["omc_exit_code"]==0 and
                  physical.get("failure_class")=="G2_PHYSICAL_CHECK_FAILED" and
                  physical.get("failure_reason") in G2_CHECK_FAILURES)),
                "CT03_B_LOCK_FAILED_PHYSICAL_ATTEMPT_RECEIPT_MISMATCH")
        return {
            "status":"G2_FAILED","native_sha256":native_sha,
            "trace_sha256":None,
            "receipt_sha256":digest({
                "native_provider_receipt":digest(receipt),
                "original_solver_failed_attempt":digest(physical)
            }),"forecast":None
        }
    require(status=="B_NATIVE_PHYSICAL_PLANNED_NO_OMC" and
            type(physical) is dict and
            physical.get("schema")==PHYSICAL_SCHEMA and
            physical.get("status")==
                "B_ORIGINAL_NATIVE_PHYSICAL_CSV_CONFORMING_NOT_HELDOUT" and
            physical.get("parent_native_sha256")==native_sha and
            physical.get("world_public_id")==plan["world_public_id"] and
            physical.get("source_snapshot_hash")==plan["source_snapshot_hash"] and
            physical.get("native_modelica_sha256")==
                plan["translated_modelica_sha256"] and
            physical.get("script_sha256")==plan["script_sha256"] and
            physical.get("observation_operator")==plan["observation_operator"] and
            physical.get("cumulative_monotonicity_tolerance_items")==
                CUMULATIVE_MONOTONIC_EPS_ITEMS and
            physical.get("reserved_truth_read") is False and
            sha(physical.get("csv_sha256")) and
            sha(physical.get("solver_log_sha256")) and
            type(physical.get("forecast")) is list,
            "CT03_B_LOCK_NATIVE_PHYSICAL_CSV_NOT_CONFORMING")
    return {
        "status":"PREDICTED","native_sha256":native_sha,
        "trace_sha256":physical["csv_sha256"],
        "receipt_sha256":digest({
            "native_provider_receipt":digest(receipt),
            "original_solver_report":digest(physical)
        }),
        "forecast":physical["forecast"]
    }


def _validate_feedback(initial_receipt,construction,b_feedback,packet):
    require(type(b_feedback) is dict and
            b_feedback.get("schema")==
              "igc-ct03-b-original-own-g1-ledger-and-revision-packet/1.0" and
            b_feedback.get("world_public_id")==construction["world_public_id"] and
            b_feedback.get("source_snapshot_hash")==
                construction["source_snapshot_hash"] and
            b_feedback.get("parent_native_sha256")==initial_receipt["result_sha256"] and
            type(packet) is dict and
            packet.get("schema")=="igc-ct03-b-own-feedback/1.0" and
            packet.get("parent_result_sha256")==initial_receipt["result_sha256"] and
            packet.get("world_public_id")==construction["world_public_id"] and
            packet.get("source_snapshot_hash")==construction["source_snapshot_hash"] and
            packet.get("own_diagnostic_sha256")==b_feedback["own_diagnostic_sha256"] and
            packet.get("retrieved_before_policy")==b_feedback["retrieved_before_policy"] and
            b_feedback["revision_packet_sha256"]==digest(packet) and
            packet.get("own_diagnostic_sha256")==digest(packet.get("own_diagnostic")) and
            sha(b_feedback["own_diagnostic_sha256"]),
            "CT03_B_LOCK_OWN_FEEDBACK_OR_PACKET_MISMATCH")


def project(*,original_native,initial_receipt,construction,b_feedback,packet,
            initial_plan,initial_physical=None,
            revision_native=None,revision_receipt=None,revision_plan=None,
            revision_physical=None,stop_reason=None,
            review_feedback=None,review_packet=None):
    validate_initial(original_native,initial_receipt,construction)
    _validate_feedback(initial_receipt,construction,b_feedback,packet)
    require((review_feedback is None)==(review_packet is None),
            "CT03_B_LOCK_REVIEW_FEEDBACK_MUST_BE_COMPLETE")
    revised_feedback=b_feedback if review_feedback is None else review_feedback
    revised_packet=packet if review_packet is None else review_packet
    if review_feedback is not None:
        _validate_feedback(initial_receipt,construction,revised_feedback,revised_packet)
        require(type(initial_physical) is dict and
                revised_feedback.get("physical_B_G2_or_G3") in ("G2","G3") and
                revised_feedback.get("physical_outcome_sha256")==
                    digest(initial_physical) and
                revised_feedback.get("previous_G1_diagnostic_sha256")==
                    b_feedback["own_diagnostic_sha256"] and
                revised_feedback.get("G1_status")==b_feedback.get("G1_status") and
                revised_feedback.get("parent_native_sha256")==
                    initial_receipt["result_sha256"],
                "CT03_B_LOCK_PHYSICAL_FEEDBACK_NOT_OWN_INITIAL_ATTEMPT")
    origin=initial_receipt["result_sha256"]
    require(sha(origin) and _model_sha(original_native)==origin,
            "CT03_B_LOCK_OWN_ORIGINAL_PARENT_MISMATCH")
    initial=_state(origin,initial_plan,initial_physical,initial_receipt)
    require(initial_plan["world_public_id"]==construction["world_public_id"] and
            initial_plan["source_snapshot_hash"]==
                construction["source_snapshot_hash"] and
            initial_plan["round_kind"]=="initial" and
            initial_plan["original_G1_feedback_sha256"]==digest(b_feedback),
            "CT03_B_LOCK_INITIAL_PLAN_NOT_OWN_CASE")
    rev_inputs=(revision_native,revision_receipt,revision_plan)
    if all(x is None for x in rev_inputs):
        require(revision_physical is None and stop_reason in STOP_REASONS,
                "CT03_B_LOCK_REVIEW_MISSING_NEEDS_EXPLICIT_STOP_REASON")
        status="NOT_EXECUTED"
        final=initial
        new_model=None
        feedback_sha=None
        item_id=None
        reason="NO_SECOND_PROVIDER_POST:"+stop_reason
    else:
        require(all(x is not None for x in rev_inputs) and
                stop_reason is None,
                "CT03_B_LOCK_PARTIAL_REVISION_NOT_ALLOWED")
        validate_revision_live(
            revision_native,revision_receipt,construction,revised_feedback,
            {"parent_native":original_native,
             "parent_receipt":initial_receipt,"packet":revised_packet})
        revised=revision_receipt["result_sha256"]
        require(revision_plan["round_kind"]=="revision" and
                revision_plan["revision_parent_native_sha256"]==origin and
                revision_plan["original_G1_feedback_sha256"]==
                    digest(revised_feedback),
                "CT03_B_LOCK_REVISED_NATIVE_NOT_OWN_CURRENT_MODEL")
        if revised==origin:
            # The second Buffalo provider call returned the SAME native.
            # No second physical attempt is necessary or permitted; preserve
            # original consequence, after confirming the same observable and
            # original Modelica hash (the script path itself may differ).
            require(revision_physical is None and
                    revision_plan["status"]==initial_plan["status"] and
                    revision_plan["observation_operator"]==
                        initial_plan["observation_operator"] and
                    revision_plan["translated_modelica_sha256"]==
                        initial_plan["translated_modelica_sha256"],
                    "CT03_B_LOCK_UNCHANGED_NATIVE_CANNOT_CONSUME_NEW_OMC")
            status="RATIFIED"
            final=initial
            new_model=None
            reason="NATIVE_UNCHANGED_AFTER_REAL_CURRENTMODEL_REVIEW"
        else:
            final=_state(revised,revision_plan,
                          revision_physical,revision_receipt)
            status="REVISED"
            new_model=revised
            reason="NATIVE_CHANGED_AFTER_REAL_CURRENTMODEL_REVIEW"
        feedback_sha=revised_feedback["own_diagnostic_sha256"]
        item_id=revised_feedback["retrieved_before_policy"]["item_id"]
    row={
        "arm":"B","candidate_id":"B-original","parent_hash":origin,
        "material_group":"B-original","initial":initial,
        "decision":{
            "status":status,"policy":"UB-IAD/sd-ai::Engine.generate",
            "feedback_hash":feedback_sha,
            "retrieved_item_id":item_id,
            "new_model_sha256":new_model
        },
        "final":final
    }
    expected={("B","B-original"):{"parent_hash":None,"group":"B-original"}}
    validate_row(row,expected,construction["world_public_id"])
    return {
        "schema":SCHEMA,"status":"B_THIRTEENTH_SLOT_VALID_NOT_ARCHIVED_OR_SCORED",
        "world_public_id":construction["world_public_id"],
        "source_snapshot_hash":construction["source_snapshot_hash"],
        "original_provider_receipt_sha256":digest(initial_receipt),
        "own_feedback_report_sha256":digest(b_feedback),
        "own_revision_packet_sha256":digest(packet),
        "second_B_provider_post_observed":revision_receipt is not None,
        "revision_stop_or_disposition":reason,
        "initial_native_G1_or_observable_status":initial_plan["status"],
        "final_native_G1_or_observable_status":(
            revision_plan["status"] if revision_plan is not None else None),
        "reserved_truth_read":False,
        "new_omc_by_projection":0,"new_provider_calls":0,
        "actual_provider_or_solver_source_verified_outside_process":False,
        "row":row
    }


def project_no_native(initial_receipt,construction):
    """A failed provider attempt still occupies B's thirteenth denominator slot.

    Requires a real native-runner failure receipt; no fabricated B parent,
    feedback, revision, zero prediction or fake provider/model success.
    """
    world=construction["world_public_id"]
    source=construction["source_snapshot_hash"]
    require(type(initial_receipt) is dict and
            initial_receipt.get("case_id")=="CT-03" and
            initial_receipt.get("world_public_id")==world and
            initial_receipt.get("condition_id")=="C0" and
            initial_receipt.get("source_snapshot_hash")==source and
            initial_receipt.get("round_kind")=="initial" and
            initial_receipt.get("mode")=="live" and
            initial_receipt.get("model_returned") is False and
            initial_receipt.get("status") in (
                "CT03_PROVIDER_ATTEMPT_NO_NATIVE",
                "CT03_PREPROVIDER_NO_NATIVE",
                "ORIGINAL_ENGINE_NO_NATIVE_MODEL",
                "RUNNER_FAILURE"
            ) and
            initial_receipt.get("upstream_source_modified") is False and
            initial_receipt.get("upstream_sha")==
              "5199f7b45f3a7ae4a773cb0dd8542940aabe9edc" and
            initial_receipt.get("transport")==
              "CLOUDFLARE_WORKERS_AI_DIRECT_REST_JSON_SCHEMA" and
            type(initial_receipt.get("provider_calls")) is int and
            initial_receipt["provider_calls"] in (0,1),
            "CT03_B_NO_NATIVE_NEEDS_REAL_ORIGINAL_FAILURE_RECEIPT")
    state={
        "status":"NO_NATIVE","native_sha256":None,
        "trace_sha256":None,
        "receipt_sha256":digest(initial_receipt),
        "forecast":None
    }
    row={
        "arm":"B","candidate_id":"B-original",
        "parent_hash":None,"material_group":"B-original",
        "initial":state,
        "decision":{
            "status":"NOT_EXECUTED",
            "policy":"UB-IAD/sd-ai::Engine.generate",
            "feedback_hash":None,
            "retrieved_item_id":None,
            "new_model_sha256":None
        },
        "final":state
    }
    validate_row(row,{("B","B-original"):
                    {"parent_hash":None,"group":"B-original"}},world)
    return {
        "schema":SCHEMA,"status":"B_THIRTEENTH_SLOT_VALID_NOT_ARCHIVED_OR_SCORED",
        "world_public_id":world,"source_snapshot_hash":source,
        "original_provider_receipt_sha256":digest(initial_receipt),
        "own_feedback_report_sha256":None,"own_revision_packet_sha256":None,
        "second_B_provider_post_observed":False,
        "revision_stop_or_disposition":"NO_AUTHENTIC_ORIGINAL_B_NATIVE",
        "initial_native_G1_or_observable_status":"NO_NATIVE",
        "final_native_G1_or_observable_status":None,
        "reserved_truth_read":False,
        "new_omc_by_projection":0,"new_provider_calls":0,
        "actual_provider_or_solver_source_verified_outside_process":False,
        "row":row
    }


def main():
    p=argparse.ArgumentParser()
    for flag in ("initial-receipt","construction","out"):
        p.add_argument("--"+flag,required=True,type=Path)
    for flag in ("original-native","b-feedback","packet","initial-plan"):
        p.add_argument("--"+flag,type=Path)
    for flag in ("initial-physical","revision-native","revision-receipt",
                 "revision-plan","revision-physical"):
        p.add_argument("--"+flag,type=Path)
    p.add_argument("--stop-reason",choices=sorted(STOP_REASONS))
    p.add_argument("--review-feedback",type=Path)
    p.add_argument("--review-packet",type=Path)
    a=p.parse_args()
    require(not a.out.exists(),"CT03_B_LOCK_REFUSE_OVERWRITE")
    def read(path):return json.loads(path.read_text(encoding="utf-8")) if path else None
    if a.original_native is None:
        require(all(x is None for x in (
            a.b_feedback,a.packet,a.initial_plan,a.initial_physical,
            a.revision_native,a.revision_receipt,a.revision_plan,
            a.revision_physical,a.stop_reason,
            a.review_feedback,a.review_packet)),
            "CT03_B_NO_NATIVE_CANNOT_INVENT_REVISION_OR_PHYSICAL")
        result=project_no_native(read(a.initial_receipt),read(a.construction))
    else:
        require(a.b_feedback and a.packet and a.initial_plan,
                "CT03_B_NATIVE_MUST_HAVE_OWN_FEEDBACK_AND_G1_PLAN")
        result=project(
            original_native=read(a.original_native),
            initial_receipt=read(a.initial_receipt),
            construction=read(a.construction),
            b_feedback=read(a.b_feedback),packet=read(a.packet),
            initial_plan=read(a.initial_plan),
            initial_physical=read(a.initial_physical),
            revision_native=read(a.revision_native),
            revision_receipt=read(a.revision_receipt),
            revision_plan=read(a.revision_plan),
            revision_physical=read(a.revision_physical),stop_reason=a.stop_reason,
            review_feedback=read(a.review_feedback),
            review_packet=read(a.review_packet))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_bytes(canonical(result)+b"\n")
    print(json.dumps({"status":result["status"],"B":1,
                      "archived":False,"new_omc":0,"provider":0}))

if __name__=="__main__":
    main()
