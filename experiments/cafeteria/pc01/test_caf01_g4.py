#!/usr/bin/env python3
"""G4 tests use invented public construction, never actual CAF-01 worlds."""
import copy
import json
import math
import hashlib
import tempfile
import unittest
from pathlib import Path

from caf01_g3 import SCHEMA as G3_SCHEMA, digest, inventory, select, lock_forecasts
from caf01_g4 import (CONTRACT, SCHEMA, G4Blocked, TIMES, forecast,
                      audit_arrival_sidecar, prepare_preholdout_package,
                      score_six_delivered_values, emit_custody_candidate)


class TestG4ConstructionOnly(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def evidence(self, delivered=None, case="CAF01"):
        if delivered is None:
            delivered = [0, 0, 1, 3, 6, 8, 10] if case == "CAF01" else [0, 10]
        times = [0, 5, 10, 15, 20, 30, 40] if case == "CAF01" else [0, 40]
        return {"schema": G3_SCHEMA, "case": case,
                "source_snapshot_sha256": "sha256:"+"a"*64,
                "public_pulse": {"kind":"pulse","rate_per_minute":1.2,
                                 "duration_minutes":20},
                "observations": [{"t_min": t,"delivered": v}
                                 for t,v in zip(times,delivered)]}

    def rows(self, evidence, ready=None):
        ready = ready or {}
        result=[]
        for item in inventory(self.contract):
            pred=ready.get(item["id"])
            ok=pred is not None
            result.append({
                "id":item["id"],
                "gates": {"G0":"PASS" if ok else "PENDING",
                          "G1":"PASS" if ok else "PENDING",
                          "G2":"PASS" if ok else "PENDING"},
                "construction_delivered":pred,
                "native_sha256":("sha256:"+"b"*64) if ok else None,
                "g2_receipt_sha256":("sha256:"+"c"*64) if ok else None,
                "rk4_receipt_sha256":None,
                "balance_max_abs":0.001 if ok else None,
                "rk4_native_max_abs_delta":None,
                "block_reason":None if ok else "AWAITING_NATIVE_G2",
                "candidate_evidence_sha256":digest(evidence),
            })
        return result

    def g3_lock(self, evidence, ready=None):
        selected=select(self.contract,evidence,self.rows(evidence,ready))
        future={key:[1,2,3,4,5,6] for key in selected["decision"]["M"]["winners"]}
        if evidence["case"] == "CAFN":
            future={}
        submission={"schema":G3_SCHEMA,
                    "selection_sha256":selected["selection_sha256"],
                    "source_snapshot_sha256":selected["source_snapshot_sha256"],
                    "evaluation_pulse":{"kind":"pulse","rate_per_minute":1.5,
                                        "duration_minutes":20},
                    "forecast_by_candidate":future,"native_g2_checks":{}}
        return selected,lock_forecasts(self.contract,selected,submission)

    def test_REF_CAF_calibration_exact_three_eligible_windows_and_median(self):
        e=self.evidence()
        x=forecast(e,self.contract)
        m=x["references"]["REF_CAF"]
        self.assertEqual(m["status"],
                         "READY_CONDITIONAL_EMPIRICAL_RATE_NOT_PHYSICAL_CAPACITY")
        self.assertEqual([(z["start_min"],z["end_min"]) for z in m["eligible_intervals"]],
                         [(5,10),(10,15),(15,20)])
        self.assertAlmostEqual(m["effective_rate_orders_per_min"],0.4)
        self.assertEqual(m["predicted_delivered"],[2,4,6,8,12,16])
        self.assertEqual(len(m["predicted_pending_derived"]),6)
        self.assertAlmostEqual(m["predicted_pending_derived"][0],5.5)
        self.assertTrue(x["actual_arrivals_sidecar_used_in_fit"] is False)
        self.assertEqual(x["independent_new_world_runs"],0)

    def test_REF_SCALE_preset_1_25_and_evaluation_arrival_clip(self):
        e=self.evidence()
        m=forecast(e,self.contract)["references"]["REF_SCALE"]
        self.assertEqual(m["status"],"READY_PRESCRIBED_INPUT_RATIO_ONLY")
        self.assertEqual(m["predicted_delivered"],[0,1.25,3.75,7.5,10,12.5])
        self.assertEqual(m["predicted_pending_derived"][-1],17.5)
        self.assertEqual(m["rate_ratio"],1.25)
        e2=self.evidence([0,6,12,18,24,24,24])
        x2=forecast(e2,self.contract)
        self.assertEqual(x2["references"]["REF_SCALE"]["predicted_delivered"],
                         [7.5,15,22.5,30,30,30])

    def test_REF_CAF_abstains_if_saturation_proxy_fails(self):
        e=self.evidence([0,6,12,18,24,24,24])
        x=forecast(e,self.contract)
        self.assertEqual(x["references"]["REF_CAF"]["status"],
                         "REF_CAPACITY_NOT_IDENTIFIABLE")
        self.assertEqual(x["references"]["REF_CAF"]["predicted_delivered"],None)
        self.assertEqual(x["references"]["REF_SCALE"]["status"],
                         "READY_PRESCRIBED_INPUT_RATIO_ONLY")

    def test_REF_CAF_abstains_with_exactly_one_eligible_interval(self):
        x=forecast(self.evidence([0,4,11,16,20,22,22]),self.contract)
        m=x["references"]["REF_CAF"]
        self.assertEqual(len(m["eligible_intervals"]),1)
        self.assertEqual(m["status"],"REF_CAPACITY_NOT_IDENTIFIABLE")

    def test_REF_CAF_zero_throughput_is_valid_conditional_rate_not_unidentified(self):
        m=forecast(self.evidence([0,0,0,0,0,0,0]),self.contract)["references"]["REF_CAF"]
        self.assertEqual(m["effective_rate_orders_per_min"],0)
        self.assertEqual(m["predicted_delivered"],[0]*6)

    def test_CAFN_both_refs_abstain_without_inventing_internal_curve(self):
        e=self.evidence(case="CAFN")
        x=forecast(e,self.contract)
        self.assertEqual(x["references"]["REF_CAF"]["status"],"REF_CAPACITY_NOT_IDENTIFIABLE")
        self.assertEqual(x["references"]["REF_SCALE"]["status"],
                         "REF_SCALE_INTERMEDIATE_DATA_NOT_AVAILABLE")
        self.assertEqual(x["references"]["REF_CAF"]["predicted_delivered"],None)
        self.assertEqual(x["references"]["REF_SCALE"]["predicted_delivered"],None)
        self.assertFalse(x["CAFN_diagnostic"]["peak_time_identifiable"])
        self.assertEqual(x["CAFN_diagnostic"]["terminal_pending_proxy_orders"],14)

    def test_rejects_false_discrete_measurement_capacity_and_future_injection(self):
        e=self.evidence([0,1,2,3,4,5,25])
        with self.assertRaisesRegex(G4Blocked,"MORE_DELIVERIES_THAN_PUBLIC_ARRIVALS"):
            forecast(e,self.contract)
        e=self.evidence()
        e["evaluation_delivered"]=[4,8,10]
        with self.assertRaisesRegex(G4Blocked,"COMMON_PUBLIC_CONSTRUCTION_INVALID"):
            forecast(e,self.contract)

    def test_no_sidecar_can_privilege_reference_fit(self):
        e=self.evidence()
        base=forecast(e,self.contract)
        obs=[]
        for row,acc in zip(e["observations"],[0,6,12,18,24,24,24]):
            obs.append({"t_min":row["t_min"],"accepted_cum_orders":acc,
                        "pending_orders":acc-row["delivered"]})
        sidecar={"schema":SCHEMA, "case":"CAF01",
                 "source_snapshot_sha256":e["source_snapshot_sha256"],
                 "observations":obs}
        audit=audit_arrival_sidecar(e,sidecar,self.contract)
        self.assertEqual(audit["status"],"PUBLIC_SIDECAR_AGGREGATE_BALANCE_AUDIT_ONLY")
        self.assertFalse(audit["used_to_fit_REF_CAF_or_REF_SCALE"])
        self.assertFalse(audit["physical_internal_stocks_independently_verified"])
        self.assertEqual(base,forecast(e,self.contract))
        changed=copy.deepcopy(sidecar)
        changed["observations"][1]["accepted_cum_orders"]=7
        changed["observations"][1]["pending_orders"]+=1
        audit_arrival_sidecar(e,changed,self.contract)
        self.assertEqual(base,forecast(e,self.contract))
        bad=copy.deepcopy(sidecar)
        bad["observations"][3]["pending_orders"]+=1
        with self.assertRaisesRegex(G4Blocked,"SIDECAR_ROW|MATERIAL_SNAPSHOT"):
            audit_arrival_sidecar(e,bad,self.contract)
        bad=copy.deepcopy(sidecar)
        bad["observations"][-1]["accepted_cum_orders"]=25
        bad["observations"][-1]["pending_orders"]+=1
        with self.assertRaisesRegex(G4Blocked,"FINAL_ARRIVAL_COUNT"):
            audit_arrival_sidecar(e,bad,self.contract)

    def test_bundle_binds_g3_and_both_refs_for_CAF01_without_truth(self):
        e=self.evidence()
        s,g3=self.g3_lock(e, {"M_C00_C72":[0,0,1,3,6,8,10]})
        x=prepare_preholdout_package(self.contract,e,s,g3)
        self.assertEqual(x["status"],"PREHOLDOUT_PACKAGE_READY_AWAITING_EXTERNAL_CUSTODY")
        self.assertEqual(x["g3_forecast_lock_sha256"],g3["forecast_lock_sha256"])
        self.assertEqual(x["selection_sha256"],s["selection_sha256"])
        self.assertEqual(x["references"]["references"]["REF_CAF"]["effective_rate_orders_per_min"],0.4)
        self.assertFalse(x["actual_evaluation_values_included"])
        self.assertFalse(x["custody"]["release_authorized"])
        self.assertIsNone(x["custody"]["external_receipt_id"])
        self.assertEqual(x["resource_consumption"]["OpenModelica_simulations"],0)
        self.assertEqual(x["resource_consumption"]["Buffalo_provider_calls"],0)
        self.assertEqual(x["preholdout_package_sha256"],
                         digest({k:v for k,v in x.items()
                                 if k!="preholdout_package_sha256"}))

    def test_bundle_CAFN_no_future_curves_and_both_refs_abstain(self):
        e=self.evidence(case="CAFN")
        s,g3=self.g3_lock(e,{"M_C00_C72":[0,10]})
        x=prepare_preholdout_package(self.contract,e,s,g3)
        self.assertEqual(x["g3_lock"]["forecast_by_candidate"],{})
        self.assertEqual(x["g3_lock"]["arm_forecasts"]["M"]["status"],
                         "CAFN_INTERNAL_PATH_AND_PEAK_UNIDENTIFIABLE")
        self.assertEqual(x["references"]["references"]["REF_SCALE"]["predicted_delivered"],None)
        self.assertFalse(x["custody"]["release_authorized"])

    def test_tampering_g3_content_or_provenance_blocks_g4_bundle(self):
        e=self.evidence()
        s,g3=self.g3_lock(e)
        bad=copy.deepcopy(g3)
        bad["arm_forecasts"]["D"]["status"]="FAKE_SUCCESS"
        with self.assertRaisesRegex(G4Blocked,"G3_CONTENT_HASH_INVALID"):
            prepare_preholdout_package(self.contract,e,s,bad)
        bad=copy.deepcopy(s)
        bad["source_snapshot_sha256"]="sha256:"+"f"*64
        with self.assertRaisesRegex(G4Blocked,"G3_CONTENT_HASH_INVALID"):
            prepare_preholdout_package(self.contract,e,bad,g3)
        bad=copy.deepcopy(g3)
        bad["external_reveal_authorized"]=True
        bad["forecast_lock_sha256"]=digest({k:v for k,v in bad.items()
                                           if k!="forecast_lock_sha256"})
        with self.assertRaisesRegex(G4Blocked,"G3_PROVENANCE_OR_REVEAL_GUARD"):
            prepare_preholdout_package(self.contract,e,s,bad)


    def test_rubric_exactly_six_cumulative_deliveries_primary_and_secondary(self):
        observed=[1,2,3,4,5,6]
        pred=[1,2,2,4,4,6]
        report=score_six_delivered_values(pred,observed)
        self.assertAlmostEqual(report["MAE_delivered_orders"],2/6)
        self.assertAlmostEqual(report["RMSE_delivered_orders"],math.sqrt(2/6))
        self.assertEqual(report["observation_count"],6)
        self.assertFalse(report["pending_independent_evidence"])

    def test_rubric_bad_future_shape_or_physical_truth_rejected(self):
        for p,y in [
            ([0]*5,[0]*6),
            ([0]*6,[0,0,0,0,0,31]),
            ([0]*6,[0,2,1,3,4,5]),
            ([float("nan")]*6,[0]*6),
            ([0]*6,[0,0,0,0,0,True]),
        ]:
            with self.subTest(p=p,y=y),self.assertRaises(G4Blocked):
                score_six_delivered_values(p,y)

    def test_byte_identical_custody_package_not_auto_published(self):
        e=self.evidence()
        selection,g3=self.g3_lock(e, {"M_C00_C72":[0,0,1,3,6,8,10]})
        bundle=prepare_preholdout_package(self.contract,e,selection,g3)
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/"future-custody"
            record=emit_custody_candidate(bundle,folder)
            file=folder/"preholdout-package.json"
            content=file.read_bytes()
            self.assertTrue(content.endswith(b"\\n"))
            self.assertEqual(json.loads(content),bundle)
            self.assertEqual("sha256:"+hashlib.sha256(content).hexdigest(),
                             record["complete_file_sha256"])
            self.assertEqual(record["internal_content_sha256"],
                             bundle["preholdout_package_sha256"])
            self.assertEqual((folder/"preholdout-package.sha256").read_text(),
                             hashlib.sha256(content).hexdigest()+
                             "  preholdout-package.json\\n")
            self.assertIsNone(record["external_witness_receipt"])
            self.assertFalse(record["evaluation_release_authorized"])
            with self.assertRaisesRegex(G4Blocked,"OUTPUT_ALREADY_EXISTS"):
                emit_custody_candidate(bundle,folder)

    def test_custody_emission_refuses_tampered_or_released_manifest(self):
        e=self.evidence()
        selection,g3=self.g3_lock(e)
        bundle=prepare_preholdout_package(self.contract,e,selection,g3)
        bad=copy.deepcopy(bundle)
        bad["custody"]["release_authorized"]=True
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(G4Blocked,"PACKAGE_TAMPERED_OR_ALREADY_RELEASED"):
                emit_custody_candidate(bad,Path(tmp)/"should-not-exist")
            self.assertFalse((Path(tmp)/"should-not-exist").exists())

    def test_contract_drift_blocks_reference_generation(self):
        e=self.evidence()
        c=copy.deepcopy(self.contract)
        c["REF_SCALE"]["rate_ratio"]=1.2
        with self.assertRaisesRegex(G4Blocked,"REFERENCE_POLICY_CHANGED"):
            forecast(e,c)
        c=copy.deepcopy(self.contract)
        c["metrics"]["primary"]=["RMSE_delivered_orders"]
        with self.assertRaisesRegex(G4Blocked,"SCORE_POLICY_CHANGED"):
            forecast(e,c)


if __name__ == "__main__":
    unittest.main()
