"""PT-07 / R4-A: freeze T2 predictive set BEFORE obtaining another world value.

OFFLINE only. Use existing 27 archived real G2 CSVs; retain *every* grid
configuration compatible with T2 construction at RMSE<=0.020, not merely one
winner per structure. Pick one new observation time from a predetermined list
using ONLY predicted curve separation. Seal predictions and model-free REF
(persistence). No world CSV, synthetic source topology or future response used.

R4-A is an in-family synthetic process check, NOT independent validation.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
from statistics import median

from scripts.arena_m3_select import sample
from scripts.arena_r3_pt06_parametric import plan,guard
from scripts.arena_r3_pt06_t23_preregister import freeze,ORIGINAL_GRID_SHA
from scripts.arena_r3_pt06_t23_evaluate import archived_candidates,validate_case,evaluate
from scripts.arena_v0_contract import canonical,digest

SCHEMA="igc-arena-r4-pt07-t2-forecast-seal/0.1"
PROTOCOL="igc-arena-r4-pt07-t2-prospective-protocol/0.1"
CASE_ID="R3-T2-EARLY-OBSERVABILITY"
SOURCE_RUN=40578550337
CONSTRUCTION_CUTOFF_ITEMS=0.020
FUTURE_DECISION_CUTOFF_ITEMS=0.020  # Policy threshold, NOT measured noise precision.
POSSIBLE_MEASUREMENT_TIMES=(0.5,1.0,1.5,2.5,3.0)  # E1 solver output grid; avoid pulse event t=2.
REF="LAST_OBSERVED_DELIVERED_PERSISTENCE"
CLAIM="SYNTHETIC_IN_FAMILY_PROCESS_CHECK_NOT_INDEPENDENT_PREDICTION"

def sha(path):
    return "sha256:"+sha256(Path(path).read_bytes()).hexdigest()

def _metric(vals):
    guard(len(vals)>0 and all(math.isfinite(x) and x>=0 for x in vals),
          "R4_EMPTY_NONFINITE_OR_NEGATIVE_FORECAST")
    return {"lower_items":min(vals),"median_items":median(vals),
            "upper_items":max(vals),"candidate_count":len(vals)}

def separation(stats):
    """Minimum of all 3 pairwise interval gaps; median gap as fallback ONLY."""
    keys=sorted(stats)
    guard(keys==["C00","C01","C02"],"R4_THREE_STRUCTURES_REQUIRED")
    gaps=[]; median_gaps=[]
    for a,b in (("C00","C01"),("C00","C02"),("C01","C02")):
        x,y=stats[a],stats[b]
        gaps.append(max(0.0,x["lower_items"]-y["upper_items"],
                         y["lower_items"]-x["upper_items"]))
        median_gaps.append(abs(x["median_items"]-y["median_items"]))
    return {"min_pairwise_envelope_gap_items":min(gaps),
            "min_pairwise_median_gap_items":min(median_gaps),
            "all_pairwise_envelopes_disjoint":all(v>0 for v in gaps),
            "pairwise_envelope_gaps_items":gaps}

def _protocol():
    return {
      "schema":PROTOCOL,"phase":"PREDECLARED_PROSPECTIVE_TIME_SELECTION",
      "case_id":CASE_ID,"historical_candidate_run_id":SOURCE_RUN,
      "historical_candidate_grid_sha256":ORIGINAL_GRID_SHA,
      "historical_T2_source_run_id":40582633807,
      "observables":["deliveredTotal"],
      "construction_window_hours":[0,0.05,0.10,0.15],
      "construction_compatibility_RMSE_cutoff_items":CONSTRUCTION_CUTOFF_ITEMS,
      "prospective_candidate_times_hours":list(POSSIBLE_MEASUREMENT_TIMES),
      "chosen_time_rule":"MAX_LEXICOGRAPHIC_MIN_PAIRWISE_ENVELOPE_GAP_THEN_MIN_MEDIAN_GAP_THEN_EARLIEST",
      "compatible_configs_rule":"ALL_27_WITH_CONSTRUCTION_RMSE_LEQ_0_020_NOT_ONLY_BEST_OF_CLASS",
      "prediction_reference_model":REF,
      "point_prediction_rule":"MEDIAN_OF_THREE_TOPOLOGY_MEDIANS_EQUAL_TOPOLOGY_WEIGHT",
      "future_reduction_policy":"KEEP_CLASS_IF_ANY_FROZEN_CONFIG_ABS_ERROR_LEQ_0_020",
      "future_reduction_cutoff_items":FUTURE_DECISION_CUTOFF_ITEMS,
      "future_threshold_status":"OPERATIONAL_CHOICE_NOT_INSTRUMENT_PRECISION",
      "predictions_from_existing_candidate_CSV_ONLY":True,
      "future_real_world_observation":"NOT_AVAILABLE_NOT_READ",
      "future_observation_solver_calls_now":0,
      "candidate_solver_calls_now":0,"provider_calls_now":0,
      "REF_is_D_arm":False,
      "no_parameter_refitting_after_new_measurement":True,
      "no_future_time_selection_after_new_measurement":True,
      "synthetic_t2_generator_public_not_blind":True,
      "independent_external_holdout":"NOT_ESTABLISHED",
      "scientific_scope":CLAIM,
      "R4_conclusion_not_yet_available":True
    }

def build(original_t1,t23,catalog):
    protocol=_protocol()
    root,src=Path(original_t1),Path(t23)
    case_path=src/"t2-construction-only.json"
    prior_path=src/"t2-decision.json"
    case=json.loads(case_path.read_text())
    frozen=freeze()[0]
    obs=validate_case(case,frozen)
    guard(case["case_id"]==CASE_ID and
          [o["t"] for o in obs]==protocol["construction_window_hours"],
          "R4_WRONG_T2_CASE_OR_WINDOW")
    # The previously committed T2 adjudication must be reproducible from
    # construction-only observations. Never open world-private/ or t2_res.csv.
    historical=json.loads(prior_path.read_text())
    recalculated=evaluate(frozen,case,root,catalog)
    guard(historical==recalculated and
          historical["status"]=="AMBIGUOUS_MULTIPLE_COMPATIBLE_STRUCTURES" and
          historical["compatible_material_classes"]==["C00","C01","C02"] and
          historical["frozen_m3_original_policy"]["status"]=="ABSTAIN",
          "R4_T2_ORIGINAL_R3_DECISION_DRIFT")
    manifest,rows,index=archived_candidates(root,frozen,catalog)
    guard(digest(manifest)==ORIGINAL_GRID_SHA and len(index)==27,
          "R4_ORIGINAL_CANDIDATES_CHANGED")
    by_csv={x["id"]:x["sha256"] for x in index}
    measured=[o["delivered"] for o in obs]
    times=[o["t"] for o in obs]
    compatible=[]
    all_construction=[]
    for candidate in manifest["candidates"]:
        ident=candidate["id"]
        predicted=sample(rows[ident],times)
        rmse=math.sqrt(sum((p-y)**2 for p,y in zip(predicted,measured))/len(times))
        item={"id":ident,"material_class":candidate["material_class"],
              "historical_source_csv_sha256":by_csv[ident],
              "construction_RMSE_items":rmse}
        all_construction.append(item)
        if rmse<=CONSTRUCTION_CUTOFF_ITEMS:
            compatible.append(item)
    compatible=sorted(compatible,key=lambda x:x["id"])
    classes={k:[x for x in compatible if x["material_class"]==k]
             for k in ("C00","C01","C02")}
    guard(all(classes.values()),"R4_NO_COMPATIBLE_CONFIG_IN_EVERY_CLASS")
    future=[]
    for t in POSSIBLE_MEASUREMENT_TIMES:
        by_class={cl:_metric([sample(rows[x["id"]],[t])[0] for x in options])
                  for cl,options in classes.items()}
        score=separation(by_class)
        future.append({"time_hours":t,"by_structure":by_class,"separation":score})
    # Select once, based exclusively on those frozen candidate forecasts.
    chosen=max(future,key=lambda x:(
        x["separation"]["min_pairwise_envelope_gap_items"],
        x["separation"]["min_pairwise_median_gap_items"],-x["time_hours"]))
    selected_time=chosen["time_hours"]
    sealed_predictions=[]
    for item in compatible:
        forecast=sample(rows[item["id"]],[selected_time])[0]
        sealed_predictions.append({**item,"predicted_delivered_items":forecast})
    by_class_forecasts={cl:[x["predicted_delivered_items"] for x in sealed_predictions
                            if x["material_class"]==cl] for cl in classes}
    summary={k:_metric(v) for k,v in by_class_forecasts.items()}
    point=median([summary[k]["median_items"] for k in sorted(summary)])
    reference=measured[-1]  # Model-free deterministic persistence.
    guard(selected_time>max(times) and
          sum(x["candidate_count"] for x in summary.values())==len(compatible) and
          set(summary)=={"C00","C01","C02"},
          "R4_FORECAST_CONTAINS_INVALID_SELECTION")
    seal={
       "schema":SCHEMA,"protocol":protocol,"protocol_sha256":digest(protocol),
       "source_case_sha256":sha(case_path),
       "source_decision_sha256":sha(prior_path),
       "construction_data_sha256":digest(obs),
       "source_manifest_sha256":digest(manifest),
       "original_csv_sha256_index":by_csv,
       "compatible_candidate_count":len(compatible),
       "compatible_by_structure":{k:[x["id"] for x in v] for k,v in classes.items()},
       "construction_RMSE_all_27":all_construction,
       "candidate_times_scored_before_new_observation":future,
       "chosen_observation_time_hours":selected_time,
       "chosen_time_evidence":"ONLY_ARCHIVED_CANDIDATE_CSVS_AND_FROZEN_T2_CONSTRUCTION",
       "chosen_time_envelopes_overlap":not chosen["separation"]["all_pairwise_envelopes_disjoint"],
       "frozen_compatible_config_predictions":sealed_predictions,
       "frozen_structure_envelopes":summary,
       "equal_structure_weight_point_prediction_items":point,
       "REF_persistence_prediction_items":reference,
       "future_observation_value":None,
       "original_world_future_solver_run":"NOT_RUN",
       "predictive_result":"NOT_EVALUATED",
       "physical_candidate_solver_runs_new":0,
       "provider_calls_new":0,
       "R4_complete":False,
       "scientific_scope":CLAIM}
    return seal

def write(root,original_t1,t23,catalog):
    root=Path(root)
    guard(not root.exists(),"R4_FORECAST_LOCK_ALREADY_EXISTS")
    seal=build(original_t1,t23,catalog)
    root.mkdir(parents=True)
    locked=canonical(seal)+b"\n"
    (root/"forecast-lock.json").write_bytes(locked)
    (root/"forecast-lock.sha256").write_text(
        "sha256:"+sha256(locked).hexdigest()+"\n")
    print(json.dumps({"status":"R4_A_FORECAST_ONLY_LOCKED_WITHOUT_NEW_RESPONSE",
        "compatible_configs":seal["compatible_candidate_count"],
        "by_structure":{k:len(v) for k,v in seal["compatible_by_structure"].items()},
        "proposed_time_h":seal["chosen_observation_time_hours"],
        "envelopes_overlap":seal["chosen_time_envelopes_overlap"],
        "new_solver_calls":0,"forecast_lock_sha256":"sha256:"+sha256(locked).hexdigest()},
        sort_keys=True))
    return seal

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original-t1",type=Path,required=True)
    p.add_argument("--t23",type=Path,required=True)
    p.add_argument("--catalog",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    write(a.out,a.original_t1,a.t23,json.loads(a.catalog.read_text()))

if __name__=="__main__":
    main()
