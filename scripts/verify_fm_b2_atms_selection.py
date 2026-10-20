"""Independently check B2 input provenance and ATMS support labels."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
COMPOSED = ROOT / "artifacts/fm-b-molecular-composer/composed_candidates.json"
COMPOSITION_REPORT = ROOT / "artifacts/fm-b-molecular-composer/composition-report.json"
SUPPORT_PLAN = ROOT / "data/synthetic/fm_b2_candidate_supports.json"
SELECTOR = ROOT / "scripts/fm_b2_atms_candidate_reasoning.py"
RESULTS = ROOT / "artifacts/fm-b2-atms-candidates"


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def minimal_consistent_environments(support_plan: dict[str, Any], candidate_id: str) -> list[list[str]]:
    nogoods = [set(item) for item in support_plan["nogoods"]]
    environments = {
        frozenset(justification["antecedent_ids"])
        for justification in support_plan["justifications"]
        if justification["candidate_id"] == candidate_id
        and not any(nogood <= set(justification["antecedent_ids"]) for nogood in nogoods)
    }
    minimal = [environment for environment in environments
               if not any(other < environment for other in environments)]
    return sorted((sorted(environment) for environment in minimal), key=lambda item: (len(item), item))


def verify_selection(candidates: dict[str, Any], support_plan: dict[str, Any],
                     selection: dict[str, Any]) -> None:
    candidate_ids = [candidate["id"] for candidate in candidates["candidates"]]
    if len(set(candidate_ids)) != len(candidate_ids):
        raise ValueError("duplicate composed candidate ids")
    structural_hashes = [structure["structural_hash"] for structure in candidates["structures"]]
    if len(structural_hashes) < 2 or len(set(structural_hashes)) != len(structural_hashes):
        raise ValueError("B2 requires structurally distinct molecular candidates")
    if selection["candidate_ids"] != candidate_ids:
        raise ValueError("selection candidate set differs from composed input")
    expected_selected = []
    expected_rejected = []
    for candidate_id in candidate_ids:
        labels = minimal_consistent_environments(support_plan, candidate_id)
        (expected_selected if labels else expected_rejected).append(candidate_id)
        artifact = next((item for item in selection["selected"] + selection["rejected"]
                        if item["candidate_id"] == candidate_id), None)
        if artifact is None or artifact["minimal_supporting_environments"] != labels:
            raise ValueError(f"ATMS label reconstruction mismatch for {candidate_id}")
        candidate = next(item for item in candidates["candidates"] if item["id"] == candidate_id)
        structure = next(item for item in candidates["structures"]
                         if item["id"] == candidate["structure_revision_id"])
        if artifact["structure_revision_id"] != structure["id"]:
            raise ValueError(f"candidate structure reference mismatch for {candidate_id}")
        if artifact["structural_hash"] != structure["structural_hash"]:
            raise ValueError(f"candidate structural hash mismatch for {candidate_id}")
    if [item["candidate_id"] for item in selection["selected"]] != expected_selected:
        raise ValueError("selected candidates do not match reconstructed labels")
    if [item["candidate_id"] for item in selection["rejected"]] != expected_rejected:
        raise ValueError("rejected candidates do not match reconstructed labels")
    if len(selection["selected"]) < 2:
        raise ValueError("B2 PoC must preserve both distinct molecular alternatives")


def main() -> int:
    report = json.loads((RESULTS / "selection-report.json").read_text(encoding="utf-8"))
    for key, path in (("candidate_document_sha256", COMPOSED),
                      ("composition_report_sha256", COMPOSITION_REPORT),
                      ("support_plan_sha256", SUPPORT_PLAN), ("selector_sha256", SELECTOR)):
        if report[key] != digest(path):
            raise SystemExit(f"{key}: current input does not match the selection report")
    candidates = json.loads(COMPOSED.read_text(encoding="utf-8"))
    support_plan = json.loads(SUPPORT_PLAN.read_text(encoding="utf-8"))
    composition_report = json.loads(COMPOSITION_REPORT.read_text(encoding="utf-8"))
    if report["composition_plan_id"] != composition_report["plan_id"]:
        raise SystemExit("selection is linked to a different composition plan")
    if support_plan.get("origin_ref") != composition_report["plan_id"]:
        raise SystemExit("support plan origin does not match the composition plan")
    selection_path = RESULTS / "molecular-atms-selection.json"
    if report["selection_sha256"] != digest(selection_path):
        raise SystemExit("selection artifact digest mismatch")
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    try:
        verify_selection(candidates, support_plan, selection)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    result = {
        "status": "B2_ATMS_MOLECULAR_SUPPORT_PASS_SYNTHETIC",
        "candidate_ids": report["candidate_ids"],
        "selected_candidate_ids": report["selected_candidate_ids"],
        "rejected_candidate_ids": report["rejected_candidate_ids"],
        "support_environment_counts": report["support_environment_counts"],
        "independent_label_reconstruction": True,
        "production_engine_selected": False,
        "empirical_or_causal_claim": False,
    }
    (RESULTS / "verification-report.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
