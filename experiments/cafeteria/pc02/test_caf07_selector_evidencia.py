#!/usr/bin/env python3
"""CAF-07 regression: decisions without fabricated posterior or DES leakage."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import caf07_selector_evidencia as experiment
from experiments.cafeteria.pc01 import caf01_des_engine as des


class EvidenceSelectorTest(unittest.TestCase):
    def test_fixed_bank_worlds_action_cost_and_observation_operator(self):
        bank=experiment.hypotheses()
        self.assertEqual(len(bank),12)
        self.assertEqual({h["capacity_h"] for h in bank},{60,75,90,105})
        self.assertEqual({h["bottleneck"] for h in bank},
                         set(experiment.STAGES))
        worlds=experiment.worlds()
        self.assertEqual([w["capacity_h"] for w in worlds],[72,88,102])
        self.assertEqual([w["actual_bottleneck"] for w in worlds],
                         list(experiment.STAGES))
        for row in bank+worlds:
            c=row["config"]
            arr=des.validate_private_config(c)
            self.assertEqual(len(arr),3)
            self.assertEqual(sum(x[0]==1 for x in arr),1)
        self.assertEqual(len(experiment.ACTION_MENU),9)
        self.assertEqual(experiment.BUDGET_COST_UNITS,8)
        self.assertGreater(experiment.ACTION_MENU[-1]["cost"],
                           experiment.BUDGET_COST_UNITS)

    def test_abstention_cost_stop_and_model_gap_are_distinct(self):
        b=experiment.hypotheses()
        # We need the selector to run solely on prediction arrays, not DES.
        fake={h["id"]:{"baseline":[7],
                       **{a["id"]:[1]*len(a["channels"])
                          for a in experiment.ACTION_MENU}}
              for h in b}
        all_ids=[h["id"] for h in b]
        self.assertEqual(experiment.select_action(
            b,fake,[])["status"],experiment.MODEL_GAP)
        stage_only=[h["id"] for h in b
                    if h["bottleneck"]=="despacho"]
        self.assertEqual(experiment.select_action(
            b,fake,stage_only)["status"],
            "STOP_DECISION_ALREADY_RESOLVED")
        self.assertEqual(experiment.select_action(
            b,fake,all_ids)["status"],experiment.NO_MEASURE)
        self.assertEqual(experiment.select_action(
            b,fake,all_ids,budget=0)["status"],experiment.NO_MEASURE)
        self.assertEqual(experiment.adjudicate(
            b,fake,all_ids,"baseline",[999])["status"],
            experiment.MODEL_GAP)
        self.assertIsNone(experiment.adjudicate(
            b,fake,all_ids,"baseline",[7])["diagnosis"])
        self.assertEqual(experiment.adjudicate(
            b,fake,stage_only,"baseline",[7])["status"],
            experiment.DECIDED)
        with self.assertRaisesRegex(ValueError,
                                    "CAF07_UNKNOWN_SENSOR_ACTION"):
            experiment.select_action(b,fake,all_ids,
                                     allowed_action_ids={"unknown"})

    def test_robust_pair_separation_uses_tolerance_and_decision_labels(self):
        bank=experiment.hypotheses()
        two=[h["id"] for h in bank
             if h["capacity_h"]==60 and
             h["bottleneck"] in ("preparacion","despacho")]
        self.assertEqual(len(two),2)
        action="delivered_15_t20"
        fake={a["id"]:{action:[0]} for a in bank}
        self.assertEqual(experiment.pair_separation(
            bank,fake,sorted(two),action),(1,0))
        fake[two[0]][action]=[3]
        self.assertEqual(experiment.pair_separation(
            bank,fake,sorted(two),action),(1,1))
        same=[h["id"] for h in bank
              if h["bottleneck"]=="preparacion"][:2]
        self.assertEqual(experiment.pair_separation(
            bank,fake,sorted(same),action),(0,0))

    def test_actual_world_probes_only_after_hypothesis_precommit(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/"caf07"
            original=des.run_toy_engine
            worlds=experiment.worlds()
            source_configs=[w["config"] for w in worlds]
            train_calls=[]
            world_calls=[]
            old_policy=experiment.caf05.d.POLICY.read_bytes()

            def checked(config,arrivals,times):
                if config in source_configs:
                    plan=root/"00_PLAN_Y_CANDIDATOS_ANTES_DE_EVALUAR.json"
                    checkpoint=root/"00B_CHECKPOINT_PRE_DES.json"
                    self.assertTrue(plan.is_file())
                    self.assertTrue(checkpoint.is_file())
                    self.assertFalse((root/"01_RESULTADOS.json").exists())
                    p=json.loads(plan.read_bytes())
                    c=json.loads(checkpoint.read_bytes())
                    self.assertEqual(p["new_world_DES_runs_before_plan"],0)
                    self.assertFalse(p["external_custody"])
                    self.assertEqual(p["tolerance_orders"],1)
                    self.assertEqual(p["budget_illustrative_units"],8)
                    self.assertEqual(c["plan_sha256"],
                                     experiment.lab.sha(plan.read_bytes()))
                    self.assertEqual(len(p["hypotheses"]),12)
                    self.assertEqual(len(p["candidate_observation_predictions"]),
                                     12)
                    idx=source_configs.index(config)
                    name=worlds[idx]["id"]
                    if len(arrivals)==24:  # baseline, 1.2/min
                        self.assertFalse((root/f"01_PRE_PROBE_{name}.json").exists())
                        self.assertEqual(times,(0,10,20,40))
                    else:  # selected 1.5/min or 1.8/min
                        file=root/f"01_PRE_PROBE_{name}.json"
                        self.assertTrue(file.is_file())
                        prior=json.loads(file.read_bytes())
                        self.assertFalse(prior["future_followup_observation_seen"])
                        self.assertEqual(prior["followup_DES_calls_so_far"],0)
                        self.assertTrue(prior["selector_decision"]["action"])
                        self.assertEqual(
                            len(arrivals),
                            30 if prior["selector_decision"]["action"]["rate"]
                            =="3/2" else 36)
                    world_calls.append((name,len(arrivals)))
                else:
                    self.assertFalse((root/"00_PLAN_Y_CANDIDATOS_ANTES_DE_EVALUAR.json").exists())
                    train_calls.append(config)
                return original(config,arrivals,times)

            with patch.object(des,"run_toy_engine",side_effect=checked):
                report=experiment.run(root)
            self.assertEqual(len(train_calls),12*10)
            self.assertGreaterEqual(len(world_calls),3)
            self.assertLessEqual(len(world_calls),6)
            self.assertEqual(report["hypothesis_DES_runs"],120)
            self.assertEqual(report["DES_runs"],len(world_calls))
            self.assertEqual(report["new_worlds"],3)
            self.assertEqual(report["confirmatory_DES_runs"],0)
            self.assertTrue(report["measurement_costs_are_illustrative"])
            self.assertFalse(report["probability_or_expected_VOI_estimated"])
            self.assertTrue(report["M_D_stage_observation_models_untouched"])
            self.assertTrue(report["evaluator_truth_not_used_in_selection"])
            self.assertEqual(experiment.caf05.d.POLICY.read_bytes(),
                             old_policy)
            self.assertEqual(len(report["evaluations"]),3)
            self.assertEqual(len((root/"02_COMPARACION.csv").read_text().splitlines()),4)
            summary=report["summary"]
            self.assertEqual(summary["correct"]+summary["wrong"]+
                             summary["abstain"],3)
            for world in report["evaluations"]:
                file=root/f"01_PRE_PROBE_{world['world']}.json"
                self.assertTrue(file.exists())
                before=json.loads(file.read_bytes())
                self.assertEqual(before["baseline_delivered_t10"],
                                 world["baseline_delivery"])
                self.assertEqual(before["selector_decision"],
                                 world["selection"])
                self.assertEqual(before["pre_probe_candidate_ids"],
                                 experiment.surviving(
                                     experiment.hypotheses(),
                                     json.loads((root/"00_PLAN_Y_CANDIDATOS_ANTES_DE_EVALUAR.json").read_bytes())[
                                         "candidate_observation_predictions"],
                                     {"baseline":world["baseline_delivery"]}))
                if world["observed_followup"] is None:
                    self.assertIsNone(world["selection"]["action"])
                else:
                    self.assertIsNotNone(world["selection"]["action"])
                if world["updated"]["diagnosis"] is None:
                    self.assertEqual(world["judgement_EVALUATOR_ONLY"],
                                     "ABSTAIN")
            manifest=json.loads((root/"04_MANIFIESTO.json").read_bytes())
            for name,digest in manifest["files_sha256"].items():
                self.assertEqual(experiment.lab.sha((root/name).read_bytes()),
                                 digest)
            with self.assertRaisesRegex(ValueError,
                                        "CAF07_OUTPUT_ALREADY_EXISTS"):
                experiment.run(root)

    def test_no_recovery_after_first_world_simulation_error(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/"caf07-abort"
            original=des.run_toy_engine
            calls=[]
            def mock(*args,**kwargs):
                if (root/"00_PLAN_Y_CANDIDATOS_ANTES_DE_EVALUAR.json").exists():
                    calls.append("first_world")
                    raise RuntimeError("INTENTIONAL_ABORT_BEFORE_WORLD_DATA")
                return original(*args,**kwargs)
            with patch.object(des,"run_toy_engine",side_effect=mock):
                with self.assertRaisesRegex(RuntimeError,"INTENTIONAL_ABORT"):
                    experiment.run(root)
            self.assertEqual(calls,["first_world"])
            self.assertTrue((root/"00_PLAN_Y_CANDIDATOS_ANTES_DE_EVALUAR.json").exists())
            self.assertFalse((root/"01_RESULTADOS.json").exists())


if __name__=="__main__":
    unittest.main()
