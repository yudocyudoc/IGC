#!/usr/bin/env python3
"""CAF-01 real CONSTRUCTION runner, restricted to GitHub Actions workflow_dispatch.

The private DES world and nonce are supplied ONLY via an Actions secret, never
via a tracked file, CLI parameter, log, or uploaded artifact. Exactly one
construction DES run; evaluation is NOT implemented in this executable.
No retries. The previous ChatGPT-local run is not used as evidence.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from fractions import Fraction
from pathlib import Path

from caf01_des_engine import half_open_arrivals, run_toy_engine
from caf01_g3 import SCHEMA as G3_SCHEMA, validate_evidence
from caf01_g4 import SCHEMA as G4_SCHEMA, audit_arrival_sidecar, forecast
from caf01_g5_seal import (CONTRACT, canonical, hard_budget, snapshot_files,
                           verify_receipt)

HERE = Path(__file__).resolve().parent
PUBLIC_RECEIPT_PATH = HERE / "receipts" / "CAF01_G5_PRECOMMIT_PUBLIC_2026-10-29.json"
EXPECTED_RECEIPT_FILE_SHA256 = (
    "df8c7056e18dffc83b0a4cad1403970778813e80585bca84236107a37de7ac93"
)
TIMES = (0, 5, 10, 15, 20, 30, 40)
EXPECTED_A = (0, 6, 12, 18, 24, 24, 24)
SECRET_ENV = "CAF01_PRIVATE_ENVELOPE_B64"


class ConstructionBlocked(ValueError):
    pass


def require(ok, code):
    if not ok:
        raise ConstructionBlocked(code)


def read_pinned_public_receipt():
    payload = PUBLIC_RECEIPT_PATH.read_bytes()
    require(hashlib.sha256(payload).hexdigest() == EXPECTED_RECEIPT_FILE_SHA256,
            "CAF01_RECEIPT_FILE_BYTES_CHANGED")
    receipt = json.loads(payload)
    require(receipt["state"] == "PRIVATE_CONFIG_PRECOMMITTED_NOT_EXTERNALLY_WITNESSED"
            and receipt["future_evaluation_reveal_authorized"] is False
            and receipt["private_DES_world_runs"] == 0,
            "CAF01_WRONG_PRECOMMIT_RECEIPT_STATE")
    return receipt


def decode_private_envelope(encoded):
    """Only decode PRIVATE bytes in memory; never write or log them."""
    require(type(encoded) is str and 0 < len(encoded) <= 200000,
            "CAF01_SECRET_NOT_CONFIGURED")
    try:
        raw = base64.b64decode(encoded, validate=True)
        require(len(raw) <= 100000, "CAF01_SECRET_TOO_LARGE")
        envelope = json.loads(raw)
        require(type(envelope) is dict
                and set(envelope) == {"schema", "config", "nonce_hex",
                                      "public_receipt_sha256"},
                "CAF01_PRIVATE_ENVELOPE_SCHEMA_CHANGED")
        nonce = bytes.fromhex(envelope["nonce_hex"])
        require(len(nonce) == 32, "CAF01_NONCE_INVALID")
        return envelope["config"], nonce, envelope["public_receipt_sha256"]
    except (ValueError, KeyError, TypeError, UnicodeError) as exc:
        raise ConstructionBlocked("CAF01_PRIVATE_ENVELOPE_UNREADABLE") from None


def prepare_authorized_inputs(encoded, receipt, contract):
    """Verify approved precommit and pinned source without running DES."""
    config, nonce, stored_sha = decode_private_envelope(encoded)
    require(stored_sha == ("sha256:" + hashlib.sha256(canonical(receipt)).hexdigest()),
            "CAF01_PRIVATE_ENVELOPE_NOT_BOUND_TO_PUBLIC_RECEIPT")
    require(receipt["pinned_source_sha256"] == snapshot_files(),
            "CAF01_PINNED_SOURCE_HASHES_CHANGED")
    budget = hard_budget(contract)
    proof = verify_receipt(config, nonce, receipt,
                           pinned_files=snapshot_files(), budget=budget)
    require(proof["state"] ==
            "LOCAL_RECOMPUTATION_MATCHES_NOT_EXTERNALLY_WITNESSED"
            and not proof["execution_authorized"],
            "CAF01_PRECOMMIT_VERIFICATION_FAILED")
    return config


def produce_construction_public_only(config, receipt, contract):
    """One DES run with the public construction pulse; no evaluation path.

    The private stage queue/busy arrays are used ONLY for conservation checks.
    No stage-specific data or secret configuration is serialized.
    """
    arrivals = half_open_arrivals("6/5", "20")
    require(len(arrivals) == 24, "CAF01_PUBLIC_CONSTRUCTION_PULSE_CHANGED")
    observations = tuple(Fraction(t) for t in TIMES)
    snapshots = run_toy_engine(config, arrivals, observations)  # EXACTLY 1 DES
    require(len(snapshots) == 7, "CAF01_CONSTRUCTION_TIME_MASK_CHANGED")

    rows = []
    for s, t, accepted in zip(snapshots, TIMES, EXPECTED_A):
        internal_material = sum(s.stage_waiting) + sum(s.stage_in_service)
        require(s.t_min == t and s.accepted_cum_orders == accepted,
                "CAF01_WRONG_EVENT_SCHEDULE_OR_READOFF")
        require(s.accepted_cum_orders == s.delivered_cum_orders + s.pending_orders
                and s.pending_orders == internal_material,
                "CAF01_CONSTRUCTION_PHYSICAL_BALANCE_FAILED")
        require(0 <= s.delivered_cum_orders <= s.accepted_cum_orders,
                "CAF01_MORE_DELIVERIES_THAN_ACCEPTED")
        rows.append({
            "t_min": t,
            "accepted_cum_orders": s.accepted_cum_orders,
            "delivered_cum_orders": s.delivered_cum_orders,
            "pending_orders": s.pending_orders,
        })

    snapshot_id = receipt["world_precommitment_sha256"]
    source = {"schema": "igc-caf01-public-construction/0.1",
              "case": "CAF01", "source_snapshot_sha256": snapshot_id,
              "public_pulse": {"kind": "pulse", "rate_per_minute": 1.2,
                               "duration_minutes": 20},
              "observations": rows,
              "independent_material_balance_verified": True,
              "evaluation_run_count": 0}
    evidence = {"schema": G3_SCHEMA, "case": "CAF01",
                "source_snapshot_sha256": snapshot_id,
                "public_pulse": {"kind": "pulse", "rate_per_minute": 1.2,
                                 "duration_minutes": 20},
                "observations": [{"t_min": r["t_min"],
                                  "delivered": r["delivered_cum_orders"]}
                                 for r in rows]}
    sidecar = {"schema": G4_SCHEMA, "case": "CAF01",
               "source_snapshot_sha256": snapshot_id,
               "observations": [{"t_min": r["t_min"],
                                 "accepted_cum_orders": r["accepted_cum_orders"],
                                 "pending_orders": r["pending_orders"]}
                                for r in rows]}
    cafn = {**evidence, "case": "CAFN",
            "observations": [evidence["observations"][0],
                             evidence["observations"][-1]]}
    validate_evidence(evidence, contract)
    validate_evidence(cafn, contract)
    audit = audit_arrival_sidecar(evidence, sidecar, contract)
    refs = forecast(evidence, contract)
    refs_n = forecast(cafn, contract)
    require(refs["future_truth_seen"] is False
            and refs_n["future_truth_seen"] is False,
            "CAF01_REFERENCES_CONTAMINATED")
    return {
        "01_construction_public.json": source,
        "02_evidence_G3_producers.json": evidence,
        "03_CAFN_masked_endpoints.json": cafn,
        "04_A_P_audit_only.json": sidecar,
        "05_G4_references_prelock.json": refs,
        "06_G4_CAFN_abstentions.json": refs_n,
        "07_G4_audit_result.json": audit,
    }


def write_public_bundle(bundle, output_dir, receipt):
    """Fail on ANY secret-shaped key; upload only files under this directory."""
    forbidden = ('"stages"', '"servers"', '"service_minutes"',
                 '"nonce_hex"', '"config"', '"stage_waiting"',
                 '"stage_in_service"', '"private_nominal_')
    out = Path(output_dir)
    require(not out.exists(), "CAF01_PUBLIC_OUTPUT_ALREADY_EXISTS")
    data = {}
    for name, value in bundle.items():
        require(name.endswith(".json") and "/" not in name and "\\" not in name,
                "CAF01_UNSAFE_ARTIFACT_FILENAME")
        payload = canonical(value) + b"\n"
        require(not any(token.encode() in payload for token in forbidden),
                "CAF01_PRIVATE_INFORMATION_IN_PUBLIC_ARTIFACT")
        data[name] = payload
    out.mkdir(parents=True, exist_ok=False)
    checksums = {}
    for name, payload in sorted(data.items()):
        (out / name).write_bytes(payload)
        checksums[name] = "sha256:" + hashlib.sha256(payload).hexdigest()
    manifest = {
        "schema": "igc-caf01-gha-construction-manifest/0.1",
        "execution_platform": "GitHub Actions",
        "workflow_event": "workflow_dispatch",
        "source_commit": os.environ.get("GITHUB_SHA"),
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "world_precommitment_sha256": receipt["world_precommitment_sha256"],
        "public_receipt_file_sha256": "sha256:" + EXPECTED_RECEIPT_FILE_SHA256,
        "files_sha256": checksums,
        "DES_construction_world_runs_consumed": 1,
        "DES_evaluation_world_runs_consumed": 0,
        "RK4_integrations_consumed": 0,
        "OpenModelica_runs_consumed": 0,
        "Buffalo_inferences_consumed": 0,
        "evaluation_truth_available": False,
        "secrets_in_artifacts": False,
        "external_witness_email_reported_by_researcher_not_cryptographically_verified": True,
    }
    (out / "08_manifest.json").write_bytes(canonical(manifest) + b"\n")
    return manifest


def main():
    """GH workflow only. Never a command to run experimental truth locally."""
    import argparse
    parser = argparse.ArgumentParser(description="GitHub-only CAF-01 construction")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    require(os.getenv("GITHUB_ACTIONS") == "true"
            and os.getenv("GITHUB_EVENT_NAME") == "workflow_dispatch"
            and os.getenv("GITHUB_RUN_ATTEMPT") == "1"
            and os.getenv("GITHUB_RUN_NUMBER") == "1",
            "CAF01_ONLY_FIRST_MANUAL_GITHUB_WORKFLOW_RUN")
    receipt = read_pinned_public_receipt()
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    config = prepare_authorized_inputs(os.environ.get(SECRET_ENV), receipt, contract)
    result = produce_construction_public_only(config, receipt, contract)
    manifest = write_public_bundle(result, args.output_dir, receipt)
    # Safe to print ONLY public ids, never stage outputs or envelope.
    print("CAF01_CONSTRUCTION_SUCCESS_PUBLIC_ONLY")
    print("SOURCE_COMMIT=" + str(manifest["source_commit"]))
    print("PUBLIC_PRECOMMIT_SHA256=" + manifest["public_receipt_file_sha256"])
    print("DES_CONSTRUCTION_RUNS=1")
    print("DES_EVALUATION_RUNS=0")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # No secret, config, nonce, or potentially sensitive traceback in logs.
        # If this occurred after DES started, DO NOT retry the workflow:
        # independently review the consumed attempt first.
        print("CAF01_CONSTRUCTION_BLOCKED_OR_FAILED")
        raise SystemExit(1) from None
