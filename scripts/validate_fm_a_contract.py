"""Validate synthetic FM-A molecular contracts and their typed references."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema.validators import validator_for


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = ROOT / "data/synthetic/fm_a_structural_candidates.json"
DEFAULT_PROPOSALS = ROOT / "data/synthetic/f3_candidate_proposals.json"
DEFAULT_BASE_CANDIDATE = ROOT / "data/synthetic/system_model_candidate.json"
PORT_DIRECTIONS = {"in", "out"}
SIGNAL_KINDS = {"FLOW", "SIGNAL", "STATE"}
CONNECTION_KINDS = {"MATERIAL_FLOW", "INFORMATION_SIGNAL", "CONTROL_SIGNAL"}
CONNECTION_SIGNAL_COMPATIBILITY = {
    "MATERIAL_FLOW": {"FLOW"},
    "INFORMATION_SIGNAL": {"SIGNAL", "STATE"},
    "CONTROL_SIGNAL": {"SIGNAL"},
}


class ContractError(ValueError):
    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code


def canonical_structure_hash(structure: dict[str, Any]) -> str:
    canonical = {
        "catalog_snapshot": structure["catalog_snapshot"],
        "molecule_instances": sorted(
            ({"id": item["id"], "molecule_definition_id": item["molecule_definition_id"]}
             for item in structure["molecule_instances"]),
            key=lambda item: item["id"],
        ),
        "connections": sorted(
            ({"from_port": item["from_port"], "to_port": item["to_port"],
              "connection_kind": item["connection_kind"]}
             for item in structure["connections"]),
            key=lambda item: (item["from_port"], item["to_port"], item["connection_kind"]),
        ),
    }
    serialized = json.dumps(
        canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(serialized).hexdigest()


def validate_references(document: dict[str, Any]) -> None:
    definitions = {item["id"]: item for item in document["molecule_definitions"]}
    structures = {item["id"]: item for item in document["structures"]}
    if len(definitions) != len(document["molecule_definitions"]):
        raise ContractError("DUPLICATE_MOLECULE", "molecule definition ids must be unique")
    if len(structures) != len(document["structures"]):
        raise ContractError("DUPLICATE_STRUCTURE", "structure revision ids must be unique")
    candidate_ids = [item["id"] for item in document["candidates"]]
    if len(set(candidate_ids)) != len(candidate_ids):
        raise ContractError("DUPLICATE_CANDIDATE", "candidate ids must be unique")

    for candidate in document["candidates"]:
        if candidate["request_id"] != document["request"]["id"]:
            raise ContractError("UNKNOWN_REQUEST", candidate["request_id"])
        if candidate["structure_revision_id"] not in structures:
            raise ContractError("UNKNOWN_STRUCTURE", candidate["structure_revision_id"])

    for structure in document["structures"]:
        instances = {item["id"]: item for item in structure["molecule_instances"]}
        if len(instances) != len(structure["molecule_instances"]):
            raise ContractError("DUPLICATE_INSTANCE", structure["id"])
        ports_by_instance: dict[str, dict[str, dict[str, Any]]] = {}
        for instance_id, instance in instances.items():
            definition = definitions.get(instance["molecule_definition_id"])
            if definition is None:
                raise ContractError("UNKNOWN_MOLECULE", instance["molecule_definition_id"])
            ports = {port["name"]: port for port in definition["ports"]}
            if len(ports) != len(definition["ports"]):
                raise ContractError("DUPLICATE_PORT", definition["id"])
            ports_by_instance[instance_id] = ports
            for port in definition["ports"]:
                if port["direction"] not in PORT_DIRECTIONS:
                    raise ContractError("UNKNOWN_DIRECTION", port["direction"])
                if port["signal_kind"] not in SIGNAL_KINDS:
                    raise ContractError("UNKNOWN_SIGNAL_KIND", port["signal_kind"])

        used_flow_outputs: set[str] = set()
        used_inputs: set[str] = set()
        connection_ids = [item["id"] for item in structure["connections"]]
        if len(set(connection_ids)) != len(connection_ids):
            raise ContractError("DUPLICATE_CONNECTION", structure["id"])
        for connection in structure["connections"]:
            if connection["connection_kind"] not in CONNECTION_KINDS:
                raise ContractError("UNKNOWN_CONNECTION_KIND", connection["connection_kind"])
            try:
                from_instance, from_name = connection["from_port"].rsplit(".", 1)
                to_instance, to_name = connection["to_port"].rsplit(".", 1)
                source = ports_by_instance[from_instance][from_name]
                target = ports_by_instance[to_instance][to_name]
            except (KeyError, ValueError) as exc:
                raise ContractError("UNKNOWN_PORT", connection["id"]) from exc
            if source["direction"] != "out" or target["direction"] != "in":
                raise ContractError("PORT_DIRECTION_MISMATCH", connection["id"])
            if (source["signal_kind"] != target["signal_kind"]
                    or source["semantic_type"] != target["semantic_type"]):
                raise ContractError("PORT_TYPE_MISMATCH", connection["id"])
            if source["unit"] != target["unit"]:
                raise ContractError("UNIT_MISMATCH", connection["id"])
            if source["signal_kind"] not in CONNECTION_SIGNAL_COMPATIBILITY[connection["connection_kind"]]:
                raise ContractError(
                    "CONNECTION_SIGNAL_MISMATCH",
                    f"{connection['id']}: {connection['connection_kind']} cannot carry {source['signal_kind']}",
                )
            if connection["to_port"] in used_inputs:
                raise ContractError("MULTIPLE_INCOMING", connection["to_port"])
            used_inputs.add(connection["to_port"])
            if source["signal_kind"] == "FLOW":
                if connection["from_port"] in used_flow_outputs:
                    raise ContractError("MATERIAL_FLOW_MULTICAST", connection["from_port"])
                used_flow_outputs.add(connection["from_port"])

        actual_hash = canonical_structure_hash(structure)
        if structure["structural_hash"] != actual_hash:
            raise ContractError("STRUCTURAL_HASH_MISMATCH", structure["id"])


def validate_linkml_objects(document: dict[str, Any], schema_dir: Path) -> None:
    objects: dict[str, list[dict[str, Any]]] = {
        "ConceptualModelRequest": [document["request"]],
        "MoleculeDefinition": document["molecule_definitions"],
        "SystemModelCandidate": document["candidates"],
        "SystemStructureRevision": document["structures"],
    }
    for top_class, values in objects.items():
        schema_path = schema_dir / f"{top_class}.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        validator_class = validator_for(schema)
        validator_class.check_schema(schema)
        validator = validator_class(schema)
        for index, value in enumerate(values):
            errors = sorted(validator.iter_errors(value), key=lambda error: list(error.path))
            if errors:
                first = errors[0]
                location = ".".join(str(part) for part in first.path) or top_class
                raise ContractError("LINKML_SCHEMA_INVALID", f"{location}: {first.message}")


def check_negative_cases(document: dict[str, Any], schema_dir: Path) -> None:
    def expect_schema_rejection(invalid: dict[str, Any], label: str) -> None:
        try:
            validate_linkml_objects(invalid, schema_dir)
        except ContractError as exc:
            if exc.code != "LINKML_SCHEMA_INVALID":
                raise
        else:
            raise ContractError("NEGATIVE_CASE_ACCEPTED", label)

    invalid = copy.deepcopy(document)
    invalid["structures"][0]["molecule_instances"][1]["molecule_definition_id"] = "urn:igc:molecule:missing"
    try:
        validate_references(invalid)
    except ContractError as exc:
        if exc.code != "UNKNOWN_MOLECULE":
            raise
    else:
        raise ContractError("NEGATIVE_CASE_ACCEPTED", "unknown molecule reference")

    for path, value, label in [
        (("molecule_definitions", 0, "ports", 0, "direction"), "sideways", "unknown port direction"),
        (("molecule_definitions", 0, "ports", 0, "signal_kind"), "UNKNOWN_SIGNAL", "unknown signal kind"),
        (("structures", 0, "connections", 0, "connection_kind"), "UNKNOWN_LINK", "unknown connection kind"),
    ]:
        invalid = copy.deepcopy(document)
        target: Any = invalid
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
        expect_schema_rejection(invalid, label)
        try:
            validate_references(invalid)
        except ContractError as exc:
            expected = {
                "unknown port direction": "UNKNOWN_DIRECTION",
                "unknown signal kind": "UNKNOWN_SIGNAL_KIND",
                "unknown connection kind": "UNKNOWN_CONNECTION_KIND",
            }[label]
            if exc.code != expected:
                raise
        else:
            raise ContractError("NEGATIVE_CASE_ACCEPTED", label)

    for connection_kind in ("INFORMATION_SIGNAL", "CONTROL_SIGNAL"):
        invalid = copy.deepcopy(document)
        invalid["structures"][0]["connections"][0]["connection_kind"] = connection_kind
        try:
            validate_references(invalid)
        except ContractError as exc:
            if exc.code != "CONNECTION_SIGNAL_MISMATCH":
                raise
        else:
            raise ContractError(
                "NEGATIVE_CASE_ACCEPTED",
                f"{connection_kind} cannot carry FLOW",
            )

    invalid = copy.deepcopy(document)
    invalid["candidates"].append(copy.deepcopy(invalid["candidates"][0]))
    try:
        validate_references(invalid)
    except ContractError as exc:
        if exc.code != "DUPLICATE_CANDIDATE":
            raise
    else:
        raise ContractError("NEGATIVE_CASE_ACCEPTED", "duplicated candidate id")

    invalid = copy.deepcopy(document)
    connections = invalid["structures"][0]["connections"]
    connections.append(copy.deepcopy(connections[0]))
    try:
        validate_references(invalid)
    except ContractError as exc:
        if exc.code != "DUPLICATE_CONNECTION":
            raise
    else:
        raise ContractError("NEGATIVE_CASE_ACCEPTED", "duplicated connection id")

    invalid = copy.deepcopy(document)
    invalid["structures"][0]["connections"][0]["from_port"] = "source0.missing"
    try:
        validate_references(invalid)
    except ContractError as exc:
        if exc.code != "UNKNOWN_PORT":
            raise
    else:
        raise ContractError("NEGATIVE_CASE_ACCEPTED", "unknown port reference")

    invalid = copy.deepcopy(document)
    queue = next(item for item in invalid["molecule_definitions"]
                 if item["id"] == "urn:igc:molecule:bounded-queue@0.1")
    next(port for port in queue["ports"] if port["name"] == "arrival")["unit"] = "packages/hour"
    try:
        validate_references(invalid)
    except ContractError as exc:
        if exc.code != "UNIT_MISMATCH":
            raise
    else:
        raise ContractError("NEGATIVE_CASE_ACCEPTED", "incompatible port unit")

    invalid = copy.deepcopy(document)
    invalid["structures"][0]["molecule_instances"].append({
        "id": "branch0",
        "molecule_definition_id": "urn:igc:molecule:bounded-queue@0.1",
        "parameter_bindings": [],
    })
    invalid["structures"][0]["connections"].append({
        "id": "invalid-material-duplication",
        "from_port": "source0.outflow",
        "to_port": "branch0.arrival",
        "connection_kind": "MATERIAL_FLOW",
    })
    try:
        validate_references(invalid)
    except ContractError as exc:
        if exc.code != "MATERIAL_FLOW_MULTICAST":
            raise
    else:
        raise ContractError("NEGATIVE_CASE_ACCEPTED", "duplicated material flow")


def compare_simple_filter_to_atms() -> dict[str, Any]:
    """Compare the PR #5 fixture's ATMS decision with a subset filter baseline."""
    from f3_candidate_selection import select_candidates

    proposals = json.loads(DEFAULT_PROPOSALS.read_text(encoding="utf-8"))
    base = json.loads(DEFAULT_BASE_CANDIDATE.read_text(encoding="utf-8"))
    simple_ids = sorted(
        proposal["candidate_id"]
        for proposal in proposals["proposals"]
        if not any(set(nogood) <= set(proposal["assumption_ids"])
                   for nogood in proposals["nogoods"])
    )
    atms_result = select_candidates(
        base,
        proposals["proposals"],
        proposals["assumptions"],
        proposals["nogoods"],
    )
    atms_ids = sorted(item["candidate"]["candidate_id"] for item in atms_result["selected"])
    return {
        "fixture": "data/synthetic/f3_candidate_proposals.json",
        "simple_filter_candidate_ids": simple_ids,
        "atms_candidate_ids": atms_ids,
        "same_selection": simple_ids == atms_ids,
        "value_added": "NOT_DEMONSTRATED" if simple_ids == atms_ids else "DIFFERENCE_REQUIRES_REVIEW",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--schema-dir", type=Path, required=True)
    parser.add_argument("--check-negative-cases", action="store_true")
    args = parser.parse_args()
    document = json.loads(args.fixture.read_text(encoding="utf-8"))
    validate_linkml_objects(document, args.schema_dir)
    validate_references(document)
    if args.check_negative_cases:
        check_negative_cases(document, args.schema_dir)
    baseline = compare_simple_filter_to_atms()
    if not baseline["same_selection"]:
        raise ContractError("S0_BASELINE_MISMATCH", json.dumps(baseline, sort_keys=True))
    print(json.dumps({
        "status": "FM_A_CONTRACT_VALID",
        "synthetic": document["synthetic"],
        "candidate_ids": [item["id"] for item in document["candidates"]],
        "structural_hashes": [item["structural_hash"] for item in document["structures"]],
        "negative_cases_checked": args.check_negative_cases,
        "simple_filter_comparison": baseline,
        "empirical_or_causal_claim": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
