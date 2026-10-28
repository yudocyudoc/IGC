"""PT-08-A offline paired Clef utility design: 3 semantic coverage treatments.

Exactly the SAME genuine T2 construction observations + all 27 original physical
candidate curves in each of the SIX matched numeric-only/numeric+note provider
requests. No Cloudflare calls, no new physics, no hidden source labels in state.
These are THREE treatments of ONE synthetic scenario, not three independent
worlds and not evidence of semantic superiority.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
import math
from pathlib import Path

from scripts.arena_clef_dual_pilot import DESCRIPTIONS
from scripts.arena_r3_pt06_t23_evaluate import archived_candidates,validate_case
from scripts.arena_r3_pt06_t23_preregister import freeze,guard
from scripts.arena_m3_select import sample
from scripts.arena_v0_contract import canonical,digest

SCHEMA="igc-arena-pt08-clef-paired-semantic-gate/0.1"
CASE="R3-T2-EARLY-OBSERVABILITY"
MODEL="@cf/cloudflare/clef"
PAIRS=3
MAX_CALLS=6
CONSTRUCTION_RMSE_LIMIT=0.02
THRESHOLDS={"yes_gte":0.70,"no_lte":0.30,
            "between":"INCONCLUSIVE_KEEP_NOT_EXCLUDED"}
TREATMENTS=(
    ("P01-SCREEN-ONLY",
     "A shift report reproduces the number of finished drinks and the digital pickup display. No one directly watched the movement of physical drinks after dispatch, including any racks or carts.",
     ("C00","C01","C02"),"NO_MATERIAL_TRACE"),
    ("P02-PARTIAL-PHYSICAL",
     "During one dispatch, an observer saw completed drinks placed into a physical holding location before they were collected. Their view ended at that location; they did not follow any downstream movement and cannot rule out another stop.",
     ("C01","C02"),"NONEXHAUSTIVE_AT_LEAST_ONE_MATERIAL_HOLD"),
    ("P03-EXHAUSTIVE-ONE-STAGE",
     "A continuous end-to-end trace followed every completed drink after dispatch: each stopped at one physical holding location, then went straight to collection. The observer explicitly checked and ruled out any second post-dispatch holding location.",
     ("C01",),"EXHAUSTIVE_EXACTLY_ONE_POST_DISPATCH_HOLD"),
)

def build(original_t1,original_t23,catalog):
    frozen=freeze()[0]
    root=Path(original_t1)
    src=Path(original_t23)
    casefile=src/"t2-construction-only.json"
    decisionfile=src/"t2-decision.json"
    case=json.loads(casefile.read_text())
    actual=validate_case(case,frozen)
    guard(case["case_id"]==CASE and
          [x["t"] for x in actual]==[0,0.05,0.10,0.15],
          "PT08_NOT_AUTHENTIC_T2_CONSTRUCTION")
    decision=json.loads(decisionfile.read_text())
    guard(decision["case_id"]==CASE and
          decision["compatible_material_classes"]==["C00","C01","C02"] and
          decision["status"]=="AMBIGUOUS_MULTIPLE_COMPATIBLE_STRUCTURES",
          "PT08_T2_CONSTRUCTION_NOT_AMBIGUOUS")
    manifest,real_rows,index=archived_candidates(root,frozen,catalog)
    guard(len(manifest["candidates"])==len(real_rows)==len(index)==27,
          "PT08_MUST_USE_27_ARCHIVED_REAL_CANDIDATES")
    times=[x["t"] for x in actual]
    values=[x["delivered"] for x in actual]
    numeric_curves={}
    compatible={}
    for candidate in manifest["candidates"]:
        i=candidate["id"]
        curve=sample(real_rows[i],times)
        rmse=math.sqrt(sum((a-b)**2 for a,b in zip(curve,values))/len(times))
        numeric_curves[i]=curve
        if rmse<=CONSTRUCTION_RMSE_LIMIT:
            compatible[i]=candidate["material_class"]
    guard(len(compatible)==27 and
          sorted(set(compatible.values()))==["C00","C01","C02"],
          "PT08_EXPECTS_EVERY_T2_EARLY_CANDIDATE_NUMERIC_COMPATIBLE")
    classes=("C00","C01","C02")
    graph_descriptions={k:DESCRIPTIONS[k] for k in classes}
    base={
       "domain":"closed_E1_material_graph_compatibility_NOT_causal_identification",
       "task":"Evaluate EACH material topology without forcing a winner. The numeric construction data are identical in both paired conditions. If operational evidence does not exhaustively trace physical movement, do not infer the absence of an unobserved storage stage. The probabilities are judgment scores, not causal likelihoods.",
       "candidate_material_classes":graph_descriptions,
       "observed_deliveredTotal_at_hours":actual,
       "fixed_27_physical_candidate_curves_at_same_hours":numeric_curves,
       "construction_RMSE_limit_items":CONSTRUCTION_RMSE_LIMIT,
       "source_curve_status":"ARCHIVED_REAL_OPENMODELICA_G2_VALIDATED",
       "measured_world_truth":"NOT_PROVIDED",
       "reasoning_goal":"IS_MATERIAL_CLASS_STILL_COMPATIBLE_WITH_ALL_GIVEN_EVIDENCE"}
    requests=[]; oracle=[]
    for ident,note,allow,kind in TREATMENTS:
        for condition in ("NUMERIC_ONLY","NUMERIC_PLUS_NOTE"):
            state=dict(base)
            if condition=="NUMERIC_PLUS_NOTE":
                state["operational_note"]=note
                state["operational_note_status"]="SYNTHETIC_AUTHOR_WRITTEN_WITH_KNOWN_SOURCE; NOT_FIELD_MEASUREMENT"
            else:
                state["operational_note"]="NOT_PROVIDED"
                state["operational_note_status"]="NO_SEMANTIC_INFORMATION"
            body={
              "model":"clef",
              "state":canonical(state).decode() if isinstance(canonical(state),bytes) else canonical(state),
              "questions":{"path_"+k:{
                    "type":"noul",
                    "instructions":(
                        "Given only the state, can topology "+k+
                        " remain physically compatible? YES if not specifically contradicted; NO if ruled out. Evaluate independently and preserve ambiguity."
                    )} for k in classes}
            }
            requests.append({"request_id":ident+":"+condition,
                  "paired_case":ident,"condition":condition,
                  "model":MODEL,"body":body})
            oracle.append({"request_id":ident+":"+condition,
                  "declared_information_treatment":kind,
                  "note_based_compatibility":list(allow) if condition=="NUMERIC_PLUS_NOTE" else list(classes),
                  "numeric_baseline_compatibility":list(classes),
                  "truth_claim":"AUTHOR_SYNTHETIC_SCOPE_NOT_BLIND_FIELD_VALIDATION"})
    guard(len(requests)==len(oracle)==MAX_CALLS and
          len({r["request_id"] for r in requests})==MAX_CALLS,
          "PT08_PAIR_OR_BUDGET_CHANGED")
    manifest_doc={
      "schema":SCHEMA,"phase":"FROZEN_REQUESTS_ONLY_NO_MODEL_CALL",
      "source_T2_case_raw_sha256":"sha256:"+sha256(casefile.read_bytes()).hexdigest(),
      "source_T2_decision_raw_sha256":"sha256:"+sha256(decisionfile.read_bytes()).hexdigest(),
      "source_candidate_run_id":40578550337,
      "source_T2_construction_run_id":40582633807,
      "source_27_candidate_csv_sha256":{i["id"]:i["sha256"] for i in index},
      "numeric_policy":"27_E1_CONFIGS_RMSE_LEQ_0_020_ON_T2_FOUR_POINTS",
      "semantic_policy":"ONLY_EXPLICITLY_STATED_PHYSICAL_EVIDENCE_WITH_COVERAGE_SCOPE",
      "original_clef_thresholds":THRESHOLDS,
      "paired_treatments":PAIRS,"provider_requests_planned":MAX_CALLS,
      "new_provider_calls_now":0,"new_solver_calls_now":0,
      "future_provider_authorization":"NOT_GRANTED",
      "instrumental_baseline":"STRONG_DETERMINISTIC_NUMERIC_AND_STRUCTURED_NOTE_ORACLE",
      "primary_metric":"FALSE_EXCLUSION_AND_CONSERVATIVE_SET_ACCURACY_PAIRED",
      "secondary_metric":"POTENTIAL_SIMULATION_PRIORITIZATION_NOT_ACTUAL_SAVING",
      "independence":"THREE_INFORMATION_TREATMENTS_OF_ONE_PUBLIC_SYNTHETIC_WORLD",
      "no_new_architecture":True,"Clairic_used":False,
      "no_private_world_csv_read":True
    }
    return {"schema":SCHEMA,"requests":requests}, {"schema":SCHEMA,"private":oracle},manifest_doc

def emit(out,original_t1,original_t23,catalog):
    out=Path(out)
    guard(not out.exists(),"PT08_PAIR_OUTPUT_ALREADY_EXISTS")
    public,private,manifest=build(original_t1,original_t23,catalog)
    out.mkdir(parents=True)
    (out/"researcher-private").mkdir()
    (out/"public-six-requests-NOT-SENT.json").write_bytes(canonical(public)+b"\n")
    (out/"researcher-private/paired-oracle-NOT-FOR_PROVIDER.json").write_bytes(canonical(private)+b"\n")
    manifest["public_six_request_sha256"]=digest(public)
    manifest["private_oracle_sha256"]=digest(private)
    (out/"manifest.json").write_bytes(canonical(manifest)+b"\n")
    return manifest

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original-t1",type=Path,required=True)
    p.add_argument("--t23",type=Path,required=True)
    p.add_argument("--catalog",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    r=emit(a.out,a.original_t1,a.t23,json.loads(a.catalog.read_text()))
    print(json.dumps({"status":"PT08_CLEF_PAIRED_SIX_REQUESTS_PREPARED_NOT_EXECUTED",
       "number_of_pairs":r["paired_treatments"],
       "provider_calls":r["new_provider_calls_now"],
       "solver_calls":r["new_solver_calls_now"],
       "sha256":r["public_six_request_sha256"]},sort_keys=True))
if __name__=="__main__":
    main()
