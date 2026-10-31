#!/usr/bin/env python3
"""Guardrails for the first full EXPLORATORY public DES world.

No external witness. Tests are software exploration, not independent trials.
"""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import caf02_lab_exploratorio as lab
import caf02_public_cut_bridge as bridge
from experiments.cafeteria.pc01 import caf01_des_engine as des


class LabTest(unittest.TestCase):
    def test_public_world_is_fixed_and_not_inferred_from_K2(self):
        world=lab.public_world()
        self.assertEqual(world["world_parameters"],lab.WORLD)
        self.assertTrue(world["world_parameters_are_public_not_secret"])
        self.assertFalse(world["formal_CAF02_trial_authorized_or_executed"])
        self.assertFalse(world["external_G5_witness"])
        self.assertEqual(
            [(x["servers"],x["service_minutes"])
             for x in world["world_parameters"]["stages"]],
            [(2,"3/2"),(1,"3/4"),(2,"3/2")])

    def test_one_complete_public_world_all_forecasts_precede_K2(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"one"
            observed_engine_rates=[]
            original=des.run_toy_engine

            def observer(config,arrivals,observations):
                observed_engine_rates.append(len(arrivals))
                if len(arrivals)==27:
                    self.assertTrue((out/"05B_CHECKPOINT_PRE_K2.json").is_file())
                    self.assertTrue((out/lab.FORECAST_FILE).is_file())
                    self.assertTrue((out/"02_G4a_PRE_K1.json").is_file())
                    self.assertTrue((out/"04_G4b_PRE_K2.json").is_file())
                    self.assertFalse((out/"06_K2_OBSERVADO.json").exists())
                    chk=json.loads((out/"05B_CHECKPOINT_PRE_K2.json").read_text())
                    self.assertEqual(chk["DES_K2_runs_so_far"],0)
                    self.assertFalse(chk["K2_truth_seen"])
                    forecast=json.loads((out/lab.FORECAST_FILE).read_text())
                    self.assertEqual(forecast["world_ref"],
                                     lab.public_world()["world_precommitment_ref"])
                    self.assertFalse(forecast["K2_truth_read"])
                    self.assertNotIn('"K2":{"delivered":',lab.canonical(forecast).decode())
                return original(config,arrivals,observations)

            with patch.object(des,"run_toy_engine",side_effect=observer):
                result=lab.run_lab(out)
            self.assertEqual(result["exploratory_DES_runs"],
                             len(observed_engine_rates))
            self.assertIn(24,observed_engine_rates)  # one K0
            self.assertEqual(observed_engine_rates[-1],27)  # K2 last
            self.assertEqual(observed_engine_rates.count(27),1)
            self.assertEqual(result["confirmatory_DES_runs"],0)
            self.assertEqual(result["status"],"EXPLORATORY_RESULTS_NOT_CONFIRMATORY")
            self.assertEqual(set(result["scores"]),set([
                "status","schema","world_precommitment_ref",
                "parent_G4a_candidate_sha256","parent_G4b_candidate_sha256",
                "scored_times_minutes","same_six_observations_for_both_arms",
                "M","D","K1_was_used",
                "K2_truth_was_synthetic_or_externally_released_NOT_ATTESTED_HERE",
                "G5_G4a_G4b_external_receipts_verified_here",
                "native_G2_verified_here","ATMS_persisted_here",
                "baseline_updated_with_K1",
                "equal_information_reference_superiority_not_claimed",
                "lab_exploratory_not_independent_custody","source_DES_lab_runs"]))
            manifest=json.loads((out/"11_MANIFIESTO.json").read_text())
            self.assertFalse(manifest["external_custody_verified"])
            self.assertFalse(manifest["ATMS_persisted"])
            self.assertTrue(manifest["K2_priors_written_before_K2"])
            self.assertTrue(manifest[
                "avoid_using_this_world_as_blind_confirmatory_sample"])
            self.assertEqual(manifest["G2_native_calls_in_this_run"],0)
            self.assertEqual(len(list(out.glob("*.json"))),10)
            self.assertTrue((out/"10_INFORME.md").is_file())
            self.assertTrue((out/"09_TABLA_K2.csv").is_file())
            for name,digest in manifest["files_sha256"].items():
                self.assertEqual(lab.sha((out/name).read_bytes()),digest)

    def test_stop_before_k2_hook_proves_one_way_checkpoint_order(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"abort"
            calls=[]
            original=des.run_toy_engine
            def observer(config,arrivals,observations):
                calls.append(len(arrivals))
                return original(config,arrivals,observations)
            def stop(folder,checkpoint):
                self.assertTrue((folder/lab.FORECAST_FILE).is_file())
                self.assertTrue((folder/"05B_CHECKPOINT_PRE_K2.json").is_file())
                self.assertEqual(checkpoint["DES_K2_runs_so_far"],0)
                raise RuntimeError("INTENTIONAL_TEST_ABORT_BEFORE_FIRST_K2")
            with patch.object(des,"run_toy_engine",side_effect=observer):
                with self.assertRaisesRegex(RuntimeError,"BEFORE_FIRST_K2"):
                    lab.run_lab(out,after_checkpoint_hook=stop)
            self.assertNotIn(27,calls)
            self.assertFalse((out/"06_K2_OBSERVADO.json").exists())
            self.assertFalse((out/"11_MANIFIESTO.json").exists())
            with self.assertRaisesRegex(lab.LabBlocked,"OUTPUT_ALREADY_EXISTS"):
                lab.run_lab(out)  # no overwrites or silent retries

    def test_result_csv_rows_and_prediction_semantics(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"sample"
            result=lab.run_lab(out)
            csv_text=(out/"09_TABLA_K2.csv").read_text()
            self.assertEqual(len(csv_text.splitlines()),7)
            self.assertIn("DES_K2_integer",csv_text)
            self.assertEqual(len(result["K2"]["delivered"]),6)
            self.assertEqual(result["scores"]["M"]["arm"],"M")
            self.assertEqual(result["scores"]["D"]["arm"],"D")
            for arm in ("M","D"):
                value=result["scores"][arm]
                self.assertEqual(value["status"] in ("PAIRED",
                    "NOT_PAIRED_ABSTENTION"),True)
                self.assertTrue(value["do_not_count_abstention_as_zero_error"])
                if value["status"]=="NOT_PAIRED_ABSTENTION":
                    self.assertIsNone(value["paired_set_loss_gain_orders"])
                    self.assertIsNone(value["revision_predictive_improvement_pass"])
            report=(out/"10_INFORME.md").read_text()
            self.assertIn("no ensayo confirmatorio",report)
            self.assertIn("K2 observado DES",report)
            self.assertIn("Hipótesis y pronósticos",report)
            self.assertNotIn("ATMS persistido: sí",report)


if __name__=="__main__":
    unittest.main()
