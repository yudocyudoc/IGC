"""Evaluator-only boundary fixture: sealed world is synthetic and never run."""
import copy
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_v0_contract import digest
from scripts.arena_cafe.ct03_execution_boundary import SCHEMA
from scripts.arena_cafe.ct03_evaluator_preflight import preflight
from scripts.arena_cafe.ct03_world_custody import prepare_private
from scripts.arena_cafe.ct03_prospective_lock import seal
from test_arena_ct03_execution_boundary import credentials, signed
from test_arena_ct03_prospective_lock import fixture as lock_fixture


def fixture(root):
    _, secret, public, registry=credentials(root)
    producer=root/"producer"
    producer.mkdir()
    construction, _, d, m, entries=lock_fixture(producer)
    from scripts.arena_cafe.ct03_prospective_lock import PROTOCOL
    config={
        "world_public_id":"W1", "stage_count":2, "capacity":2.1,
        "response_time":0.8,"custody_nonce":"FIXTURE_ONLY_NONCE_0123456789",
        "protocol_sha256":digest(json.loads(PROTOCOL.read_text(encoding="utf-8"))),
    }
    private=root/"isolated-evaluator-workspace"
    commitment=prepare_private(config,private)
    lock=seal(construction,commitment,d,m,entries)
    statement={
        "case_id":"CT-03", "world_public_id":"W1",
        "lock_sha256":lock["lock_sha256"],
        "protocol_sha256":lock["protocol_sha256"],
        "world_commitment_sha256":lock["world_commitment_sha256"],
        "archive_id":"TEST_ONLY_ARCHIVE_123456",
        "archived_before_evaluator_access":True,
    }
    witness=signed(root,statement,"LOCK_ARCHIVE","TEST_ARCHIVER",secret)
    return producer,private,lock,witness,registry,public,config,secret


class EvaluatorPreflightTests(unittest.TestCase):
    def test_private_source_separation_and_lock_are_verified_no_truth(self):
        with TemporaryDirectory() as tmp:
            producer,private,lock,witness,registry,key,config,secret=fixture(Path(tmp))
            result=preflight(
                lock=lock,archive_witness=witness,trust_registry=registry,
                archive_public_key=key,producer_root=producer,
                evaluator_private_dir=private)
            self.assertEqual(result["status"],
                "ARCHIVED_LOCK_AND_PRIVATE_SOURCE_BOUND_NOT_READY_FOR_TRUTH_REVEAL")
            self.assertFalse(result["reserved_truth_opened"])
            self.assertFalse(result["score_computed"])
            self.assertFalse(result["actual_world_solver_execution_verified"])
            # no private parameters/graph/world config or reserved samples returned
            self.assertNotIn("stage_count",repr(result))
            self.assertNotIn("capacity",repr(result))
            self.assertNotIn("observations",repr(result))

    def test_invalid_archival_signature_is_checked_before_private_access(self):
        with TemporaryDirectory() as tmp:
            producer,private,lock,witness,registry,key,config,secret=fixture(Path(tmp))
            mutated=copy.deepcopy(witness)
            mutated["statement"]["lock_sha256"]="sha256:"+"e"*64
            mutated["statement_sha256"]=digest(mutated["statement"])
            # Even an invalid path cannot be opened before the archive check.
            with self.assertRaisesRegex(ValueError,"SIGNATURE_NOT_VERIFIED"):
                preflight(lock=lock,archive_witness=mutated,
                          trust_registry=registry,archive_public_key=key,
                          producer_root=producer,
                          evaluator_private_dir=Path(tmp)/"absent_private")

    def test_private_world_mismatch_and_producer_mount_are_rejected(self):
        with TemporaryDirectory() as tmp:
            producer,private,lock,witness,registry,key,config,secret=fixture(Path(tmp))
            world=private/"private_world.mo"
            world.write_bytes(world.read_bytes()+b"\nTAMPER")
            with self.assertRaisesRegex(ValueError,"WORLD_OR_PROTOCOL_BYTES_DIVERGED"):
                preflight(lock=lock,archive_witness=witness,
                          trust_registry=registry,archive_public_key=key,
                          producer_root=producer,evaluator_private_dir=private)
            # A copied private directory inside the producer workspace is
            # forbidden even if all of its bytes match a valid commitment.
            embedded=producer/"evaluator-private"
            import shutil
            shutil.copytree(private,embedded)
            with self.assertRaisesRegex(ValueError,"INSIDE_PRODUCER_BOUNDARY"):
                preflight(lock=lock,archive_witness=witness,
                          trust_registry=registry,archive_public_key=key,
                          producer_root=producer,evaluator_private_dir=embedded)

    def test_real_cli_fixture_and_tamper_fails_without_output(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            producer,private,lock,witness,registry,key,config,secret=fixture(root)
            (root/"lock.json").write_text(json.dumps(lock))
            (root/"archive.json").write_text(json.dumps(witness))
            output=root/"preflight.json"
            args=[sys.executable,"-m","scripts.arena_cafe.ct03_evaluator_preflight",
                  "--lock",str(root/"lock.json"),
                  "--archive-witness",str(root/"archive.json"),
                  "--trust-registry",str(registry),
                  "--archive-public-key",str(key),
                  "--producer-root",str(producer),
                  "--evaluator-private-dir",str(private),
                  "--out",str(output)]
            repo=Path(__file__).resolve().parents[1]
            success=subprocess.run(args,cwd=repo,capture_output=True,text=True,
                                   timeout=30)
            self.assertEqual(success.returncode,0,success.stderr)
            self.assertTrue(output.exists())
            self.assertEqual(json.loads(output.read_text())["reserved_truth_opened"],False)
            # Archive cannot be reused against a different locked body.
            tampered=copy.deepcopy(lock)
            tampered["rows"][0]["material_group"]="sha256:"+"f"*64
            (root/"lock.json").write_text(json.dumps(tampered))
            fail_output=root/"tampered-preflight.json"
            denied=subprocess.run(args[:-1]+[str(fail_output)],cwd=repo,
                                  capture_output=True,text=True,timeout=30)
            self.assertNotEqual(denied.returncode,0)
            self.assertIn("CT03_LOCK_SEAL_TAMPERED_OR_OVERCLAIMED",denied.stderr)
            self.assertFalse(fail_output.exists())


if __name__=="__main__":
    unittest.main()
