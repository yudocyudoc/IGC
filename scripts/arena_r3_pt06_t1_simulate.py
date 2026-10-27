"""R3 PT-06 STR-02: execute the 28 *authorized* E1 simulations, no AI.

27 prospective candidate structures/parameters + ONE separate synthetic world.
The world never simulates reserved t=4..6 and the selector reads ONLY the
four public construction observations extracted in a separate process.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from scripts.arena_r3_pt06_parametric import (
    PACKAGE, CASE_PLAN, guard, plan, write_plan, generate_first_case_world_modelica)
from scripts.arena_v0_contract import canonical, digest

SCHEMA="igc-arena-r3-pt06-t1-28-solver-budget/0.1"


def commands(folder):
    """Generate a single, accountable OMC script with exactly 28 simulate calls."""
    folder=Path(folder)
    manifest=json.loads((folder/"manifest.json").read_text())
    expected,package=plan()
    guard(manifest==expected and
          (folder/(PACKAGE+".mo")).read_bytes()==package.encode() and
          (folder/"ArenaR3WorldT1-NOT-SIMULATED.mo").read_bytes()==
          generate_first_case_world_modelica().encode(),
          "R3_ORIGINAL_PREFLIGHT_BYTES_CHANGED")
    guard(len(manifest["candidates"])==27 and
          manifest["search"]["max_candidate_evaluations"]==27,
          "R3_SOLVER_BUDGET_NOT_27")
    relative=folder.as_posix()
    guard(relative.startswith("artifacts/") and ".." not in folder.parts,
          "R3_RUN_PATH_NOT_LOCAL_ARTIFACTS")
    lines=[
      "getVersion();",
      'loadFile("/repo/src/modelica/IGCMolecules.mo");',
      'loadFile("/repo/src/modelica/IGCInformationMolecules.mo");',
      f'loadFile("/repo/{relative}/{PACKAGE}.mo");',
      f'loadFile("/repo/{relative}/ArenaR3WorldT1-NOT-SIMULATED.mo");',
      "print(getErrorString());"
    ]
    for c in manifest["candidates"]:
        name=f'{PACKAGE}.{c["class_name"]}'
        ident=c["id"].lower()
        prefix=f'{relative}/candidates/{ident}'
        lines.extend([
          f'checkModel({name});',
          "print(getErrorString());",
          f'simulate({name},startTime=0,stopTime=6,numberOfIntervals=120,method="dassl",tolerance=1e-8,outputFormat="csv",fileNamePrefix="{prefix}");',
          "print(getErrorString());"
        ])
    world_name="ArenaR3World.R3WorldT1"
    lines.extend([
      f'checkModel({world_name});',
      "print(getErrorString());",
      # Deliberately stop at t=3; NO t=4,5,6 holdout of generating world.
      f'simulate({world_name},startTime=0,stopTime=3,numberOfIntervals=120,method="dassl",tolerance=1e-8,outputFormat="csv",fileNamePrefix="{relative}/world-private/t1");',
      "print(getErrorString());"
    ])
    output="\n".join(lines)+"\n"
    guard(output.count("simulate(")==28 and
          output.count("checkModel(")==28 and
          output.count('fileNamePrefix=')==28 and
          output.count("R3WorldT1},")==0 and
          "startTime=0,stopTime=3,numberOfIntervals=120" in output and
          'stopTime=6,numberOfIntervals=120' in output,
          "R3_28_SIMULATIONS_ACCOUNTING_FAILURE")
    return output


def emit(folder):
    folder=Path(folder)
    write_plan(folder)
    (folder/"candidates").mkdir()
    (folder/"world-private").mkdir()
    command=commands(folder)
    (folder/"simulate.mos").write_text(command)
    receipt={
      "schema":SCHEMA,"case_id":CASE_PLAN["case_id"],
      "source_modelica_sha256":digest(plan()[0]),
      "commands_sha256":"sha256:"+sha256(command.encode()).hexdigest(),
      "authorized_candidate_simulations":27,
      "authorized_world_simulations":1,
      "total_simulation_commands":command.count("simulate("),
      "method":"ORIGINAL_E1_MODELICA_DASSL",
      "candidate_time_window_hours":[0,6],
      "world_time_window_hours":[0,3],
      "world_reserved_times_generated":False,
      "input_profile_unchanged":True,
      "case_blueprint_not_selector_input":True,
      "provider_calls":0,"solver_calls_before_workflow":0,
      "frozen_m3_baseline":"ORIGINAL_M3_DECIDE_NOT_MODIFIED",
      "no_data_or_hypotheses_from_D_B":True,
      "no_new_topology":True,
      "future_R4_holdout":"NOT_ACCESSED"
    }
    (folder/"solver-budget.json").write_bytes(canonical(receipt)+b"\n")
    return receipt


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    x=emit(a.out)
    print(json.dumps({"status":"R3_T1_28_SIMULATION_COMMANDS_PREPARED",
                      "authorized":x["total_simulation_commands"],
                      "solver_calls_at_generation":0}))


if __name__=="__main__":
    main()
