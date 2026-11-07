"""CT-02: typed construction-only diagnostic from one original CT-03 M CSV.

No solver or provider. A receipt ties native source, one original full AST,
real CSV bytes, solver settings and the common public construction observations.
A receipt is not itself independent proof that a solver ran: provenance must
also be audited at the runner boundary before any scientific interpretation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

from scripts.arena_v0_contract import canonical, digest
from scripts.arena_cafe.ct03_m_prepare import SCHEMA as M_PREP_SCHEMA, PUBLIC_INPUT
from scripts.arena_cafe.ct_feedback_bridge import require, _sha

SCHEMA = "igc-ct02-m-native-construction-diagnostic/1.0"
OBS_SCHEMA = "igc-ct03-public-construction-observations/1.0"
RECEIPT_SCHEMA = "igc-ct03-numerical-run-receipt/1.0"
CUTS = (0., 1., 2., 4.)
RESERVED = (6., 8.)


def sha_bytes(data: bytes):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _column(row, name):
    matches = [v for k, v in row.items() if k == name or
               (k is not None and k.endswith("." + name))]
    require(len(matches) == 1, "CT02_M_CSV_OUTPUT_MISSING_OR_AMBIGUOUS:" + name)
    try:
        x = float(matches[0])
    except (ValueError, TypeError) as error:
        raise ValueError("CT02_M_CSV_OUTPUT_NOT_NUMERIC") from error
    require(math.isfinite(x), "CT02_M_CSV_NONFINITE")
    return x


def _check_public(context, construction):
    require(type(construction) is dict and
            construction.get("schema") == OBS_SCHEMA and
            construction.get("source_snapshot_hash") == context["source_hash"] and
            construction.get("world_public_id") == context["world"] and
            construction.get("condition_id") == context["condition"] and
            construction.get("time_unit") == "hours" and
            construction.get("observable") == "cumulative_delivered",
            "CT02_M_WRONG_CONSTRUCTION_SCOPE")
    require(set(construction) == {
        "schema", "source_snapshot_hash", "world_public_id", "condition_id",
        "time_unit", "observable", "observations",
    }, "CT02_M_EXTRA_FIELDS_IN_CONSTRUCTION")
    points = construction["observations"]
    require(type(points) is list and len(points) == 4 and
            [x.get("time") for x in points if type(x) is dict] == [0, 1, 2, 4],
            "CT02_M_FOUR_CONSTRUCTION_CUTS_REQUIRED")
    past = -1.0
    for x in points:
        v = x.get("delivered")
        require(type(v) in (int, float) and math.isfinite(v) and
                past <= v <= 3.4 + 1e-8, "CT02_M_INVALID_OBSERVED_DELIVERY")
        past = v
    return points


def _check_manifest(manifest, parent):
    require(type(manifest) is dict and manifest.get("schema") == M_PREP_SCHEMA and
            manifest.get("source") == PUBLIC_INPUT and
            manifest.get("candidate_count") == 6 and
            manifest.get("executed_new_omc") == 0 and
            manifest.get("provider_calls") == 0 and
            manifest.get("scientific_status") ==
              "PREPARED_NOT_PHYSICALLY_ADJUDICATED",
            "CT02_M_PREPARED_MANIFEST_NOT_AUTHENTICATED")
    require(type(parent) is dict and
            parent.get("G2") == "NOT_EXECUTED" and
            parent.get("G3") == "NOT_EXECUTED" and
            type(parent.get("original_ast")) is dict and
            parent.get("full_ast_sha256") == digest(parent["original_ast"]),
            "CT02_M_MISSING_FULL_ORIGINAL_AST")
    require(sum(x == parent for x in manifest["candidates"]) == 1,
            "CT02_M_PARENT_NOT_FROM_THE_SIX_ORIGINALS")


def _check_receipt(receipt, parent, manifest, native_bytes, csv_bytes):
    require(type(receipt) is dict and receipt.get("schema") == RECEIPT_SCHEMA and
            receipt.get("candidate_canonical_sha256") == parent["canonical_sha256"] and
            receipt.get("full_ast_sha256") == parent["full_ast_sha256"] and
            receipt.get("source_definition_sha256") == manifest["source_definition_sha256"] and
            receipt.get("modelica_sha256") == sha_bytes(native_bytes) ==
                manifest["native_modelica_sha256"] and
            receipt.get("csv_sha256") == sha_bytes(csv_bytes) and
            receipt.get("solver") == "euler" and
            receipt.get("start_time") == 0 and
            receipt.get("stop_time") == 8 and
            receipt.get("number_of_intervals") == 64 and
            receipt.get("exit_code") == 0 and
            receipt.get("output_role") == "deliveredTotal",
            "CT02_M_NATIVE_CSV_OR_RUNTIME_RECEIPT_MISMATCH")
    require(set(receipt) == {
        "schema", "candidate_canonical_sha256", "full_ast_sha256",
        "source_definition_sha256", "modelica_sha256", "csv_sha256",
        "solver", "start_time", "stop_time", "number_of_intervals",
        "exit_code", "output_role",
    }, "CT02_M_RECEIPT_CONTAINS_UNKNOWN_FIELDS")


def _sample(csv_bytes):
    try:
        content = csv_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("CT02_M_CSV_INVALID_UTF8") from exc
    reader = csv.DictReader(content.splitlines())
    require(reader.fieldnames is not None and
            len(reader.fieldnames) == len(set(reader.fieldnames)),
            "CT02_M_DUPLICATE_OR_MISSING_CSV_COLUMNS")
    sampled = {}
    seen = 0
    last_time = -math.inf
    last_delivery = -1e-7
    for row in reader:
        seen += 1
        t = _column(row, "time")
        delivered = _column(row, "deliveredTotal")
        require(0 <= t <= 8 + 1e-8 and t >= last_time - 1e-9,
                "CT02_M_UNSORTED_OR_OUTSIDE_HORIZON")
        require(delivered >= -1e-7 and
                delivered + 1e-7 >= last_delivery and
                delivered <= 3.4 + 1e-5,
                "CT02_M_INVALID_NATIVE_DELIVERY_OR_CONSERVATION")
        last_time, last_delivery = t, delivered
        for cut in CUTS:
            if abs(t - cut) <= 1e-8:
                # Multiple solver rows at one exact time are permitted only
                # when the accumulated state agrees.
                if cut in sampled:
                    require(abs(sampled[cut] - delivered) <= 1e-7,
                            "CT02_M_CONFLICTING_SAME_TIME_STOCK")
                sampled[cut] = delivered
    require(seen >= 5 and len(sampled) == 4,
            "CT02_M_EXACT_CONSTRUCTION_CSV_SAMPLES_REQUIRED")
    return sampled, seen


def build(context, *, manifest, parent, construction, receipt,
          modelica_file: Path, trace_csv: Path) -> dict:
    require(context.get("arm") == "M", "CT02_M_WRONG_ARM")
    _check_manifest(manifest, parent)
    observed = _check_public(context, construction)
    modelica_bytes = Path(modelica_file).read_bytes()
    csv_bytes = Path(trace_csv).read_bytes()
    _check_receipt(receipt, parent, manifest, modelica_bytes, csv_bytes)
    sample, count = _sample(csv_bytes)
    points = [
        {"time": int(cut), "observed": float(obs["delivered"]),
         "simulated": sample[cut],
         "residual": sample[cut] - float(obs["delivered"])}
        for cut, obs in zip(CUTS, observed)
    ]
    parent_hash = digest(parent["original_ast"])
    return {
        "arm": "M", "condition": context["condition"],
        "source_hash": context["source_hash"],
        "parent_hash": parent_hash,
        "evidence": "G3",
        "trace_sha256": sha_bytes(csv_bytes),
        "modelica_sha256": sha_bytes(modelica_bytes),
        "solver_receipt_sha256": digest(receipt),
        "diagnostic_schema": SCHEMA,
        "numerical_provenance": "BYTE_BOUND_SOLVER_RECEIPT_NOT_INDEPENDENT_PROOF",
        "construction_evidence": "ACTUAL_PUBLIC_VALUES_NOT_MOCK_DEFAULT",
        "own_evidence_only": True, "no_future_truth": True,
        "observations": points, "native_samples": count,
        "reserved_world_truth_visible": False,
        "G2": "RECEIPT_CROSS_CHECKED_PHYSICAL_RUN_NOT_INDEPENDENTLY_CERTIFIED",
        "G3": "CONSTRUCTION_RESIDUALS_ONLY_NO_HELDOUT",
    }


def main():
    p = argparse.ArgumentParser()
    for arg in ("manifest", "parent", "construction", "receipt", "context"):
        p.add_argument("--" + arg, type=Path, required=True)
    p.add_argument("--native", type=Path, required=True)
    p.add_argument("--csv", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    require(not args.out.exists(), "CT02_REFUSE_OVERWRITE")
    def get(path):
        return json.loads(path.read_text(encoding="utf-8"))
    result = build(get(args.context), manifest=get(args.manifest),
                   parent=get(args.parent), construction=get(args.construction),
                   receipt=get(args.receipt), modelica_file=args.native,
                   trace_csv=args.csv)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(canonical(result) + b"\n")
    print(json.dumps({"schema": SCHEMA, "status": result["G3"],
                      "provider_calls": 0, "new_omc": 0}))


if __name__ == "__main__":
    main()
