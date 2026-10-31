#!/usr/bin/env python3
"""CAF-05 tests: no fake stock mapping, frozen old sensor, genuine new DES."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import caf05_contrato_y_sensor as exp
from experiments.cafeteria.pc01 import caf01_des_engine as des


class Caf05Test(unittest.TestCase):
    def test_source_known_sensor_and_three_new_75h_configurations(self):
        ref=exp.known_reference()
        chosen=exp.select_from_previous_only(ref)
        self.assertEqual(chosen["measurement"],{
            "field":"stage_stock","stage":"despacho","stage_index":1,
            "minute":10,"arrival_rate_per_minute":"3/2",
            "unit":"orders (waiting + in_service)",
        })
        self.assertEqual(chosen["classifier"]["prototypes"],
                         {"preparacion":1,"despacho":6,"entrega":2})
        self.assertEqual(chosen["prior_CAF04_training_signatures"],
                         {"B":1,"C":6,"D":2})
        self.assertEqual(exp.predict_one(1,chosen)["prediction"],"preparacion")
        self.assertEqual(exp.predict_one(6,chosen)["prediction"],"despacho")
        self.assertEqual(exp.predict_one(2,chosen)["prediction"],"entrega")
        # Stock=4 ties dispatcher prototype 6 and delivery prototype 2.
        self.assertEqual(exp.predict_one(4,chosen)["status"],
                         "ABSTAIN_TIED_PROTOTYPES")
        self.assertIsNone(exp.predict_one(4,chosen)["prediction"])
        worlds=exp.all_worlds()
        self.assertEqual([r["name"] for r in worlds],["I","J","K"])
        for ix,r in enumerate(worlds):
            stages=des.validate_private_config(r["config"])
            self.assertEqual([n for n,_ in stages],[1 if i==ix else 2
                                                    for i in range(3)])
            self.assertEqual(stages[ix][1],des.Fraction(4,5))
            self.assertEqual(r["nominal_capacity_h"],75)

    def test_contract_denies_fake_mapping_for_M_and_D(self):
        contract=exp.observation_contract()
        self.assertTrue(contract[
            "no_automatic_DES_stage_M_D_stock_correspondence"])
        for arm,families in (("M",exp.M_FAMILIES),("D",exp.D_FAMILIES)):
            for family in families:
                self.assertEqual(exp.require_scoring_support(
                    contract,arm,family,"delivered")["status"],
                    exp.STATUS_SUPPORTED)
                self.assertEqual(contract["by_arm_family"][arm][family][
                    "pending_total"]["status"],exp.STATUS_DERIVED)
                for stage in exp.STAGES:
                    for field in ("waiting","in_service","stage_stock"):
                        with self.assertRaisesRegex(ValueError,
                                                    "NO_VALID_MODEL_OBSERVATION_OPERATOR"):
                            exp.require_scoring_support(contract,arm,family,
                                                        field,stage)
                        status=contract["by_arm_family"][arm][family][
                            f"{field}:{stage}"]["status"]
                        if (arm=="M" and field=="stage_stock" and
                            stage in ("preparacion","despacho")):
                            self.assertEqual(status,exp.STATUS_CONDITIONAL)
                        else:
                            self.assertEqual(status,exp.STATUS_UNSUPPORTED)

    def test_real_six_DES_runs_after_fsync_plan_and_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"caf05"
            original=des.run_toy_engine
            calls=[]
            policy=exp.d.POLICY.read_bytes()
            ref=exp.REF_PATH.read_bytes()
            def instrument(config,arrivals,times):
                plan=path/"00_SENSOR_Y_MUNDOS_PREDECLARADOS.json"
                contract=path/"01_CONTRATO_OBSERVABILIDAD.json"
                checkpoint=path/"01B_CHECKPOINT_ANTES_DE_DES.json"
                self.assertTrue(all(p.exists() for p in
                                    (plan,contract,checkpoint)))
                self.assertFalse((path/"02_RESULTADOS.json").exists())
                p=json.loads(plan.read_bytes())
                cp=json.loads(checkpoint.read_bytes())
                self.assertEqual(p["worlds_run_before_plan"],0)
                self.assertFalse(p["new_world_outcomes_seen"])
                self.assertEqual(cp["DES_runs_so_far"],0)
                self.assertEqual(cp["source_plan_sha256"],
                                 exp.lab.sha(plan.read_bytes()))
                self.assertEqual(cp["contract_sha256"],
                                 exp.lab.sha(contract.read_bytes()))
                self.assertEqual(p["sensor_selector"]["measurement"][
                    "stage"],"despacho")
                self.assertEqual(p["sensor_selector"]["classifier"][
                    "prototypes"],{"preparacion":1,"despacho":6,"entrega":2})
                self.assertEqual(p["CAF02_original_policy_sha256"],
                                 exp.lab.sha(policy))
                self.assertEqual(times,(0,10,40))
                self.assertIn(len(arrivals),(16,30))
                calls.append((config,len(arrivals)))
                return original(config,arrivals,times)
            with patch.object(des,"run_toy_engine",side_effect=instrument):
                report=exp.run(path)
            self.assertEqual(len(calls),6)
            self.assertEqual([c[1] for c in calls],[30,16]*3)
            self.assertEqual(report["DES_runs"],6)
            self.assertEqual(report["DES_confirmatory_runs"],0)
            self.assertFalse(report["external_custody"])
            self.assertTrue(report[
                "contract_cannot_score_M_D_with_DES_stage_stocks"])
            self.assertTrue(report["new_worlds_not_random_or_blinded"])
            self.assertEqual(exp.d.POLICY.read_bytes(),policy)
            self.assertEqual(exp.REF_PATH.read_bytes(),ref)
            self.assertEqual(len(report["observations"]),6)
            for row in report["observations"]:
                self.assertEqual(sum(row[
                    "all_stage_stock_in_evaluator_diagnostics_only"]),
                    row["pending_total"])
                self.assertEqual(row["delivered"]+row["pending_total"],
                                 row["accepted"])
                self.assertEqual(row["selected_sensor_reading"],
                    row["all_stage_stock_in_evaluator_diagnostics_only"][1])
                if row["rate_name"]=="LOW_OOD":
                    self.assertEqual(row["classification"]["status"],
                                     "OUT_OF_DOMAIN_PRESSURE_NO_CLASSIFICATION")
                    self.assertIsNone(row["classification"]["prediction"])
            self.assertFalse(report["summary"]["low_out_of_domain"][
                "classifier_run"])
            self.assertEqual(
                len((path/"03_OBSERVACIONES.csv").read_text().splitlines()),7)
            self.assertIn("Contrat", (path/"04_INFORME.md").read_text())
            manifest=json.loads((path/"05_MANIFIESTO.json").read_bytes())
            self.assertTrue(manifest["sensor_chosen_before_first_new_DES"])
            self.assertTrue(manifest[
                "model_observation_contract_chosen_before_first_new_DES"])
            for name,sha in manifest["files_sha256"].items():
                self.assertEqual(exp.lab.sha((path/name).read_bytes()),sha)
            with self.assertRaisesRegex(ValueError,"CAF05_OUTPUT_ALREADY_EXISTS"):
                exp.run(path)


if __name__=="__main__":
    unittest.main()
