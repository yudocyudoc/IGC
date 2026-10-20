"""Verify generated molecular topology provenance and OpenModelica traces."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POC = ROOT / "poc/short_wrappers"
RESULTS = ROOT / "artifacts/fm-b-molecular-composer"


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def load_trace(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 102 or not rows:
        raise SystemExit(f"{path.name}: expected 102 samples, got {len(rows)}")
    if not {"time", "delivered"}.issubset(rows[0]):
        raise SystemExit(f"{path.name}: required output columns missing")
    for row in rows:
        if not all(math.isfinite(float(row[key])) for key in ("time", "delivered")):
            raise SystemExit(f"{path.name}: non-finite output")
    return rows


def main() -> None:
    manifest = json.loads((POC / "provenance.json").read_text(encoding="utf-8"))
    source_hashes = {}
    for entry in manifest["files"]:
        actual = hashlib.sha256((POC / entry["path"]).read_bytes()).hexdigest()
        if actual != entry["sha256"]:
            raise SystemExit(f"source digest mismatch: {entry['path']}")
        source_hashes[entry["path"]] = "sha256:" + actual

    report = json.loads((RESULTS / "composition-report.json").read_text(encoding="utf-8"))
    candidates_path = RESULTS / "composed_candidates.json"
    modelica_path = RESULTS / "GeneratedMolecularCandidates.mo"
    mos_path = RESULTS / "run-composed-models.mos"
    if report["composed_candidates_sha256"] != sha256(candidates_path):
        raise SystemExit("composed candidate digest mismatch")
    if report["generated_modelica_sha256"] != sha256(modelica_path):
        raise SystemExit("generated Modelica digest mismatch")
    if report["generated_openmodelica_script_sha256"] != sha256(mos_path):
        raise SystemExit("generated OpenModelica script digest mismatch")
    if report["status"] != "B1_COMPOSITION_READY_FOR_EXECUTION":
        raise SystemExit("composition report is not ready")
    if len(set(report["structural_hashes"])) != len(report["structural_hashes"]):
        raise SystemExit("composed candidates do not have distinct topology hashes")

    log_text = (RESULTS / "openmodelica.log").read_text(encoding="utf-8", errors="replace")
    for model in report["generated_models"]:
        if f"Check of {model} completed successfully" not in log_text:
            raise SystemExit(f"OpenModelica did not successfully check {model}")
    traces = [load_trace(RESULTS / f"{prefix}_res.csv") for prefix in report["result_prefixes"]]
    if len(traces) < 2:
        raise SystemExit("at least two generated candidates are required for this PoC")
    reference_times = [row["time"] for row in traces[0]]
    if any([row["time"] for row in trace] != reference_times for trace in traces[1:]):
        raise SystemExit("simulation time grids differ")
    values = [[float(row["delivered"]) for row in trace] for trace in traces]
    difference = max(abs(left - right) for left, right in zip(values[0], values[1]))
    if difference <= 1e-9:
        raise SystemExit("generated topologies have indistinguishable delivered traces")

    result = {
        "status": "B1_MOLECULAR_COMPOSITION_PASS_SYNTHETIC",
        "plan_id": report["plan_id"],
        "candidate_ids": report["candidate_ids"],
        "stage_counts": report["stage_counts"],
        "structural_hashes": report["structural_hashes"],
        "source_hashes": source_hashes,
        "generated_modelica_sha256": report["generated_modelica_sha256"],
        "samples_per_candidate": len(traces[0]),
        "max_abs_delivered_difference": difference,
        "final_delivered": {report["candidate_ids"][0]: values[0][-1],
                            report["candidate_ids"][1]: values[1][-1]},
        "empirical_or_causal_claim": False,
        "license_review": manifest["license_review"],
        "runtime_admission": manifest["runtime_admission"],
    }
    (RESULTS / "verification-report.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
