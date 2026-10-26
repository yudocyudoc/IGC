"""D2: revise own-arm finite-grid parameter hypotheses using a NEW reset-trial measurement.

Methodological boundary: D2 reads D0/D1 visible data and D-only ledger projection.
No molecules, B/M/C hypotheses, model truth, holdout file, or ATMS-generated topologies.
ATMS stores logical dependencies; its supports are never empirical causal verdicts.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path

from scripts.arena_v0_contract import canonical, digest, trace_event
from scripts.arena_atms import project
from scripts.arena_d_v01 import generate, validate_case
from scripts.arena_d_v1_screen import (
    assess, candidate_grid, integrate, score, validate_protocol,
)
from scripts.arena_d_atms_bridge import (
    BridgeError, MIGRATION, POLICY, _store, _logical_record,
    checked_trace, event_id, snapshot,
)
from scripts.ledger import Ledger

SCHEMA = "igc-arena-d-revision/0.1"
TRIAL_SCHEMA = "igc-arena-d-reset-observation/0.1"
METHOD = "JOINT_FINITE_GRID_REVISION_WITH_OWN_ATMS/0.1"


def check(valid, code):
    if not valid:
        raise BridgeError(code)


def canonical_file_hash(path):
    return "sha256:" + sha256(Path(path).read_bytes()).hexdigest()


def extract_reset_observation(*, csv_path, trial_time, input_hash, screen_hash,
                              profile, output):
    """Evaluator-only. World CSV is not part of the D2 input package."""
    check(type(trial_time) in (int, float) and math.isfinite(trial_time) and trial_time > 0,
          "INVALID_RESET_TIME")
    with Path(csv_path).open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    check(len(rows) >= 10 and
          {"time", "delivered"} <= set(rows[0]), "INVALID_WORLD_CSV")
    matches = [(abs(float(r["time"]) - trial_time), float(r["delivered"]))
               for r in rows if abs(float(r["time"]) - trial_time) < 1e-7]
    check(bool(matches), "TRIAL_TIME_NOT_SAMPLED")
    value = min(matches)[1]
    check(math.isfinite(value) and value >= -1e-8, "INVALID_WORLD_VALUE")
    trial = {"schema": TRIAL_SCHEMA, "kind": "INDEPENDENT_SYNTHETIC_RESET",
             "input_hash": input_hash, "d1_screen_hash": screen_hash,
             "pulse": profile, "measurement": {
                 "t": trial_time, "delivered": round(value, 9)},
             "source_csv_hash": canonical_file_hash(csv_path),
             "epistemic_status": "SYNTHETIC_OBSERVATION_NOT_GROUND_TRUTH"}
    Path(output).write_bytes(canonical(trial) + b"\n")
    return trial


def _read_own_ledger(ledger, data, *, as_known_at):
    case_id, round_id = data["investigation_id"], data["round_id"]
    revisions = ledger.snapshot(case_id=case_id, as_known_at=as_known_at)
    prefix = f"arena:{case_id}:{round_id}:D:"
    own = {r.entity_id: r for r in revisions if r.access_policy == POLICY
           and r.entity_id.startswith(prefix)}
    def find(suffix, entity_type):
        key = event_id(case_id, round_id, suffix)
        record = own.get(key)
        check(record is not None and record.entity_type == entity_type and
              ledger.verify_integrity(entity_id=key, revision=record.revision),
              "MISSING_OR_CORRUPTED_D_HISTORY:" + suffix)
        return record.payload
    prior_screen = find("d1:screen", "ArenaDScreen")
    d0_bundle = find("d0:bundle", "ArenaDNativeBundle")
    records = [r.payload for r in own.values() if r.entity_type == "ArenaTraceEnvelope"]
    d0 = next((r for r in records if r.get("event_type") == "HYPOTHESIS_PROPOSED"
               and r.get("iteration") == 0), None)
    d1 = next((r for r in records if r.get("event_type") == "SIMULATION_REPORTED"
               and r.get("iteration") == 0), None)
    check(d0 is not None and d1 is not None, "MISSING_D0_D1_EVENTS")
    checked_trace({k: v for k, v in d0.items() if k != "kind"})
    checked_trace({k: v for k, v in d1.items() if k != "kind"})
    check(d1["previous_event_hash"] == d0["event_hash"] and
          d1["payload_hash"] == digest(prior_screen), "INVALID_D1_PROVENANCE")
    return prior_screen, d0_bundle, d1


def validate_trial(data, protocol, prior, trial):
    check(type(trial) is dict and set(trial) == {
        "schema", "kind", "input_hash", "d1_screen_hash", "pulse",
        "measurement", "source_csv_hash", "epistemic_status"
    }, "INVALID_TRIAL_PACKAGE")
    check(trial["schema"] == TRIAL_SCHEMA and
          trial["kind"] == "INDEPENDENT_SYNTHETIC_RESET" and
          trial["epistemic_status"] == "SYNTHETIC_OBSERVATION_NOT_GROUND_TRUTH",
          "NOT_INDEPENDENT_SYNTHETIC_RESET")
    check(trial["input_hash"] == prior["input_hash"] and
          trial["d1_screen_hash"] == digest(prior), "TRIAL_DIFFERENT_CASE_OR_PARENT")
    check(trial["pulse"] == data["construction"]["input_profile"],
          "TRIAL_INPUT_CHANGED")
    check(isinstance(trial["source_csv_hash"], str) and
          len(trial["source_csv_hash"]) == 71 and
          trial["source_csv_hash"].startswith("sha256:"),
          "MISSING_WORLD_CSV_PROVENANCE")
    obs = trial["measurement"]
    check(type(obs) is dict and set(obs) == {"t", "delivered"} and
          all(type(x) in (float, int) and math.isfinite(x)
              for x in obs.values()) and obs["t"] > 0,
          "INVALID_TRIAL_OBSERVATION")
    # The trial design MUST have been chosen before the world ran.
    design = prior.get("next_measurement")
    check(type(design) is dict and design.get("kind") == "NEW_INDEPENDENT_RESET_TRIAL",
          "NO_PRIOR_MEASUREMENT_DESIGN")
    check(abs(obs["t"] - design["suggested_measurement_time"]) < 1e-8 and
          obs["t"] in protocol["new_trial_sample_times"],
          "TRIAL_NOT_PRIOR_SELECTED")
    return obs


def revise(*, data, protocol, prior, atms_snapshot, trial):
    validate_case(data)
    validate_protocol(protocol, data)
    regenerated = assess(data, protocol)
    check(prior == regenerated, "HISTORICAL_D1_NOT_REPRODUCIBLE")
    check(atms_snapshot["investigation_id"] == data["investigation_id"] and
          atms_snapshot["round_id"] == data["round_id"] and
          atms_snapshot["truth_status"] == "NOT_DETERMINED_BY_ATMS",
          "FOREIGN_ATMS_CONTEXT")
    old_supported = sorted("DCOMPATIBLE:" + ident for ident in prior["eligible_ids"])
    check(sorted(atms_snapshot["conditionally_supported"]) == old_supported,
          "ATMS_PRIOR_SUPPORT_MISMATCH")
    obs = validate_trial(data, protocol, prior, trial)
    seen = data["construction"]["observations"]
    times = [row["t"] for row in seen]
    error = protocol["noise_absolute_bound"]
    check(error is not None and error >= 0, "UNBOUNDED_INSTRUMENT_CANNOT_REVISE")
    pulse = data["construction"]["input_profile"]
    candidates = {c["id"]: c for c in generate(data)["candidates"]}
    outputs = []
    count = 0
    for old in prior["results"]:
        item = candidates[old["candidate_id"]]
        best = None
        witnesses = 0
        for params in candidate_grid(item, protocol):
            prior_prediction = integrate(old["stocks"], old["loss"], params, pulse,
                                         times, protocol["integration_max_step"])
            trial_prediction = integrate(old["stocks"], old["loss"], params, pulse,
                                         [obs["t"]], protocol["integration_max_step"])[0]
            residuals = [p - row["delivered"] for p, row in zip(prior_prediction, seen)]
            residuals.append(trial_prediction - obs["delivered"])
            max_abs = max(abs(x) for x in residuals)
            rmse = math.sqrt(sum(x*x for x in residuals) / len(residuals))
            row = {"parameters": params, "max_abs_residual": max_abs,
                   "rmse": rmse, "predicted_new_trial": trial_prediction}
            if best is None or (max_abs, rmse) < (best["max_abs_residual"], best["rmse"]):
                best = row
            if max_abs <= error + 1e-5:
                witnesses += 1
            count += 1
        status = ("REVISION_GRID_COMPATIBLE_NOT_IDENTIFIED" if witnesses
                  else "REVISION_UNRESOLVED_GRID_NOT_FALSIFIED")
        outputs.append({
            "candidate_id": old["candidate_id"],
            "structure_hash": old["structure_hash"],
            "prior_status": old["status"], "revision_status": status,
            "prior_best_parameters": old["best_grid"]["parameters"],
            "revised_best_parameters": best["parameters"],
            "best_joint_fit": best,
            "compatible_joint_grid_points": witnesses,
            "parameter_changed": best["parameters"] != old["best_grid"]["parameters"],
            "structure_changed": False,
        })
    revised = sorted(x["candidate_id"] for x in outputs if x["compatible_joint_grid_points"])
    check(count == prior["grid_evaluations"], "REVISION_GRID_COUNT_CHANGED")
    conclusion = ("MULTIPLE_REMAIN_NOT_IDENTIFIED" if len(revised) >= 2 else
                  "ONE_REMAINS_OTHER_MODELS_UNRESOLVED" if len(revised) == 1 else
                  "NO_JOINT_GRID_WITNESS_INSUFFICIENT_TO_REFUTE")
    return {
        "schema": SCHEMA, "method": METHOD, "arm_id": "D",
        "investigation_id": data["investigation_id"], "round_id": data["round_id"],
        "iteration": 1, "parent_d1_hash": digest(prior), "trial_hash": digest(trial),
        "atms_projection_hash": atms_snapshot["atms"]["projection_hash"],
        "grid_evaluations": count, "noise_absolute_bound": error,
        "results": outputs, "conditionally_supported_ids": revised,
        "conclusion": conclusion, "new_trial_measurement": obs,
        "truth_status": "NOT_DETERMINED_BY_ATMS_OR_NUMERICAL_FIT",
        "no_structural_falsification": True,
        "revision_kind": "PARAMETER_AND_SUPPORT_UPDATE_NO_TOPOLOGY_GENERATION",
    }


def run(*, db, data, protocol, trial, recorded_at=None):
    """Consume only D's own ledger and new observation. Persist a new revision."""
    validate_case(data)
    if recorded_at is None:
        recorded_at = datetime.now(timezone.utc).isoformat()
    ledger = Ledger(db, Path(__file__).resolve().parents[1] / "migrations/0001_ledger.sql")
    case_id, round_id = data["investigation_id"], data["round_id"]
    history, bundle, d1_event = _read_own_ledger(ledger, data, as_known_at=recorded_at)
    before = snapshot(db=db, case_id=case_id, round_id=round_id,
                      as_known_at=recorded_at)
    report = revise(data=data, protocol=protocol, prior=history,
                    atms_snapshot=before, trial=trial)
    t = datetime.fromisoformat(recorded_at.replace("Z", "+00:00"))
    check(t.tzinfo is not None and t.utcoffset() is not None, "INVALID_RECORDED_TIME")
    # Exact originating D1 artifact and new trial remain independently accessible.
    _store(ledger, case_id=case_id, round_id=round_id, recorded_at=recorded_at,
           entity_type="ArenaDResetObservation", key="d2:trial", payload=trial)
    _store(ledger, case_id=case_id, round_id=round_id, recorded_at=recorded_at,
           entity_type="ArenaDRevision", key="d2:revision", payload=report)
    new_event = trace_event(
        arm_id="D", round_id=round_id, event_type="HYPOTHESIS_REVISED",
        iteration=1, source_hash=history["input_hash"], payload_hash=digest(report),
        previous_event_hash=d1_event["event_hash"])
    _store(ledger, case_id=case_id, round_id=round_id, recorded_at=recorded_at,
           entity_type="ArenaTraceEnvelope",
           key="trace:2:" + new_event["event_hash"][7:19],
           payload={"kind": "trace", **new_event})
    trial_assumption = "DTRIAL:" + report["trial_hash"][7:19]
    _store(ledger, case_id=case_id, round_id=round_id, recorded_at=recorded_at,
           entity_type="ArenaATMSNode", key="logic:" + trial_assumption,
           payload={"kind": "assumption", "id": trial_assumption,
                    "active": True, "source_id": trial["source_csv_hash"],
                    "epistemic_status": "SYNTHETIC_REPORTED_MEASUREMENT"})
    for candidate_id in report["conditionally_supported_ids"]:
        logic_id = "D2RULE:" + candidate_id
        _store(ledger, case_id=case_id, round_id=round_id, recorded_at=recorded_at,
               entity_type="ArenaATMSNode", key="logic:" + logic_id,
               payload={"kind": "justification", "id": logic_id, "active": True,
                        "source_id": new_event["event_hash"],
                        "antecedents": ["DCOMPATIBLE:" + candidate_id, trial_assumption],
                        "consequent": "D2CURRENT:" + candidate_id,
                        "epistemic_status": "CONDITIONAL_NEW_TRIAL_AND_OLD_GRID"})
    after = snapshot(db=db, case_id=case_id, round_id=round_id, as_known_at=recorded_at)
    current = sorted(k.removeprefix("D2CURRENT:") for k in after["logical_state"]["labels"]
                     if k.startswith("D2CURRENT:") and
                     after["logical_state"]["labels"][k])
    check(current == report["conditionally_supported_ids"], "D2_ATMS_SUPPORT_MISMATCH")
    return {"schema": SCHEMA, "status": "D2_REVISED_AND_REMEMBERED",
            "prior_support": before["conditionally_supported"],
            "current_support": current, "report": report,
            "d2_trace_event": new_event, "atms_after": after,
            "no_structural_falsification": True}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["extract", "revise"])
    p.add_argument("--db", type=Path)
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--protocol", type=Path, required=True)
    p.add_argument("--world-csv", type=Path)
    p.add_argument("--trial-time", type=float)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--trial", type=Path)
    a = p.parse_args()
    data=json.loads(a.input.read_text())
    protocol=json.loads(a.protocol.read_text())
    if a.action=="extract":
        check(a.world_csv is not None and a.trial_time is not None, "MISSING_EVALUATOR_INPUT")
        prior=assess(data,protocol)
        check(prior["next_measurement"] is not None, "NO_NEW_TRIAL_DESIGN")
        check(abs(a.trial_time-prior["next_measurement"]["suggested_measurement_time"]) < 1e-8,
              "UNPRECOMMITTED_EXPERIMENT_TIME")
        result=extract_reset_observation(
            csv_path=a.world_csv, trial_time=a.trial_time,
            input_hash=prior["input_hash"], screen_hash=digest(prior),
            profile=data["construction"]["input_profile"], output=a.output)
    else:
        check(a.db is not None and a.trial is not None, "MISSING_D2_INPUTS")
        result=run(db=a.db,data=data,protocol=protocol,
                   trial=json.loads(a.trial.read_text()))
        a.output.write_bytes(canonical(result)+b"\n")
    print(json.dumps({"status": result.get("status","TRIAL_EXTRACTED"),
                      "conclusion": result.get("report",{}).get("conclusion"),
                      "revision_hash": digest(result)}))


if __name__ == "__main__":
    main()
