"""CT-03 world factory is evaluator-private, unselected and never run by CI."""
from copy import deepcopy
import json
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_cafe.ct03_world_custody import (
    validate, make_private_source, prepare_private
)
from scripts.arena_v0_contract import digest
from scripts.arena_cafe.ct03_prospective_lock import PROTOCOL


def fixture(n=2):
    return {"world_public_id":"FIXTURE_NOT_ACTUAL_CT03",
            "stage_count":n,
            "capacity":2.1,
            "response_time":0.8,
            "custody_nonce":"FIXTURE_NONCE_PRIVATE_1234567890",
            "protocol_sha256":"sha256:"+"a"*64}


class WorldFactoryTest(unittest.TestCase):
    def test_two_three_stage_sources_only_original_e1_classes(self):
        for n in (2,3):
            modelica,commands,graph,key=make_private_source(fixture(n))
            stages=[x for x in graph["instances"]
                    if x["role"] in ("preparation","dispatch","transit")]
            self.assertEqual(len(stages),n)
            self.assertEqual(commands.count("simulate("),1)
            self.assertEqual(commands.count('method="euler"'),1)
            self.assertIn("Modelica.Blocks.Sources.RealExpression stimulus(y=if time < 2 then 1.7 else 0);",modelica)
            self.assertFalse(any(x["role"]=="report" for x in graph["instances"]))

    def test_private_manifest_and_public_commitment_separated(self):
        with TemporaryDirectory() as tmp:
            out=Path(tmp)/"private"
            result=prepare_private(fixture(),out)
            self.assertEqual(result["omc_executed"],0)
            self.assertEqual(result["provider_calls"],0)
            self.assertEqual(result["status"],"WORLD_COMMITTED_NOT_EXECUTED_NO_PUBLIC_CONSTRUCTION_YET")
            self.assertNotIn("capacity",str(result))
            self.assertNotIn("stage_count",str(result))
            self.assertTrue((out/"private-manifest.json").is_file())
            self.assertTrue((out/"private_world.mo").is_file())
            with self.assertRaisesRegex(ValueError,"PRIVATE_OUTPUT_EXISTS"):
                prepare_private(fixture(),out)

    def test_param_range_stage_nonce_and_lock_fail_closed(self):
        for key,value in (("stage_count",4),("capacity",3.4),
                          ("response_time",.2),("custody_nonce","too-short"),
                          ("protocol_sha256","missing")):
            config=fixture()
            config[key]=value
            with self.assertRaises(ValueError,msg=key):
                validate(config)


    def test_cli_guards_private_root_and_frozen_protocol_before_creating_world(self):
        """No private config/world may reside under producer or code checkout."""
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            producer=root/"producer"
            producer.mkdir()
            config=fixture()
            config["protocol_sha256"]=digest(json.loads(
                PROTOCOL.read_text(encoding="utf-8")))
            private_config=root/"sealed-config.json"
            private_config.write_text(json.dumps(config),encoding="utf-8")
            private_out=root/"custodian-private"
            public=root/"public-commitment.json"
            repo=Path(__file__).resolve().parents[1]
            base=[
                sys.executable,"-m","scripts.arena_cafe.ct03_world_custody",
                "--sealed-config",str(private_config),
                "--private-out",str(private_out),
                "--public-commitment",str(public),
                "--producer-root",str(producer),
            ]
            env={**os.environ,
                 "IGC_CT03_CUSTODIAN_AUTH":"CT03_POST_LOCK_CUSTODIAN_ONLY"}
            good=subprocess.run(base,cwd=repo,env=env,capture_output=True,
                                text=True,timeout=30)
            self.assertEqual(good.returncode,0,good.stderr)
            self.assertTrue((private_out/"private-manifest.json").is_file())
            self.assertTrue(public.is_file())
            forbidden=repo/"artifacts/DO_NOT_CREATE_TEST_PRIVATE"
            wrong=[
                sys.executable,"-m","scripts.arena_cafe.ct03_world_custody",
                "--sealed-config",str(private_config),
                "--private-out",str(forbidden),
                "--public-commitment",str(root/"bad-commitment.json"),
                "--producer-root",str(producer),
            ]
            rejected=subprocess.run(wrong,cwd=repo,env=env,capture_output=True,
                                    text=True,timeout=30)
            self.assertNotEqual(rejected.returncode,0)
            self.assertIn("CT03_WORLD_PRIVATE_PATH_INSIDE_REPO_OR_PRODUCER",
                          rejected.stderr)
            self.assertFalse(forbidden.exists())


if __name__=="__main__":
    unittest.main()
