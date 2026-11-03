"""G3 construction on known EV-01 O0; never a prospective or native-D claim.

M: analytical necessary throughput bound from six original Short E1 ASTs.
D: exploratory, externally calibrated RK4 mirror of the ORIGINAL D equations,
not an execution of the original D parameter estimator (none exists).
No provider, DES, OMC, hidden world, holdout, model selection or G4/G5.
"""
from __future__ import annotations

import argparse
from fractions import Fraction as F
from itertools import product
import json
import math
from pathlib import Path

from scripts.arena_v0_contract import canonical, digest
from scripts.arena_cafe.native_handoff import need, validate_a1_visible
from scripts.arena_cafe import r2_observational_contracts as r2
from scripts.arena_cafe import r2_causal_pos_signal as signal

SCHEMA = "igc-arena-g3-construction-descriptive/0.1"
SAMPLES = (2, 4, 6, 8, 10)
DT = 0.01  # minutes, integration is split exactly at POS kernel boundaries
CAPACITIES = (0.8, 1.2, 1.8, 2.7, 4.0)  # orders/minute, exploratory grid
RESPONSE_TIMES = (0.15, 0.35, 0.7, 1.4, 2.7)  # minutes
LOSS_TIMES = (0.5, 1.5, 4.0, 8.1, 20.0)  # minutes
NO_LOSS_PLACEHOLDER = 8.1  # not active when the topology has no loss
NEAR_BEST_MAE_DELTA = 0.25  # descriptive grid coverage; NOT a statistical CI
DEFAULT_WIDTH = F(1, 2)
ROOT = Path(__file__).resolve().parents[2]


def public_observations(visible):
    """Re-use O0 public counts; POS milestones strictly before each t."""
    validate_a1_visible(visible, "O0")
    need(F(visible["observability"]["cutoff_minutes_exact"]) == 10,
         "G3_WRONG_CONSTRUCTION_CUTOFF")
    rows = visible["construction"]["observation_series"]
    at = {F(x["t_minutes_exact"]): x for x in rows}
    need(set(F(t) for t in SAMPLES).issubset(at),
         "G3_REQUIRED_OBSERVATIONS_MISSING")
    y = [at[F(t)]["delivered_cumulative"] for t in SAMPLES]
    need(all(type(v) is int and 0 <= v <= 15 for v in y) and
         y == sorted(y), "G3_INVALID_CUMULATIVE_DELIVERIES")
    need(len(visible["construction"]["pos_arrival_events"]) == 15,
         "G3_EXPECTED_FROZEN_EV01_FIFTEEN_INPUTS")
    return y


def m_analytical_bound(visible):
    """Necessary (not sufficient) bound: all material stages start at 0."""
    y = public_observations(visible)
    r2.original_source_checks()
    composer = r2.get_composer()
    cfg, classes, _ = composer.load_registry(r2.BASE_PATH)
    graphs = composer.enumerate_graphs(cfg, classes)
    source = (ROOT / "src/modelica/IGCMolecules.mo").read_text(encoding="utf-8")
    # Stop rather than certify a bound if the native constitutive law drifts.
    need('release(minFlow=0,maxFlow=maxThroughput)' in source
         and 'stock(x0=0)' in source
         and 'deliveries(x0=0)' in source
         and 'connect(release.y,completed)' in source,
         "G3_M_NATIVE_THROUGHPUT_EQUATIONS_UNVERIFIED")
    need(len(graphs) == 6, "G3_M_NOT_SIX_ORIGINAL_AST")
    records = []
    for key, ast in graphs:
        composer.check_graph(ast, cfg, classes)
        queues = [ins for ins in ast["instances"]
                  if ins["class_id"] == "bounded-queue"]
        roles = {ins["role"] for ins in queues}
        need({"preparation", "dispatch"}.issubset(roles),
             "G3_M_MANDATORY_PHYSICAL_STAGES_MISSING")
        need(all(classes[x["class_id"]]["states"]["stock"]["initial"] == 0
                 for x in queues), "G3_M_NONZERO_INITIAL_STOCK")
        bottleneck = min(F(str(ins["parameters"]["maxThroughput"]))
                         for ins in queues)
        bound = bottleneck * F(10, 60)
        records.append({
            "native_ast_canonical_sha256": key,
            "native_ast_sha256": digest(ast),
            "physical_stage_roles": [x["role"] for x in queues],
            "bottleneck_orders_per_hour": str(bottleneck),
            "upper_bound_delivery_at_10_minutes_exact": str(bound),
            "observed_delivery_at_10_minutes": y[-1],
            "status": ("M_FIXED_PRIOR_INCOMPATIBLE_WITH_O0_DELIVERIES"
                       if F(y[-1]) > bound else
                       "BOUND_NOT_DISCRIMINATING"),
            "bound_is_necessary_not_sufficient": True,
        })
    return {
        "mode": "ORIGINAL_E1_FIXED_PRIORS_ANALYTICAL_NOT_CALIBRATED",
        "registry": "experiments/e1/registry.base.json",
        "candidate_count": len(records),
        "candidate_results": records,
        "incompatible_count": sum(x["status"].startswith("M_FIXED_PRIOR_")
                                  for x in records),
        "necessary_throughput_for_eight_in_10min_orders_per_hour":
            str(F(y[-1]) * 60 / 10),
        "new_native_simulations": 0,
        "M_method_invalidated": False,
        "M_fixed_priors_sufficient_for_current_O0": False,
    }


def _rates(s, u, cap, tau, loss_time, has_loss):
    n = len(s) - 2
    flows = [min(cap, max(0.0, x / tau)) for x in s[:n]]
    loss = max(0.0, s[0] / loss_time) if has_loss else 0.0
    return ([u - flows[0] - loss] +
            [flows[i-1] - flows[i] for i in range(1, n)] +
            [flows[-1], loss])


def _rk4(s, dt, u, cap, tau, loss_time, has_loss):
    k1 = _rates(s, u, cap, tau, loss_time, has_loss)
    k2 = _rates([x + dt * a / 2 for x, a in zip(s, k1)],
                u, cap, tau, loss_time, has_loss)
    k3 = _rates([x + dt * a / 2 for x, a in zip(s, k2)],
                u, cap, tau, loss_time, has_loss)
    k4 = _rates([x + dt * a for x, a in zip(s, k3)],
                u, cap, tau, loss_time, has_loss)
    return [x + dt * (a + 2*b + 2*c + d) / 6
            for x, a, b, c, d in zip(s, k1, k2, k3, k4)]


def integrate_native_d_equations(segments, n, has_loss, cap, tau, loss_time,
                                 dt=DT):
    """RK4 numerical MIRROR of arena_d_v01.modelica, not OMC execution."""
    need(n in (1, 2, 3) and type(has_loss) is bool and
         all(math.isfinite(v) and v > 0 for v in
             (cap, tau, loss_time, dt)), "G3_INVALID_D_NUMERICAL_INPUT")
    state = [0.0] * (n + 2)  # stocks, delivered, lost
    readings = {}
    starts = sorted(set([F(0), F(10)] + [F(t) for t in SAMPLES] +
                        [F(x["start_minutes_exact"]) for x in segments
                         if F(x["start_minutes_exact"]) < 10] +
                        [F(x["end_minutes_exact"]) for x in segments
                         if F(x["end_minutes_exact"]) < 10]))
    for a, b in zip(starts, starts[1:]):
        matching = [seg for seg in segments
                    if F(seg["start_minutes_exact"]) <= a <
                    F(seg["end_minutes_exact"])]
        need(len(matching) == 1, "G3_CAUSAL_SIGNAL_GAP_OR_OVERLAP")
        rate = float(F(matching[0]["rate_orders_per_minute_exact"]))
        steps = math.ceil(float(b-a) / dt)
        step = float(b-a) / steps
        for _ in range(steps):
            state = _rk4(state, step, rate, cap, tau, loss_time, has_loss)
        if b in (F(t) for t in SAMPLES):
            readings[int(b)] = state[n]
    need(set(readings) == set(SAMPLES) and
         all(math.isfinite(x) for x in state),
         "G3_INCOMPLETE_D_NUMERICAL_TRAJECTORY")
    return [readings[t] for t in SAMPLES], state


def d_external_grid(visible, *, width=DEFAULT_WIDTH,
                    capacities=CAPACITIES, responses=RESPONSE_TIMES,
                    losses=LOSS_TIMES):
    """Finite disclosed grid; near-best sets do NOT identify true parameters."""
    y = public_observations(visible)
    need(width in signal.SENSITIVITY_WIDTHS, "G3_NONDECLARED_KERNEL_WIDTH")
    values = (capacities, responses, losses)
    need(all(0 < len(v) <= 12 and all(
             type(x) in (int,float) and math.isfinite(x) and x > 0 for x in v)
             for v in values), "G3_PARAMETER_GRID_INVALID")
    r2.original_source_checks()
    universe = r2.d_pos_contract(visible, "O0", resources={
        "max_stocks": 3, "allow_loss": True, "max_candidates": 6,
        "max_simulations": 0,
    })
    need(universe["candidate_count"] == 6, "G3_D_NOT_SIX_ORIGINAL_GRAMMAR")
    input_signal = signal.from_visible(visible, "O0", width)
    segments = input_signal["signal"]["segments"]
    outputs = []
    for item in universe["candidates"]:
        struct = item["structure"]
        n = len(struct["stocks"])
        has_loss = struct["loss"]
        r2.lint_structure(struct)
        trials = []
        for cap, tau, loss_time in product(
                capacities, responses,
                losses if has_loss else (NO_LOSS_PLACEHOLDER,)):
            pred, final = integrate_native_d_equations(
                segments, n, has_loss, cap, tau, loss_time)
            mae = sum(abs(p - o) for p, o in zip(pred, y)) / len(y)
            trials.append({
                "params": {"capacity": cap, "response_time": tau,
                           "loss_time": loss_time if has_loss else
                           "INACTIVE_NO_LOSS_TOPOLOGY"},
                "mae": round(mae, 8),
                "predicted_deliveries": [round(v, 6) for v in pred],
                "residuals_pred_minus_observed":
                    [round(v-o, 6) for v, o in zip(pred, y)],
                "final_mass_components": [round(v, 6) for v in final],
            })
        trials.sort(key=lambda t:(t["mae"], t["params"]["capacity"],
                                  t["params"]["response_time"],
                                  str(t["params"]["loss_time"])))
        best = trials[0]
        near = [t for t in trials
                if t["mae"] <= best["mae"] + NEAR_BEST_MAE_DELTA]
        ranges = {}
        for param in ("capacity", "response_time", "loss_time"):
            seq = [t["params"][param] for t in near
                   if type(t["params"][param]) in (int, float)]
            ranges[param] = [min(seq), max(seq)] if seq else None
        outputs.append({
            "candidate_id": item["id"],
            "native_structure_sha256": item["structure_hash"],
            "native_stock_count": n,
            "native_loss": has_loss,
            "external_grid_evaluations": len(trials),
            "best_in_grid": best,
            "near_best_grid_count": len(near),
            "near_best_parameter_ranges": ranges,
            "search_is_not_identification": True,
        })
    return {
        "mode": "ARENA_EXTERNAL_CALIBRATION_EXPLORATORY_NUMERICAL_MIRROR",
        "numerical_engine": "RK4_SOURCE_EQUATIONS_D_NOT_OPENMODELICA",
        "D_native_inference": False,
        "candidate_selection_owner": "NONE_ALL_SIX_RETAINED",
        "conformity_to_OMC": "PENDING_SEPARATE_CROSSCHECK",
        "width_minutes_exact": str(width),
        "causal_signal_sha256": input_signal["signal"]["event_rate_signal_sha256"],
        "grid": {"capacity": list(capacities), "response_time": list(responses),
                 "loss_time": list(losses)},
        "near_best_mae_delta_orders": NEAR_BEST_MAE_DELTA,
        "not_a_statistical_confidence_set": True,
        "observed_deliveries": y,
        "sample_times_minutes": list(SAMPLES),
        "MAE_posthoc_exploratory": True,
        "candidates": outputs,
        "candidate_count": len(outputs),
        "parameter_sets_not_automatically_admissible_to_native_D": True,
        "provider_calls": 0,
        "omc_calls": 0,
    }


def width_sensitivity(visible, *, capacities=CAPACITIES,
                      responses=RESPONSE_TIMES, losses=LOSS_TIMES):
    """Report all three predeclared kernel widths; never choose a winner."""
    panels=[]
    for width in signal.SENSITIVITY_WIDTHS:
        d=d_external_grid(visible,width=width,capacities=capacities,
                          responses=responses,losses=losses)
        panels.append({
            "width_minutes_exact":str(width),
            "candidate_count":d["candidate_count"],
            "same_native_six_structure_hashes":
                [x["native_structure_sha256"] for x in d["candidates"]],
            "per_structure_minimum_MAE":[
                {"candidate_id":x["candidate_id"],
                 "MAE_posthoc_grid_minimum":x["best_in_grid"]["mae"],
                 "near_best_grid_count":x["near_best_grid_count"]}
                for x in d["candidates"]],
            "best_width_selected":False,
        })
    need(all(p["same_native_six_structure_hashes"] ==
             panels[0]["same_native_six_structure_hashes"] for p in panels),
         "G3_SENSITIVITY_CHANGED_NATIVE_UNIVERSE")
    return {
        "mode":"EXPLORATORY_KERNEL_SENSITIVITY_NOT_METHOD_SELECTION",
        "kernel_widths_minutes_exact":
            [str(x) for x in signal.SENSITIVITY_WIDTHS],
        "panels":panels,
        "M_priors_modified":False,
        "D_native_model_selection":False,
        "width_optimized_on_O0":False,
        "no_scientific_PASS":True,
    }


def build(visible, *, run_external_grid=False):
    m = m_analytical_bound(visible)
    d = d_external_grid(visible) if run_external_grid else {
        "mode": "NOT_RUN_OPT_IN_ONLY", "candidate_count": 6}
    return {
        "schema": SCHEMA,
        "condition_id": "O0",
        "source_snapshot_hash": visible["source_snapshot_hash"],
        "task": "OFFLINE_CONDITIONAL_REPLAY_WITH_KNOWN_POS_ARRIVALS",
        "assessment": "G3_CONSTRUCTION_ONLY_NOT_G4_G5",
        "input_is_not_forecast": True,
        "G3_is_prospective_blind_holdout": False,
        "H_j": {"observable": "delivered_cumulative",
                "measurement": "one POS pedido_entregado per order, time < sample_t",
                "D": "delivered, minutes, orders",
                "M": "deliveredTotal, hours converted to minutes, orders",
                "B": "NOT_AVAILABLE_NO_EV01_NATIVE_MODEL",
                "operational_correspondence": "CONDITIONAL_ONE_ORDER_ONE_DELIVERY",
                "continuous_vs_discrete": "DESCRIPTIVE_FIT_ONLY",
                "O1_stages": "NOT_SCORED_UNPROVEN_MEASUREMENT_OPERATOR"},
        "M": m,
        "D": d,
        "B": "NOT_RUN_NO_EV01_NATIVE_PROVIDER_MODEL",
        "gates": {"G2": "PREVIOUS_ENGINEERING_RUNS_UNCHANGED",
                  "G3": "DESCRIPTIVE_CONSTRUCTION_DIAGNOSTIC_NOT_SCIENTIFIC_PASS",
                  "G4": "NOT_RUN", "G5": "NOT_RUN", "A3": "PARTIAL"},
        "no_cross_arm_winner": True,
        "no_new_world": True,
        "no_provider_calls": True,
        "no_new_omc": True,
        "nonempirical_G2_fixture_is_not_used_as_G3_calibration": True,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--visible", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--d-external-grid", action="store_true")
    ap.add_argument("--d-width-sensitivity", action="store_true")
    args = ap.parse_args()
    need(not (args.d_external_grid and args.d_width_sensitivity),
         "G3_CHOOSE_GRID_OR_SENSITIVITY_SEPARATELY")
    need(not args.out.exists(), "G3_REFUSE_OVERWRITE")
    visible = json.loads(args.visible.read_text(encoding="utf-8"))
    report = build(visible, run_external_grid=args.d_external_grid)
    if args.d_width_sensitivity:
        report["D_width_sensitivity"] = width_sensitivity(visible)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(canonical(report) + b"\n")
    print(json.dumps({
        "M_incompatible": report["M"]["incompatible_count"],
        "D_mode": report["D"]["mode"],
        "G3": report["gates"]["G3"],
        "G4": report["gates"]["G4"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
