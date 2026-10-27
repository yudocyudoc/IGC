"""Offline post-only audit of the immutable real R3 T2/T3 physical evidence.

No solver, model re-fitting or provider calls. Rechecks every original
candidate's G2 with E1 and both world outputs, then independently reproduces
the precommitted R3/Frozen-M3 decisions from construction measurements.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path

from scripts.arena_r3_pt06_t23_preregister import freeze,guard
from scripts.arena_r3_pt06_t23_extract import extract
from scripts.arena_r3_pt06_t23_evaluate import archived_candidates,evaluate
from scripts.arena_r3_pt06_t23_grade import grade
from scripts.arena_v0_contract import canonical,digest

def sh(path):
    return "sha256:"+sha256(Path(path).read_bytes()).hexdigest()

def audit(root,original,catalog):
    root,original=Path(root),Path(original)
    protocol=freeze()[0]
    guard(json.loads((root/"protocol.json").read_text())==protocol,
          "T23_POSTONLY_PREDECLARATION_CHANGED")
    budget=json.loads((root/"world-solver-budget.json").read_text())
    mos=(root/"two-worlds-NOT-RUN.mos").read_text()
    guard(mos.count("simulate(")==2 and
          budget["solver_program_sha256"]=="sha256:"+sha256(mos.encode()).hexdigest()
          and budget["world_simulations_max"]==2 and
          budget["candidate_simulations_max"]==0,
          "T23_POSTONLY_SOLVER_BUDGET_CHANGED")
    original_manifest,old_rows,old_index=archived_candidates(original,protocol,catalog)
    guard(len(old_rows)==len(old_index)==27,"T23_POSTONLY_ORIGINAL_27_MISSING")
    public,private=extract(root,catalog)
    guard(len(public)==len(private)==2,"T23_POSTONLY_WORLDS_MISSING")
    prior_sealed=json.loads((root/"researcher-private/provenance-sealed.json").read_text())
    guard(private==prior_sealed["worlds"],"T23_POSTONLY_WORLD_PROVENANCE_CHANGED")
    for i,case in enumerate(public):
        file=root/f"t{i+2}-construction-only.json"
        guard(json.loads(file.read_text())==case,
              "T23_POSTONLY_PUBLIC_CONSTRUCTION_CHANGED")
        result=evaluate(protocol,case,original,catalog)
        decision_file=root/f"t{i+2}-decision.json"
        guard(json.loads(decision_file.read_text())==result,
              "T23_POSTONLY_DECISION_NOT_REPRODUCIBLE")
    reconstructed=grade(root)
    actual=json.loads((root/"post-selection-adjudication.json").read_text())
    guard(actual==reconstructed,"T23_POSTONLY_GRADING_CHANGED")
    return {"schema":"igc-arena-r3-pt06-t23-postonly-original-audit/0.1",
            "protocol_sha256":digest(protocol),
            "physical_source_run_id":40582633807,
            "original_candidate_source_run_id":40578550337,
            "world_simulate_calls_in_original_program":2,
            "worlds_G2_validated":2,
            "candidate_CSVs_G2_validated":len(old_rows),
            "new_solver_calls":0,"new_provider_calls":0,
            "R4_holdout_accessed":False,
            "cases":reconstructed["cases"],
            "original_decision_hashes":{
                f"T{i+2}":sh(root/f"t{i+2}-decision.json") for i in range(2)},
            "world_CSV_hashes":{
                f"T{i+2}":sh(root/"researcher-private"/f"t{i+2}_res.csv")
                for i in range(2)},
            "original_candidates_hashes":{x["id"]:x["sha256"] for x in old_index},
            "status":"POSTONLY_TWO_PREDECLARED_OUTCOMES_REPRODUCED"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True,type=Path)
    p.add_argument("--original-t1",required=True,type=Path)
    p.add_argument("--catalog",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    guard(not a.out.exists(),"T23_POSTONLY_ALREADY_AUDITED")
    r=audit(a.root,a.original_t1,json.loads(a.catalog.read_text()))
    a.out.write_bytes(canonical(r)+b"\n")
    for c in r["cases"]:
        print(json.dumps({"case_id":c["case_id"],
          "status":c["R3_grid_decision"],
          "compatible":c["R3_compatible_structures"],
          "fixed_M3":c["original_M3_status"],
          "minimum_RMSE":{k:v["rmse_items"] for k,v in c["R3_per_structure_best"].items()},
          "measurements":c["observations"],
          "world_balance":c["world_max_material_balance_residual"]},sort_keys=True))
    print(r["status"])

if __name__=="__main__":
    main()
