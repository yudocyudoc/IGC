"""Strict public five-file handoff; entirely synthetic, never archived lock."""
import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_v0_contract import digest
from scripts.arena_cafe.ct03_producer_freeze_handoff import pack,FILES
from scripts.arena_cafe.ct03_prospective_lock import seal,PROTOCOL
from scripts.arena_cafe.ct03_public import PUBLIC_INPUT
from scripts.arena_cafe.ct03_world_custody import PUBLIC_SCHEMA
from test_arena_ct03_assemble_entries import fixture
from test_arena_ct03_b_own_feedback import public

def commitment():
    protocol=json.loads(PROTOCOL.read_text())
    return {
        "schema":PUBLIC_SCHEMA,"world_public_id":public()["world_public_id"],
        "source_definition_sha256":digest(PUBLIC_INPUT),
        "private_commitment_sha256":"sha256:"+"d"*64,
        "protocol_sha256":digest(protocol),
        "status":"WORLD_COMMITTED_NOT_EXECUTED_NO_PUBLIC_CONSTRUCTION_YET",
        "evaluator_boundary":"PROCEDURAL_JOB_ISOLATION_NOT_OS_ACL_PROOF",
        "omc_executed":0,"provider_calls":0
    }

class BProducerFreezeHandoffTests(unittest.TestCase):
    def test_thirteen_own_slots_are_exactly_five_public_freeze_inputs(self):
        with TemporaryDirectory(dir=".") as tmp:
            root=Path(tmp).relative_to(Path.cwd())
            d12,b13,d,m=fixture(root/"source")
            target=root/"bundle"
            result=pack(dm_projection=d12,b_projection=b13,
                        construction=public(),commitment=commitment(),
                        d_manifest=d,m_manifest=m,out=target)
            files={str(x.relative_to(target)) for x in target.rglob("*") if x.is_file()}
            self.assertEqual(files,set(FILES))
            self.assertEqual(result["candidate_count"],13)
            self.assertFalse(result["reserved_truth_read"])
            entries=json.loads((target/"entries.json").read_text())
            c=json.loads((target/"world-commitment.json").read_text())
            lock=seal(public(),c,d,m,entries)
            self.assertEqual(lock["candidate_count"],13)
            self.assertFalse(lock["reserved_truth_opened"])
            self.assertFalse((target/"lock.json").exists())
            self.assertFalse((target/"private-manifest.json").exists())
            self.assertFalse((target/"sealed_world_res.csv").exists())

    def test_wrong_protocol_missing_slot_and_overwrite_refused(self):
        with TemporaryDirectory(dir=".") as tmp:
            root=Path(tmp).relative_to(Path.cwd())
            d12,b13,d,m=fixture(root/"source")
            args=dict(dm_projection=d12,b_projection=b13,construction=public(),
                      commitment=commitment(),d_manifest=d,m_manifest=m,
                      out=root/"bundle")
            bad=copy.deepcopy(args["commitment"])
            bad["protocol_sha256"]="sha256:"+"f"*64
            with self.assertRaisesRegex(ValueError,"COMMITMENT_OR_PROTOCOL"):
                pack(**{**args,"commitment":bad})
            self.assertFalse((root/"bundle").exists())
            missing=copy.deepcopy(d12);missing["rows"].pop()
            with self.assertRaisesRegex(ValueError,"SCOPE_OR_STATUS"):
                pack(**{**args,"dm_projection":missing})
            self.assertFalse((root/"bundle").exists())
            pack(**args)
            with self.assertRaisesRegex(ValueError,"REFUSE_OVERWRITE"):
                pack(**args)

if __name__=="__main__":
    unittest.main()
