"""ATMS-gated synthetic selection of SystemModelCandidate variants.

This is a bounded integration seam, not a production ATMS implementation.
"""
from __future__ import annotations

import copy
import math
from typing import Any

try:
    from .f0_atms_probe import AtmsProbe
except ImportError:
    from f0_atms_probe import AtmsProbe


class CandidateSelectionError(ValueError):
    """The ATMS selection contract is malformed."""


def select_candidates(
    base_candidate: dict[str, Any],
    proposals: list[dict[str, Any]],
    assumption_ids: list[str],
    nogoods: list[list[str]],
) -> dict[str, Any]:
    """Return only candidate variants supported by at least one consistent ATMS label."""
    if not proposals:
        raise CandidateSelectionError("at least one candidate proposal is required")
    if len(set(assumption_ids)) != len(assumption_ids) or any(not item for item in assumption_ids):
        raise CandidateSelectionError("assumption ids must be unique non-empty strings")
    known = set(assumption_ids)
    atms = AtmsProbe()
    for assumption_id in assumption_ids:
        atms.assume(assumption_id)

    proposal_nodes: dict[str, str] = {}
    for proposal in proposals:
        candidate_id = proposal.get("candidate_id")
        required = proposal.get("assumption_ids")
        if not isinstance(candidate_id, str) or not candidate_id or candidate_id in proposal_nodes:
            raise CandidateSelectionError("candidate ids must be unique non-empty strings")
        if not isinstance(required, list) or not required:
            raise CandidateSelectionError(f"{candidate_id} must cite at least one assumption")
        if not set(required) <= known:
            raise CandidateSelectionError(f"{candidate_id} references an unknown assumption")
        node = f"candidate_supported:{candidate_id}"
        proposal_nodes[candidate_id] = node
        atms.justify(tuple(required), node)

    for nogood in nogoods:
        if not nogood or not set(nogood) <= known:
            raise CandidateSelectionError("each nogood must cite known assumption ids")
        atms.add_nogood(frozenset(nogood))

    base_assumptions = {item["id"]: item for item in base_candidate.get("assumptions", [])}
    selected = []
    rejected = []
    for proposal in proposals:
        candidate_id = proposal["candidate_id"]
        node = proposal_nodes[candidate_id]
        labels = sorted(
            [sorted(environment) for environment in atms.labels.get(node, set())],
            key=lambda environment: (len(environment), environment),
        )
        if not labels:
            rejected.append({"candidate_id": candidate_id, "status": "REJECTED_NOGOOD",
                             "atms_node": node})
            continue

        candidate = copy.deepcopy(base_candidate)
        candidate["candidate_id"] = candidate_id
        candidate["mechanism_hypothesis"]["id"] = proposal["mechanism_hypothesis_id"]
        candidate["mechanism_hypothesis"]["statement"] = proposal["mechanism_statement"]
        candidate["status"] = "SYNTHETIC_ATMS_SELECTED"
        candidate["atms_selection"] = {
            "engine": "f0-atms-feasibility/0.1",
            "production_engine_selected": False,
            "node": node,
            "minimal_supporting_environments": labels,
        }
        for assumption_id, value in proposal.get("parameter_values", {}).items():
            if assumption_id not in base_assumptions:
                raise CandidateSelectionError(
                    f"{candidate_id} overrides unknown candidate assumption {assumption_id}"
                )
            if (not isinstance(value, (int, float)) or isinstance(value, bool)
                    or not math.isfinite(value) or value < 0):
                raise CandidateSelectionError(
                    f"{candidate_id} parameter override must be finite and non-negative"
                )
            next(item for item in candidate["assumptions"] if item["id"] == assumption_id)["value"] = value
        selected.append({"candidate": candidate, "atms_node": node,
                         "minimal_supporting_environments": labels})

    return {
        "schema": "igc-atms-candidate-selection/0.1",
        "synthetic": True,
        "prototype": "f0-atms-feasibility/0.1",
        "production_engine_selected": False,
        "selected": selected,
        "rejected": rejected,
        "labels": {
            node: [sorted(environment) for environment in sorted(
                atms.labels.get(node, set()), key=lambda item: (len(item), sorted(item))
            )]
            for node in sorted(proposal_nodes.values())
        },
        "nogoods": [sorted(item) for item in sorted(atms.nogoods, key=lambda item: (len(item), sorted(item)))],
    }
