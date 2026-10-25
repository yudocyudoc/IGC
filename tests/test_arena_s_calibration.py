"""Construction-only parameter fitting for the bounded structural pilot."""
import copy
import json
from pathlib import Path
import unittest

from scripts.arena_round import hash_obj
from scripts.arena_s_calibration import calibrate,verify_calibration
from scripts.arena_sp_producers import ProviderError
from scripts.compose_molecular_candidates import compose
from scripts.fm_b5_parameter_identifiability import sample_times,simulate

ROOT=Path(__file__).resolve().parents[1]
read=lambda name:json.loads((ROOT/name).read_text(encoding="utf-8"))


class CalibrationTests(unittest.TestCase):
    def setUp(self):
        self.plan=read("data/synthetic/fm_b3_dynamic_plan.json")
        self.plan["candidates"]=self.plan["candidates"][:2]
        self.catalog=read("data/synthetic/fm_a_structural_candidates.json")
        self.composed=compose(self.plan,self.catalog)
        self.fit=read("data/synthetic/arena_s_pilot_fit_config.json")
        self.fit["parameter_ranges"]["maxThroughput"]={
            "minimum":1.6,"maximum":1.8,"step":0.2}
        self.fit["parameter_ranges"]["responseTime"]={
            "minimum":0.8,"maximum":1.0,"step":0.2}
        cal=self.fit["calibration"]
        self.primary={
            "investigation_id":"CALIBRATION-SYNTHETIC",
            "observable_id":"delivered","unit":"units",
            "times":sample_times(cal["stop_time"],cal["observation_interval"]),
            "values":simulate(2,1.8,0.8,cal["input_amplitude"],
                cal["input_duration"],cal["stop_time"],
                cal["observation_interval"],
                self.fit["numerics"]["integration_step"]),
            "sources":["construction-only-test-fixture"],
            "input_profile":{"kind":"pulse","amplitude":cal["input_amplitude"],
                             "duration":cal["input_duration"],
                             "initial_stocks_zero":True}}
            
    def test_two_independent_parameter_fits_and_pulse(self):
        result,plan,receipt=calibrate(
            self.composed,self.plan,self.fit,self.primary)
        self.assertEqual(len(receipt["fits"]),2)
        self.assertFalse(receipt["holdout_accessed"])
        self.assertEqual(receipt["construction_hash"],hash_obj(self.primary))
        self.assertEqual(plan["external_input"]["profile"]["kind"],"pulse")
        self.assertEqual(plan["simulation"]["stop_time"],16)
        self.assertEqual(plan["simulation"]["intervals"],32)
        self.assertNotEqual(hash_obj(result),hash_obj(self.composed))
        verify_calibration(receipt,self.composed,result,self.plan,plan,
                           self.fit,self.primary)

    def test_fit_plan_rejects_hidden_generator_truth(self):
        self.fit["synthetic_data_generation"]["truth_structure"]="CS-02"
        with self.assertRaisesRegex(ProviderError,"FIT_PLAN_MUST_EXCLUDE_GENERATOR_TRUTH"):
            calibrate(self.composed,self.plan,self.fit,self.primary)

    def test_neutral_atms_supports_keep_both_structures(self):
        from scripts.fm_b2_atms_candidate_reasoning import apply_supports
        supports=read("data/synthetic/arena_s_pilot_supports.json")
        selection=apply_supports(self.composed,supports)
        self.assertEqual(
            {item["candidate_id"] for item in selection["selected"]},
            {"urn:igc:candidate:CS-01","urn:igc:candidate:CS-02"})
        self.assertEqual(selection["rejected"],[])

    def test_out_of_catalog_physical_impossibility_fails_absolute_gate(self):
        self.primary["values"]=[0,10,20,30,40]
        calibrated,plan,report=calibrate(self.composed,self.plan,
                                         self.fit,self.primary)
        self.assertEqual(report["absolute_adequacy_status"],
                         "NO_ADEQUATE_STRUCTURE")
        self.assertTrue(all(fit["absolute_adequacy"]=="INADEQUATE"
                            for fit in report["fits"].values()))
        self.assertFalse(any(fit["physical_input_bound_passed"]
                             for fit in report["fits"].values()))

    def test_construction_compatible_grid_produces_uncertainty_envelope(self):
        calibrated,plan,report=calibrate(self.composed,self.plan,
                                         self.fit,self.primary)
        for fit in report["fits"].values():
            envelope=fit["prediction_envelope_rk4"]
            self.assertEqual(len(envelope),33)
            self.assertEqual(envelope[0]["time"],0)
            self.assertEqual(envelope[-1]["time"],16)
            self.assertTrue(all(p["minimum"]<=p["maximum"] for p in envelope))
        self.assertEqual(report["uncertainty_status"],
                         "SUPPORTED_GRID_ENVELOPES_RK4_PARITY_PENDING")

    def test_wrong_construction_grid_is_rejected(self):
        self.primary["times"][-1] += 0.25
        with self.assertRaisesRegex(ProviderError,"CALIBRATION_TIME_GRID_MISMATCH"):
            calibrate(self.composed,self.plan,self.fit,self.primary)

    def test_calibration_rejects_retrospective_rewrite(self):
        result,plan,receipt=calibrate(self.composed,self.plan,self.fit,self.primary)
        corrupted=copy.deepcopy(self.primary)
        corrupted["values"][2] += 1.0
        with self.assertRaisesRegex(ProviderError,"CALIBRATION_REPLAY_MISMATCH"):
            verify_calibration(receipt,self.composed,result,self.plan,plan,
                               self.fit,corrupted)


if __name__=="__main__":
    unittest.main()
