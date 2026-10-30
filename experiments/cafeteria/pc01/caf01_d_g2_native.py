#!/usr/bin/env python3
"""CAF-01 D native G2: only 3 previously selected CAF01 construction candidates.

Consumes the immutable D-only Github #40974820126 public artifact, NOT DES.
Builds exactly one native model per topology. No refitting, RK4, evaluation,
Buffalo, M or hidden data. All solver invocations happen in GitHub Actions.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.arena_d_v01 import modelica, topology
from scripts.arena_d_v1_screen import compare_omc_csv
from scripts.arena_v0_contract import digest
from caf01_g3 import inventory, score, validate_evidence
from caf01_g5_seal import CONTRACT, canonical

HERE = Path(__file__).resolve().parent
EVIDENCE_PATH = HERE / "public_inputs/run_40915090599/CAF01.json"
EVIDENCE_SHA256 = "727501a3b5b33a63ab5a5d5f0f907d5431d0ee4f0d8b24ffd6f97758d59386fb"
PARENT_SHA256 = "e77dbbabc18370104f74c1ee88b86ec3a29d91a2cb3ec30b546a882f4a3675b3"
PARENT_RUN = "40974820126"           # the RK4 screening run containing this file
CONSTRUCTION_RUN = "40915090599"     # its upstream physical DES construction run
PARENT_ARTIFACT_ID = "12941329156"
TIMES_MINUTES = (0, 5, 10, 15, 20, 30, 40)
STEP_HOURS = 1 / 120
BOUND_MASS = .008
BOUND_PARITY = .012
WORLD = "sha256:26ca23076a44410bcafc4a7a944a5d5f6c6528dd59c96e7459e43c93a68812ad"


def require(ok, code):
    if not ok:
        raise ValueError(code)


def sha(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def read_parent(path):
    raw = Path(path).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == PARENT_SHA256,
            "D_G2_PARENT_GITHUB_BYTES_CHANGED")
    obj = json.loads(raw)
    require(obj.get("case") == "CAF01"
            and obj.get("schema") == "igc-caf01-d-only-rk4-screen/0.1"
            and obj.get("source_GitHub_workflow_run") == CONSTRUCTION_RUN
            and obj.get("source_world_precommit") == WORLD
            and obj.get("source_evidence_file_sha256") == "sha256:" + EVIDENCE_SHA256
            and obj.get("actual_RK4_invocations_this_case") == 18
            and obj.get("native_OpenModelica_simulations") == 0
            and obj.get("future_evaluation_forecasts_produced") is False
            and obj.get("evaluation_truth_read") is False,
            "D_G2_PARENT_NOT_APPROVED_CONSTRUCTION_SCREEN")
    return obj


def load_inputs():
    raw = EVIDENCE_PATH.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == EVIDENCE_SHA256,
            "D_G2_EVIDENCE_BYTES_CHANGED")
    evidence = json.loads(raw)
    contract = json.loads(CONTRACT.read_text())
    times, delivered = validate_evidence(evidence, contract)
    require(evidence["case"] == "CAF01"
            and evidence["source_snapshot_sha256"] == WORLD
            and tuple(times) == TIMES_MINUTES,
            "D_G2_UNEXPECTED_CONSTRUCTION_MASK")
    return evidence, contract, delivered


def selected_rows(parent, contract, delivered):
    """Recompute representative choice using saved curves; NEVER integrate."""
    all_d = [x for x in inventory(contract) if x["arm"] == "D"]
    rows = parent["candidate_rows"]
    require(type(rows) is list and len(rows) == 18
            and len({x["id"] for x in rows}) == 18
            and {x["id"] for x in rows} == {x["id"] for x in all_d},
            "D_G2_PARENT_GRID_INCOMPLETE")
    indexed = {x["id"]: x for x in all_d}
    for row in rows:
        candidate = indexed[row["id"]]
        require(row["structure"] == candidate["structure"]
                and row["parameters"] == {
                    "capacity": candidate["capacity"],
                    "response_time": candidate["tau"],
                    "loss_time": 1.0,
                } and row["gate"] == {"G0":"PASS", "G1":"PASS", "G2":"RK4_SCREEN"}
                and row["native_G2_verified"] is False,
                "D_G2_GRID_PARAMETER_OR_GATE_CHANGED")
        mae, rmse = score(row["construction_delivered"], delivered, TIMES_MINUTES)
        require(abs(mae - row["mae"]) < 1e-9 and abs(rmse - row["rmse"]) < 1e-9,
                "D_G2_PARENT_SCORE_NOT_REPRODUCIBLE")
    selected = []
    for struct in ("D1", "D2", "D3"):
        group = [r for r in rows if r["structure"] == struct]
        require(len(group) == 6, "D_G2_TOPOLOGY_NOT_SIX_GRID_POINTS")
        best = min(group, key=lambda r: (r["mae"], r["id"]))
        old = parent["D_preliminary_representatives"][struct]
        require(best["id"] == old["candidate_id"]
                and abs(best["mae"] - old["construction_mae"]) < 1e-9,
                "D_G2_REPRESENTATIVE_CHANGED_AFTER_SCREEN")
        selected.append(best)
    require(len(selected) == 3
            and set(parent["D_preliminary_representatives"]) == {"D1", "D2", "D3"},
            "D_G2_REPRESENTATIVE_SCOPE")
    return selected


def prepare(parent_file, output_dir):
    require(not output_dir.exists(), "D_G2_OUTPUT_EXISTS")
    parent = read_parent(parent_file)
    evidence, contract, obs = load_inputs()
    reps = selected_rows(parent, contract, obs)
    output_dir.mkdir(parents=True, exist_ok=False)
    models = []
    for i, row in enumerate(reps, start=1):
        stocks = i
        graph = topology(stocks, False)
        source = modelica({
            "structure": graph, "structure_hash": digest(graph),
            "nominal_parameters": row["parameters"],
        }, {"kind":"pulse", "rate":72, "duration":1/3})
        native_sha = sha(source.encode("utf-8"))
        require(native_sha == row["native_sha256"],
                "D_G2_NATIVE_SOURCE_DIFFERS_FROM_RK4_RECEIPT")
        name = "DStockFlow_" + digest(graph)[7:19]
        require(source.startswith("model " + name + "\n")
                and source.endswith("end " + name + ";\n")
                and "lossRate = 0;" in source,
                "D_G2_NATIVE_RENDER_CHANGED")
        model_file = output_dir / (name + ".mo")
        model_file.write_text(source, encoding="utf-8", newline="\n")
        # Separate .mos per model. Shell accounts each simulate attempt BEFORE
        # invoking OMC, and never reruns a failed model.
        mos = "\n".join([
            f'cd("{output_dir.resolve().as_posix()}");',
            f'loadFile("{model_file.resolve().as_posix()}");',
            f'checkModel({name});',
            'print(getErrorString());',
            (f'simulate({name},startTime=0,stopTime=(2.0/3.0),'
             'numberOfIntervals=80,method="dassl",tolerance=1e-9,'
             f'outputFormat="csv",fileNamePrefix="D_G2_{i}");'),
            'print(getErrorString());',
            "",
        ])
        (output_dir / f"D_G2_{i}.mos").write_text(mos, encoding="utf-8")
        models.append({
            "ordinal": i, "id": row["id"], "topology_stocks": stocks,
            "class": name, "parameters": row["parameters"],
            "source_sha256": native_sha,
            "expected_csv": f"D_G2_{i}_res.csv",
            "rk4_curve": row["construction_delivered"],
            "rk4_receipt_sha256": row["rk4_receipt_sha256"],
        })
    manifest = {
        "schema": "igc-caf01-d-native-g2/0.1",
        "stage": "PREPARED_ONLY_NOT_SOLVER_VERIFIED",
        "source_RK4_screen_run": PARENT_RUN, "source_DES_construction_run": CONSTRUCTION_RUN,
        "source_artifact_id": PARENT_ARTIFACT_ID,
        "source_file_sha256": "sha256:" + PARENT_SHA256,
        "public_evidence_sha256": "sha256:" + EVIDENCE_SHA256,
        "world_precommit": WORLD,
        "selected_models": models,
        "selected_model_count": 3,
        "maximum_new_native_construction_simulations": 3,
        "simulation_attempts_at_prepare": 0,
        "D_RK4_recomputed": False,
        "CAFN_read": False, "evaluation_read": False,
    }
    (output_dir / "preflight.json").write_bytes(canonical(manifest) + b"\n")
    return manifest


def evaluate_csv(path, stocks, rk4_curve):
    with path.open(newline="", encoding="utf-8") as fp:
        rows = list(csv.DictReader(fp))
    require(len(rows) >= 80, "D_G2_NATIVE_TOO_FEW_SAMPLES")
    required = {"time", "delivered", *[f"s{i}" for i in range(1, stocks+1)]}
    require(required.issubset(rows[0]), "D_G2_NATIVE_MATERIAL_STOCKS_MISSING")
    last_time, last_delivered = -1, -1
    max_mass = 0
    for row in rows:
        t = float(row["time"])
        d = float(row["delivered"])
        vals = [float(row[f"s{i}"]) for i in range(1,stocks+1)]
        # Lost is a known constant zero, independently fixed by loss-free
        # equations. Some OMC CSV writers omit constant alias columns.
        loss = float(row["lost"]) if "lost" in row and row["lost"] else 0.
        require(all(math.isfinite(x) for x in [t,d,*vals,loss])
                and t >= last_time - 1e-9 and d >= last_delivered - 1e-8
                and min([d,loss,*vals]) >= -BOUND_MASS,
                "D_G2_NONPHYSICAL_NATIVE_STATE")
        residual = abs(sum(vals) + d + loss - 72*min(max(t,0),1/3))
        max_mass = max(max_mass, residual)
        last_time, last_delivered = t,d
    require(abs(float(rows[0]["time"])) < 1e-8
            and abs(last_time-2/3) < 1e-6,
            "D_G2_WRONG_NATIVE_TIME_HORIZON")
    pairs = list(zip([t/60 for t in TIMES_MINUTES], rk4_curve))
    compare_omc_csv(path,pairs,atol=BOUND_PARITY)
    native_by_time = [(float(x["time"]),float(x["delivered"])) for x in rows]
    diffs = []
    for t, y in pairs:
        match = [abs(v-y) for x,v in native_by_time if abs(x-t)<1e-6]
        require(bool(match), "D_G2_MISSING_NATIVE_SAMPLE")
        diffs.append(min(match))
    require(max_mass <= BOUND_MASS and max(diffs) <= BOUND_PARITY,
            "D_G2_BALANCE_OR_PARITY_BLOCKED")
    return {"status":"PASS", "native_csv_rows":len(rows),
            "balance_max_abs":max_mass,
            "rk4_native_max_abs_delta":max(diffs),
            "delivered_final":last_delivered}


def verify(out):
    mf = json.loads((out/"preflight.json").read_bytes())
    require(mf["schema"]=="igc-caf01-d-native-g2/0.1"
            and mf["stage"]=="PREPARED_ONLY_NOT_SOLVER_VERIFIED"
            and mf["source_file_sha256"]=="sha256:"+PARENT_SHA256
            and mf["selected_model_count"]==3,
            "D_G2_PREFLIGHT_MANIFEST_BAD")
    checks = []
    for info in mf["selected_models"]:
        path = out/info["expected_csv"]
        require(path.is_file(), "D_G2_NATIVE_RESULT_MISSING")
        # OMC diagnostics must not contain a failed model or simulation,
        # even if the process returned exit code zero.
        log = (out/f"D_G2_{info['ordinal']}.log").read_text()
        require("Error:" not in log and "Simulation Failed" not in log
                and "Failed to load" not in log,
                "D_G2_NATIVE_LOG_ERROR")
        measure = evaluate_csv(path,info["topology_stocks"],info["rk4_curve"])
        checks.append({"id":info["id"], "native_source_sha256":info["source_sha256"],
                       "native_csv_sha256":sha(path.read_bytes()),
                       "native_log_sha256":sha(log.encode()),
                       "rk4_receipt_sha256":info["rk4_receipt_sha256"],
                       **measure})
    result = {
        "schema":"igc-caf01-d-g2-receipts/0.1",
        "status":"ALL_THREE_NATIVE_G2_PASSED",
        "source_RK4_screen_run":PARENT_RUN,
        "source_DES_construction_run":CONSTRUCTION_RUN,
        "source_public_evidence":"sha256:"+EVIDENCE_SHA256,
        "physical_balance_ceiling":BOUND_MASS,
        "RK4_OMC_parity_ceiling":BOUND_PARITY,
        "native_construction_simulations_consumed":3,
        "new_RK4_integrations":0,
        "new_DES_world_runs":0,
        "evaluation_simulations":0,
        "native_candidates":checks
    }
    (out/"D_G2_VERIFIED.json").write_bytes(canonical(result)+b"\n")
    return result


def require_github_one_shot():
    require(os.getenv("GITHUB_ACTIONS")=="true"
            and os.getenv("GITHUB_REF")=="refs/heads/main"
            and os.getenv("GITHUB_EVENT_NAME")=="workflow_dispatch"
            and os.getenv("GITHUB_REPOSITORY")=="yudocyudoc/IGC"
            and os.getenv("GITHUB_RUN_NUMBER")=="1"
            and os.getenv("GITHUB_RUN_ATTEMPT")=="1",
            "D_G2_ONLY_FIRST_MAIN_GITHUB_MANUAL_RUN")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("command",choices=["prepare","verify"])
    ap.add_argument("--parent",type=Path)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    require_github_one_shot()
    if a.command=="prepare":
        require(a.parent is not None,"D_G2_PARENT_REQUIRED")
        info=prepare(a.parent,a.out)
        print("D_G2_PREPARED_ONLY count="+str(info["selected_model_count"]))
    else:
        result=verify(a.out)
        print("D_G2_VERIFIED="+result["status"])


if __name__=="__main__":
    try:
        main()
    except Exception:
        print("D_G2_BLOCKED_NO_AUTOMATIC_RETRY",flush=True)
        raise SystemExit(1) from None
