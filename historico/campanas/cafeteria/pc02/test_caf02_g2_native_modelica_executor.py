#!/usr/bin/env python3
"""G2 source and native-artifact verifier tests: NO OMC or DES invoked."""
import csv
import json
import tempfile
import unittest
from pathlib import Path

import caf02_d_k0k1k2_adapter as d
import caf02_g2_native_correspondence_plan as plan
import caf02_g2_native_modelica_sources as native
import caf02_g2_native_executor as runner


class ModelicaSources(unittest.TestCase):
    def setUp(self):
        self.policy=json.loads(d.POLICY.read_text(encoding="utf-8"))

    def test_all_15_sources_have_existing_graphs_and_capacity_min(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)/"native"
            manifest=native.prepare(root)
            self.assertEqual((manifest["M_cases"],manifest["D_cases"]),(12,3))
            self.assertEqual(manifest["OMC_attempts_executed"],0)
            self.assertEqual(manifest["private_DES_runs"],0)
            self.assertFalse(manifest["K2_truth_seen"])
            self.assertEqual(len(list(root.glob("*.mo"))),15)
            self.assertEqual(len(list(root.glob("*.mos"))),15)
            self.assertEqual(len(set(x["modelica_class"] for x in
                                     manifest["source_rows"])),15)
            for row in manifest["source_rows"]:
                src=(root/row["source_file"]).read_text(encoding="utf-8")
                mos=(root/row["mos_file"]).read_text(encoding="utf-8")
                self.assertEqual(native.checksum(src),row["source_sha256"])
                self.assertEqual(native.checksum(mos),row["mos_sha256"])
                self.assertEqual(src.count("der(delivered) ="),1)
                self.assertEqual(src.count("der(accepted) = inputRate;"),1)
                self.assertEqual(src.count("if time < pulseDurationH"),1)
                self.assertEqual(src.count("min(capacity"),len(
                    row["expected_stock_columns"]))
                self.assertEqual(src.count("Real s"),len(
                    row["expected_stock_columns"]))
                self.assertEqual(src.count("Real f"),len(
                    row["expected_stock_columns"]))
                self.assertEqual(mos.count("simulate("),1)
                self.assertEqual(mos.count("checkModel("),1)
                self.assertEqual(mos.count("loadFile("),1)
                self.assertEqual(mos.count("cd("),1)
                self.assertIn(str(root),mos)
                self.assertNotIn("K2_truth",src)
                self.assertNotIn("private_des",src)
                self.assertIn('outputFormat="csv"',mos)
            with self.assertRaisesRegex(ValueError,"OUTPUT_ALREADY_EXISTS"):
                native.prepare(root)

    def test_plan_case_graph_is_not_replaced_by_D_grammar_in_M(self):
        plan_rows=plan.plan(self.policy)["cases"]
        for case in plan_rows:
            src=native.modelica_source(case)
            if case["structure"]=="C01":
                self.assertIn("capacity3H = 100",src)
                self.assertIn("der(s3) = f2 - f3;",src)
            elif case["structure"]=="C00":
                self.assertNotIn("der(s3)",src)
                self.assertIn("der(s2) = f1 - f2;",src)
            elif case["arm"]=="D":
                for n in range(1,case["stocks"]+1):
                    self.assertIn(f"response{n}H",src)
                self.assertNotIn("lossRate",src)
            self.assertIn("min(capacity1H",src)

    def test_K1_stress_pulses_in_native_units_not_minutes(self):
        cases=plan.plan(self.policy)["cases"]
        d1=next(x for x in cases if x["id"]=="D_1_72_1")
        src=native.modelica_source(d1)
        self.assertIn("pulseRateH = 90",src)
        self.assertIn("capacity1H = 72",src)
        self.assertIn("response1H = 0.016666666666666666",src)
        self.assertIn("pulseDurationH = 0.33333333333333331",src)
        c01=next(x for x in cases if x["structure"]=="C01"
                 and x["public_probe"]=="K1_C")
        raw=native.modelica_source(c01)
        self.assertIn("pulseRateH = 108",raw)

    def test_source_plan_rejects_tamper_or_unauthorized_topologies(self):
        row=plan.plan(self.policy)["cases"][0]
        altered={**row,"structure":"C999"}
        with self.assertRaisesRegex(ValueError,"UNREGISTERED_M"):
            native.modelica_source(altered)
        altered={**row,"public_probe_duration_minutes":25}
        with self.assertRaisesRegex(ValueError,"UNEXPECTED_STRUCTURE_OR_PULSE"):
            native.modelica_source(altered)

    def test_csv_math_match_cannot_claim_native_execution(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)/"native"
            manifest=native.prepare(root)
            row=next(x for x in manifest["source_rows"] if x["arm"]=="D")
            path=root/row["expected_csv_file"]
            mins=[0,*plan.TIMES]
            values=[0,*row["reference_curve_from_surrogate_not_OMC"]]
            with path.open("w",newline="",encoding="utf-8") as f:
                writer=csv.writer(f)
                writer.writerow(["time","accepted","delivered",
                                 *row["expected_stock_columns"]])
                for minute,delivery in zip(mins,values):
                    accepted=row["pulse_rate_orders_per_minute"]*min(minute,20)
                    held=[accepted-delivery]+[0]*(
                        len(row["expected_stock_columns"])-1)
                    writer.writerow([minute/60,accepted,delivery,*held])
            # These are FAKE native CSV rows, assembled from the RK4 output.
            numeric=runner.audit_csv(path,row)
            self.assertLess(numeric[
                "native_vs_surrogate_max_abs_delta_orders"],1e-8)
            result=runner.verify(root)
            self.assertEqual(result["native_pass_count"],0)
            self.assertEqual(result["native_model_attempts_marked"],0)
            self.assertEqual(result["native_fail_count"],15)
            self.assertEqual(result["status"],
                "PARTIAL_OR_FAILED_NATIVE_ARTIFACT_G2")
            self.assertFalse(result[
                "G5_G4a_G4b_external_witness_verified"])

    def test_bad_csv_mass_and_bad_csv_capacity_removed_are_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)/"native"
            manifest=native.prepare(root)
            row=next(x for x in manifest["source_rows"] if x["id"]=="D_1_72_1")
            path=root/"synthetic.csv"
            row_times=[0,*plan.TIMES]
            arrivals=[row["pulse_rate_orders_per_minute"]*min(t,20)
                      for t in row_times]
            deliveries=[0,*row["reference_curve_from_surrogate_not_OMC"]]
            with path.open("w",newline="") as fp:
                w=csv.writer(fp);w.writerow(["time","accepted","delivered","s1"])
                for t,a,delivery in zip(row_times,arrivals,deliveries):
                    w.writerow([t/60,a,delivery,a-delivery])
            self.assertIsNotNone(runner.audit_csv(path,row))
            with path.open("w",newline="") as fp:
                w=csv.writer(fp);w.writerow(["time","accepted","delivered","s1"])
                for idx,(t,a,delivery) in enumerate(zip(row_times,arrivals,
                                                          deliveries)):
                    w.writerow([t/60,a,delivery,a-delivery+(1 if idx==4 else 0)])
            with self.assertRaisesRegex(ValueError,"MASS_OR_PULSE_BALANCE"):
                runner.audit_csv(path,row)
            # A CSV copied from a high-capacity mathematical version must not
            # pass the native 0.05-order discrepancy criterion.
            d1=next(x for x in plan.plan(self.policy)["cases"]
                    if x["id"]=="D_1_72_1")
            no_cap=[0,*plan.surrogate_case(
                d1,1.5,capacity_override=plan.HIGH_CAPACITY_SHADOW_PER_HOUR)]
            with path.open("w",newline="") as fp:
                w=csv.writer(fp);w.writerow(["time","accepted","delivered","s1"])
                for t,a,delivery in zip(row_times,arrivals,no_cap):
                    w.writerow([t/60,a,delivery,a-delivery])
            with self.assertRaisesRegex(ValueError,"DELTA_OVER_0_05"):
                runner.audit_csv(path,row)

    def test_verify_rejects_missing_real_attempt_even_if_fake_marker_exists(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)/"native"
            manifest=native.prepare(root)
            first=manifest["source_rows"][0]["modelica_class"]
            (root/(first+".attempt")).write_bytes(b"INVOCATION_STARTED\n")
            (root/(first+".exit_code")).write_bytes(b"0\n")
            report=runner.verify(root)
            self.assertEqual(report["native_model_attempts_marked"],1)
            self.assertEqual(report["native_pass_count"],0)
            self.assertEqual(report["attempts"][0]["reason_code"],
                             "G2_NATIVE_CONSOLE_MISSING")
            self.assertEqual(len(report["attempts"]),15)
            self.assertEqual(report["arm_native_attempt_markers"],
                             {"M":1,"D":0})

    def test_manifest_mutation_fails_before_receipt_or_executor(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)/"native"
            manifest=native.prepare(root)
            altered=json.loads((root/"G2_SOURCE_MANIFEST.json").read_text())
            altered["source_rows"][0]["cap_orders_per_hour"]=100000
            (root/"G2_SOURCE_MANIFEST.json").write_bytes(native.canonical(altered))
            with self.assertRaisesRegex(ValueError,"MANIFEST_UNAUTHORIZED_DRIFT"):
                runner.verify(root)

if __name__=="__main__":
    unittest.main()
