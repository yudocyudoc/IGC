"""R3 PT-06 closure: authentic T1/T2/T3 evidence -> EXISTING F1a/ATMS.

Strictly offline. Read previous genuine original OpenModelica artifacts, reconstruct
existing fixed-M3 and R3 decisions, record their provenance and logical supports.
Synthetic world truths stay case-private (NOT in constructor lane:M).
Replay timestamps are administrative cuts, never historical experiment times.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from scripts.arena_atms import events_from_ledger,project
from scripts.arena_r2_memory_first_cut import MIGRATION,snapshot
from scripts.arena_r3_pt06_parametric import plan,guard
from scripts.arena_r3_pt06_evaluate import evaluate_csv
from scripts.arena_r3_pt06_t1_grade import grade as t1_grade
from scripts.arena_r3_pt06_t23_postonly import audit as t23_audit
from scripts.arena_v0_contract import canonical,digest
from scripts.ledger import Ledger

SCHEMA="igc-arena-r3-pt06-three-case-consolidation/0.1"
ADMIN_CUTS=("2026-10-28T00:00:00Z","2026-10-28T00:01:00Z",
            "2026-10-28T00:02:00Z","2026-10-28T00:03:00Z",
            "2026-10-28T00:04:00Z")
T1_CASE="R3-T1-SHIFTED-REPRESENTABLE"
T2_CASE="R3-T2-EARLY-OBSERVABILITY"
T3_CASE="R3-T3-GRID-INCOMPATIBILITY"
EXPECTED={
    T1_CASE:{"outcome":"ABSTAIN_ADMISSIBLE_GRID_HAS_NO_COMPATIBLE_STRUCTURE",
             "compatible":[],"source":"C00",
             "errors":{"C00":0.035408529,"C01":0.647636771,"C02":1.290101455}},
    T2_CASE:{"outcome":"AMBIGUOUS_MULTIPLE_COMPATIBLE_STRUCTURES",
             "compatible":["C00","C01","C02"],"source":"C01",
             "errors":{"C00":0.0004244567056,"C01":0.0,"C02":0.00003720253870}},
    T3_CASE:{"outcome":"ABSTAIN_ADMISSIBLE_GRID_HAS_NO_COMPATIBLE_STRUCTURE",
             "compatible":[],"source":"C02",
             "errors":{"C00":1.07479901367,"C01":0.43391676961,"C02":0.14383361164}}
}
SOURCE_RUNS={"T1":40578550337,"T2_T3":40582633807}
POSTONLY_RUNS={"T1":40578937420,"T2_T3":40582958825}

def rawhash(path):
    return "sha256:"+sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text())

def inspect(original_t1,original_t23,catalog):
    a,b=Path(original_t1),Path(original_t23)
    cat=read(catalog)
    planned,_=plan()
    guard(read(a/"manifest.json")==planned and
          digest(planned)=="sha256:d33cc4ca8c253226ff50efa6c47e40b9b8c32d0436f370907db2579c9dc0fde5",
          "R3_PT06_FROZEN_27_CANDIDATES_CHANGED")
    # Read and independently recompute the initial selection, not trust a prose summary.
    t1case=read(a/"construction-case.json")
    t1decision=read(a/"r3-decision.json")
    recalculated=evaluate_csv(planned,t1case,a,cat)
    guard(t1decision==recalculated,"R3_T1_DECISION_NOT_REPRODUCIBLE")
    t1truth=read(a/"world-private/provenance.json")
    t1post=read(a/"post-selection-adjudication.json")
    guard(t1_grade(t1case,t1decision,t1truth)==t1post,
          "R3_T1_POST_SELECTION_NOT_REPRODUCIBLE")
    guard(t1case["case_id"]==T1_CASE and
          t1post["world_class_declared_pre_run"]=="C00" and
          t1post["frozen_original_m3_status"]=="ABSTAIN",
          "R3_T1_METHOD_OR_SOURCE_DRIFT")
    later=t23_audit(b,a,cat)
    guard(later["physical_source_run_id"]==SOURCE_RUNS["T2_T3"] and
          later["candidate_CSVs_G2_validated"]==27 and
          later["worlds_G2_validated"]==2 and
          later["new_solver_calls"]==later["new_provider_calls"]==0 and
          later["R4_holdout_accessed"] is False,
          "R3_T23_AUTHENTIC_REPLAY_FAILED")
    cases=[]
    for name,case,decision,post,source_hash,world_hash,run,postrun in [
        (T1_CASE,t1case,t1decision,t1post,rawhash(a/"construction-case.json"),
         t1truth["original_solver_csv_sha256"],SOURCE_RUNS["T1"],POSTONLY_RUNS["T1"]),
        *[(identity,read(b/f"t{i}-construction-only.json"),
           read(b/f"t{i}-decision.json"),later["cases"][i-2],
           rawhash(b/f"t{i}-construction-only.json"),
           later["world_CSV_hashes"][f"T{i}"],SOURCE_RUNS["T2_T3"],POSTONLY_RUNS["T2_T3"])
           for i,identity in ((2,T2_CASE),(3,T3_CASE))]
    ]:
        expected=EXPECTED[name]
        compatible=decision["compatible_material_classes"]
        guard(name==case["case_id"]==decision["case_id"] and
              decision["status"]==expected["outcome"] and
              compatible==expected["compatible"] and
              decision["frozen_m3_original_policy"]["status"]=="ABSTAIN",
              "R3_PT06_PREDECLARED_NEGATIVE_AMBIGUOUS_OUTCOME_CHANGED")
        observed={k:v["rmse_items"] for k,v in decision["per_structure_best"].items()}
        guard(set(observed)==set(expected["errors"]) and
              all(abs(observed[k]-v)<0.000002 for k,v in expected["errors"].items()),
              "R3_PT06_RMSE_CHANGED")
        truth=(post["world_class_declared_pre_run"] if name==T1_CASE else
               post["actual_source_structure_REVEALED_AFTER_SELECTION"])
        guard(truth==expected["source"],"R3_PT06_POSTSELECTION_SOURCE_CHANGED")
        observations=case["construction_observations"]
        guard(len(observations)==4 and
              decision["raw_real_solver_csv_checks"]==27 if name==T1_CASE else
              len(observations)==4 and decision["original_csvs_reused"]==27,
              "R3_PT06_G2_OR_OBSERVATIONS_MISSING")
        guard(decision["independent_holdout"]=="NOT_RUN" if name==T1_CASE
              else decision["future_R4_holdout_accessed"] is False,
              "R3_PT06_RESERVE_EXPOSED")
        cases.append({
          "case_id":name,"source_run":run,"postonly_run":postrun,
          "construction_case_file_sha256":source_hash,
          "construction_observations_digest":digest(observations),
          "construction_observations":observations,
          "original_decision_file_sha256":rawhash(
             a/"r3-decision.json" if name==T1_CASE else
             b/f"t{2 if name==T2_CASE else 3}-decision.json"),
          "original_world_csv_sha256":world_hash,
          "original_M3":{"status":"ABSTAIN",
                         "details":decision["frozen_m3_original_policy"]},
          "R3_grid":{"status":decision["status"],"compatible":compatible,
                     "per_structure_minima":decision["per_structure_best"]},
          "synthetic_source_after_selection_REVIEWER_ONLY":truth,
          "world_G2_status":("G2_SIMULATED_CONDITIONALLY" if name==T1_CASE
                             else post["world_physical_G2"]),
          "world_max_balance_residual_items":(
               t1truth["world_balance_residual_max_items"] if name==T1_CASE
               else post["world_max_material_balance_residual"]),
          "claim_limit":"CONSTRUCTION_GRID_AND_DECLARED_OBSERVATION_WINDOW_ONLY"
        })
    guard([c["case_id"] for c in cases]==[T1_CASE,T2_CASE,T3_CASE],
          "R3_CASE_ORDER_CHANGED")
    return {"schema":SCHEMA,
       "phase":"PT06_R3_THREE_CASES_RECONSTRUCTED_NOT_NEW_EXPERIMENT",
       "manifest_sha256":digest(planned),
       "T23_protocol_sha256":later["protocol_sha256"],
       "case_count":3,"solver_calls_in_consolidation":0,
       "provider_calls_in_consolidation":0,
       "R4_holdout":"NOT_ACCESSED",
       "T1_candidate_simulations_historical":27,
       "new_world_simulations_historical":3,
       "T2_T3_candidate_CSV_reused":27,
       "original_M3_reference":"FROZEN_ORIGINAL_DECIDE_0_020_MAX_0_035_GAP",
       "R3_policy":"PER_CLASS_MINIMUM_WITHIN_FIXED_GRID_0_020",
       "cases":cases,
       "conclusions":{
          "T1":"OFF_GRID_WORLD_BOTH_ABSTAIN_NO_STRUCTURE_SELECTED",
          "T2":"EARLY_WINDOW_ALL_3_COMPATIBLE_M3_ABSTAIN",
          "T3":"SLOW_WORLD_NONE_COMPATIBLE_BOTH_ABSTAIN",
          "general":"FINITE_GRID_CANNOT_ESTABLISH_CAUSAL_STRUCTURE_OR_GENERALIZATION"},
       "not_started":["R4_PT07","REF","Clef","Clairic"],
       "source_artifacts_preserved":True}

def persist(db,result):
    guard(result["schema"]==SCHEMA and
          [x["case_id"] for x in result["cases"]]==
          [T1_CASE,T2_CASE,T3_CASE],"R3_INVALID_CONSOLIDATION_INPUT")
    ledger=Ledger(db,MIGRATION)
    receipts=[]
    for n,item in enumerate(result["cases"],start=1):
        case=item["case_id"]
        prefix="arena:r3:pt06:"+case+":"
        at=ADMIN_CUTS[n]
        def append(key,kind,payload,*,visibility="lane:M",when=at):
            entity=prefix+key
            full={"kind":kind,"active":True,"phase":"PT06_R3_OFFLINE_CONSOLIDATION",
                  "source_id":item["original_decision_file_sha256"],**payload}
            ledger.append_revision(entity_id=entity,entity_type="ArenaR3PT06Evidence",
                case_id=case,actor_id="arena:evaluator:r3-pt06-replay",
                idempotency_key=entity+":"+digest(full),
                payload=full,recorded_at=when,created_at=when,
                access_policy=visibility)
            return entity
        before=snapshot(db,case,ADMIN_CUTS[0],"M")
        guard(not before["visible_entities"],"R3_CASE_PREEXISTED_REPLAY")
        source=append("observed-four-construction-points","assumption",{
            "case_file_sha256":item["construction_case_file_sha256"],
            "observations_digest":item["construction_observations_digest"],
            "construction_observations":item["construction_observations"]})
        prior=append("original-G2-27-candidates","assumption",{
            "original_manifest_sha256":result["manifest_sha256"],
            "source_run":SOURCE_RUNS["T1"],
            "source_candidate_count":27})
        fixed=append("frozen-M3-policy","assumption",{
            "selection_policy":"ORIGINAL_M3_FROZEN_NOT_RETUNED",
            "threshold":0.02,"min_gap":0.035})
        variant=append("bounded-R3-policy","assumption",{
            "selection_policy":"PER_STRUCTURE_ALL_COMPATIBLE_OR_ABSTAIN",
            "threshold":0.02,"grid_candidates":27})
        append("world-G2-physical-existence","fact",{
            "physical_status":item["world_G2_status"],
            "max_mass_balance_residual_items":item["world_max_balance_residual_items"],
            "solver_csv_sha256":item["original_world_csv_sha256"],
            "claim":"REAL_SIMULATION_CONDITIONAL_NOT_EXTERNAL_VALIDATION"})
        append("original-two-decisions","fact",{
            "fixed_M3_status":item["original_M3"]["status"],
            "R3_status":item["R3_grid"]["status"],
            "compatible_material_classes":item["R3_grid"]["compatible"],
            "original_decision_file_sha256":item["original_decision_file_sha256"],
            "epistemic_scope":"DECISION_OUTCOME_NOT_WORLD_TRUTH"})
        append("source-truth-after-grading","fact",{
            "synthetic_world_origin":item["synthetic_source_after_selection_REVIEWER_ONLY"],
            "evidence_scope":"REVIEWER_ONLY_NEVER_PRODUCER_FEEDBACK"},
            visibility="case-private")
        claims={}
        for name,policy in (("original-M3",fixed),("bounded-R3",variant)):
            target=prefix+name+"-decision-supported"
            append(name+"-rule","justification",{
                "antecedents":[source,prior,policy],
                "consequent":target,
                "epistemic_status":"LOGICAL_PROVENANCE_ONLY_NOT_CAUSAL_IDENTIFICATION"})
            claims[name]=target
        after=snapshot(db,case,at,"M")
        guard(all(x in after["logical"]["labels"] and after["logical"]["labels"][x]
                  and x not in before["logical"]["labels"] for x in claims.values()) and
              prefix+"source-truth-after-grading" not in after["visible_entities"],
              "R3_ATMS_TEMPORAL_DECISION_OR_TRUTH_ISOLATION_FAILED")
        db_snapshot=ledger.snapshot(case_id=case,as_known_at=at)
        events=events_from_ledger([
           x for x in db_snapshot if x.access_policy in ("construction-visible","lane:M")])
        engine,manifest=project(events,as_known_at=at,lane="M",investigation_id=case)
        outcome=engine.what_if(disable_assumptions=[variant])
        guard(claims["bounded-R3"] in outcome["changed_nodes"] and
              claims["original-M3"] not in outcome["changed_nodes"] and
              outcome["canonical_mutated"] is False,
              "R3_ATMS_POLICY_COUNTERFACTUAL_FAILED")
        for rival in ("D","B"):
            old=snapshot(db,case,ADMIN_CUTS[0],rival)
            new=snapshot(db,case,at,rival)
            guard(old["visible_entities"]==new["visible_entities"]==[] and
                  old["logical"]["labels"]==new["logical"]["labels"],
                  "R3_PT06_RIVAL_LANE_LEAK")
        receipts.append({"case_id":case,"administrative_replay_time":at,
             "before_M_visible":len(before["visible_entities"]),
             "after_M_visible":len(after["visible_entities"]),
             "M_supported_claims":claims,
             "policy_what_if":{"R3_support_removed":True,
                               "frozen_M3_support_remains":True},
             "synthetic_truth_hidden_from_M":True,"D_B_unchanged":True,
             "ATMS_projection_hash":manifest["projection_hash"]})
    # Aggregation records only source references and already published labels.
    # It is evaluator-private, not a new inference channel into D/B/M.
    case="ARENA-R3-PT06-CONSOLIDATION"
    entity="arena:r3:pt06:reviewer:joint-closure"
    payload={"kind":"fact","active":True,
             "phase":"R3_PT06_JOINT_REVIEW_NO_ADDITIONAL_EXPERIMENT",
             "source_id":digest(result),
             "case_ids":[item["case_id"] for item in result["cases"]],
             "statuses":[item["R3_grid"]["status"] for item in result["cases"]],
             "review":"THREE_SYNTHETIC_CASES_COMPLETE_NOT_CAUSAL_IDENTIFICATION",
             "source_runs":[SOURCE_RUNS["T1"],SOURCE_RUNS["T2_T3"]]}
    ledger.append_revision(entity_id=entity,entity_type="ArenaR3PT06Review",
       case_id=case,actor_id="arena:evaluator:r3-pt06-replay",
       idempotency_key=entity+":"+digest(payload),
       payload=payload,recorded_at=ADMIN_CUTS[4],created_at=ADMIN_CUTS[4],
       access_policy="case-private")
    guard(all(not snapshot(db,case,ADMIN_CUTS[4],lane)["visible_entities"]
              for lane in ("D","B","M")),
          "R3_REVIEWER_AGGREGATE_VISIBLE_TO_CONSTRUCTORS")
    return {"administrative_replay_cuts_NOT_event_times":list(ADMIN_CUTS),
            "case_receipts":receipts,
            "reviewer_only_aggregate_entity":entity,
            "no_cross_arm_sharing":True,
            "ATMS_truth_guarantee":False}

def close(db,original_t1,original_t23,catalog):
    result=inspect(original_t1,original_t23,catalog)
    result["memory"]=persist(db,result)
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original-t1",required=True,type=Path)
    p.add_argument("--original-t23",required=True,type=Path)
    p.add_argument("--catalog",required=True,type=Path)
    p.add_argument("--db",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    guard(not a.db.exists() and not a.out.exists(),"R3_PT06_OVERWRITE_FORBIDDEN")
    result=close(a.db,a.original_t1,a.original_t23,a.catalog)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_bytes(canonical(result)+b"\n")
    print(json.dumps({"status":"R3_PT06_THREE_REAL_CASES_CONSOLIDATED",
                      "statuses":[x["R3_grid"]["status"] for x in result["cases"]],
                      "ATMS_case_receipts":len(result["memory"]["case_receipts"]),
                      "extra_solver_calls":0,"extra_AI_calls":0,
                      "report_sha256":digest(result)},sort_keys=True))

if __name__=="__main__":
    main()
