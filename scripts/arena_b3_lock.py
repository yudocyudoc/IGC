"""Lock verified FM-B3 predictions as Arena lane D; no new blind evaluation.

S/P explicitly report NOT_IMPLEMENTED rather than fabricated model outputs.
"""
from __future__ import annotations
import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path
import re

from .arena_round import (COST_UNITS, LANES, SCHEMA, b0_submission, exclusive_json,
                          hash_obj, lock_round, numbers, prepare, require)


def report_to_d(view: dict, report: dict, simulation_dir: Path) -> dict:
    require(view["lane"] == "D", "B3 must target D")
    require(report.get("status") == "B3_MOLECULAR_DYNAMICS_PASS_SYNTHETIC",
            "verified synthetic B3 report required")
    require(report.get("empirical_or_causal_claim") is False and
            report.get("explanatory_adequacy_evaluated") is False,
            "B3 must not claim empirical truth")
    disposition = report.get("candidate_disposition", {})
    selected = disposition.get("retained_and_simulated")
    rejected = disposition.get("rejected_and_not_simulated")
    require(isinstance(selected, list) and len(selected) >= 2
            and len(set(selected)) == len(selected),
            "at least two distinct simulated candidates required")
    require(isinstance(rejected, list) and not (set(rejected) & set(selected)),
            "rejected and simulated candidates overlap")
    require(disposition.get("simulated_count") == len(selected)
            and report.get("dynamic_coherence", {}).get("all_admissible_candidates_pass") is True,
            "B3 consistency/coverage missing")
    require(len(selected) <= view["budget"]["simulations"],
            "B3 exceeds D simulation budget")
    traces = report["dynamic_coherence"]["candidate_metrics"]
    require(set(traces) == set(selected), "B3 trace/candidate mismatch")
    predictions = []
    for candidate_id in selected:
        suffix = re.sub(r"[^a-z0-9_]", "_", candidate_id.rsplit(":", 1)[-1].lower())
        trace_path = simulation_dir / f"b3-{suffix}_res.csv"
        require(trace_path.is_file(), "missing B3 simulation CSV")
        digest = "sha256:" + sha256(trace_path.read_bytes()).hexdigest()
        require(digest == traces[candidate_id].get("csv_sha256"), "B3 CSV digest mismatch")
        with trace_path.open(newline="", encoding="utf-8") as source:
            records = list(csv.DictReader(source))
        require(bool(records)
                and all("time" in row and "delivered" in row for row in records),
                "missing B3 observable")
        times = numbers([float(row["time"]) for row in records])
        delivered = numbers([float(row["delivered"]) for row in records])
        result = []
        for target in view["target_times"]:
            found = [value for time, value in zip(times, delivered)
                     if abs(time - target) <= 1e-6]
            require(bool(found), "target evaluation grid absent in B3 simulation")
            result.append(found[-1])
        predictions.append({
            "candidate_id": candidate_id, "kind": "modelica_regression_candidate",
            "mechanism": "FM-B3 composed molecule candidate " + candidate_id,
            "predictions": result, "trace_sha256": digest
        })
    return {"schema": SCHEMA, "round_id": view["round_id"], "lane": "D",
            "view_hash": view["view_hash"], "status": "SUBMITTED",
            "producer": "fm_b3_verified_modelica_v0", "proposals": predictions,
            "unknowns": ["This synthetic regression does not identify a real mechanism"],
            "objections": [], "source_report_sha256": hash_obj(report),
            "cost": {"llm_calls": 0, "tokens": 0, "simulations": len(selected),
                     "human_minutes": 0, "retries": 0},
            "cost_note": "Counts simulation executions only; human preparation and CPU are unmeasured"}


def unimplemented(view: dict, producer: str) -> dict:
    require(view["lane"] in ("S", "P"), "only unimplemented producer lanes")
    return {"schema": SCHEMA, "round_id": view["round_id"], "lane": view["lane"],
            "view_hash": view["view_hash"], "status": "NOT_IMPLEMENTED",
            "producer": producer, "proposals": [],
            "unknowns": ["No independent producer output in this public FM-B3 regression"],
            "objections": [], "cost": {key: 0 for key in COST_UNITS}}


def build(spec: dict, primary: dict, report: dict,
          simulation_dir: Path, *, run_ref: str) -> tuple[dict, dict, dict]:
    views = prepare(spec, primary)
    submissions = {
        "B0": b0_submission(views["B0"], spec),
        "D": report_to_d(views["D"], report, simulation_dir),
        "S": unimplemented(views["S"], "sd-ai-unavailable-in-regression"),
        "P": unimplemented(views["P"], "clef-clairic-unavailable-in-regression")
    }
    return views, submissions, lock_round(spec, views, submissions, run_ref=run_ref)


def main() -> int:
    parser = argparse.ArgumentParser(description="Lock verified FM-B3 without opening reserve")
    for name in ("spec", "primary", "report"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--simulation-dir", required=True, type=Path)
    parser.add_argument("--run-ref", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    read = lambda path: json.loads(path.read_text(encoding="utf-8"))
    views, submissions, lock = build(read(args.spec), read(args.primary), read(args.report),
                                     args.simulation_dir, run_ref=args.run_ref)
    for lane in LANES:
        exclusive_json(args.output_dir / "views" / (lane + ".json"), views[lane])
        exclusive_json(args.output_dir / "submissions" / (lane + ".json"), submissions[lane])
    exclusive_json(args.output_dir / "prediction-lock.json", lock)
    print(json.dumps({"status": "LOCKED_NOT_EVALUATED", "lock_hash": lock["lock_hash"],
                      "simulated_candidates": len(submissions["D"]["proposals"]),
                      "S": "NOT_IMPLEMENTED", "P": "NOT_IMPLEMENTED"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
