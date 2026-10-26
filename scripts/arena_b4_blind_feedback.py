"""B4: physical construction data only, with NO suggested mechanism.

This independently authorized contrast with B3 starts at the *same byte-locked*
Buffalo B2 native model and original OpenModelica CSV. We use the existing
authenticated B2 audit to verify provenance, then export only raw observations,
native simulated stocks/flows and signed residuals. The computed algebraic
identity in B3 feedback is NOT included in B4's prompt or provider payload.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
from scripts.arena_b_physical_feedback import (
    make_feedback, require, PARENT_NATIVE_SHA, PARENT_CSV_SHA, PARENT_REPORT_SHA
)

SCHEMA="igc-b-blind-construction-residuals/0.1"
PARENT="sha256:"+PARENT_NATIVE_SHA
COLUMNS=("pending_work","delivered_work","arrivals","completions")
OBS_KEYS=("t_hour","observed_delivered_items","simulated_delivered_items",
          "residual_simulated_minus_observed_items","stock_flow_state")
PROHIBITED=("candidate_mechanism_observation","derived_exact_relation",
            "utilization^2","utilization squared","double counting",
            "maximum capacity","upper bound","nominal_capacity",
            "capacity_utilization","completion_capacity",
            "suspect equation","suspected equation","0.6 items/h",
            "0.75 items/h")


def make_blind(native_path,csv_path,report_path,visible_path):
    verified=make_feedback(native_path,csv_path,report_path,visible_path)
    rows=[]
    for row in verified["observations_and_physical_state"]:
        state={key:row["stock_flow_state"][key] for key in COLUMNS}
        rows.append({
            "t_hour":row["t_hour"],
            "observed_delivered_items":row["observed_delivered_items"],
            "simulated_delivered_items":row["simulated_delivered_items"],
            "residual_simulated_minus_observed_items":
                row["residual_simulated_minus_observed_items"],
            "stock_flow_state":state,
        })
    result={
        "schema":SCHEMA,
        "arm_id":"B",
        "origin":"B2_OWN_OPENMODELICA_REAL_CONSTRUCTION_ONLY",
        "experiment":"SEPARATE_BLIND_CONTRAST_WITH_PRIOR_MECHANISTICALLY_CUED_B3",
        "parent_native_bytes_sha256":PARENT,
        "parent_solver_csv_bytes_sha256":"sha256:"+PARENT_CSV_SHA,
        "parent_diagnostic_bytes_sha256":"sha256:"+PARENT_REPORT_SHA,
        "source_solvers_semantics":{
            "engine":"OpenModelica","method":"Euler","dt_hour":0.125,
            "lookup_interpolation":"ADAPTER_ASSUMPTION_NOT_NATIVE_PARITY_CERTIFIED",
        },
        "points":rows,
        "physical_integrity":{
            "material_balance_max_abs_items":
                verified["physical_invariants"]["euler_mass_balance_max_residual_items"]
        },
        "scope":{
            "construction_only":True,"reserved_data_included":False,
            "competing_arm_data_included":False,"original_budget_exhausted":True,
            "new_trial_not_part_of_original_round":True,
        }
    }
    validate_blind(result)
    return result


def validate_blind(v):
    require(set(v)=={"schema","arm_id","origin","experiment",
                    "parent_native_bytes_sha256",
                    "parent_solver_csv_bytes_sha256",
                    "parent_diagnostic_bytes_sha256",
                    "source_solvers_semantics","points","physical_integrity","scope"},
            "B4_BLIND_UNEXPECTED_TOP_LEVEL_FIELD")
    require(v["schema"]==SCHEMA and v["arm_id"]=="B"
            and v["parent_native_bytes_sha256"]==PARENT
            and v["parent_solver_csv_bytes_sha256"]=="sha256:"+PARENT_CSV_SHA
            and v["parent_diagnostic_bytes_sha256"]=="sha256:"+PARENT_REPORT_SHA
            and v["origin"]=="B2_OWN_OPENMODELICA_REAL_CONSTRUCTION_ONLY",
            "B4_BLIND_SOURCE_MISMATCH")
    require(v["scope"]=={
        "construction_only":True,"reserved_data_included":False,
        "competing_arm_data_included":False,"original_budget_exhausted":True,
        "new_trial_not_part_of_original_round":True},
        "B4_BLIND_SCOPE_CHANGED")
    require(v["source_solvers_semantics"]=={
        "engine":"OpenModelica","method":"Euler","dt_hour":0.125,
        "lookup_interpolation":"ADAPTER_ASSUMPTION_NOT_NATIVE_PARITY_CERTIFIED"},
        "B4_BLIND_ENGINE_CHANGED")
    require(set(v["physical_integrity"])=={"material_balance_max_abs_items"} and
            isinstance(v["physical_integrity"]["material_balance_max_abs_items"],(float,int))
            and math.isfinite(v["physical_integrity"]["material_balance_max_abs_items"])
            and v["physical_integrity"]["material_balance_max_abs_items"]<1e-8,
            "B4_BLIND_MATERIAL_BALANCE")
    pts=v["points"]
    require(isinstance(pts,list) and len(pts)==4,"B4_BLIND_POINTS_CHANGED")
    for i,p in enumerate(pts):
        require(set(p)==set(OBS_KEYS) and p["t_hour"]==[0,1,2,4][i]
                and set(p["stock_flow_state"])==set(COLUMNS),
                "B4_BLIND_OBSERVATION_FIELDS_CHANGED")
        require(all(isinstance(x,(int,float)) and math.isfinite(x)
                    for x in [p[k] for k in OBS_KEYS if k not in ("stock_flow_state",)]
                    +list(p["stock_flow_state"].values())),
                "B4_BLIND_NONFINITE")
        require(abs(p["simulated_delivered_items"]-
                    p["observed_delivered_items"]-
                    p["residual_simulated_minus_observed_items"])<1e-8,
                "B4_BLIND_RESIDUAL_TAMPERED")
        require(abs(p["stock_flow_state"]["delivered_work"]-
                    p["simulated_delivered_items"])<1e-8,
                "B4_BLIND_TRACE_TAMPERED")
    text=json.dumps(v,sort_keys=True).lower()
    require(not any(s.lower() in text for s in PROHIBITED),
            "B4_BLIND_HINT_OR_INFERRED_MECHANISM_LEAKED")
    return True


def main():
    ap=argparse.ArgumentParser()
    for arg in ("native","csv","report","visible","out"):
        ap.add_argument("--"+arg,required=True,type=Path)
    a=ap.parse_args()
    require(not a.out.exists(),"B4_FEEDBACK_ALREADY_EXISTS")
    obj=make_blind(a.native,a.csv,a.report,a.visible)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"schema":SCHEMA,"rows":len(obj["points"]),
         "mechanism_cue_sent":False,"source":"REAL_B2_SOLVER_CSV",
         "max_balance":obj["physical_integrity"]["material_balance_max_abs_items"]}))


if __name__=="__main__": main()
