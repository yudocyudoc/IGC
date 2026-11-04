"""F3/Short E1: O1 conditional necessary bound, not event-flow equivalence."""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_cafe import (
    ev01,evidence,native_pos_scenario, m_o1_capacity_certificate as cert)
from scripts import arena_event_observability as obs
from scripts.arena_v0_contract import ArenaContractError,digest
from scripts.arena_m_short_e1 import get_composer


class OriginalShortE1CapacityCertificate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw,snapshots=ev01.trace_generator()
        ev01.verify_des_parity(snapshots)
        cls.views=evidence.build(
            obs.project_events(raw,"POS"),
            obs.project_events(raw,"FULL"))["views"]
        cls.o1=cls.views["O1"]
        _,_,cls.m_manifest=native_pos_scenario.build(cls.o1,"M","O1")
        cls.report=cert.certificate(cls.o1,cls.m_manifest["candidate"])

    def test_00_frozen_20_per_hour_is_insufficient_for_nine_services_in_ten_minutes(self):
        r=self.report
        self.assertEqual("O1",r["condition_id"])
        self.assertEqual("M",r["arm_id"])
        self.assertEqual("9",str(
            r["bound_under_unverified_bridge"][
                "observed_discrete_services_completed_pre_cutoff"]))
        self.assertEqual("20",
            r["bound_under_unverified_bridge"]["max_throughput_units_per_hour_exact"])
        self.assertEqual("10/3",
            r["bound_under_unverified_bridge"][
                "maximum_possible_cumulative_completed_mass_exact"])
        self.assertEqual("54",
            r["bound_under_unverified_bridge"][
                "necessary_average_rate_to_equal_count_units_per_hour_exact"])
        self.assertEqual("17/3",
            r["bound_under_unverified_bridge"][
                "shortfall_of_nominal_max_mass_to_count_exact"])
        self.assertFalse(r["bound_under_unverified_bridge"][
            "necessary_one_to_one_condition_satisfied"])
        self.assertEqual(
            "EXCLUDED_ONLY_IF_EXACT_CUTOFF_COUNTER_EQUALS_MODEL_MASS",
            r["conditional_fixed_nominal_candidate_status"])

    def test_01_all_original_composed_graphs_have_same_prep_capacity_without_fitting(self):
        r=self.report
        composer=get_composer()
        cfg,classes,_=composer.load_registry(cert.REGISTRY)
        self.assertEqual(len(composer.enumerate_graphs(cfg,classes)),
                         r["fixed_original_E1_graphs_checked"])
        self.assertGreater(r["fixed_original_E1_graphs_checked"],1)
        self.assertTrue(r["all_original_fixed_graphs_same_preparation_cap"])
        self.assertTrue(r["enumerated_graphs_are_existing_typed_candidates_not_parameter_grid"])
        self.assertEqual(digest(self.m_manifest["candidate"]["ast"]),
                         r["original_candidate_full_ast_sha256"])

    def test_02_not_claiming_measured_sensor_error_or_native_assimilation(self):
        r=self.report
        self.assertFalse(r["bridge_empirically_verified"])
        self.assertEqual(
            "UNVERIFIED_ONE_DISCRETE_COMPLETION_EQUALS_ONE_E1_READYORDER_UNIT",
            r["bridge_assumption"])
        self.assertFalse(r["native_model_generation_uses_O1"])
        self.assertTrue(r["O1_used_for_fixed_candidate_compatibility_audit"])
        self.assertFalse(r["candidate_selected_or_fitted_using_O1"])
        self.assertEqual("NOT_ESTABLISHED",
                         r["inference_about_other_E1_parameters_or_structures"])
        self.assertEqual("NOT_CLAIMED",r["statistical_falsification"])
        self.assertFalse(r["real_sensor_error_known"])
        self.assertEqual("NOT_ESTABLISHED",r["method_level_scientific_G3"])
        self.assertTrue(r["physical_mean_service_not_converted_to_responseTime"])
        self.assertTrue(r["physical_mean_wait_not_converted_to_stock_waiting"])
        self.assertTrue(r["no_truth_FULL_or_private_DES"])
        self.assertEqual(0,r["provider_calls"])
        self.assertEqual("PARTIAL",r["A3"])
        self.assertEqual("NOT_RUN",r["G4"])
        self.assertEqual("NOT_RUN",r["G5"])

    def test_02b_requires_two_distinct_bridges_not_just_one_to_one_units(self):
        a=self.report["semantic_bridge_audit"]
        self.assertFalse(a["unit_identity_empirically_verified"])
        self.assertFalse(a["exact_cutoff_mass_equality_empirically_verified"])
        self.assertFalse(a["independent_error_budget_available"])
        self.assertTrue(self.report[
            "unit_identity_and_cutoff_equality_are_two_DISTINCT_unverified_assumptions"])
        self.assertEqual("NOT_IDENTIFIED_BY_AGGREGATED_O1",
                         a["unconditional_scientific_model_verdict"])
        self.assertEqual("NOT_VALIDATED",a["bridge_readiness"])
        self.assertEqual("MATHEMATICALLY_IMPOSSIBLE_WITH_POSITIVE_EVENTS",
                         a["pointwise_event_vs_continuous_integral_identity"])
        self.assertTrue(a["pointwise_impossibility_is_not_cutoff_mismatch_proof"])
        self.assertEqual("17/3",
                         a["necessary_shortfall_IF_EXACT_CUTOFF_BRIDGE_exact"])
        self.assertTrue(a["necessary_discrepancy_is_not_empirical_sensor_error"])
        self.assertFalse(a["native_e1_model_generated_or_fitted_from_O1"])
        self.assertTrue(a["no_case_level_preparation_completion_timestamps_in_O1"])

    def test_03_o0_cannot_run_o1_certificate(self):
        with self.assertRaisesRegex(ArenaContractError,"A1_CROSS_CONDITION"):
            cert.certificate(self.views["O0"],self.m_manifest["candidate"])

    def test_04_changed_frozen_M_preparation_parameter_is_rejected(self):
        bad=deepcopy(self.m_manifest["candidate"])
        for instance in bad["ast"]["instances"]:
            if instance["role"]=="preparation":
                instance["parameters"]["maxThroughput"]=54
        with self.assertRaisesRegex(ArenaContractError,
                                    "F3M_O1_CANDIDATE_NOT_AUTHENTIC_OR_PARAMETERS_CHANGED"):
            cert.certificate(self.o1,bad)

    def test_05_changed_E1_graph_digest_is_rejected(self):
        bad=deepcopy(self.m_manifest["candidate"])
        bad["full_ast_sha256"]="sha256:"+"0"*64
        with self.assertRaisesRegex(ArenaContractError,
                                    "F3M_O1_CANDIDATE_NOT_AUTHENTIC_OR_PARAMETERS_CHANGED"):
            cert.certificate(self.o1,bad)

    def test_06_changed_O1_observable_is_not_an_authorized_input(self):
        changed=deepcopy(self.o1)
        changed["construction"]["physical_observation"][
            "n_completed_stage_services"]=6
        with self.assertRaisesRegex(ArenaContractError,
                                    "A1_SOURCE_DIGEST_MISMATCH"):
            cert.certificate(changed,self.m_manifest["candidate"])

    def test_07_changing_registry_path_is_forbidden(self):
        with TemporaryDirectory() as temp:
            new=Path(temp)/"registry.base.json"
            new.write_text(cert.REGISTRY.read_text(encoding="utf-8"))
            with self.assertRaisesRegex(ArenaContractError,
                                        "F3M_O1_REGISTRY_NOT_F0_APPROVED"):
                cert.certificate(self.o1,self.m_manifest["candidate"],new)

    def test_08_necessary_inequality_is_not_discrete_event_observation_model(self):
        self.assertEqual("10/3",
            cert.bound(9,20,10)[
                "maximum_possible_cumulative_completed_mass_exact"])
        self.assertFalse(cert.bound(9,20,10)[
            "necessary_one_to_one_condition_satisfied"])
        self.assertTrue(cert.bound(9,54,10)[
            "necessary_one_to_one_condition_satisfied"])
        # The inequality is only necessary: passing it never proves
        # an actual native trajectory, causal mechanism or event semantics.
        self.assertTrue(cert.bound(0,20,10)[
            "necessary_one_to_one_condition_satisfied"])

    def test_09_reject_malformed_count_or_capacity(self):
        for args in ((-1,20,10),(9,-1,10),(9,20,-10),
                     (9,"NaN",10),(9,0,10),(9,20,121)):
            with self.subTest(args=args),self.assertRaises(
                    (ValueError,ArenaContractError)):
                cert.bound(*args)

    def test_10_manifest_input_linked_before_running_cli(self):
        self.assertEqual(digest(self.o1),self.m_manifest["input_hash"])
        self.assertEqual(
            self.o1["source_snapshot_hash"],
            self.m_manifest["source_snapshot_hash"])
        with TemporaryDirectory() as temp:
            root=Path(temp)
            original=root/"o1.json"; original.write_text(json.dumps(self.o1))
            manifest=root/"manifest.json"
            manifest.write_text(json.dumps(self.m_manifest))
            out=root/"cert.json"
            # Test CLI-equivalent persistence without running subprocess
            first=cert.certificate(self.o1,self.m_manifest["candidate"])
            out.write_bytes(cert.canonical(first)+b"\n")
            self.assertEqual(first,json.loads(out.read_text()))
            self.assertEqual(cert.SCHEMA,first["schema"])


if __name__=="__main__":
    unittest.main()
