"""F2 B0/B1/B2 controls: test known synthetic source and negative physical semantics."""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction as Q
import unittest

from scripts.arena_cafe import ev01
from scripts.arena_cafe import f2_physical_controls as f2
from scripts import arena_event_observability as obs


class F2PhysicalControlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw,cls.snap=ev01.trace_generator()
        cls.views={v:obs.project_events(cls.raw,v) for v in obs.VIEWS}
        cls.resources={stage:[f"{stage}-r{i+1}" for i in range(n)]
                       for stage,(n,_) in zip(ev01.STAGES,ev01.SPEC)}
        cls.available={rid:[("0","30")] for ids in cls.resources.values() for rid in ids}

    def test_replay_15_orders_45_75_225_and_nine_parity_checkpoints(self):
        report=f2.build()
        self.assertEqual(15,report["regression"]["n_orders"])
        self.assertEqual((45,75,225),
                         tuple(report["regression"][f"events_{v}"]
                               for v in ("POS","POS_KDS","FULL")))
        self.assertEqual(9,report["regression"]["checkpoints"])
        self.assertEqual("PARITY_CONFIRMED_ALL_SNAPSHOTS",
                         report["regression"]["independent_DES_parity"])
        self.assertFalse(report["new_engine_implemented"])
        self.assertEqual("NOT_ESTABLISHED",report["causal_bottleneck_discovery"])

    def test_b0_pos_conservation_no_hidden_stage_reconstruction(self):
        report=f2.b0_public(self.views["POS"],self.snap)
        self.assertEqual(9,len(report["checkpoints"]))
        self.assertEqual("B0_POS_MATERIAL_BALANCE_PASS",report["status"])
        self.assertEqual(0,report["checkpoints"][-1]["work_in_process_orders"])
        self.assertEqual(15,report["checkpoints"][-1]["delivered_cumulative"])
        self.assertNotIn("transferencia_final",str(report))
        self.assertEqual("NOT_IDENTIFIABLE",report["latent_stages_from_POS"])
        bad=deepcopy(self.snap)
        bad[2]["pending"]+=1
        with self.assertRaisesRegex(ValueError,"F2_B0_MATERIAL_NOT_CONSERVED"):
            f2.b0_public(self.views["POS"],bad)

    def test_b1_has_real_full_stages_and_cannot_use_pos_or_kds(self):
        report=f2.b1_physical(self.views["FULL"],
                {stage:n for stage,(n,_) in zip(ev01.STAGES,ev01.SPEC)})
        self.assertEqual("B1_DIRECT_FULL_INSTRUMENTATION_PASS",report["status"])
        self.assertEqual(15,report["case_cycle_balances"])
        self.assertEqual("3472/1275",report["operational_diagnosis"]
                         ["stage_metrics"]["preparacion"]["mean_wait_minutes_exact"])
        self.assertEqual("preparacion",report["operational_diagnosis"]["top_waiting_stage"])
        for s in ev01.STAGES:
            self.assertEqual({"entrances":15,"starts":15,"completions":15},
                             report["stage_event_balances"][s])
        for view in ("POS","POS_KDS"):
            with self.assertRaisesRegex(ValueError,"F2_B1_FULL_EVENT_INSTRUMENTATION_REQUIRED"):
                f2.b1_physical(self.views[view],
                    {stage:n for stage,(n,_) in zip(ev01.STAGES,ev01.SPEC)})

    def test_b2_per_physical_resource_exact_coverage_and_noncausal_activity(self):
        report=f2.resource_periods(self.views["FULL"],self.resources,"30",
                                   available=self.available)
        self.assertEqual("B2_EXACT_RESOURCE_PERIODS_PASS",report["status"])
        self.assertTrue(report["no_finite_buffer_or_blocked_after_service_in_original_DES"])
        self.assertEqual(["PROCESSING"],report["ACTIVE_definition"]["active_kinds"])
        self.assertEqual("NOT_ESTABLISHED",report["bottleneck_causal_discovery"])
        self.assertGreater(len(report["segments"]),30)
        self.assertEqual(5,len(report["resource_total_minutes"]))
        for rid,states in report["resource_total_minutes"].items():
            self.assertEqual(Q(30),sum((Q(s) for s in states.values()),Q()))
            self.assertNotIn("BLOCKED_AFTER_SERVICE",states)
            self.assertNotIn("WAITING_FOR_OPERATOR",states)
        self.assertTrue(any(
            x["by_stage"]["preparacion"]["ALL_ACTIVE"] is True
            for x in report["segments"]))
        self.assertTrue(any(
            x["by_stage"]["preparacion"]["ALL_ACTIVE"] is False
            for x in report["segments"]))
        # Stage wait pressure is not 'all stations are causal bottlenecks'.
        self.assertTrue(all(x["by_stage"]["despacho"]
                            ["aggregate_is_descriptive_not_causal_bottleneck"]
                            for x in report["segments"]))

    def test_b2_tri_state_nonvacuity_missing_telemetry_and_admin_semantics(self):
        self.assertEqual(("NO_AVAILABLE_RESOURCES","NO_AVAILABLE_RESOURCES"),
                         f2.aggregate_activity([],[]))
        self.assertEqual(("UNKNOWN","UNKNOWN"),
                         f2.aggregate_activity([],[],["prep-r1"]))
        self.assertEqual((True,"UNKNOWN"),
                         f2.aggregate_activity(["prep-r1"],["prep-r1"],["prep-r2"]))
        self.assertEqual((False,False),
                         f2.aggregate_activity(["prep-r1"],[]))
        unknown=f2.resource_periods(self.views["FULL"],self.resources,"30")
        self.assertEqual("NO_AVAILABILITY_TELEMETRY",unknown["availability_source"])
        self.assertTrue(any(
            x["by_stage"]["preparacion"]["ALL_ACTIVE"]=="UNKNOWN"
            for x in unknown["segments"]))
        bad=deepcopy(self.views["FULL"])
        row=next(r for r in bad if r["event_type"]=="servicio_inicio")
        row["source"]="administrative_pos_timestamp"
        with self.assertRaisesRegex(ValueError,"F2_ADMINISTRATIVE_NOT_PHYSICAL_TELEMETRY"):
            f2.resource_periods(bad,self.resources,"30",available=self.available)

    def test_b2_missing_and_overlapping_resource_intervals_rejected(self):
        bad=[dict(r) for r in self.views["FULL"]]
        bad.pop(next(i for i,x in enumerate(bad)
                     if x["event_type"]=="servicio_fin" and x.get("stage")=="caja"))
        with self.assertRaisesRegex(ValueError,"F2_RESOURCE_INCOMPLETE_SERVICE_INTERVAL"):
            f2.resource_periods(bad,self.resources,"30",available=self.available)
        x=deepcopy(self.views["FULL"])
        for row in x:
            if row.get("resource_id")=="caja-r2":
                row["resource_id"]="caja-r1"
        with self.assertRaisesRegex(ValueError,"F2_RESOURCE_OVERLAPPED_SERVICES"):
            f2.resource_periods(x,self.resources,"30",available=self.available)
        none={rid:[] for ids in self.resources.values() for rid in ids}
        with self.assertRaisesRegex(ValueError,"F2_RESOURCE_PROCESSING_WHILE_UNAVAILABLE"):
            f2.resource_periods(self.views["FULL"],self.resources,"30",
                                available=none)

    def test_separate_sustained_150hr_and_exact_120_68_86_220_ceilings(self):
        report=f2.sustained()
        self.assertEqual("F2_SEPARATE_SUSTAINED_CONTROL_COMPLETED",report["status"])
        self.assertEqual("150",report["demand_orders_per_hour_exact"])
        self.assertEqual("(30,90] minutes",report["measurement_window"])
        scenarios=report["scenarios"]
        self.assertEqual({"base":"68","plus_one_preparation":"86",
                          "plus_one_cashier":"68",
                          "plus_one_preparation_and_dispatch":"120"},
                         {k:v["analytic_ceiling_orders_per_hour_exact"]
                          for k,v in scenarios.items()})
        self.assertEqual(150,scenarios["base"]["new_arrivals_in_interval"])
        for item in scenarios.values():
            self.assertEqual(
                item["initial_pending_at_t0"]+item["new_arrivals_in_interval"]-
                item["delivered_in_interval"],item["pending_at_t1"])
            self.assertTrue(item["demand_exceeds_ceiling"])
            self.assertFalse(item["stable_stationary_WIP_claim"])
            self.assertTrue(item["finite_difference_is_phase_and_transient_sensitive"])
        self.assertGreater(scenarios["plus_one_preparation"]["delivered_in_interval"],
                           scenarios["base"]["delivered_in_interval"])
        self.assertEqual(scenarios["base"]["delivered_in_interval"],
                         scenarios["plus_one_cashier"]["delivered_in_interval"])
        self.assertGreater(scenarios["plus_one_preparation_and_dispatch"]
                           ["delivered_in_interval"],
                           scenarios["plus_one_preparation"]["delivered_in_interval"])
        self.assertEqual("NOT_ASSESSED",report["workstation_space_inventory_feasibility"])


if __name__=="__main__":
    unittest.main()
