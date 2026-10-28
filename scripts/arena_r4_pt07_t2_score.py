"""Prospective R4-A scoring contract only: no future response is generated here.

A separate later physical run must supply the locked-time observation with
auditable original native-model provenance; this evaluator never chooses a
new time, refits parameters or silently substitutes a best-after-reveal model.
"""
from __future__ import annotations
from hashlib import sha256
import json
import math
from pathlib import Path

from scripts.arena_r4_pt07_t2_forecast import (
    SCHEMA,CASE_ID,FUTURE_DECISION_CUTOFF_ITEMS,CLAIM,guard)
from scripts.arena_v0_contract import digest

SOURCE="SYNTHETIC_T2_FRESH_PHYSICAL_RUN_AFTER_LOCK"

def score(lock,observation):
    guard(lock["schema"]==SCHEMA and lock["future_observation_value"] is None
          and lock["predictive_result"]=="NOT_EVALUATED"
          and lock["R4_complete"] is False,
          "R4_LOCK_ALREADY_REVEALED_OR_INVALID")
    guard(type(observation) is dict and set(observation)=={
          "schema","case_id","time_hours","delivered_items","source_kind",
          "original_modelica_sha256","physical_solver_csv_sha256",
          "forecast_lock_file_sha256","collection_status"},
          "R4_UNAUTHORIZED_NEW_OBSERVATION_FIELDS_OR_TRUTH")
    guard(observation["schema"]=="igc-arena-r4-a-t2-one-future-physical-measurement/0.1"
          and observation["case_id"]==lock["protocol"]["case_id"]==CASE_ID
          and observation["time_hours"]==lock["chosen_observation_time_hours"]
          and type(observation["delivered_items"]) in (float,int)
          and math.isfinite(observation["delivered_items"])
          and observation["delivered_items"]>=0
          and observation["source_kind"]==SOURCE
          and observation["collection_status"]=="NEW_SOLVER_RUN_AFTER_LOCK"
          and all(isinstance(observation[x],str) and
                  observation[x].startswith("sha256:") and
                  len(observation[x])==71 for x in (
                    "original_modelica_sha256","physical_solver_csv_sha256",
                    "forecast_lock_file_sha256")),
          "R4_WORLD_VALUE_SOURCE_NOT_AUDITED_OR_WRONG_TIME")
    y=observation["delivered_items"]
    cutoff=lock["protocol"]["future_reduction_cutoff_items"]
    guard(cutoff==FUTURE_DECISION_CUTOFF_ITEMS==0.02,
          "R4_POST_REVEAL_TOLERANCE_CHANGE")
    surviving=[x for x in lock["frozen_compatible_config_predictions"]
                if abs(x["predicted_delivered_items"]-y)<=cutoff]
    survivors=sorted({x["material_class"] for x in surviving})
    before=sorted(lock["compatible_by_structure"])
    guard(before==["C00","C01","C02"] and
          set(survivors)<=set(before),"R4_POST_SELECTION_CLASS_DRIFT")
    status=("NO_STRUCTURE_SURVIVES_NEW_MEASUREMENT" if not survivors
            else "AMBIGUITY_RETAINED" if len(survivors)>1
            else "ONE_STRUCTURE_SURVIVES_CONDITIONALLY")
    pred=lock["equal_structure_weight_point_prediction_items"]
    ref=lock["REF_persistence_prediction_items"]
    return {
      "schema":"igc-arena-r4-a-t2-locked-prediction-evaluation/0.1",
      "scientific_scope":CLAIM,"case_id":CASE_ID,
      "time_hours":lock["chosen_observation_time_hours"],
      "new_world_delivered_items":y,
      "source_physical_solver_csv_sha256":observation["physical_solver_csv_sha256"],
      "frozen_candidate_count":lock["compatible_candidate_count"],
      "surviving_candidate_ids":[x["id"] for x in surviving],
      "surviving_structure_classes":survivors,
      "structures_before":before,"structures_after":survivors,
      "structure_set_reduction_count":len(before)-len(survivors),
      "structural_result":status,
      "prediction_point_equal_structure_medians_items":pred,
      "prediction_point_abs_error_items":abs(pred-y),
      "REF_model":"LAST_OBSERVED_DELIVERED_PERSISTENCE",
      "REF_point_prediction_items":ref,
      "REF_abs_error_items":abs(ref-y),
      "forecast_beats_REF_in_abs_error":abs(pred-y)<abs(ref-y),
      "truth_of_generating_structure_accessed":False,
      "no_parameter_update":True,"no_second_forecast_lock":True,
      "independent_external_holdout":"NOT_ESTABLISHED",
      "causal_structure_recovered":"NOT_DEMONSTRATED_WITHOUT_SEPARATE_ADJUDICATION"
    }

def score_verified_lock(lock_file,hash_file,obs_file):
    lockbytes=Path(lock_file).read_bytes()
    digest_bytes="sha256:"+sha256(lockbytes).hexdigest()
    guard(Path(hash_file).read_text().strip()==digest_bytes,
          "R4_FORECAST_LOCK_INTEGRITY_FAIL")
    lock=json.loads(lockbytes)
    obs=json.loads(Path(obs_file).read_text())
    guard(obs["forecast_lock_file_sha256"]==digest_bytes,
          "R4_FUTURE_OBSERVATION_BEFORE_FORECAST_LOCK_OR_WRONG_LOCK")
    return score(lock,obs)
