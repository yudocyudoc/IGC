"""Explain synthetic molecular differences and evaluate a finite-pulse probe."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from fm_b2_atms_candidate_reasoning import apply_supports  # noqa: E402
from fm_b3_dynamic_evaluation import (  # noqa: E402
    DynamicEvaluationError, assess_trace, class_name, digest, evaluate_comparison,
    render_evaluation_modelica, render_openmodelica_script, result_prefix,
    validate_scenario, verify_composition_provenance,
)
from verify_fm_b2_atms_selection import verify_selection  # noqa: E402

PACKAGE = "B4MolecularDynamics"
TOLERANCE = 1e-5
MOLECULE_SOURCE = ROOT / "poc/short_wrappers/IGCMolecules.mo"
SOURCE_MANIFEST = ROOT / "poc/short_wrappers/provenance.json"


class B4Error(ValueError):
    pass


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def source_profile() -> dict[str, Any]:
    manifest = load(SOURCE_MANIFEST)
    entry = next((item for item in manifest["files"] if item["path"] == "IGCMolecules.mo"), None)
    if not entry or digest(MOLECULE_SOURCE) != "sha256:" + entry["sha256"]:
        raise B4Error("molecular source differs from its provenance manifest")
    source = re.sub(r"\s+", "", MOLECULE_SOURCE.read_text(encoding="utf-8"))
    signatures = {
        "bounded_queue_stock": "SystemDynamics.Levels.Levelstock(x0=0);",
        "bounded_release": "SystemDynamics.Rates.RRaterelease(minFlow=0,maxFlow=maxThroughput);",
        "proportional_response": "Modelica.Blocks.Math.Gainresponse(k=1/responseTime);",
        "negative_feedback_level_link": "response.u=stock.level;",
        "negative_feedback_control_link": "connect(response.y,release.u);",
        "negative_feedback_release_output": "connect(release.y,completed);",
        "negative_feedback_stock_depletion": "connect(release.y1,stock.u2);",
        "queue_input_path": "connect(arrival,inflow.u);connect(inflow.y,stock.u1);",
        "source_passthrough": "connect(externalRate,incoming.u);connect(incoming.y,outflow);",
        "sink_accumulator_stock": "SystemDynamics.Levels.Level1adeliveries(x0=0);",
        "sink_accumulator_input": "connect(incoming.y,deliveries.u1);",
        "sink_accumulator_output": "total=deliveries.level;",
    }
    missing = [label for label, signature in signatures.items() if signature not in source]
    if missing:
        raise B4Error(f"molecular source does not match audited signatures: {missing}")
    return {"source_path": str(MOLECULE_SOURCE.relative_to(ROOT)).replace("\\", "/"),
            "source_sha256": digest(MOLECULE_SOURCE), "manifest_sha256": digest(SOURCE_MANIFEST),
            "source_snapshot_commit": manifest["source_snapshot_commit"],
            "verified_signatures": sorted(signatures)}


def explain_structure(plan: dict[str, Any], composed: dict[str, Any],
                      candidate_id: str, audit: dict[str, Any]) -> dict[str, Any]:
    candidate = next(item for item in composed["candidates"] if item["id"] == candidate_id)
    structure = next(item for item in composed["structures"]
                     if item["id"] == candidate["structure_revision_id"])
    definitions = {item["id"]: item for item in composed["molecule_definitions"]}
    stages = [item for item in structure["molecule_instances"]
              if item["molecule_definition_id"] == plan["roles"]["stage"]]
    chain = []
    graph: dict[str, list[str]] = {}
    for connection in structure["connections"]:
        src, dst = connection["from_port"].split(".", 1)[0], connection["to_port"].split(".", 1)[0]
        chain.append({"from_instance": src, "to_instance": dst,
                      "from_port": connection["from_port"], "to_port": connection["to_port"]})
        graph.setdefault(src, []).append(dst)
        graph.setdefault(dst, [])
    visiting: set[str] = set()
    visited: set[str] = set()
    def visit(node: str) -> bool:
        if node in visiting:
            return False
        if node in visited:
            return True
        visiting.add(node)
        if not all(visit(next_node) for next_node in graph[node]):
            return False
        visiting.remove(node)
        visited.add(node)
        return True
    graph_acyclic = all(visit(node) for node in graph)
    params = {item["parameter_id"]: item["value"] for item in stages[0]["parameter_bindings"]}
    response = float(params["responseTime"])
    capacity = float(params["maxThroughput"])
    return {
        "candidate_id": candidate_id,
        "structural_hash": structure["structural_hash"],
        "molecule_instances": [{"id": instance["id"],
            "definition_id": instance["molecule_definition_id"],
            "definition_name": definitions[instance["molecule_definition_id"]]["modelica_class"]}
            for instance in structure["molecule_instances"]],
        "stage_count": len(stages), "stock_count": len(stages) + 1,
        "flow_connections": chain,
        "internal_feedback": [{"molecule_instance": stage["id"],
            "type": "BALANCING", "polarity": "NEGATIVE",
            "path": "waiting stock → proportional response → bounded release → stock depletion",
            "capacity_units_per_hour": capacity, "response_time_hours": response}
            for stage in stages],
        "cross_molecule_feedback": not graph_acyclic,
        "cross_molecule_graph_is_acyclic": graph_acyclic,
        "declared_capacity_units_per_hour_per_stage": capacity,
        "declared_response_time_hours_per_stage": response,
        "serial_response_time_sum_hours": len(stages) * response,
        "interpretation_scope": "source-signature-verified; response-time sum is a structural descriptor, not a fitted end-to-end delay",
        "molecule_source_audit": audit,
    }


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _f(row: dict[str, str], key: str, path: Path, index: int) -> float:
    try:
        value = float(row[key])
    except (KeyError, ValueError) as exc:
        raise B4Error(f"{path.name}: invalid or missing {key} at sample {index}") from exc
    if not math.isfinite(value):
        raise B4Error(f"{path.name}: non-finite {key} at sample {index}")
    return value


def analyze_trace(path: Path, candidate_id: str, structure_profile: dict[str, Any],
                  plan: dict[str, Any]) -> dict[str, Any]:
    stages = [stage["id"] for stage in structure_profile["molecule_instances"]
              if stage["definition_id"] == plan["roles"]["stage"]]
    coherence = assess_trace(path, stages, float(plan["simulation"]["start_time"]),
                             float(plan["simulation"]["stop_time"]),
                             int(plan["simulation"]["intervals"]),
                             allow_extra_event_samples=True)
    rows = _rows(path)
    pulse = plan["external_input"]["profile"]
    pulse_end = float(pulse["start_time"]) + float(pulse["period"]) * float(pulse["width_percent"]) / 100
    cap = structure_profile["declared_capacity_units_per_hour_per_stage"]
    saturation = {}
    for stage in stages:
        key = f"completionRate_{stage}"
        rates = [_f(row, key, path, i) for i, row in enumerate(rows)]
        hit = [i for i, rate in enumerate(rates) if rate >= cap - TOLERANCE]
        saturation[stage] = {"capacity_units_per_hour": cap,
            "samples_at_capacity": len(hit),
            "first_at_capacity_time": float(rows[hit[0]]["time"]) if hit else None,
            "last_at_capacity_time": float(rows[hit[-1]]["time"]) if hit else None}
    t = [_f(row, "time", path, i) for i, row in enumerate(rows)]
    delivered = [_f(row, "delivered", path, i) for i, row in enumerate(rows)]
    tail_idx = next((i for i, time in enumerate(t) if time >= pulse_end - TOLERANCE), len(t)-1)
    return {"candidate_id": candidate_id, "csv_sha256": digest(path),
        "coherence": coherence,
        "pulse": {"start_time": pulse["start_time"], "end_time": pulse_end,
                  "amplitude_units_per_hour": pulse["amplitude"],
                  "input_total_units": pulse["amplitude"] * (pulse_end-float(pulse["start_time"]))},
        "saturation_by_stage": saturation,
        "delivery_at_pulse_end": delivered[tail_idx],
        "final_delivery": delivered[-1],
        "recovery_delivery": delivered[-1] - delivered[tail_idx],
        "time_grid": t, "delivery_series": delivered,
        "post_pulse_delivery_series": delivered[tail_idx:],
        "post_pulse_times": t[tail_idx:]}


def compare_candidates(traces: dict[str, dict[str, Any]], profiles: dict[str, dict[str, Any]]) -> dict[str, Any]:
    relation = evaluate_comparison(
        {key: {"times": value["time_grid"], "delivered_series": value["delivery_series"]}
         for key, value in traces.items()},
        {key: value["structural_hash"] for key, value in profiles.items()})
    comparisons = []
    for pair in relation["pairwise_comparisons"]:
        left, right = pair["candidate_ids"]
        a, b = traces[left], traces[right]
        comparisons.append({**pair,
            "structural_delta": {"stage_count": [profiles[left]["stage_count"], profiles[right]["stage_count"]],
                "stock_count": [profiles[left]["stock_count"], profiles[right]["stock_count"]],
                "balancing_loop_count": [len(profiles[left]["internal_feedback"]), len(profiles[right]["internal_feedback"])],
                "serial_response_time_sum_hours": [profiles[left]["serial_response_time_sum_hours"], profiles[right]["serial_response_time_sum_hours"]],
                "cross_molecule_feedback": [profiles[left]["cross_molecule_feedback"], profiles[right]["cross_molecule_feedback"]]},
            "dynamic_consequence": {"final_delivered": [a["final_delivery"], b["final_delivery"]],
                "delivery_at_pulse_end": [a["delivery_at_pulse_end"], b["delivery_at_pulse_end"]],
                "recovery_delivery": [a["recovery_delivery"], b["recovery_delivery"]],
                "max_abs_difference_during_recovery": max(abs(x-y) for x,y in zip(
                    a["post_pulse_delivery_series"], b["post_pulse_delivery_series"]))},
            "discriminating_observation": "measure cumulative deliveries and waiting stock in each stage during the recovery tail"})
    return {**relation, "pairwise_comparisons": comparisons,
        "proposed_discriminating_perturbation": {
            "kind": "finite_rate_pulse", "amplitude_units_per_hour": 3.0,
            "duration_hours": 2.0, "recovery_observation_hours": 14.0,
            "readouts": ["cumulative deliveries", "waiting stock per stage", "completion rate per stage"],
            "rationale": "the finite pulse exposes transient storage and recovery differences in serial queue counts; this proposal is evaluated only in this declared synthetic scenario",
            "optimized_or_empirically_validated": False}}


def prepare(args: argparse.Namespace) -> None:
    plan, composed = load(args.plan), load(args.candidates)
    supports = load(args.support_plan)
    report = load(args.composition_report)
    verify_composition_provenance(args.plan, args.catalog, args.candidates, report)
    selection = apply_supports(composed, supports)
    verify_selection(composed, supports, selection)
    validate_scenario(plan, report, composed, selection)
    audit = source_profile()
    profiles = {item["candidate_id"]: explain_structure(plan, composed, item["candidate_id"], audit)
                for item in selection["selected"]}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    selection_path = args.output_dir / "molecular-atms-selection.json"
    model_path = args.output_dir / f"{PACKAGE}.mo"
    mos_path = args.output_dir / "run-discriminating-pulse.mos"
    profile_path = args.output_dir / "structural-profiles.json"
    selection_path.write_text(json.dumps(selection, indent=2)+"\n", encoding="utf-8")
    model_path.write_text(render_evaluation_modelica(plan, composed, selection,
        include_completion_rates=True, package_name=PACKAGE), encoding="utf-8")
    mos_path.write_text(render_openmodelica_script(plan, composed, selection, package_name=PACKAGE), encoding="utf-8")
    profile_path.write_text(json.dumps(profiles, indent=2)+"\n", encoding="utf-8")
    output = {"status": "B4_READY_FOR_DISCRIMINATING_SIMULATION",
        "plan_sha256": digest(args.plan), "catalog_sha256": digest(args.catalog),
        "supports_sha256": digest(args.support_plan), "candidates_sha256": digest(args.candidates),
        "composition_report_sha256": digest(args.composition_report),
        "selection_sha256": digest(selection_path), "modelica_sha256": digest(model_path),
        "mos_sha256": digest(mos_path), "structural_profiles_sha256": digest(profile_path),
        "selected_ids": [x["candidate_id"] for x in selection["selected"]],
        "rejected_ids": [x["candidate_id"] for x in selection["rejected"]],
        "license_status": "DEFERRED_BY_RESEARCHER", "empirical_or_causal_claim": False}
    (args.output_dir / "b4-execution-plan.json").write_text(json.dumps(output, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(output, indent=2))


def verify(args: argparse.Namespace) -> None:
    plan, composed = load(args.plan), load(args.candidates)
    supports, report = load(args.support_plan), load(args.composition_report)
    verify_composition_provenance(args.plan, args.catalog, args.candidates, report)
    selection = load(args.output_dir / "molecular-atms-selection.json")
    verify_selection(composed, supports, selection)
    validate_scenario(plan, report, composed, selection)
    if selection != apply_supports(composed, supports):
        raise B4Error("saved ATMS selection differs from deterministic recomputation")
    audit = source_profile()
    profiles = {item["candidate_id"]: explain_structure(plan, composed, item["candidate_id"], audit)
                for item in selection["selected"]}
    profile_file = args.output_dir / "structural-profiles.json"
    if load(profile_file) != profiles:
        raise B4Error("structural profiles do not match current molecular source and candidate structures")
    manifest = load(args.output_dir / "b4-execution-plan.json")
    expected_model = render_evaluation_modelica(plan, composed, selection,
        include_completion_rates=True, package_name=PACKAGE)
    expected_mos = render_openmodelica_script(plan, composed, selection, package_name=PACKAGE)
    if (args.output_dir / f"{PACKAGE}.mo").read_text(encoding="utf-8") != expected_model:
        raise B4Error("generated Modelica diagnostics differ from independent reconstruction")
    if (args.output_dir / "run-discriminating-pulse.mos").read_text(encoding="utf-8") != expected_mos:
        raise B4Error("OpenModelica script differs from independent reconstruction")
    for key, path in {"plan_sha256": args.plan, "catalog_sha256": args.catalog,
        "supports_sha256": args.support_plan, "candidates_sha256": args.candidates,
        "composition_report_sha256": args.composition_report,
        "selection_sha256": args.output_dir / "molecular-atms-selection.json",
        "modelica_sha256": args.output_dir / f"{PACKAGE}.mo",
        "mos_sha256": args.output_dir / "run-discriminating-pulse.mos",
        "structural_profiles_sha256": profile_file}.items():
        if manifest.get(key) != digest(path):
            raise B4Error(f"{key}: B4 artifact digest mismatch")
    log = args.openmodelica_log.read_text(encoding="utf-8", errors="replace")
    if re.search(r"Error:|Failed to load|Class .* not found", log):
        raise B4Error("OpenModelica log contains an error")
    traces = {}
    for candidate_id in manifest["selected_ids"]:
        if f"Check of {PACKAGE}.{class_name(candidate_id)} completed successfully" not in log:
            raise B4Error(f"OpenModelica did not check {candidate_id}")
        path = args.output_dir / f"{result_prefix(candidate_id)}_res.csv"
        traces[candidate_id] = analyze_trace(path, candidate_id, profiles[candidate_id], plan)
    relation = compare_candidates(traces, profiles)
    evidence = {"status": "B4_DISCRIMINATING_ANALYSIS_PASS_SYNTHETIC",
        "atms_retained_and_simulated": manifest["selected_ids"],
        "atms_rejected_and_not_simulated": manifest["rejected_ids"],
        "structural_profiles": profiles, "candidate_dynamic_metrics": traces,
        "comparison_and_explanation": relation,
        "characterization_scope": ["stock/flow counts", "bounded release capacity", "declared response-time parameters",
            "source-signature-verified internal balancing feedback", "cross-molecule graph cycles", "simulated capacity saturation"],
        "limits": ["finite-pulse proposal is tested only for this synthetic scenario", "no empirical adequacy or causal claim",
            "no general Modelica structural parser; feedback diagnosis is restricted to source-verified molecule signatures"],
        "modelica_image": args.image, "openmodelica_log_sha256": digest(args.openmodelica_log),
        "license_status": "DEFERRED_BY_RESEARCHER"}
    out = args.output_dir / "b4-discriminating-analysis.json"
    out.write_text(json.dumps(evidence, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))


def common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--plan", type=Path, default=ROOT / "data/synthetic/fm_b4_discriminating_pulse_plan.json")
    p.add_argument("--catalog", type=Path, default=ROOT / "data/synthetic/fm_a_structural_candidates.json")
    p.add_argument("--candidates", type=Path, required=True)
    p.add_argument("--composition-report", type=Path, required=True)
    p.add_argument("--support-plan", type=Path, default=ROOT / "data/synthetic/fm_b4_discriminating_pulse_supports.json")
    p.add_argument("--output-dir", type=Path, default=ROOT / "artifacts/fm-b4-discriminating-analysis")


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare"); common(p)
    p = sub.add_parser("verify"); common(p); p.add_argument("--openmodelica-log", type=Path, required=True); p.add_argument("--image", required=True)
    args = parser.parse_args()
    prepare(args) if args.command == "prepare" else verify(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
