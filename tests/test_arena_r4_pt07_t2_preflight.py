"""R4-A preflight: real archived G2 candidates only; no future observations."""
import copy
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
import unittest

from scripts.arena_r4_pt07_t2_forecast import (
  CASE_ID,SCHEMA,CONSTRUCTION_CUTOFF_ITEMS,POSSIBLE_MEASUREMENT_TIMES,
  separation,build,write)
from scripts.arena_r4_pt07_t2_score import score,score_verified_lock,SOURCE
from scripts.arena_v0_contract import canonical,digest

T1=os.environ.get("ARENA_R4_T1_ORIGINAL_DIR")
T23=os.environ.get("ARENA_R4_T23_ORIGINAL_DIR")
CAT="experiments/e0/catalog.json"

@unittest.skipUnless(T1 and T23,"Original T1/T2 physical artifacts required")
class RealT2Forecast(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lock=build(T1,T23,json.loads(Path(CAT).read_text()))

    def test_all_compatible_grid_members_not_only_one_per_topology(self):
        f=self.lock
        self.assertEqual(f["schema"],SCHEMA)
        self.assertEqual(f["protocol"]["case_id"],CASE_ID)
        self.assertEqual(f["protocol"]["construction_compatibility_RMSE_cutoff_items"],
                         CONSTRUCTION_CUTOFF_ITEMS)
        self.assertEqual(len(f["construction_RMSE_all_27"]),27)
        self.assertEqual(len(f["original_csv_sha256_index"]),27)
        self.assertEqual(len(f["frozen_compatible_config_predictions"]),
                         f["compatible_candidate_count"])
        self.assertEqual(f["compatible_candidate_count"],
                         sum(len(v) for v in f["compatible_by_structure"].values()))
        self.assertEqual(sorted(f["compatible_by_structure"]),["C00","C01","C02"])
        self.assertTrue(all(x["construction_RMSE_items"]<=0.020
                            for x in f["frozen_compatible_config_predictions"]))
        scored={x["id"] for x in f["construction_RMSE_all_27"]
                if x["construction_RMSE_items"]<=0.020}
        self.assertEqual(scored,
            {x["id"] for x in f["frozen_compatible_config_predictions"]})
        self.assertEqual(set(f["compatible_by_structure"]["C01"]) & scored,
                         set(f["compatible_by_structure"]["C01"]))
        self.assertEqual(f["future_observation_value"],None)
        self.assertEqual(f["predictive_result"],"NOT_EVALUATED")
        self.assertFalse(f["R4_complete"])
        self.assertEqual(f["physical_candidate_solver_runs_new"],0)
        self.assertEqual(f["provider_calls_new"],0)
        self.assertNotIn("world-private",json.dumps(f))
        self.assertNotIn("synthetic_source_class",json.dumps(f))
        self.assertNotIn("true_world",json.dumps(f))

    def test_chosen_time_deterministic_predicted_separation_and_REF(self):
        f=self.lock
        self.assertEqual(
          [x["time_hours"] for x in f["candidate_times_scored_before_new_observation"]],
          list(POSSIBLE_MEASUREMENT_TIMES))
        selected=max(f["candidate_times_scored_before_new_observation"],
            key=lambda x:(x["separation"]["min_pairwise_envelope_gap_items"],
              x["separation"]["min_pairwise_median_gap_items"],-x["time_hours"]))
        self.assertEqual(f["chosen_observation_time_hours"],selected["time_hours"])
        self.assertGreater(f["chosen_observation_time_hours"],0.15)
        self.assertGreaterEqual(f["equal_structure_weight_point_prediction_items"],0)
        self.assertGreaterEqual(f["REF_persistence_prediction_items"],0)
        self.assertEqual(f["protocol"]["prediction_reference_model"],
                         "LAST_OBSERVED_DELIVERED_PERSISTENCE")
        self.assertFalse(f["protocol"]["REF_is_D_arm"])
        self.assertTrue(f["protocol"]["no_parameter_refitting_after_new_measurement"])
        self.assertEqual(f["protocol"]["independent_external_holdout"],
                         "NOT_ESTABLISHED")
        self.assertEqual(build(T1,T23,json.loads(Path(CAT).read_text())),f)

    def test_seal_hash_replay_and_cannot_overwrite_or_add_truth(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"sealed"
            r=write(out,T1,T23,json.loads(Path(CAT).read_text()))
            self.assertEqual(r,self.lock)
            raw=(out/"forecast-lock.json").read_bytes()
            self.assertEqual("sha256:"+sha256(raw).hexdigest(),
                             (out/"forecast-lock.sha256").read_text().strip())
            with self.assertRaisesRegex(ValueError,"R4_FORECAST_LOCK_ALREADY_EXISTS"):
                write(out,T1,T23,json.loads(Path(CAT).read_text()))
            obs=self.observation()
            obs["forecast_lock_file_sha256"]="sha256:"+sha256(raw).hexdigest()
            path=out/"future.json"
            path.write_bytes(canonical(obs)+b"\n")
            result=score_verified_lock(out/"forecast-lock.json",
                                       out/"forecast-lock.sha256",path)
            self.assertEqual(result["REF_model"],
                "LAST_OBSERVED_DELIVERED_PERSISTENCE")
            (out/"forecast-lock.sha256").write_text("sha256:"+"f"*64)
            with self.assertRaisesRegex(ValueError,"R4_FORECAST_LOCK_INTEGRITY_FAIL"):
                score_verified_lock(out/"forecast-lock.json",
                                    out/"forecast-lock.sha256",path)

    def observation(self):
        return {
          "schema":"igc-arena-r4-a-t2-one-future-physical-measurement/0.1",
          "case_id":CASE_ID,
          "time_hours":self.lock["chosen_observation_time_hours"],
          "delivered_items":0.42, # UNIT TEST INPUT ONLY: not a claimed R4 observation.
          "source_kind":SOURCE,
          "original_modelica_sha256":"sha256:"+"a"*64,
          "physical_solver_csv_sha256":"sha256:"+"b"*64,
          "forecast_lock_file_sha256":"sha256:"+"c"*64,
          "collection_status":"NEW_SOLVER_RUN_AFTER_LOCK"
        }

    def test_compatibility_set_can_narrow_fail_or_remain_ambiguous_no_retraining(self):
        f=self.lock
        o=self.observation()
        for desired in (0.0,0.42,100.0):
            o["delivered_items"]=desired
            result=score(f,o)
            surviving={x["id"] for x in f["frozen_compatible_config_predictions"]
                       if abs(x["predicted_delivered_items"]-desired)<=0.020}
            self.assertEqual(set(result["surviving_candidate_ids"]),surviving)
            self.assertFalse(result["truth_of_generating_structure_accessed"])
            self.assertTrue(result["no_parameter_update"])
            self.assertIn(result["structural_result"],[
                "NO_STRUCTURE_SURVIVES_NEW_MEASUREMENT",
                "AMBIGUITY_RETAINED","ONE_STRUCTURE_SURVIVES_CONDITIONALLY"])
        self.assertFalse(score(f,{**o,"delivered_items":100.0})[
            "surviving_structure_classes"])

    def test_fail_closed_new_time_new_model_truth_or_invalid_cutoff(self):
        o=self.observation()
        for change in ("truth","different-time","no-receipt","negative","garbage"):
            x=copy.deepcopy(o)
            if change=="truth":x["generator_true_structure"]="C01"
            if change=="different-time":x["time_hours"]=0.15
            if change=="no-receipt":x["collection_status"]="OLD_WORLD_CASE"
            if change=="negative":x["delivered_items"]=-1.0
            if change=="garbage":x["source_kind"]="NO_SOLVER"
            with self.assertRaises(ValueError):
                score(self.lock,x)
        f=copy.deepcopy(self.lock)
        f["protocol"]["future_reduction_cutoff_items"]=0.8
        with self.assertRaisesRegex(ValueError,"R4_POST_REVEAL_TOLERANCE_CHANGE"):
            score(f,o)

class PureProspectiveRules(unittest.TestCase):
    def test_interval_gap_not_same_as_three_structures_identified(self):
        s={
          "C00":{"lower_items":0,"median_items":1,"upper_items":2},
          "C01":{"lower_items":1,"median_items":3,"upper_items":4},
          "C02":{"lower_items":5,"median_items":6,"upper_items":7},
        }
        self.assertEqual(separation(s)["min_pairwise_envelope_gap_items"],0)
        self.assertFalse(separation(s)["all_pairwise_envelopes_disjoint"])
        with self.assertRaisesRegex(ValueError,"R4_THREE_STRUCTURES_REQUIRED"):
            separation({"C00":s["C00"]})

if __name__=="__main__":
    unittest.main()
