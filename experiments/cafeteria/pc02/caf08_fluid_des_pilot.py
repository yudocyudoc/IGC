#!/usr/bin/env python3
"""CAF-08: independent fluid references against the repository's CAF-01 DES.

Exploratory cross-check only; no new dependencies, inferred ground truth,
production recommendation, or modification of CAF-07B's selector.
The DES implementation is imported from the repository, NEVER copied here.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import json
from pathlib import Path
import statistics

from experiments.cafeteria.pc01 import caf01_des_engine as des

BASE_COMMIT = "5e2b5505a9224effe1b5242a3af61663b53aaa5d"
OBSERVATIONS = ((1.2, 10), (1.5, 20), (1.8, 20), (1.5, 40))
STAGES = ("preparacion", "despacho", "entrega")


def configuration(limited, capacity, extra=None):
    if extra is not None and limited:
        raise ValueError("extra-stage controls must not specify limited standard stages")
    stages = [
        {"servers": 1 if i in limited else 2,
         "service_minutes": str(Fraction(60, capacity)) if i in limited else "1"}
        for i in range(3)
    ]
    if extra is not None:
        stages.append({"servers": 1, "service_minutes": str(Fraction(60, extra))})
    result = {"schema": des.SCHEMA, "tie_policy": des.TIE_POLICY, "stages": stages}
    des.validate_private_config(result)
    return result


def capacity_rates(config):
    return [float(Fraction(servers, 1) / service)
            for servers, service in des.validate_private_config(config)]


def des_read(config, arrival_rate, minute):
    arrivals = des.half_open_arrivals(str(Fraction(str(arrival_rate))), 20)
    snapshots = des.run_toy_engine(config, arrivals, (0, 10, 20, 40))
    s = snapshots[(0, 10, 20, 40).index(minute)]
    return {"accepted": s.accepted_cum_orders,
            "delivered": s.delivered_cum_orders,
            "pending": s.pending_orders,
            "waiting": list(s.stage_waiting),
            "serving": list(s.stage_in_service)}


def simple_fluid(config, arrival_rate, minute):
    """Zero-residence, empty-initial-queue idealization DURING constant pulse.

    This is NOT a general differential equation for draining a queue after
    input stops, nor is it an event-by-event prediction for a DES.
    """
    if not 0 <= minute <= 20:
        raise ValueError("zero-lag closed form applies only during arrival pulse")
    upstream = arrival_rate
    waits = []
    for rate in capacity_rates(config):
        waits.append(max(0.0, upstream - rate) * minute)
        upstream = min(upstream, rate)
    delivered = upstream * minute
    accepted = arrival_rate * minute
    return {"accepted": accepted, "delivered": delivered,
            "pending": accepted - delivered, "waiting": waits}


def delayed_fluid(config, arrival_rate, times=(10, 20, 40), pulse=20, dt=0.005):
    """Independent discretized continuous-mass reference with fixed residence.

    Fluid work starts at capped capacity and completes after declared service
    time, including a fractional-grid completion interpolation. The source
    DES event calendar is not referenced. The output is NOT a closed form.
    """
    spec = des.validate_private_config(config)
    n = len(spec)
    steps = int(round(max(times) / dt))
    extra = int(max(float(duration) for _, duration in spec) / dt) + 5
    completions = [[0.0] * (steps + extra) for _ in spec]
    capacities = [servers / float(duration) for servers, duration in spec]
    queued = [0.0] * n
    serving = [0.0] * n
    accepted = delivered = 0.0
    marks = {round(t / dt): t for t in times}
    observations = {}
    for j in range(steps + 1):
        now = j * dt
        if j in marks:
            observations[marks[j]] = {
                "accepted": accepted, "delivered": delivered,
                "pending": accepted - delivered,
                "waiting": queued.copy(), "serving": serving.copy(),
            }
        if j == steps:
            break
        arriving = arrival_rate * dt if now < pulse - 1e-10 else 0.0
        accepted += arriving
        for i, (_, duration) in enumerate(spec):
            finishing = completions[i][j]
            serving[i] -= finishing
            if i == n - 1:
                delivered += finishing
            possible = arriving + queued[i]
            starts = min(max(0.0, possible), capacities[i] * dt)
            queued[i] = max(0.0, possible - starts)
            serving[i] += starts
            d = float(duration) / dt
            k = int(d)
            fraction = d - k
            completions[i][j + k] += (1 - fraction) * starts
            completions[i][j + k + 1] += fraction * starts
            arriving = finishing
    return observations


def worlds():
    result = []
    for i, cap in enumerate((72, 88, 102)):
        result.append(("SINGLE_%d_%d" % (cap, i), "single",
                       configuration((i,), cap)))
    for cap in (55, 90):
        for a, b in ((0, 1), (0, 2), (1, 2)):
            result.append(("DUAL_%d_%d%d" % (cap, a, b), "double",
                           configuration((a, b), cap)))
    for extra in (70, 100):
        result.append(("UNKNOWN_EXTRA_%d" % extra, "unknown-extra",
                       configuration((), 120, extra)))
    assert len(result) == 11
    return result


def errors(rows, key):
    ds = [x[key] for x in rows]
    return {"mae": round(statistics.mean(abs(x) for x in ds), 4),
            "max_abs": round(max(abs(x) for x in ds), 4),
            "bias": round(statistics.mean(ds), 4)}


def pair_experiment():
    """Passive indistinguishability; perturb ONLY preparation to 105/h."""
    a = configuration((0,), 75)
    b = configuration((0, 1), 75)
    a_after = configuration((0,), 105)
    b_after = configuration((1,), 75)
    b_after["stages"][0] = {"servers": 1, "service_minutes": str(Fraction(60, 105))}
    des.validate_private_config(b_after)
    passive = []
    for rate, t in ((1.2, 10), (1.5, 20), (1.8, 20)):
        passive.append({"arrival_rate": rate, "minute": t,
                        "simple_single": simple_fluid(a, rate, t),
                        "simple_dual": simple_fluid(b, rate, t),
                        "des_single": des_read(a, rate, t),
                        "des_dual": des_read(b, rate, t)})
    intervention = []
    for t in (20, 40):
        intervention.append({
            "minute": t, "arrival_rate": 1.5,
            "before_single": des_read(a, 1.5, t),
            "before_dual": des_read(b, 1.5, t),
            "after_single": des_read(a_after, 1.5, t),
            "after_dual": des_read(b_after, 1.5, t),
            "simple_post_single": simple_fluid(a_after, 1.5, t) if t <= 20 else None,
            "simple_post_dual": simple_fluid(b_after, 1.5, t) if t <= 20 else None,
        })
    return {"passive": passive, "intervention": intervention,
            "not_blind": True, "not_real_world_validation": True}


def run():
    rows = []
    for case_id, kind, cfg in worlds():
        for rate, t in OBSERVATIONS:
            observed = des_read(cfg, rate, t)
            lagged = delayed_fluid(cfg, rate)[t]
            row = {
                "case": case_id, "kind": kind, "arrival_rate_per_min": rate,
                "minute": t, "capacity_per_min": capacity_rates(cfg),
                "des": observed, "lagged_fluid": lagged,
                "difference_delivered_des_minus_lagged":
                    observed["delivered"] - lagged["delivered"],
                "difference_waiting_des_minus_lagged":
                    [x - y for x, y in zip(observed["waiting"], lagged["waiting"])],
            }
            if t <= 20:
                simple = simple_fluid(cfg, rate, t)
                row["zero_lag_fluid"] = simple
                row["difference_delivered_des_minus_zero_lag"] = (
                    observed["delivered"] - simple["delivered"])
            rows.append(row)
    zero = [x for x in rows if "zero_lag_fluid" in x]
    summary = {
        "n_worlds": 11, "n_observation_rows": len(rows),
        "zero_lag": errors(zero, "difference_delivered_des_minus_zero_lag"),
        "lagged": errors(rows, "difference_delivered_des_minus_lagged"),
        "by_structure": {},
    }
    for name in ("single", "double", "unknown-extra"):
        block = [x for x in rows if x["kind"] == name]
        summary["by_structure"][name] = {
            "zero_lag": errors([x for x in block if "zero_lag_fluid" in x],
                               "difference_delivered_des_minus_zero_lag"),
            "lagged": errors(block, "difference_delivered_des_minus_lagged"),
        }
    return {"schema": "igc-caf08-fluid-des-review/0.1",
            "base_commit_reference": BASE_COMMIT,
            "experimental_only": True, "truth_only_in_evaluator": False,
            "source_des": "experiments.cafeteria.pc01.caf01_des_engine",
            "method_note": "known physical configs to BOTH simulators; not a blind inference test",
            "summary": summary, "comparisons": rows,
            "identifiability_pair": pair_experiment()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
