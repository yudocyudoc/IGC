"""R2 PT-03: bounded second D/M decisions from their OWN real R1 traces.

D has no new reset-trial observation: maintain all six alternatives, not D2.
M re-applies its original M3 fixed-template thresholds and may stay ABSTAIN.
These are explicit deterministic-policy dispositions, NOT autonomous new models.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path

from scripts.arena_m3_select import decide as original_m3_decide
from scripts.arena_r1_buffalo_postonly import SHARED_SOURCE
from scripts.arena_r2_memory_first_cut import MIGRATION, load_dossier, snapshot
from scripts.arena_v0_contract import canonical, digest
from scripts.ledger import Ledger

SCHEMA="igc-arena-r2-d-m-own-policy-decision/0.1"
D_METHOD="D_R1_FINITE_ALTERNATIVES_CONSERVATIVE_RETAIN/0.1"
M_METHOD="ORIGINAL_M3_FIXED_E1_ABSTAIN_REEVALUATED/0.1"
TIMES=[0,1,2,4]


def check(ok,code):
    if not ok:
        raise ValueError(code)


def numeric_rmse(pred, obs):
    check(isinstance(pred,list) and len(pred)==len(obs),"R2_OWN_SERIES_LENGTH")
    check(all(type(x) in (int,float) and math.isfinite(x) for x in pred),
          "R2_OWN_NONFINITE")
    return math.sqrt(sum((float(a)-float(b))**2 for a,b in zip(pred,obs))/len(obs))


def own_decisions(folder):
    manifest, visible, packets, _native = load_dossier(folder)
    check(visible["source_snapshot_hash"]==SHARED_SOURCE,"R2_OTHER_PRIMARY_SOURCE")
    observations=visible["construction"]["observations"]
    check([x["t"] for x in observations]==TIMES,"R2_PRIMARY_OBSERVATION_TIMES_DRIFT")
    obs=[x["delivered"] for x in observations]
    check(len(packets["D"]["r1_candidates"])==6 and
          len(packets["M"]["r1_candidates"])==3,"R2_OWN_CANDIDATE_COUNT")
    ditems=packets["D"]["r1_candidates"]
    dproof=[]
    for item in ditems:
        g2,g3=item["g2"],item["g3"]
        check(g2["status"]=="G2_MASS_BALANCE_PASS_NOT_G3" and
              g3["status"]=="DESCRIPTIVE_ONLY_NO_INSTRUMENT_BOUND" and
              g3["parameter_status"]=="DECLARED_NOMINAL_VALUES_NOT_FITTED" and
              g3["times_hours"]==TIMES and
              abs(numeric_rmse(g3["predicted_delivered_items"],obs)-
                  g3["rmse_all_items"])<1e-9,
              "R2_D_TRACE_OR_G3_NOT_AUTHENTIC")
        dproof.append({"candidate_id":item["candidate_id"],
                       "own_csv_sha256":item["csv_sha256"],
                       "own_structure_sha256":item["structure_sha256"],
                       "own_rmse_construction_items":g3["rmse_all_items"]})
    check(len(set(x["candidate_id"] for x in dproof))==6 and
          len(set(x["own_structure_sha256"] for x in dproof))==6,
          "R2_D_DUPLICATE_ALTERNATIVE")
    d={
        "schema":SCHEMA,"arm_id":"D","iteration":1,
        "source_snapshot_hash":SHARED_SOURCE,
        "parent_state_sha256":digest(packets["D"]),
        "policy":D_METHOD,"decision":"RATIFY_SIX_ALTERNATIVES",
        "hypothesis_ids_retained":[x["candidate_id"] for x in dproof],
        "chosen_parent":None,
        "own_evidence":dproof,
        "rationale":"Six own models have valid R1 physical traces; different nominal parameters and no measurement-error bound or new independent reset-trial measurement prevent adjudicating a true structure. The smallest construction RMSE is descriptive only.",
        "structural_change":False,"parameter_change":False,
        "new_observations":False,"new_solver_runs":0,
        "new_hypotheses":0,"d2_applied":False,
        "limitation":"DETERMINISTIC_CONSERVATION_POLICY_NOT_AUTONOMOUS_D2_REVIEW"}
    mitems=packets["M"]["r1_candidates"]
    scores=[]
    for n,item in enumerate(mitems):
        g2,g3=item["g2"],item["g3"]
        check(item["candidate_id"]==f"C{n:02d}" and
              g2["status"]=="REAL_SOLVER_CSV_CHECKED" and
              g2["max_material_balance_residual"]<=0.015 and
              g3["status"]=="CONSTRUCTION_FIXED_PARAMETER_ONLY" and
              g3["parameter_status"]=="FIXED_NOT_FITTED" and
              abs(numeric_rmse(g3["predicted_delivered_items"],obs)-
                  g3["rmse_all_items"])<1e-9,
              "R2_M_OWN_TRACE_OR_PARAMETER_POLICY_CHANGED")
        scores.append({"id":item["candidate_id"],"material_queues":n+2,
                       "rmse_items":g3["rmse_all_items"],
                       "trace_sha256":item["csv_sha256"]})
    recomputed=original_m3_decide(scores,min_gap=0.035,max_best=0.02)
    prev=packets["M"]["r1_decision"]
    check(recomputed["status"]==prev["status"]=="ABSTAIN" and
          recomputed["reason"]==prev["reason"] and
          recomputed["chosen_id"]==prev["chosen_id"] is None and
          abs(recomputed["margin"]-prev["gap_items"])<1e-9,
          "R2_M_NATIVE_POLICY_CHANGED_OR_FALSE_SELECTION")
    m={
        "schema":SCHEMA,"arm_id":"M","iteration":1,
        "source_snapshot_hash":SHARED_SOURCE,
        "parent_state_sha256":digest(packets["M"]),
        "policy":M_METHOD,"decision":"RATIFY_ABSTENTION",
        "underlying_native_status":recomputed["status"],
        "chosen_parent":None,
        "own_evidence":scores,"native_reason":recomputed["reason"],
        "best_rmse_items":min(x["rmse_items"] for x in scores),
        "predeclared_max_best_rmse_items":0.02,
        "predeclared_min_gap_rmse_items":0.035,
        "rationale":"Reapplication of the unchanged original M3 decision rule to its three own archived construction traces; every fixed-parameter structure misses the admissibility RMSE. No selected parent and no new parameter search.",
        "structural_change":False,"parameter_change":False,
        "new_observations":False,"new_solver_runs":0,
        "new_hypotheses":0,"m2_applied":False,
        "limitation":"DETERMINISTIC_RATIFICATION_NO_NEW_MOLECULAR_INFERENCE"}
    return {"schema":"igc-arena-r2-pt03-own-second-decisions/0.1",
            "case_id":manifest["investigation_id"],
            "round_id":manifest["round_id"],"source_snapshot_hash":SHARED_SOURCE,
            "d":d,"m":m,"b":"PENDING_REAL_REVIEW_NOT_SIMULATED",
            "new_provider_calls":0,"new_solver_runs":0,
            "no_cross_arm_ranking":True,"holdout":"NOT_ACCESSED"}


def persist(db, folder, decisions, *, prior_cut, recorded_at):
    from scripts.arena_atms import _utc
    check(_utc(recorded_at)>_utc(prior_cut),"R2_DECISION_MUST_FOLLOW_FEEDBACK_PREPARATION")
    expected=own_decisions(folder)
    check(decisions==expected,"R2_DECISIONS_ALTERED_FROM_OWN_R1_POLICY")
    case=expected["case_id"]
    ledger=Ledger(db,MIGRATION)
    prior=ledger.snapshot(case_id=case,as_known_at=prior_cut)
    for lane in ("D","M"):
        check(any(r.entity_id=="arena:r2:"+case+":"+lane+":r2-packet-prepared"
                  and r.access_policy=="lane:"+lane for r in prior),
              "R2_FEEDBACK_NOT_PREPARED_IN_LEDGER")
        check(not any(r.entity_id.endswith(":"+lane+":r2-own-decision") for r in prior),
              "R2_DECISION_ALREADY_IN_PRIOR_CUT")
    receipts={}
    for lane,key in (("D","d"),("M","m")):
        decision=decisions[key]
        base="arena:r2:"+case+":"+lane+":"
        evidence=base+"r2-feedback-used"
        claim=base+"r2-own-decision-supported"
        nodes=[
            ("r2-feedback-used","assumption",{
                "source_id":decision["parent_state_sha256"],
                "meaning":"OWN_R1_TRACES_AND_PRIOR_DECISION_ONLY"}),
            ("r2-policy-applied","assumption",{
                "source_id":digest({"policy":decision["policy"]}),
                "meaning":"CONSERVATIVE_NO_NEW_OBSERVATIONS"}),
            ("r2-own-decision","fact",{
                "decision":decision, "epistemic_status":"DECISION_RECORDED_NOT_MODEL_TRUTH"}),
            ("r2-own-decision-justification","justification",{
                "antecedents":[evidence,base+"r2-policy-applied"],
                "consequent":claim,
                "source_id":digest(decision),
                "epistemic_status":"LOGICAL_SUPPORT_NOT_EMPIRICAL_CAUSAL_VALIDATION"})
        ]
        for name,kind,body in nodes:
            entity=base+name
            payload={"kind":kind,"active":True,"phase":"R2_OWN_POLICY_DECISION",
                     "source_id":decision["parent_state_sha256"],**body}
            revision=ledger.append_revision(
                entity_id=entity,entity_type="ArenaR2Decision",
                case_id=case,actor_id="arena:"+lane+":r2-conservative-policy",
                idempotency_key=entity+":"+digest(payload),
                payload=payload,recorded_at=recorded_at,created_at=recorded_at,
                access_policy="lane:"+lane)
            receipts[name+"_"+lane]={"entity_id":entity,
                                      "integrity_hash":revision.integrity_hash}
        old=snapshot(db,case,prior_cut,lane)
        new=snapshot(db,case,recorded_at,lane)
        check(claim not in old["logical"]["labels"] and
              claim in new["logical"]["labels"] and
              len(new["logical"]["labels"][claim])==1 and
              base+"r2-own-decision" not in old["visible_entities"] and
              base+"r2-own-decision" in new["visible_entities"],
              "R2_ATMS_BEFORE_AFTER_FAILED")
    b_before=snapshot(db,case,prior_cut,"B")
    b_after=snapshot(db,case,recorded_at,"B")
    check(b_before["visible_entities"]==b_after["visible_entities"] and
          b_before["logical"]["labels"]==b_after["logical"]["labels"],
          "R2_B_PRIVATE_VIEW_CHANGED_BY_D_M")
    return {"schema":"igc-arena-r2-pt03-ledger-outcome/0.1","case_id":case,
            "as_known_before":prior_cut,"as_known_after":recorded_at,
            "decisions":{"D":decisions["d"]["decision"],"M":decisions["m"]["decision"],
                         "B":"PENDING"},
            "records":receipts,"b_view_unchanged":True,
            "producer_calls":0,"solver_runs":0,
            "atms_truth_status":"NOT_DETERMINED_BY_ATMS"}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=["decide","persist"])
    p.add_argument("--dossier",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--db",type=Path)
    p.add_argument("--decisions",type=Path)
    p.add_argument("--prior-cut",default="2026-10-27T15:01:00Z")
    p.add_argument("--recorded-at",default="2026-10-27T15:02:00Z")
    args=p.parse_args()
    check(not args.out.exists(),"R2_OUTPUT_EXISTS")
    if args.mode=="decide":
        result=own_decisions(args.dossier)
    else:
        check(args.db is not None and args.decisions is not None,
              "R2_PERSIST_NEEDS_PREPARED_LEDGER")
        result=persist(args.db,args.dossier,
                       json.loads(args.decisions.read_text()),
                       prior_cut=args.prior_cut,recorded_at=args.recorded_at)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_bytes(canonical(result)+b"\n")
    print(json.dumps({"mode":args.mode,"result_hash":digest(result),
                      "B":"PENDING","new_provider_calls":0},sort_keys=True))

if __name__=="__main__":
    main()
