#!/usr/bin/env python3
"""M construction-only first-dispatch G2. Six predeclared E1 capacity classes.

Native solver is invoked ONLY by GitHub Actions; this program prepares and
verifies saved CSVs, with independent PASS/FAIL receipts per model. No D/B
results, DES world implementation, G4, or evaluation observations are inputs.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path

from caf01_g3 import CONTRACT
from caf01_m_producer_admission import packet, published_caf_model_sources
from caf01_m_native_preflight import render_bundle, resolve_check_only_paths

HERE=Path(__file__).resolve().parent
SOURCE_RATE=72.0
DURATION_HOURS=1/3
HORIZON_HOURS=2/3
BOUND_MASS=0.008
SAMPLES=80
CLASSES=("C00","C01","C02")
CAPS=(20,72)
SHA=lambda raw: "sha256:"+hashlib.sha256(raw).hexdigest()

def need(ok,code):
    if not ok: raise ValueError(code)

def canonical(obj):
    return (json.dumps(obj,sort_keys=True,ensure_ascii=False,
                       separators=(",",":"),allow_nan=False)+"\n").encode()

def prepare(out):
    need(not out.exists(),"M_G2_OUTPUT_EXISTS")
    contract=json.loads(CONTRACT.read_text(encoding="utf-8"))
    p=packet(contract)
    package,mos,_=render_bundle(contract)
    need(p["G2"]=="NOT_RUN" and p["budget"]["M_construction_OpenModelica_used_by_this_packet"]==0,
         "M_G2_STAGED_SOURCE_NOT_FROZEN")
    expected_names=[x["model_name"] for x in p["nine_nominal_model_sources"]]
    text=published_caf_model_sources(package,expected_names)
    members=p["six_structural_capacity_classes"]
    need(len(members)==6 and
         [(r["structure"],r["capacity_items_per_hour"]) for r in members]==
         [(s,c) for s in CLASSES for c in CAPS],
         "M_G2_WRONG_SIX_PREDECLARED_MEMBERS")
    for row in [*p["nine_nominal_model_sources"],
                *[{"model_name":x["class_name"],"source_sha256":x["source_sha256"]}
                  for x in members]]:
        need(row["source_sha256"]==SHA(text[row["model_name"]].encode("utf-8")),
             "M_G2_FINAL_CAF_SOURCE_HASH_DIFFERS")
    out.mkdir(parents=True,exist_ok=False)
    (out/"CAF01MPreflight.mo").write_bytes(package.encode("utf-8"))
    (out/"M_CHECK_ONLY.mos").write_text(resolve_check_only_paths(mos,out))
    need(SHA((out/"CAF01MPreflight.mo").read_bytes())==
         p["published_CAF01MPreflight_mo_sha256"],"M_G2_PACKAGE_BYTES_CHANGED")
    (out/"M_PRODUCER_PACKET.json").write_bytes(canonical(p))
    simulations=[]
    for n,item in enumerate(members,1):
        cls=item["class_name"]
        script="\n".join([
            f'simulate(CAF01MPreflight.{cls},startTime=0,stopTime=(2.0/3.0),'
            'numberOfIntervals=80,method="dassl",tolerance=1e-9,'
            f'outputFormat="csv",fileNamePrefix="M_G2_{n}");',
            'print(getErrorString());',
            ""
        ])
        # Every one-shot script independently loads the unchanged material
        # catalogue and exactly the published package. No source edits.
        loader="\n".join([
            f'cd("{out.resolve().as_posix()}");',
            f'loadFile("{(HERE.parents[2]/"src/modelica/IGCMolecules.mo").resolve().as_posix()}");',
            f'loadFile("{(HERE.parents[2]/"src/modelica/IGCInformationMolecules.mo").resolve().as_posix()}");',
            f'loadFile("{(out/"CAF01MPreflight.mo").resolve().as_posix()}");',
            f'checkModel(CAF01MPreflight.{cls});',
            'print(getErrorString());',
            ""
        ])
        (out/f"M_G2_{n}.mos").write_text(loader+script,encoding="utf-8")
        simulations.append({
            "ordinal":n,"id":item["id"],"class":cls,
            "structure":item["structure"],
            "capacity":item["capacity_items_per_hour"],
            "final_model_source_sha256":item["source_sha256"],
            "expected_csv":f"M_G2_{n}_res.csv",
            "nominal_capacity_aliases":item["nominal_capacity_aliases"],
        })
    result={
        "schema":"igc-caf01-m-native-g2/0.1",
        "status":"PREPARED_NOT_SIMULATED",
        "public_evidence":p["public_construction_views"]["CAF01"]["original_file_sha256"],
        "source_public_world":p["source_DES_construction_public_snapshot"],
        "source_package_sha256":p["published_CAF01MPreflight_mo_sha256"],
        "six_predeclared_members":simulations,
        "M_OMC_construction_max_new_attempts":6,
        "original_M_OMC_construction_ceiling":9,
        "C72_C100_equivalence_conditionally_assumed":True,
        "M_negative_control_additional_solver_attempts":0,
        "native_invocations_at_prepare":0,
        "evaluation_observations_read":False,
        "D_or_B_results_read":False
    }
    (out/"M_G2_PREFLIGHT.json").write_bytes(canonical(result))
    return result

def audit_csv(path, structure):
    """Physical balance from ORIGINAL E1 material Level stocks, not 'inTransit'.

    inTransit is only a transit-chain report (zero for C00), and does not
    include the preparation and dispatch material stocks. Its use as total
    pending silently and wrongly rejects otherwise conserving native curves.
    Material stock columns are fixed by the nine published native E1 models.
    """
    need(structure in CLASSES,"M_G2_STRUCTURE_NOT_PREDECLARED")
    n_transit=CLASSES.index(structure)
    columns=[
        "preparation0.stock.level",
        "dispatch0.stock.level",
        *[f"transit{i}.stock.level" for i in range(n_transit)]
    ]
    with path.open(encoding="utf-8",newline="") as fp:
        rows=list(csv.DictReader(fp))
    need(len(rows)>=81,"M_G2_NATIVE_TOO_FEW_ROWS")
    header=set(rows[0])
    expected={"time","inTransit","deliveredTotal","receipt0.deliveries.level",
              *columns}
    need(expected.issubset(header),"M_G2_NATIVE_REQUIRED_PHYSICAL_COLUMNS_MISSING")
    physical_found={c for c in header
                    if c.endswith(".stock.level") and
                    (c.startswith("preparation") or c.startswith("dispatch")
                     or c.startswith("transit"))}
    need(physical_found==set(columns),"M_G2_NATIVE_MATERIAL_STOCK_TOPOLOGY_CHANGED")
    max_mass=0.
    max_transit_alias=0.
    max_delivery_alias=0.
    prev_t=-math.inf
    prev_delivery=-math.inf
    for row in rows:
        t=float(row["time"])
        stocks=[float(row[c]) for c in columns]
        delivered=float(row["deliveredTotal"])
        delivered_stock=float(row["receipt0.deliveries.level"])
        transit_alias=float(row["inTransit"])
        need(all(math.isfinite(v) for v in [t,delivered,delivered_stock,
                                            transit_alias,*stocks]),
             "M_G2_NATIVE_NONFINITE")
        need(t>=prev_t-1e-9 and
             delivered>=prev_delivery-1e-7 and
             min(stocks+[delivered,delivered_stock])>=-BOUND_MASS and
             t>=-1e-8 and t<=HORIZON_HOURS+1e-7,
             "M_G2_NATIVE_UNPHYSICAL_STATE")
        arrival=SOURCE_RATE*min(max(t,0),DURATION_HOURS)
        # One completed item exists in the terminal delivery counter, and
        # every outstanding item exists in precisely ONE material Level.
        # Do not count display/reporting filters, aliases, or flows as stocks.
        max_mass=max(max_mass,abs(sum(stocks)+delivered-arrival))
        max_transit_alias=max(max_transit_alias,
                              abs(transit_alias-sum(stocks[2:])))
        max_delivery_alias=max(max_delivery_alias,
                               abs(delivered-delivered_stock))
        prev_t=t
        prev_delivery=delivered
    need(abs(float(rows[0]["time"]))<1e-8 and
         abs(prev_t-HORIZON_HOURS)<1e-6,
         "M_G2_NATIVE_TIME_GRID_WRONG")
    need(max_transit_alias<=BOUND_MASS and
         max_delivery_alias<=BOUND_MASS,
         "M_G2_NATIVE_REPORT_ALIAS_INCONSISTENT")
    need(max_mass<=BOUND_MASS,"M_G2_NATIVE_MASS_BALANCE_FAILED")
    points=[]
    for minute in (0,5,10,15,20,30,40):
        matches=[float(z["deliveredTotal"]) for z in rows
                 if abs(float(z["time"])-minute/60)<1e-6]
        need(len(matches)>=1,"M_G2_NATIVE_OBSERVATION_TIME_MISSING")
        points.append(matches[0])
    return {
        "status":"PASS",
        "balance_max_abs":max_mass,
        "transit_report_max_abs_delta":max_transit_alias,
        "delivery_counter_max_abs_delta":max_delivery_alias,
        "native_material_stock_columns":columns,
        "native_csv_rows":len(rows),
        "construction_delivered":points
    }


def optional_sha(file):
    try: return SHA(file.read_bytes()) if file.is_file() else None
    except OSError: return None

def verify(folder):
    p=json.loads((folder/"M_G2_PREFLIGHT.json").read_bytes())
    need(p["schema"]=="igc-caf01-m-native-g2/0.1"
         and p["status"]=="PREPARED_NOT_SIMULATED"
         and len(p["six_predeclared_members"])==6
         and [r["ordinal"] for r in p["six_predeclared_members"]]==list(range(1,7))
         and p["M_OMC_construction_max_new_attempts"]==6,
         "M_G2_INVALID_PREFLIGHT_MANIFEST")
    outcomes=[]
    for row in p["six_predeclared_members"]:
        n=row["ordinal"]
        logfile=folder/f"M_G2_{n}.console.txt"
        solverlog=folder/f"M_G2_{n}.log"
        attempt=folder/f"M_G2_{n}.attempt"
        exitcode=folder/f"M_G2_{n}.exit_code"
        csvfile=folder/row["expected_csv"]
        result={
            "ordinal":n,"id":row["id"],"status":"FAIL",
            "reason_code":None,"invocation_started":attempt.is_file(),
            "native_model_source_sha256":row["final_model_source_sha256"],
            "native_csv_sha256":optional_sha(csvfile),
            "native_solver_log_sha256":optional_sha(solverlog),
            "native_console_log_sha256":optional_sha(logfile),
            "balance_max_abs":None,"construction_delivered":None,
            "native_csv_rows":None
        }
        try:
            need(attempt.is_file() and attempt.read_bytes()==b"INVOCATION_STARTED\n",
                 "M_G2_INVOCATION_NOT_RECORDED")
            need(exitcode.is_file() and exitcode.read_bytes()==b"0\n",
                 "M_G2_NATIVE_SOLVER_EXIT_NONZERO_OR_MISSING")
            need(solverlog.is_file(),"M_G2_NATIVE_SOLVER_LOG_MISSING")
            log=solverlog.read_text(encoding="utf-8")
            need("Error:" not in log and "Failed to load" not in log
                 and "Simulation Failed" not in log,
                 "M_G2_NATIVE_SOLVER_LOG_ERRORS")
            need(csvfile.is_file(),"M_G2_NATIVE_CSV_MISSING")
            result.update(audit_csv(csvfile,row["structure"]))
        except Exception as exc:
            msg=str(exc)
            result["reason_code"]=msg if msg.startswith("M_G2_") and len(msg)<90 else "M_G2_NATIVE_VERIFICATION_ERROR"
        (folder/f"M_G2_{n}_receipt.json").write_bytes(canonical(result))
        outcomes.append(result)
    passed=sum(x["status"]=="PASS" for x in outcomes)
    result={
        "schema":"igc-caf01-m-native-g2-receipts/0.1",
        "status":"ALL_SIX_M_NATIVE_G2_PASS" if passed==6 else "PARTIAL_M_NATIVE_G2",
        "native_construction_simulations_consumed":sum(x["invocation_started"] for x in outcomes),
        "native_g2_pass_count":passed,
        "native_g2_fail_count":6-passed,
        "original_construction_OMC_ceiling":9,
        "new_DES_worlds":0,
        "new_D_RK4_integrations":0,
        "Buffalo_provider_calls":0,
        "evaluation_world_accessed":False,
        "native_candidates":outcomes,
    }
    (folder/"M_G2_AGGREGATE.json").write_bytes(canonical(result))
    return result

def require_github_one_shot():
    need(os.getenv("GITHUB_ACTIONS")=="true" and
         os.getenv("GITHUB_REF")=="refs/heads/main" and
         os.getenv("GITHUB_EVENT_NAME")=="workflow_dispatch" and
         os.getenv("GITHUB_REPOSITORY")=="yudocyudoc/IGC" and
         os.getenv("GITHUB_RUN_NUMBER")=="1" and
         os.getenv("GITHUB_RUN_ATTEMPT")=="1",
         "M_G2_FIRST_MANUAL_MAIN_RUN_ONLY")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("cmd",choices=("prepare","verify"))
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    require_github_one_shot()
    report=prepare(args.out) if args.cmd=="prepare" else verify(args.out)
    print(report["status"],flush=True)
    if args.cmd=="verify" and report["status"]!="ALL_SIX_M_NATIVE_G2_PASS":
        raise SystemExit(1)

if __name__=="__main__":
    main()
