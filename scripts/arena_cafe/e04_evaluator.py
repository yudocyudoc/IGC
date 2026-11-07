"""E04 evaluator-only historical F4 adjudication, separate from producer job.

The F4 artifact is historical known-control, NOT a new independent reserve.
No new DES or solver and never sends pair/outcome fields to the producer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from scripts.arena_v0_contract import canonical
from scripts.arena_cafe.native_handoff import need

SCHEMA="igc-arena-e04-known-pair-evaluator/0.1"


def adjudicate(producer, f4):
    need(producer["schema"]=="igc-arena-e04-action-capability-producer/0.1"
         and producer["E05_gate"]=="BLOCKED_NO_ADMISSIBLE_LOCAL_ACTION_PREDICTION"
         and producer["B"]["provider_calls"]==0,
         "E04_INVALID_PRODUCER_PACKET")
    # Pin the historical artifact's canonical bytes, not transcribed outputs.
    need(hashlib.sha256(canonical(f4)).hexdigest()==
         "25511a5c2c34782a653738586f9d7b8fe5aa33575a2fbb20fc5050dab1568d2c",
         "E04_HISTORICAL_REFERENCE_BYTES_DIFFER")
    need(f4["schema"]=="igc-arena-f4-latent-downstream-structural-symmetry/0.1"
         and f4["source_o0_hash"]==producer["public_source_hash"]
         and f4["not_an_independent_test"] is True
         and f4["proof"]["all_15_exact_terminal_delivery_times_identical"] is True
         and f4["swap_proven_for_all_arrival_schedules_under_declared_assumptions"] is True
         and f4["proof"]["commutation_claim_scope"]==
             "TWO_SINGLE_SERVER_CONSTANT_SERVICE_FCFS_UNLIMITED_BUFFER_STAGES"
         and len(f4["counterfactual_delivered_at_t10"])==2
         and abs(f4["counterfactual_delivered_at_t10"]["REFERENCE_EV01_WORLD_A"]-
                 f4["counterfactual_delivered_at_t10"]["SWAPPED_DOWNSTREAM_WORLD_B"])==
                 f4["absolute_counterfactual_gap_orders_t10"]==2
         and f4["original_O0_and_O1_compatible_for_BOTH_mechanisms"] is True,
         "E04_ORIGINAL_F4_IDENTITY_NOT_VERIFIED")
    for arm,total in (("D",81),("M",54)):
        a=producer["arms"][arm]
        need(a["attempted"]==a["not_representable"]==total and
             a["mapped"]==a["conditional_approximations"]==0 and
             all(x["predicted_action_effect"] is None for x in a["candidates"]),
             "E04_FALSE_ACTION_MAPPING")
    return {"schema":SCHEMA,
            "status":"KNOWN_F4_PAIR_VERIFIED_E04_REPRESENTATION_GAP_PARTIAL",
            "provenance":"F4_PR152_HISTORICAL_DEVELOPMENT_NOT_NEW_DATA",
            "reference_worlds":2,"same_O0_O1_and_all_15_terminal_events":True,
            "evaluator_action":"ADD_30_SECONDS_SERVICE_WORK_PER_ORDER_AT_DISPATCH_FROM_T0",
            "known_evaluator_action_effect_t10":{
                "A":f4["counterfactual_delivered_at_t10"]["REFERENCE_EV01_WORLD_A"],
                "B":f4["counterfactual_delivered_at_t10"]["SWAPPED_DOWNSTREAM_WORLD_B"]},
            "known_difference_t10_orders":2,
            "native_predictions_not_available":{"D":81,"M":54,"B":"NO_NATIVE"},
            "producer_received_evaluator_reference":False,
            "producer_environment":"APPLICATION_PROCEDURAL_SEPARATION_NOT_NETWORK_ISOLATION",
            "numerical_action_prediction_for_D_B_M":"NOT_COMPUTABLE",
            "false_uniqueness_claim":False,
            "no_new_des_or_omc":True,"no_provider":True,
            "S1_dispatch_t6":"NOT_PROVIDED_TO_PRODUCER_NOT_MEASURED_SENSOR",
            "terminal_demand_pulse_discrimination":"IMPOSSIBLE_WITHIN_F4_FIFO_COMMUTATION_CLASS",
            "E05_gate":"BLOCKED_NO_ADMISSIBLE_LOCAL_ACTION_PREDICTION",
            "G4":"NOT_RUN","G5":"NOT_RUN"}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--producer",required=True,type=Path)
    p.add_argument("--f4",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    need(not a.out.exists(),"E04_REFUSE_OVERWRITE")
    result=adjudicate(json.loads(a.producer.read_text()),json.loads(a.f4.read_text()))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_bytes(canonical(result)+b"\n")
    print(json.dumps({"status":result["status"],"E05":result["E05_gate"]},sort_keys=True))
if __name__=='__main__':main()