"""F4 one-dispatch-count witness on original two known worlds.

No blind inference claim. Tests are about discrimination in a finite,
post-hoc disclosed pair using original DES/EV01 telemetry, not a sensor
validated for a real cafeteria or a new O2 arm condition.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction as Q
import json
import os
from pathlib import Path
import unittest

from scripts.arena_cafe import ev01
from scripts.arena_cafe import f4_b2_processing_intervention as apm
from scripts.arena_cafe import f4_latent_downstream_symmetry as symmetry
from scripts.arena_cafe import f4_single_dispatch_count_observability as o2
from scripts.arena_v0_contract import ArenaContractError


class AggregateCounterContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cfg=ev01.config()
        cls.intervals=apm.analytic_intervals(cfg,ev01.ARRIVALS)
        apm.verify_des_snapshots(cfg,ev01.ARRIVALS,cls.intervals)
        apm.verify_original_full(cls.intervals)
        cls.rows=apm.physical_event_rows(cls.intervals)
        cls.cases={f"O{i:03d}" for i in range(15)}

    def test_00_dispatch_count_on_existing_half_open_grid(self):
        times=o2.completed_service_times(
            self.rows,"despacho",self.cases)
        self.assertEqual((0,0,2,4,6,9),o2.counts_before(times))
        self.assertEqual("1131/3655",
                         str(o2.closest_event_margin(times)))
        self.assertEqual(4,sum(t<Q(6) for t in times))

    def test_01_completion_exactly_at_six_excluded_until_next_grid(self):
        self.assertEqual((0,0,0,0,1,1),
                         o2.counts_before((Q(6),),o2.GRID))
        self.assertEqual((0,0,0,1,1,1),
                         o2.counts_before((Q(6)-Q(1,100),),o2.GRID))
        with self.assertRaisesRegex(ArenaContractError,
                                    "F4O2_COUNT_ON_CUTOFF_UNSTABLE"):
            o2.closest_event_margin((Q(6),))
        with self.assertRaisesRegex(ArenaContractError,
                                    "F4O2_INVALID_COUNT_GRID"):
            o2.counts_before((Q(1),),(Q(0),Q(2),Q(2)))

    def test_02_pair_consistency_does_not_select_unknown_world(self):
        candidate={
            o2.KEYS[0]:4,o2.KEYS[1]:5
        }
        self.assertEqual([o2.KEYS[0]],
             o2.two_candidate_decision(4,candidate)[
                "compatible_declared_world_keys"])
        self.assertEqual([o2.KEYS[1]],
             o2.two_candidate_decision(5,candidate)[
                "compatible_declared_world_keys"])
        missed=o2.two_candidate_decision(3,candidate)
        self.assertEqual("NEITHER_OF_TWO_DECLARED_WORLDS_COMPATIBLE",
                         missed["status"])
        self.assertFalse(missed["other_unmodeled_worlds_excluded"])
        ambiguous=o2.two_candidate_decision(9,{
            o2.KEYS[0]:9,o2.KEYS[1]:9})
        self.assertEqual(2,ambiguous[
            "number_of_compatible_declared_worlds"])
        self.assertEqual("AMBIGUOUS_WITHIN_DECLARED_TWO_WORLD_PAIR",
                         ambiguous["status"])
        with self.assertRaisesRegex(ArenaContractError,
                                    "F4O2_BAD_OBSERVED_INTEGER_COUNT"):
            o2.two_candidate_decision(4.0,candidate)

    def test_03_missing_service_finish_must_fail(self):
        fake=[x for x in deepcopy(self.rows)
              if not (x["case_id"]=="O000" and
                      x["stage"]=="despacho" and
                      x["event_type"]=="servicio_fin")]
        with self.assertRaisesRegex(ArenaContractError,
                                    "F4O2_STAGE_INTERVAL_INCOMPLETE"):
            o2.completed_service_times(fake,"despacho",self.cases)

    def test_04_duplicate_service_finish_must_fail(self):
        fake=deepcopy(self.rows)
        finish=next(r for r in fake
                    if r["stage"]=="despacho" and
                    r["event_type"]=="servicio_fin")
        fake.append(deepcopy(finish))
        with self.assertRaisesRegex(ArenaContractError,
                                    "F4O2_DUPLICATE_STAGE_EVENT"):
            o2.completed_service_times(fake,"despacho",self.cases)

    def test_05_wrong_station_provenance_does_not_become_dispatch(self):
        fake=deepcopy(self.rows)
        for r in fake:
            if r["stage"]=="despacho" and r["event_type"]=="servicio_fin":
                r["source"]="untrusted"
                break
        with self.assertRaisesRegex(ArenaContractError,
                                    "F4O2_UNAUTHORIZED_STAGE_EVENT"):
            o2.completed_service_times(fake,"despacho",self.cases)

    def test_06_resource_switch_in_same_service_rejected(self):
        fake=deepcopy(self.rows)
        for r in fake:
            if r["stage"]=="despacho" and
               r["event_type"]=="servicio_fin":
                r["resource_id"]="despacho-r2"
                break
        with self.assertRaisesRegex(ArenaContractError,
                                    "F4O2_RESOURCE_CHANGED_DURING_SERVICE"):
            o2.completed_service_times(fake,"despacho",self.cases)

    def test_07_reversed_start_and_finish_rejected(self):
        fake=deepcopy(self.rows)
        case="O000"
        first=next(r for r in fake if
                   r["case_id"]==case and r["stage"]=="despacho" and
                   r["event_type"]=="servicio_inicio")
        final=next(r for r in fake if
                   r["case_id"]==case and r["stage"]=="despacho" and
                   r["event_type"]=="servicio_fin")
        first["t_minutes_exact"]=str(
            Q(final["t_minutes_exact"])+Q(1))
        with self.assertRaisesRegex(ArenaContractError,
                                    "F4O2_NONPHYSICAL_SERVICE_INTERVAL"):
            o2.completed_service_times(fake,"despacho",self.cases)

    def test_08_wrong_case_or_stage_inventory_rejected(self):
        false_cases={"O000"}|{f"O{i:03d}" for i in range(14)}
        with self.assertRaisesRegex(ArenaContractError,
                                    "F4O2_MISSING_PHYSICAL_EVALUATOR_EVENTS"):
            o2.completed_service_times(
                self.rows,"despacho",false_cases)
        with self.assertRaisesRegex(ArenaContractError,
                                    "F4O2_UNKNOWN_STAGE"):
            o2.completed_service_times(
                self.rows,"billing",self.cases)

    def test_09_untrusted_extra_private_fields_not_accepted(self):
        fake=deepcopy(self.rows)
        for r in fake:
            if r["stage"]=="despacho":
                r["truth"]="extra_private_parameter"
                break
        with self.assertRaisesRegex(ArenaContractError,
                                    "F4O2_UNAUTHORIZED_STAGE_EVENT"):
            o2.completed_service_times(fake,"despacho",self.cases)


@unittest.skipUnless(all(os.environ.get(k) for k in (
                     "F4SYM_O0","F4SYM_O1")),
                     "Requires original O0/O1 development envelopes")
class OriginalKnownPairOnly(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.o0=json.loads(Path(os.environ["F4SYM_O0"]).read_text())
        cls.o1=json.loads(Path(os.environ["F4SYM_O1"]).read_text())
        cls.report=o2.build(cls.o0,cls.o1)

    def test_10_t6_4_versus_5_is_one_new_aggregate_scalar(self):
        r=self.report
        a,b=o2.KEYS
        self.assertEqual({a:4,b:5},
                         r["dispatch_count_at_t6_by_world"])
        self.assertEqual("6",r["measurement_window"][3:4])
        self.assertEqual(1,r["count_of_additional_aggregated_scalars"])
        self.assertEqual("NEW_DISPATCH_FINISH_COUNTER_NOT_IN_O0_OR_O1",
                         r["candidate_source"])
        self.assertEqual(["6","8"],
                         r["informative_grid_cutoffs_in_this_known_pair"])
        self.assertTrue(r["posthoc_stage_and_cutoff_selection_after_worlds_known"])
        self.assertFalse(r["O2_authorized_as_arm_input"])

    def test_11_t10_dispatch_count_and_all_terminal_counts_not_informative(self):
        r=self.report
        a,b=o2.KEYS
        self.assertEqual({a:9,b:9},
                         r["dispatch_count_at_t10_by_world"])
        self.assertEqual([0,0,2,4,6,8],
                         r["negative_control_terminal_counts_by_grid"][a])
        self.assertEqual(
            r["negative_control_terminal_counts_by_grid"][a],
            r["negative_control_terminal_counts_by_grid"][b])
        self.assertTrue(r["negative_control_preparation_counts_identical"])
        self.assertEqual(2,r["t10_two_world_rule_for_count_9"][
            "number_of_compatible_declared_worlds"])

    def test_12_posthoc_margin_is_not_evidence_of_sensor_accuracy(self):
        r=self.report
        self.assertEqual("108/935",r[
            "posthoc_smallest_distance_to_t6_of_any_dispatch_completion_exact"])
        self.assertTrue(r[
            "timing_margin_is_oracle_RETROSPECTIVE_not_sensor_calibration"])
        self.assertTrue(r["not_installed_or_independently_validated_sensor"])
        self.assertTrue(r[
            "no_missing_duplicated_or_misattributed_events_assumed"])
        self.assertFalse(r["O2_experiment_actually_performed"])

    def test_13_existing_action_stays_separate_from_baseline_measurement(self):
        r=self.report
        self.assertTrue(r[
            "t6_baseline_measurement_is_from_a_separate_run_before_any_stress"])
        self.assertTrue(r[
            "counterfactual_stress_would_reset_initial_state_at_t0"])
        self.assertTrue(r["no_post_t6_events_used_to_compute_observed_t6_count"])
        self.assertFalse(r["O2_authorized_as_arm_input"])
        self.assertTrue(r["no_private_event_data_sent_to_D_B_M"])

    def test_14_rejects_cross_condition_tampering(self):
        altered=deepcopy(self.o1)
        altered["observability"]["condition_id"]="O0"
        with self.assertRaisesRegex(ArenaContractError,"A1_CROSS_CONDITION"):
            o2.build(self.o0,altered)

    def test_15_never_claims_G5_or_general_optimal_observability(self):
        r=self.report
        self.assertEqual("PARTIAL",r["A3"])
        self.assertEqual("NOT_RUN",r["G4"])
        self.assertEqual("NOT_RUN",r["G5"])
        self.assertEqual("NOT_CREATED",r["F5_independent_reserve"])
        self.assertFalse(r["not_minimum_across_all_possible_sensors_or_worlds"] is False)
        self.assertEqual(0,r["provider_calls"])
        serialized=json.dumps(r,ensure_ascii=False)
        self.assertNotIn("case_id",serialized)
        self.assertNotIn("resource_id",serialized)
        self.assertNotIn("t_minutes_exact",serialized)
        self.assertNotIn("service_minutes",serialized)


if __name__=="__main__":
    unittest.main()
