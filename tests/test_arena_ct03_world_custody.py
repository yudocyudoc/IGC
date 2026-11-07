"""CT-03 world factory is evaluator-private, unselected and never run by CI."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_cafe.ct03_world_custody import (
    validate, make_private_source, prepare_private
)


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


if __name__=="__main__":
    unittest.main()
