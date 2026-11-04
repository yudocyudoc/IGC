"""F4 B2 PROCESSING-only APM proxy versus existing stress sensitivity.

These known synthetic worlds and the EV01/FULL source have already been used
in development. The tests never constitute blind prediction or D/B/M inference.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction as Q
import json
import os
from pathlib import Path
import unittest

from scripts.arena_cafe import ev01,evidence
from scripts.arena_cafe import f4_b2_processing_intervention as apm
from scripts.arena_cafe import f4_latent_downstream_symmetry as f4
from scripts.arena_physical import des_engine as des
from scripts import arena_event_observability as obs
from scripts.arena_v0_contract import ArenaContractError


class ProcessingPeriods(unittest.TestCase):
    def test_00_contiguous_processing_fragments_are_one_active_period(self):
        # B2 may split one uninterrupted server episode across boundaries
        # from OTHER resources. Such segmentation must not break APM.
        values=[
            (0,5,"PROCESSING"),(5,10,"PROCESSING"),
            (10,20,"UNKNOWN"),(20,30,"PROCESSING")]
        result={
            "status":"B2_EXACT_RESOURCE_PERIODS_PASS",
            "availability_source":"NO_AVAILABILITY_TELEMETRY",
            "horizon_minutes_exact":"30",
            "segments":[{
                "start_minutes_exact":str(a),"end_minutes_exact":str(b),
                "by_stage":{"preparacion":{
                    "resource_states":{"preparacion-r1":state}}}}
                for a,b,state in values],
            "resource_total_minutes":{
                "preparacion-r1":{"PROCESSING":"20","UNKNOWN":"10"}},
        }
        rank=apm.per_resource_processing_periods(
            result,{"preparacion":["preparacion-r1"]})
        self.assertEqual("preparacion",rank["winner_under_processing_only_proxy"])
        r=rank["stages"]["preparacion"]
        self.assertEqual("10",r["longest_resource_processing_minutes_exact"])
        self.assertEqual("20",r["total_resource_processing_minutes_exact"])
        self.assertEqual(2,r["processing_episode_count"])
        self.assertTrue(rank["idle_and_available_are_not_inferred_from_silence"])
        self.assertTrue(rank["not_full_active_period_method"])

    def test_01_invalid_busy_state_cannot_be_called_available_idle(self):
        value={
            "status":"B2_EXACT_RESOURCE_PERIODS_PASS",
            "availability_source":"NO_AVAILABILITY_TELEMETRY",
            "horizon_minutes_exact":"30",
            "segments":[{
                "start_minutes_exact":"0","end_minutes_exact":"30",
                "by_stage":{"preparacion":{
                    "resource_states":{"preparacion-r1":"IDLE_AVAILABLE"}}}}],
            "resource_total_minutes":{"preparacion-r1":{"PROCESSING":"0"}},
        }
        with self.assertRaisesRegex(ArenaContractError,
                                     "F4APM_B2_INVENTED_AVAILABILITY_STATE"):
            apm.per_resource_processing_periods(
                value,{"preparacion":["preparacion-r1"]})

    def test_02_bad_b2_provenance_rejected(self):
        value={
            "status":"B2_EXACT_RESOURCE_PERIODS_PASS",
            "availability_source":"DECLARED_SYNTHETIC_24_7_OR_WINDOWS",
            "horizon_minutes_exact":"30",
            "segments":[],
            "resource_total_minutes":{},
        }
        with self.assertRaisesRegex(ArenaContractError,
                                     "F4APM_B2_WITHOUT_PERMITTED_PROCESSING_PROVENANCE"):
            apm.per_resource_processing_periods(
                value,{"preparacion":["preparacion-r1"]})

    def test_03_false_per_server_processing_total_rejected(self):
        value={
            "status":"B2_EXACT_RESOURCE_PERIODS_PASS",
            "availability_source":"NO_AVAILABILITY_TELEMETRY",
            "horizon_minutes_exact":"30",
            "segments":[{
                "start_minutes_exact":"0","end_minutes_exact":"30",
                "by_stage":{"preparacion":{
                    "resource_states":{"preparacion-r1":"PROCESSING"}}}}],
            "resource_total_minutes":{"preparacion-r1":{"PROCESSING":"20"}},
        }
        with self.assertRaisesRegex(ArenaContractError,
                                     "F4APM_B2_RESOURCE_TOTAL_MISMATCH"):
            apm.per_resource_processing_periods(
                value,{"preparacion":["preparacion-r1"]})

    def test_04_two_servers_have_independent_periods_not_60min_virtual_one(self):
        value={
            "status":"B2_EXACT_RESOURCE_PERIODS_PASS",
            "availability_source":"NO_AVAILABILITY_TELEMETRY",
            "horizon_minutes_exact":"30",
            "segments":[{
                "start_minutes_exact":"0","end_minutes_exact":"30",
                "by_stage":{"caja":{"resource_states":{
                    "caja-r1":"PROCESSING","caja-r2":"PROCESSING"}}}}],
            "resource_total_minutes":{
                "caja-r1":{"PROCESSING":"30"},
                "caja-r2":{"PROCESSING":"30"}},
        }
        rank=apm.per_resource_processing_periods(
            value,{"caja":["caja-r1","caja-r2"]})
        r=rank["stages"]["caja"]
        self.assertEqual("30",r["longest_resource_processing_minutes_exact"])
        self.assertEqual("60",r["total_resource_processing_minutes_exact"])
        self.assertTrue(
            r["multiple_servers_not_merged_into_a_fictitious_single_machine"])

    def test_05_FCFS_analytic_schedule_is_original_EV01_FULL(self):
        cfg=ev01.config()
        schedule=apm.analytic_intervals(cfg,ev01.ARRIVALS)
        self.assertTrue(apm.verify_original_full(schedule))
        snapshots=apm.verify_des_snapshots(cfg,ev01.ARRIVALS,schedule)
        self.assertEqual(len(apm.CHECKPOINTS),len(snapshots))
        self.assertEqual(8,next(s.delivered_cum_orders for s in snapshots
                                if s.t_min==Q(10)))
        physical=apm.physical_event_rows(schedule)
        self.assertEqual(180,len(physical))
        self.assertEqual(15,sum(
            r["stage"]=="preparacion" and r["event_type"]=="servicio_fin"
            for r in physical))

    def test_06_counterfeit_schedule_fails_DES_snapshot_parity(self):
        cfg=ev01.config()
        schedule=apm.analytic_intervals(cfg,ev01.ARRIVALS)
        broken=deepcopy(schedule)
        broken["preparacion"][0]["finish"]=Q(5)
        with self.assertRaisesRegex(ArenaContractError,
                                    "F4APM_ANALYTIC_SERVICE_STATE_NOT_ORIGINAL_DES"):
            apm.verify_des_snapshots(cfg,ev01.ARRIVALS,broken)


@unittest.skipUnless(all(os.environ.get(k) for k in ("F4SYM_O0","F4SYM_O1")),
                     "Needs the original A1 public O0/O1 pair (not evaluator FULL)")
class ActualPairedWorlds(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.o0=json.loads(Path(os.environ["F4SYM_O0"]).read_text())
        cls.o1=json.loads(Path(os.environ["F4SYM_O1"]).read_text())
        cls.report=apm.build(cls.o0,cls.o1)

    def test_10_baseline_both_are_prep_longest_processing_not_two_active_causals(self):
        r=self.report
        self.assertEqual({
            f4.BASELINE_KEYS[0]:"preparacion",
            f4.BASELINE_KEYS[1]:"preparacion",
        },r["baseline_processing_winners"])
        self.assertEqual(8,r["baseline_deliveries_t10"][f4.BASELINE_KEYS[0]])
        self.assertEqual(8,r["baseline_deliveries_t10"][f4.BASELINE_KEYS[1]])
        self.assertTrue(r["all_15_baseline_terminal_timestamps_identical"])
        self.assertTrue(r["same_O0_O1_public_evidence_for_both_known_worlds"])

    def test_11_same_stress_breaks_capacity_order_in_a_only(self):
        r=self.report
        self.assertEqual({
            f4.BASELINE_KEYS[0]:"despacho",
            f4.BASELINE_KEYS[1]:"preparacion",
        },r["stressed_processing_winners"])
        self.assertEqual({
            f4.BASELINE_KEYS[0]:6,f4.BASELINE_KEYS[1]:8,
        },r["stressed_deliveries_t10"])
        self.assertEqual({
            f4.BASELINE_KEYS[0]:-2,f4.BASELINE_KEYS[1]:0,
        },r["difference_stress_minus_baseline"])
        self.assertEqual(f4.ACTION,r["reference_action"])
        self.assertEqual("1/2",r["same_action_only_dispatch_plus_minutes_exact"])
        self.assertEqual("NOT_ASSESSED",r[
            "action_operational_feasibility_and_cost"])

    def test_12_APM_proxy_is_not_full_machine_status_or_causal_truth(self):
        r=self.report
        for key in f4.BASELINE_KEYS:
            for series in ("baseline_processing_proxy",
                           "after_common_stress_processing_proxy"):
                info=r[series][key]
                self.assertTrue(info["not_full_active_period_method"])
                self.assertTrue(info["not_causal_bottleneck_truth"])
                self.assertEqual(
                    "LONGEST_UNINTERRUPTED_OBSERVED_PROCESSING_PER_RESOURCE",
                    info["proxy"])
                self.assertIn("BLOCKING",info["missing_states"])
                self.assertTrue(info[
                    "idle_and_available_are_not_inferred_from_silence"])
        self.assertTrue(r["B2_no_availability_telemetry"])
        self.assertEqual("PROCESSING_ONLY_NOT_FULL_APM_OR_CAUSAL_ORACLE",
                         r["active_period_proxy_scope"])

    def test_13_no_inference_leak_or_f5_claim(self):
        r=self.report
        self.assertEqual("PARTIAL",r["A3"])
        self.assertEqual("NOT_RUN",r["G4"])
        self.assertEqual("NOT_RUN",r["G5"])
        self.assertEqual("NOT_CREATED",r["F5_independent_reserve"])
        self.assertEqual(0,r["provider_calls"])
        self.assertTrue(r["B2_and_DES_evidence_only_on_evaluator_side"])
        self.assertTrue(r["not_blind_O0_O1_inference_by_D_B_M"])
        self.assertTrue(r["not_a_new_fourth_arm"])
        self.assertEqual("NOT_TRIGGERED",r["P_PM14"])
        serialized=json.dumps(r,sort_keys=True)
        self.assertNotIn("O000",serialized)
        self.assertNotIn("t_minutes_exact",serialized)
        self.assertNotIn("service_minutes",serialized)


if __name__=="__main__":
    unittest.main()
