#!/usr/bin/env python3
"""CAF-02 G2: deterministically generate 15 executable Modelica sources.

NO native execution, K0/K1 experimental observation, DES or K2 truth here.
The selected samples and parameter tuples come exclusively from the fixed
CAF02 G2 0.2 public-pulse plan. Sources are plain stock-flow ODEs, not
disguised surrogates, and use HOURS consistently (orders/hour, minutes/60).
M C01 adds a 100/h transit stage; D uses 1..3 equally parameterized stocks.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re

import caf02_d_k0k1k2_adapter as d
import caf02_g2_native_correspondence_plan as g2

SCHEMA="igc-caf02-g2-modelica-source-manifest/0.1"
NAME=re.compile(r"^M_(?:C00|C01)_\d{2}$|^D_[123]_(?:72|100)_(?:1|3|6)$")
STOP_HOURS=2.0/3.0
INTERVALS=800
SOLVER="dassl"
SOLVER_TOLERANCE=1e-9
IMAGE_TAG="openmodelica/openmodelica:v1.26.5-minimal"


def need(ok,why):
    if not ok:raise ValueError(why)


def canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(",",":"),
                       ensure_ascii=False,allow_nan=False)+"\n").encode()


def checksum(source):
    if isinstance(source,str):source=source.encode("utf-8")
    return "sha256:"+sha256(source).hexdigest()


def fmt(n):
    need(type(n) in (int,float) and n>0,"MODEL_BAD_NUMERIC_PARAMETER")
    return format(float(n),".17g")


def modelica_source(case):
    """Represent EXACT grammar/rates of the existing M and D integrators."""
    name="CAF02_"+case["id"]
    need(NAME.fullmatch(case["id"]) is not None,
         "G2_UNEXPECTED_CASE_CLASS")
    arm=case["arm"]
    need(arm in ("M","D") and case["zero_initial_stocks"] is True
         and case["public_probe_duration_minutes"]==20
         and case["public_probe_rate_per_minute"] in (1.2,1.5,1.8),
         "G2_UNEXPECTED_STRUCTURE_OR_PULSE")
    cap=case["capacity_orders_per_hour"]
    if arm=="M":
        need(case["structure"] in ("C00","C01"),
             "G2_UNREGISTERED_M_TOPOLOGY")
        n=2 if case["structure"]=="C00" else 3
        need(case["transit_capacity_orders_per_hour"]==100,
             "G2_TRANSIT_CAP_CHANGED")
        tau=[case["preparation_tau_minutes"],
             case["dispatch_tau_minutes"]]
        caps=[cap,cap]
        if n==3:
            need(case["transit_tau_minutes"] is not None,
                 "G2_M_C01_MISSING_TRANSIT")
            tau.append(case["transit_tau_minutes"])
            caps.append(100)
        else:
            need(case["transit_tau_minutes"] is None,
                 "G2_M_C00_UNEXPECTED_TRANSIT")
    else:
        n=case["stocks"]
        need(case["structure"]==f"D{n}" and 1<=n<=3
             and case["loss"] is False,"G2_D_STRUCTURE_OR_LOSS_CHANGED")
        tau=[case["shared_response_time_minutes"]]*n
        caps=[cap]*n
    arrivals=case["public_probe_rate_per_minute"]*60
    duration=case["public_probe_duration_minutes"]/60
    lines=[
        f"model {name}",
        "  // CAF02 prospective G2 ONLY; derived from fixed PUBLIC hypothesis.",
        "  // The independent DES generator is NOT used to produce this source.",
        "  // Native time: HOURS; material: orders; rates: orders/hour.",
        f"  parameter Real pulseRateH = {fmt(arrivals)};",
        f"  parameter Real pulseDurationH = {fmt(duration)};",
    ]
    for i in range(1,n+1):
        lines += [
            f"  parameter Real capacity{i}H = {fmt(caps[i-1])};",
            f"  parameter Real response{i}H = {fmt(tau[i-1]/60)};",
        ]
    lines += [
        "  Real inputRate;",
        "  Real accepted(start=0, fixed=true);",
        "  Real delivered(start=0, fixed=true);",
    ]
    for i in range(1,n+1):
        lines += [f"  Real s{i}(start=0, fixed=true);",
                  f"  Real f{i};"]
    lines += [
        "equation",
        "  inputRate = if time < pulseDurationH then pulseRateH else 0;",
        "  der(accepted) = inputRate;",
    ]
    for i in range(1,n+1):
        lines.append(
            f"  f{i} = min(capacity{i}H, max(0, s{i}/response{i}H));")
        lines.append(
            "  der(s1) = inputRate - f1;" if i==1
            else f"  der(s{i}) = f{i-1} - f{i};")
    lines += [
        f"  der(delivered) = f{n};",
        f"end {name};",
        "",
    ]
    return "\n".join(lines)


def mos_source(case,absolute_folder):
    """One future native simulation per case; no retries built in."""
    cls="CAF02_"+case["id"]
    folder=str(Path(absolute_folder).resolve())
    need('"' not in folder and "\n" not in folder,"G2_BAD_OUTPUT_PATH")
    mo=str((Path(folder)/(cls+".mo")).resolve())
    # fileNamePrefix avoids overwriting the Modelica source or other cases.
    return "\n".join([
        'setCommandLineOptions("--std=3.4");',
        f'loadFile("{mo}");',
        'print(getErrorString());',
        f'checkModel({cls});',
        'print(getErrorString());',
        f'simulate({cls},startTime=0,stopTime={fmt(STOP_HOURS)},'
        f'numberOfIntervals={INTERVALS},method="{SOLVER}",'
        f'tolerance={SOLVER_TOLERANCE:.1e},outputFormat="csv",'
        f'fileNamePrefix="{cls}");',
        'print(getErrorString());',
        "",
    ])


def compile_manifest(policy,folder):
    plan=g2.plan(policy)
    need(plan["case_counts"]=={"M":12,"D":3,"total":15},
         "G2_PLAN_CASES_NOT_12_M_3_D")
    rows=[]
    sources={}
    for case in plan["cases"]:
        name="CAF02_"+case["id"]
        raw=modelica_source(case)
        job=mos_source(case,folder)
        sources[name+".mo"]=raw
        sources[name+".mos"]=job
        rows.append({
            "id":case["id"],"arm":case["arm"],
            "structure":case["structure"],
            "public_probe":case["public_probe"],
            "pulse_rate_orders_per_minute":case["public_probe_rate_per_minute"],
            "cap_orders_per_hour":case["capacity_orders_per_hour"],
            "capacity_is_observably_active":case[
                "capacity_clamp_observably_changes_output"],
            "modelica_class":name,"source_file":name+".mo",
            "source_sha256":checksum(raw),
            "mos_file":name+".mos","mos_sha256":checksum(job),
            "expected_csv_file":name+"_res.csv",
            "expected_stock_columns":["s"+str(j) for j in
                                      range(1,1+(case["stocks"] if
                                      case["arm"]=="D" else
                                      2 if case["structure"]=="C00" else 3))],
            "observed_times_minutes":case["comparison_times_minutes"],
            "observed_times_hours":case["comparison_times_hours"],
            "reference_curve_from_surrogate_not_OMC":
                case["reference_curve_from_surrogate_not_OMC"],
            "capacity_shadow_gap_orders":case[
                "capacity_clamp_shadow_gap_max_orders"],
            "native_invocation_started":False,
            "native_result_verified":False,
        })
    need(len(rows)==15 and len(sources)==30
         and len(set(sources))==30,"G2_DUPLICATE_NATIVE_SOURCE")
    report={
        "schema":SCHEMA,
        "status":"SOURCES_PREPARED_NO_OMC_INVOCATIONS",
        "plan_sha256":checksum(canonical(plan)),
        "policy_file_sha256":checksum(d.POLICY.read_bytes()),
        "selected_models":15,
        "M_cases":12,"D_cases":3,
        "native_case_OMC_attempt_budget_max":15,
        "OMC_attempts_executed":0,
        "private_DES_runs":0,
        "K2_truth_seen":False,
        "solver":SOLVER,"solver_tolerance":SOLVER_TOLERANCE,
        "intervals":INTERVALS,"stop_time_hours":STOP_HOURS,
        "image_tag_requested_not_immutable_digest":IMAGE_TAG,
        "source_rows":rows,
    }
    return report,sources


def prepare(out):
    out=Path(out).resolve()
    need(not out.exists(),"G2_OUTPUT_ALREADY_EXISTS")
    policy=json.loads(d.POLICY.read_text(encoding="utf-8"))
    report,sources=compile_manifest(policy,out)
    out.mkdir(parents=True,exist_ok=False)
    for name,source in sources.items():
        (out/name).write_text(source,encoding="utf-8",newline="\n")
    (out/"G2_SOURCE_MANIFEST.json").write_bytes(canonical(report))
    return report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("action",choices=("prepare",))
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    report=prepare(args.out)
    print(json.dumps({"status":report["status"],
                      "source_count":report["selected_models"],
                      "native_attempts":report["OMC_attempts_executed"]},
                     sort_keys=True))


if __name__=="__main__":
    main()
