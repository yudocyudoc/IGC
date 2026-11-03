"""RF-02H: read-only operator H_j, prior provenance and G3 blocker tests."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import csv
import unittest

from scripts.arena_cafe import r2_hj_parameter_gate as h
from scripts.arena_v0_contract import ArenaContractError


class HJReadiness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        paths=(os.environ.get("RF02_PUBLIC_DIR"),
               os.environ.get("RF02_D_G2_DIR"),
               os.environ.get("RF02_M_G2_DIR"))
        if not all(paths):
            raise unittest.SkipTest("Requires frozen O0 view plus prior D and M G2 CSV artifacts")
        cls.visible=json.loads((Path(paths[0])/"O0_VISIBLE.json").read_text())
        cls.d_root,cls.m_root=map(Path,paths[1:])
        cls.d_manifest=json.loads((cls.d_root/"manifest.json").read_text())
        cls.m_manifest=json.loads((cls.m_root/"manifest.json").read_text())
        cls.report=h.build(cls.visible,cls.d_root,cls.m_root)

    def test_00_provenance_real_six_plus_six_read_only(self):
        r=self.report
        self.assertEqual("O0",r["condition_id"])
        self.assertEqual(12,r["candidate_count"])
        self.assertEqual(6,sum(x["arm_id"]=="D" for x in r["candidates"]))
        self.assertEqual(6,sum(x["arm_id"]=="M" for x in r["candidates"]))
        self.assertEqual(12,len({(x["arm_id"],x["candidate_id"])
                                 for x in r["candidates"]}))
        self.assertTrue(r["G2_source_audits_recomputed"])
        self.assertTrue(all(x["G3"]=="NOT_RUN" for x in r["candidates"]))
        self.assertEqual({h.A1_ORIGIN_RUN,h.D_ORIGIN_RUN,h.M_ORIGIN_RUN},
                         set(r["artifact_sources"].values()))
        self.assertEqual("1/2",r["rate_kernel_width_minutes_exact"])
        self.assertEqual(15,r["source_events_count"])
        self.assertEqual("NOT_RUN",r["gates"]["G3"])
        self.assertEqual("PARTIAL",r["gates"]["A3"])

    def test_01_d_and_m_native_delivery_units_operator_shape(self):
        r=self.report
        for x in r["candidates"]:
            self.assertEqual("PASS",x["H_j"]["engineering_operator"])
            self.assertEqual("orders",x["H_j"]["quantity_unit"])
            self.assertEqual("minute",x["H_j"]["common_time_unit"])
            self.assertEqual("10",x["H_j"]["window_minutes"]["end"])
            self.assertEqual("0",x["H_j"]["window_minutes"]["start"])
            self.assertGreaterEqual(x["H_j"]["sample_rows"],1000)
            self.assertTrue(x["H_j"]["monotonic_nonnegative"])
            self.assertTrue(x["H_j"]["initial_value_zero"])
            self.assertFalse(x["H_j"]["trajectory_values_exported"])
            self.assertEqual("NOT_RUN",x["H_j"]["scoring_against_observations"])
            self.assertEqual("NOT_ESTABLISHED",
                             x["H_j"]["scientific_measurement_equivalence"])
            self.assertEqual("sha256:",x["H_j"]["trace_sha256"][:7])
            if x["arm_id"]=="D":
                self.assertEqual("delivered",x["H_j"]["native_output_variable"])
                self.assertEqual("minute",x["H_j"]["native_time_unit"])
                self.assertEqual("IDENTITY",x["H_j"]["temporal_conversion"])
            else:
                self.assertEqual("deliveredTotal",x["H_j"]["native_output_variable"])
                self.assertEqual("hour",x["H_j"]["native_time_unit"])
                self.assertEqual("HOURS_TO_MINUTES_EXACT_FACTOR_60",
                                 x["H_j"]["temporal_conversion"])

    def test_02_parameter_policy_denies_G3_on_both_arms(self):
        p=self.report["parameters"]
        self.assertEqual("ENGINEERING_FIXTURE_NOT_EV01_ESTIMATE",
                         p["D"]["values_source_status"])
        self.assertTrue(p["D"]["origin_verified"])
        self.assertFalse(p["D"]["admissible_as_empirical_parameters"])
        self.assertFalse(p["D"]["eligible_for_G3"])
        self.assertEqual("NOT_RUN",p["D"]["observational_parameter_fit"])
        self.assertTrue(p["M"]["origin_verified"])
        self.assertFalse(p["M"]["admissible_as_empirical_parameters"])
        self.assertFalse(p["M"]["eligible_for_G3"])
        self.assertFalse(p["B"]["eligible_for_G3"])
        self.assertTrue(p["no_data_driven_calibration_from_O0_or_O1_this_run"])
        self.assertTrue(p["comparison_with_unequal_priors_is_not_method_comparison"])
        self.assertTrue(self.report["no_native_model_selection"])
        self.assertTrue(self.report["no_fit_to_observed_deliveries"])
        self.assertEqual("BLOCKED_G3_NEEDS_SCIENTIFIC_ADMISSION",
                         self.report["decision"])

    def test_03_hj_and_specific_noncomparable_observables(self):
        o=self.report["observables"]
        self.assertEqual("PASS_D_M_DIRECT_NATIVE_STOCKS",
                         o["delivery_cumulative"]["operator_shape"])
        self.assertFalse(o["delivery_cumulative"]["G3_ADMISSIBLE"])
        self.assertFalse(o["modeling_input"]["input_rate_is_measured"])
        self.assertFalse(o["modeling_input"]["rate_kernel_scientifically_approved"])
        self.assertFalse(o["modeling_input"]["input_created_counts_scored_as_prediction"])
        self.assertTrue(o["modeling_input"]["source_integral_is_identical_for_D_M"])
        self.assertEqual("INPUT_NOT_SCOREABLE",
                         o["O0_other"]["orders_created_cumulative"])
        self.assertEqual("NOT_NATIVE_WIP_WITH_LOSSES_OR_DEFERRED_INPUT",
                         o["O0_other"]["orders_minus_delivered"])
        self.assertEqual("NOT_TESTED_IN_O0_NOT_CROSS_ARM_EQUIVALENT",
                         o["O1_only"]["completed_preparation_services"])
        self.assertEqual("NOT_NATIVE_RESPONSE_TIME_PARAMETER",
                         o["O1_only"]["wait_service_intervals"])

    def test_04_tampered_g2_manifest_parameter_fields_are_rejected(self):
        for mutation in ("d_fixture_sha","d_false_empirical","m_registry","m_false_prior"):
            d=deepcopy(self.d_manifest)
            m=deepcopy(self.m_manifest)
            if mutation=="d_fixture_sha":
                d["nominal_fixture_sha256"]="sha256:"+"0"*64
            elif mutation=="d_false_empirical":
                d["nominal_parameters_are_non_empirical"]=False
            elif mutation=="m_registry":
                m["registry_sha256"]="sha256:"+"0"*64
            else:
                m["original_E1_parameters_fixed_not_fit_to_POS"]=False
            with self.subTest(mutation=mutation),self.assertRaises(ArenaContractError):
                h._parameter_policy(d,m)

    def test_05_csv_nonmonotonic_and_wrong_native_output_rejected(self):
        for arm in ("D","M"):
            with self.subTest(arm=arm),TemporaryDirectory() as temp:
                path=Path(temp)/"forged.csv"
                native="delivered" if arm=="D" else "deliveredTotal"
                with path.open("w",newline="") as fd:
                    w=csv.writer(fd)
                    w.writerow(["time",native])
                    for i in range(1101):
                        value=1.0 if i<=500 else 0.8
                        t=i*10/1100 if arm=="D" else i/1100/6
                        w.writerow([t,value])
                with self.assertRaises(ArenaContractError):
                    h._extract_delivered(path,arm,10.0)
                with path.open("w",newline="") as fd:
                    w=csv.writer(fd)
                    w.writerow(["time","untrusted_output"])
                    for i in range(1101):
                        t=i*10/1100 if arm=="D" else i/1100/6
                        w.writerow([t,0.0])
                with self.assertRaises(ArenaContractError):
                    h._extract_delivered(path,arm,10.0)

    def test_06_wrong_condition_or_sibling_O1_not_admitted_as_O0(self):
        wrong=deepcopy(self.visible)
        wrong["observability"]["condition_id"]="O1"
        with self.assertRaises(ArenaContractError):
            h.build(wrong,self.d_root,self.m_root)

    def test_07_no_silent_G3_switch_from_hj_evidence(self):
        r=self.report
        self.assertEqual("NOT_RUN",r["gates"]["G3"])
        self.assertFalse(r["gates"]["D_parameters_scientifically_admissible"])
        self.assertFalse(r["gates"]["M_parameters_calibrated_for_EV01"])
        self.assertFalse(r["gates"]["B_real_native_EV01_generated"])
        self.assertEqual("NOT_ESTABLISHED",
                         r["gates"]["Hj_scientific_semantic_equivalence"])
        self.assertEqual(5,len(r["blockers"]))
        self.assertEqual(0,r["cloudflare_provider_calls"])
        self.assertEqual(0,r["omc_invocations_in_this_job"])
        self.assertTrue(r["no_private_truth_access"])


if __name__=="__main__":
    unittest.main()
