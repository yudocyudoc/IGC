"""Compose and render serial-chain candidates from LinkML molecule definitions."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_fm_a_contract import (  # noqa: E402
    ContractError,
    canonical_structure_hash,
    validate_linkml_objects,
    validate_references,
)

MODEL_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def require_port(definition: dict[str, Any], name: str, direction: str,
                 signal_kind: str | None = None) -> dict[str, Any]:
    matches = [port for port in definition["ports"] if port["name"] == name]
    if len(matches) != 1:
        raise ContractError("COMPOSITION_PORT_MISSING", f"{definition['id']}.{name}")
    port = matches[0]
    if port["direction"] != direction or (signal_kind and port["signal_kind"] != signal_kind):
        raise ContractError("COMPOSITION_PORT_INCOMPATIBLE", f"{definition['id']}.{name}")
    return port


def validate_modelica_symbols(plan: dict[str, Any], document: dict[str, Any]) -> None:
    class_names = [
        "Composed_" + modelica_identifier(candidate["id"].rsplit(":", 1)[-1])
        for candidate in document["candidates"]
    ]
    if len(set(class_names)) != len(class_names):
        raise ContractError(
            "COMPOSITION_MODELICA_IDENTIFIER_COLLISION",
            "candidate ids normalize to the same Modelica class",
        )
    for candidate, class_name in zip(document["candidates"], class_names):
        if not MODEL_IDENTIFIER.fullmatch(class_name):
            raise ContractError("COMPOSITION_MODELICA_IDENTIFIER_INVALID", candidate["id"])

    for structure in document["structures"]:
        for instance in structure["molecule_instances"]:
            if not MODEL_IDENTIFIER.fullmatch(instance["id"]):
                raise ContractError("COMPOSITION_MODELICA_IDENTIFIER_INVALID", instance["id"])
            definition = next(item for item in document["molecule_definitions"]
                              if item["id"] == instance["molecule_definition_id"])
            modelica_class = definition.get("modelica_class", "")
            if not modelica_class or not all(
                MODEL_IDENTIFIER.fullmatch(part) for part in modelica_class.split(".")
            ):
                raise ContractError("COMPOSITION_MODELICA_CLASS_INVALID", modelica_class)
            for binding in instance["parameter_bindings"]:
                if not MODEL_IDENTIFIER.fullmatch(binding["parameter_id"]):
                    raise ContractError("COMPOSITION_MODELICA_IDENTIFIER_INVALID", binding["parameter_id"])
    output_name = plan["observable"]["output_name"]
    if not MODEL_IDENTIFIER.fullmatch(output_name):
        raise ContractError("COMPOSITION_MODELICA_IDENTIFIER_INVALID", output_name)


def binding_values(definition: dict[str, Any], requested: dict[str, Any]) -> list[dict[str, Any]]:
    specs = {spec["parameter_id"]: spec for spec in definition["parameters"]}
    if set(requested) != set(specs):
        raise ContractError("COMPOSITION_PARAMETER_SET", definition["id"])
    result = []
    for parameter_id, supplied in sorted(requested.items()):
        spec = specs[parameter_id]
        value = supplied.get("value")
        if not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ContractError("COMPOSITION_PARAMETER_INVALID", parameter_id)
        if supplied.get("unit") != spec["unit"]:
            raise ContractError("COMPOSITION_PARAMETER_UNIT", parameter_id)
        if "minimum" in spec and value < spec["minimum"]:
            raise ContractError("COMPOSITION_PARAMETER_BOUNDS", parameter_id)
        if "maximum" in spec and value > spec["maximum"]:
            raise ContractError("COMPOSITION_PARAMETER_BOUNDS", parameter_id)
        result.append({"parameter_id": parameter_id, "value": value, "unit": spec["unit"]})
    return result


def compose(plan: dict[str, Any], catalog: dict[str, Any]) -> dict[str, Any]:
    if plan.get("composition_rule") != "serial_chain":
        raise ContractError("COMPOSITION_RULE_UNSUPPORTED", str(plan.get("composition_rule")))
    if plan.get("request_id") != catalog["request"]["id"]:
        raise ContractError("COMPOSITION_REQUEST_MISMATCH", str(plan.get("request_id")))
    definitions = {item["id"]: item for item in catalog["molecule_definitions"]}
    try:
        source_def = definitions[plan["roles"]["source"]]
        stage_def = definitions[plan["roles"]["stage"]]
        sink_def = definitions[plan["roles"]["sink"]]
    except KeyError as exc:
        raise ContractError("COMPOSITION_MOLECULE_MISSING", str(exc)) from exc
    require_port(source_def, "outflow", "out", "FLOW")
    require_port(source_def, "externalRate", "in", "SIGNAL")
    require_port(stage_def, "arrival", "in", "FLOW")
    require_port(stage_def, "completed", "out", "FLOW")
    require_port(sink_def, "arrival", "in", "FLOW")
    observable = plan["observable"]
    ext = plan["external_input"]
    input_instance, input_port = ext["target_port"].rsplit(".", 1)
    if input_instance != plan["instances"]["source"]:
        raise ContractError("COMPOSITION_INPUT_INSTANCE", ext["target_port"])
    require_port(source_def, input_port, "in", "SIGNAL")
    input_definition = next(p for p in source_def["ports"] if p["name"] == input_port)
    if ext["unit"] != input_definition["unit"]:
        raise ContractError("COMPOSITION_INPUT_UNIT", ext["target_port"])
    if not isinstance(ext["value"], (int, float)) or not math.isfinite(ext["value"]):
        raise ContractError("COMPOSITION_INPUT_INVALID", ext["target_port"])
    sink_id, observable_port = observable["port"].rsplit(".", 1)
    if sink_id != plan["instances"]["sink"]:
        raise ContractError("COMPOSITION_OBSERVABLE_INSTANCE", observable["port"])
    require_port(sink_def, observable_port, "out", "STATE")

    structures: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    model_defs = {"source": source_def, "stage": stage_def, "sink": sink_def}
    for spec in plan["candidates"]:
        count = spec["stage_count"]
        if not isinstance(count, int) or count < 1:
            raise ContractError("COMPOSITION_STAGE_COUNT", str(count))
        source_id = plan["instances"]["source"]
        sink_id = plan["instances"]["sink"]
        stages = [f"{plan['instances']['stage_prefix']}{i}" for i in range(count)]
        instances = [
            {"id": source_id, "molecule_definition_id": source_def["id"], "parameter_bindings": []}
        ]
        stage_bindings = binding_values(stage_def, plan["parameter_bindings"])
        instances.extend({"id": stage_id, "molecule_definition_id": stage_def["id"],
                          "parameter_bindings": stage_bindings} for stage_id in stages)
        instances.append({"id": sink_id, "molecule_definition_id": sink_def["id"], "parameter_bindings": []})
        flow_nodes = [(source_id, "outflow")] + [(stage, "completed") for stage in stages]
        flow_targets = [(stage, "arrival") for stage in stages] + [(sink_id, "arrival")]
        connections = [{"id": f"c{index}", "from_port": f"{src}.{src_port}",
                        "to_port": f"{dst}.{dst_port}", "connection_kind": "MATERIAL_FLOW"}
                       for index, ((src, src_port), (dst, dst_port))
                       in enumerate(zip(flow_nodes, flow_targets), start=1)]
        structure = {
            "id": spec["structure_id"],
            "catalog_snapshot": ";".join(sorted({f"{d['id']}@{d['source_commit']}" for d in model_defs.values()})),
            "molecule_instances": instances,
            "connections": connections,
            "structural_hash": "",
        }
        structure["structural_hash"] = canonical_structure_hash(structure)
        structures.append(structure)
        candidates.append({
            "id": spec["id"], "request_id": plan["request_id"],
            "structure_revision_id": spec["structure_id"],
            "status": "HYPOTHESIS_SYNTHETIC_NOT_EMPIRICALLY_SUPPORTED",
            "assumption_refs": [], "origin_refs": [plan["id"]],
        })
    document = {"synthetic": True, "request": catalog["request"],
                "molecule_definitions": catalog["molecule_definitions"],
                "candidates": candidates, "structures": structures}
    validate_references(document)
    validate_modelica_symbols(plan, document)
    return document


def modelica_identifier(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_]", "_", value)
    if not value or value[0].isdigit():
        value = "C_" + value
    return value


def render_modelica(plan: dict[str, Any], document: dict[str, Any]) -> str:
    definitions = {item["id"]: item for item in document["molecule_definitions"]}
    lines = ["within;", "package GeneratedMolecularCandidates"]
    for candidate, structure in zip(document["candidates"], document["structures"]):
        class_name = "Composed_" + modelica_identifier(candidate["id"].rsplit(":", 1)[-1])
        instance_defs = {item["id"]: definitions[item["molecule_definition_id"]]
                         for item in structure["molecule_instances"]}
        model_lines = [f"  model {class_name}",
                 f"    Modelica.Blocks.Sources.Constant inputDriver(k={float(plan['external_input']['value']):.17g});"]
        for instance in structure["molecule_instances"]:
            bindings = {item["parameter_id"]: item["value"] for item in instance["parameter_bindings"]}
            args = ", ".join(f"{key}={float(value):.17g}" for key, value in sorted(bindings.items()))
            suffix = f"({args})" if args else ""
            model_lines.append(f"    {instance_defs[instance['id']]['modelica_class']} {instance['id']}{suffix};")
        model_lines.append(f"    output Real {plan['observable']['output_name']};")
        model_lines.append("  equation")
        model_lines.append(f"    connect(inputDriver.y, {plan['external_input']['target_port']});")
        for connection in structure["connections"]:
            model_lines.append(f"    connect({connection['from_port']}, {connection['to_port']});")
        model_lines.append(f"    {plan['observable']['output_name']} = {plan['observable']['port']};")
        model_lines.extend([f"  end {class_name};", ""])
        lines.extend(model_lines)
    return "\n".join(lines + ["end GeneratedMolecularCandidates;", ""])


def result_prefix(candidate_id: str) -> str:
    return "composed-" + modelica_identifier(candidate_id.rsplit(":", 1)[-1]).lower()


def render_openmodelica_script(plan: dict[str, Any], document: dict[str, Any]) -> str:
    lines = [
        'setModelicaPath("/opt/modelica:/opt/systemdynamics");',
        'loadFile("/opt/systemdynamics/SystemDynamics/package.mo");',
        'loadFile("/evidence/IGCMolecules.mo");',
        'loadFile("/evidence/IGCInformationMolecules.mo");',
        'loadFile("/results/GeneratedMolecularCandidates.mo");',
        "print(getErrorString());",
    ]
    classes = sorted({
        definition["modelica_class"]
        for definition in document["molecule_definitions"]
        if any(instance["molecule_definition_id"] == definition["id"]
               for structure in document["structures"]
               for instance in structure["molecule_instances"])
    })
    classes.extend("GeneratedMolecularCandidates.Composed_" +
                   modelica_identifier(candidate["id"].rsplit(":", 1)[-1])
                   for candidate in document["candidates"])
    for class_name in classes:
        lines.extend([f"checkModel({class_name});", "print(getErrorString());"])
    sim = plan["simulation"]
    for candidate in document["candidates"]:
        class_name = "GeneratedMolecularCandidates.Composed_" + modelica_identifier(
            candidate["id"].rsplit(":", 1)[-1]
        )
        lines.extend([
            f"simulate({class_name}, startTime={float(sim['start_time']):.17g}, "
            f"stopTime={float(sim['stop_time']):.17g}, numberOfIntervals={int(sim['intervals'])}, "
            f'outputFormat="csv", fileNamePrefix="{result_prefix(candidate["id"])}");',
            "print(getErrorString());",
        ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, default=ROOT / "data/synthetic/fm_b_serial_chain_plan.json")
    parser.add_argument("--catalog", type=Path, default=ROOT / "data/synthetic/fm_a_structural_candidates.json")
    parser.add_argument("--schema-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts/fm-b-molecular-composer")
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    document = compose(plan, catalog)
    validate_linkml_objects(document, args.schema_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    candidate_path = args.output_dir / "composed_candidates.json"
    modelica_path = args.output_dir / "GeneratedMolecularCandidates.mo"
    mos_path = args.output_dir / "run-composed-models.mos"
    candidate_path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    modelica_path.write_text(render_modelica(plan, document), encoding="utf-8")
    mos_path.write_text(render_openmodelica_script(plan, document), encoding="utf-8")
    report = {
        "status": "B1_COMPOSITION_READY_FOR_EXECUTION",
        "plan_id": plan["id"], "plan_sha256": digest(args.plan),
        "catalog_sha256": digest(args.catalog),
        "generator_sha256": digest(Path(__file__)),
        "composed_candidates_sha256": digest(candidate_path),
        "generated_modelica_sha256": digest(modelica_path),
        "generated_openmodelica_script_sha256": digest(mos_path),
        "candidate_ids": [item["id"] for item in document["candidates"]],
        "generated_models": [
            "GeneratedMolecularCandidates.Composed_"
            + modelica_identifier(item["id"].rsplit(":", 1)[-1])
            for item in document["candidates"]
        ],
        "result_prefixes": [result_prefix(item["id"]) for item in document["candidates"]],
        "stage_counts": [sum(item["molecule_definition_id"] == plan["roles"]["stage"]
                              for item in structure["molecule_instances"])
                         for structure in document["structures"]],
        "structural_hashes": [item["structural_hash"] for item in document["structures"]],
        "synthetic": True, "empirical_or_causal_claim": False,
        "license_status": "DEFERRED_BY_RESEARCHER",
    }
    if len(set(report["structural_hashes"])) != len(report["structural_hashes"]):
        raise ContractError("COMPOSITION_TOPOLOGY_NOT_DISTINCT", "structural hashes must differ")
    (args.output_dir / "composition-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
