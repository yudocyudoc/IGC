"""Prepare empirical *construction* feedback from Buffalo B2 own real OpenModelica trace.

Never reads D/M hypotheses, a generator world, hidden data or a holdout.
All three source artifacts are byte-locked GitHub Actions outputs.
Feedback is a diagnostic to Buffalo, not a repaired equation or a certified G3.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math
from pathlib import Path
from scripts.arena_b_construction_check import assess

PARENT_NATIVE_SHA = "d7630830b4812c8880dc88c5f93f821707a75d22e0ecdf2cc1e9b5d8ec0889b9"
PARENT_CSV_SHA = "9de161b6d55bd24f4e4d839d3665abede8dbb39b7174b8a35b0a75bfd7eded05"
PARENT_REPORT_SHA = "ba3c66d2a7b662e8a008262b459a7e920aa4c92b9630907a6e231c101b2d34a6"
SCHEMA = "igc-b-own-physical-construction-feedback/0.1"

def require(ok, code):
    if not ok: raise ValueError(code)

def locked(path, expected):
    b=Path(path).read_bytes()
    require(hashlib.sha256(b).hexdigest()==expected,"SOURCE_BYTES_CHANGED:"+Path(path).name)
    return b

def make_feedback(native_path, csv_path, report_path, visible_path):
    native=json.loads(locked(native_path,PARENT_NATIVE_SHA))
    rows=list(csv.DictReader(locked(csv_path,PARENT_CSV_SHA).decode("utf-8-sig").splitlines()))
    # Earlier CI wrote the two literal characters backslash+n after JSON,
    # not a newline. Preserve the authenticated file bytes unchanged and
    # explicitly accept only this known exact legacy footer.
    report_raw=locked(report_path,PARENT_REPORT_SHA).decode("utf8")
    report,end=json.JSONDecoder().raw_decode(report_raw)
    tail=report_raw[end:]
    require(tail.strip() in ("", r"\\n"),"UNEXPECTED_LEGACY_REPORT_TRAILER")
    visible=json.loads(Path(visible_path).read_text())
    require(set(visible)=={
        "schema","investigation_id","round_id","question","source_snapshot_hash",
        "iteration_limit","construction","observability","resources"
    }, "UNRECOGNIZED_VISIBLE_DATA")
    require(set(visible["construction"])=={"input_profile","observations","known_conditions"},
            "FOREIGN_EVIDENCE_PRESENT")
    require(visible["investigation_id"]=="B-NATIVE-SYNTHETIC" and visible["round_id"]=="R0",
            "WRONG_CONSTRUCTION_ROUND")
    require(visible["resources"]["max_llm_calls"]==1 and visible["iteration_limit"]==2,
            "ORIGINAL_BUDGET_CHANGED")
    model=native.get("model",{})
    require(isinstance(model.get("variables"),list) and len(model["variables"])==15
            and len(model.get("relationships",[]))==19,"NOT_ARCHIVED_B2_MODEL")
    calculated=assess(rows,visible)
    for key in ("balance_residual_max_items","rmse_all_observations_items",
                "rmse_noninitial_observations_items"):
        require(math.isclose(report[key],calculated[key],rel_tol=1e-10,abs_tol=1e-12),
                "ARCHIVED_REPORT_DISAGREES_WITH_REAL_CSV:"+key)
    require(report["construction_observations"]==calculated["construction_observations"],
            "ARCHIVED_OBSERVATIONS_CHANGED")
    # Provide actual physical states/flows at the observed times, no interpolation.
    selected=[]
    for item in calculated["construction_observations"]:
        match=[r for r in rows if math.isclose(float(r["time"]),item["time_hour"],abs_tol=1e-8)]
        require(len(match)==1,"AMBIGUOUS_CSV_OBSERVATION_TIME")
        row=match[0]
        keep={k:float(row[k]) for k in (
            "pending_work","delivered_work","arrivals","completions",
            "capacity_utilization","completion_capacity","nominal_capacity"
        )}
        require(all(math.isfinite(v) for v in keep.values()),"NONFINITE_PHYSICAL_SIGNAL")
        selected.append({"t_hour":item["time_hour"],"stock_flow_state":keep,
                         "observed_delivered_items":item["observed_items"],
                         "simulated_delivered_items":item["predicted_items"],
                         "residual_simulated_minus_observed_items":item["residual_items"]})
    eqs={v["name"]:v.get("equation") for v in model["variables"]}
    require(eqs["completions"]=="completion_capacity * capacity_utilization"
            and eqs["completion capacity"]=="nominal_capacity * capacity_utilization",
            "PARENT_B2_EQUATIONS_CHANGED")
    return {
        "schema":SCHEMA,"arm_id":"B",
        "scope":"OWN_BUFFALO_B2_REAL_OPENMODELICA_PHYSICAL_FEEDBACK",
        "revision_type":"SEPARATELY_AUTHORIZED_EXTENSION_AFTER_ORIGINAL_ROUND_BUDGET",
        "parent_iteration":1,"proposed_iteration":2,
        "parent_native_bytes_sha256":"sha256:"+PARENT_NATIVE_SHA,
        "parent_solver_csv_bytes_sha256":"sha256:"+PARENT_CSV_SHA,
        "parent_diagnostic_bytes_sha256":"sha256:"+PARENT_REPORT_SHA,
        "physical_solver":{"engine":"OpenModelica","method":"Euler",
                           "time_window_hour":[0,8],"dt_hour":0.125,
                           "graphical_function_semantics":"PIECEWISE_LINEAR_CLAMPED_ENDPOINTS_ADAPTER_ASSUMPTION",
                           "native_simulator_equivalence":"NOT_ESTABLISHED"},
        "observations_type":"SYNTHETIC_CONSTRUCTION_ALREADY_VISIBLE_NOT_HOLDOUT",
        "observations_and_physical_state":selected,
        "physical_invariants":{"euler_mass_balance_max_residual_items":
                                calculated["balance_residual_max_items"],
                               "conserved_material":["pending_work","delivered_work"],
                               "material_input":"arrivals"},
        "construction_adequacy":{"rmse_all_four_items":calculated["rmse_all_observations_items"],
                                 "rmse_noninitial_three_items":
                                 calculated["rmse_noninitial_observations_items"],
                                 "instrument_error_bound":"UNSPECIFIED",
                                 "g3_status":"DESCRIPTIVE_ONLY_NOT_CERTIFIED"},
        "candidate_mechanism_observation":{
            "derived_exact_relation":"completions = nominal_capacity * capacity_utilization^2",
            "derivation_from_own_equations":[
                "completion_capacity = nominal_capacity * capacity_utilization",
                "completions = completion_capacity * capacity_utilization"
            ],
            "epistemic_status":"ALGEBRAIC_IDENTITY_NOT_PROOF_OF_CAUSAL_ERROR"
        },
        "no_cross_arm_information":True,"no_holdout_information":True,
        "guidance":"Use only YOUR previous native model and these own physical diagnostic results. "
                   "Decide whether to revise structure, stocks, lookup, delays or parameters under "
                   "Buffalo quantitative SD-AI rules. Do not assume utilization squared is a bug; "
                   "justify any change. Return native model, or explain insufficient evidence. "
                   "Never claim holdout validation or a causal truth result."
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--native",type=Path,required=True)
    p.add_argument("--csv",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    p.add_argument("--visible",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    require(not a.out.exists(),"FEEDBACK_ALREADY_EXISTS")
    result=make_feedback(a.native,a.csv,a.report,a.visible)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"schema":result["schema"],
        "residuals":[r["residual_simulated_minus_observed_items"]
                    for r in result["observations_and_physical_state"]],
        "source":"REAL_B2_OPENMODELICA_CSV",
        "parent_verified":True,"heldout":"NOT_RUN"}))

if __name__=="__main__":main()
