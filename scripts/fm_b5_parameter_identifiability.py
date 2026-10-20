"""Fit serial molecular structures to noisy synthetic calibration and held-out pulse data."""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import random
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN = ROOT / "data/synthetic/fm_b5_identifiability_plan.json"
PROVENANCE = ROOT / "poc/short_wrappers/provenance.json"


class IdentifiabilityError(ValueError):
    pass


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def values(spec: dict[str, float]) -> list[float]:
    count = round((spec["maximum"] - spec["minimum"]) / spec["step"])
    return [round(spec["minimum"] + i * spec["step"], 10) for i in range(count + 1)]


def sample_times(stop: float, interval: float) -> list[float]:
    count = round(stop / interval)
    if abs(count * interval - stop) > 1e-9:
        raise IdentifiabilityError("observation interval must divide stop_time")
    return [round(i * interval, 10) for i in range(count + 1)]


def input_rate(time: float, amplitude: float, duration: float) -> float:
    return amplitude if 0 <= time < duration else 0.0


def derivative(state: list[float], time: float, stages: int, capacity: float,
               response_time: float, amplitude: float, duration: float) -> list[float]:
    stocks = state[:stages]
    completions = [min(capacity, max(0.0, stock / response_time)) for stock in stocks]
    result = [0.0] * (stages + 1)
    result[0] = input_rate(time, amplitude, duration) - completions[0]
    for i in range(1, stages):
        result[i] = completions[i - 1] - completions[i]
    result[-1] = completions[-1]
    return result


def simulate(stages: int, capacity: float, response_time: float, amplitude: float,
             duration: float, stop: float, interval: float, step: float) -> list[float]:
    steps = round(stop / step)
    if abs(steps * step - stop) > 1e-9:
        raise IdentifiabilityError("integration step must divide stop_time")
    stride = round(interval / step)
    if abs(stride * step - interval) > 1e-9:
        raise IdentifiabilityError("integration step must divide observation interval")
    state = [0.0] * (stages + 1)
    output = []
    for index in range(steps + 1):
        if index % stride == 0:
            output.append(state[-1])
        if index == steps:
            break
        t = index * step
        k1 = derivative(state, t, stages, capacity, response_time, amplitude, duration)
        k2 = derivative([x + step * y / 2 for x, y in zip(state, k1)], t + step/2,
                        stages, capacity, response_time, amplitude, duration)
        k3 = derivative([x + step * y / 2 for x, y in zip(state, k2)], t + step/2,
                        stages, capacity, response_time, amplitude, duration)
        k4 = derivative([x + step * y for x, y in zip(state, k3)], t + step,
                        stages, capacity, response_time, amplitude, duration)
        state = [x + step * (a + 2*b + 2*c + d) / 6
                 for x, a, b, c, d in zip(state, k1, k2, k3, k4)]
        state[:stages] = [max(0.0, stock) for stock in state[:stages]]
    return output


def noisy(values_: list[float], sigma: float, seed: int) -> list[float]:
    rng = random.Random(seed)
    return [value + rng.gauss(0.0, sigma) for value in values_]


def rmse(predicted: list[float], observed: list[float]) -> float:
    return math.sqrt(sum((a-b)**2 for a, b in zip(predicted, observed)) / len(observed))


def grid_fit(plan: dict[str, Any], stage_count: int, times: list[float],
             observations: list[float]) -> dict[str, Any]:
    calibration = plan["calibration"]
    sigma = float(plan["synthetic_data_generation"]["noise_standard_deviation"])
    step = float(plan["numerics"]["integration_step"])
    fits = []
    for capacity, response_time in itertools.product(
            values(plan["parameter_ranges"]["maxThroughput"]),
            values(plan["parameter_ranges"]["responseTime"])):
        predicted = simulate(stage_count, capacity, response_time,
            float(calibration["input_amplitude"]), float(calibration["input_duration"]),
            float(calibration["stop_time"]), float(calibration["observation_interval"]), step)
        sse = sum((a-b)**2 for a, b in zip(predicted, observations))
        fits.append({"maxThroughput": capacity, "responseTime": response_time,
                     "sse": sse, "rmse": rmse(predicted, observations)})
    best = min(fits, key=lambda item: (item["sse"], item["maxThroughput"], item["responseTime"]))
    cutoff = best["sse"] + float(plan["uncertainty_rule"]["delta_chi_square"]) * sigma**2
    supported = [item for item in fits if item["sse"] <= cutoff]
    return {"best_fit": best, "profile_likelihood_cutoff_sse": cutoff,
        "approx_95_percent_grid_set_size": len(supported),
        "parameter_uncertainty_set": {
            key: {"minimum": min(item[key] for item in supported),
                  "maximum": max(item[key] for item in supported)}
            for key in ("maxThroughput", "responseTime")},
        "supported_grid_points": supported}


def write_observations(path: Path, times: list[float], values_: list[float]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["time_hours", "observed_delivered_units"])
        writer.writerows((time, value) for time, value in zip(times, values_))


def read_observations(path: Path) -> tuple[list[float], list[float]]:
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    times = [float(row["time_hours"]) for row in rows]
    observations = [float(row["observed_delivered_units"]) for row in rows]
    if not rows or not all(math.isfinite(x) for x in times + observations):
        raise IdentifiabilityError(f"invalid observations in {path.name}")
    return times, observations


def run(plan_path: Path, output_dir: Path) -> dict[str, Any]:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if plan.get("synthetic") is not True or plan.get("empirical_or_causal_claim") is not False:
        raise IdentifiabilityError("B5 must be declared synthetic and non-causal")
    output_dir.mkdir(parents=True, exist_ok=True)
    data = plan["synthetic_data_generation"]
    structures = {item["id"]: int(item["stage_count"]) for item in plan["structures"]}
    if set(structures) != {"CS-01", "CS-02"} or structures["CS-01"] == structures["CS-02"]:
        raise IdentifiabilityError("B5 requires the declared one-stage and two-stage structures")
    if data["truth_structure"] not in structures:
        raise IdentifiabilityError("synthetic data generator references an undeclared structure")
    source_record = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    wrapper_record = next((item for item in source_record["files"]
                           if item["path"] == "IGCMolecules.mo"), None)
    source_path = ROOT / plan["molecule_source"]
    if not wrapper_record or digest(source_path) != "sha256:" + wrapper_record["sha256"]:
        raise IdentifiabilityError("B5 molecule source does not match the reviewed provenance snapshot")
    for parameter, value in data["truth_parameters"].items():
        bounds = plan["parameter_ranges"][parameter]
        if not float(bounds["minimum"]) <= float(value) <= float(bounds["maximum"]):
            raise IdentifiabilityError(f"synthetic truth for {parameter} lies outside the declared fit range")
    sigma = float(data["noise_standard_deviation"])
    if sigma <= 0 or not math.isfinite(sigma):
        raise IdentifiabilityError("synthetic noise standard deviation must be positive")

    calibration = plan["calibration"]
    cal_times = sample_times(float(calibration["stop_time"]), float(calibration["observation_interval"]))
    truth = data["truth_parameters"]
    calibration_truth = simulate(structures[data["truth_structure"]], float(truth["maxThroughput"]),
        float(truth["responseTime"]), float(calibration["input_amplitude"]),
        float(calibration["input_duration"]), float(calibration["stop_time"]),
        float(calibration["observation_interval"]), float(plan["numerics"]["integration_step"]))
    cal_obs = noisy(calibration_truth, sigma, int(data["calibration_noise_seed"]))
    cal_path = output_dir / "calibration-observations.csv"
    write_observations(cal_path, cal_times, cal_obs)
    calibration_fits = {name: grid_fit(plan, count, cal_times, cal_obs)
                        for name, count in structures.items()}

    held_out = plan["held_out_discrimination"]
    test_times = sample_times(float(held_out["stop_time"]), float(held_out["observation_interval"]))
    pulse_truth = simulate(structures[data["truth_structure"]], float(truth["maxThroughput"]),
        float(truth["responseTime"]), float(held_out["input_amplitude"]),
        float(held_out["input_duration"]), float(held_out["stop_time"]),
        float(held_out["observation_interval"]), float(plan["numerics"]["integration_step"]))
    test_obs = noisy(pulse_truth, sigma, int(data["pulse_noise_seed"]))
    test_path = output_dir / "held-out-pulse-observations.csv"
    write_observations(test_path, test_times, test_obs)

    step = float(plan["numerics"]["integration_step"])
    pulse_predictions: dict[str, dict[str, Any]] = {}
    for name, stage_count in structures.items():
        fit = calibration_fits[name]
        param_set = fit["supported_grid_points"]
        predictions = [simulate(stage_count, item["maxThroughput"], item["responseTime"],
            float(held_out["input_amplitude"]), float(held_out["input_duration"]),
            float(held_out["stop_time"]), float(held_out["observation_interval"]), step)
            for item in param_set]
        best_params = fit["best_fit"]
        best_prediction = simulate(stage_count, best_params["maxThroughput"], best_params["responseTime"],
            float(held_out["input_amplitude"]), float(held_out["input_duration"]),
            float(held_out["stop_time"]), float(held_out["observation_interval"]), step)
        ensemble_mean = [sum(row[index] for row in predictions) / len(predictions)
                         for index in range(len(test_times))]
        pulse_predictions[name] = {
            "held_out_rmse": rmse(ensemble_mean, test_obs),
            "best_fit_point_held_out_rmse": rmse(best_prediction, test_obs),
            "calibration_supported_ensemble_mean": ensemble_mean,
            "prediction_envelope_under_calibration_uncertainty": [
                {"minimum": min(row[i] for row in predictions),
                 "maximum": max(row[i] for row in predictions)}
                for i in range(len(test_times))],
            "best_fit_parameters_from_calibration_only": {
                "maxThroughput": best_params["maxThroughput"],
                "responseTime": best_params["responseTime"]}}

    a, b = "CS-01", "CS-02"
    gap_floor = float(plan["discrimination_rule"]["minimum_prediction_gap_in_noise_sd"]) * sigma
    separated = []
    for index, (left, right) in enumerate(zip(
            pulse_predictions[a]["prediction_envelope_under_calibration_uncertainty"],
            pulse_predictions[b]["prediction_envelope_under_calibration_uncertainty"])):
        gap = max(left["minimum"] - right["maximum"], right["minimum"] - left["maximum"], 0.0)
        if gap >= gap_floor:
            separated.append({"time_hours": test_times[index], "envelope_gap_units": gap})
    heldout_winner = min((a, b), key=lambda key: pulse_predictions[key]["held_out_rmse"])
    rmse_gap = abs(pulse_predictions[a]["held_out_rmse"] - pulse_predictions[b]["held_out_rmse"])
    target_error = float(plan["discrimination_rule"]["minimum_held_out_rmse_advantage_in_noise_sd"]) * sigma
    distinguished = (len(separated) >= int(plan["discrimination_rule"]["minimum_separated_observations"])
                     and rmse_gap >= target_error)
    result = {
        "status": "B5_PARAMETER_IDENTIFIABILITY_EVALUATED_SYNTHETIC",
        "discrimination_result": "DISTINGUISHED_ON_HELD_OUT_PULSE" if distinguished else "NOT_DISTINGUISHED_ON_HELD_OUT_PULSE",
        "structure_of_data_split": {
            "fit_data": "calibration-observations.csv",
            "held_out_data": "held-out-pulse-observations.csv",
            "parameter_fitting_used_held_out_pulse": False,
            "held_out_data_used_for_selection_or_fitting": False,
            "independent_noise_seeds": int(data["calibration_noise_seed"]) != int(data["pulse_noise_seed"])},
        "parameter_ranges": plan["parameter_ranges"],
        "noise_standard_deviation": sigma,
        "uncertainty_method": plan["uncertainty_rule"],
        "calibration_fit_by_structure": {
            name: {key: value for key, value in fit.items() if key != "supported_grid_points"}
            for name, fit in calibration_fits.items()},
        "calibration_structure_comparison": {
            "best_structure_by_calibration_rmse": min(structures,
                key=lambda name: calibration_fits[name]["best_fit"]["rmse"]),
            "best_fit_sse_by_structure": {name: fit["best_fit"]["sse"]
                for name, fit in calibration_fits.items()},
            "best_fit_rmse_by_structure": {name: fit["best_fit"]["rmse"]
                for name, fit in calibration_fits.items()},
            "interpretation": "calibration comparison is descriptive; the held-out pulse remains excluded from fitting"},
        "held_out_pulse_evaluation": {
            "input_amplitude_units_per_hour": float(held_out["input_amplitude"]),
            "input_duration_hours": float(held_out["input_duration"]),
            "observation_horizon_hours": float(held_out["stop_time"]),
            "observation_count": len(test_times),
            "rmse_by_structure": {name: item["held_out_rmse"] for name, item in pulse_predictions.items()},
            "lower_rmse_structure": heldout_winner,
            "held_out_rmse_advantage": rmse_gap,
            "best_fit_point_rmse_by_structure": {name: item["best_fit_point_held_out_rmse"]
                for name, item in pulse_predictions.items()},
            "predictive_aggregation": "unweighted mean across the calibration-compatible grid points; not a Bayesian posterior mean",
            "prediction_envelope_separated_observation_count": len(separated),
            "separated_observation_times": separated,
            "parameter_uncertainty_predictions": {name: item["prediction_envelope_under_calibration_uncertainty"]
                                                  for name, item in pulse_predictions.items()}},
        "synthetic_generation_truth": {"structure": data["truth_structure"],
                                       "parameters": truth,
                                       "purpose": "declared synthetic data generator; not used during fitting"},
        "molecular_source_revision": source_record["source_snapshot_commit"],
        "upstream_system_dynamics_revision": source_record["dependencies"]["SystemDynamics"]["commit"],
        "numerical_model_scope": "Python RK4 implementation of source-audited serial BoundedQueue stock-flow equations; not a general Modelica simulator",
        "interpretation": "parameter ranges and noise are designed synthetic values; held-out pulse can separate only these declared candidate structures under this synthetic generator",
        "empirical_or_causal_claim": False,
        "license_status": "DEFERRED_BY_RESEARCHER",
        "input_hashes": {"plan_sha256": digest(plan_path),
                         "molecular_source_sha256": digest(source_path),
                         "molecular_provenance_sha256": digest(PROVENANCE),
                         "calibration_observations_sha256": digest(cal_path),
                         "held_out_pulse_observations_sha256": digest(test_path)}}
    (output_dir / "b5-identifiability-report.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (output_dir / "b5-calibration-fits.json").write_text(json.dumps(calibration_fits, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts/fm-b5-identifiability")
    args = parser.parse_args()
    print(json.dumps(run(args.plan, args.output_dir), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
