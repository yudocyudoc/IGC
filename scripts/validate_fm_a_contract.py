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

        for connection in structure["connections"]:
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
            if connection["connection_kind"] == "MATERIAL_FLOW" and source["signal_kind"] != "FLOW":
                raise ContractError("NON_FLOW_MATERIAL_LINK", connection["id"])

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


def check_negative_cases(document: dict[str, Any]) -> None:
    invalid = copy.deepcopy(document)
    invalid["structures"][0]["molecule_instances"][1]["molecule_definition_id"] = "urn:igc:molecule:missing"
    try:
        validate_references(invalid)
    except ContractError as exc:
        if exc.code != "UNKNOWN_MOLECULE":
            raise
    else:
        raise ContractError("NEGATIVE_CASE_ACCEPTED", "unknown molecule reference")

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
        check_negative_cases(document)
    print(json.dumps({
        "status": "FM_A_CONTRACT_VALID",
        "synthetic": document["synthetic"],
        "candidate_ids": [item["id"] for item in document["candidates"]],
        "structural_hashes": [item["structural_hash"] for item in document["structures"]],
        "negative_cases_checked": args.check_negative_cases,
        "empirical_or_causal_claim": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
