"""Future T2/T3 world CSV -> construction-only separate files, no selector truth.

Offline helper only until two-world solver run is separately authorized.
World truth goes into researcher-private metadata, not case inputs.
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
from scripts.arena_r3_pt06_t23_preregister import CASES,freeze,make_world_graph,guard
from scripts.arena_r3_pt06_t23_evaluate import CASE_SCHEMA,validate_case
from scripts.arena_v0_contract import canonical,digest

def extract(root,catalog):
    root=Path(root)
    protocol,pkg,_=freeze()
    guard(json.loads((root/"protocol.json").read_text())==protocol
          and (root/"ArenaR3T23Worlds-NOT-SIMULATED.mo").read_bytes()==pkg.encode(),
          "R3_T23_WORLD_INPUT_MODIFIED")
    public=[]
    private=[]
    for i,spec in enumerate(CASES):
        f=root/"researcher-private"/f"t{i+2}_res.csv"
        guard(f.is_file(),"R3_T23_REAL_GENERATOR_CSV_MISSING")
        cfg,classes,graph,key=make_world_graph(spec)
        rows=model_rows(f)
        times=spec["times_hours"]
        public_zero={"construction":{"input_profile":{"kind":"pulse","rate":1.7,"duration":2.0},
          "observations":[{"t":t,"delivered":0.0} for t in times]}}
        g2=verify(rows,public_zero,{
            "arm_id":"M","method":"short-e1-one-minimal-molecular-candidate/0.1",
            "graph":graph},catalog)
        guard(g2["status"]=="G2_SIMULATED_CONDITIONALLY" and
              g2["max_material_balance_residual"]<=0.015,
              "R3_T23_GENERATOR_MASS_BALANCE_FAILED")
        # No out-of-window samples or future holdout are read.
        v=sample(rows,times)
        obs=[{"t":t,"delivered":float(max(0.0,y+n))}
             for t,y,n in zip(times,v,spec["declared_noise_items"])]
        case={
            "schema":CASE_SCHEMA,"case_id":spec["id"],
            "observability":"deliveredTotal",
            "public_stimulus":{"kind":"pulse","rate":1.7,"duration":2.0},
            "construction_observations":obs,
            "measurement_bound_status":"NO_INSTRUMENT_BOUND",
            "source_snapshot_hash":digest(obs),
            "synthetic_case":True}
        validate_case(case,protocol)
        public.append(case)
        private.append({
          "case_id":spec["id"],
          "true_world_material_class":spec["world_material_class"],
          "true_world_changed_response_times":spec["source_parameters"],
          "world_model_graph_sha256":"sha256:"+key,
          "actual_solver_csv_sha256":"sha256:"+sha256(f.read_bytes()).hexdigest(),
          "raw_true_delivered_at_construction_times":v,
          "synthetic_noise":spec["declared_noise_items"],
          "world_time_window_hours":[0,spec["world_stop_hour"]],
          "physical_G2":g2["status"],
          "material_balance_max":g2["max_material_balance_residual"],
          "case_sha256":digest(case),
          "never_an_input_to_selector":True,
          "no_reserved_world_observations":True})
    return public,private


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--catalog",type=Path,required=True)
    a=p.parse_args()
    cases,secret=extract(a.root,json.loads(a.catalog.read_text()))
    for i,case in enumerate(cases):
        outfile=a.root/f"t{i+2}-construction-only.json"
        guard(not outfile.exists(),"R3_T23_CASE_ALREADY_EXTRACTED")
        outfile.write_bytes(canonical(case)+b"\n")
    f=a.root/"researcher-private"/"provenance-sealed.json"
    guard(not f.exists(),"R3_T23_PRIVATE_GRADE_ALREADY_EXISTS")
    f.write_bytes(canonical({"schema":"igc-r3-t23-private-world-grading/0.1",
          "worlds":secret,"not_selector_input":True})+b"\n")
    print(json.dumps({"status":"R3_T2_T3_TWO_REAL_WORLDS_CONSTRUCTION_ONLY",
          "case_hashes":[digest(c) for c in cases],
          "world_G2":[x["physical_G2"] for x in secret],
          "new_candidate_simulations":0},sort_keys=True))

if __name__=="__main__":
    main()
