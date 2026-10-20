"""Check provenance and distinct synthetic traces from the short-wrapper PoC."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POC = ROOT / "poc/short_wrappers"
RESULTS = ROOT / "artifacts/fm-b-wrapper-poc"


def load_trace(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 101:
        raise SystemExit(f"{path.name}: expected 101 samples, got {len(rows)}")
    if "time" not in rows[0] or "delivered" not in rows[0]:
        raise SystemExit(f"{path.name}: required output columns missing")
    for row in rows:
        for column in ("time", "delivered"):
            if not math.isfinite(float(row[column])):
                raise SystemExit(f"{path.name}: non-finite {column}")
    return rows


def main() -> None:
    manifest = json.loads((POC / "provenance.json").read_text(encoding="utf-8"))
    source_hashes = {}
    for entry in manifest["files"]:
        path = POC / entry["path"]
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != entry["sha256"]:
            raise SystemExit(f"source digest mismatch: {entry['path']}")
        source_hashes[entry["path"]] = actual

    base = load_trace(RESULTS / "wrapper-cs01_res.csv")
    serial = load_trace(RESULTS / "wrapper-cs02_res.csv")
    base_values = [float(row["delivered"]) for row in base]
    serial_values = [float(row["delivered"]) for row in serial]
    max_abs_difference = max(abs(a - b) for a, b in zip(base_values, serial_values))
    if max_abs_difference <= 1e-9:
        raise SystemExit("one-stage and two-stage delivered traces are indistinguishable")

    report = {
        "status": "SHORT_WRAPPER_POC_PASS_SYNTHETIC",
        "source_hashes": source_hashes,
        "topologies": ["WrapperCS01", "WrapperCS02"],
        "samples_per_topology": len(base),
        "max_abs_delivered_difference": max_abs_difference,
        "final_delivered": {
            "one_stage": base_values[-1],
            "two_stage": serial_values[-1],
        },
        "empirical_or_causal_claim": False,
        "runtime_admission": manifest["runtime_admission"],
        "license_review": manifest["license_review"],
    }
    (RESULTS / "wrapper-poc-report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
