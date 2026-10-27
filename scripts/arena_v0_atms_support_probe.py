"""Arena V0: test the existing ATMS engine's alternative support semantics.

An epistemic logic fixture, NOT observational evidence or a completed
D/B/M research cycle. No cloud, solver, or other-arm access.
"""
from __future__ import annotations
import json
from scripts.arena_atms import ATMS, Rule

SCHEMA = "igc-arena-atms-alternative-support-proof/0.1"

def exercise():
    # Independent reasons for a provisional claim; neither is empirical truth.
    engine = ATMS(
        assumptions={"observation_a", "observation_b", "scope_valid"},
        facts=set(),
        justifications=[
            Rule("path_a", ("observation_a", "scope_valid"), "candidate_compatible",
                 source_id="source_a"),
            Rule("path_b", ("observation_b", "scope_valid"), "candidate_compatible",
                 source_id="source_b"),
            Rule("downstream", ("candidate_compatible",), "decision_worth_testing",
                 source_id="research_decision"),
        ],
        nogoods=set(),
    )
    original = engine.explain("candidate_compatible")
    assert original["minimal_environments"] == [
        ["observation_a", "scope_valid"], ["observation_b", "scope_valid"]
    ]
    branch = engine.what_if(disable_assumptions={"observation_a"})
    changed = branch["changed_nodes"]
    assert changed["candidate_compatible"]["after"] == [
        ["observation_b", "scope_valid"]
    ]
    assert changed["decision_worth_testing"]["after"] == [
        ["observation_b", "scope_valid"]
    ]
    assert engine.explain("candidate_compatible") == original
    collapsed = engine.what_if(disable_assumptions={"scope_valid"})
    assert collapsed["changed_nodes"]["candidate_compatible"]["after"] == []
    return {
        "schema": SCHEMA,
        "status": "ATMS_ALTERNATIVE_SUPPORT_AND_SELECTIVE_RETRACTION_PASS",
        "before": original["minimal_environments"],
        "after_one_support_removed": changed["candidate_compatible"]["after"],
        "after_shared_premise_removed": collapsed["changed_nodes"]["candidate_compatible"]["after"],
        "dependent_after_one_removed": changed["decision_worth_testing"]["after"],
        "canonical_mutated": branch["canonical_mutated"],
        "limits": [
            "LOGICAL_FIXTURE_NOT_EMPIRICAL_TRUTH",
            "WHAT_IF_NOT_PERSISTED_LEDGER_REVISION",
            "NO_D_B_M_ROUND_EXECUTED",
            "NO_ACCESS_CONTROL_PROVEN"
        ],
    }

if __name__ == "__main__":
    print(json.dumps(exercise(), indent=2))
