"""R4-A T2 one authorized future OpenModelica run, EXACTLY ONE simulate().

Only use the same frozen synthetic generator Modelica from original PT06 T2.
Execute to locked t=1h; fixed 800 output intervals preserves prior dt=0.00125h.
Does not execute any candidate, change stimulus, or read future world values.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path
from scripts.arena_r3_pt06_t23_preregister import freeze,WORLD_PACKAGE,guard
from scripts.arena_r4_pt07_t2_forecast import SCHEMA
from scripts.arena_v0_contract import canonical,digest

SHA="sha256:94b1231c33f605cbca4efb81aa6a6f31883e628e4303eae9cbdbd53eb78811d8"
CERT="data/diagnostics/ARENA_R4_PT07_T2_FROZEN_FORECAST_CERTIFICATE_20261027.json"

def prepare(lock_root,output):
    lock_root,output=Path(lock_root),Path(output)
    guard(not output.exists(),"R4_ONE_WORLD_OUTPUT_ALREADY_EXISTS")
    locked=(lock_root/"forecast-lock.json").read_bytes()
    checksum="sha256:"+sha256(locked).hexdigest()
    cert=json.loads(Path(CERT).read_text())
    prior=json.loads(locked)
    guard(checksum==SHA==cert["frozen_forecast_file_sha256"] and
          (lock_root/"forecast-lock.sha256").read_text().strip()==SHA,
          "R4_FORECAST_LOCK_NOT_ORIGINAL_BYTES")
    guard(prior["schema"]==SCHEMA and
          prior["chosen_observation_time_hours"]==1.0 and
          prior["future_observation_value"] is None and
          prior["R4_complete"] is False and
          prior["compatible_candidate_count"]==27 and
          all(len(v)==9 for v in prior["compatible_by_structure"].values()),
          "R4_NOT_PREDECLARED_FORECAST")
    proto,model,_=freeze()
    guard(digest(proto)=="sha256:50cd8313a1a41cfca43391e105948c929122599b04ae70a375e255cd026b6064",
          "R4_ORIGINAL_T2_PREDECLARATION_CHANGED")
    rel=output.as_posix()
    guard(rel.startswith("artifacts/") and ".." not in output.parts,
          "R4_NOT_ISOLATED_ARTIFACT_PATH")
    steps=800
    # The source package contains T2+T3 model declarations but only the
    # T2 class has a simulate() call. The extra T3 declaration is NOT run.
    mos="\n".join([
        "getVersion();",
        'loadFile("/repo/src/modelica/IGCMolecules.mo");',
        'loadFile("/repo/src/modelica/IGCInformationMolecules.mo");',
        f'loadFile("/repo/{rel}/{WORLD_PACKAGE}-ORIGINAL.mo");',
        "print(getErrorString());",
        f"checkModel({WORLD_PACKAGE}.R3T2World);",
        "print(getErrorString());",
        f'simulate({WORLD_PACKAGE}.R3T2World,startTime=0,stopTime=1,numberOfIntervals={steps},method="dassl",tolerance=1e-8,outputFormat="csv",fileNamePrefix="{rel}/new-world/r4_t2");',
        "print(getErrorString());",""])
    guard(mos.count("simulate(")==1 and mos.count("checkModel(")==1 and
          "simulate("+WORLD_PACKAGE+".R3T2World" in mos and
          "stopTime=1,numberOfIntervals=800" in mos and
          "simulate("+WORLD_PACKAGE+".R3T3World" not in mos,
          "R4_ONE_WORLD_SOLVER_BUDGET")
    output.mkdir(parents=True)
    (output/"new-world").mkdir()
    (output/f"{WORLD_PACKAGE}-ORIGINAL.mo").write_bytes(model.encode())
    (output/"one-world.mos").write_text(mos)
    receipt={
        "schema":"igc-arena-r4-a-t2-one-physical-budget/0.1",
        "forecast_lock_sha256":SHA,
        "original_T2_world_package_sha256":"sha256:"+sha256(model.encode()).hexdigest(),
        "original_T2_protocol_sha256":digest(proto),
        "solver_program_sha256":"sha256:"+sha256(mos.encode()).hexdigest(),
        "synthetic_source":"ORIGINAL_R3_T2_WORLD_UNALTERED_E1",
        "world_class_to_run":"ArenaR3T23Worlds.R3T2World",
        "run_start_hour":0,"run_stop_hour":1,
        "original_T2_solver_step_hours":0.15/120,
        "one_world_solver_step_hours":1.0/steps,
        "original_solver":"OpenModelica_v1.26.5_DASSL",
        "world_simulate_max":1,"candidate_simulate_max":0,
        "provider_inference_max":0,"automatic_retry_max":0,
        "PT07_future_measurement_at_hour":1.0,
        "solvers_executed_at_preparation":0,
        "R4_external_independent_holdout":False,
        "user_authorized":True}
    (output/"budget.json").write_bytes(canonical(receipt)+b"\n")
    return receipt

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--lock",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(prepare(a.lock,a.out),sort_keys=True))

if __name__=="__main__":
    main()
