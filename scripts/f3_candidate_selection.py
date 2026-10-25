"""ATMS-gated synthetic selection of SystemModelCandidate variants.

This is a bounded integration seam, not a production ATMS implementation.
"""
from __future__ import annotations

import copy
import math
from typing import Any

try:
    from .arena_atms import ATMS, Rule, ENGINE_VERSION
except ImportError:
    from arena_atms import ATMS, Rule, ENGINE_VERSION


class CandidateSelectionError(ValueError):
    """The ATMS selection contract is malformed."""


def select_candidates(
    base_candidate: dict[str, Any],
    proposals: list[dict[str, Any]],
    assumption_ids: list[str],
    nogoods: list[list[str]],
) -> dict[str, Any]:
    """Validate every proposal, then return candidates with consistent ATMS labels."""
    if not isinstance(proposals, list) or not proposals:
        raise CandidateSelectionError("at least one candidate proposal is required")
    if (not isinstance(assumption_ids, list)
            or any(not isinstance(item, str) or not item for item in assumption_ids)
            or len(set(assumption_ids)) != len(assumption_ids)):
        raise CandidateSelectionError("assumption ids must be unique non-empty strings")
    known = set(assumption_ids)

    base_items = base_candidate.get("assumptions")
    if not isinstance(base_items, list) or not base_items:
        raise CandidateSelectionError("base candidate must declare assumptions")
    base_assumptions: dict[str, dict[str, Any]] = {}
    for item in base_items:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
            raise CandidateSelectionError("base candidate assumptions need non-empty ids")
        if item["id"] in base_assumptions:
            raise CandidateSelectionError("base candidate assumption ids must be unique")
        base_assumptions[item["id"]] = item

    # Validate the complete input set before ATMS pruning. Invalid alternatives must
    # not disappear silently merely because a nogood removes their support label.
    proposal_nodes: dict[str, str] = {}
    parameter_values: dict[str, dict[str, int | float]] = {}
    for proposal in proposals:
        if not isinstance(proposal, dict):
            raise CandidateSelectionError("each candidate proposal must be an object")
        candidate_id = proposal.get("candidate_id")
        if not isinstance(candidate_id, str) or not candidate_id or candidate_id in proposal_nodes:
            raise CandidateSelectionError("candidate ids must be unique non-empty strings")
        required = proposal.get("assumption_ids")
        if (not isinstance(required, list) or not required
                or any(not isinstance(item, str) or not item for item in required)
                or len(set(required)) != len(required)):
            raise CandidateSelectionError(f"{candidate_id} must cite unique assumption ids")
        if not set(required) <= known:
            raise CandidateSelectionError(f"{candidate_id} references an unknown assumption")
        if not isinstance(proposal.get("mechanism_hypothesis_id"), str) or not proposal["mechanism_hypothesis_id"]:
            raise CandidateSelectionError(f"{candidate_id} needs a mechanism hypothesis id")
        if not isinstance(proposal.get("mechanism_statement"), str) or not proposal["mechanism_statement"]:
            raise CandidateSelectionError(f"{candidate_id} needs a mechanism statement")

        overrides = proposal.get("parameter_values", {})
        if not isinstance(overrides, dict):
            raise CandidateSelectionError(f"{candidate_id} parameter_values must be an object")
        checked_overrides: dict[str, int | float] = {}
        for assumption_id, value in overrides.items():
            if assumption_id not in base_assumptions:
                raise CandidateSelectionError(
                    f"{candidate_id} overrides unknown candidate assumption {assumption_id}"
                )
            if (not isinstance(value, (int, float)) or isinstance(value, bool)
                    or not math.isfinite(value) or value < 0):
                raise CandidateSelectionError(
                    f"{candidate_id} parameter override must be finite and non-negative"
                )
            checked_overrides[assumption_id] = value
        parameter_values[candidate_id] = checked_overrides
        proposal_nodes[candidate_id] = f"candidate_supported:{candidate_id}"

    if not isinstance(nogoods, list):
        raise CandidateSelectionError("nogoods must be a list")
    for nogood in nogoods:
        if (not isinstance(nogood, list) or not nogood
                or any(not isinstance(item, str) or not item for item in nogood)
                or len(set(nogood)) != len(nogood)
                or not set(nogood) <= known):
            raise CandidateSelectionError("each nogood must cite unique known assumption ids")

    proposal_rules = [
        Rule("proposal:" + proposal["candidate_id"],
             tuple(proposal["assumption_ids"]),
             proposal_nodes[proposal["candidate_id"]])
        for proposal in proposals
    ]
    atms = ATMS(
        set(assumption_ids), set(),
        proposal_rules,
        {frozenset(nogood) for nogood in nogoods}
    )

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
            "engine": ENGINE_VERSION,
            "production_engine_selected": False,
            "node": node,
            "minimal_supporting_environments": labels,
        }
        for assumption_id, value in parameter_values[candidate_id].items():
            next(item for item in candidate["assumptions"] if item["id"] == assumption_id)["value"] = value
        selected.append({"candidate": candidate, "atms_node": node,
                         "minimal_supporting_environments": labels})

    return {
        "schema": "igc-atms-candidate-selection/0.1",
        "synthetic": True,
        "prototype": ENGINE_VERSION,
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
