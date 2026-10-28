#!/usr/bin/env python3
"""CAF-01 G4 — REF-CAF, REF-SCALE and pre-holdout custody package.

Only public construction D(t) and prescribed pulses are allowed as inputs to
prediction. A(t), P(t) are audit-only sidecar fields and never calibration
features. No DES, RK4, Modelica, Buffalo, holdout or external custody calls.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
from statistics import median

from caf01_g3 import (SCHEMA as G3_SCHEMA, digest, number, validate_evidence,
                      G3Blocked, EPS)

HERE = Path(__file__).resolve().parent
CONTRACT = HERE / "ARENA_PC01_CAF01_CONTRATO_REVISION_v0_3_2026-10-28.json"
SCHEMA = "igc-caf01-g4-references-lock/0.1"
TIMES = (5, 10, 15, 20, 30, 40)
CONSTRUCTION_RATE = 1.2
EVALUATION_RATE = 1.5
DURATION = 20
EXPECTED_ARRIVALS = 24
SCALING = 1.25
REF_CAF_MIN_INTERVALS = 2
QUEUE_PROXY_CUTOFF = 1.0
DESIGN_ABS_DISCREPANCY_ORDERS = 1.0


class G4Blocked(ValueError):
    pass


def require(ok, code):
    if not ok:
        raise G4Blocked(code)


def exact_keys(value, keys, code):
    require(type(value) is dict and set(value) == set(keys), code)


def require_contract(contract):
    # Check meaningful scientific assumptions, never just a mutable label.
    require(contract["boundary"]["losses_allowed"] is False
            and contract["boundary"]["cancellations_allowed"] is False
            and contract["boundary"]["initial_accepted"] == 0
            and contract["boundary"]["initial_delivered"] == 0,
            "G4_BOUNDARY_CHANGED")
    ref = contract["REF_CAF"]
    scale = contract["REF_SCALE"]
    require(ref["method"] == "one_capacity_effective_queue_empirically_calibrated_from_construction_only"
            and ref["refit_after_lock"] is False
            and ref["actual_arrivals_sidecar_not_a_calibration_privilege"] is True
            and ref["calibration"].startswith("median delta_D/5 over >=2 pre-20-min intervals")
            and scale["method"] == "predeclared_proportional_delivered_scaling"
            and scale["rate_ratio"] == SCALING
            and scale["independent_new_world_runs"] == 0,
            "G4_REFERENCE_POLICY_CHANGED")
    require(contract["measurement_times_minutes"] == [0, *TIMES]
            and contract["new_evaluation_scored_times_minutes"] == list(TIMES)
            and contract["worlds"][0]["arrival"] == {
                "kind": "pulse", "rate": CONSTRUCTION_RATE, "duration_minutes": DURATION}
            and contract["worlds"][1]["arrival"] == {
                "kind": "pulse", "rate": EVALUATION_RATE, "duration_minutes": DURATION}
            and contract["source_proposal"]["expected_event_counts_given_half_open_pulse"]
            == {"construction": 24, "evaluation": 30},
            "G4_CLOCK_PULSE_OR_COUNT_CHANGED")
    require(contract["metrics"]["primary"] ==
            ["MAE_delivered_orders_across_6_future_times"]
            and "MAE_pending_orders" in contract["metrics"]["derived_not_independent"]
            and "RMSE_pending_orders" in contract["metrics"]["derived_not_independent"]
            and contract["metrics"]["descriptive_gain_rule_vs_REF_CAF"].startswith(
                "MAE_delivered improves by >=1 order"),
            "G4_SCORE_POLICY_CHANGED")


def arrivals_design(rate, minute):
    return rate * min(minute, DURATION)


def validate_source(evidence, contract):
    require_contract(contract)
    try:
        times, values = validate_evidence(evidence, contract)
    except (G3Blocked, KeyError, TypeError) as exc:
        raise G4Blocked("G4_COMMON_PUBLIC_CONSTRUCTION_INVALID") from exc
    # The half-open deterministic schedule guarantees exactly 24 entries by
    # t=40. A 25th delivery cannot be waved away as instrument noise.
    require(values[-1] <= EXPECTED_ARRIVALS + EPS, "G4_MORE_DELIVERIES_THAN_PUBLIC_ARRIVALS")
    return times, values


def forecast(evidence, contract):
    """Return both baselines or typed abstentions without privileged sidecar."""
    times, delivered = validate_source(evidence, contract)
    origin = {"schema": SCHEMA, "case": evidence["case"],
              "construction_evidence_sha256": digest(evidence),
              "source_snapshot_sha256": evidence["source_snapshot_sha256"],
              "public_evaluation_pulse": {
                  "kind": "pulse", "rate_per_minute": EVALUATION_RATE,
                  "duration_minutes": DURATION},
              "scored_times_minutes": list(TIMES),
              "input_features": ["CONSTRUCTION_DELIVERED_ONLY", "PRESCRIBED_ARRIVAL_PULSES"],
              "actual_arrivals_sidecar_used_in_fit": False,
              "pending_is_derived_not_independent": True,
              "independent_new_world_runs": 0,
              "reference_solver_runs": 0}
    if evidence["case"] == "CAFN":
        # Only [D(0), D(40)] are visible. Neither REF model can invent an
        # intermediate construction trajectory or saturated-interval evidence.
        refs = {
            "REF_CAF": {
                "status": "REF_CAPACITY_NOT_IDENTIFIABLE",
                "reason": "CAFN_ONLY_ENDPOINTS_NO_TWO_SATURATED_CONSTRUCTION_INTERVALS",
                "eligible_intervals": [], "effective_rate_orders_per_min": None,
                "predicted_delivered": None, "predicted_pending_derived": None,
            },
            "REF_SCALE": {
                "status": "REF_SCALE_INTERMEDIATE_DATA_NOT_AVAILABLE",
                "reason": "CAFN_MASK_NO_INTERMEDIATE_CONSTRUCTION_D_VALUES",
                "predicted_delivered": None, "predicted_pending_derived": None,
            },
        }
        origin["CAFN_diagnostic"] = {
            "observed_terminal_delivered_orders": delivered[-1],
            "public_design_total_accepted_orders": EXPECTED_ARRIVALS,
            "terminal_pending_proxy_orders": EXPECTED_ARRIVALS-delivered[-1],
            "peak_time_identifiable": False,
            "intermediate_pending_path_identifiable": False,
            "individual_waiting_times_observed": False,
        }
    else:
        # Candidate windows [0,5],[5,10],[10,15],[15,20]. Because the
        # initial backlog proxy is exactly 0, the first window never qualifies.
        eligible = []
        for i in range(4):
            a, b = times[i], times[i+1]
            pa = arrivals_design(CONSTRUCTION_RATE, a) - delivered[i]
            pb = arrivals_design(CONSTRUCTION_RATE, b) - delivered[i+1]
            if pa > QUEUE_PROXY_CUTOFF and pb > QUEUE_PROXY_CUTOFF:
                throughput = (delivered[i+1] - delivered[i])/(b-a)
                eligible.append({"start_min": a, "end_min": b,
                                 "observed_deliveries_delta": delivered[i+1]-delivered[i],
                                 "rate_orders_per_min": throughput})
        if len(eligible) < REF_CAF_MIN_INTERVALS:
            ref_caf = {
                "status": "REF_CAPACITY_NOT_IDENTIFIABLE",
                "reason": "FEWER_THAN_TWO_PRE_20_INTERVALS_WITH_PROXY_BACKLOG_GT_ONE_AT_BOTH_ENDPOINTS",
                "eligible_intervals": eligible, "effective_rate_orders_per_min": None,
                "predicted_delivered": None, "predicted_pending_derived": None,
            }
        else:
            rate = float(median(x["rate_orders_per_min"] for x in eligible))
            # Analytic mass-conserving fluid queue with zero initial stocks,
            # arrivals only for 20 min and no internal staging/delay. Never
            # interpret this empirical rate as the DES physical bottleneck.
            pred = [min(arrivals_design(EVALUATION_RATE, t), rate*t) for t in TIMES]
            ref_caf = {
                "status": "READY_CONDITIONAL_EMPIRICAL_RATE_NOT_PHYSICAL_CAPACITY",
                "reason": None, "eligible_intervals": eligible,
                "effective_rate_orders_per_min": rate,
                "effective_rate_orders_per_hour": 60*rate,
                "predicted_delivered": pred,
                "predicted_pending_derived": [
                    arrivals_design(EVALUATION_RATE, t)-y for t,y in zip(TIMES,pred)],
                "model": "SINGLE_FLUID_QUEUE_WITH_NO_INTERNAL_DELAY",
            }
        scaled = [min(arrivals_design(EVALUATION_RATE,t), SCALING*y)
                  for t, y in zip(times[1:], delivered[1:])]
        ref_scale = {
            "status": "READY_PRESCRIBED_INPUT_RATIO_ONLY",
            "rate_ratio": SCALING,
            "predicted_delivered": scaled,
            "predicted_pending_derived": [
                arrivals_design(EVALUATION_RATE, t)-y for t,y in zip(TIMES,scaled)],
            "interpretation": "PROPORTIONAL_TRANSFERENCE_NOT_STRUCTURAL_RECOVERY",
        }
        refs = {"REF_CAF": ref_caf, "REF_SCALE": ref_scale}
    result = {**origin, "references": refs,
              "primary_outcome": "CUMULATIVE_DELIVERED_ONLY",
              "future_truth_seen": False,
              "generalization_claim": "NONE"}
    result["references_sha256"] = digest(result)
    return result


def audit_arrival_sidecar(evidence, sidecar, contract):
    """Independent exposure/balance audit; NEVER a feature for forecast()."""
    times, delivered = validate_source(evidence, contract)
    exact_keys(sidecar, ("schema", "case", "source_snapshot_sha256",
                         "observations"), "G4_AUDIT_SIDECAR_FIELDS")
    require(sidecar["schema"] == SCHEMA
            and sidecar["case"] == evidence["case"]
            and sidecar["source_snapshot_sha256"] == evidence["source_snapshot_sha256"],
            "G4_AUDIT_SIDECAR_IDENTITY")
    entries = sidecar["observations"]
    require(type(entries) is list and len(entries) == len(times), "G4_AUDIT_SIDECAR_TIMES")
    mismatch = []
    previous = 0
    for item, t, d in zip(entries, times, delivered):
        exact_keys(item, ("t_min", "accepted_cum_orders", "pending_orders"),
                   "G4_AUDIT_SIDECAR_ROW_FIELDS")
        accepted, pending = item["accepted_cum_orders"], item["pending_orders"]
        require(item["t_min"] == t
                and type(accepted) is int and accepted >= previous
                and type(pending) in (float, int) and math.isfinite(pending)
                and pending >= -EPS and abs(accepted-d-pending) <= EPS,
                "G4_AUDIT_NATIVE_MATERIAL_SNAPSHOT_INCONSISTENT")
        delta = accepted-arrivals_design(CONSTRUCTION_RATE,t)
        require(abs(delta) <= DESIGN_ABS_DISCREPANCY_ORDERS+EPS,
                "G4_AUDIT_EVENT_VS_DESIGN_DISCREPANCY_TOO_LARGE")
        mismatch.append(delta)
        previous = accepted
    require(entries[-1]["accepted_cum_orders"] == EXPECTED_ARRIVALS,
            "G4_AUDIT_FINAL_ARRIVAL_COUNT_MISMATCH")
    return {"status": "PUBLIC_SIDECAR_AGGREGATE_BALANCE_AUDIT_ONLY",
            "evidence_sha256": digest(evidence),
            "sidecar_sha256": digest(sidecar),
            "event_minus_ideal_orders": mismatch,
            "used_to_fit_REF_CAF_or_REF_SCALE": False,
            "physical_internal_stocks_independently_verified": False}


def prepare_preholdout_package(contract, evidence, selection, g3_lock):
    """Prepare G3 + G4 content for independent immutable custody.

    The local SHA does NOT constitute external custody, a trusted timestamp
    or authorization to release evaluation truth.
    """
    refs = forecast(evidence, contract)
    require(type(selection) is dict and type(g3_lock) is dict,
            "G4_LOCK_INPUT_MALFORMED")
    s_body = {k:v for k,v in selection.items() if k != "selection_sha256"}
    l_body = {k:v for k,v in g3_lock.items() if k != "forecast_lock_sha256"}
    require(selection.get("selection_sha256") == digest(s_body)
            and g3_lock.get("forecast_lock_sha256") == digest(l_body),
            "G4_G3_CONTENT_HASH_INVALID")
    require(selection.get("schema") == G3_SCHEMA
            and g3_lock.get("schema") == G3_SCHEMA
            and selection.get("status") == "CONSTRUCTION_SELECTION_ONLY_NOT_HOLDOUT"
            and g3_lock.get("status") ==
            "LOCK_CONTENT_PREPARED_NEEDS_EXTERNAL_IMMUTABLE_CUSTODY"
            and selection.get("case") == evidence["case"] == g3_lock.get("case")
            and selection.get("source_snapshot_sha256") ==
            evidence["source_snapshot_sha256"] == g3_lock.get("source_snapshot_sha256")
            and selection.get("construction_observation_sha256") == digest(evidence)
            and selection.get("contract_sha256") == digest(contract)
            and g3_lock.get("selection_sha256") == selection["selection_sha256"]
            and g3_lock.get("evaluation_pulse") == refs["public_evaluation_pulse"]
            and g3_lock.get("evaluation_truth_included") is False
            and g3_lock.get("external_reveal_authorized") is False
            and g3_lock.get("g4_reference_baselines_still_require_separate_lock") is True,
            "G4_G3_PROVENANCE_OR_REVEAL_GUARD_FAILED")
    if evidence["case"] == "CAFN":
        require(g3_lock.get("forecast_by_candidate") == {}
                and g3_lock.get("evaluation_times_minutes") == [],
                "G4_CAFN_MUST_ABSTAIN_NO_CURVES")
    else:
        require(g3_lock.get("evaluation_times_minutes") == list(TIMES),
                "G4_G3_EVALUATION_TIMES_CHANGED")
    require(type(g3_lock.get("arm_forecasts")) is dict
            and set(g3_lock["arm_forecasts"]) == {"D","B","M"},
            "G4_G3_ARM_COMPLETENESS")
    bundle = {
        "schema": SCHEMA,
        "status": "PREHOLDOUT_PACKAGE_READY_AWAITING_EXTERNAL_CUSTODY",
        "contract_sha256": digest(contract),
        "construction_evidence_sha256": digest(evidence),
        "source_snapshot_sha256": evidence["source_snapshot_sha256"],
        "case": evidence["case"],
        "selection_sha256": selection["selection_sha256"],
        "g3_forecast_lock_sha256": g3_lock["forecast_lock_sha256"],
        "g3_lock": copy.deepcopy(g3_lock),
        "references": refs,
        "scoring_policy": {
            "primary": "MAE_DELIVERED_SIX_TIMES_EXCLUDING_T0",
            "secondary": "RMSE_DELIVERED_SAME_SIX_TIMES",
            "pending": "DERIVED_NOT_INDEPENDENT",
            "reference_gain_rule": "DESCRIPTIVE_AT_LEAST_ONE_ORDER_MAE_OVER_REF_CAF",
            "reference_scale": "SEPARATE_PROPORTIONALITY_CONTROL_NO_CAUSAL_RECOVERY",
            "negative_control": "CAFN_NO_INTERMEDIATE_OR_PEAK_TIMING_INFERENCE",
            "inferential_generalization": "NONE",
        },
        "actual_evaluation_values_included": False,
        "actual_arrivals_sidecar_used_to_calibrate": False,
        "custody": {
            "state": "NOT_CUSTODIED_EXTERNAL_WITNESS_REQUIRED",
            "external_receipt_id": None, "external_verified_timestamp": None,
            "external_witness_attestation_sha256": None,
            "release_authorized": False,
        },
        "resource_consumption": {
            "DES_world_runs": 0, "RK4_integrations": 0,
            "OpenModelica_simulations": 0, "Buffalo_provider_calls": 0,
        },
    }
    bundle["preholdout_package_sha256"] = digest(bundle)
    return bundle


def score_six_delivered_values(predicted, observed):
    """Pure arithmetic for AFTER independently authorized holdout release.

    This callable does not authenticate a custody receipt. Never use its
    existence as authorization to supply actual withheld evaluation values.
    Tests intentionally pass invented values only.
    """
    require(type(predicted) is list and type(observed) is list
            and len(predicted) == len(observed) == len(TIMES),
            "G4_SCORE_SIX_TIMES_REQUIRED")
    require(all(number(y) and y >= -EPS
                and y <= arrivals_design(EVALUATION_RATE, t)+1+EPS
                for t,y in zip(TIMES,predicted))
            and all(type(y) is int and
                    0 <= y <= arrivals_design(EVALUATION_RATE,t)+1+EPS
                    for t,y in zip(TIMES,observed)),
            "G4_SCORE_PHYSICAL_VALUES_REQUIRED")
    require(all(b+EPS >= a for a,b in zip(predicted,predicted[1:]))
            and all(b >= a for a,b in zip(observed,observed[1:]))
            and observed[-1] <= 30,
            "G4_SCORE_NONMONOTONE_OR_EXCESS_DELIVERIES")
    errors=[float(p)-float(y) for p,y in zip(predicted,observed)]
    return {
        "status":"DESCRIPTIVE_SIX_TIMES_NO_GENERALIZATION",
        "MAE_delivered_orders":sum(abs(d) for d in errors)/6,
        "RMSE_delivered_orders":math.sqrt(sum(d*d for d in errors)/6),
        "observation_count":6,
        "pending_independent_evidence":False,
    }


def canonical_json_bytes(data):
    return json.dumps(data,sort_keys=True,ensure_ascii=False,
                      separators=(",",":"),allow_nan=False).encode("utf-8")+b"\\n"


def emit_custody_candidate(bundle, output_dir):
    """Create a byte-identical, non-overwriting package for EXTERNAL custody.

    File SHA applies to *all file bytes* (including embedded internal hash and
    newline). The internal SHA is of content before adding its self-hash, so
    these two SHA values are expected to differ. Neither is a timestamp.
    """
    require(type(bundle) is dict and bundle.get("schema") == SCHEMA
            and bundle.get("status") ==
            "PREHOLDOUT_PACKAGE_READY_AWAITING_EXTERNAL_CUSTODY",
            "G4_WRONG_PACKAGE_TYPE")
    content={k:v for k,v in bundle.items()
             if k!="preholdout_package_sha256"}
    require(bundle.get("preholdout_package_sha256")==digest(content)
            and bundle["custody"]["state"]==
            "NOT_CUSTODIED_EXTERNAL_WITNESS_REQUIRED"
            and bundle["custody"]["release_authorized"] is False
            and bundle["actual_evaluation_values_included"] is False,
            "G4_PACKAGE_TAMPERED_OR_ALREADY_RELEASED")
    directory=Path(output_dir)
    require(not directory.exists(), "G4_CUSTODY_OUTPUT_ALREADY_EXISTS")
    directory.mkdir(parents=True,exist_ok=False)
    data=canonical_json_bytes(bundle)
    name="preholdout-package.json"
    (directory/name).write_bytes(data)
    byte_hash=hashlib.sha256(data).hexdigest()
    (directory/"preholdout-package.sha256").write_text(
        byte_hash+"  "+name+"\\n",encoding="utf-8")
    return {"status":"BYTES_EMITTED_NOT_EXTERNAL_CUSTODY",
            "internal_content_sha256":bundle["preholdout_package_sha256"],
            "complete_file_sha256":"sha256:"+byte_hash,
            "files":[name,"preholdout-package.sha256"],
            "external_witness_receipt":None,"evaluation_release_authorized":False}


def main():
    p=argparse.ArgumentParser(description="G4: pre-holdout package ONLY; does not custody or evaluate")
    p.add_argument("--evidence",required=True,type=Path)
    p.add_argument("--selection",required=True,type=Path)
    p.add_argument("--g3-lock",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    contract=json.loads(CONTRACT.read_text(encoding="utf-8"))
    evidence=json.loads(a.evidence.read_text(encoding="utf-8"))
    selection=json.loads(a.selection.read_text(encoding="utf-8"))
    g3=json.loads(a.g3_lock.read_text(encoding="utf-8"))
    bundle=prepare_preholdout_package(contract,evidence,selection,g3)
    print(json.dumps(emit_custody_candidate(bundle,a.out),sort_keys=True))


if __name__=="__main__":
    main()
