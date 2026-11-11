"""RF-02G static/pre-solver adversarial checks; real OMC is validated in CI."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_cafe import r2_causal_g2 as g
from scripts.arena_v0_contract import ArenaContractError


class CausalSixD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=os.environ.get("RF02_PUBLIC_DIR")
        if not root:
            raise unittest.SkipTest("Use frozen RF02_PUBLIC_DIR for O0")
        cls.visible=json.loads((Path(root)/"O0_VISIBLE.json").read_text())
        cls.fixture=json.loads((Path("tests/fixtures/rf02_g2_fixture_nominals.json")).read_text())

    def test_fixture_explicitly_not_empirical_and_not_e1(self):
        p=g.validate_fixture(self.fixture)
        self.assertEqual({"capacity","response_time","loss_time"},set(p))
        self.assertEqual([1.23,2.7,8.1],
            [p[x]["value"] for x in ("capacity","response_time","loss_time")])
        self.assertNotEqual([20/60,30,30],
            [p[x]["value"] for x in ("capacity","response_time","loss_time")])
        for edit in ("scope","not_ev01_empirical_estimate","source_ref"):
            x=deepcopy(self.fixture)
            if edit=="source_ref":
                x["parameters"]["capacity"]["source_ref"]="other_arm_E1_registry"
            elif edit=="scope":
                x["scope"]="SCIENCE_PREDICTION"
            else:
                x["not_ev01_empirical_estimate"]=False
            with self.subTest(edit=edit),self.assertRaises(ArenaContractError):
                g.validate_fixture(x)

    def test_prepare_generates_six_native_models_without_simulation(self):
        with TemporaryDirectory() as temp:
            out=Path(temp)/"native"
            m=g.prepare(self.visible,"O0",self.fixture,out)
            self.assertEqual("NOT_RUN_UNTIL_REAL_CSV",m["G2"])
            self.assertEqual(6,m["candidate_count"])
            self.assertTrue(m["nominal_parameters_are_non_empirical"])
            self.assertEqual("PARTIAL", "PARTIAL")
            self.assertEqual(6,len({x["structure_hash"] for x in m["candidates"]}))
            self.assertEqual(6,len(list(out.glob("*.mo"))))
            self.assertEqual(1,len(list(out.glob("*.mos"))))
            self.assertEqual(0,len(list(out.glob("*_res.csv"))))
            self.assertNotIn("compare_with_EV01_deliveries",str(m))
            self.assertIn("numberOfIntervals=2000",
                          (out/"simulate.mos").read_text())
            self.assertEqual(6,(out/"simulate.mos").read_text().count("simulate("))
            for item in m["candidates"]:
                model=(out/item["modelica_file"]).read_text()
                self.assertIn("inputRate = (if time >=",model)
                self.assertNotIn("pulseDuration",model)
                self.assertNotIn("pulseRate",model)
                self.assertTrue(item["equations_original_native"])
                self.assertEqual("NOT_RUN",item["G3"])
                self.assertEqual(item["modelica_sha256"],
                                 g.sha_file(out/item["modelica_file"]))

    def test_verify_cannot_pass_with_no_real_solver_attempt(self):
        with TemporaryDirectory() as temp:
            out=Path(temp)/"native"
            g.prepare(self.visible,"O0",self.fixture,out)
            with self.assertRaisesRegex(ArenaContractError,
                                        "RF02G_NO_REAL_SOLVER_SUCCESS"):
                g.verify(self.visible,out)
            (out/"INVOCATION_STARTED").write_text("INVOCATION_STARTED\n")
            (out/"exit_code.txt").write_text("1\n")
            with self.assertRaisesRegex(ArenaContractError,
                                        "RF02G_NO_REAL_SOLVER_SUCCESS"):
                g.verify(self.visible,out)
            (out/"exit_code.txt").write_text("0\n")
            with self.assertRaisesRegex(ArenaContractError,
                                        "RF02G_MODEL_OR_SOLVER_OUTPUT_UNAUTHENTICATED"):
                g.verify(self.visible,out)

    def test_source_and_condition_tampering_rejected(self):
        with TemporaryDirectory() as temp:
            out=Path(temp)/"native"
            g.prepare(self.visible,"O0",self.fixture,out)
            bad=deepcopy(self.visible)
            bad["construction"]["observation_series"][-1][
                "delivered_cumulative"]=0
            with self.assertRaises(ArenaContractError):
                g.verify(bad,out)
            bad_manifest=json.loads((out/"manifest.json").read_text())
            bad_manifest["G3"]="PASS"
            (out/"manifest.json").write_text(json.dumps(bad_manifest))
            with self.assertRaisesRegex(ArenaContractError,
                                        "RF02G_FALSE_NATIVE_OR_PREVIOUS_G2_CLAIM"):
                g.verify(self.visible,out)


if __name__=="__main__":
    unittest.main()
