"""Produce an evaluable S lane submission from a VERIFIED captured S simulation.

Neither a model fit nor a successful OpenModelica run establishes empirical truth.
Real provider calls are locally captured, not independently attested. A separate
custodian must hold the new observations and score a frozen PredictionLock.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

from .arena_round import SCHEMA, hash_obj, validate_submission, exclusive_json
from .arena_sp_producers import ProviderError
from .arena_s_real import ORIGIN, verify_s_only_seal
from .arena_s_calibration import verify_calibration
from .arena_sp_simulation import verify_s
from .fm_b3_dynamic_evaluation import result_prefix, digest as file_digest


def require(value: bool, reason: str) -> None:
    if not value:
        raise ProviderError(reason)


def s_submission(*, seal: dict, package: dict, catalog: dict, views: dict,
                 composed: dict, supports: dict, response: dict, draft: dict,
                 receipt: dict, calibration: dict,
                 base_composed: dict, base_plan: dict, evaluation_plan: dict,
                 fit_plan: dict, manifest: dict, verified_report: dict,
                 simulation_dir: Path, log: Path,
                 human_minutes: float) -> dict:
    """Requires actual S capture, fully replayable fit, solver log and CSV."""
    require(seal.get("origin") == ORIGIN, "S_ONLY_REAL_CAPTURE_REQUIRED")
    require(type(human_minutes) in (int,float) and math.isfinite(human_minutes)
            and human_minutes >= 0, "S_HUMAN_MINUTES_MUST_BE_MEASURED")
    verify_s_only_seal(seal, package, catalog, views, composed, supports,
                       response, draft, receipt, calibration=calibration)
    verify_calibration(calibration, base_composed, composed, base_plan,
                       evaluation_plan, fit_plan, views["S"]["primary"])
    require(manifest.get("calibration_receipt_hash") == hash_obj(calibration),
            "S_SIMULATION_FIT_RECEIPT_MISMATCH")
    actual = verify_s(manifest, seal, composed, evaluation_plan,
                      simulation_dir, log)
    require(actual == verified_report
            and actual["status"] == "S_CAPTURED_MODEL_EXECUTION_PASS_SYNTHETIC",
            "S_SIMULATION_REPORT_UNVERIFIED")
    tokens = receipt["usage"]["token_total"]
    require(type(tokens) is int and tokens >= 0,
            "S_TOKEN_USAGE_NOT_OBSERVABLE")
    view=views["S"]
    predictions=[]
    for candidate_id in seal["S"]["selection"]:
        path = simulation_dir / (result_prefix(candidate_id)+"_res.csv")
        trace = verified_report["trace_checks"][candidate_id]
        require(file_digest(path) == trace["csv_sha256"],
                "S_SIMULATION_CSV_CHANGED")
        with path.open(newline="",encoding="utf-8") as source:
            rows=list(csv.DictReader(source))
        predicted=[]
        for time in view["target_times"]:
            found=[float(row["delivered"]) for row in rows
                   if abs(float(row["time"])-float(time)) <= 1e-6]
            require(bool(found) and all(math.isfinite(x) for x in found),
                    "S_TARGET_TIME_NOT_IN_SIMULATION")
            predicted.append(found[-1])
        predictions.append({
            "candidate_id":candidate_id, "kind":"modelica_calibrated_s_candidate",
            "mechanism":"S selected from predeclared structural catalogue; not new topology",
            "predictions":predicted,"trace_sha256":trace["csv_sha256"],
            "fit_receipt_hash":calibration["report_hash"]})
    status="SUBMITTED" if predictions else "ABSTAINED"
    submission={
        "schema":SCHEMA,"round_id":view["round_id"],"lane":"S",
        "view_hash":view["view_hash"],"status":status,
        "producer":"glm-s-only-calibrated-modelica-v0",
        "proposals":predictions,
        "unknowns":(seal["S"]["unknowns"]+
                    ["Model identification and causal truth not established"]),
        "objections":[],
        "cost":{"llm_calls":1,"tokens":tokens,
                "simulations":len(predictions),
                "human_minutes":human_minutes,"retries":0},
        "cost_note":"Provider-reported tokens; operator-measured human minutes; no cash value inferred",
        "capture_receipt_hash":receipt["receipt_hash"],
        "calibration_receipt_hash":calibration["report_hash"],
        "modelica_report_hash":verified_report["report_hash"]}
    validate_submission(submission,view)
    return submission


def main():
    p=argparse.ArgumentParser(description="Create S submission from verified captured real run")
    for name in ("seal","package","catalog","views-dir","composed","supports",
                 "archive","calibration","base-composed","base-plan",
                 "evaluation-plan","fit-plan","manifest","report",
                 "simulation-dir","log","out"):
        p.add_argument("--"+name,required=True)
    p.add_argument("--human-minutes",required=True,type=float)
    args=p.parse_args()
    read=lambda name:json.loads(Path(name).read_text(encoding="utf-8"))
    archive=Path(args.archive)
    result=s_submission(
        seal=read(args.seal),package=read(args.package),
        catalog=read(args.catalog),
        views={"S":read(Path(args.views_dir)/"S.json")},
        composed=read(args.composed),supports=read(args.supports),
        response=read(archive/"response.json"),
        draft=read(archive/"s-draft.json"),
        receipt=read(archive/"receipt.json"),
        calibration=read(args.calibration),
        base_composed=read(args.base_composed),
        base_plan=read(args.base_plan),
        evaluation_plan=read(args.evaluation_plan),fit_plan=read(args.fit_plan),
        manifest=read(args.manifest),verified_report=read(args.report),
        simulation_dir=Path(args.simulation_dir),log=Path(args.log),
        human_minutes=args.human_minutes)
    exclusive_json(Path(args.out),result)
    print(json.dumps({"status":"S_LANE_SUBMITTED_NOT_EVALUATED",
                      "proposals":len(result["proposals"]),
                      "hash":hash_obj(result)}))


if __name__ == "__main__":
    main()
