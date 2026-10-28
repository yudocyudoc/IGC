#!/usr/bin/env python3
"""CAF-01 G3 decision policy: construction-only ranking and pre-holdout lock.

No provider, RK4, OpenModelica, DES, future outcome, or G2 assertion is
generated here. An external evidence custodian must verify submitted G2
receipts and persist the forecast lock BEFORE releasing evaluation truth.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

from caf01_m_equivalence import certificate

HERE = Path(__file__).resolve().parent
CONTRACT = HERE / "ARENA_PC01_CAF01_CONTRATO_REVISION_v0_3_2026-10-28.json"
SCHEMA = "igc-caf01-g3-decision/0.1"
EPS = 1e-6           # numeric identity only, NOT an instrument/noise bound
BAND = 0.25          # operational competitive band, NOT measurement error
MASS = 0.008         # G2 stock-balance ceiling (orders); conditional
PARITY = 0.012      # original D Python/OMC parity check; conditional
SHA = re.compile(r"^sha256:[0-9a-f]{64}$")


class G3Blocked(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise G3Blocked(code)


def digest(value):
    return "sha256:" + hashlib.sha256(json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
        allow_nan=False).encode("utf-8")).hexdigest()


def number(x):
    return type(x) in (int, float) and math.isfinite(x)


def exact_keys(value, keys, code):
    require(type(value) is dict and set(value) == set(keys), code)


def inventory(contract):
    """Admissible *executed* configurations, no private generator assumptions."""
    d, m, b = (contract["methods"][a] for a in ("D", "M", "B"))
    cert = certificate(contract)
    require(cert["status"] == "STATIC_UPPER_BOUND_ONLY"
            and cert["inactive_capacities"] == [72, 100]
            and cert["within_structure_upper_bound_classes"] == 6
            and cert["nominal_configurations"] == 9, "G3_M_CERTIFICATE_MISMATCH")
    require(d["topology_stock_counts"] == [1, 2, 3]
            and d["loss_variants"] == [False]
            and d["parameter_grid"] == {
                "capacity_items_per_hour": [48, 72, 96],
                "response_time_hours": [0.125, 0.25],
                "loss_time_hours": [1.0]}
            and b["candidate_models_max"] == 1, "G3_ARM_INVENTORY_CHANGED")
    require(contract["budget"]["OpenModelica_candidate_runs"]["total_max"] == 26
            and contract["budget"]["Python_RK4_integrations_D"]["total_max"] == 36
            and contract["budget"]["DES_world_runs"]["total_max"] == 2
            and contract["budget"]["provider_inferences"]["Buffalo_max"] == 2,
            "G3_BUDGET_CONTRACT_CHANGED")
    items = []
    for stocks in (1, 2, 3):
        for cap in (48, 72, 96):
            for tau in (0.125, 0.25):
                items.append({"id": f"D{stocks}_C{cap}_T{tau:g}", "arm": "D",
                              "structure": f"D{stocks}", "capacity": cap,
                              "tau": tau, "nominal_aliases": []})
    for structure in m["structural_classes"]:
        for cap, aliases in ((20, [20]), (72, [72, 100])):
            items.append({"id": f"M_{structure}_C{cap}", "arm": "M",
                          "structure": structure, "capacity": cap, "tau": 0.5,
                          "nominal_aliases": aliases})
    items.append({"id": "B_NATIVE_1", "arm": "B", "structure": "B_UNVERIFIED",
                  "capacity": None, "tau": None, "nominal_aliases": []})
    require(len(items) == 25, "G3_INVENTORY_SIZE_INCORRECT")
    return items


def plan(contract):
    items = inventory(contract)
    return {
        "schema": SCHEMA,
        "status": "POLICY_PREPARED_NOT_EXPERIMENT_AUTHORIZED",
        "contract_sha256": digest(contract),
        "construction_candidate_inventory": items,
        "proposed_max_modelica_per_phase": {"D": 3, "M": 6, "B": 1},
        "conditional_total_modelica_ceiling": 20,
        "v03_original_modelica_ceiling_unchanged": 26,
        "RK4_D_CAF01_max": 18, "RK4_D_CAFN_max": 18,
        "DES_worlds_max": 2, "Buffalo_calls_max": 2,
        "comparison_policy": {"primary": "MAE_DELIVERED_CONSTRUCTION_ONLY",
                              "competitive_band_orders": BAND,
                              "numeric_equality_orders": EPS,
                              "material_balance_tolerance_orders": MASS,
                              "D_RK4_OMC_parity_max_abs_orders": PARITY},
        "m_proven_capacity_aliases": {"C00": [72, 100],
                                     "C01": [72, 100], "C02": [72, 100]},
        "restrictions": [
            "M grouping is conditional on unchanged E1 release and native material conservation.",
            "20 OM is a ceiling conditional on M equivalence, not an authorization or actual saving.",
            "D's 18 RK4 fits precede selecting at most one native candidate per topology.",
            "G2 receipts must be verified independently; hashes in supplied rows are assertions.",
            "No future observation may be an input to G3 selection.",
            "CAF-N uses only t=0 and t=40 construction observations, never full-series rankings.",
        ]
    }


def validate_evidence(evidence, contract):
    exact_keys(evidence, ("schema", "case", "source_snapshot_sha256",
                          "observations", "public_pulse"), "G3_EVIDENCE_FIELDS")
    require(evidence["schema"] == SCHEMA and evidence["case"] in ("CAF01", "CAFN")
            and type(evidence["source_snapshot_sha256"]) is str
            and SHA.fullmatch(evidence["source_snapshot_sha256"]) is not None,
            "G3_EVIDENCE_IDENTITY")
    exact_keys(evidence["public_pulse"], ("kind", "rate_per_minute",
                                          "duration_minutes"), "G3_PULSE_FIELDS")
    p = evidence["public_pulse"]
    require(p == {"kind": "pulse", "rate_per_minute": 1.2,
                  "duration_minutes": 20}, "G3_CONSTRUCTION_PULSE_CHANGED")
    rows = evidence["observations"]
    times = [0, 5, 10, 15, 20, 30, 40] if evidence["case"] == "CAF01" else [0, 40]
    require(type(rows) is list and len(rows) == len(times), "G3_CONSTRUCTION_MASK")
    vals = []
    for row, t in zip(rows, times):
        exact_keys(row, ("t_min", "delivered"), "G3_OBSERVATION_FIELDS")
        require(row["t_min"] == t and number(row["delivered"])
                and row["delivered"] >= 0, "G3_BAD_OBSERVATION")
        vals.append(float(row["delivered"]))
    require(abs(vals[0]) <= EPS and all(y + EPS >= x for x, y in zip(vals, vals[1:])),
            "G3_OBSERVATION_MONOTONICITY")
    for t, y in zip(times, vals):
        # One order of count/integral mismatch is known from discrete arrivals.
        require(y <= (1.2 * min(t, 20)) + 1 + EPS, "G3_DELIVERED_EXCEEDS_INPUT")
    return times, vals


def score(pred, obs, times):
    require(type(pred) is list and len(pred) == len(obs), "G3_PREDICTION_SHAPE")
    vals = []
    for y, t in zip(pred, times):
        require(number(y) and y >= -EPS
                and y <= 1.2 * min(t, 20) + 1 + EPS, "G3_NONPHYSICAL_CONSTRUCTION_PREDICTION")
        vals.append(float(y))
    require(abs(vals[0]) <= EPS
            and all(b + EPS >= a for a, b in zip(vals, vals[1:])),
            "G3_NONMONOTONE_CONSTRUCTION_PREDICTION")
    diffs = [a-b for a,b in zip(vals[1:], obs[1:])]
    return (sum(abs(x) for x in diffs) / len(diffs),
            math.sqrt(sum(x*x for x in diffs) / len(diffs)))


def select(contract, evidence, rows):
    """Validate COMPLETE inventory and choose by construction data only.

    All absent models must be represented as BLOCKED rows, not silently dropped.
    """
    times, obs = validate_evidence(evidence, contract)
    expected = {x["id"]: x for x in inventory(contract)}
    require(type(rows) is list and len(rows) == len(expected), "G3_INCOMPLETE_MANIFEST")
    byid = {}
    for r in rows:
        exact_keys(r, ("id", "gates", "construction_delivered",
                       "native_sha256", "g2_receipt_sha256",
                       "rk4_receipt_sha256", "balance_max_abs", "rk4_native_max_abs_delta",
                       "block_reason", "candidate_evidence_sha256"), "G3_CANDIDATE_FIELDS")
        require(r["candidate_evidence_sha256"] == digest(evidence),
                "G3_CANDIDATE_EVIDENCE_HASH_MISMATCH")
        ident = r["id"]
        require(type(ident) is str and ident in expected
                and ident not in byid, "G3_UNKNOWN_OR_DUPLICATE_CANDIDATE")
        exact_keys(r["gates"], ("G0", "G1", "G2"), "G3_GATE_FIELDS")
        require(all(x in ("PASS", "RK4_SCREEN", "BLOCKED", "FAIL", "PENDING")
                    for x in r["gates"].values()), "G3_GATE_STATUS")
        arm = expected[ident]["arm"]
        g = r["gates"]
        screened = (arm == "D" and g["G0"] == g["G1"] == "PASS"
                    and g["G2"] == "RK4_SCREEN")
        native_pass = all(x == "PASS" for x in g.values())
        require(not (g["G0"] == "RK4_SCREEN" or g["G1"] == "RK4_SCREEN"
                     or (g["G2"] == "RK4_SCREEN" and arm != "D")),
                "G3_RK4_SCOPE_ONLY_D")
        if screened or native_pass:
            require(isinstance(r["native_sha256"], str) and
                    SHA.fullmatch(r["native_sha256"]) is not None,
                    "G3_MISSING_NATIVE_SOURCE_HASH")
            require(number(r["balance_max_abs"]) and
                    0 <= r["balance_max_abs"] <= MASS, "G3_UNVERIFIED_MATERIAL_BALANCE")
            if arm == "D":
                require(isinstance(r["rk4_receipt_sha256"], str) and
                        SHA.fullmatch(r["rk4_receipt_sha256"]) is not None,
                        "G3_MISSING_D_RK4_RECEIPT")
            else:
                require(r["rk4_receipt_sha256"] is None,
                        "G3_RK4_NOT_APPLICABLE_TO_B_M")
            if native_pass and arm == "D":
                require(number(r["rk4_native_max_abs_delta"])
                        and 0 <= r["rk4_native_max_abs_delta"] <= PARITY,
                        "G3_D_RK4_NATIVE_PARITY_UNVERIFIED")
            else:
                require(r["rk4_native_max_abs_delta"] is None,
                        "G3_NATIVE_PARITY_UNSCOPED")
            if native_pass:
                require(isinstance(r["g2_receipt_sha256"], str) and
                        SHA.fullmatch(r["g2_receipt_sha256"]) is not None,
                        "G3_MISSING_NATIVE_G2_RECEIPT")
            else:
                require(r["g2_receipt_sha256"] is None,
                        "G3_RK4_SCREEN_CANNOT_CLAIM_NATIVE_G2")
            require(r["block_reason"] is None, "G3_READY_WITH_BLOCK_REASON")
            mae, rmse = score(r["construction_delivered"], obs, times)
            byid[ident] = {"id": ident, "arm": arm,
                           "structure": expected[ident]["structure"],
                           "mae": mae, "rmse": rmse, "eligible": True,
                           "native_g2_pass": native_pass}
        else:
            require(r["construction_delivered"] is None
                    and (r["native_sha256"] is None or
                         (isinstance(r["native_sha256"], str) and
                          SHA.fullmatch(r["native_sha256"])))
                    and r["g2_receipt_sha256"] is None
                    and r["rk4_receipt_sha256"] is None
                    and r["balance_max_abs"] is None
                    and r["rk4_native_max_abs_delta"] is None
                    and type(r["block_reason"]) is str and bool(r["block_reason"]),
                    "G3_BLOCKED_ROW_CANNOT_CLAIM_G2_OR_CURVE")
            byid[ident] = {"id": ident, "arm": arm,
                           "structure": expected[ident]["structure"],
                           "eligible": False, "block_reason": r["block_reason"],
                           "gates": r["gates"]}
    decisions = {}
    for arm in ("D", "M", "B"):
        all_arm = [byid[x["id"]] for x in expected.values() if x["arm"] == arm]
        valid = [v for v in all_arm if v["eligible"]]
        if not valid:
            decisions[arm] = {"status": "NO_VALID_CANDIDATE", "winners": [],
                              "representatives": [], "parameter_ambiguity": False,
                              "blocked": [v["id"] for v in all_arm],
                              "representatives_pending_g2": [],
                              "winners_pending_g2": []}
            continue
        structures = sorted({v["structure"] for v in valid})
        representatives = []
        structure_alternatives = {}
        for struct in structures:
            candidates = [v for v in valid if v["structure"] == struct]
            # deterministic lexical fallback is ONLY an execution representative
            # not a statement that nearby parameters were identified.
            best = min(candidates, key=lambda v:(v["mae"], v["id"]))
            alternatives = [v["id"] for v in candidates
                            if v["mae"] <= best["mae"] + BAND + EPS]
            representatives.append(best)
            structure_alternatives[struct] = alternatives
        champion = min(x["mae"] for x in representatives)
        winners = [x for x in representatives if x["mae"] <= champion+BAND+EPS]
        ambiguity = any(len(structure_alternatives[x["structure"]])>1 for x in winners)
        decisions[arm] = {
            "status": ("STRUCTURE_OR_PARAMETER_NOT_IDENTIFIABLE"
                       if len(winners) > 1 or ambiguity else "CONDITIONAL_SINGLE_WINNER"),
            "winners": [x["id"] for x in winners],
            "representatives": [x["id"] for x in representatives],
            "parameter_ambiguity": ambiguity,
            "near_best_alternatives": {s: ids for s, ids in structure_alternatives.items()},
            "best_mae": champion,
            "blocked": [v["id"] for v in all_arm if not v["eligible"]],
            "representatives_pending_g2": [x["id"] for x in representatives
                                           if not x["native_g2_pass"]],
            "winners_pending_g2": [x["id"] for x in winners
                                   if not x["native_g2_pass"]],
        }
    report = {
        "schema": SCHEMA,
        "status": "CONSTRUCTION_SELECTION_ONLY_NOT_HOLDOUT",
        "case": evidence["case"],
        "contract_sha256": digest(contract),
        "source_snapshot_sha256": evidence["source_snapshot_sha256"],
        "construction_observation_sha256": digest(evidence),
        "inventory_sha256": digest(list(expected.values())),
        "decision": decisions,
        "selection_metric": "MAE_DELIVERED_EXCLUDING_T0",
        "competitive_band_orders": BAND,
        "numeric_equality_orders": EPS,
        "g2_evidence": "RK4_SCREEN_NOT_NATIVE_G2; RECEIPT_HASH_REQUIRES_EXTERNAL_VERIFICATION",
        "known_limitations": [
            "Competitive band is a prospective decision rule, NOT sensor noise bound.",
            "Construction fit is not causal recovery or a statistical test.",
            "D's 18 RK4 rows are screened before native G2; only preselected representatives can receive native G2.",
            "Native G2 failure or D RK4/OMC parity failure blocks a representative; never reselect using future data.",
            "G2 receipt hashes and balances are not independently fetched by this module.",
            "M C72 represents the C72/C100 proven capacity alias within each structure.",
            "CAF-N intermediate backlog and peak timing are NOT IDENTIFIABLE.",
        ]
    }
    report["selection_sha256"] = digest(report)
    return report


def lock_forecasts(contract, selection, submission):
    """Lock construction-selected diagnostics without consulting holdout truth.

    CAF-N never requests future curves. For CAF01, an individual D candidate
    failing its post-RK4 native G2 check forces *D-only* abstention; it never
    invalidates otherwise correctly submitted M or B forecasts. A malformed
    shared manifest/provenance still fails closed for all arms.
    """
    exact_keys(submission, ("schema", "selection_sha256",
                            "source_snapshot_sha256", "evaluation_pulse",
                            "forecast_by_candidate", "native_g2_checks"),
               "G3_LOCK_INPUT_FIELDS")
    original_selection = {k: v for k, v in selection.items()
                          if k != "selection_sha256"}
    require(selection.get("selection_sha256") == digest(original_selection),
            "G3_SELECTION_TAMPERED")
    require(submission["schema"] == SCHEMA
            and selection["schema"] == SCHEMA
            and selection["status"] == "CONSTRUCTION_SELECTION_ONLY_NOT_HOLDOUT"
            and selection["contract_sha256"] == digest(contract)
            and submission["selection_sha256"] == selection["selection_sha256"]
            and submission["source_snapshot_sha256"] ==
            selection["source_snapshot_sha256"], "G3_LOCK_PROVENANCE_MISMATCH")
    require(submission["evaluation_pulse"] ==
            {"kind": "pulse", "rate_per_minute": 1.5, "duration_minutes": 20},
            "G3_EVALUATION_PULSE_CHANGED")
    supplied = submission["forecast_by_candidate"]
    checks = submission["native_g2_checks"]
    require(type(supplied) is dict, "G3_LOCK_FORECAST_BAD_TYPE")
    require(type(checks) is dict, "G3_NATIVE_G2_CHECKS_BAD")

    # CAF-N is a negative control about non-identifiability from endpoints,
    # NOT a future trajectory prediction exercise. Demanding six invented
    # values would spend an unauthorized budget and fake an informative curve.
    if selection["case"] == "CAFN":
        require(not supplied and not checks,
                "G3_CAFN_NO_FUTURE_CURVES_OR_ADDITIONAL_NATIVE_G2")
        arm_results = {}
        for arm, chosen in selection["decision"].items():
            winners = chosen["winners"]
            arm_results[arm] = {
                "status": ("CAFN_INTERNAL_PATH_AND_PEAK_UNIDENTIFIABLE"
                           if winners else "NO_VALID_CANDIDATE"),
                "prediction": None, "envelope": None, "winners": winners,
                "internal_trajectory_identifiable": False,
                "non_identifiable": [
                    "INTERMEDIATE_BACKLOG_TRAJECTORY",
                    "TIME_OF_PEAK_PENDING",
                    "INDIVIDUAL_WAITING_TIMES",
                ],
            }
        effective_forecasts = {}
        d_outcomes = {}
        discarded_d = []
    else:
        require(selection["case"] == "CAF01", "G3_UNKNOWN_SELECTION_CASE")
        d_decision = selection["decision"]["D"]
        pending = set(d_decision["winners_pending_g2"])
        planned = set(d_decision["representatives"])
        require(set(checks).issubset(pending) and pending.issubset(planned),
                "G3_NATIVE_G2_ONLY_PRESELECTED_D_WINNERS")

        # A known D check may fail scientifically. Record its result rather
        # than treating that as a schema error for independent arms B and M.
        # Never select an alternate D winner after a failure.
        d_outcomes = {}
        safe_checks = {}
        for ident in sorted(pending):
            if ident not in checks:
                d_outcomes[ident] = "FAIL_MISSING_NATIVE_G2_RECEIPT"
                continue
            receipt = checks[ident]
            exact_keys(receipt, ("g2_receipt_sha256", "balance_max_abs",
                                 "rk4_native_max_abs_delta"),
                       "G3_NATIVE_G2_CHECK_FIELDS")
            sha = receipt["g2_receipt_sha256"]
            mass = receipt["balance_max_abs"]
            parity = receipt["rk4_native_max_abs_delta"]
            sha_ok = type(sha) is str and SHA.fullmatch(sha) is not None
            mass_ok = number(mass)
            parity_ok = number(parity)
            safe_checks[ident] = {
                "g2_receipt_sha256": sha if sha_ok else None,
                "balance_max_abs": mass if mass_ok else None,
                "rk4_native_max_abs_delta": parity if parity_ok else None,
            }
            if not sha_ok:
                d_outcomes[ident] = "FAIL_INVALID_NATIVE_G2_RECEIPT"
            elif not mass_ok or not (0 <= mass <= MASS):
                d_outcomes[ident] = "FAIL_MATERIAL_BALANCE"
            elif not parity_ok or not (0 <= parity <= PARITY):
                d_outcomes[ident] = "FAIL_D_RK4_NATIVE_PARITY"
            else:
                d_outcomes[ident] = "PASS"
        d_failed = sorted(i for i, status in d_outcomes.items() if status != "PASS")

        # For D: either ALL construction-selected winners pass native G2,
        # or D abstains as an arm. Do not promote a runner-up opportunistically.
        # An optional already-produced D curve from a failed candidate is
        # explicitly discarded, never validated as G2 or included in the lock.
        required = {winner for arm, decision in selection["decision"].items()
                    if arm != "D" or not d_failed
                    for winner in decision["winners"]}
        allowed = required | (set(d_decision["winners"]) if d_failed else set())
        require(required.issubset(supplied) and set(supplied).issubset(allowed),
                "G3_LOCK_FORECAST_MISSING_OR_EXTRANEOUS")
        discarded_d = sorted(set(supplied) - required)
        effective_forecasts = {key: supplied[key] for key in sorted(required)}
        times = (5, 10, 15, 20, 30, 40)
        for ident, curve in effective_forecasts.items():
            require(type(curve) is list and len(curve) == 6,
                    "G3_FUTURE_PREDICTION_SHAPE")
            require(all(number(v) and -EPS <= v <= 1.5*min(t, 20)+1+EPS
                        for v, t in zip(curve, times)),
                    "G3_FUTURE_PREDICTION_OUTSIDE_PHYSICAL_BOUND")
            require(all(b+EPS >= a for a,b in zip(curve, curve[1:])),
                    "G3_FUTURE_PREDICTION_NONMONOTONIC")

        arm_results = {}
        for arm, chosen in selection["decision"].items():
            ids = chosen["winners"]
            if not ids:
                arm_results[arm] = {"status": "NO_VALID_CANDIDATE",
                                    "prediction": None, "envelope": None,
                                    "winners": []}
                continue
            if arm == "D" and d_failed:
                arm_results[arm] = {
                    "status": "ABSTAIN_D_NATIVE_G2_FAILED",
                    "prediction": None, "envelope": None,
                    "winners": ids, "failed_preselected": d_failed,
                    "native_g2_outcomes": d_outcomes,
                    "replacement_forbidden": True,
                }
                continue
            curves = [effective_forecasts[i] for i in ids]
            bounds = [{"min":min(y), "max":max(y)} for y in zip(*curves)]
            shared = all(bound["max"]-bound["min"] <= EPS for bound in bounds)
            if chosen["parameter_ambiguity"]:
                status, point = "ABSTAIN_POINT_PARAMETER_UNIDENTIFIABLE", None
            elif len(ids) == 1:
                status, point = "CONDITIONAL_POINT_FORECAST_NOT_STRUCTURAL_ID", curves[0]
            elif shared:
                status, point = "SHARED_FORECAST_MULTIPLE_STRUCTURES_NOT_IDENTIFIED", curves[0]
            else:
                status, point = "ABSTAIN_POINT_DIVERGENT_COMPATIBLE_STRUCTURES", None
            arm_results[arm] = {"status": status, "prediction": point,
                                "envelope": bounds, "winners": ids}

    # No external custody or access to the evaluation response is implied.
    lock = {
        "schema": SCHEMA,
        "status": "LOCK_CONTENT_PREPARED_NEEDS_EXTERNAL_IMMUTABLE_CUSTODY",
        "selection_sha256": selection["selection_sha256"],
        "source_snapshot_sha256": selection["source_snapshot_sha256"],
        "case": selection["case"],
        "evaluation_times_minutes": [5, 10, 15, 20, 30, 40]
                                    if selection["case"] == "CAF01" else [],
        "evaluation_pulse": submission["evaluation_pulse"],
        "forecast_by_candidate": effective_forecasts,
        "native_g2_checks_for_preselected_D":
            safe_checks if selection["case"] == "CAF01" else {},
        "native_g2_outcomes_for_preselected_D": d_outcomes,
        "discarded_D_forecast_identifiers_due_to_failed_G2": discarded_d,
        "arm_forecasts": arm_results,
        "evaluation_truth_included": False,
        "external_reveal_authorized": False,
        "g4_reference_baselines_still_require_separate_lock": True,
    }
    lock["forecast_lock_sha256"] = digest(lock)
    return lock
