"""RF-02T causal event kernel without external solver, DES or provider calls."""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction as Q
import hashlib
import json
import os
from pathlib import Path
import unittest

from scripts.arena_cafe import evidence
from scripts.arena_cafe import r2_causal_pos_signal as t
from scripts.arena_cafe import r2_observational_contracts as r2
from scripts.arena_v0_contract import digest,ArenaContractError


class CausalPOS(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=os.environ.get("RF02_PUBLIC_DIR")
        if not root:
            raise unittest.SkipTest("RF02_PUBLIC_DIR must name the frozen A1 public artifact")
        cls.views={condition:json.loads(
            (Path(root)/(condition+"_VISIBLE.json")).read_text())
            for condition in ("O0","O1")}

    def test_00_exact_causal_kernel_has_no_pre_event_mass(self):
        out=t._signal([Q(3,10)],Q(10),Q(1,2))
        self.assertEqual("1",out["total_event_mass_orders_exact"])
        self.assertEqual("1",out["mass_before_cutoff_orders_exact"])
        self.assertEqual("0",out["mass_deferred_after_cutoff_orders_exact"])
        self.assertEqual(0,t.event_rate_at([Q(3,10)],Q(1,2),Q(1,4)))
        self.assertEqual(0,t.event_mass_until([Q(3,10)],Q(1,2),Q(3,10)))
        self.assertEqual(2,t.event_rate_at([Q(3,10)],Q(1,2),Q(3,10)))
        self.assertEqual(0,t.event_rate_at([Q(3,10)],Q(1,2),Q(4,5)))
        self.assertEqual(1,t.event_mass_until([Q(3,10)],Q(1,2),Q(4,5)))
        self.assertEqual(0,t.event_rate_at([Q(3,10)],Q(1,2),Q(-1,2)))
        self.assertTrue(out["no_lookahead_in_mathematical_kernel"])

    def test_01_tail_after_cutoff_deferred_not_redistributed(self):
        out=t._signal([Q(99,10)],Q(10),Q(1,2))
        self.assertEqual("1/5",out["mass_before_cutoff_orders_exact"])
        self.assertEqual("4/5",out["mass_deferred_after_cutoff_orders_exact"])
        self.assertEqual("52/5",out["support_end_minutes_exact"])
        self.assertTrue(out["tail_not_truncated_or_moved_before_event"])
        self.assertEqual(Q(1,5),t.event_mass_until([Q(99,10)],Q(1,2),Q(10)))
        self.assertEqual(Q(1),t.event_mass_until([Q(99,10)],Q(1,2),Q(52,5)))

    def test_02_multiple_overlaps_and_simultaneous_event_masses(self):
        cases=[
            ([Q(1),Q(1),Q(6,5)],Q(1,2),Q(10)),
            ([Q(0),Q(1,4),Q(3,4),Q(19,2)],Q(1/2),Q(10)),
            ([Q(1,3),Q(2,3),Q(9,10)],Q(1,4),Q(10)),
        ]
        for times,width,cutoff in cases:
            with self.subTest(times=times):
                x=t._signal(times,cutoff,width)
                b=Q(x["mass_before_cutoff_orders_exact"])
                a=Q(x["mass_deferred_after_cutoff_orders_exact"])
                self.assertEqual(Q(len(times)),a+b)
                self.assertEqual(b,t.event_mass_until(times,width,cutoff))
                for segment in x["segments"]:
                    start=Q(segment["start_minutes_exact"])
                    end=Q(segment["end_minutes_exact"])
                    rate=Q(segment["rate_orders_per_minute_exact"])
                    self.assertEqual(rate,t.event_rate_at(times,width,start))
                    self.assertEqual(rate*(end-start),
                                     Q(segment["mass_orders_exact"]))
                    self.assertGreaterEqual(rate,0)

    def test_03_invalid_events_and_unregistered_width_rejected(self):
        for events,cutoff,width in (
            ([Q(-1,2)],Q(10),Q(1,2)),
            ([Q(10)],Q(10),Q(1,2)),
            ([Q(3),Q(1)],Q(10),Q(1,2)),
            ([Q(1)],Q(10),Q(1,3)),
        ):
            with self.subTest(events=events,width=width):
                with self.assertRaises(ArenaContractError):
                    t._signal(events,cutoff,width)

    def test_04_observed_pos_O0_O1_exact_same_signal_with_distinct_views(self):
        a=t.from_visible(self.views["O0"],"O0")
        b=t.from_visible(self.views["O1"],"O1")
        self.assertNotEqual(a["public_input_sha256"],b["public_input_sha256"])
        self.assertEqual(a["signal"],b["signal"])
        self.assertEqual(a["events_hash"],b["events_hash"])
        self.assertEqual(15,a["signal"]["events_count"])
        self.assertEqual("1/2",a["signal"]["width_minutes_exact"])
        self.assertEqual(
            "CAUSAL_RIGHT_RECTANGULAR_EVENT_KERNEL/0.1",a["signal"]["policy"])
        self.assertEqual("NOT_GRANTED",a["scientific_policy_approval"])
        self.assertEqual("NOT_RUN",a["G2"])
        self.assertEqual("NOT_RUN",b["G3"])
        mass=Q(a["signal"]["mass_before_cutoff_orders_exact"])
        tail=Q(a["signal"]["mass_deferred_after_cutoff_orders_exact"])
        self.assertEqual(15,mass+tail)

    def test_05_delivery_observations_do_not_alter_the_signal(self):
        old=self.views["O0"]
        new=deepcopy(old)
        for row in new["construction"]["observation_series"]:
            row["delivered_cumulative"]=0
        new["source_snapshot_hash"]=digest({
            "schema":evidence.SCHEMA,
            "condition":"O0",
            "cutoff_minutes_exact":str(new["observability"]["cutoff_minutes_exact"]),
            "construction":new["construction"]})
        old_sig=t.from_visible(old,"O0")
        new_sig=t.from_visible(new,"O0")
        self.assertNotEqual(old_sig["public_input_sha256"],
                            new_sig["public_input_sha256"])
        self.assertEqual(old_sig["signal"],new_sig["signal"])
        self.assertEqual(old_sig["events_hash"],new_sig["events_hash"])

    def test_06_sensitivity_policies_are_predeclared_not_G3_selected(self):
        signals=[t.from_visible(self.views["O0"],"O0",width=w) for w in
                 t.SENSITIVITY_WIDTHS]
        self.assertEqual(["1/4","1/2","1"],
                         [x["signal"]["width_minutes_exact"] for x in signals])
        self.assertEqual(3,len({x["signal"]["event_rate_signal_sha256"]
                                for x in signals}))
        self.assertTrue(all(x["selection_after_G3"]=="FORBIDDEN" and
                            x["G2"]==x["G3"]=="NOT_RUN" for x in signals))

    @staticmethod
    def nominal():
        # Conformance ONLY: intentionally unrelated to Short E1 nominal.
        return {
            "capacity":{"value":1.23,"unit":"orders/minute","status":"ASSUMED",
                        "actor":"INVESTIGATOR","source_kind":
                        "EXPLICIT_UNVALIDATED_ASSUMPTION",
                        "source_ref":"RF02T-FIXTURE-RENDER-ONLY"},
            "response_time":{"value":2.7,"unit":"minute","status":"ASSUMED",
                        "actor":"INVESTIGATOR","source_kind":
                        "EXPLICIT_UNVALIDATED_ASSUMPTION",
                        "source_ref":"RF02T-FIXTURE-RENDER-ONLY"},
            "loss_time":{"value":8.1,"unit":"minute","status":"ASSUMED",
                        "actor":"INVESTIGATOR","source_kind":
                        "EXPLICIT_UNVALIDATED_ASSUMPTION",
                        "source_ref":"RF02T-FIXTURE-RENDER-ONLY"},
        }

    def test_07_all_six_D_native_rendered_texts_causal_no_solver(self):
        params=self.nominal()
        for condition in ("O0","O1"):
            x=t.render_six_with_declared_nominals(
                self.views[condition],condition,params)
            self.assertEqual(6,x["candidate_count"])
            self.assertEqual("NONE",x["selection_owner"])
            self.assertEqual(0,x["solver_invocations"])
            self.assertEqual("NOT_RUN",x["G2"])
            self.assertEqual("NOT_ESTABLISHED",x["scientific_adequacy"])
            self.assertEqual(6,len({row["modelica_sha256"] for row in x["candidates"]}))
            self.assertEqual([1,1,2,2,3,3],
                [len(r2.topology(n,loss)["stocks"])
                 for n in (1,2,3) for loss in (False,True)])
            for candidate in x["candidates"]:
                source=candidate["modelica"]
                self.assertIn("time >=",source)
                self.assertIn("inputRate = (if ",source)
                self.assertNotIn("pulseRate",source)
                self.assertNotIn("pulseDuration",source)
                self.assertEqual("NOT_RUN",candidate["G3"])
                self.assertTrue(candidate[
                    "all_native_balance_and_bound_equations_unchanged"])
                self.assertEqual("sha256:"+hashlib.sha256(
                    source.encode()).hexdigest(),candidate["modelica_sha256"])
        a=t.render_six_with_declared_nominals(self.views["O0"],"O0",params)
        b=t.render_six_with_declared_nominals(self.views["O1"],"O1",params)
        self.assertEqual([r["modelica_sha256"] for r in a["candidates"]],
                         [r["modelica_sha256"] for r in b["candidates"]])

    def test_08_render_refuses_unproven_or_other_arm_nominals(self):
        p=self.nominal()
        bad=deepcopy(p);bad["capacity"]["source_ref"]="E1_REGISTRY"
        with self.assertRaises(ArenaContractError):
            t.render_six_with_declared_nominals(
                self.views["O0"],"O0",bad)
        bad=deepcopy(p);bad["loss_time"]["value"]=0
        with self.assertRaises(ArenaContractError):
            t.render_six_with_declared_nominals(
                self.views["O0"],"O0",bad)
        with self.assertRaises(ArenaContractError):
            t.render_six_with_declared_nominals(
                self.views["O0"],"O0",None)

    def test_09_source_and_scope_rejection_for_future_or_physical_leak(self):
        visible=self.views["O0"]
        bad=deepcopy(visible)
        bad["construction"]["physical_observation"]={"secret":1}
        with self.assertRaises(ArenaContractError):
            t.from_visible(bad,"O0")
        with self.assertRaises(ArenaContractError):
            t.from_visible(visible,"O1")
        bad=deepcopy(visible)
        bad["construction"]["pos_arrival_events"][-1]["t_minutes_exact"]="11"
        with self.assertRaises(ArenaContractError):
            t.from_visible(bad,"O0")


if __name__=="__main__":
    unittest.main()
