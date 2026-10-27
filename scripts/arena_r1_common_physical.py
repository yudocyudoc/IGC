"""R1: physically evaluate D + restored M3 against ONE common construction input.

B stays blocked until a specific new Buffalo inference budget is authorized.
This module never invokes providers or solvers. The CI workflow executes
OpenModelica on the nine OWN candidates, then this module authenticates and
scores solver traces. No holdout, winner, or structural identification claims.
"""
from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import json
import math
from pathlib import Path

from scripts.arena_d_v01 import generate as generate_d, modelica as d_modelica, verify_csv
from scripts.arena_v0_common_evidence import prepare as prepare_evidence
from scripts.arena_v0_contract import canonical, digest
from scripts.arena_v0_first_round import run as first_round


SCHEMA = "igc-arena-r1-common-physical-construction/0.1"


def require(condition, code):
    if not condition:
        raise ValueError(code)


def bytes_hash(value):
    return "sha256:" + sha256(value).hexdigest()


def expected_d(source, assumptions):
    evidence = prepare_evidence(source, assumptions)
    derived = evidence["arms"]["D"]
    require(derived["status"] == "READY_CONDITIONAL_ASSUMPTIONS",
            "R1_D_NEEDS_EXPLICIT_NOMINAL_ASSUMPTIONS")
    native = generate_d(derived["derived_input"])
    return evidence, derived["derived_input"], native


def d_manifest(source, assumptions):
    evidence, data, native = expected_d(source, assumptions)
    specs = []
    for c in native["candidates"]:
        name = "DStockFlow_" + c["structure_hash"][7:19]
        model = d_modelica(c, data["construction"]["input_profile"])
        specs.append({
            "candidate_id": c["id"], "class": name,
            "modelica_file": name + ".mo",
            "modelica_sha256": bytes_hash(model.encode("utf-8")),
            "native_structure_sha256": c["structure_hash"],
            "g1_lint": c["lint"],
            "stock_count": len(c["structure"]["stocks"]),
            "has_loss": c["structure"]["loss"],
        })
    return {
        "schema": "igc-arena-r1-d-source-manifest/0.1",
        "common_input_hash": evidence["common_input_hash"],
        "source_snapshot_hash": evidence["source_snapshot_hash"],
        "derived_input_hash": digest(data),
        "native_sha256": digest(native),
        "assumptions": "DECLARED_NOMINAL_NOT_FITTED",
        "solver": {"image": "openmodelica/openmodelica:v1.27.1-minimal",
                   "method": "dassl", "start": 0, "stop": 8,
                   "intervals": 160, "tolerance": 1e-8},
        "candidates": specs,
    }


def prepare_d(source, assumptions, folder):
    folder = Path(folder)
    require(not folder.exists(), "R1_D_PREPARATION_EXISTS")
    manifest = d_manifest(source, assumptions)
    _, data, native = expected_d(source, assumptions)
    folder.mkdir(parents=True)
    commands = ['getVersion();']
    for c, spec in zip(native["candidates"], manifest["candidates"]):
        model = d_modelica(c, data["construction"]["input_profile"])
        (folder / spec["modelica_file"]).write_bytes(model.encode("utf-8"))
        name = spec["class"]
        path = "/repo/" + folder.as_posix().lstrip("/")
        commands.extend([
            f'loadFile("{path}/{name}.mo");',
            f'checkModel({name});',
            'print(getErrorString());',
            f'simulate({name},startTime=0,stopTime=8,numberOfIntervals=160,'
            f'method="dassl",tolerance=1e-8,outputFormat="csv",'
            f'fileNamePrefix="{path}/{name}");',
            'print(getErrorString());'
        ])
    (folder / "simulate.mos").write_text("\n".join(commands) + "\n")
    (folder / "manifest.json").write_bytes(canonical(manifest) + b"\n")
    return manifest


def checked_d_manifest(source, assumptions, folder):
    folder = Path(folder)
    declared = json.loads((folder / "manifest.json").read_text())
    expected = d_manifest(source, assumptions)
    require(declared == expected, "R1_D_MANIFEST_CHANGED_OR_WRONG_SOURCE")
    _, data, native = expected_d(source, assumptions)
    require(len(native["candidates"]) == len(expected["candidates"]),
            "R1_D_CANDIDATE_COUNT_CHANGED")
    for c, spec in zip(native["candidates"], expected["candidates"]):
        raw = (folder / spec["modelica_file"]).read_bytes()
        require(bytes_hash(raw) == spec["modelica_sha256"] and
                raw == d_modelica(c, data["construction"]["input_profile"]).encode("utf-8"),
                "R1_D_MODEL_CHANGED")
    return expected


def sampled_deliveries(path, times):
    with Path(path).open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    require(len(rows) >= 80, "R1_D_INSUFFICIENT_SOLVER_ROWS")
    values = []
    for t in times:
        hits = []
        for row in rows:
            sample_t, sample_y = float(row["time"]), float(row["delivered"])
            require(math.isfinite(sample_t) and math.isfinite(sample_y),
                    "R1_D_NONFINITE_SERIES")
            if abs(sample_t - t) < 1e-7:
                hits.append(sample_y)
        require(bool(hits), "R1_D_MISSING_SAMPLE_TIME")
        require(max(hits) - min(hits) < 1e-5,
                "R1_D_CONFLICTING_EVENT_TIME")
        values.append(hits[-1])
    return values


def assess(source, assumptions, *, d_root, m_root):
    """Fail closed unless the OWN original Modelica sources and CSVs are present."""
    d_root, m_root = Path(d_root), Path(m_root)
    manifest = checked_d_manifest(source, assumptions, d_root)
    common = first_round(source, assumptions, m_csv_root=m_root)
    assert common["source_snapshot_hash"] == manifest["source_snapshot_hash"]
    require(common["arms"]["D"]["native_sha256"] == manifest["native_sha256"] and
            common["arms"]["D"]["derived_input_hash"] == manifest["derived_input_hash"],
            "R1_D_COMMON_NATIVE_DIVERGED")
    observations = source["observations"]
    obs_times = [x["t"] for x in observations]
    observed = [x["delivered"] for x in observations]
    profile = source["input_profile"]
    d_results = []
    for spec in manifest["candidates"]:
        csv_path = d_root / (spec["class"] + "_res.csv")
        conservation = verify_csv(csv_path, spec["stock_count"], profile)
        predicted = sampled_deliveries(csv_path, obs_times)
        rmse = math.sqrt(sum((a - b)**2 for a, b in zip(predicted, observed)) /
                         len(observed))
        remainder = [(a - b)**2 for t, a, b in
                     zip(obs_times, predicted, observed) if t > 0]
        require(bool(remainder), "R1_D_NO_NONINITIAL_OBSERVATIONS")
        d_results.append({
            "candidate_id": spec["candidate_id"],
            "structure_sha256": spec["native_structure_sha256"],
            "modelica_sha256": spec["modelica_sha256"],
            "csv_sha256": bytes_hash(csv_path.read_bytes()),
            "g0": "REGENERATED_FROM_OWN_D_GRAMMAR_NOT_GENERAL_TRANSLATION_PROOF",
            "g1": spec["g1_lint"]["status"] + "_LIMITED_GRAMMAR",
            "g2": conservation,
            "g3": {
                "status": "DESCRIPTIVE_ONLY_NO_INSTRUMENT_BOUND",
                "rmse_all_items": rmse,
                "rmse_noninitial_items": math.sqrt(sum(remainder) / len(remainder)),
                "n_all": len(observed), "n_noninitial": len(remainder),
                "times_hours": obs_times, "predicted_delivered_items": predicted,
                "parameter_status": "DECLARED_NOMINAL_VALUES_NOT_FITTED",
            },
        })
    m = common["arms"]["M"]
    choice = m["evaluation"]
    require(len(choice["scored_candidates"]) == 3 and
            len(choice["trace_sha256"]) == 3 and
            choice["parameters_fitted"] is False and
            choice["reserved_evaluation"] == "NOT_RUN",
            "R1_M_INCOMPLETE_OR_EVALUATION_UNTRUSTED")
    m_report = []
    for c in choice["scored_candidates"]:
        native = next(x for x in m["native"]["candidates"] if x["id"] == c["id"])
        m_report.append({
            "candidate_id": c["id"], "graph_sha256": native["canonical_sha256"],
            "modelica_sha256": native["modelica_sha256"],
            "csv_sha256": choice["trace_sha256"][c["id"]],
            "g0": "OWN_E1_SOURCE_HASH_VERIFIED_SEMANTICS_CONDITIONAL",
            "g1": "E1_GRAPH_CHECK_AND_TYPE_CONTRACT_NOT_GENERAL_DIMENSIONAL_PROOF",
            "g2": {"status": "REAL_SOLVER_CSV_CHECKED",
                   "max_material_balance_residual": c["max_material_balance"]},
            "g3": {"status": "CONSTRUCTION_FIXED_PARAMETER_ONLY",
                   "rmse_all_items": c["rmse_items"],
                   "predicted_delivered_items": c["predicted_construction"],
                   "parameter_status": "FIXED_NOT_FITTED"}
        })
    require(common["arms"]["B"]["status"] == "BLOCKED" and
            common["arms"]["B"]["provider_calls"] == 0,
            "R1_B_MUST_REMAIN_UNAUTHORIZED")
    result = {
        "schema": SCHEMA,
        "round_id": source["round_id"],
        "source_snapshot_hash": common["source_snapshot_hash"],
        "common_input_hash": common["common_input_hash"],
        "construction_observations": observations,
        "arms": {
            "D": {"status": "SIX_OWN_MODELS_G2_WITH_DESCRIPTIVE_G3",
                  "method": "generic-conservative-chain-search/0.1",
                  "derived_input_sha256": manifest["derived_input_hash"],
                  "candidates": d_results,
                  "structure_selection": "NOT_IDENTIFIED"},
            "M": {"status": choice["status"], "method": m["native"]["method"],
                  "derived_input_sha256": m["derived_input_hash"],
                  "candidates": m_report, "decision": {
                      "status": choice["status"], "chosen_id": choice["chosen_id"],
                      "reason": choice["reason"],
                      "gap_items": choice["margin"]
                  }},
            "B": {"status": "BLOCKED", "reason": "NEW_NATIVE_BUFFALO_INFERENCE_REQUIRES_AUTHORIZATION_AND_BUDGET",
                  "derived_input_sha256": common["arms"]["B"]["derived_input_hash"],
                  "provider_calls": 0}
        },
        "external_solver_provenance": {
            "D": manifest["solver"],
            "M": {"image": "openmodelica/openmodelica:v1.26.5-minimal",
                  "method": "dassl", "start": 0, "stop": 4, "intervals": 80,
                  "libraries": ["MSL 4.0.0", "SystemDynamics 2.1.2"]},
            "models_simulated": {"D": len(d_results), "M": len(m_report), "B": 0}},
        "arm_feedback": "NOT_DELIVERED",
        "ledger_atms_joint_persistence": "NOT_RUN",
        "ref_baseline": "NOT_RUN",
        "empirical_holdout": "NOT_ACCESSED",
        "cross_arm_winner": "NONE_DECLARED",
        "scope": "R1_PARTIAL_COMMON_CONSTRUCTION_D_AND_M_PHYSICAL_ONLY",
    }
    require(result["arms"]["D"]["derived_input_sha256"] !=
            result["arms"]["M"]["derived_input_sha256"],
            "R1_DISTINCT_METHOD_INPUTS_NOT_TRACED")
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["prepare-d", "assess"])
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--assumptions", type=Path, required=True)
    p.add_argument("--d-root", type=Path, required=True)
    p.add_argument("--m-root", type=Path)
    p.add_argument("--out", type=Path)
    a = p.parse_args()
    source = json.loads(a.source.read_text())
    assumptions = json.loads(a.assumptions.read_text())
    if a.action == "prepare-d":
        result = prepare_d(source, assumptions, a.d_root)
    else:
        require(a.m_root is not None and a.out is not None,
                "R1_ASSESS_NEEDS_M_AND_OUTPUT")
        require(not a.out.exists(), "R1_OUTPUT_EXISTS")
        result = assess(source, assumptions, d_root=a.d_root, m_root=a.m_root)
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_bytes(canonical(result) + b"\n")
    print(json.dumps({"action": a.action,
                      "sha256": digest(result),
                      "status": result.get("scope", "D_SOURCES_READY")},
                     sort_keys=True))


if __name__ == "__main__":
    main()
