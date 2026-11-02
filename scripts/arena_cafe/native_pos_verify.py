"""Independent A1 numerical conservation audit for native POS scenario traces.

Native CSV and explicit solver attempt marker are required; Python-only traces
are never accepted as G2. The solver invocation itself is an external CI fact,
not established cryptographically by these local assertions.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
from fractions import Fraction as Q

from scripts.arena_cafe import native_pos_scenario as scenario, observation_eval as hj
from scripts.arena_cafe.native_handoff import need, validate_a1_visible
from scripts.arena_v0_contract import canonical, digest

SCHEMA="igc-cafe-a1-pos-native-g2-engineering-audit/0.1"


def sha(path):
    return "sha256:"+hashlib.sha256(Path(path).read_bytes()).hexdigest()


def expected_input_at(t_min,bins):
    """Known mass of the *published piecewise reconstruction*, not raw DES."""
    result=0.0
    for b in bins:
        start=float(Q(b["start_minutes_exact"]))
        end=float(Q(b["end_minutes_exact"]))
        result+=b["orders"] * min(1.0,max(0.0,(t_min-start)/(end-start)))
    return result


def audit(visible,manifest,source,script,csv_file,attempt_marker,exit_marker):
    arm=manifest.get("arm_id")
    condition=manifest.get("condition_id")
    need(arm in ("D","M") and condition in ("O0","O1"),"A1_G2_BAD_ARM_CONDITION")
    validate_a1_visible(visible,condition)
    need(manifest.get("schema")==scenario.SCHEMA
         and manifest.get("input_hash")==digest(visible)
         and manifest.get("source_snapshot_hash")==visible["source_snapshot_hash"],
         "A1_G2_INPUT_PROVENANCE_MISMATCH")
    need(manifest.get("modelica_sha256")==sha(source)
         and manifest.get("mos_sha256")==sha(script),
         "A1_G2_NATIVE_MODEL_OR_SCRIPT_CHANGED")
    need(manifest.get("reconstruction_bins")==scenario.bins_from_pos(visible,condition),
         "A1_G2_NATIVE_SOURCE_BINS_CHANGED")
    need(Path(attempt_marker).read_text().strip()=="INVOCATION_STARTED"
         and Path(exit_marker).read_text().strip()=="0",
         "A1_G2_NO_SUCCESSFUL_SOLVER_ATTEMPT")
    csv_path=Path(csv_file)
    need(csv_path.is_file() and csv_path.stat().st_size>500,
         "A1_G2_MISSING_NATIVE_SOLVER_CSV")
    # The backend E1 minimal graph is exactly source→preparation→dispatch→receipt.
    # The precise instance ids are supplied by the graph emitted under the
    # native candidate manifest, not guessed by position or world labels.
    if arm=="M":
        from scripts.arena_cafe.observation_eval import _candidate_roles
        roles=_candidate_roles(manifest["candidate"],
                               Path("experiments/e1/registry.base.json"))
        stock_columns=[roles["preparation"]+".stock.level",
                       roles["receipt"]+".total"]
        graph=manifest["candidate"]["ast"]
        dispatch=[x["id"] for x in graph["instances"] if x["role"]=="dispatch"]
        need(len(dispatch)==1,"A1_G2_M_DISPATCH_NOT_UNIQUE")
        stock_columns=[roles["preparation"]+".stock.level",
                       dispatch[0]+".stock.level"]
    else:
        stock_columns=["s1","s2"]
    data=hj._rows(csv_path)
    max_residual=0.0
    prev=-math.inf
    prev_delivery=-math.inf
    seen_times=[]
    for row in data:
        native_t=hj._column(row,"time")
        minute=native_t*(60 if arm=="M" else 1)
        need(minute+1e-8>=prev and -1e-8<=minute<=10+1e-7,
             "A1_G2_TIME_OR_CUTOFF")
        delivered=hj._column(row,"deliveredTotal" if arm=="M" else "delivered")
        stock=[hj._column(row,name) for name in stock_columns]
        need(min([delivered,*stock])>=-1e-6 and delivered+1e-6>=prev_delivery,
             "A1_G2_NEGATIVE_OR_DECREASING_STOCK")
        expected=expected_input_at(minute,manifest["reconstruction_bins"])
        residual=abs(delivered+sum(stock)-expected)
        max_residual=max(max_residual,residual)
        prev=minute;prev_delivery=delivered
        seen_times.append(minute)
    need(abs(seen_times[0])<=1e-7 and abs(seen_times[-1]-10)<=1e-6,
         "A1_G2_INCOMPLETE_SOLVER_WINDOW")
    need(max_residual<=0.08,"A1_G2_MATERIAL_BALANCE_FAILED")
    return {"schema":SCHEMA,"arm_id":arm,"condition_id":condition,
            "status":"NATIVE_G2_MATERIAL_BALANCE_PASS_ENGINEERING_ONLY",
            "solver_attempt_marker_present":True,
            "solver_exit_code":0,
            "native_model_sha256":sha(source),
            "solver_script_sha256":sha(script),"solver_csv_sha256":sha(csv_path),
            "candidate_full_hash":digest(manifest["candidate"]),
            "nominal_parameters_are_assumptions":True,
            "stimulus_is_half_minute_reconstruction":True,
            "max_material_residual_orders":max_residual,
            "output_rows":len(data),
            "G3":"NOT_RUN",
            "independent_forecast":"NOT_RUN",
            "scientific_calibration_or_identification":"NOT_DEMONSTRATED"}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--visible",type=Path,required=True)
    p.add_argument("--native-dir",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    need(not a.out.exists(),"A1_G2_REPORT_ALREADY_EXISTS")
    root=a.native_dir
    report=audit(json.loads(a.visible.read_text()),
      json.loads((root/"manifest.json").read_text()),
      root/"native.mo",root/"simulate.mos",
      root/"native_res.csv",root/"INVOCATION_STARTED",root/"exit_code.txt")
    a.out.write_bytes(canonical(report)+b"\n")
    print(json.dumps({k:report[k] for k in
                      ("arm_id","condition_id","status","max_material_residual_orders")}))


if __name__=="__main__":
    main()
