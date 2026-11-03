"""Adversarial same-information PM value checks on already-mined EV-01."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import unittest

from scripts.arena_cafe import f3_pm_incremental as pm


@unittest.skipUnless(
    all(os.environ.get(k) for k in (
        "F3P_EV01_REPORT","F3P_FULL_CSV","F3P_F2_REPORT",
        "F3P_O0","F3P_O1")),
    "Needs original PM4Py EV01 report, evaluator FULL and B0/B1/B2, A1 O0/O1")
class OriginalPmEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load=lambda name:json.loads(
            Path(os.environ[name]).read_text(encoding="utf-8"))
        cls.ev01=load("F3P_EV01_REPORT")
        cls.full=pm.read_full(os.environ["F3P_FULL_CSV"])
        cls.f2=load("F3P_F2_REPORT")
        cls.o0=load("F3P_O0")
        cls.o1=load("F3P_O1")
        cls.report=pm.audit(cls.ev01,cls.full,cls.f2,cls.o0,cls.o1)

    def test_01_original_pm_recomputed_exactly_from_cases(self):
        r=self.report
        self.assertEqual(15,r["n_cases"])
        self.assertEqual(1,r["full_case_route_variants"])
        self.assertEqual(0,r["repeated_stage_cases"])
        self.assertEqual(15,r["full_case_route_counts"][0]["cases"])
        self.assertTrue(r["full_dfg_14_edges_count_15_each"])
        self.assertEqual(
            {"POS":{"activities":3,"dfg_edges":2},
             "POS_KDS":{"activities":5,"dfg_edges":4},
             "FULL":{"activities":15,"dfg_edges":14}},
            r["pm4py_event_views"])

    def test_02_identifiability_and_scope_unchanged(self):
        r=self.report
        self.assertEqual(
            "NO_INCREMENTAL_ROUTE_VARIATION_OVER_B1_IN_KNOWN_EV01",
            r["incremental_process_information_verdict"])
        self.assertEqual(
            "NOT_OBSERVED_IN_THIS_EV01",
            r["PM_reveals_additional_structural_requirement_over_B1"])
        self.assertEqual("NOT_TRIGGERED_FOR_THIS_KNOWN_CONTROL",r["PM_14"])
        self.assertEqual("NOT_ADJUDICATED",r["global_F6"])
        self.assertEqual("NOT_RUN",r["same_evidence_P_ablation_per_D_B_M"])
        self.assertEqual("PARTIAL",r["A3"])
        self.assertEqual("NOT_RUN",r["G4"])
        self.assertEqual("NOT_RUN",r["G5"])
        self.assertTrue(r["no_new_PM_or_DES_or_provider_execution"])

    def test_03_poisoned_mined_edge_is_rejected(self):
        fake=deepcopy(self.ev01)
        fake["pm4py_discovery"]["FULL"]["edges"][0]["count"]-=1
        with self.assertRaises((ValueError,AssertionError)):
            pm.audit(fake,self.full,self.f2,self.o0,self.o1)

    def test_04_cross_view_stage_leak_is_rejected(self):
        fake=deepcopy(self.o0)
        fake["construction"]["pos_arrival_events"][0]["stage"]="despacho"
        with self.assertRaises((ValueError,AssertionError)):
            pm.audit(self.ev01,self.full,self.f2,fake,self.o1)

    def test_05_f2_b1_stage_corruption_is_rejected(self):
        fake=deepcopy(self.f2)
        fake["B1"]["operational_diagnosis"]["stage_order_directly_observed"]=[
            "despacho","preparacion","caja","transferencia_final"]
        with self.assertRaises((ValueError,AssertionError)):
            pm.audit(self.ev01,self.full,fake,self.o0,self.o1)

    def test_06_invalid_physical_source_not_silently_promoted(self):
        rows=deepcopy(self.full)
        row=next(x for x in rows if x["event_type"]=="servicio_inicio")
        row["source"]="kds_click"
        with self.assertRaises((ValueError,AssertionError)):
            pm.audit(self.ev01,rows,self.f2,self.o0,self.o1)

    def test_07_inconsistent_disclosed_window_not_accepted(self):
        fake=deepcopy(self.o1)
        fake["observability"]["cutoff_minutes_exact"]="12"
        with self.assertRaises((ValueError,AssertionError)):
            pm.audit(self.ev01,self.full,self.f2,self.o0,fake)


if __name__=="__main__":
    unittest.main()
