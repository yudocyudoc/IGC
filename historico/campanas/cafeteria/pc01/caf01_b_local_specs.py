#!/usr/bin/env python3
"""CAF-01 local Buffalo specs bridge; offline, no provider/solver calls.

Delegates equation translation to unchanged historical Buffalo translator.
A temporary deep copy uses the legacy solver specs ONLY to pass its guard;
the original CAF specs and original source hash are preserved separately.
No provider-to-OpenModelica dynamical parity is claimed.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.arena_b_native_to_modelica import generate as legacy_generate
from scripts.arena_b_native_to_modelica import TranslationBlocked, VERSION
from scripts.arena_b_native_series import resolve_roles

CONTRACT = Path(__file__).with_name("ARENA_PC01_CAF01_CONTRATO_REVISION_v0_3_2026-10-28.json")
SPEC_KEYS = {"startTime", "stopTime", "dt", "timeUnits", "integrationMethod"}
HISTORICAL = {"startTime": 0, "stopTime": 8, "dt": 0.125,
              "timeUnits": "hour", "integrationMethod": "Euler"}
CAF = {"startTime": 0, "stopTime": 2/3, "dt": 1/120,
       "timeUnits": "hour", "integrationMethod": "Euler"}


def digest(obj):
    b = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(b).hexdigest()


def check_scope(document, contract):
    if type(document) is not dict or type(document.get("model")) is not dict:
        raise TranslationBlocked("NOT_NATIVE_BUFFALO_ENVELOPE")
    specs = document["model"].get("specs")
    b = contract["methods"]["B"]
    if (type(specs) is not dict or set(specs) != SPEC_KEYS
            or b["historical_specs"] != HISTORICAL
            or set(b["CAF_local_specs_proposal"]) != SPEC_KEYS):
        raise TranslationBlocked("B_LOCAL_SPECS_FIELDS_OR_PIN_CHANGED")
    for k in ("startTime", "stopTime", "dt"):
        for x in (specs[k], b["CAF_local_specs_proposal"][k]):
            if type(x) not in (int, float) or not math.isfinite(x):
                raise TranslationBlocked("B_LOCAL_NONFINITE_OR_INVALID_TIME")
            if not math.isclose(x, CAF[k], abs_tol=1e-14, rel_tol=0):
                raise TranslationBlocked("B_NATIVE_SPECS_OUTSIDE_CAF_SCOPE:" + k)
    for k in ("timeUnits", "integrationMethod"):
        if specs[k] != CAF[k] or b["CAF_local_specs_proposal"][k] != CAF[k]:
            raise TranslationBlocked("B_NATIVE_SPECS_OUTSIDE_CAF_SCOPE:" + k)
    if (b["candidate_models_max"] != 1 or b["candidate_OpenModelica_max"] != 2
            or b["negative_control_native_simulations_max"] != 0):
        raise TranslationBlocked("B_CAF_BUDGET_CHANGED")


def bridge(document, contract):
    check_scope(document, contract)
    proxy = copy.deepcopy(document)
    proxy["model"]["specs"] = copy.deepcopy(HISTORICAL)
    name, code, upstream = legacy_generate(proxy)
    # Proof of the bridge's only permitted change, independent of source hash.
    a = copy.deepcopy(document)
    b = copy.deepcopy(proxy)
    a["model"].pop("specs")
    b["model"].pop("specs")
    if a != b or upstream["model"] != name or upstream["native_simulation_specs"] != HISTORICAL:
        raise TranslationBlocked("B_NATIVE_PAYLOAD_CHANGED_OR_UPSTREAM_MISMATCH")
    variables = document["model"]["variables"]
    stocks = sum(v.get("type") == "stock" for v in variables)
    flows = sum(v.get("type") == "flow" for v in variables)
    try:
        # Material roles only; CSV and simulator parity are still unverified.
        names = {v["name"].replace(" ", "_") for v in variables}
        mapped = resolve_roles(document, names)
    except ValueError as exc:
        mapping_status = "BLOCKED_SERIES_VIEW_NOT_PROVIDER_MODEL_FAILURE"
        mapping = None
        mapping_reason = str(exc)
    else:
        mapping_status = "SHAPE_MAPPED_CSV_AND_DYNAMICS_UNVERIFIED"
        mapping = mapped["roles"]
        mapping_reason = None
    report = {
        "schema": "igc-caf01-b-local-specs-bridge/0.1",
        "status": "OFFLINE_TRANSLATED_NOT_EXECUTED",
        "original_document_sha256": digest(document),
        "original_without_specs_sha256": digest(a),
        "legacy_translation_proxy_sha256": digest(proxy),
        "modelica_sha256": "sha256:" + hashlib.sha256(code.encode()).hexdigest(),
        "modelica_class": name,
        "legacy_translator_version": VERSION,
        "legacy_translator_status": upstream["status"],
        "actual_native_specs": copy.deepcopy(document["model"]["specs"]),
        "historical_specs_used_only_for_translation": copy.deepcopy(HISTORICAL),
        "caf_solver_specs_preserved_for_future_authorized_execution": copy.deepcopy(CAF),
        "native_equations_modified": False,
        "stocks": stocks, "flows": flows,
        "series_mapping_status": mapping_status,
        "series_roles_if_unambiguous": mapping,
        "series_block_reason": mapping_reason,
        "native_check_model_runs": 0, "native_simulation_runs": 0,
        "buffalo_provider_calls": 0,
        "g0": "CONDITIONAL_LOOKUP_TIME_AND_INTEGRATION_PARITY_NOT_PROVEN",
        "g1": "UNVERIFIED", "g2": "NOT_RUN", "g3": "NOT_RUN",
        "limitations": [
            "Legacy translator has NOT acquired native CAF-spec compatibility.",
            "Only a temporary COPY of specs was normalized for equation translation.",
            "Native Buffalo TIME, lookups and Euler discretization require parity tests.",
            "Series roles require verification against actual native CSV columns.",
            "No private world, model selection or prediction was evaluated."
        ]
    }
    return name, code, report


def check_script(name, folder):
    file = (Path(folder).resolve() / (name + ".mo"))
    if not file.is_file():
        raise TranslationBlocked("B_LOCAL_GENERATED_MODEL_MISSING")
    path = file.as_posix()
    if any(c in path for c in ('"', "\n", "\r")):
        raise TranslationBlocked("B_LOCAL_UNSAFE_MODEL_PATH")
    return ('getVersion();\nloadFile("' + path + '");\n'
            + 'checkModel(' + name + ');\nprint(getErrorString());\n')


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--native", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    if args.out.exists():
        raise TranslationBlocked("B_LOCAL_OUTPUT_EXISTS")
    document = json.loads(args.native.read_text(encoding="utf-8"))
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    name, code, report = bridge(document, contract)
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / (name + ".mo")).write_text(code, encoding="utf-8")
    (args.out / "check_only.mos").write_text(check_script(name, args.out), encoding="utf-8")
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "series_mapping": report["series_mapping_status"],
                      "model": name, "provider_calls": 0, "solver_runs": 0}))


if __name__ == "__main__":
    main()
