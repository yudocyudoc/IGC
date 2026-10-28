#!/usr/bin/env python3
"""Only invented construction arrays. No DES or real Buffalo evidence is used."""
import copy
import json
import unittest
from pathlib import Path

from caf01_g3 import (CONTRACT, G3Blocked, BAND, EPS, MASS,
                      SCHEMA, digest, inventory, lock_forecasts, plan, select)


class TestCAF01G3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(Path(CONTRACT).read_text(encoding="utf-8"))

    def evidence(self, case="CAF01"):
        full = [0, 1, 2, 3, 4, 5, 6]
        times = [0, 5, 10, 15, 20, 30, 40]
        if case == "CAFN":
            full, times = [0, 6], [0, 40]
        return {"schema": SCHEMA, "case": case,
                "source_snapshot_sha256": "sha256:" + "a"*64,
                "public_pulse": {"kind": "pulse", "rate_per_minute": 1.2,
                                 "duration_minutes": 20},
                "observations": [{"t_min": t, "delivered": y}
                                 for t, y in zip(times, full)]}

    def rows(self, evidence, ready=None):
        ready = ready or {}
        rows = []
        for item in inventory(self.contract):
            pred = ready.get(item["id"])
            ok = pred is not None
            rows.append({
                "id": item["id"],
                "gates": {"G0": "PASS" if ok else "PENDING",
                          "G1": "PASS" if ok else "PENDING",
                          "G2": "PASS" if ok else "PENDING"},
                "construction_delivered": pred if ok else None,
                "native_sha256": "sha256:" + "b"*64 if ok else None,
                "g2_receipt_sha256": "sha256:" + "c"*64 if ok else None,
                "balance_max_abs": 0.002 if ok else None,
                "block_reason": None if ok else "AWAITING_G2",
                "candidate_evidence_sha256": digest(evidence),
            })
        return rows

    def future(self, selection, forecasts):
        return {"schema": SCHEMA,
                "selection_sha256": selection["selection_sha256"],
                "source_snapshot_sha256": selection["source_snapshot_sha256"],
                "evaluation_pulse": {
                    "kind": "pulse", "rate_per_minute": 1.5, "duration_minutes": 20},
                "forecast_by_candidate": forecasts}

    def test_inventory_and_conditional_budgets(self):
        p = plan(self.contract)
        by = p["construction_candidate_inventory"]
        self.assertEqual(len(by), 25)
        self.assertEqual(sum(x["arm"] == "D" for x in by), 18)
        self.assertEqual(sum(x["arm"] == "M" for x in by), 6)
        self.assertEqual(sum(x["arm"] == "B" for x in by), 1)
        self.assertNotIn("M_C00_C100", {x["id"] for x in by})
        for s in ("C00", "C01", "C02"):
            self.assertEqual(next(x["nominal_aliases"] for x in by
                             if x["id"] == "M_" + s + "_C72"), [72,100])
        self.assertEqual(p["conditional_total_modelica_ceiling"], 20)
        self.assertEqual(p["v03_original_modelica_ceiling_unchanged"], 26)
        self.assertEqual((p["RK4_D_CAF01_max"], p["RK4_D_CAFN_max"]), (18,18))

    def test_construction_selects_unique_conditional_D_without_future(self):
        e = self.evidence()
        rows = self.rows(e, {"D1_C48_T0.125": [0,1,2,3,4,5,6]})
        s = select(self.contract,e,rows)
        self.assertEqual(s["decision"]["D"]["winners"], ["D1_C48_T0.125"])
        self.assertEqual(s["decision"]["D"]["status"], "CONDITIONAL_SINGLE_WINNER")
        self.assertEqual(s["decision"]["M"]["status"], "NO_VALID_CANDIDATE")
        self.assertEqual(s["decision"]["B"]["status"], "NO_VALID_CANDIDATE")
        self.assertEqual(s["g2_evidence"], "RECEIPT_HASH_ASSERTED_REQUIRES_EXTERNAL_VERIFICATION")

    def test_D_same_structure_near_best_requires_parameter_abstention(self):
        e = self.evidence()
        rows = self.rows(e, {"D1_C48_T0.125": [0,1,2,3,4,5,6],
                             "D1_C72_T0.25": [0,1.2,2.2,3.2,4.2,5.2,6.2]})
        s = select(self.contract,e,rows)
        d = s["decision"]["D"]
        self.assertEqual(d["winners"], ["D1_C48_T0.125"])
        self.assertTrue(d["parameter_ambiguity"])
        self.assertIn("D1_C72_T0.25", d["near_best_alternatives"]["D1"])
        lock = lock_forecasts(self.contract,s,self.future(s,{"D1_C48_T0.125":[1,2,3,4,5,6]}))
        self.assertEqual(lock["arm_forecasts"]["D"]["status"],
                         "ABSTAIN_POINT_PARAMETER_UNIDENTIFIABLE")
        self.assertIsNone(lock["arm_forecasts"]["D"]["prediction"])

    def test_nearby_distinct_structures_retained_not_merged(self):
        e = self.evidence()
        rows = self.rows(e, {"D1_C48_T0.125": [0,1,2,3,4,5,6],
                             "D2_C48_T0.125": [0,1.2,2.2,3.2,4.2,5.2,6.2]})
        s = select(self.contract,e,rows)
        self.assertEqual(len(s["decision"]["D"]["winners"]), 2)
        self.assertEqual(s["decision"]["D"]["status"],
                         "STRUCTURE_OR_PARAMETER_NOT_IDENTIFIABLE")
        f = self.future(s,{"D1_C48_T0.125":[1,2,3,4,5,6],
                           "D2_C48_T0.125":[1,2,4,5,6,7]})
        lock = lock_forecasts(self.contract,s,f)
        self.assertEqual(lock["arm_forecasts"]["D"]["status"],
                         "ABSTAIN_POINT_DIVERGENT_COMPATIBLE_STRUCTURES")
        self.assertEqual(lock["arm_forecasts"]["D"]["envelope"][2],
                         {"min":3, "max":4})

    def test_multiple_structures_same_future_may_share_curve_not_identity(self):
        e = self.evidence()
        rows = self.rows(e, {"M_C00_C72": [0,1,2,3,4,5,6],
                             "M_C01_C72": [0,1,2,3,4,5,6]})
        s = select(self.contract,e,rows)
        self.assertEqual(s["decision"]["M"]["status"],
                         "STRUCTURE_OR_PARAMETER_NOT_IDENTIFIABLE")
        f = self.future(s,{i:[1,2,3,4,5,6] for i in s["decision"]["M"]["winners"]})
        lock = lock_forecasts(self.contract,s,f)
        self.assertEqual(lock["arm_forecasts"]["M"]["status"],
                         "SHARED_FORECAST_MULTIPLE_STRUCTURES_NOT_IDENTIFIED")
        self.assertEqual(lock["arm_forecasts"]["M"]["prediction"],[1,2,3,4,5,6])

    def test_numerical_equivalence_does_not_force_cross_structure_merging(self):
        e = self.evidence()
        ready = {"M_C00_C72": [0,1,2,3,4,5,6],
                 "M_C01_C72": [0,1,2,3,4,5,6]}
        s = select(self.contract, e,self.rows(e,ready))
        self.assertEqual(len(s["decision"]["M"]["winners"]),2)

    def test_B_single_or_blocked_but_never_imputed(self):
        e = self.evidence()
        s = select(self.contract,e,self.rows(e,{"B_NATIVE_1":[0,1,2,3,4,5,6]}))
        self.assertEqual(s["decision"]["B"]["winners"],["B_NATIVE_1"])
        self.assertEqual(s["decision"]["D"]["status"],"NO_VALID_CANDIDATE")

    def test_CAFN_strict_mask_and_no_claim_of_internal_trajectory(self):
        e = self.evidence("CAFN")
        s = select(self.contract,e,self.rows(e,{"D1_C48_T0.125":[0,6]}))
        self.assertEqual(s["case"],"CAFN")
        lock = lock_forecasts(self.contract,s,self.future(
            s,{"D1_C48_T0.125":[1,2,3,4,5,6]}))
        self.assertEqual(lock["arm_forecasts"]["D"]["status"],
                         "CAFN_INTERNAL_PATH_AND_PEAK_UNIDENTIFIABLE")
        bad = copy.deepcopy(e)
        bad["observations"].insert(1,{"t_min":5,"delivered":1})
        with self.assertRaisesRegex(G3Blocked,"CONSTRUCTION_MASK"):
            select(self.contract,bad,self.rows(bad))

    def test_extra_future_field_is_rejected_before_selection(self):
        e = self.evidence()
        e["future_delivered"]=[10,15,19]
        with self.assertRaisesRegex(G3Blocked,"EVIDENCE_FIELDS"):
            select(self.contract,e,self.rows(self.evidence()))

    def test_m_c100_duplicate_alias_not_extra_candidate(self):
        e = self.evidence()
        r = self.rows(e)
        r.append(copy.deepcopy(r[0]))
        r[-1]["id"] = "M_C00_C100"
        with self.assertRaisesRegex(G3Blocked,"INCOMPLETE_MANIFEST"):
            select(self.contract,e,r)

    def test_missing_candidate_or_duplicate_fails_closed(self):
        e = self.evidence()
        rows = self.rows(e)
        with self.assertRaisesRegex(G3Blocked,"INCOMPLETE_MANIFEST"):
            select(self.contract,e,rows[:-1])
        rows[-1] = copy.deepcopy(rows[0])
        with self.assertRaisesRegex(G3Blocked,"DUPLICATE"):
            select(self.contract,e,rows)

    def test_g2_unverified_receipt_and_over_balance_fail(self):
        e=self.evidence()
        rows=self.rows(e, {"M_C00_C72":[0,1,2,3,4,5,6]})
        bad = copy.deepcopy(rows)
        next(x for x in bad if x["id"]=="M_C00_C72")["g2_receipt_sha256"]=None
        with self.assertRaisesRegex(G3Blocked,"MISSING_NATIVE_G2"):
            select(self.contract,e,bad)
        bad=copy.deepcopy(rows)
        next(x for x in bad if x["id"]=="M_C00_C72")["balance_max_abs"]=MASS+1e-5
        with self.assertRaisesRegex(G3Blocked,"UNVERIFIED_MATERIAL"):
            select(self.contract,e,bad)

    def test_evidence_hash_binding_prevents_cross_case_reuse(self):
        e=self.evidence()
        rows=self.rows(e)
        rows[0]["candidate_evidence_sha256"]="sha256:"+"f"*64
        with self.assertRaisesRegex(G3Blocked,"EVIDENCE_HASH_MISMATCH"):
            select(self.contract,e,rows)

    def test_evaluation_forecast_cannot_change_selection_or_source(self):
        e=self.evidence()
        s=select(self.contract,e,self.rows(e,{"D1_C48_T0.125":[0,1,2,3,4,5,6]}))
        f=self.future(s,{"D1_C48_T0.125":[1,2,3,4,5,6]})
        lock=lock_forecasts(self.contract,s,f)
        self.assertEqual(lock["evaluation_truth_included"],False)
        self.assertFalse(lock["external_reveal_authorized"])
        self.assertEqual(lock["status"],
                         "LOCK_CONTENT_PREPARED_NEEDS_EXTERNAL_IMMUTABLE_CUSTODY")
        tamper=copy.deepcopy(s)
        tamper["decision"]["D"]["winners"]=[]
        with self.assertRaisesRegex(G3Blocked,"SELECTION_TAMPERED"):
            lock_forecasts(self.contract,tamper,f)
        tamper=copy.deepcopy(f)
        tamper["source_snapshot_sha256"]="sha256:"+"d"*64
        with self.assertRaisesRegex(G3Blocked,"LOCK_PROVENANCE"):
            lock_forecasts(self.contract,s,tamper)

    def test_future_truth_leak_and_unknown_extra_forecast_rejected(self):
        e=self.evidence()
        s=select(self.contract,e,self.rows(e,{"B_NATIVE_1":[0,1,2,3,4,5,6]}))
        f=self.future(s,{"B_NATIVE_1":[1,2,3,4,5,6]})
        f["actual_evaluation_delivered"]=[0,1]
        with self.assertRaisesRegex(G3Blocked,"LOCK_INPUT_FIELDS"):
            lock_forecasts(self.contract,s,f)
        f=self.future(s,{"B_NATIVE_1":[1,2,3,4,5,6]})
        f["forecast_by_candidate"]["M_C00_C72"]=[1,2,3,4,5,6]
        with self.assertRaisesRegex(G3Blocked,"FORECAST_MISSING_OR_EXTRANEOUS"):
            lock_forecasts(self.contract,s,f)

    def test_physical_bounds_in_construction_and_future(self):
        e=self.evidence()
        rows=self.rows(e,{"D1_C48_T0.125":[0,100,200,300,400,500,600]})
        with self.assertRaisesRegex(G3Blocked,"NONPHYSICAL"):
            select(self.contract,e,rows)
        s=select(self.contract,e,self.rows(e,{"D1_C48_T0.125":[0,1,2,3,4,5,6]}))
        bad=self.future(s,{"D1_C48_T0.125":[1,2,3,4,5,999]})
        with self.assertRaisesRegex(G3Blocked,"FUTURE_PREDICTION_OUTSIDE"):
            lock_forecasts(self.contract,s,bad)

    def test_policy_fails_closed_if_original_contract_changes(self):
        c=copy.deepcopy(self.contract)
        c["methods"]["M"]["frozen_response_time_hours"]["preparation"]=1
        with self.assertRaisesRegex(ValueError,"NO_CERTIFICATE"):
            plan(c)
        c=copy.deepcopy(self.contract)
        c["methods"]["D"]["loss_variants"]=[False,True]
        with self.assertRaisesRegex(G3Blocked,"INVENTORY_CHANGED"):
            plan(c)


if __name__ == "__main__":
    unittest.main()
