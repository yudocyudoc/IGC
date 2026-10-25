"""Single-attempt GitHub Actions diagnostic for an already-frozen GLM-5.3 prompt.

No automatic retry, no mutation of Arena NW2 captures, no holdout access.
Uses repo Actions secrets only. Any provider error or invalid S JSON is a
reported failure and NOT a scientific abstention.
"""
from __future__ import annotations

import json
import os
import re
import sys
from hashlib import sha256
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / "data/diagnostics/glm53_nw2_config_probe_request.json"
MODEL = "@cf/zai-org/glm-5.3-flash"
ALLOWED = {"urn:igc:candidate:CS-01", "urn:igc:candidate:CS-02"}
RESULT = Path("artifacts/glm53-nw2-github-probe/provider-result.json")
SCHEMA = "igc-glm53-github-probe/0.1"


def canonical(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def parse_selection(response_content: str) -> dict:
    if not isinstance(response_content, str) or not response_content.strip():
        raise ValueError("EMPTY_MODEL_RESPONSE")
    text = response_content.strip()
    if text.startswith("```"):
        match = re.fullmatch(r"```(?:json)?\s*([\s\S]*?)\s*```", text, flags=re.I)
        if match is None:
            raise ValueError("INVALID_JSON_FENCE")
        text = match.group(1).strip()
    try:
        parsed = json.loads(text)
    except ValueError as exc:
        raise ValueError("INVALID_JSON") from exc
    if not isinstance(parsed, dict) or set(parsed) != {
        "selected_candidate_ids", "rationale", "falsifier", "unknowns", "next_test"
    }:
        raise ValueError("INVALID_S_SCHEMA")
    ids = parsed["selected_candidate_ids"]
    if not isinstance(ids, list) or any(not isinstance(i, str) for i in ids):
        raise ValueError("INVALID_S_SELECTION")
    if len(ids) != len(set(ids)) or not set(ids) <= ALLOWED:
        raise ValueError("UNKNOWN_OR_DUPLICATE_CANDIDATE")
    if any(not isinstance(parsed[k], str) or not parsed[k].strip()
           for k in ("rationale", "falsifier", "next_test")):
        raise ValueError("INVALID_S_ARGUMENTS")
    if not isinstance(parsed["unknowns"], list) or any(
        not isinstance(v, str) for v in parsed["unknowns"]
    ):
        raise ValueError("INVALID_S_UNKNOWNS")
    return parsed


def validate_request(pkg: dict) -> dict:
    if (pkg.get("schema") != "igc-nw2-config-probe/0.1"
            or pkg.get("round_id") != "ARENA-GLM53-NW2-20261024"
            or pkg.get("model") != MODEL
            or pkg.get("purpose") != "CONFIGURATION_ONLY_NOT_ARENA_RETRY_OR_S_SUBMISSION"
            or pkg.get("attempts_allowed") != 1 or pkg.get("retries_allowed") != 0
            or pkg.get("frozen_before_call") is not True
            or pkg.get("holdout_status") != "NOT_ACCESSED"):
        raise ValueError("FROZEN_REQUEST_CONTRACT_MISMATCH")
    body = pkg.get("body")
    if (not isinstance(body, dict)
            or body.get("temperature") != 0
            or body.get("reasoning_effort") != "low"
            or body.get("max_completion_tokens") != 4096
            or len(body.get("messages", [])) != 2
            or [x.get("role") for x in body["messages"]] != ["system", "user"]
            or not all(isinstance(x.get("content"), str) and x["content"] for x in body["messages"])
            or "IGC-NW2-INDEPENDENT-PULSE" not in body["messages"][1]["content"]):
        raise ValueError("FROZEN_BODY_CONTRACT_MISMATCH")
    return body


def write_status(status: dict) -> None:
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    with RESULT.open("x", encoding="utf-8", newline="\n") as file:
        json.dump(status, file, ensure_ascii=False, sort_keys=True, indent=2)
        file.write("\n")


def execute() -> int:
    pkg = json.loads(REQUEST.read_text(encoding="utf-8"))
    body = validate_request(pkg)
    run_attempt = os.environ.get("GITHUB_RUN_ATTEMPT", "1")
    run_id = os.environ.get("GITHUB_RUN_ID")
    status: dict = {
        "schema": SCHEMA, "purpose": pkg["purpose"], "round_id": pkg["round_id"],
        "model": MODEL, "request_body_sha256": "sha256:" + sha256(canonical(body)).hexdigest(),
        "run_id": run_id, "run_attempt": run_attempt, "max_provider_calls": 1,
        "provider_calls_attempted": 0, "retries": 0,
        "formal_s_submission": False, "prediction_lock_created": False,
        "holdout_accessed": False, "source": "GitHub Actions one-shot HTTPS request",
        "status": "NOT_STARTED",
    }
    if run_attempt != "1":
        status["status"] = "GUARD_RERUN_FORBIDDEN"
        write_status(status)
        print(status["status"])
        return 1
    account = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    if not re.fullmatch(r"[a-fA-F0-9]{32}", account):
        status["status"] = "CONFIG_MISSING_OR_INVALID_CLOUDFLARE_ACCOUNT_ID"
        write_status(status)
        print(status["status"])
        return 1
    if not token:
        status["status"] = "CONFIG_MISSING_CLOUDFLARE_API_TOKEN"
        write_status(status)
        print(status["status"])
        return 1
    url = f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{MODEL}"
    request = Request(url, data=canonical(body), method="POST",
                      headers={"Authorization": "Bearer " + token,
                               "Content-Type": "application/json", "Accept": "application/json"})
    status["provider_calls_attempted"] = 1
    try:
        with urlopen(request, timeout=150) as stream:
            http_status = stream.status
            response = json.load(stream)
    except HTTPError as exc:
        status["http_status"] = exc.code
        status["status"] = ("RATE_LIMITED_NO_RETRY" if exc.code == 429
                            else "PROVIDER_HTTP_ERROR_NO_RETRY")
        status["error_class"] = "HTTPError"
        # Do not log HTTP response body or any secrets.
        write_status(status)
        print(f'{status["status"]} HTTP_{exc.code}')
        return 1
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        status["status"] = "TRANSPORT_OR_RESPONSE_ERROR_NO_RETRY"
        status["error_class"] = type(exc).__name__
        write_status(status)
        print(status["status"])
        return 1
    status["http_status"] = http_status
    if not isinstance(response, dict) or response.get("success") is not True:
        status["status"] = "PROVIDER_UNSUCCESSFUL_NO_RETRY"
        write_status(status)
        print(status["status"])
        return 1
    obj = response.get("result")
    if not isinstance(obj, dict) or obj.get("model") != MODEL:
        status["status"] = "MODEL_MISMATCH"
        write_status(status)
        print(status["status"])
        return 1
    choices = obj.get("choices")
    first = choices[0] if isinstance(choices, list) and choices else {}
    message = first.get("message", {}) if isinstance(first, dict) else {}
    content = message.get("content") if isinstance(message, dict) else None
    status.update({
        "provider_request_id": obj.get("id"), "finish_reason": first.get("finish_reason"),
        "usage": obj.get("usage"), "content": content,
        "reasoning_content_present": bool(message.get("reasoning_content")) if isinstance(message, dict) else False,
        "reasoning_content_stored": False,
    })
    try:
        selection = parse_selection(content)
        if first.get("finish_reason") != "stop":
            raise ValueError("RESPONSE_NOT_FINISHED")
    except ValueError as exc:
        status["status"] = "UNUSABLE_S_JSON"
        status["validation_error"] = str(exc)
        write_status(status)
        print(status["status"], status["validation_error"])
        return 1
    status["status"] = "VALID_DIAGNOSTIC_JSON_NOT_ARENA_SUBMISSION"
    status["selected_candidate_ids"] = selection["selected_candidate_ids"]
    write_status(status)
    print(status["status"], "selected_count=" + str(len(selection["selected_candidate_ids"])))
    return 0


if __name__ == "__main__":
    sys.exit(execute())
