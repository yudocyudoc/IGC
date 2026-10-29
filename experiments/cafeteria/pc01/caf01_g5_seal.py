#!/usr/bin/env python3
"""CAF-01 G5 preparation: offline private-world commitment, NEVER world execution.

There is intentionally no real CAF-01 configuration or nonce in this repo.
"seal" is opt-in, researcher-operated LOCALLY outside the git worktree.
It does not select a model, run DES, call Buffalo, or authorize construction.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
from fractions import Fraction
import json
import os
from pathlib import Path
import re
import secrets
import sys

from caf01_des_engine import (DESBlocked, SCHEMA as DES_SCHEMA, TIE_POLICY,
                              half_open_arrivals, private_commitment,
                              validate_private_config)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CONTRACT = HERE / "ARENA_PC01_CAF01_CONTRATO_REVISION_v0_3_2026-10-28.json"
FILES_TO_PIN = (
    "caf01_des_engine.py",
    "caf01_g3.py",
    "caf01_g4.py",
    "caf01_g5_seal.py",
    CONTRACT.name,
)
SCHEMA = "igc-caf01-g5-offline-world-precommit/0.1"
SHA = re.compile(r"^sha256:[0-9a-f]{64}$")


class G5Blocked(ValueError):
    pass


def require(value, error):
    if not value:
        raise G5Blocked(error)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha_bytes(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def snapshot_files():
    """Hash the exact local source bytes; a later edit invalidates verification."""
    return {name: sha_bytes((HERE / name).read_bytes()) for name in FILES_TO_PIN}


def hard_budget(contract):
    """Original unspent v0.3 ceilings; M equivalence saving is NOT automatic."""
    b = contract["budget"]
    d = b["Python_RK4_integrations_D"]
    om = b["OpenModelica_candidate_runs"]
    des = b["DES_world_runs"]
    providers = b["provider_inferences"]
    require(
        des["construction_max"] == des["evaluation_max"] == 1
        and des["total_max"] == 2
        and d["CAF01_construction_max"] == d["CAF_N_masked_max"] == 18
        and d["evaluation_max"] == 0 and d["total_max"] == 36
        and (om["D_construction_max"], om["D_evaluation_max"],
             om["B_construction_max"], om["B_evaluation_max"],
             om["M_construction_max"], om["M_evaluation_max"]) ==
            (3, 3, 1, 1, 9, 9)
        and om["total_max"] == 26
        and providers["Buffalo_CAF01_max"] == providers["Buffalo_CAF_N_max"] == 1
        and providers["Buffalo_max"] == 2
        and b["automatic_retries"] == 0
        and all(b[key] == 0 for key in (
            "actual_DES_runs", "actual_OpenModelica_runs",
            "actual_RK4_integrations", "actual_provider_calls")),
        "G5_BUDGET_CHANGED_OR_ALREADY_CONSUMED")
    return {
        "binding_preparation_ceiling_original_v03": {
            "DES": {"construction": 1, "evaluation": 1, "total": 2},
            "RK4_D": {"CAF01_construction": 18, "CAFN_masked": 18, "total": 36},
            "OpenModelica": {
                "D": {"construction": 3, "evaluation": 3},
                "B": {"construction": 1, "evaluation": 1},
                "M": {"construction": 9, "evaluation": 9},
                "total": 26,
            },
            "Buffalo": {"CAF01": 1, "CAFN": 1, "total": 2},
            "automatic_retries": 0,
        },
        "conditional_not_yet_authorized_OM_reduction": {
            "D": {"construction": 3, "evaluation": 3},
            "B": {"construction": 1, "evaluation": 1},
            "M": {"construction": 6, "evaluation": 6},
            "total": 20,
            "condition": "Astra_signoff_and_native_dynamic_M_equivalence",
        },
        "status": "CEILINGS_ONLY_ZERO_RUNS_NOT_EXECUTION_AUTHORIZED",
    }



def private_analytic_metrics(config):
    """Exact ex-ante capacity/latency math; NEVER calls DES or predicts D(t).

    Keep this object in the evaluator's private context. It MUST NOT be
    serialized in producer views or the public commitment receipt.
    """
    try:
        stages = validate_private_config(config)
    except DESBlocked as exc:
        raise G5Blocked("G5_INVALID_PRIVATE_CONFIG") from exc
    throughputs = tuple(Fraction(servers, 1) / duration
                        for servers, duration in stages)
    minimum = min(throughputs)
    latency = sum((duration for _, duration in stages), Fraction(0))
    return {
        "private_nominal_throughput_by_stage": throughputs,
        "private_nominal_bottleneck": minimum,
        "private_rho_construction": Fraction(6, 5) / minimum,
        "private_rho_evaluation": Fraction(3, 2) / minimum,
        "private_zero_queue_latency_minutes": latency,
    }


def check_private_design(config):
    """Fail closed against the Astra-approved public DESIGN criteria only.

    This arithmetic is not a DES preview, identifiability check, or physical
    plausibility review. Human operational justification remains mandatory.
    """
    metrics = private_analytic_metrics(config)
    rho = metrics["private_rho_construction"]
    latency = metrics["private_zero_queue_latency_minutes"]
    require(Fraction(21, 20) <= rho <= Fraction(5, 4)
            and 0 < latency <= Fraction(4),
            "G5_PRIVATE_DESIGN_OUTSIDE_APPROVED_ANALYTIC_REGIME")
    require(metrics["private_rho_evaluation"] == Fraction(5, 4) * rho,
            "G5_EVALUATION_LOAD_RATIO_CHANGED")
    # The first construction acceptance occurs at t=5/12 minutes.
    require(Fraction(5, 12) + latency < Fraction(5),
            "G5_FIRST_DELIVERY_BEFORE_FIVE_NOT_GUARANTEED")
    return {
        "status": "APPROVED_ANALYTIC_BAND_ONLY_NOT_DES_VALIDATED",
        "private_parameters_exposed": False,
        "operational_rationale_approved": False,
        "world_selected_or_executed_by_this_check": False,
        "seal_or_construction_authorized": False,
    }


def make_public_receipt(config, nonce, *, pinned_files, budget):
    """Contains no stage count, service time, servers, configuration or nonce."""
    # Check the approved private analytic regime BEFORE issuing any
    # official CAF-01 precommitment. Do not include the private metrics.
    check_private_design(config)
    require(type(nonce) is bytes and len(nonce) == 32,
            "G5_NONCE_MUST_BE_32_PRIVATE_BYTES")
    require(set(pinned_files) == set(FILES_TO_PIN)
            and all(type(x) is str and SHA.fullmatch(x) for x in pinned_files.values()),
            "G5_INCOMPLETE_SOURCE_PINS")
    require(type(budget) is dict
            and budget.get("status") == "CEILINGS_ONLY_ZERO_RUNS_NOT_EXECUTION_AUTHORIZED",
            "G5_BUDGET_NOT_PREPARED")
    arrivals = {
        "construction": len(half_open_arrivals("6/5", "20")),
        "evaluation": len(half_open_arrivals("3/2", "20")),
    }
    require(arrivals == {"construction": 24, "evaluation": 30},
            "G5_PUBLIC_EVENT_COUNT_CHANGED")
    receipt = {
        "schema": SCHEMA,
        "state": "PRIVATE_CONFIG_PRECOMMITTED_NOT_EXTERNALLY_WITNESSED",
        "world_precommitment_sha256": private_commitment(config, nonce),
        "pinned_source_sha256": pinned_files,
        "tie_policy": TIE_POLICY,
        "public_arrival_counts": arrivals,
        "sampling_minutes": [0, 5, 10, 15, 20, 30, 40],
        "private_parameters_in_receipt": False,
        "configuration_selected_by": "RESEARCHER_OFFLINE_NOT_REVEALED",
        "budget": budget,
        "physical_constraints": {
            "zero_initial_material": True,
            "losses": False,
            "cancellations": False,
            "finite_servers_at_each_stage": True,
            "inventory_or_waiting_room_capacity_modelled": False,
        },
        "private_DES_world_runs": 0,
        "future_evaluation_reveal_authorized": False,
        "external_custody": {
            "witness_receipt_id": None,
            "independent_timestamp": None,
            "verification_status": "NOT_VERIFIED",
        },
    }
    receipt["receipt_content_sha256"] = sha_bytes(canonical(receipt))
    return receipt


def verify_receipt(config, nonce, receipt, *, pinned_files, budget):
    """Offline consistency only; NEVER validates third-party custody/time."""
    require(type(receipt) is dict and receipt.get("schema") == SCHEMA,
            "G5_BAD_RECEIPT_SCHEMA")
    try:
        expected = make_public_receipt(
            config, nonce, pinned_files=pinned_files, budget=budget)
    except (DESBlocked, ValueError, TypeError) as exc:
        raise G5Blocked("G5_CANNOT_RECOMPUTE_PRECOMMITMENT") from exc
    require(hmac.compare_digest(canonical(receipt), canonical(expected)),
            "G5_PRECOMMITMENT_OR_SOURCE_CHANGED")
    return {
        "state": "LOCAL_RECOMPUTATION_MATCHES_NOT_EXTERNALLY_WITNESSED",
        "world_precommitment_sha256": receipt["world_precommitment_sha256"],
        "external_custody_verified": False,
        "execution_authorized": False,
    }


def _outside_repo(path):
    require(isinstance(path, Path) and path.is_absolute(), "G5_ABSOLUTE_PATH_REQUIRED")
    raw = path.expanduser()
    resolved = raw.resolve()
    require(resolved != ROOT and not resolved.is_relative_to(ROOT),
            "G5_PRIVATE_OR_RECEIPT_PATH_INSIDE_REPO")
    require(not raw.is_symlink(), "G5_SYMLINK_PATH_REJECTED")
    return resolved


def _atomic_new_file(path, content, mode=0o600):
    descriptor = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        path.unlink(missing_ok=True)
        raise


def seal_offline(config_path, private_dir, public_receipt_path, *, nonce=None):
    """Only explicit local invocation with externally chosen config; no runner.

    Private envelope is emitted outside GitHub, with owner-only file mode.
    Caller must independently custody the public receipt BEFORE construction.
    """
    config_path = _outside_repo(Path(config_path))
    private_dir = _outside_repo(Path(private_dir))
    public_receipt_path = _outside_repo(Path(public_receipt_path))
    require(config_path.is_file() and not config_path.is_symlink(),
            "G5_PRIVATE_INPUT_MISSING")
    require(not private_dir.exists() and not public_receipt_path.exists(),
            "G5_OUTPUT_ALREADY_EXISTS")
    require(public_receipt_path.parent.is_dir()
            and not public_receipt_path.is_relative_to(private_dir)
            and private_dir != public_receipt_path.parent,
            "G5_PUBLIC_AND_PRIVATE_PATHS_NOT_SEPARATE")
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise G5Blocked("G5_BAD_PRIVATE_INPUT_JSON") from exc
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    budget = hard_budget(contract)
    secret = secrets.token_bytes(32) if nonce is None else nonce
    receipt = make_public_receipt(config, secret, pinned_files=snapshot_files(),
                                  budget=budget)
    private = {
        "schema": SCHEMA,
        "config": config,
        "nonce_hex": secret.hex(),
        "public_receipt_sha256": sha_bytes(canonical(receipt)),
    }
    # Config, secret, and any diagnostic labels MUST remain outside repository.
    private_dir.mkdir(mode=0o700, parents=False, exist_ok=False)
    _atomic_new_file(private_dir / "private-envelope.json", canonical(private)+b"\n")
    _atomic_new_file(public_receipt_path, canonical(receipt)+b"\n")
    return {
        "state": "PRECOMMITTED_LOCALLY_NOT_EXTERNALLY_CUSTODIED",
        "world_precommitment_sha256": receipt["world_precommitment_sha256"],
        "public_receipt_file_sha256":
            sha_bytes(public_receipt_path.read_bytes()),
        "construction_run_authorized": False,
        "evaluation_run_authorized": False,
        "private_config_in_output": False,
    }


def main():
    p = argparse.ArgumentParser(description="G5 private world precommit: NO experiments")
    cmd = p.add_subparsers(dest="command", required=True)
    cmd.add_parser("plan", help="print budget ceilings, no secret and no runs")
    pre = cmd.add_parser("preflight",
                         help="check private load/latency without DES or printing values")
    pre.add_argument("--config", required=True, type=Path)
    s = cmd.add_parser("seal", help="explicitly seal researcher-selected config offline")
    s.add_argument("--config", required=True, type=Path)
    s.add_argument("--private-dir", required=True, type=Path)
    s.add_argument("--public-receipt", required=True, type=Path)
    s.add_argument("--ack-researcher-selected-offline", action="store_true")
    args = p.parse_args()
    if args.command == "plan":
        print(json.dumps(hard_budget(json.loads(CONTRACT.read_text())), sort_keys=True))
        return
    if args.command == "preflight":
        secret_path = _outside_repo(args.config)
        require(secret_path.is_file() and not secret_path.is_symlink(),
                "G5_PRIVATE_INPUT_MISSING")
        try:
            secret_config = json.loads(secret_path.read_text(encoding="utf-8"))
        except (ValueError, UnicodeError) as exc:
            raise G5Blocked("G5_BAD_PRIVATE_INPUT_JSON") from exc
        result = check_private_design(secret_config)
        print(json.dumps(result, sort_keys=True))
        return
    require(args.ack_researcher_selected_offline,
            "G5_EXPLICIT_PRIVATE_SELECTION_ACK_REQUIRED")
    # Do not emit config, nonce or private path to logs.
    result = seal_offline(args.config, args.private_dir, args.public_receipt)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
