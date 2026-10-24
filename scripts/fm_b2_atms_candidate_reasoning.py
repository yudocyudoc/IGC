"""Apply the shared Arena ATMS engine to composed molecular candidates."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from arena_atms import ATMS, Rule, ENGINE_VERSION  # noqa: E402


class MolecularAtmsError(ValueError):
    pass


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def apply_supports(composed: dict[str, Any], support_plan: dict[str, Any]) -> dict[str, Any]:
    if support_plan.get("synthetic") is not True:
        raise MolecularAtmsError("support plan must be explicitly synthetic")
    candidates = {item["id"]: item for item in composed.get("candidates", [])}
    structures = {item["id"]: item for item in composed.get("structures", [])}
    if len(candidates) != len(composed.get("candidates", [])):
        raise MolecularAtmsError("composed candidate ids must be unique")
    if len(structures) != len(composed.get("structures", [])):
        raise MolecularAtmsError("composed structure ids must be unique")
    referenced = set()
    for candidate in candidates.values():
        structure_id = candidate["structure_revision_id"]
        if structure_id not in structures:
            raise MolecularAtmsError(f"candidate has missing structure: {candidate['id']}")
        referenced.add(candidate["id"])

    assumptions = support_plan.get("assumptions")
    if not isinstance(assumptions, list) or not assumptions:
        raise MolecularAtmsError("at least one assumption is required")
    assumption_ids = [item.get("id") for item in assumptions if isinstance(item, dict)]
    if len(assumption_ids) != len(assumptions) or any(not isinstance(item, str) or not item for item in assumption_ids):
        raise MolecularAtmsError("assumption ids must be non-empty strings")
    if len(set(assumption_ids)) != len(assumption_ids):
        raise MolecularAtmsError("assumption ids must be unique")
    known = set(assumption_ids)

    justifications = support_plan.get("justifications")
    if not isinstance(justifications, list) or not justifications:
        raise MolecularAtmsError("at least one justification is required")
    justification_ids: set[str] = set()
    covered_candidates: set[str] = set()
    for justification in justifications:
        if not isinstance(justification, dict):
            raise MolecularAtmsError("each justification must be an object")
        identifier = justification.get("id")
        candidate_id = justification.get("candidate_id")
        antecedents = justification.get("antecedent_ids")
        if not isinstance(identifier, str) or not identifier or identifier in justification_ids:
            raise MolecularAtmsError("justification ids must be unique non-empty strings")
        justification_ids.add(identifier)
        if candidate_id not in candidates:
            raise MolecularAtmsError(f"justification references unknown candidate: {candidate_id}")
        if (not isinstance(antecedents, list) or not antecedents
                or any(not isinstance(item, str) or not item for item in antecedents)
                or len(set(antecedents)) != len(antecedents)
                or not set(antecedents) <= known):
            raise MolecularAtmsError(f"invalid antecedents in {identifier}")
        covered_candidates.add(candidate_id)
    if covered_candidates != referenced:
        missing = sorted(referenced - covered_candidates)
        extra = sorted(covered_candidates - referenced)
        raise MolecularAtmsError(f"candidate support coverage mismatch; missing={missing}, extra={extra}")

    nogoods = support_plan.get("nogoods")
    if not isinstance(nogoods, list):
        raise MolecularAtmsError("nogoods must be a list")
    for nogood in nogoods:
        if (not isinstance(nogood, list) or not nogood
                or any(not isinstance(item, str) or not item for item in nogood)
                or len(set(nogood)) != len(nogood) or not set(nogood) <= known):
            raise MolecularAtmsError("each nogood must contain unique known assumption ids")

    nodes = {candidate_id: f"molecular_candidate_supported:{candidate_id}"
             for candidate_id in candidates}
    engine = ATMS(
        set(assumption_ids),
        set(),
        [Rule(item["id"], tuple(item["antecedent_ids"]), nodes[item["candidate_id"]])
         for item in justifications],
        {frozenset(item) for item in nogoods},
    )

    selected = []
    rejected = []
    for candidate_id, candidate in candidates.items():
        node = nodes[candidate_id]
        labels = sorted((sorted(environment) for environment in engine.labels.get(node, set())),
                        key=lambda item: (len(item), item))
        structure = structures[candidate["structure_revision_id"]]
        entry = {
            "candidate_id": candidate_id,
            "structure_revision_id": structure["id"],
            "structural_hash": structure["structural_hash"],
            "atms_node": node,
            "minimal_supporting_environments": labels,
        }
        if labels:
            entry["status"] = "SUPPORTED_SYNTHETIC"
            selected.append(entry)
        else:
            entry["status"] = "REJECTED_NOGOOD"
            rejected.append(entry)

    return {
        "schema": "igc-fm-b2-atms-molecular-selection/0.1",
        "synthetic": True,
        "engine": ENGINE_VERSION,
        "production_engine_selected": False,
        "selection_policy": "retain_every_candidate_with_at_least_one_consistent_minimal_environment",
        "candidate_ids": list(candidates),
        "selected": selected,
        "rejected": rejected,
        "nogoods": [sorted(item) for item in nogoods],
        "assumptions": assumptions,
        "justifications": justifications,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=Path,
                        default=ROOT / "artifacts/fm-b-molecular-composer/composed_candidates.json")
    parser.add_argument("--support-plan", type=Path,
                        default=ROOT / "data/synthetic/fm_b2_candidate_supports.json")
    parser.add_argument("--composition-report", type=Path,
                        default=ROOT / "artifacts/fm-b-molecular-composer/composition-report.json")
    parser.add_argument("--output-dir", type=Path,
                        default=ROOT / "artifacts/fm-b2-atms-candidates")
    args = parser.parse_args()
    candidates = json.loads(args.candidates.read_text(encoding="utf-8"))
    support_plan = json.loads(args.support_plan.read_text(encoding="utf-8"))
    composition_report = json.loads(args.composition_report.read_text(encoding="utf-8"))
    if support_plan.get("origin_ref") != composition_report.get("plan_id"):
        raise MolecularAtmsError("support plan origin does not match the composition plan")
    if composition_report.get("composed_candidates_sha256") != digest(args.candidates):
        raise MolecularAtmsError("composed candidate file does not match the composition report")
    result = apply_supports(candidates, support_plan)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "input-composed-candidates.json").write_bytes(args.candidates.read_bytes())
    (args.output_dir / "input-composition-report.json").write_bytes(args.composition_report.read_bytes())
    (args.output_dir / "input-support-plan.json").write_bytes(args.support_plan.read_bytes())
    output_path = args.output_dir / "molecular-atms-selection.json"
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    report = {
        "status": "B2_ATMS_MOLECULAR_SUPPORT_PASS_SYNTHETIC",
        "candidate_document_sha256": digest(args.candidates),
        "composition_report_sha256": digest(args.composition_report),
        "support_plan_sha256": digest(args.support_plan),
        "selector_sha256": digest(Path(__file__)),
        "selection_sha256": digest(output_path),
        "candidate_ids": result["candidate_ids"],
        "composition_plan_id": composition_report["plan_id"],
        "selected_candidate_ids": [item["candidate_id"] for item in result["selected"]],
        "rejected_candidate_ids": [item["candidate_id"] for item in result["rejected"]],
        "support_environment_counts": {
            item["candidate_id"]: len(item["minimal_supporting_environments"])
            for item in result["selected"]
        },
        "engine": result["engine"],
        "production_engine_selected": False,
        "empirical_or_causal_claim": False,
    }
    report_path = args.output_dir / "selection-report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
