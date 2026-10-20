"""Generate and simulate a traceable synthetic SystemModelCandidate handoff."""
from __future__ import annotations

import copy
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_PATH = ROOT / "data" / "synthetic" / "system_model_candidate.json"
CLAIM_PATH = ROOT / "data" / "synthetic" / "claim.json"
SOURCE_PATH = ROOT / "data" / "synthetic" / "source.txt"
OUTPUT_DIR = ROOT / "artifacts" / "f0" / "candidate-handoff"
DURATION_HOURS = 10.0


class HandoffError(ValueError):
    """The synthetic candidate cannot be safely transformed."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_candidate(candidate: dict[str, Any], claim: dict[str, Any], source_text: str) -> dict[str, Any]:
    if candidate.get("schema") != "igc-system-model-candidate/0.2":
        raise HandoffError("unsupported candidate schema")
    if candidate.get("entity_type") != "SystemModelCandidate":
        raise HandoffError("candidate must be typed as SystemModelCandidate")
    if claim.get("entity_type") != "ClaimOccurrence":
        raise HandoffError("source entity must be typed as ClaimOccurrence")
    if candidate.get("synthetic") is not True or claim.get("synthetic") is not True:
        raise HandoffError("this integration gate accepts synthetic fixtures only")
    if candidate.get("source_claim_id") != claim.get("claim_id"):
        raise HandoffError("candidate source_claim_id does not resolve to the claim fixture")
    quote = claim.get("quote")
    if not isinstance(quote, str) or not quote or source_text.count(quote) != 1:
        raise HandoffError("claim quote must occur exactly once in the source fixture")
    offset = source_text.index(quote)

    mechanism = candidate.get("mechanism_hypothesis")
    if not isinstance(mechanism, dict) or mechanism.get("claim_id") != claim.get("claim_id"):
        raise HandoffError("mechanism hypothesis must reference the candidate claim")
    assumptions = candidate.get("assumptions")
    if not isinstance(assumptions, list) or not assumptions:
        raise HandoffError("candidate must declare assumptions")
    by_id = {}
    for item in assumptions:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
            raise HandoffError("each assumption must have a stable id")
        if item["id"] in by_id:
            raise HandoffError("assumption ids must be unique")
        if item.get("synthetic") is not True:
            raise HandoffError("all parameters in this gate must be explicitly synthetic")
        value = item.get("value")
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
            raise HandoffError(f"assumption {item['id']} must have a finite numeric value")
        if value < 0:
            raise HandoffError(f"assumption {item['id']} cannot be negative")
        by_id[item["id"]] = item
    referenced = mechanism.get("assumption_ids")
    if not isinstance(referenced, list) or set(referenced) != set(by_id):
        raise HandoffError("mechanism assumption references must resolve exactly to declared assumptions")

    structure = candidate.get("structure")
    if not isinstance(structure, dict) or structure.get("kind") != "single_stock":
        raise HandoffError("only the single_stock synthetic structure is supported")
    stock = structure.get("stock")
    if not isinstance(stock, dict) or stock.get("unit") != "orders":
        raise HandoffError("stock must declare unit 'orders'")
    if not isinstance(stock.get("initial_value"), (int, float)) or isinstance(stock.get("initial_value"), bool):
        raise HandoffError("stock initial_value must be numeric")
    inflow = structure.get("inflow")
    outflow = structure.get("outflow")
    for flow, role in ((inflow, "inflow"), (outflow, "outflow")):
        if not isinstance(flow, dict) or flow.get("unit") != "orders/hour":
            raise HandoffError(f"{role} must declare rate unit 'orders/hour'")
        assumption = by_id.get(flow.get("assumption_id"))
        if assumption is None:
            raise HandoffError(f"{role} references an undeclared assumption")
        expected_parameter = "arrivalRate" if role == "inflow" else "completionRate"
        if (assumption.get("role") != role or assumption.get("unit") != flow["unit"]
                or assumption.get("parameter") != expected_parameter):
            raise HandoffError(f"{role} assumption role/parameter/unit does not match the flow")
    return {
        "source_claim_id": claim["claim_id"],
        "source_id": claim.get("source_id"),
        "quote": quote,
        "quote_start": offset,
        "quote_end": offset + len(quote),
        "assumption_map": by_id,
    }


def render_model(candidate: dict[str, Any], model_name: str) -> str:
    params = {item["id"]: item for item in candidate["assumptions"]}
    inflow_id = candidate["structure"]["inflow"]["assumption_id"]
    outflow_id = candidate["structure"]["outflow"]["assumption_id"]
    stock = candidate["structure"]["stock"]
    arrival = params[inflow_id]["value"]
    completion = params[outflow_id]["value"]
    initial = stock["initial_value"]
    return (
        "within ;\n"
        f"model {model_name}\n"
        "  // Synthetic generated fixture; not an empirical or causal model.\n"
        f"  // Candidate: {candidate['candidate_id']}\n"
        f"  // Mechanism hypothesis: {candidate['mechanism_hypothesis']['id']}\n"
        f"  // Inflow assumption: {inflow_id}\n"
        f"  // Outflow assumption: {outflow_id}\n"
        f"  parameter Real arrivalRate = {float(arrival):.12g};\n"
        f"  parameter Real completionRate = {float(completion):.12g};\n"
        f"  Real {stock['name']}(start={float(initial):.12g}, fixed=true);\n"
        "equation\n"
        f"  der({stock['name']}) = arrivalRate - completionRate;\n"
        f"end {model_name};\n"
    )


def _csv_final_stock(path: Path, stock_name: str) -> float:
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if not rows or stock_name not in rows[-1]:
        raise HandoffError(f"simulation result is missing {stock_name}")
    return float(rows[-1][stock_name])


def _run_openmodelica(output_dir: Path, image: str | None) -> tuple[str, str]:
    docker = shutil.which("docker")
    omc = shutil.which("omc")
    if image and not docker:
        raise HandoffError("Docker is configured but unavailable")
    if not image and not omc:
        raise HandoffError("OpenModelica is unavailable")
    base_path = output_dir / "CandidateBase.mo"
    changed_path = output_dir / "CandidatePerturbed.mo"
    mos_path = output_dir / "simulate.mos"
    if image:
        base_arg = "/workspace/" + base_path.relative_to(ROOT).as_posix()
        changed_arg = "/workspace/" + changed_path.relative_to(ROOT).as_posix()
        mos_arg = "/workspace/" + mos_path.relative_to(ROOT).as_posix()
        workdir = "/workspace/" + output_dir.relative_to(ROOT).as_posix()
        command = [docker, "run", "--rm", "--volume", f"{ROOT}:/workspace",
                   "--workdir", workdir, image, "omc", mos_arg]
    else:
        base_arg, changed_arg = base_path.as_posix(), changed_path.as_posix()
        mos_arg = mos_path.as_posix()
        command = [omc, mos_arg]
    mos_path.write_text(
        f"loadFile({json.dumps(base_arg)});\n"
        "getErrorString();\n"
        "simulate(CandidateBase, startTime=0.0, stopTime=10.0, numberOfIntervals=100, outputFormat=\"csv\", fileNamePrefix=\"base\");\n"
        "getErrorString();\n"
        f"loadFile({json.dumps(changed_arg)});\n"
        "getErrorString();\n"
        "simulate(CandidatePerturbed, startTime=0.0, stopTime=10.0, numberOfIntervals=100, outputFormat=\"csv\", fileNamePrefix=\"perturbed\");\n"
        "getErrorString();\n",
        encoding="utf-8",
    )
    try:
        completed = subprocess.run(command, cwd=output_dir, capture_output=True, text=True,
                                   timeout=600 if image else 120, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise HandoffError(f"OpenModelica execution failed: {type(exc).__name__}") from exc
    log = completed.stdout + "\n--- STDERR ---\n" + completed.stderr
    (output_dir / "omc.log").write_text(log, encoding="utf-8")
    if completed.returncode != 0 or "Error:" in log:
        raise HandoffError("OpenModelica reported an error; see omc.log")
    base_csv = output_dir / "base_res.csv"
    changed_csv = output_dir / "perturbed_res.csv"
    if not base_csv.is_file() or not changed_csv.is_file():
        raise HandoffError("OpenModelica did not produce both simulation CSV files")
    return str(base_csv), str(changed_csv)


def run_candidate_handoff() -> dict[str, Any]:
    """Validate, generate, perturb, simulate and hash a synthetic candidate handoff."""
    stage = "system_model_candidate_and_handoff"
    try:
        candidate_bytes = CANDIDATE_PATH.read_bytes()
        claim_bytes = CLAIM_PATH.read_bytes()
        source_bytes = SOURCE_PATH.read_bytes()
        candidate = json.loads(candidate_bytes)
        claim = json.loads(claim_bytes)
        source_text = source_bytes.decode("utf-8")
        evidence = validate_candidate(candidate, claim, source_text)

        output_dir = OUTPUT_DIR
        output_dir.mkdir(parents=True, exist_ok=True)
        base_model = render_model(candidate, "CandidateBase")
        base_model_path = output_dir / "CandidateBase.mo"
        base_model_path.write_text(base_model, encoding="utf-8")

        changed = copy.deepcopy(candidate)
        inflow_id = changed["structure"]["inflow"]["assumption_id"]
        parameter = next(item for item in changed["assumptions"] if item["id"] == inflow_id)
        before = parameter["value"]
        parameter["value"] = before + 1
        changed_model = render_model(changed, "CandidatePerturbed")
        changed_model_path = output_dir / "CandidatePerturbed.mo"
        changed_model_path.write_text(changed_model, encoding="utf-8")

        base_csv, changed_csv = _run_openmodelica(output_dir, os.environ.get("IGC_OMC_DOCKER_IMAGE"))
        stock_name = candidate["structure"]["stock"]["name"]
        base_final = _csv_final_stock(Path(base_csv), stock_name)
        changed_final = _csv_final_stock(Path(changed_csv), stock_name)
        assumption_by_id = {item["id"]: item for item in candidate["assumptions"]}
        expected_base = candidate["structure"]["stock"]["initial_value"] + (
            assumption_by_id[candidate["structure"]["inflow"]["assumption_id"]]["value"]
            - assumption_by_id[candidate["structure"]["outflow"]["assumption_id"]]["value"]
        ) * DURATION_HOURS
        if not math.isclose(base_final, expected_base, rel_tol=1e-7, abs_tol=1e-7):
            raise HandoffError("base simulation output does not match the declared stock-flow equation")
        if math.isclose(base_final, changed_final, rel_tol=1e-7, abs_tol=1e-7):
            raise HandoffError("parameter perturbation did not change the simulated result")

        manifest = {
            "schema": "igc-candidate-handoff-evidence/0.1",
            "status": "PASS_SYNTHETIC_INTEGRATION_ONLY",
            "synthetic": True,
            "source": {"id": evidence["source_id"], "sha256": _sha256(source_bytes),
                       "quote_start": evidence["quote_start"], "quote_end": evidence["quote_end"]},
            "claim": {"id": evidence["source_claim_id"], "entity_type": claim["entity_type"],
                      "sha256": _sha256(claim_bytes)},
            "candidate": {"id": candidate["candidate_id"], "entity_type": candidate["entity_type"],
                          "sha256": _sha256(candidate_bytes)},
            "mechanism_hypothesis_id": candidate["mechanism_hypothesis"]["id"],
            "assumptions": [
                {"id": item["id"], "parameter": item["parameter"], "value": item["value"],
                 "unit": item["unit"], "synthetic": item["synthetic"]}
                for item in candidate["assumptions"]
            ],
            "generator_sha256": _sha256(Path(__file__).read_bytes()),
            "generated_models": {
                "base": {"path": str(base_model_path.relative_to(ROOT)),
                         "sha256": _sha256(base_model.encode("utf-8"))},
                "perturbed": {"path": str(changed_model_path.relative_to(ROOT)),
                              "parameter": parameter["parameter"], "before": before,
                              "after": parameter["value"],
                              "sha256": _sha256(changed_model.encode("utf-8"))},
            },
            "simulation": {
                "engine": os.environ.get("IGC_OMC_DOCKER_IMAGE", "omc on PATH"),
                "duration_hours": DURATION_HOURS,
                "base_result": {"path": str(Path(base_csv).relative_to(ROOT)),
                                "sha256": _sha256(Path(base_csv).read_bytes()),
                                "final_stock": base_final},
                "perturbed_result": {"path": str(Path(changed_csv).relative_to(ROOT)),
                                     "sha256": _sha256(Path(changed_csv).read_bytes()),
                                     "final_stock": changed_final},
                "output_changed": not math.isclose(base_final, changed_final,
                                                    rel_tol=1e-7, abs_tol=1e-7),
            },
            "interpretation": "Software wiring evidence only; no empirical fidelity or causal claim.",
        }
        manifest_path = output_dir / "handoff.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                                 encoding="utf-8")
        return {"stage": stage, "status": "PASS", "evidence": str(manifest_path.relative_to(ROOT)),
                "candidate_id": candidate["candidate_id"], "base_final_stock": base_final,
                "perturbed_final_stock": changed_final}
    except Exception as exc:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "handoff-error.json").write_text(
            json.dumps({"stage": stage, "status": "FAIL",
                        "reason": f"{type(exc).__name__}: {exc}"}, indent=2) + "\n",
            encoding="utf-8")
        return {"stage": stage, "status": "FAIL",
                "reason": f"{type(exc).__name__}: {exc}",
                "evidence": str((OUTPUT_DIR / "handoff-error.json").relative_to(ROOT))}
