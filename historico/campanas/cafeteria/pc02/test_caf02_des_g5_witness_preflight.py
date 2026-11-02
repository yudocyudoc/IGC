#!/usr/bin/env python3
"""CAF-02 private DES / external signatures tests. Only PUBLIC toy fixture runs.

Keypairs below are made in-memory in tests and do NOT represent a real
external witness. No G5 is genuinely sealed, no real private world selected,
no real K0/K1/K2 DES executed and no K2 data released.
"""
import base64
import copy
import json
import unittest
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat

from experiments.cafeteria.pc01 import caf01_des_engine as engine
from experiments.cafeteria.pc02 import caf02_des_evaluator_preflight as eva
from experiments.cafeteria.pc02 import caf02_g5_local_precommit as g5
from experiments.cafeteria.pc02 import caf02_external_witness_verify as witness
from experiments.cafeteria.pc02 import caf02_public_cut_bridge as bridge

CONFIG={"schema":engine.SCHEMA,"tie_policy":engine.TIE_POLICY,
        "stages":[{"servers":1,"service_minutes":"3/2"},
                  {"servers":2,"service_minutes":"1"}]}
NONCE=bytes(range(32))
assert len(NONCE)==32
DECLARATION=("Externally selected hypothetical toy configuration; "
             "not an actual independent evaluator nor an external G5.")
TIMES=("2026-10-30T18:00:00Z",
       "2026-10-30T18:10:00Z",
       "2026-10-30T18:20:00Z")


def local_chain():
    g=g5.local_g5_candidate(CONFIG,NONCE,
                            selection_declaration=DECLARATION)
    a=bridge.package({
        "cut":"G4a_PRE_K1_CANDIDATE_NOT_SEALED",
        "world_precommitment_ref":g["world_precommitment_ref"]})
    bb=bridge.package({
        "cut":"G4b_PRE_K2_CANDIDATE_NOT_SEALED",
        "world_precommitment_ref":g["world_precommitment_ref"],
        "parent_G4a_candidate_sha256":a["candidate_sha256"]})
    return g,a,bb


def synthetic_signed_chain(g,a,bb,private_key):
    packets=[g,a,bb]
    output=[]
    previous=None
    signed_previous=None
    for i,(stage,obj) in enumerate(zip(witness.STAGES,packets)):
        payload=witness.event_message(
            stage=stage,
            world_ref=g["world_precommitment_ref"],
            subject_sha=obj["candidate_sha256"],
            parent_sha=previous,
            previous_signed_event_sha=signed_previous,
            utc_timestamp=TIMES[i],
            witness_id="IN_MEMORY_TEST_ONLY_NOT_EXTERNAL_WITNESS",
            sequence=i+1)
        wrapper={
            "event":payload,
            "signature_ed25519_base64":base64.b64encode(
                private_key.sign(witness.canonical(payload))).decode("ascii")}
        output.append(wrapper)
        previous=obj["candidate_sha256"]
        signed_previous=witness.sha(witness.canonical(wrapper))
    return output


class DESAndWitnessTest(unittest.TestCase):
    def test_pinned_engine_uses_exact_arrivals_and_zero_real_runs(self):
        report=eva.check_source_contract()
        self.assertEqual(report["arrival_counts"],
                         {"K0":24,"K1_A":20,"K1_B":30,
                          "K1_C":36,"K2":27})
        self.assertEqual(report["world_runs_consumed"],0)
        self.assertEqual(report["source_hashes"]["des_engine"],
                         eva.hash_bytes(eva.ENGINE.read_bytes()))
        self.assertFalse(report["independent_source_G5_selected"])

    def test_fixed_toy_des_exercises_three_masks_but_not_campaign(self):
        report=eva.synthetic_fixed_fixture_smoke()
        self.assertTrue(report["masks_validated"])
        self.assertEqual(report["synthetic_fixed_fixture_simulations"],3)
        self.assertEqual(report["real_CAF02_world_runs"],0)
        self.assertFalse(report["G5_world_selected"])
        self.assertFalse(report["K2_real_truth_seen"])
        with self.assertRaisesRegex(ValueError,"REAL_DES_EXECUTION_BLOCKED"):
            eva.execute_private_trial(config=CONFIG)

    def test_public_G5_salted_candidate_does_not_disclose_private_config(self):
        receipt=g5.local_g5_candidate(CONFIG,NONCE,
                                      selection_declaration=DECLARATION)
        self.assertTrue(g5.verify_local_candidate(CONFIG,NONCE,receipt)[
                        "local_precommitment_recomputes"])
        self.assertEqual(receipt["external_witness_verified"],False)
        self.assertEqual(receipt["G5_execution_authorized"],False)
        self.assertEqual(receipt["DES_campaign_world_runs"],0)
        serialized=g5.canonical(receipt)
        self.assertNotIn(b'"stages":',serialized)
        self.assertNotIn(b'"servers":',serialized)
        self.assertNotIn(b'"service_minutes":',serialized)
        self.assertNotIn(NONCE,serialized)
        self.assertEqual(set(receipt["pinned_exact_source_sha256"]),
                         {"des_engine","evaluator_contract",
                          "public_mask","public_policy",
                          "g5_local_precommit","external_witness_verifier",
                          "public_cut_bridge","k2_adjudicator_boundary",
                          "k2_set_scoring"})
        other=g5.local_g5_candidate(CONFIG,b"x"*32,
                                    selection_declaration=DECLARATION)
        self.assertNotEqual(receipt["world_precommitment_ref"],
                            other["world_precommitment_ref"])

    def test_G5_tampering_untracked_source_or_private_nonce_rejected(self):
        original=g5.local_g5_candidate(CONFIG,NONCE,
                                        selection_declaration=DECLARATION)
        other=copy.deepcopy(original)
        other["pinned_exact_source_sha256"]["des_engine"]="sha256:"+"0"*64
        with self.assertRaisesRegex(ValueError,"PINNED_SOURCE_MISMATCH"):
            g5.verify_local_candidate(CONFIG,NONCE,other)
        with self.assertRaisesRegex(ValueError,"MISMATCH"):
            g5.verify_local_candidate(CONFIG,b"z"*32,original)
        with self.assertRaisesRegex(ValueError,"NONCE"):
            g5.local_g5_candidate(CONFIG,b"short",
                                   selection_declaration=DECLARATION)
        with self.assertRaisesRegex(ValueError,"EXECUTION_AUTHORIZATION"):
            g5.authorize_g5_world_run()

    def test_pinned_external_key_three_valid_signatures_not_custody(self):
        signer=Ed25519PrivateKey.generate()
        pub=signer.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)
        anchor=witness.sha(pub)
        g,a,bb=local_chain()
        signed=synthetic_signed_chain(g,a,bb,signer)
        report=witness.verify_ordered_g5_g4a_g4b(
            g,a,bb,signed,public_key_raw=pub,
            pinned_public_key_sha256=anchor)
        self.assertEqual(report["status"],
            "THREE_CRYPTOSIGNATURES_VALID_CLAIMED_ORDER_ONLY")
        self.assertEqual(len(report["signed_event_hashes"]),3)
        self.assertFalse(report["external_independence_accredited"])
        self.assertFalse(report["trusted_clock_accredited"])
        self.assertFalse(report["execution_authorized"])
        self.assertFalse(report["K2_reveal_authorized"])
        with self.assertRaises(witness.AttestationBlocked):
            witness.authorize_k2_release(report)

    def test_forged_signature_wrong_pinned_key_and_reordered_stage_fail(self):
        signer=Ed25519PrivateKey.generate()
        pub=signer.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)
        fake=Ed25519PrivateKey.generate().public_key().public_bytes(
            Encoding.Raw,PublicFormat.Raw)
        g,a,bb=local_chain()
        signed=synthetic_signed_chain(g,a,bb,signer)
        with self.assertRaisesRegex(witness.AttestationBlocked,
                                    "PUBLIC_KEY_NOT_PINNED"):
            witness.verify_ordered_g5_g4a_g4b(
                g,a,bb,signed,public_key_raw=fake,
                pinned_public_key_sha256=witness.sha(pub))
        forged=copy.deepcopy(signed)
        forged[1]["event"]["witness_claimed_utc"]="2026-10-30T18:09:59Z"
        with self.assertRaisesRegex(witness.AttestationBlocked,"SIGNATURE_INVALID"):
            witness.verify_ordered_g5_g4a_g4b(
                g,a,bb,forged,public_key_raw=pub,
                pinned_public_key_sha256=witness.sha(pub))
        with self.assertRaisesRegex(witness.AttestationBlocked,
                                    "WRONG_ORDER"):
            witness.verify_ordered_g5_g4a_g4b(
                g,a,bb,[signed[1],signed[0],signed[2]],
                public_key_raw=pub,pinned_public_key_sha256=witness.sha(pub))

    def test_stage_G4b_parent_drift_and_changed_G4a_fail(self):
        signer=Ed25519PrivateKey.generate()
        pub=signer.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)
        g,a,bb=local_chain()
        signed=synthetic_signed_chain(g,a,bb,signer)
        wrong=copy.deepcopy(bb)
        wrong["parent_G4a_candidate_sha256"]="sha256:"+"f"*64
        wrong["candidate_sha256"]=bridge.digest({
            k:v for k,v in wrong.items() if k!="candidate_sha256"})
        with self.assertRaisesRegex(witness.AttestationBlocked,"PACKAGE_PARENT"):
            witness.verify_ordered_g5_g4a_g4b(
                g,a,wrong,signed,public_key_raw=pub,
                pinned_public_key_sha256=witness.sha(pub))
        wrong=copy.deepcopy(a)
        wrong["candidate_sha256"]="sha256:"+"e"*64
        with self.assertRaises(bridge.CutBlocked):
            witness.verify_ordered_g5_g4a_g4b(
                g,wrong,bb,signed,public_key_raw=pub,
                pinned_public_key_sha256=witness.sha(pub))

if __name__=="__main__":
    unittest.main()
