"""E02 development construction: original D/M producers, actual historical OMC and scoped review.

Never infer independent B outputs, capacity measurements, model compatibility bands,
or new observations. This module runs only with published A1 public O0/O1 and
authentic #143 D/M G2 artifacts (G2 verify is repeated before H_j consumption).
D/M second decisions are explicitly owned by a versioned experimental policy,
NOT a claim that original enumerators learned mechanisms autonomously.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
import json
import math
from pathlib import Path

from scripts.arena_cafe import (
    observation_eval as oe, observation_ports as ports,
    r2_observational_contracts as r2, r2_causal_pos_signal as signal,
    r2_causal_g2 as d_g2, r2_m_six_causal_g2 as m_g2,
)
from scripts.arena_v0_contract import canonical, digest
from scripts.ledger import Ledger
from scripts.arena_atms import events_from_ledger, project
from scripts.arena_memory import load_events_from_ledger, retrieve
from scripts.arena_cafe.native_handoff import need

ROOT=Path(__file__).resolve().parents[2]
SCHEMA="igc-arena-cafe-continuity-e02-development/0.1"
POLICY="D-M-SET-DESCRIPTIVE-SECOND-DECISION/0.1"
REGISTRY=ROOT/"experiments/e1/registry.base.json"
ARMS=("D","M")
CONDS=("O0","O1")
B_STATUS="BLOCKED_NOT_RUN_NOT_ABSTENTION"


def _vector(evaluation):
    scores=[x for x in evaluation.get("comparisons",[])
            if x["observable"]=="delivered_cumulative"]
    if len(scores)!=6 or [x["t_minutes"] for x in scores]!=[0,2,4,6,8,10]:
        return {"status":"NOT_COMPARABLE_SIX_TERMINAL_CUTS",
                "reason":"MISSING_OR_MISALIGNED_NATIVE_DELIVERY_OBSERVABLE"}
    errs=[x["residual_orders"] for x in scores]
    return {"status":"DESCRIPTIVE_ONLY_NOT_COMPATIBILITY",
            "observed":[x["observed_orders"] for x in scores],
            "native":[round(x["native_prediction"],7) for x in scores],
            "residuals":[round(x,7) for x in errs],
            "MAE":round(sum(abs(e) for e in errs)/6,7),
            "RMSE":round(math.sqrt(sum(e*e for e in errs)/6),7),
            "max_abs":round(max(abs(e) for e in errs),7),
            "no_epsilon_model_defended":True}


def _evaluate_one(visible, arm, condition, rows, native_dir):
    port=ports.port(visible,arm,condition,registry=REGISTRY if arm=="M" else None)
    outcomes=[]
    for item in rows:
        native_id=item["candidate_id"] if arm=="D" else item["canonical_sha256"]
        csv=Path(native_dir)/(item["csv_prefix"]+"_res.csv")
        # E1's enumerator exports a 64-hex canonical key; H_j's original
        # candidate wrapper requires the prefixed canonical digest. Converting
        # its representation does NOT change the AST, family, or parameters.
        graph=({"ast":item["original_ast"],
                "canonical_sha256":"sha256:"+item["canonical_sha256"]}
                if arm=="M" else None)
        try:
            ev=oe.evaluate(visible,port,trace_csv=csv,candidate=graph,
                           registry=REGISTRY if arm=="M" else None)
            need(ev["status"]=="DESCRIPTIVE_HJ_PROBE_ONLY_UNVERIFIED_TRACE",
                 "E02_HJ_UNEXPECTED_STATUS")
            diagnostic=_vector(ev)
            diagnostic["H_j_provenance"]="READONLY_OPERATOR_WITH_SEPARATELY_AUTHENTICATED_G2"
            diagnostic["native_csv_sha256"]=ev["trace_sha256"]
        except (ValueError,KeyError,TypeError,AssertionError) as exc:
            diagnostic={"status":"NOT_COMPARABLE_HJ_ERROR",
                        "reason":str(exc),"H_j_provenance":"FAILED"}
        outcomes.append({"candidate":native_id,"diagnostic":diagnostic})
    need(len(outcomes)==6 and len({r["candidate"] for r in outcomes})==6,
         "E02_NOT_ALL_SIX_CANDIDATES_REPORTED")
    return outcomes


def _policy_decision(arm, diagnostics):
    comparable=[x for x in diagnostics if x["diagnostic"]["status"]==
                "DESCRIPTIVE_ONLY_NOT_COMPATIBILITY"]
    all_ids=[x["candidate"] for x in diagnostics]
    return {
        "policy":POLICY,"author":"EXPLICIT_EXPERIMENTAL_POLICY_NOT_ORIGINAL_ENUMERATOR",
        "first_decision":{"status":"UNSELECTED_SIX_NATIVE_CANDIDATES",
                          "candidate_ids":all_ids},
        "private_feedback":{
            "own_diagnostic_by_candidate":diagnostics,
            "rival_outputs_visible":False,
            "physical_private_des_visible":False,
            "epsilon_model":"UNDEFENDED_NO_PASS_OR_FAIL",
        },
        "second_decision":{
            "status":"RATIFY_UNRESOLVED_FULL_SET_WITH_EXPLICIT_LIMITS",
            "candidate_ids":all_ids,
            "because":(
                "D parameters remain engineering fixture; no independent capacity measurement"
                if arm=="D" else
                "Original E1 priors fixed; no model discrepancy band or calibrated selection"
            ),
            "method_revision":"NONE_STRUCTURE_AND_PARAMETERS_UNCHANGED",
            "own_feedback_considered":True,
            "native_regeneration":"NOT_PERFORMED",
            "scientific_compatibility":"NOT_CLAIMED",
        },
        "attempted_comparable":len(comparable),
        "attempted_total":len(diagnostics),
        "not_a_causal_O1_ablation":True,
    }


def _memory(ledger, arm, condition, report, recorded):
    """Store actual source -> native -> diagnostic -> feedback -> decision lineage.

    Existing F1a ledger is canonical. ATMS supports *use* of artifacts, not
    truth of their scientific content. Exactly one scoped development round.
    """
    case=f"E02-{arm}-{condition}"
    need(arm in ARMS and condition in CONDS and type(report) is dict,
         "E02_MISSING_OR_INVALID_EVIDENCE_RECORD")
    need(set(report)=={"source","native","diagnostics","feedback","decision"},
         "E02_EVIDENCE_CHAIN_INCOMPLETE")
    source,native,diagnostics,feedback,decision=(
        report[k] for k in ("source","native","diagnostics","feedback","decision"))
    need(type(source) is dict and source.get("source_snapshot_hash") and
         source.get("visible_sha256") and source.get("condition")==condition,
         "E02_SOURCE_NOT_HASH_BOUND")
    need(type(native) is dict and native.get("arm")==arm and
         native.get("manifest_sha256") and native.get("G2")==
         "HISTORICAL_AUTHENTIC_REAL_OMC_VERIFIED",
         "E02_NATIVE_NOT_HASH_BOUND")
    need(type(diagnostics) is list and len(diagnostics)==6 and
         all(type(x) is dict and x.get("candidate") and
             type(x.get("diagnostic")) is dict for x in diagnostics) and
         len({x["candidate"] for x in diagnostics})==6,
         "E02_DIAGNOSTIC_SET_INVALID")
    ids=[x["candidate"] for x in diagnostics]
    need(native.get("candidate_ids")==ids and
         type(native.get("verified_g2_traces")) is dict and
         set(native["verified_g2_traces"])==set(ids) and
         all(isinstance(v,str) and v.startswith("sha256:") and len(v)==71
             for v in native["verified_g2_traces"].values()),
         "E02_NATIVE_TRACE_IDENTITY_MISMATCH")
    need(type(feedback) is dict and
         feedback.get("own_diagnostic_by_candidate")==diagnostics and
         feedback.get("rival_outputs_visible") is False and
         feedback.get("physical_private_des_visible") is False and
         type(decision) is dict and decision.get("private_feedback")==feedback and
         decision.get("first_decision",{}).get("candidate_ids")==ids and
         decision.get("second_decision",{}).get("candidate_ids")==ids and
         decision.get("author")=="EXPLICIT_EXPERIMENTAL_POLICY_NOT_ORIGINAL_ENUMERATOR",
         "E02_FEEDBACK_OR_DECISION_NOT_CAUSED_BY_OWN_DIAGNOSTIC")
    need(recorded.tzinfo is not None and recorded.utcoffset() is not None,
         "E02_RECORDED_TIME_NEEDS_ZONE")
    t0=recorded.astimezone(timezone.utc)
    t1=t0+timedelta(microseconds=1)
    stamps=[t.isoformat() for t in (t0,t1)]
    bodies={"source":source,"native":native,"diagnostics":diagnostics,
            "feedback":feedback,"decision":decision}
    hashes={k:digest(v) for k,v in bodies.items()}
    ids_map={k:case+":"+k.upper()+":"+h[7:23] for k,h in hashes.items()}
    initial=case+":INITIAL"
    revised=case+":RETAINED_AMBIGUITY"
    support=case+":SUPPORT"
    fb_rule=case+":FEEDBACK_FROM_DIAGNOSTIC"
    decision_rule=case+":DECISION_FROM_FEEDBACK"
    knowledge=case+":KNOWLEDGE"
    staged=[]

    def put(entity,typ,payload,at,key):
        staged.append((entity,typ,payload,stamps[at],case+":"+key))

    # Hash-identified artifacts carry the evidence itself, not only a generic
    # stamp. Their references can be checked against native manifests/CSV.
    for role,body in bodies.items():
        put(case+":ARTIFACT:"+role.upper(),"EvidenceArtifact",{
            "schema":"igc-e02-evidence-artifact/0.1",
            "artifact_sha256":hashes[role],
            "artifact_role":role,
            "data":body,
            "dependencies":(
                [] if role=="source" else
                ["source:"+hashes["source"]] if role=="native" else
                ["native:"+hashes["native"]] if role=="diagnostics" else
                ["diagnostics:"+hashes["diagnostics"]] if role=="feedback" else
                ["feedback:"+hashes["feedback"]]),
        },0 if role in ("source","native") else 1,"artifact-"+role)
    for role in ("source","native","diagnostics"):
        put(ids_map[role],"ATMSNode",{
            "kind":"assumption","active":True,
            "evidence_artifact_sha256":hashes[role],
            "assumption_type":"DOCUMENTED_EVIDENCE_AVAILABLE_NOT_SCIENTIFIC_TRUTH"
        },0 if role!="diagnostics" else 1,"anchor-"+role)
    put(support,"ATMSNode",{"kind":"justification","active":True,
        "antecedents":[ids_map["source"],ids_map["native"]],
        "consequent":initial,"source_id":ids_map["native"]},0,"support-v1")
    put(knowledge,"KnowledgeItem",{"kind":"knowledge","active":True,
        "node_id":initial,"source_id":ids_map["native"],
        "title":case+" native universe before own feedback",
        "text":"Six authentic G2 engineering traces, no scientific model band",
        "source_revision":1,"source_artifact_sha256":hashes["source"],
        "native_artifact_sha256":hashes["native"]},0,"knowledge-v1")
    put(fb_rule,"ATMSNode",{"kind":"justification","active":True,
        "antecedents":[ids_map["diagnostics"]],
        "consequent":ids_map["feedback"],
        "source_id":ids_map["diagnostics"],
        "feedback_sha256":hashes["feedback"]},1,"feedback-rule")
    put(decision_rule,"ATMSNode",{"kind":"justification","active":True,
        "antecedents":[ids_map["feedback"]],
        "consequent":ids_map["decision"],"source_id":ids_map["feedback"],
        "decision_sha256":hashes["decision"]},1,"decision-rule")
    put(support,"ATMSNode",{"kind":"justification","active":True,
        "antecedents":[ids_map["source"],ids_map["native"],ids_map["decision"]],
        "consequent":revised,"source_id":ids_map["decision"]},1,"support-v2")
    put(knowledge,"KnowledgeItem",{"kind":"knowledge","active":True,
        "node_id":revised,"source_id":ids_map["decision"],
        "title":case+" revision supported by own diagnostics",
        "text":decision["second_decision"]["status"],
        "source_revision":2,
        "diagnostics_sha256":hashes["diagnostics"],
        "feedback_sha256":hashes["feedback"],
        "decision_sha256":hashes["decision"]},1,"knowledge-v2")
    for entity,typ,payload,stamp,key in staged:
        ledger.append_revision(entity_id=entity,entity_type=typ,case_id=case,
            actor_id="arena-e02-explicit-policy",idempotency_key=key,
            payload=payload,recorded_at=stamp,created_at=stamp,
            access_policy="lane:"+arm)
    cuts=[]
    engines=[]
    for stamp in stamps:
        snapshot=ledger.snapshot(case_id=case,as_known_at=stamp)
        eng,projection=project(events_from_ledger(snapshot),as_known_at=stamp,
                               investigation_id=case,lane=arm)
        kn,events=load_events_from_ledger(Path(ledger.db_path),case,stamp)
        result=retrieve(investigation_id=case,lane=arm,as_known_at=stamp,
                        query="native ambiguity",knowledge_records=kn,
                        atms_events=events)
        cuts.append({"at":stamp,
                     "initial_supported":eng.explain(initial)["supported"],
                     "retained_supported":eng.explain(revised)["supported"],
                     "visible_knowledge":[x["node_id"] for x in result["items"]],
                     "projection_hash":projection["projection_hash"]})
        engines.append(eng)
    need(cuts[0]["initial_supported"] and
         not cuts[0]["retained_supported"] and
         not cuts[1]["initial_supported"] and
         cuts[1]["retained_supported"],"E02_TEMPORAL_SUPPORT_NOT_EVIDENCE_BOUND")
    alternative=engines[1].what_if(disable_assumptions=(ids_map["diagnostics"],))
    need(revised in alternative["changed_nodes"] and
         ids_map["source"] not in alternative["changed_nodes"] and
         ids_map["native"] not in alternative["changed_nodes"],
         "E02_DIAGNOSTIC_REMOVAL_NOT_LOCALIZED")
    return {"status":"SCOPED_ATMS_EVIDENCE_BOUND_REVISION_NOT_EMPIRICAL_LEARNING",
            "case_id":case,"cuts":cuts,"artifact_sha256":hashes,
            "support_node_ids":ids_map,
            "diagnostic_removal_changes_only_dependent_conclusions":True,
            "recorded_revisions":len(staged),
            "truth_status":"NOT_ESTABLISHED_BY_ATMS"}


def retract_e02_diagnostic(ledger, arm, condition, node_id, recorded):
    """Append an actual correction; never mutate an older knowledge snapshot."""
    case=f"E02-{arm}-{condition}"
    need(arm in ARMS and condition in CONDS and
         node_id.startswith(case+":DIAGNOSTICS:") and
         recorded.tzinfo is not None,"E02_INVALID_RETRACTION_CONTEXT")
    stamp=recorded.astimezone(timezone.utc).isoformat()
    # Do not accept arbitrary nodes from another case or synthetic assumptions.
    prior=ledger.snapshot(case_id=case,as_known_at=stamp)
    matches=[x for x in prior if x.entity_id==node_id and
             x.entity_type=="ATMSNode" and
             x.payload.get("kind")=="assumption" and x.payload.get("active") is True]
    need(len(matches)==1,"E02_DIAGNOSTIC_NOT_CURRENTLY_ACTIVE")
    ledger.append_revision(entity_id=node_id,entity_type="ATMSNode",
        case_id=case,actor_id="arena-e02-diagnostic-retraction",
        idempotency_key=case+":retract:"+node_id+":"+stamp,
        payload={"kind":"assumption","active":False,
                 "reason":"EVIDENCE_DIAGNOSTIC_RETRACTED",
                 "superseded_diagnostic_hash":matches[0].payload["evidence_artifact_sha256"]},
        recorded_at=stamp,created_at=stamp,access_policy="lane:"+arm)
    eng,_=project(events_from_ledger(
         ledger.snapshot(case_id=case,as_known_at=stamp)),
         as_known_at=stamp,lane=arm,investigation_id=case)
    return {"case_id":case,"at":stamp,"revised_supported":
            eng.explain(case+":RETAINED_AMBIGUITY")["supported"],
            "source_supported":True,
            "native_supported":True,
            "reason":"WITHDRAWN_DIAGNOSTIC_AFFECTS_ITS_DEPENDENT_DECISION"}

def run(o0,o1,d_dir,m_dir,db):
    from scripts.arena_cafe.native_handoff import validate_a1_visible
    for c,v in (("O0",o0),("O1",o1)):
        validate_a1_visible(v,c)
    need(signal.from_visible(o0,"O0")["signal"]==
         signal.from_visible(o1,"O1")["signal"],
         "E02_CONDITIONS_DO_NOT_SHARE_EXOGENOUS_ARRIVALS")
    d_verified=d_g2.verify(o0,Path(d_dir))
    m_verified=m_g2.verify(o0,Path(m_dir))
    need(d_verified["G2"]==m_verified["G2"]=="PASS_REAL_OMC_ENGINEERING_ONLY",
         "E02_G2_NOT_AUTHENTICATED")
    need(d_verified["signal_sha256"]==m_verified["same_causal_signal_hash_as_D"],
         "E02_SIGNAL_NOT_SHARED")
    d_manifest=json.loads((Path(d_dir)/"manifest.json").read_text())
    m_manifest=json.loads((Path(m_dir)/"manifest.json").read_text())
    need(d_manifest["candidate_count"]==m_manifest["candidate_count"]==6,
         "E02_NATIVE_UNIVERSE_CHANGED")
    ledger=Ledger(db,ROOT/"migrations/0001_ledger.sql")
    results={}
    for cond,v in (("O0",o0),("O1",o1)):
        results[cond]={}
        for arm,manifest,nativedir in (("D",d_manifest,d_dir),("M",m_manifest,m_dir)):
            diagnostics=_evaluate_one(v,arm,cond,manifest["candidates"],nativedir)
            decision=_policy_decision(arm,diagnostics)
            results[cond][arm]={
                "native_source":"D-POS_SIX_ORIGINAL_D_STRUCTURES" if arm=="D"
                                else "SIX_ORIGINAL_SHORT_E1_FULL_AST",
                "G2":"HISTORICAL_AUTHENTIC_REAL_OMC_VERIFIED",
                "G3":"DESCRIPTIVE_ONLY_NO_EPSILON_MODEL",
                "candidate_count":6,
                "parameters":"D_EXTERNAL_FIXTURE_NOT_MEASURED" if arm=="D"
                             else "E1_FIXED_PRIORS_NOT_ESTIMATED",
                "H_j":diagnostics,"decision":decision,
            }
            verified=d_verified if arm=="D" else m_verified
            verified_traces={}
            for x in verified["candidates"]:
                key=x["candidate_id"] if arm=="D" else x["canonical_sha256"]
                verified_traces[key]=(x["csv_sha256"] if arm=="D"
                                      else x["solver_csv_sha256"])
            evidence_record={
                "source":{
                    "condition":cond,
                    "source_snapshot_hash":v["source_snapshot_hash"],
                    "visible_sha256":digest(v),
                    "public_cutoff_minutes_exact":
                        v["observability"]["cutoff_minutes_exact"],
                },
                "native":{
                    "arm":arm,"manifest_sha256":digest(manifest),
                    "candidate_ids":[x["candidate"] for x in diagnostics],
                    "verified_g2_traces":verified_traces,
                    "G2":"HISTORICAL_AUTHENTIC_REAL_OMC_VERIFIED",
                },
                "diagnostics":diagnostics,
                "feedback":decision["private_feedback"],
                "decision":decision,
            }
            memory=_memory(ledger,arm,cond,evidence_record,
                           datetime.now(timezone.utc))
            results[cond][arm]["memory"]=memory
    return {"schema":SCHEMA,"case":"EV-01","dataset":"PUBLIC_DEVELOPMENT_O0_O1",
            "status":"E02_PARTIAL_B_NOT_RUN_D_M_POLICY_REVIEW_RECORDED",
            "no_prospective_prediction":True,
            "D_M":"ORIGINAL_STRUCTURES_SOLVED_USING_REUSED_G2",
            "Buffalo":{"status":B_STATUS,"provider_calls":0,"native_model":None,
                       "second_decision":"NOT_EXECUTED"},
            "OpenModelica_new_invocations":0,"OpenModelica_G2_reused":12,
            "sample_unit":"ONE_KNOWN_SYNTHETIC_WORLD_TWO_VIEWS_NOT_INDEPENDENT",
            "conditions":results,"scientific_compatibility":"NOT_ESTABLISHED",
            "experimental_policy_owner":POLICY}


def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--o0",required=True,type=Path)
    p.add_argument("--o1",required=True,type=Path)
    p.add_argument("--d-dir",required=True,type=Path)
    p.add_argument("--m-dir",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    need(not args.out.exists(),"E02_REFUSE_OVERWRITE")
    args.out.mkdir(parents=True)
    views=[json.loads(x.read_text(encoding="utf-8")) for x in (args.o0,args.o1)]
    result=run(*views,args.d_dir,args.m_dir,args.out/"e02_ledger.sqlite")
    (args.out/"report.json").write_bytes(canonical(result)+b"\n")
    print(json.dumps({"status":result["status"],"provider_calls":0,
                      "D_M_six_by_two":True,"new_omc":0},sort_keys=True))


if __name__=="__main__":
    main()
