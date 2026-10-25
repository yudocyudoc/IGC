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


def s_g3_disposition(seal: dict, calibration: dict) -> dict:
    """Adjudicate construction adequacy AFTER retaining the sealed S selection.

    Candidate-level rejection is an experimental observation, never a
    transport failure or a substitute choice made on behalf of S.
    """
    original=list(seal["S"]["selection"])
    fits=calibration["fits"]
    require(len(original)==len(set(original)) and all(cid in fits for cid in original),
            "S_SELECTED_CANDIDATES_NOT_IN_CALIBRATION")
    retained=[]
    discarded=[]
    for cid in original:
        fit=fits[cid]
        state=fit["absolute_adequacy"]
        require(state in ("ADEQUATE","INADEQUATE"), "S_G3_INVALID_ADEQUACY_STATE")
        if state=="ADEQUATE":
            retained.append(cid)
        else:
            discarded.append({
                "candidate_id":cid,
                "reason":"G3_ABSOLUTE_CONSTRUCTION_INADEQUACY",
                "construction_rmse":fit["best_fit"]["rmse"],
                "absolute_rmse_threshold":fit["absolute_rmse_threshold"],
                "physical_input_bound_passed":fit["physical_input_bound_passed"]})
    return {"original_selected_candidate_ids":original,
            "retained_candidate_ids":retained,
            "discarded_candidates":discarded,
            "adjudication":"G3_PER_CANDIDATE_AFTER_S_SEAL"}



def s_submission(*, seal: dict, package: dict, catalog: dict, views: dict,
                 composed: dict, supports: dict, response: dict, draft: dict,
                 receipt: dict, calibration: dict,
                 base_composed: dict, base_plan: dict, evaluation_plan: dict,
                 fit_plan: dict, manifest: dict, verified_report: dict,
                 simulation_dir: Path, log: Path,
                 human_minutes: float, composer_file: Path | None = None) -> dict:
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
                      simulation_dir, log, composer_file=composer_file)
    require(actual == verified_report
            and actual["status"] == "S_CAPTURED_MODEL_EXECUTION_PASS_SYNTHETIC",
            "S_SIMULATION_REPORT_UNVERIFIED")
    g3=s_g3_disposition(seal,calibration)
    require(bool(g3["retained_candidate_ids"]),
            "S_NO_SELECTED_ADEQUATE_USE_ABSTENTION")
    tokens = receipt["usage"]["token_total"]
    require(type(tokens) is int and tokens >= 0,
            "S_TOKEN_USAGE_NOT_OBSERVABLE")
    view=views["S"]
    predictions=[]
    for candidate_id in g3["retained_candidate_ids"]:
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
        fit=calibration["fits"][candidate_id]
        envelopes=[]
        for target in view["target_times"]:
            matches=[x for x in fit["prediction_envelope_rk4"]
                     if abs(x["time"]-float(target))<1e-9]
            require(len(matches)==1,"S_UNCERTAINTY_TARGET_MISSING")
            envelopes.append({"minimum":matches[0]["minimum"],
                              "maximum":matches[0]["maximum"]})
        predictions.append({
            "candidate_id":candidate_id, "kind":"modelica_calibrated_s_candidate",
            "mechanism":"S selected from predeclared structural catalogue; not new topology",
            "predictions":predicted,"trace_sha256":trace["csv_sha256"],
            "fit_receipt_hash":calibration["report_hash"],
            "absolute_adequacy":fit["absolute_adequacy"],
            "uncertainty_envelope_rk4_not_solver_verified":envelopes})
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
                "simulations":len(actual["simulated_ids"]),
                "human_minutes":human_minutes,"retries":0},
        "cost_note":"Provider-reported tokens; operator-measured human minutes; no cash value inferred",
        "capture_receipt_hash":receipt["receipt_hash"],
        "calibration_receipt_hash":hash_obj(calibration),
        "modelica_report_hash":verified_report["report_hash"],
        "s_g3_disposition":g3}
    validate_submission(submission,view)
    return submission



def s_abstention(*, seal: dict, package: dict, catalog: dict, views: dict,
                 composed: dict, supports: dict, response: dict, draft: dict,
                 receipt: dict, calibration: dict, base_composed: dict,
                 base_plan: dict, evaluation_plan: dict, fit_plan: dict,
                 human_minutes: float,
                 manifest: dict | None = None,
                 verified_report: dict | None = None,
                 simulation_dir: Path | None = None,
                 log: Path | None = None,
                 composer_file: Path | None = None) -> dict:
    """Typed abstention when no *selected* candidate passes G3.

    Optional verified solver evidence is accounted for rather than silently
    pretending no simulation occurred.
    """
    require(seal.get("origin")==ORIGIN,"S_ONLY_REAL_CAPTURE_REQUIRED")
    require(type(human_minutes) in (int,float) and math.isfinite(human_minutes)
            and human_minutes >= 0, "S_HUMAN_MINUTES_MUST_BE_MEASURED")
    verify_s_only_seal(seal,package,catalog,views,composed,supports,
                       response,draft,receipt,calibration=calibration)
    verify_calibration(calibration,base_composed,composed,base_plan,
                       evaluation_plan,fit_plan,views["S"]["primary"])
    g3=s_g3_disposition(seal,calibration)
    require(not g3["retained_candidate_ids"],
            "S_ABSTENTION_HAS_SELECTED_ADEQUATE_CANDIDATE")
    provided=(manifest,verified_report,simulation_dir,log,composer_file)
    require(all(x is not None for x in provided) or all(x is None for x in provided),
            "S_ABSTENTION_INCOMPLETE_SIMULATION_EVIDENCE")
    simulations=0
    if manifest is not None:
        require(bool(g3["original_selected_candidate_ids"]),
                "S_EMPTY_SELECTION_CANNOT_HAVE_MODEL_EXECUTION")
        require(manifest.get("calibration_receipt_hash")==hash_obj(calibration),
                "S_SIMULATION_FIT_RECEIPT_MISMATCH")
        actual=verify_s(manifest,seal,composed,evaluation_plan,
                        simulation_dir,log,composer_file=composer_file)
        require(actual==verified_report
                and actual["status"]=="S_CAPTURED_MODEL_EXECUTION_PASS_SYNTHETIC",
                "S_SIMULATION_REPORT_UNVERIFIED")
        simulations=len(actual["simulated_ids"])
    tokens=receipt["usage"]["token_total"]
    require(type(tokens) is int and tokens >= 0,
            "S_TOKEN_USAGE_NOT_OBSERVABLE")
    view=views["S"]
    origin=("S_SELECTION_EMPTY" if not g3["original_selected_candidate_ids"]
        else "ABSOLUTE_CONSTRUCTION_GATE" if
          calibration.get("absolute_adequacy_status")=="NO_ADEQUATE_STRUCTURE"
        else "S_SELECTED_NO_ADEQUATE_STRUCTURE")
    submission={
        "schema":SCHEMA,"round_id":view["round_id"],"lane":"S",
        "view_hash":view["view_hash"],"status":"ABSTAINED",
        "producer":"glm-s-only-calibrated-modelica-v0",
        "proposals":[],
        "unknowns":seal["S"]["unknowns"]+[
            "No selected structural candidate passes the construction-only G3 gate"
            if g3["original_selected_candidate_ids"]
            else "No structural candidate selected; insufficient evidence or uncertainty"],
        "objections":[],
        "cost":{"llm_calls":1,"tokens":tokens,"simulations":simulations,
                "human_minutes":human_minutes,"retries":0},
        "cost_note":"Provider usage and verified solver executions if supplied; no fabricated simulations",
        "capture_receipt_hash":receipt["receipt_hash"],
        "calibration_receipt_hash":hash_obj(calibration),
        "abstention_origin":origin,
        "s_g3_disposition":g3,
        "modelica_report_hash":(verified_report["report_hash"]
                                if simulations else None)}
    validate_submission(submission,view)
    return submission


def main():
    p=argparse.ArgumentParser(description="Create S submission from verified captured real run")
    for name in ("seal","package","catalog","views-dir","composed","supports",
                 "archive","calibration","base-composed","base-plan",
                 "evaluation-plan","fit-plan","out"):
        p.add_argument("--"+name,required=True)
    for name in ("manifest","report","simulation-dir","log","composer-file"):
        p.add_argument("--"+name)
    p.add_argument("--human-minutes",required=True,type=float)
    args=p.parse_args()
    read=lambda name:json.loads(Path(name).read_text(encoding="utf-8"))
    archive=Path(args.archive)
    common=dict(
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
        human_minutes=args.human_minutes)
    adjudication=s_g3_disposition(common["seal"],common["calibration"])
    solver_args=(args.manifest,args.report,args.simulation_dir,args.log,args.composer_file)
    if not adjudication["retained_candidate_ids"]:
        require(all(x is not None for x in solver_args) or
                all(x is None for x in solver_args),
                "S_ABSTENTION_INCOMPLETE_SIMULATION_EVIDENCE")
        evidence=(dict(manifest=read(args.manifest),verified_report=read(args.report),
                       simulation_dir=Path(args.simulation_dir),log=Path(args.log),
                       composer_file=Path(args.composer_file))
                  if args.manifest else {})
        result=s_abstention(**common,**evidence)
    else:
        require(all(solver_args),"S_SIMULATION_EVIDENCE_REQUIRED")
        result=s_submission(
            **common,manifest=read(args.manifest),
            verified_report=read(args.report),
            simulation_dir=Path(args.simulation_dir),log=Path(args.log),
            composer_file=Path(args.composer_file))
    exclusive_json(Path(args.out),result)
    print(json.dumps({"status":"S_LANE_LOCKABLE_NOT_EVALUATED",
                      "proposals":len(result["proposals"]),
                      "hash":hash_obj(result)}))


if __name__ == "__main__":
    main()
