"""Arena Café: actual queue/throughput diagnosis from one instrumented cafe log."""
from __future__ import annotations
import csv
from fractions import Fraction as Q
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

import arena_ev01_event_views as ev01
import arena_cafeteria_operational_closure as cafe
from scripts import arena_event_observability as obs


class CafeOperationalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.truth,cls.snapshots=ev01.trace_generator()
        cls.full=obs.project_events(cls.truth,"FULL")
        cls.server_count=dict(zip(ev01.STAGES,(s[0] for s in ev01.SPEC)))

    def test_15_orders_and_four_stages_prove_exact_balance(self):
        r=cafe.diagnosis(self.full,self.server_count)
        self.assertEqual(r["n_orders"],15)
        self.assertEqual(r["stage_order_directly_observed"],list(ev01.STAGES))
        self.assertEqual(r["cycle_balances_passed"],15)
        self.assertEqual(r["top_waiting_stage"],"preparacion")
        self.assertEqual(r["n_stages_actually_instrumented"],4)
        self.assertGreater(Q(r["stage_metrics"]["preparacion"]["mean_wait_minutes_exact"]),
                           Q(r["stage_metrics"]["caja"]["mean_wait_minutes_exact"]))
        self.assertEqual(r["stage_metrics"]["transferencia_final"]
                         ["mean_wait_minutes_exact"],"0")
        self.assertEqual(sum(r["stage_metrics"][s]["share_total_wait_percent"]
                             for s in ev01.STAGES),100.0)
        self.assertGreater(r["stage_metrics"]["preparacion"]["max_waiting_at_event_boundaries"],0)

    def test_measured_wait_and_service_exactly_match_known_physical_trace(self):
        stats=cafe.diagnosis(self.full,self.server_count)["stage_metrics"]
        self.assertEqual(stats["preparacion"]["mean_service_minutes_exact"],"15/17")
        self.assertEqual(stats["despacho"]["mean_service_minutes_exact"],"30/43")
        self.assertEqual(stats["transferencia_final"]["mean_service_minutes_exact"],"3/11")
        self.assertEqual(stats["caja"]["mean_service_minutes_exact"],"1")
        self.assertEqual(stats["preparacion"]["mean_wait_minutes_exact"],"3472/1275")
        self.assertEqual(stats["caja"]["mean_wait_minutes_exact"],"49/75")

    def test_denies_internal_queue_diagnosis_from_pos_and_kds(self):
        for view in ("POS","POS_KDS"):
            data=obs.project_events(self.truth,view)
            with self.assertRaises((ValueError,KeyError)):
                cafe.diagnosis(data,self.server_count)
            reading=obs.analyze_view(data,view)
            self.assertTrue(all("per_stage_observed" not in row for row in reading["cases"]))

    def test_duplicate_clock_or_resource_corruption_is_rejected(self):
        x=[dict(r) for r in self.full]
        target=next(r for r in x if r.get("stage")=="preparacion"
                    and r["event_type"]=="servicio_inicio")
        target["t_minutes_exact"]="-1"
        with self.assertRaises(ValueError):
            cafe.diagnosis(x,self.server_count)
        with self.assertRaisesRegex(ValueError,"CAFE_INVALID_SERVER_CAPACITY"):
            cafe.diagnosis(self.full,{**self.server_count,"preparacion":0})
        with self.assertRaisesRegex(ValueError,"CAFE_SERVER_SCHEMA_NOT_MATCH_STAGE_OBSERVATION"):
            cafe.diagnosis(self.full,{"preparacion":1})

    def test_full_csv_parser_reads_existing_ev01_export_and_requires_all_fields(self):
        with TemporaryDirectory() as tmp:
            out=Path(tmp)/"full.csv"
            headers=("case_id","event_seq","activity","event_type",
                     "t_minutes_exact","source","stage","resource_id")
            with out.open("w",encoding="utf-8",newline="") as fh:
                w=csv.DictWriter(fh,fieldnames=headers)
                w.writeheader()
                w.writerows(self.full)
            read=cafe.read_full_csv(out)
            self.assertEqual(cafe.diagnosis(read,self.server_count)["top_waiting_stage"],
                             "preparacion")
            with out.open("w",encoding="utf-8") as fh:
                fh.write("case_id,event_type,t_minutes_exact\nO000,created,0\n")
            with self.assertRaisesRegex(ValueError,"CAFE_FULL_INSTRUMENTATION_REQUIRED"):
                cafe.read_full_csv(out)

    def test_tied_events_are_grouped_not_false_queue_spikes(self):
        peaks=cafe.queue_peaks(self.full,ev01.STAGES)
        self.assertEqual(peaks["transferencia_final"],0)
        self.assertEqual(peaks["despacho"],0)
        self.assertGreater(peaks["preparacion"],0)
        self.assertGreater(peaks["caja"],0)

    def test_baseline_and_two_capacity_changes_use_existing_des(self):
        comparisons=cafe.compare_capacity_scenarios(
            ev01.config(),ev01.ARRIVALS,cafe.CHECKPOINTS,
            {"extra_preparation":1,"extra_cashier":0})
        self.assertEqual(comparisons["model"],"CAF01_DETERMINISTIC_DES")
        base=comparisons["baseline_snapshots"]
        prep=comparisons["alternatives"]["extra_preparation"]
        cashier=comparisons["alternatives"]["extra_cashier"]
        self.assertLess(base["10"]["delivered"],15)
        self.assertGreaterEqual(prep["snapshots"]["10"]["delivered"],
                                base["10"]["delivered"])
        self.assertGreaterEqual(cashier["snapshots"]["10"]["delivered"],
                                base["10"]["delivered"])
        self.assertGreater(max(prep["delta_delivered_vs_baseline"].values()),0)
        self.assertGreater(max(prep["delta_delivered_vs_baseline"].values()),
                           max(cashier["delta_delivered_vs_baseline"].values()))
        self.assertTrue(comparisons["counterfactuals_do_not_measure_cost_or_workstation_feasibility"])

    def test_end_to_end_reproduces_report_and_signed_manifest(self):
        with TemporaryDirectory() as tmp:
            out=Path(tmp)/"cafe"
            report=cafe.run(out,"a"*40,"b"*40)
            self.assertEqual(report["full_operational_diagnosis"]["n_orders"],15)
            self.assertEqual(report["recommendation"],"SIMULATE_EXTRA_PREPARATION_CAPACITY_FIRST")
            self.assertTrue(report["uses_only_full_instrumentation_for_internal_waits"])
            self.assertFalse(report["real_business_validated"])
            self.assertTrue(report["physical_feasibility_and_cost_not_verified"])
            self.assertEqual(report["observability"]["POS"],
                             "CYCLE_ONLY_NO_INTERNAL_DECOMPOSITION")
            self.assertTrue((out/"02_DIAGNOSTICO.md").read_text().startswith("# Diagnóstico operativo"))
            manifest=json.loads((out/"03_MANIFEST.json").read_text())
            for name,digest in manifest["files_sha256"].items():
                self.assertEqual(digest,"sha256:"+sha256((out/name).read_bytes()).hexdigest())
            with self.assertRaisesRegex(ValueError,"CAFE_REFUSE_OVERWRITE"):
                cafe.run(out,"a"*40,"b"*40)


if __name__=="__main__":
    unittest.main(verbosity=2)
