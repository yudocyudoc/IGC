#!/usr/bin/env python3
"""CAF-01 arm D: ONE GitHub-only 18-grid RK4 screen per isolated public view.

No DES, OpenModelica simulation, Buffalo, M, G4 references, native-G2 claims,
holdout results, or evaluation predictions. All parameters come from the
unchanged public PC-01 contract. No additional fitting loops or reruns.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scripts.arena_d_v01 import modelica, topology
from scripts.arena_d_v1_screen import integrate
from scripts.arena_v0_contract import digest
from caf01_g3 import inventory, score, validate_evidence
from caf01_g5_seal import CONTRACT, canonical

HERE = Path(__file__).resolve().parent
PUBLIC = HERE / "public_inputs" / "run_40915090599"
INPUTS = {
    "CAF01": ("CAF01.json",
              "727501a3b5b33a63ab5a5d5f0f907d5431d0ee4f0d8b24ffd6f97758d59386fb",
              (0, 5, 10, 15, 20, 30, 40)),
    "CAFN": ("CAFN.json",
             "8112019ffad402ff1f1e0deafa3b4f1786bb37488258d5c7fe16e0404e22d5a1",
             (0, 40)),
}
WORLD_PRECOMMIT = "sha256:26ca23076a44410bcafc4a7a944a5d5f6c6528dd59c96e7459e43c93a68812ad"
EXPERIMENTAL_GITHUB_RUN = "40915090599"
STEP_HOURS = 1 / 120
BALANCE_CERTIFIED_MAX = 0.00002


class DScreenBlocked(ValueError):
    pass


def require(ok, reason):
    if not ok:
        raise DScreenBlocked(reason)


def read_view(case):
    require(case in INPUTS, "D_UNKNOWN_CASE")
    file_name, expected_hash, times = INPUTS[case]
    raw = (PUBLIC / file_name).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected_hash,
            "D_GITHUB_PUBLIC_EVIDENCE_BYTES_CHANGED")
    document = json.loads(raw)
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    validate_evidence(document, contract)
    require(document["case"] == case
            and document["source_snapshot_sha256"] == WORLD_PRECOMMIT
            and tuple(x["t_min"] for x in document["observations"]) == times,
            "D_CASE_MASK_OR_COMMITMENT_MISMATCH")
    require(contract["methods"]["D"]["parameter_grid"] == {
        "capacity_items_per_hour": [48, 72, 96],
        "response_time_hours": [0.125, 0.25],
        "loss_time_hours": [1.0],
    } and contract["methods"]["D"]["construction_RK4_max"] == 18
      and contract["methods"]["D"]["CAF_N_RK4_max"] == 18
      and contract["methods"]["D"]["RK4_integration_max_step_hours"] >= STEP_HOURS,
      "D_GRID_OR_RK4_BUDGET_CHANGED")
    return document, contract, expected_hash


def require_github_one_shot():
    require(os.environ.get("GITHUB_ACTIONS") == "true"
            and os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
            and os.environ.get("GITHUB_REF") == "refs/heads/main"
            and os.environ.get("GITHUB_REPOSITORY") == "yudocyudoc/IGC"
            and os.environ.get("GITHUB_RUN_NUMBER") == "1"
            and os.environ.get("GITHUB_RUN_ATTEMPT") == "1",
            "D_ONLY_FIRST_GITHUB_MAIN_MANUAL_EXECUTION")


def run_case(case, on_invocation=None):
    """Exactly 18 calls; on_invocation called BEFORE each chargeable RK4 call."""
    evidence, contract, input_sha = read_view(case)
    observations = evidence["observations"]
    sample_times = [r["t_min"] / 60 for r in observations]
    expected = [r["delivered"] for r in observations]
    public_pulse = {"rate": 72, "duration": 1/3}
    universe = [x for x in inventory(contract) if x["arm"] == "D"]
    require(len(universe) == 18, "D_INVENTORY_NOT_18")
    outputs = []
    for ordinal, entry in enumerate(universe, start=1):
        require(entry["capacity"] in (48, 72, 96)
                and entry["tau"] in (0.125, 0.25)
                and entry["structure"] in ("D1", "D2", "D3"),
                "D_UNEXPECTED_GRID_ROW")
        stocks = int(entry["structure"][1:])
        params = {"capacity": entry["capacity"],
                  "response_time": entry["tau"], "loss_time": 1.0}
        # Event marker emitted before the actual invocation. On failure,
        # count that candidate as consumed; do not retry automatically.
        if on_invocation is not None:
            on_invocation(case, ordinal)
        curve = integrate(stocks, False, params, public_pulse,
                          sample_times, STEP_HOURS)
        require(len(curve) == len(observations), "D_RK4_BAD_OUTPUT_SIZE")
        mae, rmse = score(list(curve), expected,
                          [x["t_min"] for x in observations])
        structure = topology(stocks, False)
        structure_hash = digest(structure)
        native_source = modelica({
            "structure": structure,
            "structure_hash": structure_hash,
            "nominal_parameters": params,
        }, public_pulse)
        native_sha = "sha256:" + hashlib.sha256(native_source.encode("utf-8")).hexdigest()
        receipt = {
            "schema": "igc-caf01-d-rk4-candidate-receipt/0.1",
            "case": case,
            "candidate": entry["id"],
            "public_construction_input_sha256": "sha256:" + input_sha,
            "observations_hours": sample_times,
            "predicted_delivered": list(curve),
            "native_source_sha256": native_sha,
            "step_hours": STEP_HOURS,
            "balance_certified_upper_bound_orders": BALANCE_CERTIFIED_MAX,
            "status": "RK4_SCREEN_ONLY_NOT_NATIVE_G2",
        }
        outputs.append({
            "id": entry["id"], "structure": entry["structure"],
            "parameters": params, "construction_delivered": list(curve),
            "mae": mae, "rmse": rmse,
            "native_sha256": native_sha,
            "rk4_receipt_sha256": digest(receipt),
            "balance_max_abs": BALANCE_CERTIFIED_MAX,
            "balance_value_is_certified_upper_bound": True,
            "gate": {"G0": "PASS", "G1": "PASS", "G2": "RK4_SCREEN"},
            "native_G2_verified": False,
        })
    # D-only preliminary selection: one representative per topology.
    # Never pretend M/B have been measured or produce locked future curves.
    chosen = {}
    for structure in ("D1", "D2", "D3"):
        group = [r for r in outputs if r["structure"] == structure]
        best = min(group, key=lambda r: (r["mae"], r["id"]))
        chosen[structure] = {"candidate_id": best["id"],
                             "construction_mae": best["mae"],
                             "near_best_alternatives": [
                                 r["id"] for r in group
                                 if r["mae"] <= best["mae"] + 0.25 + 1e-6
                             ],
                             "native_G2_status": "PENDING_NOT_EXECUTED"}
    return {
        "schema": "igc-caf01-d-only-rk4-screen/0.1",
        "case": case,
        "source_GitHub_workflow_run": EXPERIMENTAL_GITHUB_RUN,
        "source_world_precommit": WORLD_PRECOMMIT,
        "source_evidence_file_sha256": "sha256:" + input_sha,
        "actual_RK4_invocations_this_case": 18,
        "native_OpenModelica_simulations": 0,
        "DES_world_runs": 0,
        "Buffalo_provider_calls": 0,
        "parameter_grid": contract["methods"]["D"]["parameter_grid"],
        "candidate_rows": outputs,
        "D_preliminary_representatives": chosen,
        "joint_D_B_M_G3_selection_performed": False,
        "future_evaluation_forecasts_produced": False,
        "evaluation_truth_read": False,
        "CAFN_intermediate_readings_used": False if case == "CAFN" else None,
    }


def invocation_marker(case, ordinal):
    print(f"CAF01_D_RK4_INVOCATION_STARTED case={case} ordinal={ordinal}/18",
          flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--case", choices=("CAF01", "CAFN"), required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    require_github_one_shot()
    # An exact one-shot output directory makes accidental overwritten results fatal.
    require(not args.out.exists(), "D_OUTPUT_ALREADY_EXISTS")
    result = run_case(args.case, on_invocation=invocation_marker)
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "D_RK4_SCREEN.json").write_bytes(canonical(result) + b"\n")
    print(f"CAF01_D_RK4_SCREEN_SUCCESS case={args.case} runs=18", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # No arbitrary exception message; prevent leaking unexpected values.
        print("CAF01_D_RK4_SCREEN_BLOCKED_OR_FAILED_NO_AUTOMATIC_RETRY", flush=True)
        raise SystemExit(1) from None
