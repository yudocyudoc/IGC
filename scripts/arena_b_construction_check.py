"""Construction-only diagnostics for a *real* Buffalo Modelica CSV.

G3 in Arena v1.3 concerns construction-data adequacy; *heldout* evaluation is
a separate downstream stage. In the absence of a declared instrument-error
bound, report descriptive errors but NEVER label construction fit G3 PASS.

This verifier also enforces Euler material conservation without borrowing the
deterministic or molecular generators.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


def finite(row, field):
    if field not in row:
        raise ValueError("MISSING_BUFFALO_SERIES:" + field)
    try:
        v=float(row[field])
    except (ValueError, TypeError) as exc:
        raise ValueError("BAD_BUFFALO_SERIES:" + field) from exc
    if not math.isfinite(v):
        raise ValueError("NONFINITE_BUFFALO_SERIES:" + field)
    return v


def assess(rows, visible):
    if not isinstance(visible, dict) or visible.get("schema") != "igc-arena-visible-input/0.1":
        raise ValueError("BAD_CONSTRUCTION_INPUT")
    raw=visible.get("construction",{}).get("observations")
    if not isinstance(raw,list) or len(raw)<2:
        raise ValueError("MISSING_CONSTRUCTION_OBSERVATIONS")
    # The pinned B experiment uses two material stocks and two material flows,
    # all explicitly named in its native Buffalo output.
    points=[]
    for row in rows:
        t=finite(row,"time")
        vals={name:finite(row,name) for name in
              ("pending_work","delivered_work","arrivals","completions")}
        if points and t<points[-1][0]-1e-9:
            raise ValueError("BUFFALO_TIME_BACKWARDS")
        if points and abs(t-points[-1][0])<1e-9:
            points[-1]=(t,vals)  # OpenModelica may duplicate terminal row
        else:
            points.append((t,vals))
    if len(points)<60:
        raise ValueError("TOO_FEW_REAL_BUFFALO_ROWS")
    if abs(points[0][0])>1e-9:
        raise ValueError("BUFFALO_MISSING_T0")
    if (abs(points[0][1]["pending_work"])>1e-8 or
            abs(points[0][1]["delivered_work"])>1e-8):
        raise ValueError("NONZERO_INITIAL_STOCK")
    max_balance=0.0
    for (ta,a),(tb,b) in zip(points,points[1:]):
        dt=tb-ta
        if dt<=0 or abs(dt-.125)>1e-7:
            raise ValueError("BUFFALO_EULER_GRID_MISMATCH")
        if min(a["pending_work"],a["delivered_work"],b["pending_work"],
               b["delivered_work"]) < -1e-3:
            raise ValueError("NEGATIVE_MATERIAL_STOCK")
        # Because the integrator is pinned to Euler, the change of
        # *total* stock must equal incoming arrivals at the left endpoint.
        delta=(b["pending_work"]+b["delivered_work"]
               -a["pending_work"]-a["delivered_work"])
        max_balance=max(max_balance,abs(delta-dt*a["arrivals"]))
    if max_balance>1e-4:
        raise ValueError("BUFFALO_MATERIAL_BALANCE_FAILED")
    observations=[]
    for item in raw:
        t=float(item["t"]); actual=float(item["delivered"])
        if not (math.isfinite(t) and math.isfinite(actual)):
            raise ValueError("NONFINITE_CONSTRUCTION_VALUE")
        selected=[v for x,v in points if abs(t-x)<1e-8]
        if len(selected)!=1:
            raise ValueError("CONSTRUCTION_TIME_NOT_ON_SOLVER_GRID")
        pred=selected[0]["delivered_work"]
        observations.append({"time_hour":t,"observed_items":actual,
                             "predicted_items":pred,"residual_items":pred-actual})
    def rmse(pts):
        return math.sqrt(sum(x["residual_items"]**2 for x in pts)/len(pts))
    noninitial=[x for x in observations if x["time_hour"]>0]
    if not noninitial:
        raise ValueError("NO_NONINITIAL_CONSTRUCTION_POINTS")
    return {
        "schema":"igc-arena-b-construction-diagnostic/0.1",
        "arm_id":"B","source":"OpenModelica CSV from original Buffalo native model",
        "modelica_status":"G2_SIMULATED_CONDITIONALLY",
        "solver":"Euler","steps":len(points)-1,
        "balance_residual_max_items":max_balance,
        "construction_observations":observations,
        "rmse_all_observations_items":rmse(observations),
        "rmse_noninitial_observations_items":rmse(noninitial),
        "rmse_denominators":{"all_observations":len(observations),
                            "noninitial_observations":len(noninitial)},
        "g3_construction_status":"DESCRIPTIVE_ONLY_NO_INSTRUMENT_BOUND",
        "heldout_evaluation_status":"NOT_RUN",
        "causal_identification":"NOT_DEMONSTRATED",
        "not_cross_arm_ranking":True,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--csv",required=True,type=Path)
    p.add_argument("--visible",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    if a.out.exists():
        raise ValueError("DIAGNOSTIC_OUTPUT_ALREADY_EXISTS")
    with a.csv.open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))
    result=assess(rows,json.loads(a.visible.read_text()))
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"status":result["g3_construction_status"],
                      "all_rmse":result["rmse_all_observations_items"],
                      "noninitial_rmse":result["rmse_noninitial_observations_items"],
                      "max_balance":result["balance_residual_max_items"]}))


if __name__=="__main__":
    main()
