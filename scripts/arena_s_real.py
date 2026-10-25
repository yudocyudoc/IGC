"""One-provider S capture and independently auditable ATMS handoff.

Does not replace the existing three-provider S/P round. The S-only route permits
a structural pilot when Clef/Clairic cannot be reached. Local hashes establish
consistency, never independent attestation, causal truth or blindness.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time
from typing import Callable
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from .arena_round import canonical, exclusive_json, hash_obj, no_hidden
from .arena_sp_producers import (
    ProviderError, _validate_schedule, parse_s_response, MODELS
)
from .arena_sp_capture import usage_of
from .fm_b2_atms_candidate_reasoning import apply_supports

SCHEMA = "igc-arena-s-single-capture/0.1"
AUTHORIZATION = "RUN_ARENA_S_ONE"
ORIGIN = "S_SINGLE_PROVIDER_CAPTURE"
TEST_ORIGIN = "S_SINGLE_PROVIDER_TEST_ONLY"


def check(predicate: bool, message: str) -> None:
    if not predicate:
        raise ProviderError(message)


def capture_s(package: dict, catalog: dict, *, authorization: str,
              out_dir: Path, run_ref: str, env: dict | None = None,
              sender: Callable = urlopen,
              capture_method: str = "PYTHON_URLLIB",
              clock: Callable = time.perf_counter) -> dict:
    """One explicit provider request; unique archive; never automatically retry."""
    _validate_schedule(package)
    check(authorization == AUTHORIZATION, "NO_INFERENCE: S-only authorization required")
    check(isinstance(run_ref, str) and bool(run_ref.strip()), "S_RUN_REF_REQUIRED")
    check(capture_method in ("PYTHON_URLLIB", "INJECTED_TEST_SENDER"),
          "S_CAPTURE_METHOD_INVALID")
    check((capture_method == "PYTHON_URLLIB" and sender is urlopen) or
          (capture_method == "INJECTED_TEST_SENDER" and sender is not urlopen),
          "S_CAPTURE_METHOD_TRANSPORT_MISMATCH")
    check(hash_obj(catalog) == package["manifest"]["catalog_hash"],
          "S catalog modified after request preparation")
    env = os.environ if env is None else env
    account = env.get("CLOUDFLARE_ACCOUNT_ID", "")
    token = env.get("CLOUDFLARE_API_TOKEN", "")
    check(len(account) == 32 and all(c in "0123456789abcdefABCDEF" for c in account)
          and bool(token), "NO_INFERENCE: valid Cloudflare credentials required")
    req = package["requests"][0]
    check(req["model_name"] == "S_GLM" and req["endpoint"] == MODELS["S_GLM"],
          "S_ONLY_REQUIRES_PREPARED_GLM_REQUEST")
    out_dir.mkdir(parents=True, exist_ok=False)
    exclusive_json(out_dir / "started.json", {
        "schema": SCHEMA, "run_ref": run_ref,
        "request_hash": req["body_hash"], "state": "STARTED_NOT_COMPLETED"})
    request = Request(
        f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{req['endpoint']}",
        data=canonical(req["body"]), method="POST",
        headers={"Authorization": "Bearer " + token,
                 "Content-Type": "application/json", "Accept": "application/json"})
    start = clock()
    try:
        with sender(request, timeout=150) as stream:
            response = json.load(stream)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError):
        # An ambiguous timeout is not permission to replay the same call.
        raise ProviderError("S_PROVIDER_CALL_FAILED_NO_RETRY") from None
    duration_ms = max(0., (clock() - start) * 1000.)
    # Persist the original response even if it cannot be normalized.
    exclusive_json(out_dir / "response.json", response)
    parsed = parse_s_response(package, response, catalog)
    receipt = {
        "schema": SCHEMA, "run_ref": run_ref,
        "capture_method": capture_method,
        "mock": capture_method != "PYTHON_URLLIB",
        "requests_hash": package["manifest"]["requests_hash"],
        "catalog_hash": hash_obj(catalog),
        "view_hash": req["view_hash"],
        "request_body_hash": req["body_hash"],
        "response_hash": hash_obj(response),
        "parsed_s_hash": hash_obj(parsed),
        "calls_completed": 1, "retries": 0,
        "duration_ms": duration_ms, "usage": usage_of(response),
        "independent_attestation": False,
        "empirical_causality": "NOT_PROVEN"}
    no_hidden(receipt)
    receipt["receipt_hash"] = hash_obj(receipt)
    exclusive_json(out_dir / "s-draft.json", parsed)
    exclusive_json(out_dir / "receipt.json", receipt)
    exclusive_json(out_dir / "completed.json", {
        "schema": SCHEMA, "state": "S_SINGLE_CAPTURE_COMPLETE_NOT_EVALUATED",
        "receipt_hash": receipt["receipt_hash"]})
    return receipt


def verify_s_capture(package: dict, catalog: dict, response: dict,
                     draft: dict, receipt: dict,
                     *, require_live: bool = False) -> None:
    _validate_schedule(package)
    check(receipt.get("schema") == SCHEMA, "S_RECEIPT_SCHEMA")
    check(receipt.get("receipt_hash") == hash_obj({
        key: value for key, value in receipt.items() if key != "receipt_hash"}),
        "S_RECEIPT_TAMPERED")
    req = package["requests"][0]
    check(receipt.get("requests_hash") == package["manifest"]["requests_hash"]
          and receipt.get("catalog_hash") == hash_obj(catalog)
          and receipt.get("request_body_hash") == req["body_hash"]
          and receipt.get("view_hash") == req["view_hash"],
          "S_REQUEST_PROVENANCE_MISMATCH")
    check(receipt.get("response_hash") == hash_obj(response)
          and receipt.get("parsed_s_hash") == hash_obj(draft),
          "S_RESPONSE_PROVENANCE_MISMATCH")
    check(draft == parse_s_response(package, response, catalog),
          "S_DRAFT_NOT_FROM_PROVIDER_RESPONSE")
    check(receipt.get("calls_completed") == 1 and receipt.get("retries") == 0
          and receipt.get("usage") == usage_of(response),
          "S_USAGE_OR_CALL_COUNT_MISMATCH")
    check(receipt.get("independent_attestation") is False
          and receipt.get("empirical_causality") == "NOT_PROVEN"
          and receipt.get("capture_method") in
          ("PYTHON_URLLIB", "INJECTED_TEST_SENDER")
          and receipt.get("mock") is (receipt["capture_method"] != "PYTHON_URLLIB"),
          "S_CAPTURE_CLAIMS_INVALID")
    if require_live:
        check(receipt["capture_method"] == "PYTHON_URLLIB"
              and receipt["mock"] is False, "MOCK_IS_NOT_REAL_S_PROVIDER")
    # Even PYTHON_URLLIB is not independently attested; the operator can
    # fabricate a local receipt. These checks prove consistency only.


def seal_s_only(package: dict, catalog: dict, views: dict, composed: dict,
                supports: dict, response: dict, draft: dict, receipt: dict,
                calibration: dict | None = None) -> dict:
    """ATMS admit a single S proposal without waiting for P."""
    verify_s_capture(package, catalog, response, draft, receipt)
    check(views["S"].get("view_hash") == package["manifest"]["view_hashes"]["S"],
          "S_VIEW_PROVENANCE_MISMATCH")
    check(set(x["candidate_id"] for x in catalog["candidates"]) ==
          set(x["id"] for x in composed["candidates"]),
          "S_CATALOG_COMPOSITION_MISMATCH")
    if calibration is not None:
        check(calibration.get("status") == "PARAMETERS_FITTED_CONSTRUCTION_ONLY"
              and calibration.get("report_hash") == hash_obj({
                  k:v for k,v in calibration.items() if k != "report_hash"})
              and calibration.get("construction_hash") == views["S"]["primary_hash"]
              and calibration.get("calibrated_composed_hash") == hash_obj(composed)
              and calibration.get("holdout_accessed") is False,
              "S_CALIBRATION_PROVENANCE_INVALID")
    selection = apply_supports(composed, supports)
    allowed = {item["candidate_id"]: item for item in selection["selected"]}
    rejected = {item["candidate_id"] for item in selection["rejected"]}
    selected = draft["selected_candidate_ids"]
    check(not set(selected) & set(rejected),
          "ATMS_REJECTED_CANDIDATE")
    check(set(selected) <= set(allowed), "S_UNSUPPORTED_CANDIDATE")
    origin = TEST_ORIGIN if receipt["mock"] else ORIGIN
    seal = {
        "schema": "igc-arena-s-handoff/0.1",
        "round_id": package["manifest"]["round_id"],
        "origin": origin, "synthetic": True,
        "eligible_for_empirical_scoring": False,
        "provider_attestation": "LOCAL_CAPTURE_ONLY_NOT_INDEPENDENT",
        "requests_hash": package["manifest"]["requests_hash"],
        "provider_response_hash": hash_obj(response),
        "provider_receipt_hash": receipt["receipt_hash"],
        "provider_draft_hash": hash_obj(draft),
        "calibration_receipt_hash": (hash_obj(calibration) if calibration else None),
        "catalog_hash": hash_obj(catalog),
        "atms_support_plan_hash": hash_obj(supports),
        "composed_candidates_hash": hash_obj(composed),
        "atms_selection_hash": hash_obj(selection),
        "views": {"S": views["S"]["view_hash"]},
        "S": {
            "selection": list(selected),
            "admitted": [allowed[item] for item in selected],
            "rejected_by_atms": sorted(rejected),
            "rationale": draft["rationale"],
            "falsifier": draft["falsifier"],
            "next_test": draft["next_test"],
            "unknowns": draft["unknowns"],
            "state": ("STRUCTURE_SELECTED_NOT_SIMULATED" if selected
                      else "ABSTAINED_NO_STRUCTURE")}}
    no_hidden(seal)
    seal["handoff_hash"] = hash_obj(seal)
    return seal


def verify_s_only_seal(seal: dict, package: dict, catalog: dict, views: dict,
                       composed: dict, supports: dict, response: dict,
                       draft: dict, receipt: dict,
                       calibration: dict | None = None) -> None:
    check(seal.get("handoff_hash") == hash_obj({
        k: v for k, v in seal.items() if k != "handoff_hash"}),
        "S_HANDOFF_TAMPERED")
    check(seal == seal_s_only(package, catalog, views, composed, supports,
                             response, draft, receipt, calibration=calibration),
          "S_HANDOFF_DEPENDENCY_MISMATCH")


def main() -> None:
    p = argparse.ArgumentParser(description="S-only capture/verification/handoff")
    actions = p.add_subparsers(dest="action", required=True)
    capture = actions.add_parser("capture")
    for name in ("package", "catalog", "out-dir", "run-ref", "authorization"):
        capture.add_argument("--" + name, required=True)
    seal = actions.add_parser("seal")
    for name in ("package", "catalog", "views-dir", "composed",
                 "supports", "archive", "out"):
        seal.add_argument("--" + name, required=True)
    seal.add_argument("--calibration", type=str)
    args = p.parse_args()
    read = lambda path: json.loads(Path(path).read_text(encoding="utf-8"))
    if args.action == "capture":
        out = capture_s(read(args.package), read(args.catalog),
                        authorization=args.authorization,
                        out_dir=Path(args.out_dir), run_ref=args.run_ref)
    else:
        archive = Path(args.archive)
        out = seal_s_only(
            read(args.package), read(args.catalog),
            {"S": read(Path(args.views_dir)/"S.json")},
            read(args.composed), read(args.supports),
            read(archive/"response.json"), read(archive/"s-draft.json"),
            read(archive/"receipt.json"),
            calibration=read(args.calibration) if args.calibration else None)
        exclusive_json(Path(args.out), out)
    print(json.dumps({"status": "S_ONLY_CAPTURED" if args.action == "capture"
                      else "S_ONLY_HANDOFF_LOCKED_NOT_EVALUATED",
                      "hash": out.get("receipt_hash", out.get("handoff_hash"))}))


if __name__ == "__main__":
    main()
