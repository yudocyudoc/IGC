#!/usr/bin/env python3
"""CAF-01: single reserved DES evaluation, GitHub Actions only.

The already-sealed DES configuration is read from the EXISTING environment
secret. This is an explicitly labelled historical-G5-custody waiver, NOT
retroactive proof of the original world commitment. No model, forecast or
baseline is refitted here. No DES is executed by preflight or CI tests.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
from fractions import Fraction
from pathlib import Path
import subprocess

from caf01_construction_github import (
    SECRET_ENV, read_pinned_public_receipt, prepare_authorized_inputs,
    HISTORICAL_LOCAL_CONSTRUCTION_INVOCATIONS,
)
from caf01_des_engine import half_open_arrivals, run_toy_engine
from caf01_g3 import digest
from caf01_g4 import score_six_delivered_values
from caf01_g5_seal import CONTRACT, canonical

HERE = Path(__file__).resolve().parent
TIMES = (0, 5, 10, 15, 20, 30, 40)
SCORE_TIMES = (5, 10, 15, 20, 30, 40)
EXPECTED_ACCEPTED = (0, 8, 15, 23, 30, 30, 30)
PACKAGE_SHA = "8ce3d5713df480201dfcb982b5aa291857a09584eeb5fa2456cacfdff179df8f"
G3_SELECTION_SHA = "sha256:8d01851ef98028b2afe756577a119346aea73c4cd806fe6ee5efbd8d0f1a5a3b"
G3_LOCK_SHA = "sha256:13e820eeaad59cb89eb56ddfa4e43b9b472c7188166a3c1d34b7487e05bfab71"
WORLD_SHA = "sha256:26ca23076a44410bcafc4a7a944a5d5f6c6528dd59c96e7459e43c93a68812ad"
G5_RECEIPT_SHA = "sha256:feff6d77444455a49f39cac57a7f65f6eb1039318205b1e8dde8d10ef48355bd"
TSA_CERT_SHA = "8bfb0305bb64e2571ca507552ef3245cb1c2fee8728e0ff8689225081ea13467"
CA_CERT_SHA = "2151b61137ffa86bf664691ba67e7da0b19f98c758e3d228d5d8ebf27e044438"
CONFIRM = "RUN_CAF01_RESERVED_DES_EVALUATION_ONCE"
WAIVER = "ACCEPT_UNVERIFIED_HISTORICAL_G5_CUSTODY"
G4_RUN = 41006338774
TSA_RUN = 41006622753


class EvaluationBlocked(ValueError):
    pass


def need(ok, code):
    if not ok:
        raise EvaluationBlocked(code)


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def verify_witness(witness):
    """Reverify the existing signed timestamp, with NO new TSA network call."""
    witness = Path(witness)
    for name, expected in (("tsa.crt", TSA_CERT_SHA),
                           ("cacert.pem", CA_CERT_SHA)):
        need(sha_bytes((witness / name).read_bytes()) == expected,
             "EVAL_TSA_CERTIFICATE_PIN_MISMATCH")
    cmd = ["openssl", "ts", "-verify",
           "-in", str(witness / "binding.tsr"),
           "-data", str(witness / "binding.json"),
           "-CAfile", str(witness / "cacert.pem"),
           "-untrusted", str(witness / "tsa.crt")]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True,
                                text=True, timeout=20)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        raise EvaluationBlocked("EVAL_EXTERNAL_TIMESTAMP_VERIFICATION_FAILED") from None
    need("Verification: OK" in result.stdout + result.stderr,
         "EVAL_EXTERNAL_TIMESTAMP_NOT_VERIFIED")


def load_frozen_package(g4_file, witness_dir):
    """Only public bytes and the old third-party witness. Never DES."""
    g4_file, witness_dir = Path(g4_file), Path(witness_dir)
    raw = g4_file.read_bytes()
    need(sha_bytes(raw) == PACKAGE_SHA, "EVAL_G4_EXACT_BYTES_CHANGED")
    verify_witness(witness_dir)
    need((witness_dir / "preholdout-package.json").read_bytes() == raw,
         "EVAL_WITNESSED_PACKAGE_DIFFERS_FROM_ORIGINAL")
    binding = json.loads((witness_dir / "binding.json").read_bytes())
    need(binding["exact_G4_preholdout_file_sha256"] == "sha256:" + PACKAGE_SHA
         and binding["G3_selection_sha256"] == G3_SELECTION_SHA
         and binding["DES_private_world_precommitment_public_hash"] == WORLD_SHA
         and binding["G5_public_precommit_receipt_content_sha256"] == G5_RECEIPT_SHA
         and binding["native_model_forecast_GitHub_run"] == G4_RUN
         and binding["G5_original_prior_external_custody"] == "NOT_VERIFIED"
         and binding["future_evaluation_release_authorized"] is False
         and binding["evaluation_truth_read"] is False,
         "EVAL_WITNESS_BINDING_CHANGED")
    p = json.loads(raw)
    body = {k: v for k, v in p.items() if k != "preholdout_package_sha256"}
    lock = p["g3_lock"]
    lock_body = {k: v for k, v in lock.items() if k != "forecast_lock_sha256"}
    need(p["preholdout_package_sha256"] == digest(body)
         and p["preholdout_package_sha256"] == binding["G4_internal_content_sha256"]
         and lock["forecast_lock_sha256"] == digest(lock_body) == G3_LOCK_SHA
         and p["selection_sha256"] == lock["selection_sha256"] == G3_SELECTION_SHA
         and p["g3_forecast_lock_sha256"] == G3_LOCK_SHA
         and p["source_snapshot_sha256"] == lock["source_snapshot_sha256"] == WORLD_SHA
         and p["case"] == lock["case"] == "CAF01"
         and p["scoring_policy"]["primary"] == "MAE_DELIVERED_SIX_TIMES_EXCLUDING_T0"
         and p["scoring_policy"]["secondary"] == "RMSE_DELIVERED_SAME_SIX_TIMES"
         and p["actual_evaluation_values_included"] is False
         and p["custody"]["release_authorized"] is False
         and p["custody"]["state"] == "NOT_CUSTODIED_EXTERNAL_WITNESS_REQUIRED",
         "EVAL_G4_LOCK_OR_POLICY_CHANGED")
    need(lock["evaluation_times_minutes"] == list(SCORE_TIMES)
         and lock["evaluation_pulse"] ==
             {"kind": "pulse", "rate_per_minute": 1.5, "duration_minutes": 20}
         and lock["evaluation_truth_included"] is False
         and lock["external_reveal_authorized"] is False,
         "EVAL_PULSE_OR_FUTURE_MASK_CHANGED")
    arms = lock["arm_forecasts"]
    need(set(arms) == {"D", "M", "B"}
         and arms["D"]["status"] == "ABSTAIN_POINT_PARAMETER_UNIDENTIFIABLE"
         and arms["D"]["prediction"] is None
         and arms["M"]["status"] == "CONDITIONAL_POINT_FORECAST_NOT_STRUCTURAL_ID"
         and arms["M"]["winners"] == ["M_C00_C72"]
         and arms["B"]["status"] == "NO_VALID_CANDIDATE"
         and arms["B"]["prediction"] is None
         and len(arms["M"]["prediction"]) == 6
         and lock["forecast_by_candidate"]["M_C00_C72"] == arms["M"]["prediction"],
         "EVAL_ARM_STATUS_OR_M_CURVE_CHANGED")
    refs = p["references"]["references"]
    need(set(refs) == {"REF_CAF", "REF_SCALE"}
         and refs["REF_SCALE"]["status"] == "READY_PRESCRIBED_INPUT_RATIO_ONLY"
         and len(refs["REF_SCALE"]["predicted_delivered"]) == 6,
         "EVAL_FROZEN_REFERENCES_INCOMPLETE")
    receipt = read_pinned_public_receipt()
    need(receipt["world_precommitment_sha256"] == WORLD_SHA
         and receipt["receipt_content_sha256"] == G5_RECEIPT_SHA
         and receipt["external_custody"]["verification_status"] == "NOT_VERIFIED"
         and receipt["future_evaluation_reveal_authorized"] is False,
         "EVAL_G5_HISTORICAL_STATE_MISMATCH")
    return p, receipt


def validate_physical_snapshots(snapshots):
    need(len(snapshots) == len(TIMES), "EVAL_OBSERVATION_COUNT")
    delivered = []
    rows = []
    last = 0
    for s, t, a in zip(snapshots, TIMES, EXPECTED_ACCEPTED):
        need(s.t_min == Fraction(t)
             and type(s.accepted_cum_orders) is int
             and s.accepted_cum_orders == a
             and type(s.delivered_cum_orders) is int
             and last <= s.delivered_cum_orders <= a
             and s.pending_orders == a - s.delivered_cum_orders
             and s.pending_orders == sum(s.stage_waiting) + sum(s.stage_in_service),
             "EVAL_DES_NATIVE_PHYSICAL_BALANCE_OR_CALENDAR_FAILED")
        delivered.append(s.delivered_cum_orders)
        rows.append({"t_min": t, "accepted_cum_orders": a,
                     "delivered_cum_orders": s.delivered_cum_orders,
                     "pending_orders": s.pending_orders})
        last = s.delivered_cum_orders
    need(delivered[0] == 0 and rows[-1]["accepted_cum_orders"] == 30,
         "EVAL_NONEMPTY_INITIAL_STOCK_OR_WRONG_EVENT_COUNT")
    return delivered[1:], rows


def score_locked(package, observed):
    """Competitive scoring for M and frozen refs ONLY; D/B are noncompetitive."""
    refs = package["references"]["references"]
    predictions = {"M": package["g3_lock"]["arm_forecasts"]["M"]["prediction"]}
    for label, key in (("REF-CAF", "REF_CAF"), ("REF-SCALE", "REF_SCALE")):
        curve = refs[key].get("predicted_delivered")
        if curve is not None:
            predictions[label] = curve
    scores = {name: score_six_delivered_values(curve, observed)
              for name, curve in predictions.items()}
    mae_m = scores["M"]["MAE_delivered_orders"]
    comparisons = {}
    for label in ("REF-CAF", "REF-SCALE"):
        if label in scores:
            delta = scores[label]["MAE_delivered_orders"] - mae_m
            comparisons[label] = {
                "reference_minus_M_MAE_orders": delta,
                "M_lower_MAE": delta > 0,
                "at_least_one_order_gain": delta >= 1,
                "descriptive_only": True,
            }
        else:
            comparisons[label] = {
                "status": "REFERENCE_ABSTAINED_NO_COMPARISON",
                "descriptive_only": True,
            }
    return {
        "evaluated_participants": ["M", "REF-CAF", "REF-SCALE"],
        "scores": scores,
        "comparisons": comparisons,
        "D": {"status": "ABSTAIN_POINT_PARAMETER_UNIDENTIFIABLE",
              "competitive_MAE": None,
              "representative_curve_not_competitive": True},
        "Buffalo": {"status": "NO_VALID_CANDIDATE", "competitive_MAE": None},
        "no_structural_identification_or_statistical_generalization_claim": True,
    }


def github_one_shot_guard():
    need(os.getenv("GITHUB_ACTIONS") == "true"
         and os.getenv("GITHUB_REPOSITORY") == "yudocyudoc/IGC"
         and os.getenv("GITHUB_REF") == "refs/heads/main"
         and os.getenv("GITHUB_EVENT_NAME") == "workflow_dispatch"
         and os.getenv("GITHUB_RUN_NUMBER") == "1"
         and os.getenv("GITHUB_RUN_ATTEMPT") == "1"
         and os.getenv("CAF01_EVAL_CONFIRMATION") == CONFIRM
         and os.getenv("CAF01_G5_WAIVER") == WAIVER,
         "EVAL_REQUIRES_FIRST_MAIN_DISPATCH_AND_EXPLICIT_G5_WAIVER")


def evaluate(package, receipt, output_dir, secret):
    """Run ONE precommitted DES, log invocation before the engine is entered."""
    contract = json.loads(CONTRACT.read_bytes())
    config = prepare_authorized_inputs(secret, receipt, contract)
    arrivals = half_open_arrivals("3/2", "20")
    need(len(arrivals) == 30 and
         tuple(sum(x <= Fraction(t) for x in arrivals) for t in TIMES)
         == EXPECTED_ACCEPTED, "EVAL_PUBLIC_ARRIVAL_SCHEDULE_CHANGED")
    output_dir = Path(output_dir)
    need(not output_dir.exists(), "EVAL_OUTPUT_EXISTS")
    output_dir.mkdir(parents=True, exist_ok=False)
    print("CAF01_RESERVED_DES_EVALUATION_INVOCATION_STARTED=1", flush=True)
    print("CAF01_EVALUATION_ATTEMPT_COUNTS_EVEN_IF_FAILED=1", flush=True)
    snapshots = run_toy_engine(config, arrivals, tuple(Fraction(x) for x in TIMES))
    observed, rows = validate_physical_snapshots(snapshots)
    result = {
        "schema": "igc-caf01-reserved-evaluation-g5-waiver/0.1",
        "source_snapshot_sha256": WORLD_SHA,
        "g4_exact_file_sha256": "sha256:" + PACKAGE_SHA,
        "g3_forecast_lock_sha256": G3_LOCK_SHA,
        "timestamp_witness_run": TSA_RUN,
        "native_model_forecast_run": G4_RUN,
        "evaluation_DES_runs_consumed_this_attempt": 1,
        "historical_local_construction_DES_invocations":
            HISTORICAL_LOCAL_CONSTRUCTION_INVOCATIONS,
        "prior_GitHub_construction_reproductions": 1,
        "known_construction_invocations_before_evaluation":
            HISTORICAL_LOCAL_CONSTRUCTION_INVOCATIONS + 1,
        "original_construction_budget_exceeded": True,
        "historical_G5_external_custody": "NOT_VERIFIED",
        "historical_G5_requirement": "EXPLICITLY_WAIVED_NOT_RETROACTIVELY_SATISFIED",
        "scientific_status": "DESCRIPTIVE_EVALUATION_WITH_HISTORICAL_G5_PROTOCOL_DEVIATION",
        "evaluation_pulse": {"kind": "pulse", "rate_per_minute": 1.5,
                             "duration_minutes": 20},
        "evaluation_readouts": rows,
        "primary_observed_delivered_six_times": observed,
        "private_world_structure_or_nonce_disclosed": False,
        "no_refit_no_replacement": True,
    }
    # Preserve the public readout even if post-evaluation scoring fails.
    (output_dir / "01_DES_PUBLIC_EVALUATION.json").write_bytes(canonical(result) + b"\n")
    report = {
        **result,
        "scoring": score_locked(package, observed),
    }
    payload = canonical(report) + b"\n"
    forbidden = (b'"stages"', b'"servers"', b'"service_minutes"',
                 b'"nonce_hex"', b'"config"', b'"stage_waiting"', b'"stage_in_service"')
    need(not any(s in payload for s in forbidden), "EVAL_PRIVATE_WORLD_LEAK")
    (output_dir / "02_LOCKED_SCORES.json").write_bytes(payload)
    hashes = {p.name: "sha256:" + sha_bytes(p.read_bytes())
              for p in sorted(output_dir.iterdir())}
    (output_dir / "03_SHA256_MANIFEST.json").write_bytes(
        canonical({"files": hashes, "GitHub_run_id": os.getenv("GITHUB_RUN_ID"),
                   "one_DES_evaluation_attempt": 1,
                   "no_additional_OpenModelica_RK4_or_Buffalo": True}) + b"\n")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("preflight", "evaluate"))
    parser.add_argument("--g4", required=True)
    parser.add_argument("--witness", required=True)
    parser.add_argument("--output-dir")
    args = parser.parse_args()
    if args.mode == "evaluate":
        github_one_shot_guard()
        need(bool(args.output_dir), "EVAL_OUTPUT_REQUIRED")
    package, receipt = load_frozen_package(args.g4, args.witness)
    if args.mode == "preflight":
        print("CAF01_RESERVED_EVALUATION_PREFLIGHT_G4_TSA_G5_PASS_NO_DES")
        return
    need(os.environ.get(SECRET_ENV), "EVAL_PRIVATE_ENVELOPE_SECRET_MISSING")
    evaluate(package, receipt, args.output_dir, os.environ[SECRET_ENV])
    print("CAF01_RESERVED_EVALUATION_LOCKED_SCORE_COMPLETE_DES_ONE", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Never disclose the secret, stage timings or a private traceback.
        print("CAF01_RESERVED_EVALUATION_BLOCKED_OR_FAILED", flush=True)
        raise SystemExit(1) from None
