"""Synthetic ablation of an ATMS probe against simpler support rules."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from itertools import product
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from f0_atms_probe import AtmsProbe  # noqa: E402


class AblationError(ValueError):
    pass


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical(labels: dict[str, set[frozenset[str]]]) -> dict[str, list[list[str]]]:
    return {node: [sorted(env) for env in sorted(envs, key=lambda e: (len(e), sorted(e)))]
            for node, envs in sorted(labels.items())}


def _prune(envs: set[frozenset[str]], nogoods: list[frozenset[str]]) -> set[frozenset[str]]:
    return {env for env in envs if not any(ng <= env for ng in nogoods)}


def direct_filter(scenario: dict[str, Any]) -> dict[str, list[list[str]]]:
    """Enumerate each direct conjunction and remove environments containing a nogood."""
    nogoods = [frozenset(x) for x in scenario["nogoods"]]
    labels = {node: set() for node in scenario["candidate_nodes"]}
    for rule in scenario["rules"]:
        if rule["consequent"] in labels:
            labels[rule["consequent"]].add(frozenset(rule["antecedents"]))
    return _canonical({node: _prune(envs, nogoods) for node, envs in labels.items()})


def rule_closure(scenario: dict[str, Any]) -> dict[str, list[list[str]]]:
    """Compute a transparent positive OR/AND least fixed point over assumption sets."""
    labels: dict[str, set[frozenset[str]]] = {
        assumption: {frozenset({assumption})} for assumption in scenario["assumptions"]
    }
    nogoods = [frozenset(x) for x in scenario["nogoods"]]
    changed = True
    while changed:
        changed = False
        for rule in scenario["rules"]:
            choices = [labels.get(node, set()) for node in rule["antecedents"]]
            if any(not choice for choice in choices):
                continue
            derived = {frozenset().union(*combo) for combo in product(*choices)}
            updated = labels.setdefault(rule["consequent"], set()) | _prune(derived, nogoods)
            # Remove non-minimal environments, matching ATMS label semantics.
            minimal = {env for env in updated if not any(other < env for other in updated)}
            if minimal != labels[rule["consequent"]]:
                labels[rule["consequent"]] = minimal
                changed = True
    return _canonical({node: labels.get(node, set()) for node in scenario["candidate_nodes"]})


def atms_labels(scenario: dict[str, Any]) -> dict[str, list[list[str]]]:
    engine = AtmsProbe()
    for assumption in scenario["assumptions"]:
        engine.assume(assumption)
    for rule in scenario["rules"]:
        engine.justify(tuple(rule["antecedents"]), rule["consequent"])
    for nogood in scenario["nogoods"]:
        engine.add_nogood(frozenset(nogood))
    return _canonical({node: engine.labels.get(node, set()) for node in scenario["candidate_nodes"]})


def run(plan_path: Path, output_dir: Path) -> dict[str, Any]:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if plan.get("synthetic") is not True:
        raise AblationError("plan must be explicitly synthetic")
    outputs: dict[str, Any] = {}
    for scenario in plan["scenarios"]:
        atms = atms_labels(scenario)
        baseline = direct_filter(scenario) if scenario["id"] == "S0-simple-filter" else None
        closure = rule_closure(scenario)
        expected = scenario["expected_labels"]
        if atms != expected or closure != expected:
            raise AblationError(f"declared label mismatch in {scenario['id']}")
        if baseline is not None and baseline != expected:
            raise AblationError("simple filter mismatch in S0")
        comparator_matches = (atms == baseline) if baseline is not None else (atms == closure)
        outputs[scenario["id"]] = {
            "question": scenario["question"],
            "atms_labels": atms,
            "direct_filter_labels": baseline,
            "or_and_closure_labels": closure,
            "atms_matches_or_and": atms == closure,
            "primary_comparator": "direct_filter" if baseline is not None else "or_and_closure",
            "atms_value_added": "NOT_DEMONSTRATED" if comparator_matches else "DIFFERENCE_OBSERVED",
            "expected_labels": expected,
            "rule_count": len(scenario["rules"]),
            "nogood_count": len(scenario["nogoods"])
        }

    # Same tasks are paired with method-specific, machine-readable context. No model call
    # occurs here: the artifact measures interface coverage/readiness, not LLM answer quality.
    context_scenarios: dict[str, dict[str, Any]] = {name: {} for name in ("atms", "simple_filter", "or_and_closure")}
    for scenario in plan["scenarios"]:
        sid = scenario["id"]
        result = outputs[sid]
        context_scenarios["atms"][sid] = {
            "candidate_labels": result["atms_labels"],
            "minimal_supporting_environments": result["atms_labels"],
            "justification_rules": scenario["rules"],
            "nogoods": scenario["nogoods"]
        }
        context_scenarios["or_and_closure"][sid] = {
            "derived_candidate_environments": result["or_and_closure_labels"],
            "rule_trace": scenario["rules"],
            "nogoods": scenario["nogoods"]
        }
        if sid == "S0-simple-filter":
            context_scenarios["simple_filter"][sid] = {
                "candidate_status": {
                    node: "SUPPORTED" if result["direct_filter_labels"][node] else "UNSUPPORTED"
                    for node in scenario["candidate_nodes"]
                },
                "matching_nogoods": scenario["nogoods"]
            }
        else:
            context_scenarios["simple_filter"][sid] = {
                "candidate_status": {
                    node: "SUPPORTED" if result["atms_labels"][node] else "UNSUPPORTED"
                    for node in scenario["candidate_nodes"]
                },
                "limitation": "Boolean candidate status omits alternative support lineage"
            }
    context = {
        method: {
            "schema": "igc-atms-llm-context/0.1",
            "method": method,
            "synthetic": True,
            "scenarios": context_scenarios[method],
            "source_plan_sha256": digest(plan_path),
            "guardrails": ["logical support is not causal proof", "do not promote hypotheses to canonical facts"]
        }
        for method in context_scenarios
    }
    task_bundle = {
        "schema": "igc-atms-llm-evaluation-tasks/0.1",
        "tasks": plan["llm_tasks"],
        "answer_quality_status": "NOT_EVALUATED_NO_MODEL_PROVIDER_CONFIGURED",
        "paired_contexts": sorted(context),
        "protocol": "Use the identical task wording and scoring rubric for each context; record model, version, prompt, output, latency, token usage, factuality, citations, and abstentions. Randomize/blind condition labels before scoring."
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    for method, payload in context.items():
        (output_dir / f"llm-context-{method}.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (output_dir / "llm-evaluation-tasks.json").write_text(json.dumps(task_bundle, indent=2) + "\n", encoding="utf-8")
    report = {
        "status": "FM_12_13_SYNTHETIC_ABLATION_PASS_WITH_LLM_UTILITY_NOT_EVALUATED",
        "plan_sha256": digest(plan_path),
        "script_sha256": digest(Path(__file__)),
        "scenarios": outputs,
        "overall_atms_value_added": "NOT_DEMONSTRATED" if all(x["atms_value_added"] == "NOT_DEMONSTRATED" for x in outputs.values()) else "MIXED",
        "llm_interface": {
            "context_packets_generated": True,
            "paired_tasks": len(plan["llm_tasks"]),
            "answer_quality": "NOT_EVALUATED_NO_MODEL_PROVIDER_CONFIGURED",
            "claims_of_llm_utility": False
        },
        "synthetic": True,
        "empirical_or_causal_claim": False
    }
    (output_dir / "ablation-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, default=ROOT / "data/synthetic/fm_12_13_ablation_plan.json")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts/fm-12-13-atms-ablation")
    args = parser.parse_args()
    print(json.dumps(run(args.plan, args.output_dir), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
