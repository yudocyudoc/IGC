"""Arena S/P independent inference adapters, reusing the proven short EPI04 API shape.

This module NEVER infers by itself during preparation/tests. A user must explicitly
authorize a bounded 3-call run and configure existing Cloudflare API credentials.
Provider judgments are draft proposals, not Modelica models, truth or predictions.
"""
from __future__ import annotations
import argparse
import json
import os
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from typing import Any, Callable

from .arena_round import (SCHEMA as ROUND_SCHEMA, RoundError, canonical, hash_obj,
                          validate_spec, no_hidden, numbers, validate_submission)

SCHEMA = "igc-arena-sp-provider/0.1"
AUTHORIZATION = "RUN_ARENA_SP_MAX3"
MODELS = {
    "S_GLM": "@cf/zai-org/glm-5.3-flash",
    "P_CLEF": "@cf/cloudflare/clef",
    "P_CLAIRIC": "@cf/cloudflare/clairic",
}
ORDER = ("S_GLM", "P_CLEF", "P_CLAIRIC")
CHOICES = {
    "INSUFFICIENT": "Data cannot identify which causal topology generated the observable",
    "CS_01": "The visible evidence supports CS-01 more strongly, subject to explicit assumptions",
    "CS_02": "The visible evidence supports CS-02 more strongly, subject to explicit assumptions",
    "EQUIVALENT": "Candidates remain observationally equivalent within current measurements",
}


class ProviderError(ValueError):
    pass


def check_views(views: dict, spec: dict) -> None:
    validate_spec(spec)
    if not isinstance(views, dict) or not all(x in views for x in ("S", "P")):
        raise ProviderError("missing S/P views")
    for lane in ("S", "P"):
        view = views[lane]
        if view.get("lane") != lane or view.get("round_id") != spec["round_id"]:
            raise ProviderError("cross-lane or cross-round view")
        if view.get("spec_hash") != hash_obj(spec):
            raise ProviderError("spec mismatch")
        content = dict(view)
        digest = content.pop("view_hash", None)
        if digest != hash_obj(content):
            raise ProviderError("view hash mismatch")
        no_hidden(view)
    if views["S"]["primary_hash"] != views["P"]["primary_hash"]:
        raise ProviderError("unequal construction data")


def build_requests(views: dict, spec: dict, catalog: dict) -> dict:
    """Produce provider-ready, hash-pinned requests with no other lane's output."""
    check_views(views, spec)
    if catalog.get("schema") != "igc-arena-public-catalog/0.1" or catalog.get("synthetic") is not True:
        raise ProviderError("unsupported/non-synthetic public model catalog")
    if catalog.get("round_id") != spec["round_id"]:
        raise ProviderError("catalog from another round")
    no_hidden(catalog)
    candidates = catalog.get("candidates")
    if not isinstance(candidates, list) or len(candidates) < 2:
        raise ProviderError("at least two public candidate definitions required")
    ids = [item.get("candidate_id") for item in candidates if isinstance(item, dict)]
    if len(ids) != len(candidates) or not all(isinstance(x, str) and x for x in ids):
        raise ProviderError("invalid candidate definitions")
    if len(set(ids)) != len(ids):
        raise ProviderError("duplicate candidate identifiers")
    if any("predictions" in item or "outcome" in item for item in candidates):
        raise ProviderError("candidate catalog cannot leak model evaluation")
    for lane in ("S", "P"):
        if views[lane]["budget"]["llm_calls"] < (1 if lane == "S" else 2):
            raise ProviderError("requested calls exceed lane budget")
    construction = views["S"]["primary"]
    numeric = numbers(construction["values"])
    if len(numeric) < 2:
        raise ProviderError("two construction observations needed for Clairic check")
    # This is deliberately *not* a structural parameter estimate. Clairic
    # cross-checks only arithmetic on visible data.
    numeric_state = {
        "task": "calculate_last_observed_increment",
        "last_two_values": numeric[-2:],
        "units": spec["observability"]["unit"],
        "conventions": "last minus previous; no forecasting, no gold, no causal assertion",
    }
    s_state = {"question": spec["question"], "construction": construction,
               "observability": spec["observability"], "catalog": candidates,
               "retrieval": views["S"].get("retrieval"),
               "target_times": spec["target_times"],
               "task": "propose_and_criticize_causal_structures"}
    s_instructions = (
        "You are SD-AI proposing candidate system-dynamics mechanisms, not asserting truth. "
        "Use ONLY the candidate_id values in the public catalog. Never write Modelica "
        "or numeric trajectories. Return exactly one JSON object: "
        '{"selected_candidate_ids":["..."],"rationale":"...","falsifier":"...",'
        '"unknowns":["..."],"next_test":"..."}. '
        "You may select zero candidates if information is insufficient. "
        "Do not access reserve, other lane submissions, or hidden world parameters. "
        "State is: " + json.dumps(s_state, ensure_ascii=False, sort_keys=True)
    )
    p_context = {"question": spec["question"], "construction": views["P"]["primary"],
                 "candidates": candidates, "retrieval": views["P"].get("retrieval"),
                 "task": "assess_identifiability_not_truth"}
    p_state = json.dumps(p_context, ensure_ascii=False, sort_keys=True)
    bodies = {
        "S_GLM": {"messages": [{"role": "user", "content": s_instructions}],
                  "temperature": 0.1, "max_completion_tokens": 600,
                  "chat_template_kwargs": {"enable_thinking": False}},
        "P_CLEF": {"model": "clef", "state": p_state,
                   "questions": {"assessment": {"type": "choice",
                     "instructions": (
                         "Classify what the *visible construction evidence* permits. "
                         "Support is conditional, not causal truth. Choose one criterion."),
                     "criteria": CHOICES}}},
        "P_CLAIRIC": {"model": "clairic",
                      "state": json.dumps(numeric_state, ensure_ascii=False, sort_keys=True),
                      "fields": {"observed_increment": {"type": "number", "decimals": 4,
                                  "instructions": (
                                      "Compute exactly the last observation minus the previous "
                                      "observation. This is not a forecast or inferred parameter.")}}},
    }
    requests = []
    for name in ORDER:
        lane = "S" if name.startswith("S_") else "P"
        item = {"schema": SCHEMA, "round_id": spec["round_id"], "lane": lane,
                "view_hash": views[lane]["view_hash"],
                "model_name": name, "endpoint": MODELS[name], "body": bodies[name]}
        item["body_hash"] = hash_obj(item["body"])
        requests.append(item)
    manifest = {"schema": SCHEMA, "round_id": spec["round_id"],
                "catalog_hash": hash_obj(catalog),
                "spec_hash": hash_obj(spec),
                "view_hashes": {lane: views[lane]["view_hash"] for lane in ("S", "P")},
                "model_order": list(ORDER), "calls_planned": 3,
                "calls_made": 0, "authorization": "NO_INFERENCE",
                "requests_hash": hash_obj(requests)}
    return {"manifest": manifest, "requests": requests}


def _validate_schedule(package: dict) -> None:
    manifest, requests = package["manifest"], package["requests"]
    if (manifest.get("schema") != SCHEMA or manifest.get("calls_planned") != 3
        or manifest.get("calls_made") != 0 or manifest.get("authorization") != "NO_INFERENCE"):
        raise ProviderError("unapproved or previously executed schedule")
    if not isinstance(requests, list) or [r.get("model_name") for r in requests] != list(ORDER):
        raise ProviderError("provider schedule differs")
    if manifest.get("requests_hash") != hash_obj(requests):
        raise ProviderError("provider schedule tampered")
    for request in requests:
        model = request["model_name"]
        if (request.get("endpoint") != MODELS[model]
            or request.get("lane") != ("S" if model.startswith("S_") else "P")
            or hash_obj(request.get("body")) != request.get("body_hash")
            or request.get("round_id") != manifest["round_id"]
            or request.get("view_hash") != manifest["view_hashes"][request["lane"]]):
            raise ProviderError("provider request integrity failure")


def _unwrap(raw: dict) -> dict:
    if not isinstance(raw, dict) or raw.get("success") is False:
        raise ProviderError("unsuccessful provider response")
    result = raw.get("result", raw)
    if not isinstance(result, dict):
        raise ProviderError("invalid provider payload")
    return result



def parse_s_response(package: dict, response: dict, catalog: dict) -> dict:
    """Parse S independently of P, preserving the original strict candidate checks."""
    _validate_schedule(package)
    if hash_obj(catalog) != package["manifest"]["catalog_hash"]:
        raise ProviderError("catalog mismatch on S decoding")
    ids = {x["candidate_id"] for x in catalog["candidates"]}
    s = _unwrap(response)
    raw = s.get("response")
    if not isinstance(raw, str):
        choices = s.get("choices")
        if isinstance(choices, list) and choices and isinstance(choices[0], dict):
            raw = choices[0].get("message", {}).get("content")
    if not isinstance(raw, str):
        raise ProviderError("S response missing textual proposal")
    # Some real GLM responses wrap a valid JSON object in a markdown fence.
    # Remove only an entire enclosing fence; schema/IDs remain strictly checked.
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        import re
        match = re.fullmatch(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, flags=re.I)
        if match:
            cleaned = match.group(1).strip()
    try:
        s_out = json.loads(cleaned)
    except (TypeError, ValueError) as exc:
        raise ProviderError("S response is not JSON") from exc
    if not isinstance(s_out, dict):
        raise ProviderError("S must return a JSON object")
    chosen = s_out.get("selected_candidate_ids")
    if not isinstance(chosen, list) or not all(isinstance(x, str) for x in chosen):
        raise ProviderError("S candidate IDs must be a list of strings")
    if len(set(chosen)) != len(chosen) or not set(chosen) <= ids:
        raise ProviderError("S invented/duplicated candidate")
    for name in ("rationale", "falsifier", "next_test"):
        if not isinstance(s_out.get(name), str) or not s_out[name].strip():
            raise ProviderError(f"S missing {name}")
    if not isinstance(s_out.get("unknowns"), list) or not all(
       isinstance(x, str) for x in s_out["unknowns"]):
        raise ProviderError("S unknowns must be strings")

    return {"selected_candidate_ids": chosen,
            "rationale": s_out["rationale"], "falsifier": s_out["falsifier"],
            "unknowns": s_out["unknowns"], "next_test": s_out["next_test"]}


def parse_responses(package: dict, responses: dict[str, dict], catalog: dict) -> dict:
    _validate_schedule(package)
    if set(responses) != set(ORDER):
        raise ProviderError("three independent provider responses required")
    ids = {x["candidate_id"] for x in catalog["candidates"]}
    if hash_obj(catalog) != package["manifest"]["catalog_hash"]:
        raise ProviderError("catalog mismatch on decoding")
    s_out = parse_s_response(package, responses["S_GLM"], catalog)
    clef, clairic = (_unwrap(responses[k]) for k in ORDER[1:])
    a = clef.get("answers", {}).get("assessment", {})
    if not isinstance(a, dict) or a.get("choice") not in CHOICES:
        raise ProviderError("Clef missing approved assessment choice")
    p = a.get("probabilities")
    if p is not None and (not isinstance(p, dict) or set(p) != set(CHOICES)
       or any(type(x) not in (float, int) or not 0 <= x <= 1 for x in p.values())
       or abs(sum(p.values()) - 1) > .02):
        raise ProviderError("Clef reported invalid confidence distribution")
    n = clairic.get("answers", {}).get("observed_increment", {}).get("value")
    if type(n) not in (int, float):
        raise ProviderError("Clairic value must be numeric")
    numeric = numbers([n])[0]
    base = package["requests"][2]["body"]["state"]
    state = json.loads(base)
    expected = state["last_two_values"][-1] - state["last_two_values"][-2]
    valid_arithmetic = abs(numeric - expected) < 0.00011
    # An incorrect numerical result is explicitly flagged; it cannot become
    # a parameter estimate or correction of the observed construction data.
    output = {"schema": SCHEMA, "round_id": package["manifest"]["round_id"],
              "status": "PROVIDER_DRAFTS_NOT_LANE_SUBMISSIONS",
              "S": {"lane": "S", "status": "CANDIDATES_PROPOSED_NOT_SIMULATED",
                    "selected_candidate_ids": s_out["selected_candidate_ids"], "rationale": s_out["rationale"],
                    "falsifier": s_out["falsifier"], "unknowns": s_out["unknowns"],
                    "next_test": s_out["next_test"]},
              "P": {"lane": "P", "status": "JUDGEMENTS_NOT_TOPOLOGIES",
                    "support_assessment": a["choice"],
                    "confidence": p if p is not None else None,
                    "numeric_crosscheck": {"reported": numeric,
                                           "deterministic_expected": expected,
                                           "valid_arithmetic": valid_arithmetic}},
              "claims_of_truth": False, "predictions_generated": False,
              "requests_hash": package["manifest"]["requests_hash"],
              "response_hashes": {k: hash_obj(v) for k,v in responses.items()}}
    output["output_hash"] = hash_obj(output)
    return output


def run_authorized(package: dict, *, authorization: str, env: dict | None = None,
                   sender: Callable = urlopen, on_result: Callable | None = None,
                   clock: Callable = time.perf_counter) -> dict[str, dict]:
    """Bounded provider calls, no retries, never invoked by CI."""
    _validate_schedule(package)
    if authorization != AUTHORIZATION:
        raise ProviderError("NO_INFERENCE: explicit RUN_ARENA_SP_MAX3 required")
    env = os.environ if env is None else env
    account = env.get("CLOUDFLARE_ACCOUNT_ID", "")
    token = env.get("CLOUDFLARE_API_TOKEN", "")
    if not account or not token:
        raise ProviderError("NO_INFERENCE: Cloudflare API credentials unavailable")
    if not (len(account) == 32 and all(c in "0123456789abcdefABCDEF" for c in account)):
        raise ProviderError("NO_INFERENCE: invalid Cloudflare account ID")
    raw_results = {}
    for req in package["requests"]:
        url = (f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/"
               + req["endpoint"])
        request = Request(url, data=canonical(req["body"]), method="POST",
                          headers={"Authorization": "Bearer " + token,
                                   "Content-Type": "application/json", "Accept": "application/json"})
        started = clock()
        try:
            with sender(request, timeout=150) as response:
                raw_results[req["model_name"]] = json.load(response)
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            # Fail closed, no retries, no unauthorized fallbacks.
            raise ProviderError("PROVIDER_CALL_FAILED_NO_RETRY:" + type(exc).__name__) from None
        _unwrap(raw_results[req["model_name"]])
        if on_result is not None:
            # Callback errors abort the campaign; no subsequent call is made.
            on_result(req["model_name"], raw_results[req["model_name"]],
                      max(0.0, (clock() - started) * 1000.0))
    return raw_results


def main() -> int:
    p = argparse.ArgumentParser(description="S/P model proposal adapter; no automatic inference")
    commands = p.add_subparsers(dest="action", required=True)
    prep = commands.add_parser("prepare")
    prep.add_argument("--spec", type=Path, required=True)
    prep.add_argument("--views-dir", type=Path, required=True)
    prep.add_argument("--catalog", type=Path, required=True)
    prep.add_argument("--out", type=Path, required=True)
    parse = commands.add_parser("parse")
    for key in ("package", "responses", "catalog", "out"):
        parse.add_argument("--" + key, type=Path, required=True)
    call = commands.add_parser("infer")
    call.add_argument("--package", type=Path, required=True)
    call.add_argument("--authorization", required=True)
    call.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    load = lambda path: json.loads(path.read_text(encoding="utf-8"))
    if args.action == "prepare":
        pkg = build_requests({x:load(args.views_dir/(x+".json")) for x in ("S","P")},
                             load(args.spec), load(args.catalog))
        data = pkg
    elif args.action == "parse":
        data = parse_responses(load(args.package), load(args.responses), load(args.catalog))
    else:
        data = run_authorized(load(args.package), authorization=args.authorization)
    from .arena_round import exclusive_json
    exclusive_json(args.out, data)
    print(json.dumps({"status": "PREPARED_NO_INFERENCE" if args.action == "prepare"
                      else "PROVIDER_REQUESTS_COMPLETE" if args.action == "infer"
                      else "PROVIDER_DRAFTS_PARSED",
                      "file": str(args.out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
