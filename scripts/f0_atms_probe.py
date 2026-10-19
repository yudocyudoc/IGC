"""Small F0 feasibility probe for assumption labels and nogood pruning.

This is a synthetic prototype, not a selected or production ATMS engine.
"""
from __future__ import annotations

from itertools import product


Environment = frozenset[str]
Label = set[Environment]


def _minimal(environments: set[Environment]) -> Label:
    return {
        environment for environment in environments
        if not any(other < environment for other in environments)
    }


class AtmsProbe:
    def __init__(self) -> None:
        self.labels: dict[str, Label] = {}
        self.justifications: list[tuple[tuple[str, ...], str]] = []
        self.nogoods: Label = set()

    def assume(self, node: str) -> None:
        self.labels[node] = {frozenset({node})}

    def justify(self, antecedents: tuple[str, ...], consequent: str) -> None:
        self.labels.setdefault(consequent, set())
        self.justifications.append((antecedents, consequent))
        self.propagate()

    def add_nogood(self, environment: Environment) -> None:
        self.nogoods = _minimal(self.nogoods | {environment})
        for node, label in self.labels.items():
            self.labels[node] = {
                candidate for candidate in label
                if not any(nogood <= candidate for nogood in self.nogoods)
            }
        self.propagate()

    def propagate(self) -> None:
        changed = True
        while changed:
            changed = False
            for antecedents, consequent in self.justifications:
                if any(not self.labels.get(node) for node in antecedents):
                    continue
                choices = [self.labels[node] for node in antecedents]
                candidates = {
                    frozenset().union(*environment_tuple)
                    for environment_tuple in product(*choices)
                }
                candidates = {
                    environment for environment in candidates
                    if not any(nogood <= environment for nogood in self.nogoods)
                }
                updated = _minimal(self.labels[consequent] | candidates)
                if updated != self.labels[consequent]:
                    self.labels[consequent] = updated
                    changed = True

    def supported_in(self, node: str, context: Environment) -> bool:
        return any(environment <= context for environment in self.labels.get(node, set()))


def run_atms_probe() -> dict:
    atms = AtmsProbe()
    atms.assume("candidate_m1")
    atms.assume("candidate_m2")
    atms.assume("promotion_active")
    atms.assume("promotion_inactive")
    atms.justify(("candidate_m1",), "model_m1_supported")
    atms.justify(("candidate_m2",), "model_m2_supported")
    atms.justify(("promotion_active", "promotion_inactive"), "impossible_pair")
    atms.add_nogood(frozenset({"promotion_active", "promotion_inactive"}))

    alternatives_coexist = (
        atms.supported_in("model_m1_supported", frozenset({"candidate_m1", "candidate_m2"}))
        and atms.supported_in("model_m2_supported", frozenset({"candidate_m1", "candidate_m2"}))
    )
    nogood_pruned = not atms.labels["impossible_pair"]
    return {
        "stage": "atms_reasoning",
        "status": "PASS" if alternatives_coexist and nogood_pruned else "FAIL",
        "prototype": "f0-atms-feasibility/0.1",
        "production_engine_selected": False,
        "alternatives_coexist": alternatives_coexist,
        "nogood_pruned": nogood_pruned,
        "minimal_labels": {
            node: [sorted(environment) for environment in sorted(label, key=lambda e: (len(e), sorted(e)))]
            for node, label in sorted(atms.labels.items())
        },
    }
