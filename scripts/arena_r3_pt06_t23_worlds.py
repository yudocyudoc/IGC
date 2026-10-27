"""PT-06 T2/T3 executable-in-future world-only physical budget: TWO runs max.

No provider and ZERO candidate replay simulations: all 27 candidate real CSVs
come from authentic R3-T1 Actions #40578550337. No workflow triggers these
commands without a separate one-shot authorization.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path

from scripts.arena_r3_pt06_t23_preregister import freeze,emit,CASES,WORLD_PACKAGE,guard
from scripts.arena_v0_contract import canonical,digest

SCHEMA="igc-arena-r3-t23-two-world-solver-budget/0.1"


def commands(folder):
    folder=Path(folder)
    protocol,package,_=freeze()
    guard(json.loads((folder/"protocol.json").read_text())==protocol
          and (folder/(WORLD_PACKAGE+"-NOT-SIMULATED.mo")).read_bytes()==package.encode(),
          "R3_T23_WORLD_PROTOCOL_OR_PACKAGE_CHANGED")
    rel=folder.as_posix()
    guard(rel.startswith("artifacts/") and ".." not in folder.parts,
          "R3_T23_WORLD_SIMULATION_PATH_INVALID")
    lines=["getVersion();",
           'loadFile("/repo/src/modelica/IGCMolecules.mo");',
           'loadFile("/repo/src/modelica/IGCInformationMolecules.mo");',
           f'loadFile("/repo/{rel}/{WORLD_PACKAGE}-NOT-SIMULATED.mo");',
           "print(getErrorString());"]
    for i,c in enumerate(CASES):
        name=f"{WORLD_PACKAGE}.R3T{i+2}World"
        stop=format(c["world_stop_hour"],".15g")
        outfile=f"{rel}/researcher-private/t{i+2}"
        lines.extend([f"checkModel({name});","print(getErrorString());",
          f'simulate({name},startTime=0,stopTime={stop},numberOfIntervals=120,method="dassl",tolerance=1e-8,outputFormat="csv",fileNamePrefix="{outfile}");',
          "print(getErrorString());"])
    result="\n".join(lines)+"\n"
    guard(result.count("simulate(")==2 and result.count("checkModel(")==2
          and result.count("fileNamePrefix=")==2 and
          result.count("stopTime=0.15")==1 and result.count("stopTime=3,")==1
          and not any(x in result for x in ("R3C00P","R3C01P","R3C02P")),
          "R3_T23_SOLVER_BUDGET_EXCEEDED")
    return result


def prepare(folder):
    root=Path(folder)
    protocol=emit(root)
    script=commands(root)
    (root/"two-worlds-NOT-RUN.mos").write_text(script)
    budget={
      "schema":SCHEMA,"predeclared_protocol_hash":digest(protocol),
      "source":"ORIGINAL_SHORT_E1_NO_NEW_MODEL_FAMILY",
      "world_simulations_max":2,"candidate_simulations_max":0,
      "reuse_original_27_G2_csvs":True,"original_source_run":40578550337,
      "original_source_artifact":12769310740,
      "solver_program_sha256":"sha256:"+sha256(script.encode()).hexdigest(),
      "original_M3_decider_frozen":True,
      "new_provider_calls_max":0,"automatic_retries":0,
      "new_solver_calls_now":0,"worlds_not_simulated":True,
      "future_R4_holdout":"NOT_ACCESSED",
      "authorization":"NOT_YET_REQUESTED_FOR_TWO_WORLDS"}
    (root/"world-solver-budget.json").write_bytes(canonical(budget)+b"\n")
    return budget


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    b=prepare(a.out)
    print(json.dumps({"status":"T2_T3_SOLVER_PROGRAM_PREPARED_NOT_EXECUTED",
         "world_simulation_cap":b["world_simulations_max"],
         "candidate_simulation_cap":0,"new_solver_calls":0}))

if __name__=="__main__":
    main()
