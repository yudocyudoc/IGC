"""Convert ONE real new T2 OpenModelica CSV into a single locked-time observation.

The world graph and previous T2 world CSV are used ONLY for physical
provenance/instrument consistency, never submitted to frozen R4 selector.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
import math
from pathlib import Path

from scripts.arena_m3_select import model_rows,sample
from scripts.arena_m_visible_verify import verify
from scripts.arena_r3_pt06_t23_preregister import freeze,CASES,make_world_graph,guard,WORLD_PACKAGE
from scripts.arena_r4_pt07_t2_one_world import SHA
from scripts.arena_r4_pt07_t2_score import SOURCE
from scripts.arena_v0_contract import canonical,digest

def filehash(p):
    return "sha256:"+sha256(Path(p).read_bytes()).hexdigest()

def extract(new_root,old_t23,lock_root,catalog):
    new_root,old_t23,lock_root=map(Path,(new_root,old_t23,lock_root))
    budget=json.loads((new_root/"budget.json").read_text())
    protocol,original_package,_=freeze()
    original=old_t23/(WORLD_PACKAGE+"-NOT-SIMULATED.mo")
    new_model=new_root/(WORLD_PACKAGE+"-ORIGINAL.mo")
    guard(original.read_bytes()==new_model.read_bytes()==original_package.encode()
          and filehash(new_model)==budget["original_T2_world_package_sha256"],
          "R4_T2_GENERATING_SOURCE_DIFFERS_FROM_PREDECLARED")
    lockfile=lock_root/"forecast-lock.json"
    guard(filehash(lockfile)==budget["forecast_lock_sha256"]==SHA,
          "R4_T2_LOCK_OR_BUDGET_TAMPERED")
    lock=json.loads(lockfile.read_text())
    guard(lock["chosen_observation_time_hours"]==1.0 and
          budget["world_simulate_max"]==1 and budget["candidate_simulate_max"]==0,
          "R4_T2_NOT_SINGLE_DECLARED_FUTURE_TIME")
    new_csv=new_root/"new-world/r4_t2_res.csv"
    old_csv=old_t23/"researcher-private/t2_res.csv"
    guard(new_csv.is_file() and old_csv.is_file(),"R4_T2_REAL_FRESH_OR_ORIGINAL_CSV_MISSING")
    old_rows=model_rows(old_csv)
    new_rows=model_rows(new_csv)
    guard(all(0<=float(row["time"])<=1.00000001 for row in new_rows)
          and math.isclose(float(new_rows[-1]["time"]),1.0,abs_tol=1e-7),
          "R4_T2_NEW_RUN_PASSES_FUTURE_TIME_WINDOW")
    # Verify same synthetic world and its original early public construction
    # trajectory. This is a *provenance/solver consistency* audit, not a new
    # conditioning step; future score sees ONLY the locked time's value.
    early=[0,0.05,0.1,0.15]
    early_new=sample(new_rows,early)
    early_old=sample(old_rows,early)
    max_early_discrepancy=max(abs(a-b) for a,b in zip(early_new,early_old))
    guard(max_early_discrepancy<=1e-5,
          "R4_T2_NEW_GENERATOR_NOT_REPRODUCING_ORIGINAL_EARLY_RUN")
    cfg,classes,graph,_=make_world_graph(CASES[0])
    visible={"construction":{"input_profile":{
          "kind":"pulse","rate":1.7,"duration":2.0},
          "observations":[{"t":0,"delivered":0.0},
                          {"t":1,"delivered":0.0}]}}
    check=verify(new_rows,visible,{
        "arm_id":"M","method":"short-e1-one-minimal-molecular-candidate/0.1",
        "graph":graph},catalog)
    guard(check["status"]=="G2_SIMULATED_CONDITIONALLY"
          and check["max_material_balance_residual"]<=0.015,
          "R4_T2_NEW_WORLD_NOT_PHYSICALLY_VALID")
    actual=sample(new_rows,[lock["chosen_observation_time_hours"]])[0]
    observation={
        "schema":"igc-arena-r4-a-t2-one-future-physical-measurement/0.1",
        "case_id":lock["protocol"]["case_id"],
        "time_hours":1.0,"delivered_items":actual,
        "source_kind":SOURCE,
        "original_modelica_sha256":filehash(new_model),
        "physical_solver_csv_sha256":filehash(new_csv),
        "forecast_lock_file_sha256":SHA,
        "collection_status":"NEW_SOLVER_RUN_AFTER_LOCK"}
    private={
        "schema":"igc-arena-r4-a-t2-researcher-private-provenance/0.1",
        "old_T2_original_world_csv_sha256":filehash(old_csv),
        "new_T2_future_world_csv_sha256":filehash(new_csv),
        "world_source_package_sha256":filehash(new_model),
        "synthetic_generating_class_REVEAL_AFTER_SCORING":"C01",
        "original_T2_spec_sha256":digest(CASES[0]),
        "old_source_time_window_hours":[0,0.15],
        "new_source_time_window_hours":[0,1],
        "early_four_points_max_abs_delta_items":max_early_discrepancy,
        "physical_G2":check["status"],
        "maximum_material_balance_residual_items":check["max_material_balance_residual"],
        "new_physical_observation_sha256":digest(observation),
        "world_time_after_1h_not_simulated":True,
        "no_R4_external_holdout":True}
    return observation,private

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--new-root",type=Path,required=True)
    p.add_argument("--original-t23",type=Path,required=True)
    p.add_argument("--lock",type=Path,required=True)
    p.add_argument("--catalog",type=Path,required=True)
    a=p.parse_args()
    pub,priv=extract(a.new_root,a.original_t23,a.lock,json.loads(a.catalog.read_text()))
    public=a.new_root/"one-new-physical-observation.json"
    private=a.new_root/"new-world/source-provenance-PRIVATE.json"
    guard(not public.exists() and not private.exists(),"R4_T2_MEASUREMENT_ALREADY_CAPTURED")
    public.write_bytes(canonical(pub)+b"\n")
    private.write_bytes(canonical(priv)+b"\n")
    print(json.dumps({"status":"R4_T2_FRESH_ONE_HOUR_PHYSICAL_OBSERVATION",
       "time_h":pub["time_hours"],"value_items":pub["delivered_items"],
       "G2":priv["physical_G2"],
       "original_vs_new_early_max_delta":priv["early_four_points_max_abs_delta_items"]},
       sort_keys=True))

if __name__=="__main__":
    main()
