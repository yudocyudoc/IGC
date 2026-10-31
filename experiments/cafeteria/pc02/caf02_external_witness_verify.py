#!/usr/bin/env python3
"""CAF02 external custody detached Ed25519 verifier, no key generation/signing.

A real independent witness must publish/pin its Ed25519 PUBLIC key SHA256
*outside* this repo and outside the experiment producer before G5. Each
receipt is signed by that witness outside this code. A locally generated
test key is NEVER an independent custodian. Timestamp is a SIGNED CLAIM,
not proof of trusted wall-clock time. No K2 release capability is here.
"""
from __future__ import annotations

import base64
from datetime import datetime,timezone
from hashlib import sha256
import json
import re

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat

SCHEMA="igc-caf02-external-witness-event/0.1"
PIN=re.compile(r"^sha256:[a-f0-9]{64}$")
STAGES=("G5","G4a","G4b")


class AttestationBlocked(ValueError):
    pass


def need(ok,msg):
    if not ok:raise AttestationBlocked(msg)


def canonical(x):
    return (json.dumps(x,sort_keys=True,ensure_ascii=False,
                       separators=(",",":"),allow_nan=False)+"\n").encode()


def sha(x):
    return "sha256:"+sha256(x).hexdigest()


def utc(s):
    need(type(s) is str and
         re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z",s),
         "WITNESS_UTC_TIMESTAMP_FORMAT_INVALID")
    try: v=datetime.fromisoformat(s.replace("Z","+00:00"))
    except ValueError as exc:
        raise AttestationBlocked("WITNESS_BAD_UTC_TIMESTAMP") from exc
    need(v.tzinfo==timezone.utc,"WITNESS_TIMEZONE_NOT_UTC")
    return v


def event_message(*,stage,world_ref,subject_sha,parent_sha,
                  previous_signed_event_sha,utc_timestamp,witness_id,sequence):
    """Data template ONLY, no cryptographic signature or independent clock."""
    need(stage in STAGES and sequence==STAGES.index(stage)+1,
         "WITNESS_STAGE_OR_SEQUENCE_INVALID")
    need(all(type(k) is str and PIN.fullmatch(k) for k in
             (world_ref,subject_sha)),"WITNESS_HASH_FORMAT_INVALID")
    need((parent_sha is None and previous_signed_event_sha is None)
         if stage=="G5" else
         (type(parent_sha) is str and PIN.fullmatch(parent_sha) and
          type(previous_signed_event_sha) is str and
          PIN.fullmatch(previous_signed_event_sha)),
         "WITNESS_MISSING_CHAIN_PARENT")
    need(type(witness_id) is str and 4<=len(witness_id)<=128,
         "WITNESS_ID_INVALID")
    utc(utc_timestamp)
    return {
        "schema":SCHEMA,
        "stage":stage,
        "sequence":sequence,
        "world_precommitment_ref":world_ref,
        "subject_candidate_sha256":subject_sha,
        "parent_candidate_sha256":parent_sha,
        "previous_signed_event_sha256":previous_signed_event_sha,
        "witness_id":witness_id,
        "witness_claimed_utc":utc_timestamp,
        "signature_scheme":"Ed25519_SHA256_PINNED_EXTERNAL_PUBLIC_KEY",
        "external_witness_independence_not_proven_by_crypto_alone":True,
        "trusted_time_source_not_proven_by_crypto_alone":True,
    }


def verify_signed_event(signed,*,witness_public_key_raw,
                        out_of_band_pinned_key_sha256):
    """Return signature result; never create or trust a key found in receipt."""
    need(type(signed) is dict and
         set(signed)=={"event","signature_ed25519_base64"},
         "WITNESS_SIGNED_WRAPPER_FIELDS")
    event=signed["event"]
    need(type(event) is dict and
         set(event)==set(event_message(
             stage="G5",world_ref="sha256:"+"0"*64,
             subject_sha="sha256:"+"0"*64,parent_sha=None,
             previous_signed_event_sha=None,
             utc_timestamp="2026-01-01T00:00:00Z",
             witness_id="witness-placeholder",sequence=1)),
         "WITNESS_EVENT_FIELDS_INVALID")
    # Exact typed schema without accepting caller-injected attestation fields.
    need(event["schema"]==SCHEMA,"WITNESS_SCHEMA_CHANGED")
    need(event==event_message(
        stage=event["stage"],
        world_ref=event["world_precommitment_ref"],
        subject_sha=event["subject_candidate_sha256"],
        parent_sha=event["parent_candidate_sha256"],
        previous_signed_event_sha=event["previous_signed_event_sha256"],
        utc_timestamp=event["witness_claimed_utc"],
        witness_id=event["witness_id"],
        sequence=event["sequence"]),
        "WITNESS_EVENT_NOT_CANONICAL")
    need(type(witness_public_key_raw) is bytes and
         len(witness_public_key_raw)==32 and
         type(out_of_band_pinned_key_sha256) is str and
         PIN.fullmatch(out_of_band_pinned_key_sha256),
         "WITNESS_INDEPENDENT_KEY_PIN_MISSING")
    need(sha(witness_public_key_raw)==out_of_band_pinned_key_sha256,
         "WITNESS_PUBLIC_KEY_NOT_PINNED")
    try:
        signature=base64.b64decode(
            signed["signature_ed25519_base64"],validate=True)
        Ed25519PublicKey.from_public_bytes(
            witness_public_key_raw).verify(signature,canonical(event))
    except (InvalidSignature,ValueError,TypeError) as exc:
        raise AttestationBlocked("WITNESS_SIGNATURE_INVALID") from exc
    need(len(signature)==64,"WITNESS_SIGNATURE_LENGTH_INVALID")
    return {
        "detached_signature_valid":True,
        "signed_event_sha256":sha(canonical(signed)),
        "witness_claimed_time_not_independent_clock_proof":True,
        "signer_independence_requires_out_of_band_institutional_review":True,
        "external_execution_authorized":False,
        "K2_reveal_authorized":False,
    }


def verify_ordered_g5_g4a_g4b(g5,g4a,g4b,receipts,*,public_key_raw,
                             pinned_public_key_sha256):
    """Verify signed PRE-exposure chain, NOT independently verify chronology.

    Expected packets are local content candidates; the signer attests their
    exact SHA. The K2 evaluator must additionally authenticate the signer's
    actual organization and timeline out of band before any release.
    """
    from experiments.cafeteria.pc02 import caf02_public_cut_bridge as bridge
    need(type(receipts) is list and len(receipts)==3,
         "WITNESS_THREE_SIGNED_RECEIPTS_REQUIRED")
    bridge.checked_receipt(g4a)
    bridge.checked_receipt(g4b)
    need(g5.get("state")=="LOCAL_ONLY_NOT_EXTERNALLY_WITNESSED_NOT_AUTHORIZED"
         and g5.get("external_witness_verified") is False
         and g5.get("G5_execution_authorized") is False,
         "WITNESS_G5_NOT_LOCAL_PRECOMMIT")
    expected={
        "G5":g5["candidate_sha256"],
        "G4a":g4a["candidate_sha256"],
        "G4b":g4b["candidate_sha256"],
    }
    world=g5["world_precommitment_ref"]
    need(g4a["world_precommitment_ref"]==world
         and g4b["world_precommitment_ref"]==world
         and g4b["parent_G4a_candidate_sha256"]==
             g4a["candidate_sha256"],"WITNESS_WORLD_OR_PACKAGE_PARENT_MISMATCH")
    predecessor=None
    prev_hash=None
    prev_time=None
    identity=None
    verified=[]
    for stage,receipt in zip(STAGES,receipts):
        obj=receipt["event"]
        need(obj["stage"]==stage
             and obj["world_precommitment_ref"]==world
             and obj["subject_candidate_sha256"]==expected[stage]
             and obj["parent_candidate_sha256"]==predecessor
             and obj["previous_signed_event_sha256"]==prev_hash,
             "WITNESS_WRONG_ORDER_OR_SUBJECT_OR_PARENT")
        result=verify_signed_event(
            receipt,witness_public_key_raw=public_key_raw,
            out_of_band_pinned_key_sha256=pinned_public_key_sha256)
        time=utc(obj["witness_claimed_utc"])
        need(prev_time is None or prev_time<time,
             "WITNESS_NONINCREASING_CLAIMED_TIMESTAMPS")
        need(identity is None or identity==obj["witness_id"],
             "WITNESS_ISSUER_CHANGED_MID_CHAIN")
        prev_hash=result["signed_event_sha256"]
        predecessor=obj["subject_candidate_sha256"]
        prev_time=time
        identity=obj["witness_id"]
        verified.append(result)
    return {
        "status":"THREE_CRYPTOSIGNATURES_VALID_CLAIMED_ORDER_ONLY",
        "same_pinned_public_key":True,
        "same_world_precommitment":True,
        "G5_G4a_G4b_content_and_signed_parents_match":True,
        "external_independence_accredited":False,
        "trusted_clock_accredited":False,
        "execution_authorized":False,
        "K2_reveal_authorized":False,
        "signed_event_hashes":[x["signed_event_sha256"] for x in verified],
    }


def authorize_k2_release(*args,**kwargs):
    raise AttestationBlocked(
        "WITNESS_SIGNATURE_CHAIN_ALONE_IS_NOT_INDEPENDENT_REVIEW_OR_K2_AUTHORIZATION")
