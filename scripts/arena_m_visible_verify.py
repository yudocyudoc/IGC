"""Independent numerical audit of the single Arena-M OpenModelica trace.

This is descriptive construction-data comparison, not heldout G3 or causal proof.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
from pathlib import Path


def get(row, name):
    matches=[v for k,v in row.items() if k==name or k.endswith("."+name)]
    if len(matches)!=1:
        raise ValueError("MISSING_OR_DUPLICATE_COLUMN:"+name)
    value=float(matches[0])
    if not math.isfinite(value):
        raise ValueError("NONFINITE_VALUE:"+name)
    return value


def verify(rows, visible):
    times=[]
    for row in rows:
        t=get(row,"time")
        if times and t < times[-1][0]-1e-9:
            raise ValueError("TIME_BACKWARDS")
        if times and abs(t-times[-1][0])<1e-9:
            times[-1]=(t,row)
        else:
            times.append((t,row))
    if len(times)<70:
        raise ValueError("MISSING_REAL_MODELICA_SAMPLES")
    rate=float(visible["construction"]["input_profile"]["rate"])
    duration=float(visible["construction"]["input_profile"]["duration"])
    max_balance=0.0
    for t,row in times:
        d=get(row,"deliveredTotal")
        w=get(row,"inTransit")
        if min(d,w)<-0.001:
            raise ValueError("NEGATIVE_MATERIAL_STOCK")
        residual=abs(d+w - rate*min(t,duration))
        max_balance=max(max_balance,residual)
    if max_balance>0.015:
        raise ValueError("GLOBAL_MATERIAL_BALANCE_FAILURE")
    points=[]
    for obs in visible["construction"]["observations"]:
        wanted=float(obs["t"])
        hits=[row for t,row in times if abs(t-wanted)<1e-6]
        if len(hits)!=1:raise ValueError("OBS_TIME_NOT_IN_OM_GRID")
        simulated=get(hits[0],"deliveredTotal")
        observed=float(obs["delivered"])
        points.append({"time":wanted,"observed":observed,"simulated":simulated,
                       "residual":simulated-observed})
    nonzero=[p for p in points if p["time"]>0]
    rmse=math.sqrt(sum(p["residual"]**2 for p in nonzero)/len(nonzero))
    return {"schema":"igc-arena-m-common-pulse-check/0.1",
       "engine":"OPENMODELICA_REAL_CSV", "status":"G2_SIMULATED_CONDITIONALLY",
       "input_pulse":visible["construction"]["input_profile"],
       "technical_samples":len(times),"max_material_balance_residual":max_balance,
       "construction_only":True,"observations":points,"rmse_items":rmse,
       "g3_heldout":"NOT_RUN","g0_semantic_role_mapping":"PROVISIONAL",
       "causal_identification":"NOT_DEMONSTRATED",
       "warning":"Short E1 fixed parameters not fitted; no public holdout or evidence-based molecular selection."}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--csv",required=True,type=Path)
    ap.add_argument("--visible",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    a=ap.parse_args()
    with a.csv.open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))
    payload=verify(rows,json.loads(a.visible.read_text()))
    a.out.write_text(json.dumps(payload,indent=2)+"\n")
    print(json.dumps(payload))


if __name__=="__main__":
    main()
