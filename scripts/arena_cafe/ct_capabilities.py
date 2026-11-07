"""CT-01: read-only access map for historical D2/M2/B5/R4.

A repository source Git blob is verified locally. GitHub Actions artifact
metadata is NOT a verification of the internal archived bytes. No legacy
experiment is repeated, and this is not a new scientific comparison.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "experiments/cafeteria/CT01_HISTORICAL_CAPABILITIES_2026-11-07.json"


def git_blob(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def load_index(index: Path = INDEX, root: Path = ROOT) -> dict:
    data = json.loads(index.read_text(encoding="utf-8"))
    if data["schema"] != "igc-ct01-historical-capability-access/1.0":
        raise ValueError("CT01_INVALID_INDEX_SCHEMA")
    found = {item["id"] for item in data["capabilities"]}
    if found != {"D2", "M2", "B5", "R4"} or len(data["capabilities"]) != 4:
        raise ValueError("CT01_FOUR_ORIGINAL_CAPABILITIES_REQUIRED")
    for entry in data["capabilities"]:
        path = root / entry["source_path"]
        if not path.is_file() or git_blob(path) != entry["source_git_blob"]:
            raise ValueError("CT01_ORIGINAL_METHOD_SOURCE_DRIFT:" + entry["id"])
        if not entry["artifacts"] or any(a.get("id") is None or not a.get("expires_at")
                                         for a in entry["artifacts"]):
            raise ValueError("CT01_ARTIFACT_METADATA_INCOMPLETE:" + entry["id"])
        if not entry.get("adapter") or not entry.get("contract"):
            raise ValueError("CT01_CONTRACT_INCOMPLETE:" + entry["id"])
    return data


def applicability(capability_id: str, context: dict, data: dict) -> dict:
    entries = {x["id"]: x for x in data["capabilities"]}
    if capability_id not in entries:
        raise ValueError("CT01_UNKNOWN_CAPABILITY")
    if type(context) is not dict:
        raise ValueError("CT01_CONTEXT_REQUIRED")
    if capability_id == "D2":
        if not context.get("reset_trial_authenticated"):
            status = "NOT_APPLICABLE_MISSING_RESET_TRIAL"
        elif not all(context.get(k) for k in ("d1_parent_authenticated", "grid_declared", "uncertainty_declared")):
            status = "NOT_APPLICABLE_MISSING_D1_CONTRACT"
        else:
            status = "CONTRACT_PRECONDITIONS_DECLARED_NOT_EXECUTED"
    elif capability_id == "M2":
        if not context.get("own_parent_authenticated"):
            status = "NOT_APPLICABLE_MISSING_OWN_PARENT"
        elif not {2.0, 4.0}.issubset(set(context.get("observation_times_h", []))):
            status = "NOT_APPLICABLE_MISSING_LATE_OBSERVATIONS"
        else:
            status = "NEW_CASE_REQUIRES_VERSIONED_WRAPPER_NOT_HISTORICAL_REPLAY"
    elif capability_id == "B5":
        status = "HISTORICAL_ONLY_NOT_A_PARENT_FOR_CURRENT_CASE"
    else:
        status = "HISTORICAL_LOCK_ADJUDICATION_PROTOCOL_ONLY"
    return {
        "capability": capability_id, "status": status,
        "method_source_sha1_verified": True,
        "historical_run_id": entries[capability_id]["run_id"],
        "artifact_internal_bytes_verified": False,
        "experimental_result_reproduced": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    data = load_index()
    report = {"schema": "igc-ct01-source-contract-check/1.0",
              "count": 4, "no_provider_or_omc": True,
              "metadata_not_archive_byte_verification": True,
              "ct03_d2": applicability("D2", {}, data),
              "capabilities": [e["id"] for e in data["capabilities"]]}
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
