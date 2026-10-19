"""Run the synthetic F0 vertical wiring probe without hiding missing engines."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "data" / "synthetic" / "source.txt"
CLAIM_PATH = ROOT / "data" / "synthetic" / "claim.json"
MODEL_PATH = ROOT / "spike" / "f0_vertical" / "F0ToyStock.mo"
CANDIDATE_PATH = ROOT / "spike" / "f0_vertical" / "candidate-stub.json"
OUTPUT_DIR = ROOT / "artifacts" / "f0"


def overall_status(stages: list[dict]) -> str:
    states = {stage["status"] for stage in stages}
    if "FAIL" in states:
        return "FAIL"
    if states & {"PENDING", "STUB", "NOT_RUN"}:
        return "BLOCKED"
    return "PASS"


def source_and_annotation() -> tuple[list[dict], dict]:
    source_bytes = SOURCE_PATH.read_bytes()
    source_text = source_bytes.decode("utf-8")
    claim = json.loads(CLAIM_PATH.read_text(encoding="utf-8"))
    quote = claim["quote"]
    offset = source_text.find(quote)
    if offset < 0:
        return ([{"stage": "source_ingest", "status": "FAIL",
                  "reason": "claim quote is not present in source"}], {})

    source_hash = hashlib.sha256(source_bytes).hexdigest()
    source_stage = {
        "stage": "source_ingest_and_anchor",
        "status": "PASS",
        "source_id": claim["source_id"],
        "source_sha256": source_hash,
        "quote_start": offset,
        "quote_end": offset + len(quote),
        "synthetic": bool(claim.get("synthetic")),
    }
    annotation = {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "id": "annotation-synthetic-001",
        "type": "Annotation",
        "motivation": "assessing",
        "body": {"id": claim["claim_id"], "type": "TextualBody",
                 "value": quote, "purpose": "tagging"},
        "target": {
            "source": claim["source_id"],
            "selector": {"type": "TextQuoteSelector", "exact": quote},
        },
        "_fixture": {"synthetic": True, "source_sha256": source_hash},
    }
    annotation_stage = {
        "stage": "web_annotation_shape",
        "status": "PENDING",
        "reason": "JSON shape emitted, but no Web Annotation validator is installed or run",
        "draft_artifact": "annotation-draft.json",
    }
    return [source_stage, annotation_stage], annotation


def dependency_stage(stage: str, modules: list[str], commands: list[str] | None = None) -> dict:
    missing_modules = [name for name in modules if importlib.util.find_spec(name) is None]
    missing_commands = [name for name in (commands or []) if shutil.which(name) is None]
    missing = missing_modules + missing_commands
    return {
        "stage": stage,
        "status": "PENDING" if missing else "NOT_RUN",
        "reason": ("required component(s) unavailable: " + ", ".join(missing))
        if missing else "components are present, but this spike has no configured adapter",
        "missing": missing,
    }


def run_openmodelica() -> dict:
    omc = shutil.which("omc")
    if not omc:
        return {"stage": "openmodelica_compile_and_simulate", "status": "PENDING",
                "reason": "omc was not found on PATH; no compilation or simulation was run"}

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    model_file = json.dumps(MODEL_PATH.as_posix())
    prefix = "f0_toy_stock"
    mos_path = OUTPUT_DIR / "simulate.mos"
    mos_path.write_text(
        f"loadFile({model_file});\n"
        "getErrorString();\n"
        f"simulate(F0ToyStock, startTime=0.0, stopTime=10.0, numberOfIntervals=100, outputFormat=\"csv\", fileNamePrefix=\"{prefix}\");\n"
        "getErrorString();\n",
        encoding="utf-8",
    )
    try:
        completed = subprocess.run(
            [omc, str(mos_path)], cwd=OUTPUT_DIR, capture_output=True,
            text=True, timeout=120, check=False,
        )
    except subprocess.TimeoutExpired as exc:
        (OUTPUT_DIR / "omc.log").write_text(str(exc), encoding="utf-8")
        return {"stage": "openmodelica_compile_and_simulate", "status": "FAIL",
                "reason": "omc timed out after 120 seconds"}

    log = completed.stdout + "\n--- STDERR ---\n" + completed.stderr
    (OUTPUT_DIR / "omc.log").write_text(log, encoding="utf-8")
    csv_path = OUTPUT_DIR / f"{prefix}_res.csv"
    errors = "Error:" in log or "Error:" in completed.stderr
    if completed.returncode != 0 or errors or not csv_path.is_file():
        return {"stage": "openmodelica_compile_and_simulate", "status": "FAIL",
                "reason": "omc did not produce a successful result CSV",
                "return_code": completed.returncode, "log": "omc.log"}
    return {"stage": "openmodelica_compile_and_simulate", "status": "PASS",
            "model": str(MODEL_PATH.relative_to(ROOT)), "log": "omc.log",
            "csv": str(csv_path.relative_to(ROOT))}


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stages, annotation = source_and_annotation()
    if annotation:
        (OUTPUT_DIR / "annotation-draft.json").write_text(
            json.dumps(annotation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    stages.extend([
        dependency_stage("rdf_crminf_prov_and_shacl", ["rdflib", "pyshacl"]),
        dependency_stage("sparql_query", ["rdflib"]),
        {"stage": "atms_reasoning", "status": "PENDING",
         "reason": "no ATMS implementation selected or installed"},
        {"stage": "system_model_candidate_and_handoff", "status": "STUB",
         "reason": "candidate is a labeled contract stub; no candidate is promoted",
         "stub_artifact": str(CANDIDATE_PATH.relative_to(ROOT))},
        run_openmodelica(),
        {"stage": "cloudflare_d1_r2_persistence", "status": "NOT_RUN",
         "reason": "cloud resources are out of scope for this local synthetic spike"},
    ])
    report = {
        "schema": "igc-f0-spike-report/0.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_status": overall_status(stages),
        "claim": "Synthetic wiring probe only; not evidence about a real system.",
        "stages": stages,
    }
    report_path = OUTPUT_DIR / "run.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({"overall_status": report["overall_status"], "report": str(report_path),
                      "stages": stages}, ensure_ascii=False, indent=2))
    return 0 if report["overall_status"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
