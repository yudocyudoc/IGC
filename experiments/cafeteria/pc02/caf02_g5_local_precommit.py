#!/usr/bin/env python3
"""CAF02 LOCAL G5 candidate commitment - no execution or external attestation.

The evaluator's independent human/operator supplies NEW private configuration
and 32-byte secret nonce OFFLINE, outside repo, before any real K0. This module
does not choose parameters, preview observations, or provide a DES run path.
Local SHA-256 precommitment is not an external G5 witness or authorization.
"""
from __future__ import annotations

from hashlib import sha256
from hmac import compare_digest
import json

from experiments.cafeteria.pc01 import caf01_des_engine as engine
from experiments.cafeteria.pc02 import caf02_des_evaluator_preflight as evaluator

SCHEMA="igc-caf02-g5-local-candidate/0.1"
DOMAIN=b"IGC_CAF02_DES_G5_SOURCE_AND_PRIVATE_CONFIG_v1\x00"


def need(condition,reason):
    if not condition:raise ValueError(reason)


def canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"),
                      ensure_ascii=False,allow_nan=False).encode("utf-8")


def sha(b):
    return "sha256:"+sha256(b).hexdigest()


def local_g5_candidate(private_config,nonce,*,selection_declaration):
    """Produces PUBLIC candidate with zero private parameters, no nonce.

    selection_declaration is an externally reviewable free-text provenance
    statement, NOT evidence of actual independence or signature.
    """
    need(type(nonce) is bytes and len(nonce)==32,
         "G5_PRIVATE_NONCE_32_BYTES_REQUIRED")
    need(type(selection_declaration) is str
         and 20<=len(selection_declaration)<=2048,
         "G5_INDEPENDENT_SELECTION_PROVENANCE_NOT_DECLARED")
    engine.validate_private_config(private_config)
    contract=evaluator.check_source_contract()
    pins=contract["source_hashes"]
    need(set(pins)=={"des_engine","evaluator_contract",
                     "public_mask","public_policy"},
         "G5_SOURCE_PIN_INCOMPLETE")
    seed=DOMAIN+nonce+b"\x00"+engine.canonical_private_bytes(
        private_config)+b"\x00"+canonical(pins)
    world_ref=sha(seed)
    public={
        "schema":SCHEMA,
        "state":"LOCAL_ONLY_NOT_EXTERNALLY_WITNESSED_NOT_AUTHORIZED",
        "world_precommitment_ref":world_ref,
        "pinned_exact_source_sha256":pins,
        "source_engine_concept":
            "GENERIC_DISCRETE_EVENT_SERVER_QUEUE_CALENDAR_NOT_E1_OR_D_ODE",
        "source_code_reused_from_CAF01_generic_engine":True,
        "CAF01_historical_world_reused":False,
        "source_independence_claim":"DECLARATION_ONLY_NOT_AUDITED",
        "selection_declaration":selection_declaration,
        "private_parameters_or_nonce_in_public_receipt":False,
        "public_inputs":contract["public_pulses"],
        "event_order":engine.TIE_POLICY,
        "G2_reference":contract["G2_native_evidence_reference_only"],
        "DES_campaign_world_runs":0,
        "automatic_retries_allowed":0,
        "K2_released":False,
        "external_witness_signature_present":False,
        "external_witness_verified":False,
        "G5_execution_authorized":False,
    }
    public["candidate_sha256"]=sha(canonical(public)+b"\n")
    return public


def verify_local_candidate(private_config,nonce,receipt):
    need(type(receipt) is dict and receipt.get("schema")==SCHEMA,
         "G5_RECEIPT_SCHEMA_CHANGED")
    expected=local_g5_candidate(private_config,nonce,
        selection_declaration=receipt["selection_declaration"])
    need(compare_digest(canonical(expected),canonical(receipt)),
         "G5_RECOMPUTATION_OR_PINNED_SOURCE_MISMATCH")
    return {
        "local_precommitment_recomputes":True,
        "external_custody_verified":False,
        "world_run_authorized":False,
        "no_private_config_revealed":True,
    }


def authorize_g5_world_run(*args,**kwargs):
    raise ValueError("G5_EXTERNAL_CUSTODY_AND_EXECUTION_AUTHORIZATION_NOT_AVAILABLE")
