"""F3 E1 bridge: no equality of a jump counter and bounded fluid integral."""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction as Q
import unittest

from scripts.arena_cafe import (
    ev01,evidence,native_pos_scenario,
    m_o1_capacity_certificate as cap,
    m_o1_bridge_semantics as bridge)
from scripts import arena_event_observability as obs
from scripts.arena_v0_contract import ArenaContractError


class BridgeSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        events,_=ev01.trace_generator()
        cls.views=evidence.build(
            obs.project_events(events,"POS"),
            obs.project_events(events,"FULL"))["views"]
        cls.o1=cls.views["O1"]
        _,_,manifest=native_pos_scenario.build(cls.o1,"M","O1")
        cls.cert=cap.certificate(cls.o1,manifest["candidate"])
        cls.numeric=cls.cert["bound_under_unverified_bridge"]

    def test_00_bounded_fluid_integral_is_continuous_but_count_jumps(self):
        a=bridge.audit(self.o1,self.numeric)
        self.assertEqual("MATHEMATICALLY_IMPOSSIBLE_WITH_POSITIVE_EVENTS",
                         a["pointwise_event_vs_continuous_integral_identity"])
        # Over any interval of length 1/100 minute, a flow of 20/h
        # can accumulate at most 1/300 mass, whereas a single observed
        # discrete completion causes a unit jump in the event counter.
        self.assertEqual(Q(1,300),Q(20,60)*Q(1,100))
        self.assertTrue(Q(20,60)*Q(1,100)<1)
        self.assertEqual("NOT_VALIDATED",a["bridge_readiness"])

    def test_01_one_to_one_unit_identity_does_not_prove_cutoff_mass_identity(self):
        a=bridge.audit(self.o1,self.numeric)
        self.assertEqual(
            "UNVERIFIED_ONE_PHYSICAL_PREP_COMPLETION_IS_ONE_READYORDER_UNIT",
            a["unit_identity_requirement"])
        self.assertEqual(
            "UNVERIFIED_EXACT_COUNT_EQUALS_INTEGRAL_AT_SAME_CUTOFF",
            a["exact_cutoff_mass_equality_requirement"])
        self.assertFalse(a["unit_identity_empirically_verified"])
        self.assertFalse(a["exact_cutoff_mass_equality_empirically_verified"])
        self.assertEqual("NOT_IDENTIFIED_BY_AGGREGATED_O1",
                         a["unconditional_scientific_model_verdict"])

    def test_02_missing_event_clock_and_error_budget_stays_missing(self):
        a=bridge.audit(self.o1,self.numeric)
        self.assertEqual("9",str(a["original_positive_event_count"]))
        self.assertTrue(a["no_case_level_preparation_completion_timestamps_in_O1"])
        self.assertTrue(a["no_per_completion_readyorder_measurement_links_in_O1"])
        self.assertTrue(a["strict_before_cutoff_requires_declared_boundary_policy"])
        self.assertFalse(a["independent_error_budget_available"])
        self.assertEqual("17/3",
            a["necessary_absolute_discrepancy_to_avoid_exclusion_under_1_to_1_exact"])
        self.assertEqual("NOT_RUN",a["sensor_calibration_or_discretization_fit"])
        self.assertEqual("NOT_ESTABLISHED",a["G3"])

    def test_03_modified_count_cannot_be_paired_with_old_native_bound(self):
        b=deepcopy(self.numeric)
        b["observed_discrete_services_completed_pre_cutoff"]=8
        with self.assertRaisesRegex(ArenaContractError,
                                    "F3M_BRIDGE_BOUND_NOT_BOUND_TO_O1"):
            bridge.audit(self.o1,b)

    def test_04_modified_capacity_or_max_integral_is_rejected(self):
        for change in ({"max_throughput_units_per_hour_exact":"54"},
                       {"maximum_possible_cumulative_completed_mass_exact":"9"},
                       {"shortfall_of_nominal_max_mass_to_count_exact":"0"},
                       {"necessary_one_to_one_condition_satisfied":True}):
            with self.subTest(change=change),self.assertRaisesRegex(
                    ArenaContractError,"F3M_BRIDGE_BOUND_NOT_BOUND_TO_O1"):
                bridge.audit(self.o1,{**self.numeric,**change})

    def test_05_no_O0_sibling_as_O1(self):
        with self.assertRaisesRegex(ArenaContractError,"A1_CROSS_CONDITION"):
            bridge.audit(self.views["O0"],self.numeric)

    def test_06_bound_is_not_selecting_or_fitting_E1(self):
        a=bridge.audit(self.o1,self.numeric)
        self.assertFalse(a["native_e1_model_generated_or_fitted_from_O1"])
        self.assertEqual("PARTIAL",a["F3"])
        self.assertEqual("NOT_RUN",a["G4"])
        self.assertEqual("NOT_RUN",a["G5"])
        self.assertGreaterEqual(len(a["required_additional_evidence"]),5)


if __name__=="__main__":
    unittest.main()
