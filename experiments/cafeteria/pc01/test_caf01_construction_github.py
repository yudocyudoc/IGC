#!/usr/bin/env python3
"""GitHub CI tests: only INVENTED toy worlds, never the private CAF-01 config."""
from __future__ import annotations

import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from caf01_des_engine import SCHEMA as DES_SCHEMA, TIE_POLICY
from caf01_construction_github import (
    ConstructionBlocked, EXPECTED_A, EXPECTED_RECEIPT_FILE_SHA256,
    PUBLIC_RECEIPT_PATH, SECRET_ENV, TIMES, decode_private_envelope,
    prepare_authorized_inputs, produce_construction_public_only,
    read_pinned_public_receipt, write_public_bundle,
)
from caf01_g5_seal import (CONTRACT, canonical, hard_budget,
                           make_public_receipt, sha_bytes, snapshot_files)


def invented_config():
    # Synthetic unit fixture only. Not the selected CAF-01 world.
    return {"schema": DES_SCHEMA, "tie_policy": TIE_POLICY,
            "stages": [{"servers": 2, "service_minutes": "2"},
                       {"servers": 1, "service_minutes": "1/2"}]}


class TestCAF01GitHubConstructionPreparation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT.read_text())
        cls.nonce = bytes([17])*32

    def fake_receipt(self):
        return make_public_receipt(invented_config(), self.nonce,
                                   pinned_files=snapshot_files(),
                                   budget=hard_budget(self.contract))

    def toy_secret(self, receipt):
        content={"schema": "igc-caf01-g5-offline-world-precommit/0.1",
                 "config": invented_config(), "nonce_hex": self.nonce.hex(),
                 "public_receipt_sha256": sha_bytes(canonical(receipt))}
        return base64.b64encode(canonical(content)).decode("ascii")

    def test_public_receipt_bytes_are_exactly_the_emailed_file(self):
        self.assertTrue(PUBLIC_RECEIPT_PATH.is_file())
        data=PUBLIC_RECEIPT_PATH.read_bytes()
        self.assertEqual(len(data),2135)
        self.assertTrue(data.endswith(b"\n"))
        self.assertEqual(hashlib.sha256(data).hexdigest(),
                         EXPECTED_RECEIPT_FILE_SHA256)
        r=read_pinned_public_receipt()
        self.assertEqual(r["pinned_source_sha256"],snapshot_files())
        self.assertEqual(r["state"],
                         "PRIVATE_CONFIG_PRECOMMITTED_NOT_EXTERNALLY_WITNESSED")
        self.assertFalse(r["future_evaluation_reveal_authorized"])

    def test_secret_precommit_match_checked_without_DES(self):
        r=self.fake_receipt()
        secret=self.toy_secret(r)
        config=prepare_authorized_inputs(secret,r,self.contract)
        self.assertEqual(config,invented_config())
        altered=copy.deepcopy(r)
        altered["world_precommitment_sha256"]="sha256:"+"0"*64
        with self.assertRaisesRegex(ConstructionBlocked,
                                    "NOT_BOUND_TO_PUBLIC_RECEIPT"):
            prepare_authorized_inputs(secret,altered,self.contract)

    def test_wrong_nonce_or_private_parameters_rejected_without_DES(self):
        r=self.fake_receipt()
        b=json.loads(base64.b64decode(self.toy_secret(r)))
        b["nonce_hex"]="0f"*32
        encoded=base64.b64encode(canonical(b)).decode()
        with self.assertRaises(ValueError):
            prepare_authorized_inputs(encoded,r,self.contract)
        with self.assertRaisesRegex(ConstructionBlocked,"SECRET_NOT_CONFIGURED"):
            decode_private_envelope(None)
        with self.assertRaisesRegex(ConstructionBlocked,"PRIVATE_ENVELOPE_UNREADABLE"):
            decode_private_envelope("THIS IS NOT BASE64")

    def test_one_toy_construction_produces_only_public_outputs(self):
        r=self.fake_receipt()
        output=produce_construction_public_only(invented_config(),r,self.contract)
        self.assertEqual(len(output),7)
        source=output["01_construction_public.json"]
        self.assertEqual([row["t_min"] for row in source["observations"]],
                         list(TIMES))
        self.assertEqual([row["accepted_cum_orders"]
                          for row in source["observations"]],list(EXPECTED_A))
        self.assertEqual(source["evaluation_run_count"],0)
        self.assertEqual(
            output["02_evidence_G3_producers.json"]["source_snapshot_sha256"],
            r["world_precommitment_sha256"])
        self.assertEqual(len(output["03_CAFN_masked_endpoints.json"]
                             ["observations"]),2)
        refs=output["05_G4_references_prelock.json"]
        self.assertFalse(refs["future_truth_seen"])
        self.assertEqual(refs["independent_new_world_runs"],0)
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/"new-output"
            with patch.dict(os.environ,{"GITHUB_SHA":"fixture",
                                         "GITHUB_RUN_ID":"toy-ci",
                                         "GITHUB_RUN_ATTEMPT":"1"}):
                manifest=write_public_bundle(output,folder,r)
            self.assertEqual(manifest["DES_construction_world_runs_consumed"],1)
            self.assertEqual(manifest["DES_evaluation_world_runs_consumed"],0)
            self.assertEqual(len(manifest["files_sha256"]),7)
            for p in folder.iterdir():
                content=p.read_text()
                for secret in ['"nonce_hex"','"stages"','"servers"',
                               '"service_minutes"','"stage_in_service"',
                               '"stage_waiting"']:
                    self.assertNotIn(secret,content)
            with self.assertRaisesRegex(ConstructionBlocked,
                                        "PUBLIC_OUTPUT_ALREADY_EXISTS"):
                write_public_bundle(output,folder,r)

    def test_no_secret_keys_can_be_written_to_public_artifact(self):
        r=self.fake_receipt()
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"public"
            with self.assertRaisesRegex(ConstructionBlocked,
                                        "PRIVATE_INFORMATION_IN_PUBLIC_ARTIFACT"):
                write_public_bundle({"secret.json":{"nonce_hex":"NEVER"}},
                                    p,r)
            self.assertFalse(p.exists())

    def test_no_evaluation_runner_and_pulse_is_construction(self):
        import inspect
        import caf01_construction_github as mod
        body=inspect.getsource(mod.produce_construction_public_only)
        self.assertIn('half_open_arrivals("6/5", "20")',body)
        self.assertNotIn('half_open_arrivals("3/2", "20")',body)
        self.assertNotIn("evaluation_snapshots",body)
        self.assertNotIn('run_toy_engine(config, evaluation',body)


if __name__=="__main__":
    unittest.main()
