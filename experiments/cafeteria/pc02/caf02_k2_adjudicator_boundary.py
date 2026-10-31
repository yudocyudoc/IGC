#!/usr/bin/env python3
"""POST-RELEASE adjudicator-side K2 syntax only. NOT a release authorization.

Must be deployed in a separate controlled process, after independently
authenticated G5/G4a/G4b receipts. There is NO K2 release functionality or
witness-verification method here. Never install this module in the G4a/G4b
producer execution environment.
"""
from fractions import Fraction
from caf02_public_cut_bridge import checked_receipt, need, TIMES, digest
import caf02_k2_set_scoring as scoring

def validate_k2_after_external_release(payload,g4a,g4b):
    """Adjudication-side schema only: never call in a producer G4a/G4b step.

    Does NOT authorize release. Independent G5/G4a/G4b external receipts
    must be authenticated *outside this module* before even reading K2.
    """
    checked_receipt(g4a)
    checked_receipt(g4b)
    need(g4b["parent_G4a_candidate_sha256"]==g4a["candidate_sha256"],
         "K2_PARENT_G4a_CHANGED")
    need(type(payload) is dict
         and set(payload)=={"cut","delivered","world_precommitment_ref"}
         and payload["cut"]=="K2"
         and payload["world_precommitment_ref"]==g4a["world_precommitment_ref"],
         "K2_RESERVED_MASK_OR_WORLD_REF_INVALID")
    ys=payload["delivered"]
    # The private DES schedules t_j=(j+1/2)/1.35, with acceptances at
    # snapshot time INCLUDED. Simple floor(1.35*t) is WRONG at minutes 5
    # and 10: there can be 7 and 14 accepted orders, respectively.
    rate=Fraction(27,20)
    arrivals=[Fraction(2*j+1,2)/rate for j in range(27)]
    max_accepted=[sum(x<=t for x in arrivals) for t in TIMES]
    need(max_accepted==[7,14,20,27,27,27],
         "K2_PUBLIC_ARRIVAL_SCHEDULE_CHANGED")
    need(type(ys) is list and len(ys)==6
         and all(type(y) is int for y in ys)
         and all(0<=x<=y for x,y in zip([0]+ys[:-1],ys))
         and all(y<=cap for y,cap in zip(ys,max_accepted)),
         "K2_RESERVED_INTEGER_OR_PHYSICAL_LIMIT")
    return ys




def score_both_arms_after_external_release(k2_payload,g4a,g4b,policy):
    """Pure POST-RELEASE K2 adjudication; does NOT check external witnesses.

    This function must only be invoked by an externally authorized evaluator
    after independent verification of G5, G4a and G4b. The local test call
    with synthetic truth proves arithmetic wiring, NOT custody or release.
    """
    truth=validate_k2_after_external_release(k2_payload,g4a,g4b)
    need(policy.get("status")=="DRAFT_FOR_REVIEW_NOT_FROZEN_NOT_AUTHORIZED"
         and policy.get("no_world_runs_authorized") is True,
         "K2_ONLY_OFFLINE_DRAFT_ADJUDICATION_IMPLEMENTED")
    import caf02_joint_md_k1_design as joint
    need(g4a["policy_hash"]==g4b["policy_hash"]==joint.hash_object(policy)
         and g4b["world_precommitment_ref"]==
             g4a["world_precommitment_ref"]
         and g4a["cut"]=="G4a_PRE_K1_CANDIDATE_NOT_SEALED"
         and g4b["cut"]=="G4b_PRE_K2_CANDIDATE_NOT_SEALED",
         "K2_WRONG_STAGED_PARENT_OR_POLICY")
    need(g4b["K2_prior_M_by_family_sha256"]==
         digest(g4a["K2_prior_M_by_family"])
         and g4b["K2_prior_D_by_family_sha256"]==
         digest(g4a["K2_prior_D_by_family"])
         and g4a["K2_K0_only_references"]["K1_measurement_seen"] is False
         and g4a["K2_K0_only_references"]["K2_truth_seen"] is False,
         "K2_PREVIOUS_PREDICTIONS_OR_REFERENCES_NOT_LOCKED")
    references=g4a["K2_K0_only_references"]
    ref_caf=references["REF_CAF"]["predicted_K2_delivered"]
    ref_scale=references["REF_SCALE"]["predicted_K2_delivered"]
    kwargs={
        "min_improvement":policy["k2"]["delta_success_at_least_orders"],
        "point_max_width":policy["k2"]["point_eligibility_max_width_orders"],
    }
    scored={}
    for arm in ("M","D"):
        scored[arm]=scoring.adjudicate(
            g4a["K2_prior_"+arm+"_by_family"],
            g4b["K2_revised_"+arm+"_by_family"],
            ref_caf,ref_scale,truth,arm=arm,**kwargs)
    return {
        "status":"OFFLINE_DESCRIPTIVE_POST_RELEASE_SCORING_NOT_EXTERNAL_CUSTODY",
        "schema":"igc-caf02-k2-both-arms-offline-adjudication/0.1",
        "world_precommitment_ref":g4a["world_precommitment_ref"],
        "parent_G4a_candidate_sha256":g4a["candidate_sha256"],
        "parent_G4b_candidate_sha256":g4b["candidate_sha256"],
        "scored_times_minutes":list(TIMES),
        "same_six_observations_for_both_arms":True,
        "M":scored["M"],"D":scored["D"],
        "K1_was_used":g4b["K1_used"],
        "K2_truth_was_synthetic_or_externally_released_NOT_ATTESTED_HERE":True,
        "G5_G4a_G4b_external_receipts_verified_here":False,
        "native_G2_verified_here":False,
        "ATMS_persisted_here":False,
        "baseline_updated_with_K1":False,
        "equal_information_reference_superiority_not_claimed":True,
    }


def authorize_K2_reveal(*args,**kwargs):
    raise ValueError("K2_REVEAL_NOT_AUTHORIZED_OR_IMPLEMENTED_EXTERNAL_WITNESS_REQUIRED")
