#!/usr/bin/env python3
"""CAF02 numerical-margin finite-grid spot check, NO independent world.

Compare E1-molecule Heun trajectories over the PREDECLARED C00/C01 grid,
five public inputs and three steps. Numerical convergence is NOT a proof
that the discrete-event source is accurately represented, nor a rigorous
global bound on solver error, nor native Modelica parity.
"""
import argparse
import hashlib
import json
from pathlib import Path

import caf02_structural_k0k1k2 as s

PROTOCOL=Path(__file__).with_name(
    "CAF02_INDEPENDENT_K0K1K2_POLICY_PROPOSAL_2026-10-30.json")
STEPS=(.05,.025,.0125)


def inspect(policy):
    s.verify_existing_repertoire()
    assert policy["status"]=="DRAFT_FOR_REVIEW_NOT_FROZEN_NOT_AUTHORIZED"
    assert policy["no_world_runs_authorized"] is True
    p=policy["candidate_parameters"]
    times=p["preparation_tau_minutes"]
    caps=p["shared_preparation_dispatch_capacity_orders_per_hour"]
    transit=p["transit_tau_minutes_C01"]
    assert times==[1,1.5,2,3] and caps==[72,100]
    assert transit==[.25,1,6]
    menu=policy["k1"]["menu"]
    rates=[
        policy["k0"]["public_arrival_pulse"]["rate_per_minute"],
        *[x["rate_per_minute"] for x in menu],
        policy["k2"]["future_public_pulse"]["rate_per_minute"],
    ]
    assert rates==[1.2,1,1.5,1.8,1.35]
    assert policy["k1"]["numerical_allowance_orders"]==.02
    outcomes=[]
    for family in ("C00","C01"):
        for tp in times:
            for td in times:
                for cap in caps:
                    for tt in (transit if family=="C01" else [None]):
                        for rate in rates:
                            curves=[
                                s.simulate(family,tp,td,cap,tt or 1,rate,
                                           step=dt)
                                for dt in STEPS
                            ]
                            d01=max(abs(a-b) for a,b in
                                    zip(curves[0],curves[1]))
                            d12=max(abs(a-b) for a,b in
                                    zip(curves[1],curves[2]))
                            outcomes.append((d01,d12,family,tp,td,
                                             cap,tt,rate))
    largest_05_025=max(outcomes,key=lambda x:x[0])
    largest_025_0125=max(outcomes,key=lambda x:x[1])
    # Convergence witness: BOTH differences are less than one quarter
    # of the proposed allowance, leaving room for unproved true error.
    guard=policy["k1"]["numerical_allowance_orders"]
    pass_finite=(largest_05_025[0]<=guard/4
                 and largest_025_0125[1]<=guard/4)
    return {
        "status":"FINITE_GRID_NUMERICAL_CONVERGENCE_ONLY",
        "policy_sha256":"sha256:"+hashlib.sha256(
            json.dumps(policy,sort_keys=True,separators=(",",":"))
            .encode()).hexdigest(),
        "candidate_structures":["C00","C01"],
        "nominal_grid_count_C00":32,
        "nominal_grid_count_C01":96,
        "public_rates_per_minute":rates,
        "step_minutes":list(STEPS),
        "trajectory_comparisons":len(outcomes),
        "max_delta_step_0_05_vs_0_025_orders":largest_05_025[0],
        "where_max_delta_0_05_vs_0_025":list(largest_05_025[2:]),
        "max_delta_step_0_025_vs_0_0125_orders":largest_025_0125[1],
        "where_max_delta_0_025_vs_0_0125":list(largest_025_0125[2:]),
        "numeric_policy_guard_orders":guard,
        "difference_threshold_guard_quarter_orders":guard/4,
        "finite_grid_refinement_witness_pass":pass_finite,
        "independent_world_evidence":False,
        "native_Modelica_parity_proven":False,
        "certified_true_global_error_bound":False,
        "DES_runs":0,
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",required=True)
    args=ap.parse_args()
    path=Path(args.output_dir)
    if path.exists():raise SystemExit("OUTPUT_ALREADY_EXISTS")
    policy=json.loads(PROTOCOL.read_text(encoding="utf-8"))
    result=inspect(policy)
    path.mkdir(parents=True)
    (path/"NUMERICAL_MARGIN_FINITE_GRID.json").write_text(
        json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("CAF02_NUMERICAL_FINITE_GRID_ONLY",
          "pairs",result["trajectory_comparisons"],
          "max_step_deltas",
          result["max_delta_step_0_05_vs_0_025_orders"],
          result["max_delta_step_0_025_vs_0_0125_orders"],
          "PASS",result["finite_grid_refinement_witness_pass"])
    if not result["finite_grid_refinement_witness_pass"]:
        raise SystemExit("NUMERICAL_GUARD_NOT_SUPPORTED_ON_FINITE_GRID")


if __name__=="__main__":
    main()
