#!/usr/bin/env python3
"""CAF-02 evaluator DES source: fixed-contract preflight, NOT campaign runner.

Reuses only the generic discrete-event calendar implementation in CAF-01,
never its observations, parameters, historical holdout, G5 waiver or runs.
No M/D imports, no producer access, no private world selected here.
The 3 sample simulations are deliberately FIXED TOY FIXTURES in CI, not
authorized K0/K1/K2 trials and cannot be driven by arbitrary private config.
Real execution entry points are deliberately absent.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json

from experiments.cafeteria.pc01 import caf01_des_engine as engine
from experiments.cafeteria.pc02 import caf02_private_source_boundary as boundary

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
POLICY=HERE/"CAF02_INDEPENDENT_K0K1K2_POLICY_PROPOSAL_2026-10-30.json"
ENGINE=ROOT/"experiments/cafeteria/pc01/caf01_des_engine.py"
G2_SUCCESS_RUN="https://github.com/yudocyudoc/IGC/actions/runs/41154315886"
FIXTURE_ONLY=True

def require(ok,reason):
    if not ok:raise ValueError(reason)


def hash_bytes(b):
    return "sha256:"+sha256(b).hexdigest()


def public_pulses(policy):
    require(policy["boundary"]["initial_material_stocks"]==0 and
            policy["boundary"]["reset_each_cut"] is True and
            policy["boundary"]["no_loss"] is True and
            policy["boundary"]["no_cancellations"] is True and
            policy["boundary"]["stop_minutes"]==40 and
            policy["resource_ceiling"]["world_DES"]=={
                "K0_max":1,"K1_max_if_selected":1,
                "K2_max_if_authorized":1,"total_max":3,"retries":0},
            "CAF02_DES_BOUNDARY_OR_BUDGET_CHANGED")
    k0=policy["k0"]["public_arrival_pulse"]
    k2=policy["k2"]["future_public_pulse"]
    menu=policy["k1"]["menu"]
    require(k0=={"rate_per_minute":1.2,"duration_minutes":20}
            and k2=={"rate_per_minute":1.35,"duration_minutes":20}
            and menu==[
                {"rate_per_minute":1.0,"t_min":10,"duration_minutes":20},
                {"rate_per_minute":1.5,"t_min":20,"duration_minutes":20},
                {"rate_per_minute":1.8,"t_min":30,"duration_minutes":20},
            ],"CAF02_DES_PUBLIC_PULSE_CHANGED")
    return {"K0":k0,"K1_menu":menu,"K2":k2}


def evaluator_source_pins():
    """Pin exact bytes, including the engine inherited from CAF-01."""
    files={
        "des_engine":ENGINE,
        "evaluator_contract":HERE/"caf02_des_evaluator_preflight.py",
        "public_mask":HERE/"caf02_private_source_boundary.py",
        "public_policy":POLICY,
    }
    return {label:hash_bytes(path.read_bytes())
            for label,path in files.items()}


def check_source_contract():
    policy=json.loads(POLICY.read_bytes())
    require(policy["status"]=="DRAFT_FOR_REVIEW_NOT_FROZEN_NOT_AUTHORIZED"
            and policy["no_world_runs_authorized"] is True,
            "CAF02_NOT_LOCAL_DRAFT_NO_WORLD")
    pulses=public_pulses(policy)
    require(engine.TIE_POLICY=="COMPLETE_THEN_ACCEPT_THEN_START_DOWNSTREAM_FIRST"
            and engine.MAX_STAGES==6
            and engine.SCHEMA=="igc-caf01-des-private-world/0.1",
            "CAF02_DES_GENERIC_ENGINE_CHANGED")
    rates={
        "K0":"6/5","K1_A":"1","K1_B":"3/2",
        "K1_C":"9/5","K2":"27/20"}
    counts={k:len(engine.half_open_arrivals(v,20)) for k,v in rates.items()}
    require(counts=={"K0":24,"K1_A":20,"K1_B":30,
                     "K1_C":36,"K2":27},
            "CAF02_DES_HALF_OPEN_ARRIVALS_CHANGED")
    timing={k:tuple(boundary.public_arrival_count(v,t)
                    for t in (5,10,15,20,30,40))
            for k,v in rates.items()}
    require(timing["K0"][:2]==(6,12) and
            timing["K2"]==(7,14,20,27,27,27),
            "CAF02_DES_OBSERVATION_SCHEDULE_CHANGED")
    return {
        "schema":"igc-caf02-des-evaluator-preflight/0.1",
        "state":"GENERIC_ENGINE_SOURCE_ONLY_NO_PRIVATE_WORLD_SELECTED",
        "engine_is_CAF01_GENERIC_CODE_ONLY":True,
        "historical_CAF01_world_or_observations_reused":False,
        "public_pulses":pulses,
        "arrival_counts":counts,
        "source_hashes":evaluator_source_pins(),
        "independent_source_G5_selected":False,
        "world_runs_consumed":0,
        "G2_native_evidence_reference_only":G2_SUCCESS_RUN,
        "external_G5_witness_verified":False,
    }


def synthetic_fixed_fixture_smoke():
    """ONE hard-coded public fixture, 3 toy runs; NO external/private config.

    This is testing the event calendar and masks, not doing the scientific
    campaign. The function intentionally does not accept config or K2 secrets.
    """
    config={
        "schema":engine.SCHEMA,
        "tie_policy":engine.TIE_POLICY,
        "stages":[{"servers":1,"service_minutes":"1"},
                  {"servers":2,"service_minutes":"2"}],
    }
    # These fixture values are PUBLIC TEST DATA, never candidate world settings.
    def make(rate,times):
        arrivals=engine.half_open_arrivals(rate,20)
        return engine.run_toy_engine(config,arrivals,(0,*times))[1:]
    g5="sha256:"+"a"*64
    k0=boundary.masked_k0(make("6/5",(5,10)),g5)
    k1=boundary.masked_k1(
        make("3/2",(20,))[0],
        {"rate_per_minute":1.5,"t_min":20},g5)
    k2=boundary.reserved_k2_inside_evaluator(
        make("27/20",(5,10,15,20,30,40)),g5)
    require(set(k0)=={"cut","delivered_t5","delivered_t10",
                      "world_precommitment_ref"} and
            set(k1)=={"cut","measurement","delivered",
                      "world_precommitment_ref"} and
            set(k2)=={"cut","delivered","world_precommitment_ref"},
            "CAF02_DES_FIXTURE_FAILED_PUBLIC_MASK")
    require(k0["delivered_t5"]<=k0["delivered_t10"]<=12
            and len(k2["delivered"])==6,
            "CAF02_DES_FIXTURE_MASS_OR_COUNTS_FAILED")
    return {
        "status":"SYNTHETIC_ENGINE_FIXTURE_ONLY_NOT_SCIENTIFIC_EVIDENCE",
        "synthetic_fixed_fixture_simulations":3,
        "real_CAF02_world_runs":0,
        "configuration_is_fixed_public_fixture":True,
        "G5_world_selected":False,
        "K2_real_truth_seen":False,
        "masks_validated":True,
    }


def execute_private_trial(*args,**kwargs):
    raise ValueError(
        "CAF02_REAL_DES_EXECUTION_BLOCKED_EXTERNAL_G5_G4_WITNESS_"
        "AND_AUTHORIZATION_RUNNER_NOT_IMPLEMENTED")


if __name__=="__main__":
    print(json.dumps(check_source_contract(),sort_keys=True))
