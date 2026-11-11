#!/usr/bin/env python3
"""CAF02 native G2 post-only receipts from exactly 15 bounded OMC attempts.

No OMC invocation is possible from this module. The separate one-shot manual
workflow writes .attempt BEFORE each Docker/OMC command, followed by exit code,
native console, source and actual CSV. Missing CSV/log/exit => FAIL, never
silent substitution by Heun or RK4. All 15 cases are retained on failure.

A local native artifact receipt is NOT independent custody, does NOT identify
the world, and cannot authenticate the CI system by itself.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
from pathlib import Path

import caf02_d_k0k1k2_adapter as d
import caf02_g2_native_modelica_sources as sources

SCHEMA="igc-caf02-native-g2-attempt-receipts/0.1"
MAX_BALANCE_ERROR=.02
MAX_NEGATIVE_STATE_ERROR=.02


def need(ok,reason):
    if not ok:raise ValueError(reason)


def audit_csv(path,row):
    """Validate physical stocks and compare continuous native time-series."""
    with Path(path).open(encoding="utf-8",newline="") as fp:
        reader=csv.DictReader(fp)
        cols=set(reader.fieldnames or [])
        needed={"time","accepted","delivered",*row["expected_stock_columns"]}
        need(needed<=cols,"G2_NATIVE_CSV_MISSING_MATERIAL_COLUMNS")
        trace=list(reader)
    need(len(trace)>=7,"G2_NATIVE_CSV_INSUFFICIENT_ROWS")
    rate=row["pulse_rate_orders_per_minute"]
    duration=20.0
    stocks=row["expected_stock_columns"]
    samples=[]
    last_t=-1.0
    last_delivered=0.0
    peak_balance=0.0
    for obj in trace:
        values={key:float(obj[key]) for key in needed}
        need(all(math.isfinite(x) for x in values.values()),
             "G2_NATIVE_CSV_NONFINITE")
        t=values["time"]
        delivered=values["delivered"]
        accepted=values["accepted"]
        held=[values[n] for n in stocks]
        expected_accepted=rate*min(max(0.0,t*60),duration)
        material=accepted-delivered-sum(held)
        peak_balance=max(peak_balance,abs(material),
                         abs(accepted-expected_accepted))
        need(t>=last_t-1e-9 and
             -1e-9<=t<=2/3+1e-8,
             "G2_NATIVE_CSV_TIME_NOT_MONOTONE_OR_OUTSIDE_HORIZON")
        need(delivered>=last_delivered-MAX_NEGATIVE_STATE_ERROR,
             "G2_NATIVE_DELIVERY_NOT_MONOTONE")
        need(min(accepted,delivered,*held)>=-MAX_NEGATIVE_STATE_ERROR,
             "G2_NATIVE_NEGATIVE_MATERIAL")
        need(peak_balance<=MAX_BALANCE_ERROR,
             "G2_NATIVE_MASS_OR_PULSE_BALANCE_FAILURE")
        samples.append((t,delivered))
        last_delivered=delivered
        last_t=t
    need(abs(samples[0][0])<1e-8
         and abs(samples[-1][0]-2/3)<1e-8,
         "G2_NATIVE_CSV_MISSING_RESET_OR_FINAL_TIME")
    found=[]
    for desired in row["observed_times_hours"]:
        matches=[v for t,v in samples if abs(t-desired)<1e-7]
        need(matches,"G2_NATIVE_CSV_MISSING_PREDECLARED_SAMPLE_TIME")
        # Event steps may duplicate a timestamp. With the declared input
        # pulse, delivered is continuous; reject contradictory duplicates.
        need(max(matches)-min(matches)<.01,
             "G2_NATIVE_AMBIGUOUS_EVENT_TIME_DELIVERED")
        found.append(matches[-1])
    report=sources.g2.evaluate_offline_submitted_trace(
        {"public_probe_rate_per_minute":rate,
         "public_probe_duration_minutes":duration,
         "reference_curve_from_surrogate_not_OMC":
             row["reference_curve_from_surrogate_not_OMC"]},
        row["observed_times_hours"],found)
    need(report["numeric_trace_within_proposed_tolerance"],
         "G2_NATIVE_VS_EXISTING_SURROGATE_DELTA_OVER_0_05")
    return {
        "native_rows":len(trace),
        "native_csv_sample_times_hours":row["observed_times_hours"],
        "native_delivered_at_six_predeclared_times":found,
        "surrogate_delivered_at_six_predeclared_times":
            row["reference_curve_from_surrogate_not_OMC"],
        "native_vs_surrogate_max_abs_delta_orders":
            report["max_abs_difference_orders"],
        "mass_conservation_max_abs_orders":peak_balance,
        "numeric_criterion":"MAX_ABS_DELTA_0_05_ORDERS",
        "physical_balance_max_abs_allowed_orders":MAX_BALANCE_ERROR,
    }


def verify(folder):
    """A report is always written and all 15 cases accounted for, PASS/FAIL."""
    folder=Path(folder).resolve()
    manifest_path=folder/"G2_SOURCE_MANIFEST.json"
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    policy=json.loads(d.POLICY.read_text(encoding="utf-8"))
    expected,_=sources.compile_manifest(policy,folder)
    need(manifest==expected,"G2_MANIFEST_UNAUTHORIZED_DRIFT")
    counts={"M":0,"D":0}
    result=[]
    for row in manifest["source_rows"]:
        name=row["modelica_class"]
        counts[row["arm"]]+=1
        item={
            "id":row["id"],"arm":row["arm"],
            "structure":row["structure"],
            "public_probe":row["public_probe"],
            "status":"FAIL",
            "reason_code":None,
            "native_invocation_marker_present":False,
            "native_solver_exit_code":None,
            "native_source_sha256":row["source_sha256"],
            "native_script_sha256":row["mos_sha256"],
            "native_csv_sha256":None,
            "native_solver_console_sha256":None,
        }
        attempt=folder/(name+".attempt")
        code=folder/(name+".exit_code")
        console=folder/(name+".console.txt")
        rawcsv=folder/row["expected_csv_file"]
        try:
            need(sources.checksum((folder/row["source_file"]).read_bytes())==
                 row["source_sha256"],"G2_SOURCE_BYTES_TAMPERED")
            need(sources.checksum((folder/row["mos_file"]).read_bytes())==
                 row["mos_sha256"],"G2_SCRIPT_BYTES_TAMPERED")
            need(attempt.is_file() and
                 attempt.read_bytes()==b"INVOCATION_STARTED\n",
                 "G2_INVOCATION_NOT_RECORDED")
            item["native_invocation_marker_present"]=True
            need(code.is_file(),"G2_NATIVE_EXIT_CODE_MISSING")
            exitcode=code.read_text(encoding="ascii").strip()
            item["native_solver_exit_code"]=exitcode
            need(exitcode=="0","G2_NATIVE_NONZERO_SOLVER_EXIT")
            need(console.is_file(),"G2_NATIVE_CONSOLE_MISSING")
            log=console.read_text(encoding="utf-8")
            item["native_solver_console_sha256"]=sources.checksum(
                console.read_bytes())
            need("record SimulationResult" in log
                 and "resultFile" in log
                 and not any(x in log for x in
                     ("Error:","Simulation Failed","Failed to load",
                      "Error occurred","Class not found")),
                 "G2_NATIVE_CONSOLE_NOT_SUCCESSFUL_SIMULATION")
            need(rawcsv.is_file(),"G2_NATIVE_CSV_MISSING")
            item["native_csv_sha256"]=sources.checksum(rawcsv.read_bytes())
            item.update(audit_csv(rawcsv,row))
            item["status"]="PASS_NATIVE_ARTIFACT_LOCAL_NOT_EXTERNAL_G5"
            item["reason_code"]=None
        except (OSError,UnicodeError,KeyError,TypeError,ValueError) as exc:
            code=str(exc)
            item["reason_code"]=(code if code.startswith("G2_")
                                 else "G2_NATIVE_ARTIFACT_VERIFICATION_EXCEPTION")
        (folder/(name+".receipt.json")).write_bytes(sources.canonical(item))
        result.append(item)
    need(counts=={"M":12,"D":3},"G2_VERIFY_WRONG_ARM_BUDGET")
    done=sum(x["native_invocation_marker_present"] for x in result)
    passed=sum(x["status"].startswith("PASS") for x in result)
    outcome={
        "schema":SCHEMA,
        "status":("ALL_FIFTEEN_NATIVE_ARTIFACT_G2_PASS_NOT_EXTERNAL_CUSTODY"
                  if passed==15 and done==15
                  else "PARTIAL_OR_FAILED_NATIVE_ARTIFACT_G2"),
        "source_manifest_sha256":sources.checksum(manifest_path.read_bytes()),
        "native_model_attempts_marked":done,
        "native_pass_count":passed,
        "native_fail_count":15-passed,
        "native_budget_max":15,
        "arm_native_attempt_markers":{
            arm:sum(x["arm"]==arm and x["native_invocation_marker_present"]
                    for x in result) for arm in ("M","D")},
        "OpenModelica_version_image_tag_requested":sources.IMAGE_TAG,
        "image_resolved_identity_file_present":
            (folder/"IMAGE_DIGEST.txt").is_file(),
        "private_DES_runs":0,
        "K2_truth_seen":False,
        "G5_G4a_G4b_external_witness_verified":False,
        "native_identity_without_external_attestation_is_limited":True,
        "attempts":result,
    }
    (folder/"G2_NATIVE_VERIFICATION.json").write_bytes(sources.canonical(outcome))
    return outcome


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("action",choices=("verify",))
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    v=verify(args.out)
    print(json.dumps({
        "status":v["status"],"attempts":v["native_model_attempts_marked"],
        "passed":v["native_pass_count"],"failed":v["native_fail_count"]},
        sort_keys=True))
    if v["status"]!="ALL_FIFTEEN_NATIVE_ARTIFACT_G2_PASS_NOT_EXTERNAL_CUSTODY":
        raise SystemExit(1)


if __name__=="__main__":
    main()
