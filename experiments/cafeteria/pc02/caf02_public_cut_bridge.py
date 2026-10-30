#!/usr/bin/env python3
"""CAF02 producer-side staged public cut adapter (NO evaluator or DES imports).

Creates G4a/G4b *candidate* packages from strictly masked public integer
observations. No source world, K2 outcome, nonce, secret, external timestamp,
OMC or provider is loaded. SHA256 binds bytes, but cannot authenticate source,
prove temporal order or satisfy external custody. No DES execution CLI exists.

Actual G5, G4a and G4b external receipts and independent private-world runner
must be established separately before a prospective experiment can start.
"""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
import json
import re

import caf02_d_k0k1k2_adapter as d
import caf02_structural_k0k1k2 as m
import caf02_joint_md_k1_design as joint
import caf02_k0_limited_references as references

SCHEMA="igc-caf02-public-cuts-staging/0.1"
SHA=re.compile(r"^sha256:[0-9a-f]{64}$")
TIMES=(5,10,15,20,30,40)


class CutBlocked(ValueError):
    pass


def need(cond,msg):
    if not cond:raise CutBlocked(msg)


def canonical(obj):
    return (json.dumps(obj,sort_keys=True,ensure_ascii=False,
                       separators=(",",":"),allow_nan=False)+"\n").encode()


def digest(obj):
    return "sha256:"+sha256(canonical(obj)).hexdigest()


def checked_receipt(candidate):
    """Verify integrity of staged local bytes only, never external custody."""
    need(type(candidate) is dict
         and candidate.get("schema")==SCHEMA
         and candidate.get("external_custody_verified") is False
         and candidate.get("evaluation_K2_truth_seen") is False,
         "CUT_CANDIDATE_WRONG_SCHEMA_OR_CUSTODY_CLAIM")
    stored=candidate.get("candidate_sha256")
    need(type(stored) is str and SHA.fullmatch(stored),
         "CUT_CANDIDATE_SHA_MISSING")
    obj={k:v for k,v in candidate.items() if k!="candidate_sha256"}
    need(digest(obj)==stored,"CUT_CANDIDATE_LOCAL_HASH_CHANGED")
    return True


def package(fields):
    need("candidate_sha256" not in fields,"CUT_DOUBLE_HASH_FIELD")
    result={"schema":SCHEMA,"external_custody_verified":False,
            "evaluation_K2_truth_seen":False,**fields}
    result["candidate_sha256"]=digest(result)
    return result


def validate_k0_visible(payload):
    """NO accepted counts, full DES curve, stages, seed, queue, or K2."""
    need(type(payload) is dict
         and set(payload)=={"cut","delivered_t5","delivered_t10",
                            "world_precommitment_ref"}
         and payload["cut"]=="K0",
         "K0_PUBLIC_MASK_FIELDS_ONLY")
    a,bb=payload["delivered_t5"],payload["delivered_t10"]
    need(type(a) is int and type(bb) is int
         and 0<=a<=6 and a<=bb<=12,
         "K0_PUBLIC_INTEGER_COUNT_OR_PHYSICAL_LIMIT")
    ref=payload["world_precommitment_ref"]
    need(type(ref) is str and SHA.fullmatch(ref),
         "K0_G5_COMMITMENT_REF_MISSING")
    return a,bb


def validate_k1_visible(payload,decision,world_ref):
    need(type(payload) is dict
         and set(payload)=={"cut","measurement","delivered",
                            "world_precommitment_ref"}
         and payload["cut"]=="K1"
         and payload["world_precommitment_ref"]==world_ref,
         "K1_PUBLIC_MASK_OR_G5_REF_CHANGED")
    chosen=decision["proposed_measurement"]
    need(chosen is not None and
         type(payload["measurement"]) is dict
         and payload["measurement"]==chosen
         and type(payload["delivered"]) is int
         and 0<=payload["delivered"]<=
             chosen["rate_per_minute"]*min(chosen["t_min"],20),
         "K1_PUBLIC_OBSERVATION_NOT_PRESELECTED_OR_INVALID")
    return {**chosen,"delivered":payload["delivered"]}


def m_envelopes(rows_by_family,rate):
    out={}
    for family,rows in rows_by_family.items():
        if not rows:
            out[family]=None
            continue
        predictions=[m.curve(row,rate) for row in rows]
        out[family]={
            "lower":[min(row[t] for row in predictions) for t in range(6)],
            "upper":[max(row[t] for row in predictions) for t in range(6)],
            "candidate_count":len(rows),
        }
    return out


def create_g4a_candidate(k0_public,policy):
    """Only two public K0 values; all model hypotheses and K2 priors."""
    need(policy.get("no_world_runs_authorized") is True,
         "G4A_LOCAL_DRAFT_REQUIRES_NO_WORLD_EXECUTION")
    a,bb=validate_k0_visible(k0_public)
    mk0,dk0=joint.from_public_k0(a,bb,policy)
    selection=joint.select(mk0,dk0,policy)
    rate=policy["k2"]["future_public_pulse"]["rate_per_minute"]
    mp=m_envelopes({f:mk0[f]["eligible"] for f in m.FAMILIES},rate)
    dp={f:d.family_envelope(dk0["compatible"][f],rate)
        for f in ("D1","D2","D3")}
    baseline=references.forecast(a,bb,
        policy["k0"]["public_arrival_pulse"]["rate_per_minute"],rate)
    return package({
        "cut":"G4a_PRE_K1_CANDIDATE_NOT_SEALED",
        "world_precommitment_ref":k0_public["world_precommitment_ref"],
        "policy_hash":joint.hash_object(policy),
        "K0_public":deepcopy(k0_public),
        "K0_M":mk0,
        "K0_D":dk0,
        "K1_preselected_common":selection,
        "K2_prior_M_by_family":mp,
        "K2_prior_D_by_family":dp,
        "K2_K0_only_references":baseline,
        "K1_delivered_observation_present":False,
        "K2_forecast_times_minutes":list(TIMES),
        "K2_scored_values_present":False,
        "state":"NOT_CUSTODIED_EXTERNAL_G4a_WITNESS_REQUIRED",
        "DES_runs":0,
        "native_OpenModelica_parity_verified":False,
        "ATMS_persistence_verified":False,
    })


def create_g4b_candidate(g4a,k1_public,policy):
    """Revise using EXACTLY the selected one-count K1; preserve prior K2."""
    checked_receipt(g4a)
    need(g4a["cut"]=="G4a_PRE_K1_CANDIDATE_NOT_SEALED"
         and g4a["policy_hash"]==joint.hash_object(policy)
         and not g4a["K1_delivered_observation_present"]
         and not g4a["K2_scored_values_present"],
         "G4B_WRONG_PARENT_OR_POLICY")
    selected=g4a["K1_preselected_common"]
    mk0,dk0=g4a["K0_M"],g4a["K0_D"]
    need(selected["K0_fingerprints"]=={
         "M":joint.hash_object(mk0),"D":joint.hash_object(dk0)},
         "G4B_K0_CANDIDATES_TAMPERED")
    if selected["proposed_measurement"] is None:
        need(k1_public is None,"G4B_K1_INJECTED_WHEN_NO_K1_SELECTED")
        m1={
            "status":"K1_NOT_EXECUTED_SHARED_NO_HYPOTHESIS",
            "updated":{f:{"kept":mk0[f]["eligible"],
                           "count_before":len(mk0[f]["eligible"]),
                           "count_after":len(mk0[f]["eligible"])}
                       for f in m.FAMILIES},
            "revision_type":"NO_K1_EVIDENCE_NO_REVISION",
            "surviving_families":[f for f in m.FAMILIES
                                  if mk0[f]["eligible"]],
            "K1_observation":None,
        }
        d1=d.revise_k1(dk0,selected,None,policy)
        used=False
    else:
        evidence=validate_k1_visible(
            k1_public,selected,g4a["world_precommitment_ref"])
        m1=m.k1_revise(mk0,selected,evidence,
                       policy["k1"]["absolute_residual_tolerance_orders"])
        d1=d.revise_k1(dk0,selected,evidence,policy)
        used=True
    rate=policy["k2"]["future_public_pulse"]["rate_per_minute"]
    mpost=m_envelopes({f:m1["updated"][f]["kept"] for f in m.FAMILIES},rate)
    dpost={f:d.family_envelope(d1["compatible"][f],rate)
           for f in ("D1","D2","D3")}
    need(used or (mpost==g4a["K2_prior_M_by_family"]
                  and dpost==g4a["K2_prior_D_by_family"]),
         "G4B_NO_K1_MUST_RETAIN_PREVIOUS_FORECASTS")
    return package({
        "cut":"G4b_PRE_K2_CANDIDATE_NOT_SEALED",
        "parent_G4a_candidate_sha256":g4a["candidate_sha256"],
        "world_precommitment_ref":g4a["world_precommitment_ref"],
        "policy_hash":g4a["policy_hash"],
        "K1_public":deepcopy(k1_public),
        "K1_used":used,
        "M_K1_revision":m1,
        "D_K1_revision":d1,
        "K2_prior_M_by_family_sha256":digest(g4a["K2_prior_M_by_family"]),
        "K2_prior_D_by_family_sha256":digest(g4a["K2_prior_D_by_family"]),
        "K2_revised_M_by_family":mpost,
        "K2_revised_D_by_family":dpost,
        "K2_forecast_times_minutes":list(TIMES),
        "K2_scored_values_present":False,
        "state":"NOT_CUSTODIED_EXTERNAL_G4b_WITNESS_REQUIRED",
        "DES_runs":0,
        "native_OpenModelica_parity_verified":False,
        "ATMS_persistence_verified":False,
    })


def validate_k2_reserved(payload,g4a,g4b):
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
    need(type(ys) is list and len(ys)==6
         and all(type(y) is int for y in ys)
         and all(0<=x<=y for x,y in zip([0]+ys[:-1],ys))
         and all(y<=int(1.35*min(t,20)+1e-9)
                 for y,t in zip(ys,TIMES)),
         "K2_RESERVED_INTEGER_OR_PHYSICAL_LIMIT")
    return ys


def authorize_world_execution(*args,**kwargs):
    """No implicit unlocking through policy flags or caller-supplied hashes."""
    raise CutBlocked(
        "CAF02_WORLD_EXECUTION_NOT_IMPLEMENTED_EXTERNAL_G5_WITNESS_"
        "AND_EXPLICIT_SEPARATE_AUTHORIZATION_REQUIRED")


def main():
    """Opt-in LOCAL preparation, never external approval or world invocation."""
    import argparse
    from pathlib import Path
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stage",required=True,choices=("G4a","G4b"))
    ap.add_argument("--public-evidence",help="K0/K1 masked JSON; omit only for skipped K1")
    ap.add_argument("--g4a-candidate",help="mandatory for G4b")
    ap.add_argument("--out",required=True,help="must not exist")
    args=ap.parse_args()
    policy=json.loads(d.POLICY.read_text(encoding="utf-8"))
    need(policy["status"]=="DRAFT_FOR_REVIEW_NOT_FROZEN_NOT_AUTHORIZED",
         "ONLY_LOCAL_DRAFT_PREPARATION_SUPPORTED")
    need(not Path(args.out).exists(),"CUT_OUTPUT_ALREADY_EXISTS")
    if args.stage=="G4a":
        need(bool(args.public_evidence) and not args.g4a_candidate,
             "G4a_REQUIRES_K0_ONLY")
        public=json.loads(Path(args.public_evidence).read_text(encoding="utf-8"))
        candidate=create_g4a_candidate(public,policy)
    else:
        need(bool(args.g4a_candidate),"G4b_PARENT_G4a_MANDATORY")
        parent=json.loads(Path(args.g4a_candidate).read_text(encoding="utf-8"))
        public=(json.loads(Path(args.public_evidence).read_text(encoding="utf-8"))
                if args.public_evidence else None)
        candidate=create_g4b_candidate(parent,public,policy)
    with Path(args.out).open("xb") as handle:
        handle.write(canonical(candidate))
    print("CAF02_STAGE_CANDIDATE_ONLY_NOT_EXTERNALLY_CUSTODIED",args.stage,
          candidate["candidate_sha256"],"NO_DES_NO_NATIVE_NO_K2")


if __name__=="__main__":
    main()
