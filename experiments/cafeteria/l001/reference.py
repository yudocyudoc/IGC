"""CAF-L001 bounded observed 2-receptacle trajectory. Not a service distribution."""
from __future__ import annotations
import csv
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

HERE = Path(__file__).resolve().parent
METRICS = HERE / "metricas_original.csv"
EXPECTED_SHA256 = "f45e12578813f75ae6f201e5390f93e39bf115aed2849edd704072f09544fc28"
NODES = ("H04", "H05", "H06", "H07")
FIELDS = ("id", "metric", "lower", "upper", "unit", "source_events", "kind",
          "sample_size_batches", "usable_as_service_distribution", "interpretation")

def read_metrics(path=METRICS, *, pin=True):
    raw = Path(path).read_bytes()
    if pin and sha256(raw).hexdigest() != EXPECTED_SHA256:
        raise ValueError("METRIC_SOURCE_SHA256_CHANGED")
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if tuple(reader.fieldnames or []) != FIELDS:
            raise ValueError("METRIC_SCHEMA_CHANGED")
        rows = list(reader)
    if len(rows) != 9 or {r["id"] for r in rows} != {f"F{i:02d}" for i in range(1, 10)}:
        raise ValueError("METRIC_IDS_CHANGED")
    data = {}
    for r in rows:
        if r["sample_size_batches"] != "1" or r["usable_as_service_distribution"].lower() != "false":
            raise ValueError("SERVICE_DISTRIBUTION_PROMOTION_PROHIBITED")
        low, high = float(r["lower"]), float(r["upper"])
        if not (0 <= low <= high < float("inf")):
            raise ValueError("INVALID_BOUNDS")
        events = json.loads(r["source_events"])
        if r["id"] == "F09":
            if events != ["H01", "H05", "H06"] or r["unit"] != "recipiente*s_video" or r["kind"] != "integral_cohorte":
                raise ValueError("F09_DERIVED_AREA_SEMANTICS_CHANGED")
        elif len(events) != 2 or not set(events) <= (set(NODES) | {"H01"}) or r["unit"] != "s_video" or r["kind"] != "intervalo_entre_hitos":
            raise ValueError("INVALID_TIME_METRIC_SEMANTICS")
        data[r["id"]] = {"bounds":[low,high], "events":events, "metric":r["metric"],
                         "derived_not_independent":r["id"]=="F09"}
    return data

def coefficient(metric):
    c = np.zeros(4)
    events = metric["events"]
    if len(events) == 3:
        c[NODES.index("H05")] = 1
        c[NODES.index("H06")] = 1
    else:
        start,end = events
        if start != "H01":
            c[NODES.index(start)] -= 1
        if end != "H01":
            c[NODES.index(end)] += 1
    return c

def constraints(metrics, *, direct=True):
    a,b = [], []
    for m in metrics.values():
        c = coefficient(m)
        lo,hi = m["bounds"]
        a.extend((c, -c))
        b.extend((hi, -lo))
    for first,last in (("H01","H04"),("H04","H05"),("H05","H06"),("H06","H07")):
        c = np.zeros(4)
        if first != "H01":
            c[NODES.index(first)] += 1
        c[NODES.index(last)] -= 1
        a.append(c)
        b.append(0)
    if direct:
        from experiments.cafeteria.l001.e00_correction import direct_constraint_rows
        da, db = direct_constraint_rows()
        a.extend(da)
        b.extend(db)
    return np.asarray(a), np.asarray(b)

def solve(objective,a,b):
    ans=linprog(objective, A_ub=a, b_ub=b, bounds=[(None,None)]*4, method="highs")
    if not ans.success:
        raise ValueError("NO_JOINTLY_FEASIBLE_TRAJECTORY")
    return ans

def compare_legacy(metrics):
    from experiments.cafeteria.l001.e00_correction import check_lineage
    return check_lineage(metrics)

def execute(path=METRICS, *, pin=True):
    metrics=read_metrics(path,pin=pin)
    a,b=constraints(metrics)
    witness=solve(np.ones(4),a,b).x
    times={"H01":0.0, **{n:round(float(v),6) for n,v in zip(NODES,witness)}}
    ranges={}
    for i,n in enumerate(NODES):
        c=np.zeros(4);c[i]=1
        ranges[n]=[round(float(solve(c,a,b).fun),6),round(float(-solve(-c,a,b).fun),6)]
    verified={}
    for k,item in metrics.items():
        value=float(coefficient(item)@witness)
        lo,hi=item["bounds"]
        if not lo-1e-6<=value<=hi+1e-6:
            raise AssertionError("INCONSISTENT_INTERNAL_SOLVER")
        verified[k]={"bounds":item["bounds"],"witness":round(value,6),
                     "derived_not_independent":item["derived_not_independent"]}
    h4,h5,h6,h7=[times[k] for k in NODES]
    trace=[
        {"t":0.0,"event":"H01_FIRST_VISIBLE","pending":2,"received":0},
        {"t":h4,"event":"H04_PICKUP_END","pending":2,"received":0},
        {"t":h5,"event":"H05_FIRST_RECEIPT","pending":1,"received":1},
        {"t":h6,"event":"H06_SECOND_RECEIPT","pending":0,"received":2},
        {"t":h7,"event":"H07_PASS_CONTACT","pending":0,"received":2},
    ]
    if any(e["pending"]+e["received"]!=2 for e in trace):
        raise AssertionError("MATERIAL_NOT_CONSERVED")
    if abs((h5+h6)-verified["F09"]["witness"])>1e-6:
        raise AssertionError("F09_DERIVED_AREA_MISMATCH")
    return {
        "schema":"igc-caf-l001-reference/0.1",
        "status":"JOINTLY_FEASIBLE_OBSERVATIONAL_CONSTRAINTS",
        "source_sha256":"sha256:"+sha256(Path(path).read_bytes()).hexdigest(),
        "clock":"video_seconds_not_certified_physical",
        "sample_size_batches":1,
        "ranges_relative_H01_video_s":{"H01":[0,0],**ranges},
        "one_nonunique_witness":times, "checks":verified,
        "trace":trace,
        "area_receptacle_video_s":round(h5+h6,6),
        "legacy":compare_legacy(metrics),
        "rejected_in_this_batch_if_measurements_hold":[
            "TWO_RECEIPTS_EXACTLY_SIMULTANEOUS",
            "BOTH_RECEIVED_AT_PICKUP_END",
        ],
        "nonclaims":["NOT_SERVICE_TIMES","NOT_ARRIVAL_PROCESS",
                     "NOT_FULL_CAFE_INVENTORY","NOT_REALTIME_CLOCK",
                     "NOT_NINE_INDEPENDENT_OBSERVATIONS","NOT_RECONCILED_WITH_MASTER"],
    }
