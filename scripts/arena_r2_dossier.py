"""PT-01: reconstruct authentic R1 and freeze strictly own-arm R2 feedback.

All inputs are *downloaded* R1 GitHub Actions artifacts. No provider, solver,
rival model leakage, synthetic repairs or fabricated second decisions.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import zipfile

from scripts.arena_r1_buffalo_postonly import ORIGINAL_NATIVE_SHA, SHARED_SOURCE
from scripts.arena_r1_buffalo_initial import build as b_visible_from_primary
from scripts.arena_v0_contract import canonical, digest

SCHEMA = "igc-arena-r2-expediente/0.1"
B_SCHEMA = "igc-arena-r2-b-own-build-failure/0.1"
B_NATIVE_ENTRY = "r1-b-live/native-output.json"
B_LOG_ENTRY = "r1-b-physical/omc.log"
R1_REPORT_ENTRY = "r1-three-arm-initial-report.json"
B_VISIBLE_ENTRY = "r1-b-visible.json"
B_NATIVE = "sha256:" + ORIGINAL_NATIVE_SHA
# Pinned to the *historical, captured solver log*, not a reproduction guess.
VALID_ENDING = "Failed to build model: BuffaloNative_02b3b170558b"

def require(ok: bool, code: str) -> None:
    if not ok:
        raise ValueError(code)

def _json(raw: bytes):
    return json.loads(raw.decode("utf-8"))

def _sha(raw: bytes) -> str:
    return "sha256:" + sha256(raw).hexdigest()

def _read_zip(z: zipfile.ZipFile, path: str) -> bytes:
    require(path in z.namelist() and not path.startswith("/"), "R2_MISSING_R1_ARCHIVE_ENTRY")
    return z.read(path)

def prepare(primary: dict, artifact_zip: Path, adjudication: dict) -> dict:
    with zipfile.ZipFile(artifact_zip) as z:
        native_bytes = _read_zip(z, B_NATIVE_ENTRY)
        log_bytes = _read_zip(z, B_LOG_ENTRY)
        original_report = _json(_read_zip(z, R1_REPORT_ENTRY))
        b_visible_bytes = _read_zip(z, B_VISIBLE_ENTRY)
        raw_receipt = _json(_read_zip(z, "r1-b-live/receipt.json"))
        raw_reply = _read_zip(z, "r1-b-live/cloudflare-raw.json")
        original_g0 = _json(_read_zip(z, "r1-b-physical/pre-physical.json"))
    visible = _json(b_visible_bytes)
    require(_sha(native_bytes) == B_NATIVE, "R2_WRONG_BUFFALO_PARENT_BYTES")
    require(_sha(raw_reply) == original_report["B"]["provider"]["raw_response_sha256"],
            "R2_TAMPERED_REAL_PROVIDER_REPLY")
    require(digest(visible) == original_report["B"]["provider"]["visible_input_sha256"],
            "R2_WRONG_ORIGINAL_VISIBLE_BYTES")
    require(visible == b_visible_from_primary(primary), "R2_PRIMARY_EVIDENCE_OR_B_PROMPT_DRIFT")
    require(visible["source_snapshot_hash"] == SHARED_SOURCE and
            original_report["source_snapshot_hash"] == SHARED_SOURCE and
            adjudication["source_snapshot_hash"] == SHARED_SOURCE,
            "R2_WRONG_SOURCE_SNAPSHOT")
    require(adjudication["schema"] == "igc-arena-r1-initial-adjudicated/0.1"
            and adjudication["status"] == "R1_INITIAL_THREE_ARMS_ATTEMPTED_B_G1_NEGATIVE",
            "R2_NOT_POSTONLY_R1_ADJUDICATION")
    require(adjudication["B"]["initial_native_sha256"] == B_NATIVE and
            original_report["B"]["initial_native_sha256"] == B_NATIVE,
            "R2_R1_B_NATIVE_IDENTITY_LOST")
    require(adjudication["B"]["g1"]["g1_status"] == "FAIL_UNANCHORED_ALGEBRAIC_IDENTITY"
            and adjudication["B"]["g2"] == "FAILED_TO_BUILD_NO_PHYSICAL_SERIES"
            and adjudication["B"]["g3"] == "NOT_COMPUTABLE",
            "R2_R1_NOT_NEGATIVE")
    require(adjudication["D"] == original_report["D"] and
            adjudication["M"] == original_report["M"],
            "R2_HISTORIC_D_M_STATE_TAMPERED")
    require(adjudication["B"]["provider"]["provider_calls_started"] == 1 and
            raw_receipt["live_provider_calls"] == 1 and
            raw_receipt["original_upstream_modified"] is False,
            "R2_ORIGINAL_NOT_SINGLE_NATIVE_INFERENCE")
    require(original_g0["g0_status"] == "TRANSLATED_CONDITIONALLY",
            "R2_ORIGINAL_G0_SCOPE_DRIFT")
    require(VALID_ENDING in log_bytes.decode("utf-8", errors="strict"),
            "R2_NOT_REAL_ORIGINAL_BUILD_FAILURE")
    require(len(adjudication["D"]["candidates"]) == 6 and
            len(adjudication["M"]["candidates"]) == 3 and
            adjudication["M"]["decision"]["status"] == "ABSTAIN",
            "R2_NOT_R1_M3_ABSTENTION")
    log = log_bytes.decode("utf-8")
    # No postonly diagnosis in the model's feedback. It is held for evaluator.
    b_feedback = {
        "schema": B_SCHEMA, "arm_id": "B", "round_id": visible["round_id"],
        "source_snapshot_hash": SHARED_SOURCE,
        "parent_native_bytes_sha256": B_NATIVE,
        "parent_solver_log_bytes_sha256": _sha(log_bytes),
        "native_translation": "CONDITIONAL_WITH_DECLARED_ASSUMPTIONS",
        "physical_result": "SIMULATION_BUILD_FAILED",
        "has_solver_trajectory": False, "g3": "NOT_COMPUTABLE",
        "own_openmodelica_log": log,
        "instruction": (
            "Review your own unchanged native proposal in light of this actual "
            "OpenModelica run. Independently decide whether to revise your model, "
            "retain it with justified uncertainty, or abstain. No repair, "
            "equation location, alternative mechanism or claimed causal truth "
            "is supplied by the evaluator."
        )
    }
    for key in ("mathematical_underdetermination", "capacity_constrained_throughput",
                "congestion_multiplier", "product_of_capacity_effects",
                "pulse_shape_discrepancy", "rmse_all_items", "candidate_id"):
        require(key not in json.dumps(b_feedback), "R2_B_DIAGNOSIS_OR_RIVAL_LEAK")
    d_package = {
        "schema": "igc-arena-r2-arm-own-state/0.1",
        "arm_id": "D", "source_snapshot_hash": SHARED_SOURCE,
        "r1_native_state": "SIX_INDEPENDENT_CANDIDATES_NOT_ONE_SELECTED_PARENT",
        "r1_candidates": adjudication["D"]["candidates"],
        "r1_status": adjudication["D"]["status"],
        "requested_decision": "RATIFY_ALTERNATIVES_OR_EXPLICITLY_REVISE_WITH_EVIDENCE",
        "r2_decision": "PENDING_NOT_FABRICATED",
        "new_observations": False
    }
    m_package = {
        "schema": "igc-arena-r2-arm-own-state/0.1",
        "arm_id": "M", "source_snapshot_hash": SHARED_SOURCE,
        "r1_candidates": adjudication["M"]["candidates"],
        "r1_decision": adjudication["M"]["decision"],
        "r1_status": adjudication["M"]["status"],
        "chosen_parent": None,
        "requested_decision": "RATIFY_ABSTENTION_OR_DECLARE_SEPARATE_NEW_POLICY",
        "r2_decision": "PENDING_NOT_FABRICATED",
        "new_observations": False
    }
    manifest = {
        "schema": SCHEMA, "investigation_id": visible["investigation_id"],
        "round_id": visible["round_id"], "source_snapshot_hash": SHARED_SOURCE,
        "r1_method_attempts": {"D":6, "M":3, "B":1},
        "r1_outcomes": {"D":"SIX_G2_REAL", "M":"THREE_G2_REAL_M3_ABSTAIN",
                        "B":"NATIVE_G1_NEGATIVE_NO_G2_NO_RMSE"},
        "b_parent_native_bytes_sha256": B_NATIVE,
        "b_original_log_bytes_sha256": _sha(log_bytes),
        "b_raw_provider_reply_bytes_sha256": _sha(raw_reply),
        "r1_adjudicated_report_sha256": digest(adjudication),
        "r1_initial_report_sha256": digest(original_report),
        "r1_visible_source_sha256": digest(visible),
        "method_private_hashes": {
            "B_feedback": digest(b_feedback), "D_own": digest(d_package),
            "M_own": digest(m_package)},
        "producer_calls": 0, "solver_calls": 0,
        "r2_revision": "NOT_INFERRED",
        "next_provider_authorization": "REQUIRED_SEPARATELY",
        "epistemic_scope": "PT01_RECONSTRUCTION_ONLY"
    }
    return {"b_native_bytes":native_bytes,"b_visible":visible,
            "b_feedback":b_feedback,"d_own":d_package,"m_own":m_package,
            "manifest":manifest}

def save(bundle: dict, folder: Path):
    require(not folder.exists(), "R2_EXPEDIENTE_OUTPUT_EXISTS")
    folder.mkdir(parents=True)
    (folder/"b-parent-native.json").write_bytes(bundle["b_native_bytes"])
    for name, key in (("b-visible.json","b_visible"),
                      ("b-own-feedback.json","b_feedback"),
                      ("d-own-state.json","d_own"),
                      ("m-own-state.json","m_own"),
                      ("manifest.json","manifest")):
        (folder/name).write_bytes(canonical(bundle[key])+b"\n")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--archive",type=Path,required=True)
    p.add_argument("--adjudication",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    data=prepare(_json(args.source.read_bytes()),args.archive,_json(args.adjudication.read_bytes()))
    save(data,args.out)
    print(json.dumps({"status":"R2_PT01_READY_NO_INFERENCE",
                      "source":SHARED_SOURCE,
                      "parent_native":B_NATIVE,
                      "manifest_hash":digest(data["manifest"])}))

if __name__=="__main__":
    main()
