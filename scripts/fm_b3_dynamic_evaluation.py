"""Execute ATMS-admissible molecular alternatives and assess stock-flow coherence."""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from fm_b2_atms_candidate_reasoning import apply_supports  # noqa: E402
from verify_fm_b2_atms_selection import verify_selection  # noqa: E402
from compose_molecular_candidates import modelica_identifier  # noqa: E402

TOLERANCE = 1e-5


class DynamicEvaluationError(ValueError):
    pass


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def class_name(candidate_id: str) -> str:
    return "Evaluate_" + modelica_identifier(candidate_id.rsplit(":", 1)[-1])


def result_prefix(candidate_id: str) -> str:
    return "b3-" + modelica_identifier(candidate_id.rsplit(":", 1)[-1]).lower()


def validate_scenario(plan: dict[str, Any], composition_report: dict[str, Any],
                      composed: dict[str, Any], selection: dict[str, Any]) -> None:
    if plan.get("synthetic") is not True or plan.get("empirical_or_causal_claim") is not False:
        raise DynamicEvaluationError("B3 plan must be explicitly synthetic and non-causal")
    if composition_report.get("plan_id") != plan.get("id"):
        raise DynamicEvaluationError("composition report is for a different plan")
    candidates = {item["id"]: item for item in composed.get("candidates", [])}
    structures = {item["id"]: item for item in composed.get("structures", [])}
    selected_ids = [item["candidate_id"] for item in selection.get("selected", [])]
    rejected_ids = [item["candidate_id"] for item in selection.get("rejected", [])]
    if len(selected_ids) < 2:
        raise DynamicEvaluationError("B3 requires at least two supported structural alternatives")
    if not rejected_ids:
        raise DynamicEvaluationError("B3 scenario must include an ATMS-rejected alternative")
    if len(set(selected_ids + rejected_ids)) != len(selected_ids + rejected_ids):
        raise DynamicEvaluationError("ATMS selection repeats a candidate")
    if set(selected_ids + rejected_ids) != set(candidates):
        raise DynamicEvaluationError("ATMS selection does not partition the composed candidate set")
    if set(selection.get("candidate_ids", [])) != set(candidates):
        raise DynamicEvaluationError("ATMS candidate set differs from composition")
    if any(candidates[item]["structure_revision_id"] not in structures for item in candidates):
        raise DynamicEvaluationError("candidate refers to a missing structure")
    if len({structures[candidates[item]["structure_revision_id"]]["structural_hash"]
            for item in selected_ids}) != len(selected_ids):
        raise DynamicEvaluationError("supported candidates must have distinct structures")


def verify_composition_provenance(plan_path: Path, catalog_path: Path, candidates_path: Path,
                                  composition_report: dict[str, Any]) -> None:
    expected = {
        "plan_sha256": plan_path,
        "catalog_sha256": catalog_path,
        "generator_sha256": ROOT / "scripts/compose_molecular_candidates.py",
        "composed_candidates_sha256": candidates_path,
    }
    for key, path in expected.items():
        if composition_report.get(key) != digest(path):
            raise DynamicEvaluationError(f"composition report input mismatch: {key}")


def render_evaluation_modelica(plan: dict[str, Any], composed: dict[str, Any],
                               selection: dict[str, Any],
                               include_completion_rates: bool = False,
                               package_name: str = "B3MolecularDynamics") -> str:
    definitions = {item["id"]: item for item in composed["molecule_definitions"]}
    candidates = {item["id"]: item for item in composed["candidates"]}
    structures = {item["id"]: item for item in composed["structures"]}
    lines = ["within;", f"package {package_name}"]
    for support in selection["selected"]:
        candidate = candidates[support["candidate_id"]]
        structure = structures[candidate["structure_revision_id"]]
        model_class = "GeneratedMolecularCandidates.Composed_" + modelica_identifier(
            candidate["id"].rsplit(":", 1)[-1]
        )
        source = next(item["id"] for item in structure["molecule_instances"]
                      if item["molecule_definition_id"] == plan["roles"]["source"])
        sink = next(item["id"] for item in structure["molecule_instances"]
                    if item["molecule_definition_id"] == plan["roles"]["sink"])
        stages = [item["id"] for item in structure["molecule_instances"]
                  if item["molecule_definition_id"] == plan["roles"]["stage"]]
        if not stages:
            raise DynamicEvaluationError(f"selected candidate has no stages: {candidate['id']}")
        cname = class_name(candidate["id"])
        model_lines = [
            f"  model {cname}",
            f"    {model_class} candidate;",
            "    Modelica.Blocks.Continuous.Integrator cumulativeInput(initType=Modelica.Blocks.Types.Init.InitialState, y_start=0);",
            "    Modelica.Blocks.Continuous.Integrator cumulativeTerminalInput(initType=Modelica.Blocks.Types.Init.InitialState, y_start=0);",
        ]
        for stage in stages:
            model_lines.extend([
                f"    Modelica.Blocks.Continuous.Integrator cumulativeArrival_{stage}(initType=Modelica.Blocks.Types.Init.InitialState, y_start=0);",
                f"    Modelica.Blocks.Continuous.Integrator cumulativeCompletion_{stage}(initType=Modelica.Blocks.Types.Init.InitialState, y_start=0);",
                f"    output Real waiting_{stage};",
                f"    output Real cumulativeArrivals_{stage};",
                f"    output Real cumulativeCompletions_{stage};",
                f"    output Real queueBalanceError_{stage};",
            ])
            if include_completion_rates:
                model_lines.append(f"    output Real completionRate_{stage};")
        model_lines.extend([
            "    output Real delivered;",
            "    output Real acceptedTotal;",
            "    output Real terminalArrivals;",
            "    output Real systemInventory;",
            "    output Real systemBalanceError;",
            "    output Real terminalBalanceError;",
            "  equation",
            f"    cumulativeInput.u = candidate.{source}.outflow;",
            f"    cumulativeTerminalInput.u = candidate.{sink}.arrival;",
            "    delivered = candidate.delivered;",
            "    acceptedTotal = cumulativeInput.y;",
            "    terminalArrivals = cumulativeTerminalInput.y;",
            "    systemInventory = delivered + " + " + ".join(
                f"candidate.{stage}.waiting" for stage in stages
            ) + ";",
            "    systemBalanceError = acceptedTotal - systemInventory;",
            "    terminalBalanceError = terminalArrivals - delivered;",
        ])
        for stage in stages:
            model_lines.extend([
                f"    cumulativeArrival_{stage}.u = candidate.{stage}.arrival;",
                f"    cumulativeCompletion_{stage}.u = candidate.{stage}.completed;",
                f"    waiting_{stage} = candidate.{stage}.waiting;",
                f"    cumulativeArrivals_{stage} = cumulativeArrival_{stage}.y;",
                f"    cumulativeCompletions_{stage} = cumulativeCompletion_{stage}.y;",
                f"    queueBalanceError_{stage} = cumulativeArrivals_{stage} - cumulativeCompletions_{stage} - waiting_{stage};",
            ])
            if include_completion_rates:
                model_lines.append(f"    completionRate_{stage} = candidate.{stage}.completed;")
        model_lines.extend([f"  end {cname};", ""])
        lines.extend(model_lines)
    return "\n".join(lines + [f"end {package_name};", ""])


def render_openmodelica_script(plan: dict[str, Any], composed: dict[str, Any],
                               selection: dict[str, Any],
                               package_name: str = "B3MolecularDynamics") -> str:
    lines = [
        'setModelicaPath("/opt/modelica:/opt/systemdynamics");',
        'loadFile("/opt/systemdynamics/SystemDynamics/package.mo");',
        'loadFile("/evidence/IGCMolecules.mo");',
        'loadFile("/evidence/IGCInformationMolecules.mo");',
        'loadFile("/composer/GeneratedMolecularCandidates.mo");',
        f'loadFile("/results/{package_name}.mo");',
        "print(getErrorString());",
    ]
    selected = [item["candidate_id"] for item in selection["selected"]]
    candidates = {item["id"]: item for item in composed["candidates"]}
    if set(selected) & {item["candidate_id"] for item in selection["rejected"]}:
        raise DynamicEvaluationError("rejected candidate cannot be executed")
    sim = plan["simulation"]
    for candidate_id in selected:
        evaluation_class = package_name + "." + class_name(candidate_id)
        lines.extend([
            f"checkModel({evaluation_class});",
            "print(getErrorString());",
            f"simulate({evaluation_class}, startTime={float(sim['start_time']):.17g}, "
            f"stopTime={float(sim['stop_time']):.17g}, numberOfIntervals={int(sim['intervals'])}, "
            f'outputFormat="csv", fileNamePrefix="{result_prefix(candidates[candidate_id]["id"])}");',
            "print(getErrorString());",
        ])
    return "\n".join(lines) + "\n"


def _number(row: dict[str, str], key: str, path: Path, row_index: int) -> float:
    try:
        value = float(row[key])
    except (KeyError, ValueError) as exc:
        raise DynamicEvaluationError(f"{path.name}: missing or invalid {key} at row {row_index}") from exc
    if not math.isfinite(value):
        raise DynamicEvaluationError(f"{path.name}: non-finite {key} at row {row_index}")
    return value


def assess_trace(path: Path, stage_ids: list[str], start: float, stop: float,
                 intervals: int, allow_extra_event_samples: bool = False) -> dict[str, Any]:
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    expected_samples = intervals + 2
    if (len(rows) < expected_samples if allow_extra_event_samples else len(rows) != expected_samples):
        relation = "at least" if allow_extra_event_samples else "exactly"
        raise DynamicEvaluationError(f"{path.name}: expected {relation} {expected_samples} samples, got {len(rows)}")
    required = {"time", "delivered", "acceptedTotal", "systemInventory", "systemBalanceError",
                "terminalBalanceError", "terminalArrivals"}
    required.update(f"waiting_{stage}" for stage in stage_ids)
    required.update(f"cumulativeArrivals_{stage}" for stage in stage_ids)
    required.update(f"cumulativeCompletions_{stage}" for stage in stage_ids)
    required.update(f"queueBalanceError_{stage}" for stage in stage_ids)
    if not rows or not required <= set(rows[0]):
        raise DynamicEvaluationError(f"{path.name}: missing dynamic diagnostic columns {sorted(required - set(rows[0]) if rows else required)}")
    times = [_number(row, "time", path, index) for index, row in enumerate(rows)]
    if abs(times[0] - start) > TOLERANCE or abs(times[-1] - stop) > TOLERANCE:
        raise DynamicEvaluationError(f"{path.name}: simulation time bounds differ from the plan")
    if any(right < left - TOLERANCE for left, right in zip(times, times[1:])):
        raise DynamicEvaluationError(f"{path.name}: time cannot move backwards")
    if not any(right > left + TOLERANCE for left, right in zip(times, times[1:])):
        raise DynamicEvaluationError(f"{path.name}: simulation time did not advance")
    if allow_extra_event_samples:
        nominal_grid = [start + (stop - start) * index / intervals for index in range(intervals + 1)]
        missing_grid = [point for point in nominal_grid
                        if not any(abs(sample - point) <= TOLERANCE for sample in times)]
        if missing_grid:
            raise DynamicEvaluationError(f"{path.name}: event samples are allowed only when the planned time grid is retained; missing {missing_grid[:3]}")
    metrics = {key: [] for key in ["delivered", "acceptedTotal", "systemInventory", "systemBalanceError", "terminalBalanceError", "terminalArrivals"]}
    for stage in stage_ids:
        metrics[f"waiting_{stage}"] = []
        metrics[f"cumulativeArrivals_{stage}"] = []
        metrics[f"cumulativeCompletions_{stage}"] = []
        metrics[f"queueBalanceError_{stage}"] = []
    independent_global_errors = []
    independent_queue_errors = {stage: [] for stage in stage_ids}
    for index, row in enumerate(rows):
        for key in metrics:
            metrics[key].append(_number(row, key, path, index))
        if metrics["delivered"][-1] < -TOLERANCE or metrics["acceptedTotal"][-1] < -TOLERANCE:
            raise DynamicEvaluationError(f"{path.name}: cumulative quantities cannot be negative")
        for stage in stage_ids:
            if metrics[f"waiting_{stage}"][-1] < -TOLERANCE:
                raise DynamicEvaluationError(f"{path.name}: negative queue stock {stage}")
        reconstructed_inventory = metrics["delivered"][-1] + sum(
            metrics[f"waiting_{stage}"][-1] for stage in stage_ids
        )
        if abs(metrics["systemInventory"][-1] - reconstructed_inventory) > TOLERANCE:
            raise DynamicEvaluationError(f"{path.name}: inventory observable does not match state stocks")
        global_error = metrics["acceptedTotal"][-1] - metrics["delivered"][-1] - sum(
            metrics[f"waiting_{stage}"][-1] for stage in stage_ids
        )
        independent_global_errors.append(global_error)
        if abs(global_error) > TOLERANCE:
            raise DynamicEvaluationError(f"{path.name}: independently reconstructed global stock-flow conservation failed")
        terminal_error = metrics["terminalArrivals"][-1] - metrics["delivered"][-1]
        if abs(terminal_error) > TOLERANCE:
            raise DynamicEvaluationError(f"{path.name}: independently reconstructed terminal balance failed")
        if abs(metrics["systemBalanceError"][-1] - global_error) > TOLERANCE:
            raise DynamicEvaluationError(f"{path.name}: exported global balance diagnostic disagrees with independent reconstruction")
        if abs(metrics["terminalBalanceError"][-1] - terminal_error) > TOLERANCE:
            raise DynamicEvaluationError(f"{path.name}: exported terminal diagnostic disagrees with independent reconstruction")
        if metrics["delivered"][-1] > metrics["acceptedTotal"][-1] + TOLERANCE:
            raise DynamicEvaluationError(f"{path.name}: delivered quantity exceeds accepted input")
        for stage in stage_ids:
            queue_error = (metrics[f"cumulativeArrivals_{stage}"][-1]
                           - metrics[f"cumulativeCompletions_{stage}"][-1]
                           - metrics[f"waiting_{stage}"][-1])
            independent_queue_errors[stage].append(queue_error)
            if abs(queue_error) > TOLERANCE:
                raise DynamicEvaluationError(f"{path.name}: independently reconstructed queue stock-flow balance failed at {stage}")
            if abs(metrics[f"queueBalanceError_{stage}"][-1] - queue_error) > TOLERANCE:
                raise DynamicEvaluationError(f"{path.name}: exported queue diagnostic disagrees with independent reconstruction at {stage}")
    for key in ("delivered", "acceptedTotal"):
        if any(right + TOLERANCE < left for left, right in zip(metrics[key], metrics[key][1:])):
            raise DynamicEvaluationError(f"{path.name}: {key} must not decrease")
    duplicate_events = [
        {"time": left, "previous_sample_row": index, "sample_row": index + 1}
        for index, (left, right) in enumerate(zip(times, times[1:]))
        if abs(right - left) <= TOLERANCE
    ]
    return {
        "samples": len(rows),
        "final_delivered": metrics["delivered"][-1],
        "final_accepted_total": metrics["acceptedTotal"][-1],
        "final_system_inventory": metrics["systemInventory"][-1],
        "final_waiting": {stage: metrics[f"waiting_{stage}"][-1] for stage in stage_ids},
        "max_abs_independent_global_balance_error": max(abs(value) for value in independent_global_errors),
        "max_abs_independent_terminal_balance_error": max(abs(a - b) for a, b in zip(
            metrics["terminalArrivals"], metrics["delivered"])),
        "max_abs_queue_balance_error": {
            stage: max(abs(value) for value in independent_queue_errors[stage]) for stage in stage_ids
        },
        "repeated_timestamp_count": len(duplicate_events),
        "repeated_timestamp_events": duplicate_events,
        "times": times,
        "delivered_series": metrics["delivered"],
    }


def evaluate_comparison(traces: dict[str, dict[str, Any]], structural_hashes: dict[str, str]) -> dict[str, Any]:
    pairs = []
    for left, right in itertools.combinations(traces, 2):
        if structural_hashes[left] == structural_hashes[right]:
            raise DynamicEvaluationError("compared candidates must have distinct structural hashes")
        a, b = traces[left], traces[right]
        if a["times"] != b["times"]:
            raise DynamicEvaluationError("candidate trajectories use different time grids")
        difference = max(abs(x - y) for x, y in zip(a["delivered_series"], b["delivered_series"]))
        discriminating = difference > TOLERANCE
        pairs.append({"candidate_ids": [left, right],
                      "dynamic_relation": "DISCRIMINATING" if discriminating else "NON_DISCRIMINATING",
                      "max_abs_delivered_difference": difference,
                      "interpretation": ("outputs differ under this scenario" if discriminating
                                         else "structurally distinct alternatives are observationally equivalent under this scenario"),
                      "next_step": (None if discriminating else
                                    "retain both; test a finite input pulse and observe delivery during the recovery tail")})
    return {"status": ("NON_DISCRIMINATING" if any(
                item["dynamic_relation"] == "NON_DISCRIMINATING" for item in pairs
            ) else "DISCRIMINATING_UNDER_SCENARIO"),
            "pairwise_comparisons": pairs, "ranking_performed": False,
            "empirical_adequacy_evaluated": False}


def prepare(args: argparse.Namespace) -> None:
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    composed = json.loads(args.candidates.read_text(encoding="utf-8"))
    composition_report = json.loads(args.composition_report.read_text(encoding="utf-8"))
    support_plan = json.loads(args.support_plan.read_text(encoding="utf-8"))
    if support_plan.get("origin_ref") != plan.get("id"):
        raise DynamicEvaluationError("support plan origin does not match B3 plan")
    verify_composition_provenance(args.plan, args.catalog, args.candidates, composition_report)
    selection = apply_supports(composed, support_plan)
    verify_selection(composed, support_plan, selection)
    validate_scenario(plan, composition_report, composed, selection)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    selection_path = args.output_dir / "molecular-atms-selection.json"
    modelica_path = args.output_dir / "B3MolecularDynamics.mo"
    mos_path = args.output_dir / "run-admissible-candidates.mos"
    selection_path.write_text(json.dumps(selection, indent=2) + "\n", encoding="utf-8")
    modelica_path.write_text(render_evaluation_modelica(plan, composed, selection), encoding="utf-8")
    mos_path.write_text(render_openmodelica_script(plan, composed, selection), encoding="utf-8")
    report = {
        "status": "B3_READY_FOR_DYNAMIC_EXECUTION",
        "plan_sha256": digest(args.plan), "catalog_sha256": digest(args.catalog),
        "support_plan_sha256": digest(args.support_plan),
        "composition_report_sha256": digest(args.composition_report),
        "candidate_document_sha256": digest(args.candidates),
        "selection_sha256": digest(selection_path),
        "evaluator_sha256": digest(Path(__file__)),
        "evaluation_modelica_sha256": digest(modelica_path),
        "openmodelica_script_sha256": digest(mos_path),
        "candidate_ids": selection["candidate_ids"],
        "selected_candidate_ids": [item["candidate_id"] for item in selection["selected"]],
        "rejected_candidate_ids": [item["candidate_id"] for item in selection["rejected"]],
        "simulation_classes": ["B3MolecularDynamics." + class_name(item["candidate_id"])
                               for item in selection["selected"]],
        "synthetic": True, "ranking_performed": False,
        "empirical_adequacy_evaluated": False, "license_status": "DEFERRED_BY_RESEARCHER",
    }
    report_path = args.output_dir / "b3-execution-plan.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


def verify(args: argparse.Namespace) -> None:
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    composed = json.loads(args.candidates.read_text(encoding="utf-8"))
    composition_report = json.loads(args.composition_report.read_text(encoding="utf-8"))
    support_plan = json.loads(args.support_plan.read_text(encoding="utf-8"))
    verify_composition_provenance(args.plan, args.catalog, args.candidates, composition_report)
    report_path = args.output_dir / "b3-execution-plan.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    for key, path in (
        ("plan_sha256", args.plan), ("catalog_sha256", args.catalog),
        ("support_plan_sha256", args.support_plan),
        ("composition_report_sha256", args.composition_report),
        ("candidate_document_sha256", args.candidates),
        ("evaluator_sha256", Path(__file__)),
        ("selection_sha256", args.output_dir / "molecular-atms-selection.json"),
        ("evaluation_modelica_sha256", args.output_dir / "B3MolecularDynamics.mo"),
        ("openmodelica_script_sha256", args.output_dir / "run-admissible-candidates.mos"),
    ):
        if report.get(key) != digest(path):
            raise DynamicEvaluationError(f"{key}: input or generated artifact digest mismatch")
    selection = json.loads((args.output_dir / "molecular-atms-selection.json").read_text(encoding="utf-8"))
    verify_selection(composed, support_plan, selection)
    validate_scenario(plan, composition_report, composed, selection)
    selected_ids = [item["candidate_id"] for item in selection["selected"]]
    rejected_ids = [item["candidate_id"] for item in selection["rejected"]]
    if report.get("selected_candidate_ids") != selected_ids or report.get("rejected_candidate_ids") != rejected_ids:
        raise DynamicEvaluationError("execution plan candidate partition differs from verified ATMS selection")
    mos_text = (args.output_dir / "run-admissible-candidates.mos").read_text(encoding="utf-8")
    for candidate_id in selected_ids:
        if f"simulate(B3MolecularDynamics.{class_name(candidate_id)}," not in mos_text:
            raise DynamicEvaluationError(f"selected candidate is not scheduled: {candidate_id}")
    for candidate_id in rejected_ids:
        if f"simulate(B3MolecularDynamics.{class_name(candidate_id)}," in mos_text:
            raise DynamicEvaluationError(f"rejected candidate is scheduled: {candidate_id}")
    log_text = args.openmodelica_log.read_text(encoding="utf-8", errors="replace")
    for candidate_id in selected_ids:
        expected_check = f"Check of B3MolecularDynamics.{class_name(candidate_id)} completed successfully"
        if expected_check not in log_text:
            raise DynamicEvaluationError(f"OpenModelica did not check {candidate_id} successfully")
    if re.search(r"Error:|Failed to load|Class .* not found", log_text):
        raise DynamicEvaluationError("OpenModelica log contains an error")
    composed_candidates = {item["id"]: item for item in composed["candidates"]}
    structures = {item["id"]: item for item in composed["structures"]}
    traces: dict[str, dict[str, Any]] = {}
    structural_hashes = {}
    for candidate_id in selected_ids:
        candidate = composed_candidates[candidate_id]
        structure = structures[candidate["structure_revision_id"]]
        stage_ids = [item["id"] for item in structure["molecule_instances"]
                     if item["molecule_definition_id"] == plan["roles"]["stage"]]
        trace_path = args.output_dir / f"{result_prefix(candidate_id)}_res.csv"
        traces[candidate_id] = assess_trace(trace_path, stage_ids,
                                            float(plan["simulation"]["start_time"]),
                                            float(plan["simulation"]["stop_time"]),
                                            int(plan["simulation"]["intervals"]))
        traces[candidate_id]["csv_sha256"] = digest(trace_path)
        structural_hashes[candidate_id] = structure["structural_hash"]
    comparison = evaluate_comparison(traces, structural_hashes)
    evidence = {
        "status": "B3_MOLECULAR_DYNAMICS_PASS_SYNTHETIC",
        "candidate_disposition": {
            "retained_and_simulated": selected_ids,
            "rejected_and_not_simulated": rejected_ids,
            "simulated_count": len(traces),
        },
        "dynamic_coherence": {
            "criteria": ["finite outputs", "nondecreasing common time grid; repeated event timestamps allowed",
                         "nonnegative stocks and cumulative quantities",
                         "monotone cumulative deliveries and accepted input",
                         "per-queue arrivals - completions = stock",
                         "terminal arrivals = delivered", "input = delivered + queue stocks"],
            "tolerance": TOLERANCE,
            "all_admissible_candidates_pass": True,
            "candidate_metrics": traces,
        },
        "comparison": comparison,
        "evidence_hashes": {"openmodelica_log_sha256": digest(args.openmodelica_log),
                            "modelica_image": args.image,
                            "evaluation_modelica_sha256": digest(args.output_dir / "B3MolecularDynamics.mo"),
                            "selection_sha256": digest(args.output_dir / "molecular-atms-selection.json")},
        "empirical_or_causal_claim": False,
        "explanatory_adequacy_evaluated": False,
        "license_status": "DEFERRED_BY_RESEARCHER",
    }
    evidence_path = args.output_dir / "b3-dynamic-evaluation.json"
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))


def common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--plan", type=Path, default=ROOT / "data/synthetic/fm_b3_dynamic_plan.json")
    parser.add_argument("--catalog", type=Path, default=ROOT / "data/synthetic/fm_a_structural_candidates.json")
    parser.add_argument("--candidates", type=Path, default=ROOT / "artifacts/fm-b-molecular-composer/composed_candidates.json")
    parser.add_argument("--composition-report", type=Path, default=ROOT / "artifacts/fm-b-molecular-composer/composition-report.json")
    parser.add_argument("--support-plan", type=Path, default=ROOT / "data/synthetic/fm_b3_dynamic_supports.json")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts/fm-b3-molecular-dynamics")


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare")
    common_args(prepare_parser)
    verify_parser = subparsers.add_parser("verify")
    common_args(verify_parser)
    verify_parser.add_argument("--openmodelica-log", type=Path, required=True)
    verify_parser.add_argument("--image", required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args)
    else:
        verify(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
