#!/usr/bin/env python3
"""G2 PR preflight: synthetic / mocked, zero OpenModelica or RK4 invocations."""
import csv
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from caf01_d_g2_native import (
    EVIDENCE_SHA256, PARENT_SHA256, WORLD, evaluate_csv, load_inputs,
    prepare, read_parent, require_github_one_shot, selected_rows, verify,
)
from caf01_g3 import inventory, score
from scripts.arena_d_v01 import modelica, topology
from scripts.arena_v0_contract import digest
import hashlib


def invented_parent(contract, observations):
    """Fake candidate *results* fabricated from public observations, NOT RK4."""
    rows=[]
    for entry in [x for x in inventory(contract) if x["arm"]=="D"]:
        graph=topology(int(entry["structure"][1:]),False)
        params={"capacity":entry["capacity"],"response_time":entry["tau"],"loss_time":1.0}
        native=modelica({"structure":graph,"structure_hash":digest(graph),
                         "nominal_parameters":params},
                        {"kind":"pulse","rate":72,"duration":1/3})
        sh="sha256:"+hashlib.sha256(native.encode()).hexdigest()
        curve=list(observations)
        mae,rmse=score(curve,observations,[0,5,10,15,20,30,40])
        rows.append({"id":entry["id"],"structure":entry["structure"],
                     "parameters":params,"construction_delivered":curve,
                     "mae":mae,"rmse":rmse,
                     "native_sha256":sh,"rk4_receipt_sha256":"sha256:"+"4"*64,
                     "gate":{"G0":"PASS","G1":"PASS","G2":"RK4_SCREEN"},
                     "native_G2_verified":False})
    representatives={}
    for struct in ("D1","D2","D3"):
        best=min([r for r in rows if r["structure"]==struct],
                 key=lambda r:(r["mae"],r["id"]))
        representatives[struct]={"candidate_id":best["id"],
                                 "construction_mae":best["mae"]}
    return {"candidate_rows":rows,"D_preliminary_representatives":representatives}


class TestDNativeG2(unittest.TestCase):
    def test_pinned_public_construction_not_evaluation(self):
        evidence,contract,obs=load_inputs()
        self.assertEqual(evidence["case"],"CAF01")
        self.assertEqual(evidence["source_snapshot_sha256"],WORLD)
        self.assertEqual(obs,[0,3,8,13,18,24,24])
        self.assertEqual(len([x for x in inventory(contract) if x["arm"]=="D"]),18)

    def test_refuse_unpinned_parent_without_solver(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"D_RK4_SCREEN.json"
            f.write_text('{"case":"CAF01"}')
            with self.assertRaisesRegex(ValueError,"PARENT_GITHUB_BYTES_CHANGED"):
                read_parent(f)

    def test_three_selected_original_sources_no_refit(self):
        _,contract,obs=load_inputs()
        fake=invented_parent(contract,obs)
        with tempfile.TemporaryDirectory() as d:
            output=Path(d)/"g2"
            with patch("caf01_d_g2_native.read_parent",return_value=fake):
                manifest=prepare(Path(d)/"fake-parent.json",output)
            self.assertEqual(manifest["simulation_attempts_at_prepare"],0)
            self.assertEqual(len(manifest["selected_models"]),3)
            self.assertEqual(sorted(p.name for p in output.glob("*.mos")),
                             ["D_G2_1.mos","D_G2_2.mos","D_G2_3.mos"])
            self.assertEqual(sorted(x["topology_stocks"]
                                    for x in manifest["selected_models"]),[1,2,3])
            for i in (1,2,3):
                mos=(output/f"D_G2_{i}.mos").read_text()
                self.assertEqual(mos.count("simulate("),1)
                self.assertIn('outputFormat="csv"',mos)
                self.assertIn("stopTime=(2.0/3.0)",mos)
                self.assertNotIn("1.5",mos)
            with self.assertRaisesRegex(ValueError,"OUTPUT_EXISTS"):
                with patch("caf01_d_g2_native.read_parent",return_value=fake):
                    prepare(Path(d)/"fake-parent.json",output)

    def test_representatives_frozen_and_incomplete_manifest_blocked(self):
        _,contract,obs=load_inputs()
        fake=invented_parent(contract,obs)
        selected=selected_rows(fake,contract,obs)
        self.assertEqual(len(selected),3)
        fake["D_preliminary_representatives"]["D2"]["candidate_id"]="D2_FAKE"
        with self.assertRaisesRegex(ValueError,"REPRESENTATIVE_CHANGED"):
            selected_rows(fake,contract,obs)

    def test_fake_csv_checks_mass_and_parity(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"fabricated.csv"
            fieldnames=["time","delivered","s1","lost"]
            def write(tamper=False):
                with f.open("w",newline="") as h:
                    w=csv.DictWriter(h,fieldnames=fieldnames)
                    w.writeheader()
                    for i in range(81):
                        t=i/120
                        accepted=72*min(t,1/3)
                        w.writerow({"time":t,"delivered":0,
                                    "s1": accepted+(1 if tamper else 0),"lost":0})
            write()
            data=evaluate_csv(f,1,[0]*7)
            self.assertEqual(data["status"],"PASS")
            self.assertEqual(data["rk4_native_max_abs_delta"],0)
            write(tamper=True)
            with self.assertRaisesRegex(ValueError,"BALANCE_OR_PARITY_BLOCKED"):
                evaluate_csv(f,1,[0]*7)

    def fake_prepared_with_three_solver_outputs(self, output_dir, *,
                                                invalid_mass=None,
                                                exit_failure=None,
                                                missing_attempt=None):
        """Three fabricated native CSVs. NO OMC/DES/RK4 ever invoked."""
        _, contract, observations=load_inputs()
        invented=invented_parent(contract,observations)
        with patch("caf01_d_g2_native.read_parent",return_value=invented):
            prepare(output_dir.parent/"fake_parent.json",output_dir)
        mf_path=output_dir/"preflight.json"
        mf=json.loads(mf_path.read_bytes())
        for info in mf["selected_models"]:
            info["rk4_curve"]=[0.]*7  # invented, not the real D screen results
            n=info["ordinal"]
            count=info["topology_stocks"]
            if missing_attempt!=n:
                (output_dir/f"D_G2_{n}.attempt").write_text("INVOCATION_STARTED\n")
            (output_dir/f"D_G2_{n}.exit_code").write_text(
                "2\n" if n==exit_failure else "0\n")
            (output_dir/f"D_G2_{n}.log").write_text("fictional synthetic OMC log\n")
            p=output_dir/info["expected_csv"]
            fields=["time","delivered",*[f"s{i}" for i in range(1,count+1)],"lost"]
            with p.open("w",newline="") as fp:
                writer=csv.DictWriter(fp,fieldnames=fields)
                writer.writeheader()
                for i in range(81):
                    t=i/120
                    mass=72*min(t,1/3)
                    row={"time":t,"delivered":0,"lost":0}
                    row.update({f"s{k}":(mass if k==1 else 0)
                                for k in range(1,count+1)})
                    if n==invalid_mass:
                        row["s1"]+=1
                    writer.writerow(row)
        mf_path.write_text(json.dumps(mf)+"\n")

    def test_partial_failure_keeps_two_independent_pass_receipts(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/"three"
            self.fake_prepared_with_three_solver_outputs(out,invalid_mass=2)
            result=verify(out)
            self.assertEqual(result["status"],"PARTIAL_NATIVE_G2")
            self.assertEqual(result["representatives_passed"],2)
            self.assertEqual(result["native_construction_simulations_consumed"],3)
            self.assertEqual([r["status"] for r in result["native_candidates"]],
                             ["PASS","FAIL","PASS"])
            self.assertEqual(result["native_candidates"][1]["reason_code"],
                             "D_G2_BALANCE_OR_PARITY_BLOCKED")
            self.assertTrue((out/"D_G2_VERIFIED.json").is_file())
            self.assertEqual(len(list(out.glob("D_G2_*_receipt.json"))),3)
            for i,expected in ((1,"PASS"),(2,"FAIL"),(3,"PASS")):
                receipt=json.loads((out/f"D_G2_{i}_receipt.json").read_bytes())
                self.assertEqual(receipt["status"],expected)
                self.assertEqual(receipt["id"],result["native_candidates"][i-1]["id"])
                self.assertEqual(receipt["invocation_started"],True)

    def test_failed_solver_exit_and_missing_attempt_cannot_erase_pass(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/"three"
            self.fake_prepared_with_three_solver_outputs(out,exit_failure=2,
                                                         missing_attempt=3)
            result=verify(out)
            self.assertEqual([r["status"] for r in result["native_candidates"]],
                             ["PASS","FAIL","FAIL"])
            self.assertEqual(result["native_candidates"][1]["reason_code"],
                             "D_G2_SOLVER_EXIT_NONZERO")
            self.assertEqual(result["native_candidates"][2]["reason_code"],
                             "D_G2_INVOCATION_NOT_RECORDED")
            self.assertEqual(result["native_construction_simulations_consumed"],2)
            self.assertEqual(result["native_candidates"][0]["status"],"PASS")
            self.assertEqual(len(list(out.glob("D_G2_*_receipt.json"))),3)

    def test_cli_reports_global_error_only_after_persisting_receipts(self):
        from caf01_d_g2_native import main
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/"three"
            self.fake_prepared_with_three_solver_outputs(out,invalid_mass=2)
            with patch("caf01_d_g2_native.require_github_one_shot"), \
                 patch("sys.argv",["caf01_d_g2_native.py","verify","--out",str(out)]):
                with self.assertRaises(SystemExit) as ex:
                    main()
            self.assertEqual(ex.exception.code,1)
            self.assertTrue((out/"D_G2_VERIFIED.json").is_file())
            self.assertEqual(len(list(out.glob("D_G2_*_receipt.json"))),3)
            self.assertEqual(json.loads((out/"D_G2_1_receipt.json").read_text())["status"],
                             "PASS")
            self.assertEqual(json.loads((out/"D_G2_3_receipt.json").read_text())["status"],
                             "PASS")

    def test_restrict_to_first_manual_main_run(self):
        good={"GITHUB_ACTIONS":"true","GITHUB_REF":"refs/heads/main",
              "GITHUB_EVENT_NAME":"workflow_dispatch",
              "GITHUB_REPOSITORY":"yudocyudoc/IGC",
              "GITHUB_RUN_NUMBER":"1","GITHUB_RUN_ATTEMPT":"1"}
        with patch.dict(os.environ,good,clear=True):
            require_github_one_shot()
        for key,value in [("GITHUB_REF","refs/heads/feature"),
                          ("GITHUB_RUN_NUMBER","2"),
                          ("GITHUB_RUN_ATTEMPT","2"),
                          ("GITHUB_EVENT_NAME","pull_request"),
                          ("GITHUB_REPOSITORY","other/IGC")]:
            with self.subTest(key=key):
                with patch.dict(os.environ,{**good,key:value},clear=True):
                    with self.assertRaisesRegex(ValueError,"FIRST_MAIN_GITHUB"):
                        require_github_one_shot()


if __name__=="__main__":
    unittest.main()
