#!/usr/bin/env python3
"""Five-world CAF02 exploratory test, including REAL DES output and leakage."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import caf02_lab_exploratorio as lab
import caf02_lab_matriz_cinco_mundos as matrix
from experiments.cafeteria.pc01 import caf01_des_engine as des


class MatrixTest(unittest.TestCase):
    def test_five_worlds_are_declared_before_outcomes_and_A_unchanged(self):
        rows=matrix.fixed_specs()
        self.assertEqual([x["id"] for x in rows],list("ABCDE"))
        self.assertEqual([x["capacity_orders_per_hour"] for x in rows],
                         [80.,60.,60.,60.,120.])
        self.assertEqual(rows[0]["config"],lab.WORLD)
        self.assertEqual(rows[0]["world_name"],lab.VERSION)
        for x in rows:
            self.assertEqual(len(x["config"]["stages"]),3)
            self.assertTrue(x["world_name"].startswith("CAF02_LAB_WORLD_"))
        for label in "BCD":
            self.assertEqual(sorted([x["servers"]
                for x in matrix.spec(label)["config"]["stages"]]),[1,2,2])
        self.assertEqual([x["servers"] for x in
                          matrix.spec("E")["config"]["stages"]],[2,2,2])

    def test_k2_cannot_be_simulated_until_each_world_forecasts_written(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)/"matrix"
            attempts=[]
            original=des.run_toy_engine
            before_policy=lab.d.POLICY.read_bytes()

            def intercepted(config,arrivals,obs):
                if len(arrivals)==27:
                    world_id=next(tag for tag in matrix.NAMES
                                  if matrix.spec(tag)["config"]==config)
                    w=folder/("mundo_"+world_id)
                    self.assertTrue((folder/"00_PLAN_FIJO.json").is_file())
                    self.assertTrue((w/"02_G4a_PRE_K1.json").is_file())
                    self.assertTrue((w/"04_G4b_PRE_K2.json").is_file())
                    self.assertTrue((w/lab.FORECAST_FILE).is_file())
                    self.assertTrue((w/"05B_CHECKPOINT_PRE_K2.json").is_file())
                    self.assertFalse((w/"06_K2_OBSERVADO.json").exists())
                    chk=json.loads((w/"05B_CHECKPOINT_PRE_K2.json").read_bytes())
                    self.assertFalse(chk["K2_truth_seen"])
                    self.assertEqual(chk["DES_K2_runs_so_far"],0)
                    attempts.append(world_id)
                return original(config,arrivals,obs)

            with patch.object(des,"run_toy_engine",side_effect=intercepted):
                result=matrix.run_matrix(folder)
            self.assertEqual(attempts,list("ABCDE"))
            self.assertEqual(result["world_count"],5)
            self.assertEqual(result["status"],
                "FIVE_PUBLIC_DES_EXPLORATORY_WORLDS_EXECUTED")
            self.assertEqual(result["DES_confirmatory_runs"],0)
            self.assertEqual(result["new_OpenModelica_calls"],0)
            self.assertEqual(result["provider_calls"],0)
            self.assertFalse(result["external_custody_verified"])
            self.assertEqual(lab.d.POLICY.read_bytes(),before_policy)
            self.assertEqual(result["DES_lab_runs"],
                sum(r["DES_lab_runs"] for r in result["worlds"]))
            self.assertGreaterEqual(result["DES_lab_runs"],10)
            self.assertLessEqual(result["DES_lab_runs"],15)
            self.assertEqual(result["worlds"][0]["K0_D5"],2)
            self.assertEqual(result["worlds"][0]["K0_D10"],8)
            self.assertEqual(result["worlds"][0]["K2_des"],
                             [2,8,15,22,27,27])
            for entry in result["worlds"]:
                self.assertEqual(entry["confirmatory_DES_runs"],0)
                self.assertEqual(len(entry["K2_des"]),6)
                self.assertEqual(set(entry["M"]["family_K1"]),{"C00","C01"})
                self.assertEqual(set(entry["D"]["family_K1"]),
                                 {"D1","D2","D3"})
                for arm in ("M","D"):
                    scored=entry[arm]
                    if scored["paired"]:
                        self.assertIsInstance(scored["gain"],float)
                    else:
                        self.assertIsNone(scored["gain"])
                w=folder/("mundo_"+entry["id"])
                m=json.loads((w/"11_MANIFIESTO.json").read_bytes())
                self.assertTrue(m["K2_priors_written_before_K2"])
                self.assertFalse(m["external_custody_verified"])
                for name,digest in m["files_sha256"].items():
                    self.assertEqual(lab.sha((w/name).read_bytes()),digest)
            csv=(folder/"02_COMPARACION.csv").read_text()
            self.assertEqual(len(csv.splitlines()),6)
            report=(folder/"03_INFORME.md").read_text()
            self.assertIn("REF_SCALE",report)
            self.assertIn("Cinco mundos",report)
            self.assertIn("no",report.lower())
            digest=json.loads((folder/"04_ARCHIVOS_SHA256.json").read_bytes())
            for name,h in digest["files"].items():
                self.assertEqual(lab.sha((folder/name).read_bytes()),h)
            with self.assertRaisesRegex(ValueError,"MATRIX_OUTPUT_ALREADY_EXISTS"):
                matrix.run_matrix(folder)

    def test_original_world_A_output_remains_default_without_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=lab.run_lab(Path(tmp)/"default_A")
            self.assertEqual(a["world_name"],lab.VERSION)
            self.assertEqual(a["world_parameters"],lab.WORLD)
            self.assertEqual(a["K0"]["delivered_t5"],2)
            self.assertEqual(a["K2"]["delivered"],[2,8,15,22,27,27])


if __name__=="__main__":
    unittest.main()
