"""PT06: extract four construction measurements from the REAL R3-T1 world CSV.

The selector receives a separate JSON case with NO generating graph, parameters,
truth identifier, or future observation. The private world ends at t=3 hours.
"""
from __future__ import annotations
import argparse
import copy
from hashlib import sha256
import json
from pathlib import Path

from scripts.arena_m3_prepare import family
from scripts.arena_m3_select import model_rows,sample
from scripts.arena_m_visible_verify import verify
from scripts.arena_r3_pt06_parametric import CASE_PLAN,plan,guard,generate_first_case_world_modelica
from scripts.arena_r3_pt06_evaluate import CASE_SCHEMA, checked_case
from scripts.arena_v0_contract import canonical,digest

SCHEMA="igc-arena-r3-pt06-t1-construction-extraction/0.1"


def extract(folder,catalog_file):
    folder=Path(folder)
    model=folder/"ArenaR3WorldT1-NOT-SIMULATED.mo"
    guard(model.read_bytes()==generate_first_case_world_modelica().encode(),
          "R3_T1_WORLD_MODEL_CHANGED")
    path=folder/"world-private"/"t1_res.csv"
    guard(path.is_file(),"R3_T1_REAL_WORLD_SOLVER_CSV_MISSING")
    cfg,classes,paths=family()
    source_key,source_graph=paths[0]
    source_graph=copy.deepcopy(source_graph)
    for inst in source_graph["instances"]:
        role=inst["role"]
        if role in CASE_PLAN["generating_role_responseTime_hours"]:
            inst["parameters"]["responseTime"]=CASE_PLAN["generating_role_responseTime_hours"][role]
    rows=model_rows(path)
    catalog=json.loads(Path(catalog_file).read_text())
    public={"construction":{"input_profile":{"kind":"pulse","rate":1.7,"duration":2},
                            "observations":[{"t":t,"delivered":0.0} for t in [0,1,2,3]]}}
    g2=verify(rows,public,{
        "arm_id":"M","method":"short-e1-one-minimal-molecular-candidate/0.1",
        "graph":source_graph},catalog)
    guard(g2["status"]=="G2_SIMULATED_CONDITIONALLY" and
          g2["max_material_balance_residual"]<=0.015,
          "R3_T1_WORLD_FAILED_PHYSICAL_G2")
    raw=sample(rows,[0,1,2,3])
    observed=[max(0.0,actual+noise) for actual,noise in
              zip(raw,CASE_PLAN["declared_noise_items"])]
    construction=[{"t":t,"delivered":float(y)}
                  for t,y in zip(CASE_PLAN["construction_times_hours"],observed)]
    case={
       "schema":CASE_SCHEMA,"case_id":CASE_PLAN["case_id"],
       "observability":"deliveredTotal",
       "public_stimulus":{"kind":"pulse","rate":1.7,"duration":2.0},
       "construction_observations":construction,
       "measurement_bound_status":"NO_INSTRUMENT_BOUND",
       "source_snapshot_hash":digest(construction),
       "synthetic_case":True
    }
    checked_case(case,plan()[0])
    private={
       "schema":SCHEMA,"case_id":CASE_PLAN["case_id"],
       "world_source":"ORIGINAL_E1_C00_OFF_GRID_PARAMETERS",
       "world_material_topology":"C00",
       "world_responseTime_hours":CASE_PLAN["generating_role_responseTime_hours"],
       "original_world_model_sha256":"sha256:"+sha256(model.read_bytes()).hexdigest(),
       "original_solver_csv_sha256":"sha256:"+sha256(path.read_bytes()).hexdigest(),
       "world_simulated_time_window_hours":[0,3],
       "world_reserved_observations":"NOT_GENERATED",
       "world_solver_G2_status":g2["status"],
       "world_balance_residual_max_items":g2["max_material_balance_residual"],
       "world_raw_samples_t0_1_2_3":raw,
       "noise_items":CASE_PLAN["declared_noise_items"],
       "construction_case_sha256":digest(case),
       "no_G3_or_independent_holdout":True,
    }
    return case,private


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--catalog",type=Path,required=True)
    a=p.parse_args()
    public,private=extract(a.root,a.catalog)
    casepath=a.root/"construction-case.json"
    guard(not casepath.exists(),"R3_T1_CASE_ALREADY_EXISTS")
    casepath.write_bytes(canonical(public)+b"\n")
    privatepath=a.root/"world-private"/"provenance.json"
    guard(not privatepath.exists(),"R3_T1_PRIVATE_PROVENANCE_ALREADY_EXISTS")
    privatepath.write_bytes(canonical(private)+b"\n")
    print(json.dumps({"status":"R3_T1_REAL_WORLD_FOUR_CONSTRUCTION_POINTS_ONLY",
                      "case_sha256":digest(public),
                      "world_G2":private["world_solver_G2_status"],
                      "world_max_balance":private["world_balance_residual_max_items"]}))

if __name__=="__main__":
    main()
