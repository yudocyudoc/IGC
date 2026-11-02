#!/usr/bin/env python3
"""CAF-01 D: derive THREE loss-free models from the unchanged D grammar.

Preparation ONLY: no RK4 integration, no Modelica simulation, no DES, no
Buffalo. The output .mos invokes checkModel, never simulate or buildModel.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scripts.arena_d_v01 import lint_structure, modelica, topology
from scripts.arena_v0_contract import digest

CONTRACT = Path(__file__).with_name(
    "ARENA_PC01_CAF01_CONTRATO_REVISION_v0_3_2026-10-28.json"
)


def generate(contract):
    d = contract["methods"]["D"]
    units = contract["unit_conversion"]
    boundary = contract["boundary"]
    if (d["max_topologies"] != 3 or d["topology_stock_counts"] != [1, 2, 3]
            or d["loss_variants"] != [False] or boundary["losses_allowed"] is not False):
        raise ValueError("D_BOUNDARY_OR_TOPOLOGY_CHANGED")
    grid = d["parameter_grid"]
    if (grid != {"capacity_items_per_hour": [48, 72, 96],
                 "response_time_hours": [0.125, 0.25],
                 "loss_time_hours": [1.0]}
            or d["construction_RK4_max"] != 18 or d["CAF_N_RK4_max"] != 18
            or d["construction_OpenModelica_max"] != 3
            or d["evaluation_OpenModelica_max"] != 3):
        raise ValueError("D_PARAMETER_OR_BUDGET_CHANGED")
    if (units["arrival_construction_rate_items_per_hour"] != 72
            or units["arrival_evaluation_rate_items_per_hour"] != 90
            or abs(units["pulse_duration_hours"] - 1/3) > 1e-14
            or abs(units["forecast_horizon_hours"] - 2/3) > 1e-14):
        raise ValueError("D_UNITS_OR_PULSE_CHANGED")
    sample_times = units["observation_times_hours"]
    if len(sample_times) != 7 or any(
        abs(x-y) > 1e-12 for x,y in zip(sample_times, (0, 1/12, 1/6, 1/4, 1/3, 1/2, 2/3))
    ):
        raise ValueError("D_SAMPLE_TIMES_CHANGED")
    proposal = {"capacity": 72, "response_time": 0.25, "loss_time": 1.0}
    if d["nominal_example_unfitted"] != proposal:
        raise ValueError("D_NOMINAL_ASSUMPTIONS_CHANGED")
    items = []
    for stocks in d["topology_stock_counts"]:
        structure = topology(stocks, False)
        lint_structure(structure)
        structure_hash = digest(structure)
        candidate = {"structure": structure, "structure_hash": structure_hash,
                     "nominal_parameters": proposal.copy()}
        src = modelica(candidate, {"kind": "pulse", "rate": 72, "duration": 1/3})
        original_name = "DStockFlow_" + structure_hash[7:19]
        name = f"DCAF_{stocks}"
        if (src.count("model " + original_name + "\n") != 1
                or src.count("end " + original_name + ";") != 1):
            raise ValueError("D_NATIVE_RENDER_TEMPLATE_CHANGED")
        src = src.replace("model " + original_name + "\n", "model " + name + "\n")
        src = src.replace("end " + original_name + ";", "end " + name + ";")
        # The original renderer uses 12 significant digits. Preserve the
        # *exact expression* for the public pulse boundary, not a rounded 0.33.
        rendered_duration = f"{1/3:.12g}"
        marker = f"parameter Real pulseDuration = {rendered_duration};"
        if src.count(marker) != 1:
            raise ValueError("D_PULSE_RENDER_TEMPLATE_CHANGED")
        src = src.replace(marker, "parameter Real pulseDuration = (1.0/3.0);")
        if "lossRate = 0;" not in src or "der(lost) = lossRate;" not in src:
            raise ValueError("D_LOSS_FREE_EQUATIONS_CHANGED")
        items.append({"model": name, "stocks": stocks, "loss": False,
                      "source_structure_hash": structure_hash, "source": src})
    if len(items) != 3:
        raise ValueError("D_THREE_MODELS_REQUIRED")
    manifest = {
        "status": "D_NATIVE_CHECK_PREPARATION_ONLY",
        "input_policy": "PUBLIC_CONSTRUCTION_PULSE_ONLY",
        "model_count": 3,
        "native_check_model_calls": 3,
        "RK4_construction_budget": 18,
        "RK4_CAF_N_budget": 18,
        "RK4_executed": 0,
        "modelica_simulations_executed": 0,
        "horizon_hours": "2/3",
        "pulse_duration_hours": "1/3",
        "nominal_parameters_unfitted": proposal,
        "models": [{k:v for k,v in item.items() if k != "source"} for item in items],
        "limitations": [
            "checkModel validates equation balance but not numerical trajectories or conservation",
            "D modelica generator, topology grammar and source equations are unchanged",
            "No D grid was fitted to observations; no construction/evaluation world generated",
            "18 + 18 RK4 integrations and 3 + 3 OMC runs are ceilings, not spent",
        ]
    }
    return items, manifest


def check_script(items, output_dir):
    output_dir = Path(output_dir).resolve()
    statements = ['getVersion();']
    for item in items:
        path = output_dir / (item["model"] + ".mo")
        if not path.is_file():
            raise ValueError("D_MODELICA_SOURCE_MISSING:" + str(path))
        resolved = path.as_posix()
        if '"' in resolved or "\n" in resolved or "\r" in resolved:
            raise ValueError("D_MODELICA_UNSAFE_PATH")
        statements += [
            f'loadFile("{resolved}");',
            f'checkModel({item["model"]});',
        ]
    statements.append('print(getErrorString());')
    return "\n".join(statements) + "\n"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    if args.out.exists():
        raise ValueError("OUTPUT_ALREADY_EXISTS")
    items, manifest = generate(json.loads(CONTRACT.read_text(encoding="utf-8")))
    args.out.mkdir(parents=True)
    for item in items:
        (args.out / (item["model"] + ".mo")).write_text(item["source"], encoding="utf-8")
    (args.out / "check_only.mos").write_text(check_script(items, args.out), encoding="utf-8")
    (args.out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "models": 3, "solver_runs": 0}))


if __name__ == "__main__":
    main()
