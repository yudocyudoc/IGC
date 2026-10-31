#!/usr/bin/env python3
"""CAF-03 integration: real DES, four pre-K2 forecasts, policy invariants."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import caf03_laboratorio_politicas as caf
from experiments.cafeteria.pc01 import caf01_des_engine as des


class Caf03Test(unittest.TestCase):
    def test_three_fixed_physical_worlds_share_bottleneck_station(self):
        scenarios=caf.specs()
        self.assertEqual([s["id"] for s in scenarios],list("FGH"))
        self.assertEqual([s["nominal_capacity_orders_per_hour"]
                          for s in scenarios],[70.,90.,110.])
        self.assertEqual(caf.K1,{"rate_per_minute":1.5,"t_min":20})
        self.assertEqual(caf.POLICIES,("original","absolute_only"))
        for s in scenarios:
            stages=s["config"]["stages"]
            self.assertEqual(len(stages),3)
            self.assertEqual([x["servers"] for x in stages],[2,1,2])
            self.assertEqual(stages[0]["service_minutes"],"1")
            self.assertEqual(stages[2]["service_minutes"],"1")
        self.assertIsInstance(caf.policy_guard(),dict)

    def test_each_K1_and_K2_called_after_all_relevant_forecasts_are_on_disk(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/"caf03"
            called=[]
            original=des.run_toy_engine
            policy_bytes=caf.d.POLICY.read_bytes()

            def instrument(config,arrivals,obs):
                names=[name for name in caf.NAMES if
                       caf.scenario(name)["config"]==config]
                self.assertEqual(len(names),1)
                name=names[0]
                w=root/("mundo_"+name)
                if len(arrivals)==30:  # first and only K1 per world
                    called.append((name,"K1"))
                    self.assertTrue((root/"00_PLAN_PREDECLARADO.json").is_file())
                    self.assertTrue((w/"02_CANDIDATOS_Y_PREDICCIONES_ANTES_DE_K1.json").is_file())
                    self.assertTrue((w/"02B_CHECKPOINT_PRE_K1.json").is_file())
                    self.assertFalse((w/"03_K1.json").exists())
                    prior=json.loads((w/"02_CANDIDATOS_Y_PREDICCIONES_ANTES_DE_K1.json").read_text())
                    self.assertFalse(prior["K1_seen"])
                    self.assertFalse(prior["K2_seen"])
                    self.assertEqual(set(prior["K2_forecasts_K0_by_variant"]),
                                     {"M","D"})
                    for arm in ("M","D"):
                        self.assertEqual(set(prior["K2_forecasts_K0_by_variant"][arm]),
                                         {"original","absolute_only"})
                elif len(arrivals)==27:  # first and only K2 per world
                    called.append((name,"K2"))
                    self.assertTrue((w/caf.FORECAST).is_file())
                    self.assertTrue((w/"05B_CHECKPOINT_PRE_K2.json").is_file())
                    self.assertTrue((w/"04_CANDIDATOS_POST_K1.json").is_file())
                    self.assertFalse((w/"06_K2_OBSERVADO.json").exists())
                    predicted=json.loads((w/caf.FORECAST).read_text())
                    cp=json.loads((w/"05B_CHECKPOINT_PRE_K2.json").read_text())
                    self.assertFalse(predicted["K2_truth_seen"])
                    self.assertFalse(cp["K2_truth_seen"])
                    self.assertEqual(cp["K2_DES_calls_so_far"],0)
                    self.assertEqual(cp["four_policy_forecast_sha256"],
                                     caf.lab.sha((w/caf.FORECAST).read_bytes()))
                    self.assertEqual(set(predicted["K1_K2_posterior_by_arm_policy"]),
                                     {"M","D"})
                    self.assertEqual(set(predicted["K0_K2_prior_by_arm_policy"]),
                                     {"M","D"})
                    for arm in ("M","D"):
                        self.assertEqual(set(predicted[
                            "K1_K2_posterior_by_arm_policy"][arm]),
                            {"original","absolute_only"})
                else:
                    self.assertEqual(len(arrivals),24)  # K0
                    called.append((name,"K0"))
                return original(config,arrivals,obs)

            with patch.object(des,"run_toy_engine",side_effect=instrument):
                report=caf.run(root)

            self.assertEqual(called,[(name,cut) for name in "FGH"
                                       for cut in ("K0","K1","K2")])
            self.assertEqual(report["world_count"],3)
            self.assertEqual(report["DES_exploratory_runs"],9)
            self.assertEqual(report["DES_confirmatory_runs"],0)
            self.assertFalse(report["external_custody"])
            self.assertEqual(caf.d.POLICY.read_bytes(),policy_bytes)
            self.assertTrue(report["original_CAF02_policy_unchanged"])
            for row in report["worlds"]:
                self.assertEqual(row["K2"][-1],27)
                self.assertGreaterEqual(row["K1"],0)
                self.assertLessEqual(row["K1"],30)
                self.assertEqual(set(row["variant_results"]),{"M","D"})
                for arm in ("M","D"):
                    o=row["variant_results"][arm]["original"]
                    a=row["variant_results"][arm]["absolute_only"]
                    for which in ("K0","K1"):
                        self.assertGreaterEqual(sum(
                            a[which+"_count_by_family"].values()),
                            sum(o[which+"_count_by_family"].values()))
                    for variant in (o,a):
                        loss=variant["K1_loss"]
                        if loss is None:
                            self.assertIsNone(variant["K1_width_half_mean"])
                            self.assertIsNone(variant["K1_outside_mean"])
                            self.assertIsNone(variant["K1_coverage"])
                        else:
                            self.assertAlmostEqual(loss,
                                variant["K1_width_half_mean"]+
                                variant["K1_outside_mean"],places=7)
                w=root/("mundo_"+row["world"])
                manifest=json.loads((w/"09_MANIFIESTO.json").read_text())
                self.assertFalse(manifest["external_custody"])
                self.assertTrue(manifest[
                    "pre_K2_forecasts_written_before_DES_K2"])
                for p,h in manifest["files_sha256"].items():
                    self.assertEqual(caf.lab.sha((w/p).read_bytes()),h)
            summary_csv=(root/"02_COMPARACION.csv").read_text()
            self.assertEqual(len(summary_csv.splitlines()),13)
            report_md=(root/"03_INFORME.md").read_text()
            self.assertIn("Tres mundos nuevos",report_md)
            self.assertIn("Anchura/2",report_md)
            digest=json.loads((root/"04_HASHES.json").read_text())["files_sha256"]
            for f,h in digest.items():
                self.assertEqual(caf.lab.sha((root/f).read_bytes()),h)
            with self.assertRaisesRegex(ValueError,"CAF03_OUTPUT_ALREADY_EXISTS"):
                caf.run(root)

    def test_stop_after_all_four_predictions_prevents_k2(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/"stopped"
            called=[]
            original=des.run_toy_engine
            def instrument(config,arrivals,times):
                called.append(len(arrivals))
                return original(config,arrivals,times)

            def stop(w):
                self.assertTrue((w/caf.FORECAST).is_file())
                self.assertTrue((w/"05B_CHECKPOINT_PRE_K2.json").is_file())
                raise RuntimeError("STOP_BEFORE_K2_TEST")

            with patch.object(des,"run_toy_engine",side_effect=instrument):
                with self.assertRaisesRegex(RuntimeError,"STOP_BEFORE_K2_TEST"):
                    caf.run(root,before_k2_hook=stop)
            self.assertEqual(called,[24,30])
            self.assertFalse((root/"mundo_F"/"06_K2_OBSERVADO.json").exists())
            self.assertFalse((root/"01_RESULTADOS.json").exists())
            with self.assertRaisesRegex(ValueError,"CAF03_OUTPUT_ALREADY_EXISTS"):
                caf.run(root)

    def test_stop_before_k1_prevents_k1_and_k2(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/"before_K1"
            called=[]
            orig=des.run_toy_engine
            def f(config,arrivals,times):
                called.append(len(arrivals))
                return orig(config,arrivals,times)
            def stop(folder):
                self.assertTrue((folder/"02B_CHECKPOINT_PRE_K1.json").exists())
                raise RuntimeError("STOP_BEFORE_K1_TEST")
            with patch.object(des,"run_toy_engine",side_effect=f):
                with self.assertRaisesRegex(RuntimeError,"STOP_BEFORE_K1_TEST"):
                    caf.run(root,before_k1_hook=stop)
            self.assertEqual(called,[24])


if __name__=="__main__":unittest.main()
