"""Signed custody contracts. RSA keys, CSV and jobs here are TEMP TEST FIXTURES.

Signing in tests is NOT certification of solver execution or external custody.
No provider, OpenModelica, evaluator truth, or real world in these tests.
"""
import base64
import copy
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_v0_contract import canonical, digest
from scripts.arena_cafe.ct03_m_construction_diagnostic import sha_bytes
from scripts.arena_cafe.ct03_execution_boundary import (
    REGISTRY, SCHEMA, verify_witness, verify_runner, verify_archive,
)
from scripts.arena_cafe.ct03_prospective_lock import seal
from test_arena_ct03_m_construction_diagnostic import make_example
from test_arena_ct03_prospective_lock import fixture as lock_fixture

def shell(*args):
    x = subprocess.run(["openssl", *map(str,args)],
                       capture_output=True, text=True, timeout=15)
    if x.returncode:
        raise RuntimeError(x.stderr)
    return x.stdout


def credentials(root):
    trust = root / "independent-key-fixture"
    trust.mkdir()
    secret, public = trust / "runner-key.pem", trust / "runner-public.pem"
    archive_secret, archive_public = trust / "archivist-key.pem", trust / "archivist-public.pem"
    for private, pub in ((secret, public), (archive_secret, archive_public)):
        shell("genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048",
              "-out", private)
        shell("pkey", "-in", private, "-pubout", "-out", pub)
    registry = trust / "registry.json"
    registry.write_text(json.dumps({"schema": REGISTRY, "authorities": [
        {"id": "TEST_RUNNER", "purpose": "PHYSICAL_OMC",
         "public_key_sha256": sha_bytes(public.read_bytes())},
        {"id": "TEST_ARCHIVER", "purpose": "LOCK_ARCHIVE",
         "public_key_sha256": sha_bytes(archive_public.read_bytes())},
    ]}))
    return trust, secret, public, registry, archive_secret, archive_public


def signed(root, statement, purpose, authority, secret):
    text = root / "message.json"
    signature = root / "message.sig"
    text.write_bytes(canonical(statement))
    shell("dgst", "-sha256", "-sign", secret, "-out", signature, text)
    return {"schema": SCHEMA, "purpose": purpose, "authority_id": authority,
            "statement": statement, "statement_sha256": digest(statement),
            "signature_base64": base64.b64encode(signature.read_bytes()).decode()}


def runner_fixture(root):
    producer = root / "producer"
    producer.mkdir()
    manifest, parent, ctx, obs, receipt, mo, csv = make_example(producer)
    log = producer / "omc.log"
    log.write_text("TEST ONLY: fabricated stdout, never an OpenModelica run!\n")
    statement = {
        "case_id": "CT-03", "world_public_id": "W1", "arm": "M",
        "round_kind": "initial",
        "candidate_id": parent["canonical_sha256"],
        "parent_hash": parent["full_ast_sha256"],
        "receipt_sha256": digest(receipt),
        "script_sha256": sha_bytes((mo.parent / "simulate.mos").read_bytes()),
        "modelica_sha256": sha_bytes(mo.read_bytes()),
        "csv_sha256": sha_bytes(csv.read_bytes()),
        "solver_log_sha256": sha_bytes(log.read_bytes()),
        "command": receipt["simulation_command"], "csv_filename": csv.name,
        "solver_image": "openmodelica/openmodelica:v1.26.5-minimal",
        "runner_job_id": "FIXTURE_ONLY_123456",
        "workflow_run_url": "https://github.com/yudocyudoc/IGC/actions/runs/123456",
        "exit_code": 0,
    }
    return producer, manifest, parent, receipt, mo, csv, log, statement


def verify_run(root, statement, *, signature, public, registry, producer,
               manifest, parent, receipt, mo, csv, log):
    return verify_runner(
        witness=signature, trust_registry=registry, public_key=public,
        producer_root=producer, manifest=manifest, parent=parent,
        receipt=receipt, modelica_file=mo, script_file=mo.parent/"simulate.mos",
        csv_file=csv, solver_log=log)


class IndependentWitnessContractTest(unittest.TestCase):
    def test_signed_synthetic_runner_bytes_pass_without_claiming_g2(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            _, secret, public, registry, archive_secret, archive_public=credentials(root)
            producer, m,p,r,mo,csv,log,statement=runner_fixture(root)
            witness=signed(root,statement,"PHYSICAL_OMC","TEST_RUNNER",secret)
            result=verify_run(root,statement,signature=witness,public=public,
                              registry=registry,producer=producer,
                              manifest=m,parent=p,receipt=r,mo=mo,csv=csv,log=log)
            self.assertEqual(result["candidate_id"],p["canonical_sha256"])
            self.assertFalse(result["authentic_solver_execution_proven"])
            self.assertEqual(result["omc_executed_by_verifier"],0)
            self.assertIn("NOT_CERTIFIED",result["status"])

    def test_mutations_signature_key_role_and_model_are_rejected(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            _, secret, public, registry, archive_secret, archive_public=credentials(root)
            producer,m,p,r,mo,csv,log,statement=runner_fixture(root)
            witness=signed(root,statement,"PHYSICAL_OMC","TEST_RUNNER",secret)
            def check(w=witness,**kwargs):
                return verify_run(root,statement,signature=w,public=public,
                                  registry=registry,producer=producer,
                                  manifest=m,parent=p,receipt=r,mo=mo,csv=csv,log=log,
                                  **kwargs)
            mutated=copy.deepcopy(witness)
            mutated["statement"]["parent_hash"]="sha256:"+"f"*64
            mutated["statement_sha256"]=digest(mutated["statement"])
            with self.assertRaisesRegex(ValueError,"SIGNATURE_NOT_VERIFIED"):
                check(w=mutated)
            mutated=signed(root,{**statement,"csv_sha256":"sha256:"+"f"*64},
                          "PHYSICAL_OMC","TEST_RUNNER",secret)
            with self.assertRaisesRegex(ValueError,"SIGNED_COMMAND_LOG_OR_PARENT_MISMATCH"):
                check(w=mutated)
            mutated=signed(root,statement,"LOCK_ARCHIVE","TEST_ARCHIVER",secret)
            with self.assertRaisesRegex(ValueError,"WITNESS_SCOPE_OR_DIGEST_MISMATCH"):
                check(w=mutated)
            malformed=copy.deepcopy(witness)
            malformed["signature_base64"]="NOT BASE64??"
            with self.assertRaisesRegex(ValueError,"SIGNATURE_BASE64_INVALID"):
                check(w=malformed)
            badreg = json.loads(registry.read_text())
            badreg["authorities"][0]["public_key_sha256"]="sha256:"+"e"*64
            registry.write_text(json.dumps(badreg))
            with self.assertRaisesRegex(ValueError,"PUBLIC_KEY_NOT_PINNED"):
                check()

    def test_signed_log_cannot_override_changed_output_or_self_supplied_trust(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            trust,secret,public,registry,archive_secret,archive_public=credentials(root)
            producer,m,p,r,mo,csv,log,statement=runner_fixture(root)
            witness=signed(root,statement,"PHYSICAL_OMC","TEST_RUNNER",secret)
            log.write_bytes(log.read_bytes()+b"TAMPER\n")
            with self.assertRaisesRegex(ValueError,"SIGNED_COMMAND_LOG_OR_PARENT_MISMATCH"):
                verify_run(root,statement,signature=witness,public=public,
                           registry=registry,producer=producer,manifest=m,
                           parent=p,receipt=r,mo=mo,csv=csv,log=log)
            # Even a correct signature is rejected if trust assets are inside
            # the producer tree (separation is a deployment prerequisite).
            inside = producer / "operator-key.json"
            inside.write_bytes(registry.read_bytes())
            with self.assertRaisesRegex(ValueError,"INSIDE_PRODUCER_BOUNDARY"):
                verify_run(root,statement,signature=witness,public=public,
                           registry=inside,producer=producer,manifest=m,
                           parent=p,receipt=r,mo=mo,csv=csv,log=log)

    def test_archive_signature_is_required_before_any_evaluator_release(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            _, secret, public, registry, archive_secret, archive_public=credentials(root)
            producer=root/"producer"
            producer.mkdir()
            c, world, d, m, entries=lock_fixture(producer)
            lock=seal(c,world,d,m,entries)
            statement={
                "case_id":"CT-03",
                "world_public_id":"W1",
                "lock_sha256":lock["lock_sha256"],
                "protocol_sha256":lock["protocol_sha256"],
                "world_commitment_sha256":lock["world_commitment_sha256"],
                "archive_id":"FIXTURE_ARCHIVE_123",
                "archived_before_evaluator_access":True,
            }
            witness=signed(root,statement,"LOCK_ARCHIVE","TEST_ARCHIVER",archive_secret)
            out=verify_archive(lock=lock,witness=witness,trust_registry=registry,
                               public_key=archive_public,producer_root=producer)
            self.assertFalse(out["reserved_truth_opened"])
            self.assertEqual(out["lock_sha256"],lock["lock_sha256"])
            different=copy.deepcopy(lock)
            different["rows"][0]["parent_hash"]="sha256:"+"f"*64
            with self.assertRaisesRegex(ValueError,"SEAL_TAMPERED"):
                verify_archive(lock=different,witness=witness,trust_registry=registry,
                               public_key=archive_public,producer_root=producer)
            wrong=signed(root,{**statement,"lock_sha256":"sha256:"+"e"*64},
                         "LOCK_ARCHIVE","TEST_ARCHIVER",archive_secret)
            with self.assertRaisesRegex(ValueError,"ARCHIVE_SIGNED_LOCK_MISMATCH"):
                verify_archive(lock=lock,witness=wrong,trust_registry=registry,
                               public_key=archive_public,producer_root=producer)
            self.assertEqual(out["status"],
                             "LOCK_ARCHIVE_SIGNATURE_AND_BYTES_VERIFIED_NO_TRUTH_READ")


if __name__=="__main__":
    unittest.main()
