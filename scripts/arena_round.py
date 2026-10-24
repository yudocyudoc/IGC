"""IGC Arena: round preparation, independent submissions, immutable local LOCK.

No inference is fabricated. Holdout evaluation is a separate privileged operation.
Real blindness needs an external custodian; hashes and GitHub timestamps alone do
not establish access isolation.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from math import isfinite, sqrt
from pathlib import Path
from typing import Any

SCHEMA = "igc-arena-round/0.1"
LANES = ("B0", "D", "S", "P")
FORBIDDEN = {"gold", "holdout", "true_mechanism", "generating_model",
             "hidden_truth", "evaluation_answer"}
COST_UNITS = ("llm_calls", "tokens", "simulations", "human_minutes", "retries")


class RoundError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RoundError(message)


def canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode()


def hash_obj(obj: Any) -> str:
    return "sha256:" + sha256(canonical(obj)).hexdigest()


def parse_time(value: str) -> datetime:
    require(isinstance(value, str), "UTC timestamp required")
    try:
        d = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RoundError("invalid timestamp") from exc
    require(d.tzinfo is not None, "timezone required")
    return d.astimezone(timezone.utc)


def numbers(values: Any) -> list[float]:
    require(isinstance(values, list) and bool(values), "non-empty numeric array required")
    require(all(type(x) in (int, float) and isfinite(x) for x in values),
            "finite numbers required")
    return [float(x) for x in values]


def increasing(values: list[float]) -> bool:
    return all(b > a for a, b in zip(values, values[1:]))


def no_hidden(obj: Any) -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            require(key.casefold() not in FORBIDDEN,
                    "hidden/reserved material in constructor document")
            no_hidden(value)
    elif isinstance(obj, list):
        for value in obj:
            no_hidden(value)


def validate_spec(spec: dict) -> None:
    no_hidden(spec)
    require(spec.get("schema") == SCHEMA and spec.get("synthetic") is True,
            "unsupported round schema")
    for key in ("investigation_id", "round_id", "question", "observable_id", "as_known_at"):
        require(isinstance(spec.get(key), str) and bool(spec[key]), f"{key} required")
    parse_time(spec["as_known_at"])
    require(spec.get("blindness_claim") in ("NOT_ESTABLISHED",
            "EXTERNAL_CUSTODIAN_REQUIRED"), "blindness cannot be asserted by local protocol")
    require(spec.get("allowed_lanes") == list(LANES),
            "all lanes must be declared, including abstentions")
    target = numbers(spec.get("target_times"))
    require(increasing(target), "target times must strictly increase")
    obs = spec.get("observability")
    require(isinstance(obs, dict) and obs.get("kind") in ("observed", "proxy"),
            "observability contract missing")
    require(bool(obs.get("unit")) and bool(obs.get("instrument")), "instrument and unit required")
    require(spec.get("evaluation_metric") == "RMSE", "unsupported metric")
    budgets = spec.get("budgets")
    require(isinstance(budgets, dict) and set(budgets) == set(LANES),
            "per-lane budget required")
    for caps in budgets.values():
        require(isinstance(caps, dict) and set(caps) == set(COST_UNITS),
                "budget units incomplete")
        require(all(type(caps[k]) in (int, float) and isfinite(caps[k]) and caps[k] >= 0
                    for k in COST_UNITS), "invalid budget cap")
    require(spec.get("max_retries") == 0,
            "first round does not permit post-diagnostic retries")


def validate_construction(spec: dict, primary: dict) -> None:
    no_hidden(primary)
    require(primary.get("investigation_id") == spec["investigation_id"],
            "construction case mismatch")
    require(primary.get("observable_id") == spec["observable_id"], "observable mismatch")
    require(primary.get("unit") == spec["observability"]["unit"], "unit mismatch")
    times, values = numbers(primary.get("times")), numbers(primary.get("values"))
    require(len(times) == len(values) and increasing(times), "invalid construction series")
    require(times[-1] < numbers(spec["target_times"])[0],
            "construction overlaps evaluation horizon")
    require(isinstance(primary.get("sources"), list) and bool(primary["sources"]),
            "primary sources required")
    require(all(isinstance(x, str) and x for x in primary["sources"]),
            "invalid primary source")


def prepare(spec: dict, primary: dict, retrieval: dict[str, dict] | None = None) -> dict:
    validate_spec(spec)
    validate_construction(spec, primary)
    retrieval = retrieval or {}
    require(set(retrieval) <= {"D", "S", "P"},
            "B0 cannot inherit enriched retrieval")
    for lane, bundle in retrieval.items():
        no_hidden(bundle)
        require(bundle.get("lane") == lane, "retrieval bundle supplied to wrong lane")
        require(bundle.get("investigation_id") == spec["investigation_id"],
                "retrieval case mismatch")
        require(bundle.get("as_known_at") == parse_time(spec["as_known_at"]).isoformat(),
                "retrieval snapshot time mismatch")
        require(bundle.get("holdout_accessed") is False, "retrieval used reserved evidence")
    common = {"schema": SCHEMA, "round_id": spec["round_id"],
              "investigation_id": spec["investigation_id"],
              "spec_hash": hash_obj(spec), "primary_hash": hash_obj(primary),
              "question": spec["question"], "as_known_at": spec["as_known_at"],
              "primary": primary, "target_times": spec["target_times"],
              "observability": spec["observability"]}
    views = {}
    for lane in LANES:
        view = dict(common, lane=lane, budget=spec["budgets"][lane],
                    retrieval=retrieval.get(lane) if lane != "B0" else None)
        view["view_hash"] = hash_obj(view)
        views[lane] = view
    return views


def b0_submission(view: dict, spec: dict) -> dict:
    require(view["lane"] == "B0", "baseline only")
    observed = numbers(view["primary"]["values"])
    predictions = [observed[-1]] * len(spec["target_times"])
    return {"schema": SCHEMA, "round_id": spec["round_id"], "lane": "B0",
            "view_hash": view["view_hash"], "status": "SUBMITTED",
            "producer": "persistence_baseline_v0",
            "proposals": [{"candidate_id": "B0-PERSISTENCE", "kind": "baseline",
                           "predictions": predictions,
                           "mechanism": "last observation held constant"}],
            "unknowns": ["No structural identification or exogenous drivers"],
            "objections": [], "cost": {key: 0 for key in COST_UNITS}}


def validate_submission(submission: dict, view: dict) -> None:
    no_hidden(submission)
    require(submission.get("schema") == SCHEMA and submission.get("lane") == view["lane"],
            "lane/schema mismatch")
    require(submission.get("round_id") == view["round_id"], "round mismatch")
    require(submission.get("view_hash") == view["view_hash"],
            "view tampered or mismatched")
    require(submission.get("status") in ("SUBMITTED", "ABSTAINED", "NOT_IMPLEMENTED"),
            "unknown lane status")
    require(bool(submission.get("producer")), "producer attribution required")
    cost = submission.get("cost")
    require(isinstance(cost, dict) and set(cost) == set(COST_UNITS),
            "all actual costs required")
    require(all(type(cost[k]) in (int, float) and isfinite(cost[k])
                and 0 <= cost[k] <= view["budget"][k] for k in COST_UNITS),
            "budget exceeded")
    require(cost["retries"] == 0, "retries forbidden in first evaluation")
    for name in ("unknowns", "objections"):
        require(isinstance(submission.get(name), list), f"{name} list required")
    proposals = submission.get("proposals")
    require(isinstance(proposals, list), "proposal list required")
    if submission["status"] != "SUBMITTED":
        require(not proposals and bool(submission["unknowns"]),
                "abstention requires reason, no candidates")
        return
    require(bool(proposals), "submitted lane requires a proposal")
    seen = set()
    for proposal in proposals:
        require(isinstance(proposal, dict) and isinstance(proposal.get("candidate_id"), str),
                "candidate ID required")
        candidate_id = proposal["candidate_id"]
        require(bool(candidate_id) and candidate_id not in seen,
                "duplicate or empty candidate ID")
        seen.add(candidate_id)
        require(bool(proposal.get("kind")), "proposal kind required")
        if view["lane"] in ("B0", "D", "S"):
            require(isinstance(proposal.get("mechanism"), str) and proposal["mechanism"],
                    "mechanism description required")
            prediction = numbers(proposal.get("predictions"))
            require(len(prediction) == len(view["target_times"]),
                    "prediction horizon mismatch")
        if view["lane"] == "P":
            require(proposal.get("kind") in ("assessment", "parameter_proposal"),
                    "P must not manufacture a topology")
            require("predictions" not in proposal,
                    "P is not a structural prediction producer")


def lock_round(spec: dict, views: dict, submissions: dict, *, run_ref: str) -> dict:
    validate_spec(spec)
    require(isinstance(run_ref, str) and run_ref, "run ref required")
    require(set(views) == set(LANES) == set(submissions),
            "all lanes must submit or abstain")
    for lane in LANES:
        require(views[lane]["spec_hash"] == hash_obj(spec), "spec changed")
        require(views[lane]["lane"] == lane, "view lane changed")
        contents = dict(views[lane])
        contents.pop("view_hash", None)
        require(views[lane]["view_hash"] == hash_obj(contents), "view tampered")
        validate_submission(submissions[lane], views[lane])
    require(submissions["B0"]["status"] == "SUBMITTED", "B0 baseline required")
    require(submissions["B0"] == b0_submission(views["B0"], spec),
            "baseline is not the preregistered deterministic comparator")
    data = {"schema": SCHEMA, "round_id": spec["round_id"],
            "investigation_id": spec["investigation_id"], "run_ref": run_ref,
            "spec": spec, "spec_hash": hash_obj(spec),
            "view_hashes": {lane: views[lane]["view_hash"] for lane in LANES},
            "submission_hashes": {lane: hash_obj(submissions[lane]) for lane in LANES},
            "submissions": {lane: submissions[lane] for lane in LANES},
            "evaluation_status": "LOCKED_NOT_EVALUATED",
            "blindness": "NOT_ESTABLISHED"}
    data["lock_hash"] = hash_obj(data)
    return data


def verify_lock(lock: dict) -> None:
    actual = lock.get("lock_hash")
    copied = dict(lock)
    copied.pop("lock_hash", None)
    require(actual == hash_obj(copied), "LOCK_TAMPERED")
    require(lock.get("evaluation_status") == "LOCKED_NOT_EVALUATED", "invalid lock status")
    require(lock.get("spec_hash") == hash_obj(lock["spec"]), "spec altered inside lock")
    require(set(lock["submissions"]) == set(LANES), "missing submission")
    require(all(hash_obj(lock["submissions"][lane]) == lock["submission_hashes"][lane]
                for lane in LANES), "submission tampered")


def score_locked(lock: dict, reserved: dict, *, custodian_ref: str) -> dict:
    """Never call from producer workflow. External custodial controls required."""
    verify_lock(lock)
    spec = lock["spec"]
    require(isinstance(custodian_ref, str) and custodian_ref,
            "custodian identity required")
    require(reserved.get("round_id") == lock["round_id"], "reserve wrong round")
    require(reserved.get("observable_id") == spec["observable_id"],
            "reserve wrong observable")
    require(reserved.get("unit") == spec["observability"]["unit"],
            "reserve unit mismatch")
    require(reserved.get("times") == spec["target_times"], "reserve grid mismatch")
    observed = numbers(reserved.get("values"))
    require(len(observed) == len(spec["target_times"]), "reserve value count mismatch")
    require(isinstance(reserved.get("reserve_id"), str) and reserved["reserve_id"],
            "reserve ID required")
    scores = {}
    for lane in LANES:
        submission = lock["submissions"][lane]
        if submission["status"] != "SUBMITTED":
            scores[lane] = {"status": submission["status"], "candidates": []}
            continue
        candidates = []
        for proposal in submission["proposals"]:
            if "predictions" not in proposal:
                candidates.append({"candidate_id": proposal["candidate_id"],
                                   "result": "NOT_APPLICABLE"})
                continue
            prediction = numbers(proposal["predictions"])
            rmse = sqrt(sum((a - b) ** 2 for a, b in zip(prediction, observed))
                        / len(observed))
            candidates.append({"candidate_id": proposal["candidate_id"],
                               "rmse": rmse})
        scores[lane] = {"status": "EVALUATED", "candidates": candidates}
    report = {"schema": SCHEMA, "round_id": lock["round_id"],
              "lock_hash": lock["lock_hash"], "reserve_id": reserved["reserve_id"],
              "reserve_sha256": hash_obj(reserved),
              "custodian_ref": custodian_ref, "metric": "RMSE", "scores": scores,
              "blindness": "NOT_ESTABLISHED_BY_SOFTWARE",
              "empirical_causality": "NOT_PROVEN",
              "consumption": "HOLDOUT_CONSUMED_FOR_THIS_ROUND"}
    report["report_hash"] = hash_obj(report)
    return report


def exclusive_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as writer:
            writer.write(canonical(data) + b"\n")
    except FileExistsError as exc:
        raise RoundError(f"IMMUTABLE_ARTIFACT_EXISTS: {path}") from exc


def evaluate_once(lock: dict, reserve: dict, receipts_dir: Path, *,
                  custodian_ref: str) -> dict:
    """Local single-use guard, NOT a substitute for permissioned remote storage."""
    report = score_locked(lock, reserve, custodian_ref=custodian_ref)
    receipt = {"schema": SCHEMA, "reserve_id": reserve["reserve_id"],
               "round_id": lock["round_id"], "lock_hash": lock["lock_hash"],
               "report_hash": report["report_hash"], "consumption": "HOLDOUT_CONSUMED"}
    name = sha256(reserve["reserve_id"].encode()).hexdigest() + ".json"
    exclusive_json(receipts_dir / name, receipt)
    return report


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    cli = argparse.ArgumentParser(description="IGC Arena reproducible construction, lock, evaluation")
    sub = cli.add_subparsers(dest="action", required=True)
    pr = sub.add_parser("prepare")
    pr.add_argument("--spec", type=Path, required=True)
    pr.add_argument("--primary", type=Path, required=True)
    pr.add_argument("--out", type=Path, required=True)
    seal = sub.add_parser("lock")
    seal.add_argument("--spec", type=Path, required=True)
    seal.add_argument("--views", type=Path, required=True)
    seal.add_argument("--submissions", type=Path, required=True)
    seal.add_argument("--run-ref", required=True)
    seal.add_argument("--out", type=Path, required=True)
    ev = sub.add_parser("evaluate")
    ev.add_argument("--lock", type=Path, required=True)
    ev.add_argument("--reserve", type=Path, required=True)
    ev.add_argument("--receipts", type=Path, required=True)
    ev.add_argument("--custodian-ref", required=True)
    ev.add_argument("--out", type=Path, required=True)
    args = cli.parse_args()
    if args.action == "prepare":
        views = prepare(_read(args.spec), _read(args.primary))
        for lane, view in views.items():
            exclusive_json(args.out / (lane + ".json"), view)
        print(json.dumps({"status": "PREPARED", "lanes": list(views)}))
    elif args.action == "lock":
        views = {lane: _read(args.views / (lane + ".json")) for lane in LANES}
        submissions = {lane: _read(args.submissions / (lane + ".json")) for lane in LANES}
        locked = lock_round(_read(args.spec), views, submissions, run_ref=args.run_ref)
        exclusive_json(args.out, locked)
        print(json.dumps({"status": "LOCKED", "lock_hash": locked["lock_hash"]}))
    else:
        locked = _read(args.lock)
        report = evaluate_once(locked, _read(args.reserve), args.receipts,
                               custodian_ref=args.custodian_ref)
        exclusive_json(args.out, report)
        print(json.dumps({"status": "HOLDOUT_CONSUMED",
                          "report_hash": report["report_hash"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
