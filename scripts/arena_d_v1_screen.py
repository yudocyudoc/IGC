"""Arena D1: bounded deterministic calibration and non-falsifying candidate screen.

No LLM, molecules, ATMS inference, hidden truth, or cross-lane information.
A finite parameter grid can exhibit compatibility, NOT structural impossibility.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

from scripts.arena_v0_contract import canonical, digest, trace_event
from scripts.arena_d_v01 import generate, modelica, validate_case

SCHEMA = "igc-d-observation-screen/0.1"
EVALUATION = "FINITE_GRID_CONSTRUCTION_SCREEN_NOT_IDENTIFICATION"


class ScreenError(ValueError):
    pass


def require(ok, code):
    if not ok:
        raise ScreenError(code)


def numeric(v):
    return type(v) in (int, float) and math.isfinite(v)


def validate_protocol(protocol, data):
    require(type(protocol) is dict and set(protocol) == {
        "schema", "noise_absolute_bound", "parameter_grid", "max_grid_evaluations",
        "integration_max_step", "new_trial_sample_times"
    }, "BAD_SCREEN_PROTOCOL")
    require(protocol["schema"] == SCHEMA, "BAD_SCREEN_SCHEMA")
    noise = protocol["noise_absolute_bound"]
    require(noise is None or (numeric(noise) and noise >= 0),
            "INVALID_INSTRUMENT_BOUND")
    grid = protocol["parameter_grid"]
    require(type(grid) is dict and set(grid) == {"capacity", "response_time", "loss_time"},
            "INVALID_GRID")
    for field, values in grid.items():
        require(type(values) is list and 1 <= len(values) <= 12 and
                all(numeric(x) and x > 0 for x in values) and
                len(values) == len(set(values)), "INVALID_GRID_" + field.upper())
    maximum = protocol["max_grid_evaluations"]
    require(type(maximum) is int and 1 <= maximum <= 1000, "INVALID_GRID_BUDGET")
    require(numeric(protocol["integration_max_step"]) and
            .002 <= protocol["integration_max_step"] <= .05, "INVALID_STEP")
    times = protocol["new_trial_sample_times"]
    require(type(times) is list and 2 <= len(times) <= 30 and
            all(numeric(t) and 0 < t <= 24 for t in times) and
            all(b > a for a, b in zip(times, times[1:])), "INVALID_NEW_TRIAL_TIMES")
    require(times[-1] > data["construction"]["observations"][0]["t"],
            "UNINFORMATIVE_TRIAL_SCHEDULE")
    # Count precisely the candidates the bounded generator actually emits.
    candidates = generate(data)["candidates"]
    expected = sum(len(grid["capacity"]) * len(grid["response_time"]) *
                   (len(grid["loss_time"]) if c["structure"]["loss"] else 1)
                   for c in candidates)
    # Fail closed instead of silently truncating one topology's parameter search.
    if expected > maximum:
        raise ScreenError("GRID_BUDGET_EXCEEDED")
    return expected


def integrate(stocks, loss, params, pulse, sample_times, max_step):
    """Independent RK4 with an EXACT input pulse boundary (piecewise constant u).

    This is an exploratory solver, not an independent validation of Modelica.
    """
    require(1 <= stocks <= 3 and type(loss) is bool, "BAD_STOCK_TOPOLOGY")
    cap, tau, loss_tau = (params[k] for k in ("capacity", "response_time", "loss_time"))
    require(all(numeric(x) and x > 0 for x in (cap, tau, loss_tau)), "BAD_PARAMETERS")
    rate, duration = pulse["rate"], pulse["duration"]
    require(numeric(rate) and rate > 0 and numeric(duration) and duration > 0, "BAD_PULSE")
    require(all(numeric(t) and 0 <= t <= 24 for t in sample_times) and
            all(b >= a for a, b in zip(sample_times, sample_times[1:])), "BAD_QUERY_TIMES")

    def derivative(y, u):
        flows = [min(cap, max(0., y[i] / tau)) for i in range(stocks)]
        leak = max(0., y[0] / loss_tau) if loss else 0.
        return ([u - flows[0] - leak] +
                [flows[i-1] - flows[i] for i in range(1, stocks)] +
                [flows[-1], leak])

    y = [0.] * (stocks + 2)
    t = 0.
    output = []
    for target in sample_times:
        while t < target - 1e-12:
            next_stop = min(target, t + max_step)
            if t < duration - 1e-12:
                next_stop = min(next_stop, duration)
            h = next_stop - t
            require(h > 1e-13, "NON_PROGRESSING_INTEGRATOR")
            u = rate if (t + h / 2) < duration else 0.
            a = derivative(y, u)
            b = derivative([v + h * s / 2 for v, s in zip(y, a)], u)
            c = derivative([v + h * s / 2 for v, s in zip(y, b)], u)
            d = derivative([v + h * s for v, s in zip(y, c)], u)
            y = [v + h*(p + 2*q + 2*r + s)/6
                 for v, p, q, r, s in zip(y, a, b, c, d)]
            t = next_stop
            require(all(math.isfinite(v) and v >= -1e-8 for v in y),
                    "NONPHYSICAL_NUMERICAL_STATE")
        injected = rate * min(target, duration)
        require(abs(sum(y) - injected) <= 2e-5, "INTEGRATOR_MASS_BALANCE_ERROR")
        output.append(y[stocks])
    return output


def score(values, observations):
    residuals = [pred - row["delivered"] for pred, row in zip(values, observations)]
    return {"max_abs_residual": max(abs(d) for d in residuals),
            "rmse": math.sqrt(sum(x*x for x in residuals) / len(residuals))}


def candidate_grid(candidate, protocol):
    g = protocol["parameter_grid"]
    for cap in g["capacity"]:
        for tau in g["response_time"]:
            for loss_tau in (g["loss_time"] if candidate["structure"]["loss"] else
                             [g["loss_time"][0]]):
                yield {"capacity": cap, "response_time": tau, "loss_time": loss_tau}


def assess(data, protocol):
    validate_case(data)
    total = validate_protocol(protocol, data)
    enumeration = generate(data)
    times = [r["t"] for r in data["construction"]["observations"]]
    readings = data["construction"]["observations"]
    pulse = data["construction"]["input_profile"]
    noise = protocol["noise_absolute_bound"]
    grid_results = []
    compatible = []
    count = 0
    for c in enumeration["candidates"]:
        best = None
        compatible_witnesses = 0
        for params in candidate_grid(c, protocol):
            values = integrate(len(c["structure"]["stocks"]), c["structure"]["loss"],
                               params, pulse, times, protocol["integration_max_step"])
            quality = score(values, readings)
            candidate_score = {"parameters": params, "predicted": values, **quality}
            if best is None or (quality["max_abs_residual"], quality["rmse"]) < (
                    best["max_abs_residual"], best["rmse"]):
                best = candidate_score
            if noise is not None and quality["max_abs_residual"] <= noise + 1e-5:
                compatible_witnesses += 1
            count += 1
        status = ("UNCERTAINTY_UNSPECIFIED" if noise is None else
                  "GRID_COMPATIBLE_NOT_IDENTIFIED" if compatible_witnesses > 0 else
                  "UNRESOLVED_GRID_NOT_FALSIFIED")
        entry = {"candidate_id": c["id"], "structure_hash": c["structure_hash"],
                 "stocks": len(c["structure"]["stocks"]), "loss": c["structure"]["loss"],
                 "status": status, "compatible_grid_points": compatible_witnesses,
                 "best_grid": best, "modelica_source_status": "D0_G2_SEPARATELY_TESTED"}
        grid_results.append(entry)
        if compatible_witnesses:
            compatible.append(entry)
    require(count <= total and count <= protocol["max_grid_evaluations"], "BUDGET_OVERRUN")
    # Independent physical invariants applicable to every candidate of this grammar.
    bound_conflicts = []
    if noise is not None:
        for i, row in enumerate(readings):
            allowed_mass = pulse["rate"] * min(row["t"], pulse["duration"])
            if row["delivered"] > allowed_mass + noise + 1e-5:
                bound_conflicts.append({"observation_index": i, "kind": "DELIVERED_EXCEEDS_INPUT"})
            if row["delivered"] < -noise - 1e-5:
                bound_conflicts.append({"observation_index": i, "kind": "NEGATIVE_CUMULATIVE"})
            if i and row["delivered"] + noise + 1e-5 < readings[i-1]["delivered"] - noise:
                bound_conflicts.append({"observation_index": i, "kind": "MONOTONE_INTERVAL_CONTRADICTION"})
    if bound_conflicts:
        conclusion = "OBSERVATION_CONTRADICTS_DECLARED_FAMILY_OR_INSTRUMENT_BOUND"
    elif noise is None:
        conclusion = "INSUFFICIENT_INSTRUMENT_INFORMATION"
    elif len(compatible) >= 2:
        conclusion = "NON_DISCRIMINATING_MULTIPLE_GRID_COMPATIBLE"
    elif len(compatible) == 1:
        conclusion = "ONE_GRID_COMPATIBLE_OTHERS_UNRESOLVED"
    else:
        conclusion = "NO_GRID_FIT_NOT_STRUCTURAL_FALSIFICATION"
    proposed = None
    if len(compatible) >= 2 and not bound_conflicts:
        # A *new independent reset* makes early measurements feasible.
        schedule = protocol["new_trial_sample_times"]
        scored = []
        for t in schedule:
            preds = [
                integrate(c["stocks"], c["loss"], c["best_grid"]["parameters"],
                          pulse, [t], protocol["integration_max_step"])[0]
                for c in compatible
            ]
            scored.append({"t_since_new_reset": t,
                           "predicted_spread": max(preds) - min(preds)})
        choice = max(scored, key=lambda row: row["predicted_spread"])
        proposed = {"kind": "NEW_INDEPENDENT_RESET_TRIAL",
                    "input_profile": pulse,
                    "suggested_measurement_time": choice["t_since_new_reset"],
                    "predicted_spread_nominal": choice["predicted_spread"],
                    "unit": data["observability"]["time_unit"],
                    "caveat": ("Heuristic maximum among best-grid fits; uncertain parameters "
                               "could overlap; no optimal-design or identification claim.")}
    return {"schema": SCHEMA, "method": EVALUATION,
            "arm_id": "D", "round_id": data["round_id"],
            "input_hash": enumeration["input_hash"], "protocol_hash": digest(protocol),
            "instrument_bound": noise, "grid_evaluations": count,
            "results": grid_results, "eligible_ids": [x["candidate_id"] for x in compatible],
            "conclusion": conclusion, "physical_bound_issues": bound_conflicts,
            "next_measurement": proposed, "no_structural_falsification": True,
            "notes": ("Finite-grid fit is neither exclusion over continuous parameters "
                      "nor evidence of the unique causal generator.")}


def write_evaluation(data, protocol, root, parent_event):
    """Require an actual upstream D0 event; never synthesize a fake ancestor."""
    require(type(parent_event) is dict and
            set(parent_event) == {"schema", "arm_id", "round_id", "event_type",
                                  "iteration", "source_hash", "payload_hash",
                                  "previous_event_hash", "event_hash"},
            "BAD_PARENT_EVENT")
    checkhash = digest({k: v for k, v in parent_event.items() if k != "event_hash"})
    require(parent_event["event_hash"] == checkhash, "TAMPERED_PARENT_EVENT")
    require(parent_event["arm_id"] == "D" and
            parent_event["round_id"] == data["round_id"] and
            parent_event["iteration"] == 0 and
            parent_event["event_type"] == "HYPOTHESIS_PROPOSED" and
            parent_event["previous_event_hash"] is None,
            "PARENT_NOT_D0_ROOT")
    require(not root.exists(), "OUTPUT_ALREADY_EXISTS")
    result = assess(data, protocol)
    require(parent_event["source_hash"] == result["input_hash"],
            "PARENT_DIFFERENT_EVIDENCE")
    root.mkdir(parents=True, exist_ok=False)
    (root / "screen.json").write_bytes(canonical(result) + b"\n")
    # Retain evidence of the SAME D hypothesis family and own-arm only.
    original = generate(data)
    candidate_by_id = {c["id"]: c for c in original["candidates"]}
    for entry in result["results"]:
        c = dict(candidate_by_id[entry["candidate_id"]])
        c["nominal_parameters"] = dict(entry["best_grid"]["parameters"])
        text = modelica(c, data["construction"]["input_profile"])
        name = "Dfit_" + c["structure_hash"][7:19]
        # Keep Modelica top-level class equal to Modelica source's class name.
        raw_name = "DStockFlow_" + c["structure_hash"][7:19]
        text = text.replace("model " + raw_name, "model " + name).replace(
            "end " + raw_name + ";", "end " + name + ";")
        (root / (name + ".mo")).write_text(text, encoding="utf-8")
    second = trace_event(arm_id="D", round_id=data["round_id"],
                         event_type="SIMULATION_REPORTED", iteration=0,
                         source_hash=original["input_hash"], payload_hash=digest(result),
                         previous_event_hash=parent_event["event_hash"])
    (root / "memory-events.json").write_bytes(canonical([parent_event, second]) + b"\n")
    return result


def compare_omc_csv(csv_path, result, *, atol=.012):
    """Numerical parity check; *not* source-model validation nor causal accuracy."""
    with Path(csv_path).open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    require(len(rows) >= 10 and "time" in rows[0] and "delivered" in rows[0],
            "BAD_OMC_SAMPLES")
    samples = [(float(x["time"]), float(x["delivered"])) for x in rows]
    require(all(math.isfinite(t) and math.isfinite(y) for t, y in samples),
            "NONFINITE_OMC_SAMPLES")
    for t, predicted in result:
        matches = [(abs(x-t), y) for x, y in samples if abs(x-t) < 1e-6]
        require(bool(matches), "MISSING_OMC_COMPARISON_TIME")
        err = abs(min(matches)[1] - predicted)
        require(err <= atol, "MODEL_SIMULATOR_PARITY_FAILED")
    return {"status": "PYTHON_OMC_NUMERICAL_PARITY", "sample_count": len(result),
            "tolerance": atol}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=["evaluate", "parity"])
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--protocol", type=Path, required=True)
    p.add_argument("--output", type=Path)
    p.add_argument("--csv", type=Path)
    p.add_argument("--candidate-id")
    p.add_argument("--parent-event", type=Path)
    args = p.parse_args()
    data = json.loads(args.input.read_text())
    protocol = json.loads(args.protocol.read_text())
    if args.command == "evaluate":
        require(args.output is not None and args.parent_event is not None,
                "MISSING_OUTPUT_OR_PARENT_EVENT")
        parent_event = json.loads(args.parent_event.read_text())
        result = write_evaluation(data, protocol, args.output, parent_event)
        print(json.dumps({"conclusion": result["conclusion"],
                          "grid_evaluations": result["grid_evaluations"],
                          "eligible_count": len(result["eligible_ids"])}))
    else:
        require(args.csv is not None and args.candidate_id is not None,
                "MISSING_PARITY_ARGUMENTS")
        result = assess(data, protocol)
        entry = next((x for x in result["results"]
                      if x["candidate_id"] == args.candidate_id), None)
        require(entry is not None, "UNKNOWN_CANDIDATE")
        pairs = list(zip((o["t"] for o in data["construction"]["observations"]),
                         entry["best_grid"]["predicted"]))
        print(json.dumps(compare_omc_csv(args.csv, pairs)))


if __name__ == "__main__":
    main()
