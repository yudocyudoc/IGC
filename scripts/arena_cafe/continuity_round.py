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
        graph=({"ast":item["original_ast"],
                "canonical_sha256":item["canonical_sha256"]} if arm=="M" else None)
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
    """One scoped before/after revision per D/M condition in existing F1a + ATMS."""
    case=f"E02-{arm}-{condition}"
    anchor=case+":NATIVE_EVIDENCE_ASSUMED"
    rule=case+":REVIEW_SUPPORT"
    knowledge=case+":KNOWLEDGE"
    first=case+":INITIAL"
    second=case+":RETAINED_AMBIGUITY"
    t0=recorded.astimezone(timezone.utc)
    t1=t0+timedelta(microseconds=1)
    stages=[
        (anchor,"ATMSNode",{"kind":"assumption","active":True,
             "assumption_type":"G2_ENGINEERING_NOT_SCIENTIFICALLY_FITTED"},t0,"anchor"),
        (rule,"ATMSNode",{"kind":"justification","active":True,
             "antecedents":[anchor],"consequent":first,"source_id":anchor},t0,"rule0"),
        (knowledge,"KnowledgeItem",{"kind":"knowledge","active":True,
             "node_id":first,"source_id":anchor,
             "title":case+" initial native universe",
             "text":"G2 historical six native candidates, no selection",
             "source_revision":1,"epistemic_status":"ENGINEERING_ONLY"},t0,"knowledge0"),
        (rule,"ATMSNode",{"kind":"justification","active":True,
             "antecedents":[anchor],"consequent":second,"source_id":anchor},t1,"rule1"),
        (knowledge,"KnowledgeItem",{"kind":"knowledge","active":True,
             "node_id":second,"source_id":anchor,
             "title":case+" retained ambiguity after feedback",
             "text":"Own descriptive discrepancies, no epsilon model or native refit",
             "source_revision":2,"epistemic_status":"DESCRIPTIVE_UNRESOLVED"},t1,"knowledge1"),
    ]
    for entity,typ,payload,t,key in stages:
        stamp=t.isoformat()
        ledger.append_revision(entity_id=entity,entity_type=typ,case_id=case,
             actor_id="arena-e02-explicit-policy",idempotency_key=case+":"+key,
             payload=payload,recorded_at=stamp,created_at=stamp,
             access_policy="lane:"+arm)
    cuts=[]
    for t in (t0,t1):
        stamp=t.isoformat()
        rev=ledger.snapshot(case_id=case,as_known_at=stamp)
        eng,projection=project(events_from_ledger(rev),as_known_at=stamp,
                               investigation_id=case,lane=arm)
        kn,events=load_events_from_ledger(Path(ledger.db_path),case,stamp)
        result=retrieve(investigation_id=case,lane=arm,as_known_at=stamp,
                        query="native ambiguity",knowledge_records=kn,
                        atms_events=events)
        cuts.append({"at":stamp,"initial_supported":eng.explain(first)["supported"],
                     "retained_supported":eng.explain(second)["supported"],
                     "visible_knowledge":[x["node_id"] for x in result["items"]],
                     "projection_hash":projection["projection_hash"]})
    if not cuts[0]["initial_supported"] or cuts[0]["retained_supported"] or \
       cuts[1]["initial_supported"] or not cuts[1]["retained_supported"]:
        raise ValueError("E02_MEMORY_NOT_RECONSTRUCTIBLE")
    return {"status":"SCOPED_ATMS_REVISION_DEMONSTRATED_NOT_EMPIRICAL_LEARNING",
            "case_id":case,"cuts":cuts}


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
            memory=_memory(ledger,arm,cond,decision,datetime.now(timezone.utc))
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
