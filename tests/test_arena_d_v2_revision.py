"""D2: revised own-arm hypotheses after an independent synthetic reset observation.

Unit fixtures use mathematical observations; real OpenModelica is required by CI.
"""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.arena_atms import ATMS
from scripts.arena_v0_contract import INPUT_SCHEMA, digest, trace_event
from scripts.arena_d_v01 import generate
from scripts.arena_d_v1_screen import assess, integrate
from scripts.arena_d_atms_bridge import (
    BridgeError, MIGRATION, _store, snapshot, _logical_record
)
from scripts.arena_d_v2_revision import (
    TRIAL_SCHEMA, revise, validate_trial, run, extract_reset_observation
)
from scripts.ledger import Ledger

STAMP0="2026-10-25T18:00:00-06:00"
STAMP1="2026-10-25T19:00:00-06:00"


def visible():
    return {
      "schema":INPUT_SCHEMA, "investigation_id":"D2-UNIT",
      "round_id":"R0", "question":"Independent reset and mechanism revision",
      "source_snapshot_hash":"sha256:"+"1"*64, "iteration_limit":2,
      "construction":{
        "input_profile":{"kind":"pulse","rate":1.7,"duration":2},
        "nominal_parameters":{"capacity":2,"response_time":1,"loss_time":3},
        "observations":[{"t":0,"delivered":0},{"t":1,"delivered":0.35},
                        {"t":2,"delivered":1.1},{"t":4,"delivered":2.5}]
      },
      "observability":{"stock_unit":"items","time_unit":"hour",
                       "observable":"cumulative_delivered"},
      "resources":{"max_stocks":3,"allow_loss":True,"max_candidates":6,
                   "max_simulations":6}
    }


def protocol():
    return {
      "schema":"igc-d-observation-screen/0.1","noise_absolute_bound":.2,
      "parameter_grid":{"capacity":[1.2,2,2.8],
                        "response_time":[.5,1,1.5],
                        "loss_time":[1.5,3,6]},
      "max_grid_evaluations":140,"integration_max_step":.02,
      "new_trial_sample_times":[.25,.5,.75,1,1.25,1.5,2,2.5,3,4,6,8]
    }


def trial(data, protocol, prior, *, delivered=None):
    time=prior["next_measurement"]["suggested_measurement_time"]
    if delivered is None:
        delivered=integrate(2,False,{"capacity":2,"response_time":1,
                                     "loss_time":3},
                            data["construction"]["input_profile"],
                            [time],.02)[0]
    return {
      "schema":TRIAL_SCHEMA,
      "kind":"INDEPENDENT_SYNTHETIC_RESET",
      "input_hash":prior["input_hash"],
      "d1_screen_hash":digest(prior),
      "pulse":data["construction"]["input_profile"],
      "measurement":{"t":time,"delivered":round(delivered,9)},
      "source_csv_hash":"sha256:"+"a"*64,
      "epistemic_status":"SYNTHETIC_OBSERVATION_NOT_GROUND_TRUTH"
    }


def seed_ledger(db, data, before, at=STAMP0):
    ledger=Ledger(db,MIGRATION)
    case_id,round_id=data["investigation_id"],data["round_id"]
    enum=generate(data)
    d0=trace_event(arm_id="D",round_id=round_id,
                   event_type="HYPOTHESIS_PROPOSED",iteration=0,
                   source_hash=enum["input_hash"],payload_hash=digest(enum))
    d1=trace_event(arm_id="D",round_id=round_id,
                   event_type="SIMULATION_REPORTED",iteration=0,
                   source_hash=enum["input_hash"],payload_hash=digest(before),
                   previous_event_hash=d0["event_hash"])
    def store(entity_type,key,payload):
        return _store(ledger,case_id=case_id,round_id=round_id,
                      recorded_at=at,entity_type=entity_type,
                      key=key,payload=payload)
    store("ArenaDNativeBundle","d0:bundle",enum)
    store("ArenaDScreen","d1:screen",before)
    store("ArenaTraceEnvelope","trace:0:"+d0["event_hash"][7:19],
          {"kind":"trace",**d0})
    store("ArenaTraceEnvelope","trace:1:"+d1["event_hash"][7:19],
          {"kind":"trace",**d1})
    for id in ("DOBS","DINSTR","DGRID"):
        store("ArenaATMSNode","logic:"+id,_logical_record(
            kind="assumption",id=id,case_id=case_id,
            source_id=d1["event_hash"]))
    for id in before["eligible_ids"]:
        key="DSTRUCT:"+id
        store("ArenaATMSNode","logic:"+key,_logical_record(
            kind="assumption",id=key,case_id=case_id,
            source_id=d0["event_hash"]))
        store("ArenaATMSNode","logic:DWITNESS:"+id,_logical_record(
            kind="justification",id="DWITNESS:"+id,
            case_id=case_id,source_id=d1["event_hash"],
            antecedents=["DSTRUCT:"+id,"DOBS","DINSTR","DGRID"],
            consequent="DCOMPATIBLE:"+id))
    return d0,d1


class DeterministicD2RevisionTests(unittest.TestCase):
    def test_precommitted_design_is_independent_reset(self):
        data=visible()
        p=protocol()
        prior=assess(data,p)
        self.assertEqual(len(prior["eligible_ids"]),2)
        self.assertEqual(prior["next_measurement"]["suggested_measurement_time"],8)
        t=trial(data,p,prior)
        self.assertEqual(validate_trial(data,p,prior,t)["t"],8)

    def test_new_trial_revises_support_without_claiming_causes(self):
        data,p=visible(),protocol()
        before=assess(data,p)
        with tempfile.TemporaryDirectory() as temp:
            db=Path(temp)/"ledger.db"
            seed_ledger(db,data,before)
            memory=snapshot(db=db,case_id=data["investigation_id"],
                            round_id=data["round_id"],as_known_at=STAMP0)
            revised=revise(data=data,protocol=p,prior=before,atms_snapshot=memory,
                           trial=trial(data,p,before))
            self.assertEqual(len(before["eligible_ids"]),2)
            self.assertEqual(len(revised["conditionally_supported_ids"]),1)
            self.assertEqual(revised["conclusion"],
                             "ONE_REMAINS_OTHER_MODELS_UNRESOLVED")
            self.assertEqual(revised["revision_kind"],
                             "PARAMETER_AND_SUPPORT_UPDATE_NO_TOPOLOGY_GENERATION")
            self.assertTrue(revised["no_structural_falsification"])
            self.assertTrue(all(not item["structure_changed"]
                                for item in revised["results"]))

    def test_unexplained_outlier_returns_no_joint_witness_not_falsification(self):
        data,p=visible(),protocol()
        before=assess(data,p)
        with tempfile.TemporaryDirectory() as temp:
            db=Path(temp)/"ledger.db"
            seed_ledger(db,data,before)
            memory=snapshot(db=db,case_id=data["investigation_id"],
                            round_id=data["round_id"],as_known_at=STAMP0)
            revised=revise(data=data,protocol=p,prior=before,
                           atms_snapshot=memory,trial=trial(data,p,before,delivered=99))
            self.assertEqual(revised["conditionally_supported_ids"],[])
            self.assertEqual(revised["conclusion"],
                             "NO_JOINT_GRID_WITNESS_INSUFFICIENT_TO_REFUTE")
            self.assertTrue(revised["no_structural_falsification"])

    def test_reject_gold_other_lane_changed_trial_and_posthoc_time(self):
        data,p=visible(),protocol()
        prior=assess(data,p)
        for mutate in (
            lambda t: t.update(gold="secret"),
            lambda t: t.update(other_arm_result="M"),
            lambda t: t["measurement"].update(t=7.),
            lambda t: t.update(input_hash="sha256:"+"b"*64),
            lambda t: t.update(source_csv_hash="sha256:not-a-valid-hash"),
        ):
            candidate=trial(data,p,prior)
            mutate(candidate)
            with self.subTest(candidate=candidate),self.assertRaises(BridgeError):
                validate_trial(data,p,prior,candidate)

    def test_reject_unexpected_history_and_atms_mismatch(self):
        data,p=visible(),protocol()
        prior=assess(data,p)
        with tempfile.TemporaryDirectory() as temp:
            db=Path(temp)/"ledger.db"
            seed_ledger(db,data,prior)
            memory=snapshot(db=db,case_id=data["investigation_id"],
                            round_id=data["round_id"],as_known_at=STAMP0)
            wrong=copy.deepcopy(memory)
            wrong["conditionally_supported"]=[]
            with self.assertRaisesRegex(BridgeError,"ATMS_PRIOR_SUPPORT_MISMATCH"):
                revise(data=data,protocol=p,prior=prior,atms_snapshot=wrong,
                       trial=trial(data,p,prior))
            wrong=copy.deepcopy(prior)
            wrong["results"][0]["status"]="FALSIFIED"
            with self.assertRaisesRegex(BridgeError,"HISTORICAL_D1_NOT_REPRODUCIBLE"):
                revise(data=data,protocol=p,prior=wrong,atms_snapshot=memory,
                       trial=trial(data,p,prior))

    def test_persistent_revision_chain_and_historical_atms(self):
        data,p=visible(),protocol()
        prior=assess(data,p)
        with tempfile.TemporaryDirectory() as temp:
            db=Path(temp)/"ledger.db"
            _,d1=seed_ledger(db,data,prior)
            result=run(db=db,data=data,protocol=p,trial=trial(data,p,prior),
                       recorded_at=STAMP1)
            after=result["atms_after"]
            current=result["current_support"]
            self.assertEqual(len(current),1)
            self.assertEqual(result["d2_trace_event"]["previous_event_hash"],d1["event_hash"])
            self.assertEqual(result["d2_trace_event"]["iteration"],1)
            self.assertTrue(after["truth_status"]=="NOT_DETERMINED_BY_ATMS")
            self.assertEqual(len(after["conditionally_supported"]),2,
                             "D1 history is not overwritten")
            historical=snapshot(db=db,case_id=data["investigation_id"],
                                round_id=data["round_id"],as_known_at=STAMP0)
            self.assertFalse(any(x.startswith("D2CURRENT:") for x in
                                 historical["logical_state"]["labels"]))
            self.assertEqual(len(historical["conditionally_supported"]),2)
            with self.assertRaisesRegex(BridgeError,"D2_ALREADY_RECORDED_FOR_ROUND"):
                run(db=db,data=data,protocol=p,trial=trial(data,p,prior),
                    recorded_at="2026-10-25T20:00:00-06:00")

    def test_missing_own_ledger_history_fails(self):
        data,p=visible(),protocol()
        with tempfile.TemporaryDirectory() as temp:
            db=Path(temp)/"ledger.db"
            Ledger(db,MIGRATION)
            with self.assertRaisesRegex(BridgeError,"MISSING_OR_CORRUPTED_D_HISTORY"):
                run(db=db,data=data,protocol=p,trial=trial(data,p,assess(data,p)),
                    recorded_at=STAMP1)


if __name__=="__main__":
    unittest.main()
