#!/usr/bin/env python3
"""CAF-01 M: build a dry-run native Modelica preflight, never execute simulations.

Uses existing E1 composer/backend. Changes only parameter bindings and public
pulse/horizon. Produces a manifest and checkModel-only .mos; no hidden DES.
"""
import argparse
import copy
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
E1 = ROOT / "experiments" / "e1"
sys.path.insert(0, str(E1))
import composer
import backend

CONTRACT = Path(__file__).with_name("ARENA_PC01_CAF01_CONTRATO_REVISION_v0_3_2026-10-28.json")


def checked_models(contract, registry=E1 / "registry.base.json"):
    cfg, classes, _ = composer.load_registry(registry)
    graphs = composer.enumerate_graphs(cfg, classes)
    m = contract["methods"]["M"]
    if m["structural_classes"] != ["C00", "C01", "C02"]:
        raise ValueError("UNSUPPORTED_STRUCTURE_CONTRACT")
    if contract["boundary"]["losses_allowed"] or contract["boundary"]["initial_pending"] != 0:
        raise ValueError("UNSUPPORTED_BOUNDARY")
    # Only material-path variants. Do not infer topology labels from names
    # supplied by a private DES, and do not count signal-only report filters.
    physical = [(key, graph) for key, graph in graphs if not any(
        ins["role"] in ("report", "amplifier") for ins in graph["instances"])]
    topology = {}
    for key, graph in physical:
        transit_count = sum(ins["role"] == "transit" for ins in graph["instances"])
        if transit_count in topology:
            raise ValueError("AMBIGUOUS_M_MATERIAL_TOPOLOGY")
        topology[transit_count] = (key, graph)
    if set(topology) != {0, 1, 2}:
        raise ValueError("M_MATERIAL_TOPOLOGY_MISSING")
    capacities = m["proposed_bounded_capacity_grid_items_per_hour"]
    if len(capacities) != 3 or len(set(capacities)) != 3 or any(
        type(x) is not int or x <= 0 for x in capacities
    ):
        raise ValueError("M_GRID_NOT_THREE_POSITIVE_INTEGERS")
    time_cfg = m["frozen_response_time_hours"]
    if time_cfg != {"preparation": 0.5, "dispatch": 0.5, "transit_if_present": 1.6}:
        raise ValueError("UNEXPECTED_RESPONSE_TIMES")
    items = []
    for count, label in enumerate(m["structural_classes"]):
        original_key, original = topology[count]
        for cap in capacities:
            graph = copy.deepcopy(original)
            for ins in graph["instances"]:
                role = ins["role"]
                if role in ("preparation", "dispatch"):
                    ins["parameters"] = {"maxThroughput": cap, "responseTime": time_cfg[role]}
                elif role == "transit":
                    ins["parameters"] = {"maxThroughput": 100, "responseTime": time_cfg["transit_if_present"]}
            # The same original linter and backend validate the instantiated graph.
            composer.check_graph(graph, cfg, classes)
            name = f"CAF01_{label}_C{cap}"
            model = backend.render_model(name, graph, cfg, classes)
            items.append({"name": name, "structure": label, "transit_count": count,
                          "capacity": cap, "original_graph_sha256": original_key,
                          "model": model})
    if len(items) != 9:
        raise ValueError("M_CANDIDATE_COUNT_MISMATCH")
    return items


def render_bundle(contract):
    items = checked_models(contract)
    conversion = contract["unit_conversion"]
    worlds = contract["worlds"]
    if len(worlds) != 2 or any(w["arrival"]["duration_minutes"] != 20 for w in worlds):
        raise ValueError("UNEXPECTED_PULSE_DURATION")
    if [w["stop_minutes"] for w in worlds] != [40, 40]:
        raise ValueError("UNEXPECTED_HORIZON")
    # Use the declared hour-conversion, not rounded 0.33.
    stop = conversion["forecast_horizon_hours"]
    duration = conversion["pulse_duration_hours"]
    if abs(stop - 2/3) > 1e-12 or abs(duration - 1/3) > 1e-12:
        raise ValueError("UNEXPECTED_UNIT_CONVERSION")
    expected_rates = [72, 90]
    if [w["arrival"]["rate"] * 60 for w in worlds] != expected_rates:
        raise ValueError("UNEXPECTED_RATE_CONVERSION")
    header = 'within;\npackage CAF01MPreflight\n'
    models = []
    for item in items:
        model = item["model"]
        # Existing backend's fixed synthetic probe; exact replacement guarded.
        start = '    Modelica.Blocks.Sources.Pulse pulse(amplitude=6,period=4,width=40,startTime=1);'
        end = '        if probe==3 then ramp.y else highPulse.y);'
        if model.count(start) != 1 or model.count(end) != 1:
            raise ValueError("UPSTREAM_STIMULUS_CHANGED")
        before, rest = model.split(start, 1)
        _, after = rest.split(end, 1)
        model = before + ('    parameter Real publicRate=72;\n'
                          '    Modelica.Blocks.Sources.RealExpression stimulus('
                          'y=if time < (1.0/3.0) then publicRate else 0);') + after
        if "der(" in model or "when " in model:
            raise ValueError("CUSTOM_DYNAMICS_PROHIBITED")
        models.append(model)
    package = header + "\n\n".join(models) + (
        '\n  annotation(uses(Modelica(version="4.0.0"),SystemDynamics(version="2.1.2")));\n'
        'end CAF01MPreflight;\n')
    cmds = ['getVersion();', 'loadModel(Modelica, {"4.0.0"});',
            'loadModel(SystemDynamics, {"2.1.2"});',
            'loadFile("src/modelica/IGCMolecules.mo");',
            'loadFile("src/modelica/IGCInformationMolecules.mo");',
            'loadFile("CAF01MPreflight.mo");']
    for item in items:
        cmds.append(f'checkModel(CAF01MPreflight.{item["name"]});')
    cmds.append('print(getErrorString());')
    manifest = {"status": "GENERATED_NOT_COMPILED_NOT_SIMULATED",
                "native_check_models": len(items),
                "simulation_budget_spent": 0,
                "construction_rate_items_per_hour": 72,
                "evaluation_rate_items_per_hour": 90,
                "pulse_duration_hours": "1/3",
                "horizon_hours": "2/3",
                "models": [{k: v for k, v in x.items() if k != "model"} for x in items],
                "limitations": ["G2 is not passed until native compilation and conservation checks.",
                                "No private DES, calibration, selection or evaluation used.",
                                "This output is a construction proposal; checkModel is not simulate."]}
    return package, "\n".join(cmds) + "\n", manifest


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    if args.out.exists():
        raise ValueError("OUTPUT_ALREADY_EXISTS")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    modelica, mos, manifest = render_bundle(contract)
    args.out.mkdir(parents=True)
    (args.out / "CAF01MPreflight.mo").write_text(modelica, encoding="utf-8")
    (args.out / "check_only.mos").write_text(mos, encoding="utf-8")
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "candidates": len(manifest["models"])}))


if __name__ == "__main__":
    main()
