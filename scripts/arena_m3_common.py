"""Use the recovered M3 policy on the common Arena construction evidence.

The historical M3 trial remains unchanged. This adapter removes its fixed case
names/times from the runtime boundary, not its molecules, parameters or policy.
It prepares three material paths and selects only after their own solver CSVs.
"""
from __future__ import annotations

import json
import math
from hashlib import sha256
from pathlib import Path

from scripts.arena_v0_contract import (
    SUBMISSION_SCHEMA, arm_view, canonical, digest, trace_event, validate_submission,
)
from scripts.arena_m3_prepare import family, require
from scripts.arena_m3_select import decide, model_rows, sample
from scripts.arena_m_visible_pulse import (
    ROOT, backend, public_pulse, stimulus_only_replace,
)
from scripts.arena_m_visible_verify import verify

METHOD = "short-e1-m3-common-construction/0.1"


def prepare(visible):
    view, rate, duration = public_pulse(visible)
    require(visible["resources"].get("max_model_proposals", 0) >= 3 and
            visible["resources"].get("max_simulations", 0) >= 3,
            "M3_REQUIRES_THREE_CANDIDATE_BUDGET")
    cfg, classes, paths = family()
    candidates, models = [], {}
    for n, (key, graph) in sorted(paths.items()):
        ident = f"C{n:02d}"
        name = f"ArenaCommonM3_{ident}"
        text = stimulus_only_replace(backend.render_model(name, graph, cfg, classes),
                                     rate, duration)
        text = "within;\n" + text + "\n"
        candidates.append({"id": ident, "class": name, "graph": graph,
                           "canonical_sha256": "sha256:" + key,
                           "material_queues": n + 2,
                           "modelica_sha256": "sha256:" + sha256(text.encode()).hexdigest()})
        models[ident] = text
    native = {"schema": "igc-arena-m3-common-native/0.1", "arm_id": "M",
              "method": METHOD, "visible_input_sha256": view["input_hash"],
              "registry_sha256": digest(cfg), "candidates": candidates,
              "parameters_fitted": False, "role_projection": "ASSUMED_NOT_IDENTIFIED",
              "max_best_rmse_items": 0.02, "min_gap_rmse_items": 0.035}
    submission = {"schema": SUBMISSION_SCHEMA, "arm_id": "M",
                  "round_id": visible["round_id"], "iteration": 0,
                  "parent_revision_id": None, "native_artifact_sha256": digest(native),
                  "method_version": METHOD,
                  "hypothesis_ids": ["M-" + c["canonical_sha256"][7:19] for c in candidates],
                  "status": "PROPOSED", "unknowns": ["NOT_SIMULATED", "NOT_SELECTED"],
                  "assumption_ids": ["FIXED_E1_PARAMETERS", "ASSUMED_TYPED_ROLE_PROJECTION"],
                  "evidence_refs": [visible["source_snapshot_hash"]],
                  "notes": "Three material paths; information-only aliases remain unidentifiable."}
    validate_submission(view, submission)
    event = trace_event(arm_id="M", round_id=visible["round_id"],
                        event_type="HYPOTHESIS_PROPOSED", iteration=0,
                        source_hash=view["input_hash"], payload_hash=digest(submission))
    return {"native": native, "models": models, "submission": submission, "event": event}


def write_models(prepared, folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=False)
    for candidate in prepared["native"]["candidates"]:
        (folder / (candidate["class"] + ".mo")).write_bytes(
            prepared["models"][candidate["id"]].encode("utf-8"))
    (folder / "manifest.json").write_bytes(canonical(prepared["native"]) + b"\n")


def evaluate(visible, prepared, csv_root):
    # Rebind the exact candidate family to the current construction input.
    require(prepared == prepare(visible), "M3_COMMON_PREPARATION_CHANGED")
    csv_root = Path(csv_root)
    trace_manifest = json.loads((csv_root / "manifest.json").read_text(encoding="utf-8"))
    require(trace_manifest == prepared["native"], "M3_COMMON_TRACE_INPUT_MISMATCH")
    catalog = json.loads((ROOT / "experiments/e0/catalog.json").read_text())
    observations = visible["construction"]["observations"]
    scores, traces = [], {}
    for c in prepared["native"]["candidates"]:
        model = csv_root / (c["class"] + ".mo")
        require("sha256:" + sha256(model.read_bytes()).hexdigest() == c["modelica_sha256"],
                "M3_COMMON_MODELICA_CHANGED")
        csv = csv_root / (c["id"].lower() + "_res.csv")
        rows = model_rows(csv)
        check = verify(rows, visible, {"arm_id": "M",
            "method": "short-e1-one-minimal-molecular-candidate/0.1", "graph": c["graph"]}, catalog)
        predictions = sample(rows, [o["t"] for o in observations])
        rmse = math.sqrt(sum((p-o["delivered"])**2 for p,o in zip(predictions,observations)) / len(observations))
        scores.append({"id": c["id"], "material_queues": c["material_queues"],
                       "rmse_items": rmse, "predicted_construction": predictions,
                       "max_material_balance": check["max_material_balance_residual"]})
        traces[c["id"]] = "sha256:" + sha256(csv.read_bytes()).hexdigest()
    choice = decide(scores, min_gap=0.035, max_best=0.02)
    return {**choice, "scored_candidates": scores, "trace_sha256": traces,
            "construction_input_hash": digest(visible), "g2": "CSV_CHECKED_CONDITIONALLY",
            "g3": "CONSTRUCTION_FIXED_PARAMETER_SELECTION",
            "parameters_fitted": False, "reserved_evaluation": "NOT_RUN",
            "used_cross_arm_information": False}
