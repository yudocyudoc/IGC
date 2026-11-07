"""E02 Buffalo: append two authentic real natives and two G1 diagnostic vintages.

Provenance/time-aware additive correction to the frozen six-case F1a/ATMS ledger.
No provider call, native generation, native review, model rewriting, solver or DES.
Prior timeout evidence remains queryable at its original as_known_at cut.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil

from scripts.ledger import Ledger
from scripts.arena_atms import events_from_ledger, project
from scripts.arena_v0_contract import canonical

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "igc-e02-b-genuine-native-g1-temporal-adjudication/0.1"
PREVIOUS_RUN = 42322465960
LIVE_RUN = 42331388032
G1_ORIGINAL_RUN = 42331727460
G1_CORRECTED_RUN = 42335080421
PINNED = {
 "baseline": {
  "combined_ledger.sqlite": "e751e6044738bfd803d68e53119a925bb233319ef6e7d4742c07a748d603fc3d",
  "three_arm_report.json": "be9cfa35471e0300641c05cc9f0750fded5460a8e7d4b6d53e0334e1504a01c5",
  "b_attempt_reconciliation.json": "ccfbc25768689fcebb9066719e18f081fdc1cfc332fc6214f376a6744d5a3fee"
 },
 "G1_OLD": {
  "O0/g1-diagnostic.json": "a2fea218e02c61289bbafca16eae9760bbca65e7d412ea051689b4507a468f1e",
  "O1/g1-diagnostic.json": "added5eb1af3319ee9a7066b6a70a381631edcca46e6d72877832e8d708fd8ad"
 },
 "G1_NEW": {
  "O0/g1-diagnostic.json": "77ad4366ea01c9b8b5064b4db3bda176f511c60ea9dc2a53c9257c5579e4e7fa",
  "O1/g1-diagnostic.json": "7d7dfb3c836df1bfaf6b25d2c0a8e83edd32b8be65f7343d6f642d3814401847"
 },
 "O0": {
  "initial/cf-call-started.json": "b6790165cf043e4ccbbd797e448d362b490beefe78c56e8e95c86f1b81ecb0e7",
  "initial/cf-effective-request.json": "3e9ca9690c09aa7aba76c7d23b67bb56c138ac2087c9e397b865cd78b63e53c2",
  "initial/native-engine-result.json": "d7f30c0707e4f1a9762c7bddc7725a56bdb6d9f0e9cecf958e31bf0d783e4f65",
  "initial/receipt.json": "63c18ba2ba3803ea1323cd2bee7d089ecec38af347c605b8d1f5a49165622ced",
  "initial/provider-raw.json": "965271cbf3ba92e4125aeb0a088be62f8d3d9928954bacbd0dd0d3322761aad9",
  "initial/request-metadata.json": "ef1a425af61ab4bb6382470320d994695e5d30a201429791a39fe7a1fb9d6481",
  "staged/b-visible.json": "9a1bd8ac930b058add9be92fed539afc5447a3b817c147ea8990bfada798c34e"
 },
 "O1": {
  "initial/cf-call-started.json": "9d771866d778de15c617fc67d68a5d4a8451930569aba312f32d8a1bbef6f345",
  "initial/cf-effective-request.json": "7fffd4c7e72178ab55d535ca1243796e99d059af38a84713988233798e75611e",
  "initial/native-engine-result.json": "fd56288448ce8f6b66f76e1e4647900d8daf2dec4c92fb5431b1c32396f676b7",
  "initial/receipt.json": "6f30dc94365719cb6c2a587cbcd2960238b496f46f816b8d3b039a6a7e7c87b1",
  "initial/provider-raw.json": "cbdc1f200f40664f274ea176318d8df5d95cab184991c2666d8504e32d6856f9",
  "initial/request-metadata.json": "280d68a5c15271bca88e695a67342c217ed081ca1cf044ca6409f793745064a6",
  "staged/b-visible.json": "b34d50be81dbc09133b47eb70db724f5af78a128e9a54f44a3edafa4599d64dd"
 },
}
# Source: timestamped GitHub Actions log lines, UTC. Ceil to microsecond to
# avoid backdating a known outcome by a fractional microsecond during parsing.
KNOWLEDGE_TIMES = {
 "O0": {"native":"2026-11-07T02:55:15.171422+00:00",
        "g1_old":"2026-11-07T02:57:48.939248+00:00"},
 "O1": {"native":"2026-11-07T02:54:41.857578+00:00",
        "g1_old":"2026-11-07T02:57:48.939385+00:00"},
 "g1_new":"2026-11-07T03:40:44.785455+00:00",
}
EXPECTED_CODES = {
 "O0": {"GRAPHICAL_LOOKUP_NEEDS_ADAPTER", "UPSTREAM_FLOW_LOOKUP_IGNORED", "VARIABLE_CALLED_AS_FUNCTION"},
 "O1": {"GRAPHICAL_LOOKUP_NEEDS_ADAPTER", "UNRESOLVED_SYMBOL", "UNDECLARED_FUNCTION_CALL"},
}
MODEL_HASH = {"O0":"sha256:f090f082095bb21348c8d1313baf45beefab7422199cc9f62a34073973bd0c28",
              "O1":"sha256:1c74cc6ea8476ec543d47e74e68ea60e61eec3e56d537b3c4976d20c77106eff"}
KERNEL_HASH = "sha256:10170292eafd1f751247f03986ef4c0cd36fb36a9f3d1597b9bee9df7672e204"
ZIP_HASHES = {"O0":"ee8ff514f1931ec8fe2d80e86193414f6f2c8f223d39bb9b06b58f2db6501da9",
              "O1":"481640697422ef25ca25f122308e1d853426298a30a3e9cac450b172c214d458"}


def _sha(data:bytes)->str:
    return "sha256:"+sha256(data).hexdigest()


def _get(root:Path, name:str, expected:str)->dict:
    data=(root/name).read_bytes()
    if sha256(data).hexdigest()!=expected:
        raise ValueError("PINNED_MEMBER_CHANGED:"+str(root/name))
    obj=json.loads(data)
    if not isinstance(obj,dict):
        raise ValueError("PINNED_NOT_JSON:"+name)
    return obj


def _check_member(root:Path, name:str, expected:str)->str:
    data=(root/name).read_bytes()
    if sha256(data).hexdigest()!=expected:
        raise ValueError("PINNED_MEMBER_CHANGED:"+str(root/name))
    return _sha(data)


def inspect(condition:str, live:Path, old:Path, corrected:Path)->dict:
    """Reject mixed conditions, altered raw archives or ungrounded G1 claims."""
    if condition not in ("O0","O1"):
        raise ValueError("UNKNOWN_B_CONDITION")
    pins=PINNED[condition]
    r=_get(live,"initial/receipt.json",pins["initial/receipt.json"])
    native=_get(live,"initial/native-engine-result.json",pins["initial/native-engine-result.json"])
    raw=_get(live,"initial/provider-raw.json",pins["initial/provider-raw.json"])
    req=_get(live,"initial/cf-effective-request.json",pins["initial/cf-effective-request.json"])
    meta=_get(live,"initial/request-metadata.json",pins["initial/request-metadata.json"])
    started=_get(live,"initial/cf-call-started.json",pins["initial/cf-call-started.json"])
    visible=_get(live,"staged/b-visible.json",pins["staged/b-visible.json"])
    g1_old=_get(old,condition+"/g1-diagnostic.json",PINNED["G1_OLD"][condition+"/g1-diagnostic.json"])
    g1_new=_get(corrected,condition+"/g1-diagnostic.json",PINNED["G1_NEW"][condition+"/g1-diagnostic.json"])
    if not (r.get("case_id")=="EV-01" and r.get("condition_id")==condition
        and r.get("mode")=="live" and r.get("round_kind")=="initial"
        and r.get("model_returned") is True and r.get("provider_calls")==1
        and r.get("proxy_requests")==1 and r.get("http_status")==200
        and r.get("provider_finish_reason")=="stop" and r.get("native_error") is None
        and r.get("result_sha256")==MODEL_HASH[condition]
        and r.get("arrival_signal_sha256")==KERNEL_HASH
        and r.get("backend")=="OPEN_ROUTER" and r.get("backend_alias")=="cloudflare/glm-5.3-flash"
        and r.get("transport")=="CLOUDFLARE_WORKERS_AI_DIRECT_REST_JSON_SCHEMA"
        and r.get("upstream_sha")=="5199f7b45f3a7ae4a773cb0dd8542940aabe9edc"
        and r.get("horizon_matches_case") is True
        and r.get("original_engine_max_tokens")==16000):
        raise ValueError("LIVE_RECEIPT_OR_NATIVE_IDENTITY_INVALID:"+condition)
    if not (req.get("target_endpoint")=="Workers AI /ai/run/{model}"
        and req.get("actual_model")=="@cf/zai-org/glm-5.3-flash"
        and req.get("body_sha256")==r.get("translated_body_sha256")
        and req.get("body",{}).get("max_completion_tokens")==16000
        and req.get("body",{}).get("reasoning_effort")=="low"
        and req.get("body",{}).get("stream") is False
        and meta.get("original_alias_model")=="cloudflare/glm-5.3-flash"
        and meta.get("request_sha256")==r.get("request_sha256")
        and started.get("calls_started")==1
        and started.get("effective_body_sha256")==r.get("translated_body_sha256")
        and raw.get("success") is True and isinstance(raw.get("result"),dict)
        and visible.get("observability",{}).get("condition_id")==condition
        and visible.get("source_snapshot_hash")==r.get("source_snapshot_hash")
        and visible.get("construction",{}).get("declared_input_reconstruction",{}).get("signal_sha256")==KERNEL_HASH):
        raise ValueError("LIVE_CLOUDFLARE_OR_SOURCE_CONTRACT_CHANGED:"+condition)
    m=native.get("model",{})
    if not (len(m.get("variables",[]))==r.get("variable_count")
        and len(m.get("relationships",[]))==r.get("relationship_count")
        and abs(m.get("specs",{}).get("stopTime",-1)-1/6)<1e-10):
        raise ValueError("LIVE_NATIVE_NOT_EXPECTED:"+condition)
    if not (g1_old.get("schema")=="igc-b-native-g1-preflight/0.1"
        and g1_new.get("schema")=="igc-b-native-g1-preflight/0.2"
        and len(g1_old.get("issues",[]))==({"O0":11,"O1":2}[condition])
        and len(g1_new.get("issues",[]))==3
        and {x.get("code") for x in g1_new["issues"]}==EXPECTED_CODES[condition]
        and len(g1_new.get("one_point_graphical_markers",[]))==({"O0":5,"O1":0}[condition])
        and g1_new.get("status")=="G1_ISSUES_FOUND"
        and g1_new.get("g1_certified") is False
        and g1_new.get("g2_executed") is False
        and g1_new.get("variable_count")==len(m["variables"]) 
        and g1_new.get("relationship_count")==len(m["relationships"])):
        raise ValueError("G1_VINTAGES_OR_NATIVE_COUNTS_CHANGED:"+condition)
    # The old status is an observed prior diagnostic, NOT a scientific claim.
    # No G2 wrapper, no DIFF / corrective equation, no invented native decision.
    if condition=="O0":
        v=m["variables"][2]
        if not (v.get("type")=="flow" and len(v.get("graphicalFunction",{}).get("points",[]))==32
            and "order_creation_pattern(TIME)" in v.get("equation","")):
            raise ValueError("O0_FLOW_NATIVE_DEFECT_CHANGED")
    else:
        v=m["variables"][0]
        if not (v.get("type")=="variable" and len(v.get("graphicalFunction",{}).get("points",[]))==24
            and "arrival_input_by_time(TIME)" in v.get("equation","")):
            raise ValueError("O1_UNDECLARED_FUNCTION_DEFECT_CHANGED")
    return {
      "condition":condition,"source_snapshot_hash":r["source_snapshot_hash"],
      "shared_kernel_sha256":KERNEL_HASH,"raw_native_object_serialization_sha256":r["result_sha256"],
      "original_result_member_sha256":_sha((live/"initial/native-engine-result.json").read_bytes()),
      "provider_raw_member_sha256":_sha((live/"initial/provider-raw.json").read_bytes()),
      "request_member_sha256":_sha((live/"initial/cf-effective-request.json").read_bytes()),
      "receipt_member_sha256":_sha((live/"initial/receipt.json").read_bytes()),
      "original_g1_member_sha256":_sha((old/(condition+"/g1-diagnostic.json")).read_bytes()),
      "corrected_g1_member_sha256":_sha((corrected/(condition+"/g1-diagnostic.json")).read_bytes()),
      "source_artifact_zip_sha256_verified_prior":"sha256:"+ZIP_HASHES[condition],
      "live_run_id":LIVE_RUN,"real_artifact_id":{"O0":13557641048,"O1":13557710707}[condition],
      "provider_calls":1,"http_status":200,"native_produced":True,
      "native_variables":len(m["variables"]),"native_relationships":len(m["relationships"]),
      "request_started_at":started["timestamp"],
      "native_logged_at_utc_microsecond_ceiling":KNOWLEDGE_TIMES[condition]["native"],
      "G1_v01_knowledge_at":KNOWLEDGE_TIMES[condition]["g1_old"],
      "G1_v01_status":g1_old["status"],"G1_v01_issue_count":len(g1_old["issues"]),
      "G1_v02_knowledge_at":KNOWLEDGE_TIMES["g1_new"],
      "G1_v02_status":g1_new["status"],"G1_v02_issue_codes":sorted(EXPECTED_CODES[condition]),
      "G1_v02_issue_count":3,
      "single_point_non_lookup_markers":len(g1_new.get("one_point_graphical_markers",[])),
      "G2":"NOT_RUN","G3":"NOT_RUN","native_revision_calls":0,
    }


def _proj(db:Ledger,case:str,cut:str):
    eng,r=project(events_from_ledger(db.snapshot(case_id=case,as_known_at=cut)),
                  as_known_at=cut,investigation_id=case,lane=case.split("-")[1])
    return eng,r["projection_hash"]


def _write(db:Ledger,case:str,eid:str,typ:str,payload:dict,at:str,
           key:str,occurred_at:str|None=None):
    created_at=at
    return db.append_revision(entity_id=eid,entity_type=typ,case_id=case,
        actor_id="arena-e02-b-temporal-native-evidence",idempotency_key=case+":"+key,
        payload=payload,recorded_at=at,created_at=created_at,occurred_at=occurred_at,
        access_policy="lane:B")


def append_new_knowledge(db:Ledger,r:dict)->dict:
    c=r["condition"];case="E02-B-"+c
    t1=r["native_logged_at_utc_microsecond_ceiling"]
    t2=r["G1_v01_knowledge_at"]
    t3=r["G1_v02_knowledge_at"]
    before=(datetime.fromisoformat(t1)-timedelta(microseconds=1)).isoformat()
    assert datetime.fromisoformat(t1)<datetime.fromisoformat(t2)<datetime.fromisoformat(t3)
    fail=case+":PROVIDER_ATTEMPT_FAILED"
    no_native=case+":NO_NATIVE_EVALUABLE"
    source=case+":SOURCE_ATTEMPT_DECLARED"
    model=case+":NATIVE_FROM_CORRECTED_SECOND_INITIAL"
    available=case+":NATIVE_AVAILABLE_AT_NEW_KNOWLEDGE_CUT"
    olddiag=case+":ORIGINAL_G1_PRELIMINARY_OBSERVED"
    newdiag=case+":CORRECTED_G1_OBSERVED"
    blocked=case+":G2_BLOCKED_BY_CURRENT_NATIVE_DEFECTS"
    oldeng,oldhash=_proj(db,case,before)
    if not (oldeng.explain(fail)["supported"] and
            oldeng.explain(no_native)["supported"] and
            not oldeng.explain(available)["supported"]):
        raise ValueError("B_OLD_FAILED_ATTEMPT_CUT_INVALID:"+case)
    artifact="sha256:"+sha256(canonical(r)).hexdigest()
    _write(db,case,case+":CORRECTED_NATIVE_ARTIFACT","EvidenceArtifact",{
       "schema":SCHEMA,"role":"PROVIDER_AND_ORIGINAL_ENGINE_RESULT",
       "artifact_sha256":artifact,"data":r,
       "source_run_id":LIVE_RUN,"no_native_mutation":True,
       "provenance":"REAL_HTTP_200_INITIAL_GENERATION_AFTER_PRIOR_FAILED_TRANSPORT",
       "request_occurred_at":r["request_started_at"],
       "result_known_at":t1,
    },t1,"real-native-artifact",occurred_at=r["request_started_at"])
    _write(db,case,model,"ATMSNode",{"kind":"fact","active":True,
       "claim":"NEW_AUTHENTIC_INITIAL_NATIVE_RETURNED_HTTP_200_NOT_REVISION",
       "evidence_artifact_sha256":artifact,
       "native_result_sha256":r["raw_native_object_serialization_sha256"],
    },t1,"real-native-fact",occurred_at=t1)
    # Revise the old *derived, current-availability* rule; historical failure
    # remains a supported fact, and past snapshots still activate the old rule.
    _write(db,case,case+":RULE","ATMSNode",{
       "kind":"justification","active":False,"antecedents":[fail],
       "consequent":no_native,"source_id":fail,
       "reason":"OBSOLETE_CURRENT_AVAILABILITY_AFTER_NEW_INITIAL_SUCCESS;_PRIOR_FAILURE_FACT_RETAINED",
       "new_live_run_id":LIVE_RUN,
    },t1,"supersede-outdated-no-native-rule")
    _write(db,case,case+":REAL_NATIVE_RULE","ATMSNode",{
       "kind":"justification","active":True,"antecedents":[model],
       "consequent":available,"source_id":model,
    },t1,"real-native-rule")
    _write(db,case,case+":KNOWLEDGE","KnowledgeItem",{
       "kind":"knowledge","active":True,"source_revision":2,
       "node_id":available,"source_id":model,
       "title":"Buffalo "+c+": genuine separate initial generation obtained",
       "text":"HTTP 200 native returned, but no G1/G2 conclusion yet; earlier timeout preserved",
       "epistemic_status":"NATIVE_GENERATED_NOT_YET_ADJUDICATED",
       "evidence_artifact_sha256":artifact,
    },t1,"knowledge-native-v2")
    old_hash=r["original_g1_member_sha256"]
    _write(db,case,case+":G1_V01_ARTIFACT","EvidenceArtifact",{
       "schema":SCHEMA,"role":"HISTORICAL_G1_V01_ADVISORY_REPORT",
       "artifact_sha256":old_hash,"data":{
          "status":r["G1_v01_status"],"issue_count":r["G1_v01_issue_count"],
          "source_run_id":G1_ORIGINAL_RUN,"not_empirical_truth":True}},t2,"g1-old-artifact")
    _write(db,case,olddiag,"ATMSNode",{"kind":"fact","active":True,
       "claim":"ORIGINAL_ADVISORY_DIAGNOSTIC_REPORTED_NOT_CERTIFIED",
       "evidence_artifact_sha256":old_hash,"not_established_scientifically":True},t2,"g1-old-fact")
    _write(db,case,case+":KNOWLEDGE","KnowledgeItem",{
       "kind":"knowledge","active":True,"source_revision":3,
       "node_id":olddiag,"source_id":olddiag,
       "title":"Buffalo "+c+": original G1 v0.1 advisory recorded",
       "text":"Prior lexical flags not final; one-point lookup semantics pending review",
       "epistemic_status":"PRELIMINARY_G1_DIAGNOSTIC_NOT_SCIENTIFIC_CERTIFICATION",
       "evidence_artifact_sha256":old_hash,
    },t2,"knowledge-g1-v01")
    corrected_hash=r["corrected_g1_member_sha256"]
    _write(db,case,case+":G1_V02_ARTIFACT","EvidenceArtifact",{
       "schema":SCHEMA,"role":"CORRECTED_G1_V02_UPSTREAM_ADJUDICATION",
       "artifact_sha256":corrected_hash,"data":{
          "status":r["G1_v02_status"],"issue_count":3,
          "issue_codes":r["G1_v02_issue_codes"],
          "single_point_non_lookup_markers":r["single_point_non_lookup_markers"],
          "source_run_id":G1_CORRECTED_RUN,"diagnosis_not_solver":True}},t3,"g1-corrected-artifact")
    _write(db,case,newdiag,"ATMSNode",{"kind":"fact","active":True,
       "claim":"UPSTREAM_ALIGNED_G1_V02_PROVENANCE_BOUND_BLOCKERS_RECORDED",
       "evidence_artifact_sha256":corrected_hash,
       "native_result_sha256":r["raw_native_object_serialization_sha256"],
    },t3,"g1-corrected-fact")
    _write(db,case,case+":G1_BLOCK_RULE","ATMSNode",{
       "kind":"justification","active":True,
       "antecedents":[model,newdiag],"consequent":blocked,"source_id":newdiag,
       "epistemic_scope":"CURRENT_NATIVE_NOT_ADMISSIBLE_FOR_FAITHFUL_G2",
       "not_method_generalization":True,
    },t3,"g1-block-rule")
    _write(db,case,case+":KNOWLEDGE","KnowledgeItem",{
       "kind":"knowledge","active":True,"source_revision":4,
       "node_id":blocked,"source_id":newdiag,
       "title":"Buffalo "+c+": authentic initial native not G1 admissible",
       "text":"G1 v0.2 upstream-aligned blocking functions/input; no G2 or native review",
       "epistemic_status":"LOCAL_STATIC_NATIVE_INPUT_FUNCTION_BLOCK_NOT_METHOD_IMPOSSIBILITY",
       "evidence_artifact_sha256":corrected_hash,
       "native_result_sha256":r["raw_native_object_serialization_sha256"],
    },t3,"knowledge-g1-v02")
    cuts=[]
    for label,when in (("before_new_native",before),("after_native",t1),
                       ("after_original_g1",t2),("after_corrected_g1",t3)):
        eng,h=_proj(db,case,when)
        snap=db.snapshot(case_id=case,as_known_at=when)
        knowledge=[x for x in snap if x.entity_id==case+":KNOWLEDGE"]
        cuts.append({"name":label,"as_known_at":when,"projection_hash":h,
           "failed_transport_fact_still_supported":eng.explain(fail)["supported"],
           "no_native_currently_supported":eng.explain(no_native)["supported"],
           "native_available":eng.explain(available)["supported"],
           "old_g1_recorded":eng.explain(olddiag)["supported"],
           "corrected_g1_recorded":eng.explain(newdiag)["supported"],
           "g2_blocked_current_native":eng.explain(blocked)["supported"],
           "current_knowledge_revision":knowledge[0].revision if knowledge else None,
           "current_knowledge_node":knowledge[0].payload.get("node_id") if knowledge else None})
    if not (cuts[0]["failed_transport_fact_still_supported"] and
            cuts[0]["no_native_currently_supported"] and not cuts[0]["native_available"]
        and cuts[1]["failed_transport_fact_still_supported"] and
            not cuts[1]["no_native_currently_supported"] and cuts[1]["native_available"]
        and not cuts[1]["g2_blocked_current_native"]
        and cuts[2]["old_g1_recorded"] and not cuts[2]["corrected_g1_recorded"]
        and not cuts[2]["g2_blocked_current_native"]
        and cuts[3]["failed_transport_fact_still_supported"]
        and cuts[3]["native_available"] and cuts[3]["corrected_g1_recorded"]
        and cuts[3]["g2_blocked_current_native"]
        and cuts[3]["current_knowledge_revision"]==4
        and cuts[0]["projection_hash"]==oldhash):
        raise ValueError("E02_B_TEMPORAL_MEMORY_NOT_CAUSALLY_RECONSTRUCTIBLE:"+case)
    return {"case_id":case,"artifact_sha256":artifact,
        "status":"REAL_NATIVE_RETURNED_G1_V02_BLOCKED_NO_SECOND_DECISION",
        "historical_failure_fact_preserved":True,
        "new_revision_calls":0,"new_provider_calls_for_ledger":0,
        "new_revisions_appended":12,"snapshots":cuts}


def combine(baseline:Path, o0:Path,o1:Path,old:Path,corrected:Path,out:Path)->dict:
    if out.exists():
        raise ValueError("E02_B_CLOSURE_REFUSE_OVERWRITE")
    for name,pin in PINNED["baseline"].items():
        _check_member(baseline,name,pin)
    records={c:inspect(c,path,old,corrected) for c,path in (("O0",o0),("O1",o1))}
    if (records["O0"]["shared_kernel_sha256"]!=records["O1"]["shared_kernel_sha256"]
        or records["O0"]["source_snapshot_hash"]==records["O1"]["source_snapshot_hash"]):
        raise ValueError("LIVE_O0_O1_OBSERVABILITY_ISOLATION_BROKEN")
    baseline_report=json.loads((baseline/"three_arm_report.json").read_text())
    old_b=json.loads((baseline/"b_attempt_reconciliation.json").read_text())
    if not (baseline_report["status"]=="E02_THREE_METHODS_ATTEMPTED_B_TIMEOUT_NO_NATIVE_MODEL_PARTIAL"
        and baseline_report["buffalo_actual_provider_calls_attempted"]==2
        and old_b["attempted_provider_calls"]==2):
        raise ValueError("OLD_SCIENTIFIC_STATUS_CHANGED")
    out.mkdir(parents=True)
    dbpath=out/"combined_ledger_v2.sqlite"
    shutil.copyfile(baseline/"combined_ledger.sqlite",dbpath)
    db=Ledger(dbpath,ROOT/"migrations/0001_ledger.sql")
    historical={}
    for c in ("O0","O1"):
        case="E02-B-"+c
        history=old_b["memory"][c]["snapshots"]
        historical[case]=[]
        for snap in history:
            e,h=_proj(db,case,snap["at"])
            if h!=snap["projection_hash"]:
                raise ValueError("B_HISTORICAL_ATMS_SNAPSHOT_CHANGED:"+case)
            historical[case].append({"as_known_at":snap["at"],"projection_hash":h})
    dm={}
    for case,row in baseline_report["dm_temporal_projections_preserved"].items():
        _,h=_proj(db,case,row["as_known_at"])
        if h!=row["projection_hash"]:
            raise ValueError("DM_HISTORICAL_ATMS_SNAPSHOT_CHANGED:"+case)
        dm[case]={"as_known_at":row["as_known_at"],"projection_hash":h}
    updated={c:append_new_knowledge(db,r) for c,r in records.items()}
    for case,rows in historical.items():
        for row in rows:
            _,h=_proj(db,case,row["as_known_at"])
            if h!=row["projection_hash"]:
                raise ValueError("B_HISTORICAL_SUPPORT_WAS_MUTATED:"+case)
    for case,row in dm.items():
        _,h=_proj(db,case,row["as_known_at"])
        if h!=row["projection_hash"]:
            raise ValueError("DM_PROJECTION_WAS_MUTATED:"+case)
    # Case scopes, model-authentic receipts and non-mutating SQLite integrity.
    for c in ("O0","O1"):
        case="E02-B-"+c
        for rv in db.snapshot(case_id=case,as_known_at=KNOWLEDGE_TIMES["g1_new"]):
            if not db.verify_integrity(entity_id=rv.entity_id,revision=rv.revision):
                raise ValueError("E02_LEDGER_INTEGRITY_FAILURE:"+rv.entity_id)
    result={
       "schema":SCHEMA,"status":"E02_B_TWO_GENUINE_INITIAL_NATIVE_MODELS_G1_V02_STATIC_BLOCKED",
       "source_frozen_ledger_workflow_run_id":PREVIOUS_RUN,
       "source_live_workflow_run_id":LIVE_RUN,
       "source_g1_original_run_id":G1_ORIGINAL_RUN,
       "source_g1_corrected_run_id":G1_CORRECTED_RUN,
       "frozen_baseline_ledger_bytes_sha256":"sha256:"+PINNED["baseline"]["combined_ledger.sqlite"],
       "old_three_arm_report_is_historical_not_rewritten":True,
       "old_corrected_live_results_manifest_is_historical_not_rewritten":True,
       "dm_temporal_projections_preserved":dm,
       "b_prior_timeout_temporal_projections_preserved":historical,
       "previous_failed_provider_attempts":2,"corrected_successful_initial_attempts":2,
       "total_e02_b_provider_attempts":4,"provider_attempt_budget":4,
       "original_b_native_revision_decisions":0,"new_provider_calls":0,"new_omc_runs":0,
       "no_private_evaluator_or_other_arm_inputs":True,
       "G1":"CURRENT_TWO_NATIVE_G1_V02_BLOCKED_NOT_CERTIFIED",
       "G2":"NOT_RUN","G3":"NOT_RUN","G4":"NOT_RUN","G5":"NOT_RUN",
       "E05":"BLOCKED_ACTION_NOT_FAITHFUL_OR_VALIDATED",
       "source_layer_semantics":{
           "request_started_at":"raw native-run cf-call-started.timestamp (provider event start)",
           "native_logged_at":"timestamp from authentic GitHub native-return log; ceil to 1 microsecond, not a latent model time",
           "diagnostics_known_at":"GitHub Actions log confirming old and corrected G1; ceil to 1 microsecond",
           "frozen_timeout_ledger_time":"earlier synthetic deterministic replay ingestion cutoff, NOT true provider runtime",
           "recorded_at":"known-at provenance per artifact; never backdate successful native to request start",
           "prior_facts":"failed attempt remains true but derived NO_NATIVE_EVALUABLE current-availability support retired after new generation"},
       "conditions":{c:{"source":records[c],"memory":updated[c]} for c in ("O0","O1")},
       "what_this_does_not_claim":"B_SEMANTIC_OR_PHYSICAL_SUCCESS_OR_SECOND_NATIVE_DECISION",
    }
    (out/"adjudication_report.json").write_bytes(canonical(result)+b"\n")
    return result


def main():
    ap=argparse.ArgumentParser()
    for x in ("baseline","o0","o1","g1-old","g1-new","out"):
        ap.add_argument("--"+x,required=True,type=Path)
    x=ap.parse_args()
    result=combine(x.baseline,x.o0,x.o1,x.g1_old,x.g1_new,x.out)
    print(json.dumps({k:result[k] for k in ("status","total_e02_b_provider_attempts",
          "original_b_native_revision_decisions","new_provider_calls","new_omc_runs")},sort_keys=True))

if __name__=="__main__":
    main()