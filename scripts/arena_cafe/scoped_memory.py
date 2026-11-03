"""F1: real append-only Arena ledger + ATMS for exactly one authorized A1 lineage.

This is application-level, trusted-controller scoping, not an OS ACL and NOT a
new ledger/ATMS engine. Caller must provide a single validated visible input.
Only metadata, hashes, native results and declared assumptions are recorded.
Other scopes are never fetched before ATMS projection or memory retrieval.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re

from scripts.arena_cafe.native_handoff import need, validate_a1_visible
from scripts.arena_v0_contract import canonical, digest
from scripts.ledger import Ledger
from scripts.arena_atms import events_from_ledger, project
from scripts.arena_memory import load_events_from_ledger, retrieve

SCHEMA = "igc-arena-cafe-a1-ledger-scope/0.1"
ARMS = ("D", "B", "M")
ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "migrations/0001_ledger.sql"
ENTITIES = ("evidence", "assumption", "support", "knowledge")
STATES = {
    "worker": {
        "D": {"BLOCKED_ORIGINAL_D_CONTRACT"},
        "B": {"ORIGINAL_ENGINE_OFFLINE_MOCK"},
        "M": {"ORIGINAL_E1_ENUMERATOR_ENGINEERING_ONLY"},
    },
    "native": {
        "D": {"NATIVE_G2_MATERIAL_BALANCE_PASS_ENGINEERING_ONLY"},
        "M": {"NATIVE_G2_MATERIAL_BALANCE_PASS_ENGINEERING_ONLY"},
    },
}


def scope(visible, arm, condition, run_kind):
    validate_a1_visible(visible, condition)
    need(arm in ARMS and condition in ("O0", "O1"),
         "A1_MEMORY_WRONG_ARM_CONDITION")
    need(run_kind in STATES and arm in STATES[run_kind],
         "A1_MEMORY_UNSUPPORTED_RUN_KIND")
    world = visible["observability"]["world_public_id"]
    need(re.fullmatch(r"[A-Za-z0-9_-]{1,80}", world) is not None,
         "A1_MEMORY_WORLD_INVALID")
    # Fixed experiment/replica/iteration are deliberate for known control A1.
    # The native engineering run and legacy worker have separate case IDs.
    case = f"a1-{world}-r0-{arm}-{condition}-i0-{run_kind}"
    return {"experiment_id":"cafe-a1", "world_public_id":world,
            "replica_id":"r0","arm_id":arm,"condition_id":condition,
            "iteration_id":"i0","run_kind":run_kind,"case_id":case,
            "source_snapshot_hash":visible["source_snapshot_hash"],
            "visible_input_hash":digest(visible)}


def _verify_receipt(visible, context, receipt, manifest=None, hj=None):
    arm=context["arm_id"]; condition=context["condition_id"]
    run_kind=context["run_kind"]
    status=receipt.get("status")
    need(status in STATES[run_kind][arm],
         "A1_MEMORY_STATUS_NOT_ORIGINAL_METHOD")
    if run_kind=="worker":
        need(receipt.get("arm")==arm and receipt.get("condition")==condition
             and receipt.get("visible_input_hash")==context["visible_input_hash"]
             and receipt.get("source_snapshot_hash")==context["source_snapshot_hash"]
             and receipt.get("scientific_use_proven") is False
             and receipt.get("provider_calls")==0,
             "A1_MEMORY_WORKER_SOURCE_OR_SCOPE_MISMATCH")
        need(manifest is None and hj is None,
             "A1_MEMORY_WORKER_UNEXPECTED_MODEL")
    else:
        need(receipt.get("arm_id")==arm and
             receipt.get("condition_id")==condition and
             receipt.get("nominal_parameters_are_assumptions") is True,
             "A1_MEMORY_NATIVE_RECEIPT_MISMATCH")
        need(type(manifest) is dict and
             manifest.get("arm_id")==arm and
             manifest.get("condition_id")==condition and
             manifest.get("input_hash")==context["visible_input_hash"] and
             manifest.get("source_snapshot_hash")==context["source_snapshot_hash"] and
             manifest.get("candidate") is not None and
             manifest.get("scientific_inference")=="NOT_ESTABLISHED",
             "A1_MEMORY_NATIVE_MANIFEST_MISMATCH")
        need(type(hj) is dict and hj.get("arm_id")==arm
             and hj.get("condition_id")==condition
             and hj.get("visible_input_hash")==context["visible_input_hash"]
             and hj.get("status")=="DESCRIPTIVE_HJ_PROBE_ONLY_UNVERIFIED_TRACE"
             and hj.get("scientific_status")=="NOT_ESTABLISHED",
             "A1_MEMORY_HJ_SCOPE_OR_CLAIM_MISMATCH")
        # The g2 receipt itself must refer to the candidate preserved in the
        # native manifest. Do not read any external candidate directories.
        need(receipt.get("candidate_full_hash")==digest(manifest["candidate"]),
             "A1_MEMORY_CANDIDATE_CROSS_LINK_MISMATCH")
    return status


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def record(db, visible, arm, condition, run_kind, receipt, *,
           manifest=None, hj=None, timestamp=None):
    context=scope(visible,arm,condition,run_kind)
    status=_verify_receipt(visible,context,receipt,manifest,hj)
    time=timestamp or _now()
    ledger=Ledger(db,MIGRATION)
    case=context["case_id"]
    policy="lane:"+arm
    prefix=case+":"
    # A record is a logical fact about artifacts, NOT scientific evidence that
    # the model/assumption is true.
    source_node=prefix+"source"
    assumption_node=prefix+"nominal-or-runtime-assumption"
    outcome_node=prefix+"reported-outcome"
    data={
        "evidence":{
            "kind":"fact","active":True,"scope_hash":digest(context),
            "source_snapshot_hash":context["source_snapshot_hash"],
            "visible_input_hash":context["visible_input_hash"],
            "cutoff_minutes_exact":visible["observability"]["cutoff_minutes_exact"],
            "source_origin":"SYNTHETIC_KNOWN_CONTROL_NOT_REAL_POS"},
        "assumption":{
            "kind":"assumption","active":True,
            "assumption_type":("NOMINAL_UNFITTED_D_OR_E1_PARAMETERS"
                               if run_kind=="native" else "LEGACY_WORKER_OR_OFFLINE_MOCK"),
            "truth_status":"NOT_DETERMINED"},
        "support":{
            "kind":"justification","active":True,
            "antecedents":[source_node,assumption_node],
            "consequent":outcome_node,
            "source_id":source_node,
            "interpretation":"TRACE_DEPENDENCY_NOT_EMPIRICAL_VERIFICATION"},
        "knowledge":{
            "kind":"knowledge","active":True,
            "node_id":outcome_node,"source_id":source_node,
            "title":"A1 scoped native outcome "+status,
            "text":"Synthetic cafe observed POS, scoped original-method receipt "+status,
            "item_type":"ENGINEERING_OUTCOME","epistemic_status":"NOT_EMPIRICALLY_VERIFIED",
            "source_revision":1,
        },
    }
    entity_names={
        "evidence":source_node,
        "assumption":assumption_node,
        "support":prefix+"support-rule",
        "knowledge":prefix+"knowledge",
    }
    # The originally provided receipt is retained only by hash, never copied
    # into the ATMS as a fact about physical truth.
    refs={"receipt_sha256":digest(receipt),
          "manifest_sha256":digest(manifest) if manifest is not None else None,
          "hj_sha256":digest(hj) if hj is not None else None}
    for kind in ENTITIES:
        payload={"schema":SCHEMA,"scope":context,"refs":refs,**data[kind]}
        ledger.append_revision(
            entity_id=entity_names[kind],
            entity_type="KnowledgeItem" if kind=="knowledge" else "ATMSNode",
            case_id=case,actor_id="arena-a1-trusted-runner",
            idempotency_key=entity_names[kind]+":first",
            payload=payload,recorded_at=time,created_at=time,
            access_policy=policy)
    return inspect(db,visible,arm,condition,run_kind,at=time)


def inspect(db,visible,arm,condition,run_kind,*,at=None):
    context=scope(visible,arm,condition,run_kind)
    time=at or _now()
    case=context["case_id"]
    ledger=Ledger(db,MIGRATION)
    # Critical boundary: exact case_id is passed to SQL snapshot, BEFORE
    # events_from_ledger, ATMS propagation, retrieval/FTS, or prompting.
    revisions=ledger.snapshot(case_id=case,as_known_at=time)
    need(len(revisions)==len(ENTITIES),
         "A1_MEMORY_MISSING_OR_UNAUTHORIZED_SCOPE")
    need(all(r.case_id==case and r.access_policy=="lane:"+arm
             and r.payload.get("scope")==context
             and ledger.verify_integrity(entity_id=r.entity_id,revision=r.revision)
             for r in revisions),
         "A1_MEMORY_SCOPE_OR_INTEGRITY_VIOLATION")
    atms_events=events_from_ledger(revisions)
    engine,atms=project(atms_events,as_known_at=time,
                        investigation_id=case,lane=arm)
    assumption=case+":nominal-or-runtime-assumption"
    outcome=case+":reported-outcome"
    need(engine.supported_in(outcome,[assumption]),
         "A1_MEMORY_ATMS_OUTCOME_NOT_SUPPORTED")
    knowledge,known_atms=load_events_from_ledger(Path(db),case,time)
    need(known_atms==atms_events,"A1_MEMORY_LEDGER_ATMS_DRIFT")
    lookup=retrieve(investigation_id=case,lane=arm,as_known_at=time,
                    query="outcome scoped synthetic cafe",top_k=5,
                    knowledge_records=knowledge,atms_events=known_atms)
    need(len(lookup["items"])==1 and lookup["items"][0]["node_id"]==outcome,
         "A1_MEMORY_SCOPED_RETRIEVAL_MISSING")
    return {"schema":SCHEMA,"context":context,"recorded_as_of":time,
            "revisions":len(revisions),"ledger_integrity_verified":True,
            "atms_projection_hash":atms["projection_hash"],
            "atms_outcome":engine.explain(outcome),
            "retrieval_count":len(lookup["items"]),
            "cross_condition_and_cross_arm_injected":False,
            "security_limit":"APPLICATION_SCOPE_EXACT_CASE_ID_NOT_OS_ACL",
            "empirical_truth_from_ATMS":"NOT_ESTABLISHED",
            "memory_gate":"PARTIAL_APP_LEVEL_NO_FORMAL_OS_OR_API_ACL"}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=("record","inspect"))
    p.add_argument("--db",type=Path,required=True)
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--arm",choices=ARMS,required=True)
    p.add_argument("--condition",choices=("O0","O1"),required=True)
    p.add_argument("--run-kind",choices=("worker","native"),required=True)
    p.add_argument("--receipt",type=Path)
    p.add_argument("--manifest",type=Path)
    p.add_argument("--hj",type=Path)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    need(not a.out.exists(),"A1_MEMORY_REFUSE_OVERWRITE")
    v=json.loads(a.input.read_text())
    if a.action=="record":
        need(a.receipt is not None,"A1_MEMORY_NEEDS_RECEIPT")
        result=record(a.db,v,a.arm,a.condition,a.run_kind,
                      json.loads(a.receipt.read_text()),
                      manifest=json.loads(a.manifest.read_text()) if a.manifest else None,
                      hj=json.loads(a.hj.read_text()) if a.hj else None)
    else:
        need(a.receipt is None and a.manifest is None and a.hj is None,
             "A1_MEMORY_INSPECT_NO_EXTRA_FILES")
        result=inspect(a.db,v,a.arm,a.condition,a.run_kind)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_bytes(canonical(result)+b"\n")
    print(json.dumps({"scope":result["context"]["case_id"],
                      "revisions":result["revisions"],
                      "memory_gate":result["memory_gate"]}))


if __name__=="__main__":
    main()
