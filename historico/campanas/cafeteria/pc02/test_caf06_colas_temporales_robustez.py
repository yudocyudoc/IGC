#!/usr/bin/env python3
"""CAF-06: actual new DES, frozen sensor rule, no illicit M/D stage mapping."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import caf06_colas_temporales_robustez as ex
from experiments.cafeteria.pc01 import caf01_des_engine as des


class Caf06Tests(unittest.TestCase):
    def test_world_grid_and_preset_policies(self):
        worlds=ex.specs()
        self.assertEqual(len(worlds),9)
        self.assertEqual([w["id"] for w in worlds],
                         [f"W{c}{s}" for c in (65,85,95) for s in "PDE"])
        self.assertEqual({w["nominal_capacity_per_hour"] for w in worlds},
                         {65,85,95})
        for w in worlds:
            stocks=des.validate_private_config(w["config"])
            i=ex.STAGES.index(w["true_bottleneck"])
            self.assertEqual([x[0] for x in stocks],
                             [1 if k==i else 2 for k in range(3)])
            self.assertEqual(stocks[i][1],des.Fraction(
                60,w["nominal_capacity_per_hour"]))
        b=ex.frozen_baseline()
        self.assertEqual(b["classifier"]["prototypes"],
                         {"preparacion":1,"despacho":6,"entrega":2})
        self.assertEqual(ex.QUEUE_RULE["observations_t_min"],[10,20])
        self.assertEqual(len(ex.STAGES),3)

    def test_rule_abstains_on_no_growth_and_ties_without_truth_label(self):
        p=ex.diagnose_growth
        self.assertEqual(p([0,0,0],[0,0,0])["status"],
                         "ABSTAIN_NO_POSITIVE_GROWTH")
        self.assertIsNone(p([0,0,0],[0,0,0])["predicted_bottleneck"])
        self.assertEqual(p([0,0,0],[2,2,0])["status"],
                         "ABSTAIN_TIED_GROWTH")
        self.assertEqual(p([0,0,0],[0,4,0])["predicted_bottleneck"],
                         "despacho")
        self.assertEqual(p([1,1,0],[3,1,0])["predicted_bottleneck"],
                         "preparacion")
        # Positive absolute wait at t20 is insufficient if no growth.
        self.assertEqual(p([5,0,0],[5,0,0])["status"],
                         "ABSTAIN_NO_POSITIVE_GROWTH")

    def test_real_27_DES_calls_all_after_precommitted_plan(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/"caf06"
            original=des.run_toy_engine
            seen=[]
            policy_before=ex.prior.d.POLICY.read_bytes()
            prior_before=ex.prior.REF_PATH.read_bytes()

            def instrument(config,arrivals,observations):
                plan=root/"00_PLAN_PRE_DES.json"
                checkpoint=root/"00B_CHECKPOINT_PRE_DES.json"
                self.assertTrue(plan.is_file())
                self.assertTrue(checkpoint.is_file())
                self.assertFalse((root/"01_RESULTADOS.json").exists())
                self.assertEqual(observations,(0,10,20,40))
                d=json.loads(plan.read_bytes())
                c=json.loads(checkpoint.read_bytes())
                self.assertFalse(d["future_world_outcomes_seen"])
                self.assertEqual(d["world_executions_before_plan"],0)
                self.assertEqual(c["DES_calls_so_far"],0)
                self.assertEqual(c["source_plan_sha256"],
                                 ex.lab.sha(plan.read_bytes()))
                self.assertEqual(d["CAF02_official_policy_SHA256"],
                                 ex.lab.sha(policy_before))
                self.assertEqual(d["CAF05_frozen_baseline"]["classifier"][
                    "prototypes"],{"preparacion":1,"despacho":6,"entrega":2})
                self.assertEqual(d["three_queue_frozen_rule"],ex.QUEUE_RULE)
                self.assertEqual(len(d["worlds"]),9)
                self.assertEqual(d["demands"],dict(ex.RATES))
                seen.append((config,len(arrivals)))
                return original(config,arrivals,observations)

            with patch.object(des,"run_toy_engine",side_effect=instrument):
                report=ex.run(root)
            self.assertEqual(len(seen),27)
            self.assertEqual([n for _,n in seen],[16,30,36]*9)
            self.assertEqual(report["DES_runs"],27)
            self.assertEqual(report["world_count"],9)
            self.assertEqual(report["DES_confirmatory_runs"],0)
            self.assertTrue(report["comparison_not_equal_information"])
            self.assertTrue(report["M_D_stage_stock_mapping_already_blocked"])
            self.assertEqual(ex.prior.d.POLICY.read_bytes(),policy_before)
            self.assertEqual(ex.prior.REF_PATH.read_bytes(),prior_before)
            self.assertEqual(len(report["observations"]),27)
            self.assertEqual(set(report["comparisons"]),{
                "LOW","MATCHED","HIGH"})
            for x in report["observations"]:
                for key in ("t10","t20"):
                    point=x[key]
                    self.assertEqual(
                        sum(point["stock_by_stage"].values()),
                        point["total_pending"])
                    self.assertEqual(
                        point["accepted"],
                        point["delivered"]+point["total_pending"])
                    for stage in ex.STAGES:
                        self.assertEqual(
                            point["waiting_by_stage"][stage]+
                            point["in_service_by_stage"][stage],
                            point["stock_by_stage"][stage])
                self.assertEqual(x["three_queue_temporal_rule"][
                    "growth_by_stage"],{
                    stage:x["t20"]["waiting_by_stage"][stage]-
                    x["t10"]["waiting_by_stage"][stage]
                    for stage in ex.STAGES})
                if x["rate_name"]!="MATCHED":
                    self.assertEqual(
                        x["one_sensor_CAF05_fixed_baseline"]["status"],
                        "NOT_APPLIED_OUTSIDE_CAF05_1_5_PER_MIN")
                    self.assertIsNone(
                        x["one_sensor_CAF05_fixed_baseline"]["prediction"])
            self.assertEqual(len((root/"02_COMPARACION.csv").read_text().splitlines()),
                             28)
            self.assertIn("Observaciones combinadas",
                          (root/"03_INFORME.md").read_text())
            manifest=json.loads((root/"04_MANIFIESTO.json").read_bytes())
            self.assertTrue(manifest[
                "pre_DES_plan_and_checkpoint_written"])
            for filename,sha in manifest["files_sha256"].items():
                self.assertEqual(ex.lab.sha((root/filename).read_bytes()),sha)
            with self.assertRaisesRegex(ValueError,"CAF06_OUTPUT_ALREADY_EXISTS"):
                ex.run(root)

    def test_failed_first_DES_not_substituted_and_plan_retained(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/"fail"
            called=[]
            def deny(*args,**kwargs):
                called.append(True)
                self.assertTrue((root/"00_PLAN_PRE_DES.json").exists())
                self.assertTrue((root/"00B_CHECKPOINT_PRE_DES.json").exists())
                raise RuntimeError("INTENTIONAL_FIRST_DES_ABORT")
            with patch.object(des,"run_toy_engine",side_effect=deny):
                with self.assertRaisesRegex(RuntimeError,
                                            "INTENTIONAL_FIRST_DES_ABORT"):
                    ex.run(root)
            self.assertEqual(len(called),1)
            self.assertFalse((root/"01_RESULTADOS.json").exists())
            with self.assertRaisesRegex(ValueError,"CAF06_OUTPUT_ALREADY_EXISTS"):
                ex.run(root)


if __name__=="__main__":
    unittest.main()
