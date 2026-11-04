"""F4 analytic downstream permutation with original EV01 O0 and O1.

No catalog search. The exact recurrence tests the algebraic invariance;
the unchanged CAF-01 DES separately verifies it with the actual EV01 pulse.
The private evaluator configuration never enters a native D/B/M worker.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction as Q
import json
import os
from pathlib import Path
import unittest

from scripts.arena_cafe import f4_latent_downstream_symmetry as symmetry
from scripts.arena_cafe import ev01
from scripts.arena_physical import des_engine as des
from scripts.arena_v0_contract import ArenaContractError


class ExactCommutation(unittest.TestCase):
    def test_00_swapping_two_single_server_stations_commutes(self):
        # Three distinct arrival patterns are not a parameter grid or
        # replacement for the proof of the max-plus identity.
        streams=(
            (Q(0),Q(1),Q(2),Q(3)),
            (Q(0),Q(1,10),Q(3,2),Q(151,100)),
            (Q(0),Q(0),Q(0),Q(2)),
        )
        for arrivals in streams:
            for a,b in ((Q(2,3),Q(7,5)),):
                _,mid_ab=symmetry.one_server_departures(arrivals,a)
                _,end_ab=symmetry.one_server_departures(mid_ab,b)
                _,mid_ba=symmetry.one_server_departures(arrivals,b)
                _,end_ba=symmetry.one_server_departures(mid_ba,a)
                self.assertEqual(end_ab,end_ba)

    def test_01_false_claim_when_one_intermediate_stage_has_two_servers(self):
        config_a,config_b=symmetry.private_pair()
        a=des.validate_private_config(config_a)
        b=des.validate_private_config(config_b)
        self.assertEqual(a[:2],b[:2])
        self.assertEqual((1,1),(a[2][0],a[3][0]))
        self.assertEqual(a[2][1],b[3][1])
        self.assertEqual(a[3][1],b[2][1])
        self.assertNotEqual(a[2][1],a[3][1])

    def test_02_same_intervention_absolute_service_addition_stage2_only(self):
        a,b=symmetry.private_pair()
        for config in (a,b):
            perturbed=symmetry.stressed(config)
            original=des.validate_private_config(config)
            changed=des.validate_private_config(perturbed)
            self.assertEqual(original[:2],changed[:2])
            self.assertEqual(original[3],changed[3])
            self.assertEqual(original[2][0],changed[2][0])
            self.assertEqual(original[2][1]+Q(1,2),changed[2][1])
            self.assertEqual(des.TIE_POLICY,perturbed["tie_policy"])

    def test_03_changing_order_does_not_change_analytic_terminal_timestamps(self):
        arrivals=des.half_open_arrivals("5/2",6)
        a,b=symmetry.private_pair()
        for config in (a,b):
            spec=des.validate_private_config(config)
            caja=symmetry.n_server_fixed_departures(
                arrivals,spec[0][0],spec[0][1])
            _,prep=symmetry.one_server_departures(caja,spec[1][1])
            _,third=symmetry.one_server_departures(prep,spec[2][1])
            _,terminal=symmetry.one_server_departures(third,spec[3][1])
            self.assertEqual(15,len(terminal))
            self.assertEqual(15,sum(x<Q(20) for x in terminal))


@unittest.skipUnless(all(os.environ.get(k) for k in
                     ("F4SYM_O0","F4SYM_O1")),
                     "Requires original separately frozen public O0 and O1")
class SameActualO0AndO1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.o0=json.loads(Path(os.environ["F4SYM_O0"]).read_text())
        cls.o1=json.loads(Path(os.environ["F4SYM_O1"]).read_text())
        cls.report=symmetry.build(cls.o0,cls.o1)

    def test_10_matches_all_real_synthetic_O0_checkpoints_exactly(self):
        r=self.report
        self.assertEqual([0,0,2,4,6,8],
                         r["both_baselines_delivered_cumulative_at_O0_times"])
        self.assertTrue(r["original_O0_and_O1_compatible_for_BOTH_mechanisms"])
        self.assertTrue(r["proof"][
            "all_15_exact_terminal_delivery_times_identical"])
        self.assertEqual(15,r["proof"]["total_terminal_events_verified"])
        self.assertTrue(r["swap_proven_for_all_arrival_schedules_under_declared_assumptions"])

    def test_11_matches_original_O1_preparation_complete_count_wait_mean(self):
        o1=self.report["original_O1_preparation_aggregate"]
        self.assertEqual(9,o1["n_completed_stage_services"])
        self.assertEqual("15/17",o1["mean_service_minutes_exact"])
        self.assertEqual("1204/765",o1["mean_wait_minutes_exact"])
        self.assertTrue(self.report["proof"][
            "all_preparation_start_finish_times_identical"])

    def test_12_counterfactual_a_stresses_dispatch_more_than_b(self):
        r=self.report
        self.assertEqual({
            "REFERENCE_EV01_WORLD_A":6,"SWAPPED_DOWNSTREAM_WORLD_B":8
        },r["counterfactual_delivered_at_t10"])
        self.assertEqual(2,r["absolute_counterfactual_gap_orders_t10"])
        self.assertEqual("1/2",
                         r["intervention"]["added_service_minutes_exact"])
        self.assertTrue(r["intervention"][
            "same_absolute_change_from_t0_both_worlds"])
        self.assertTrue(r["intervention"][
            "not_a_business_improvement_proposal"])
        self.assertEqual("NOT_ASSESSED",
                         r["intervention"]["operational_feasibility_and_cost"])

    def test_13_not_a_double_bottleneck_under_baseline(self):
        r=self.report
        self.assertEqual("PREPARACION",
                         r["same_active_baseline_bottleneck_in_both"])
        self.assertTrue(r["ambiguous_latent_downstream_constraint"])
        self.assertTrue(r["stage_paths_same_in_both_no_process_route_variation"])
        self.assertEqual("NOT_DEMONSTRATED",
                         r["PM_incremental_over_B1_B2"])

    def test_14_no_private_evaluator_trace_or_truth_as_arm_input(self):
        r=self.report
        self.assertTrue(r["internal_stage_wip_is_evaluator_only"])
        self.assertTrue(r["proof"]["timestamp_sequences_evaluator_only_not_exported"])
        self.assertEqual("NOT_RUN",r["D_B_M_native_inference_on_this_design"])
        self.assertEqual("NOT_CREATED",r["F5_independent_reserve"])
        self.assertEqual("PARTIAL",r["A3"])
        self.assertEqual("NOT_RUN",r["G4"])
        self.assertEqual("NOT_RUN",r["G5"])
        self.assertTrue(r["no_parameter_grid_or_fitter_or_new_DES_engine"])
        self.assertTrue(r["no_live_provider_no_PM4Py_no_OMC"])
        self.assertTrue(r["not_an_independent_test"])
        self.assertNotIn("reference_private_configuration",r)
        self.assertNotIn("per_case_service_start_timestamps",r)

    def test_15_modified_O1_preparation_aggregate_rejected(self):
        false=deepcopy(self.o1)
        false["construction"]["physical_observation"][
            "mean_service_minutes_exact"]="1"
        with self.assertRaises((ValueError,ArenaContractError)):
            symmetry.build(self.o0,false)

    def test_16_forged_public_o0_delivery_sequence_rejected(self):
        false=deepcopy(self.o0)
        false["construction"]["observation_series"][3][
            "delivered_cumulative"]=5
        with self.assertRaises((ValueError,ArenaContractError)):
            symmetry.build(false,self.o1)

    def test_17_relabelled_other_world_rejected(self):
        false=deepcopy(self.o1)
        false["observability"]["world_public_id"]="another-world"
        with self.assertRaises((ValueError,ArenaContractError)):
            symmetry.build(self.o0,false)


if __name__=="__main__":
    unittest.main()
