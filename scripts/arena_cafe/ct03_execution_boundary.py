"""CT-03: verify third-party runner and archive witnesses WITHOUT running a solver.

A hash/receipt/log bundle, even an internally consistent one, cannot prove an
OpenModelica execution. Detached signatures authenticate the statement against
a public key whose fingerprint is pinned in a separately supplied trust registry.
A real deployment MUST keep private signing keys / registry outside producer
workspaces and establish the signer's independence externally. Tests with
temporary keys demonstrate verification mechanics ONLY, not scientific G2.

This module DOES NOT create signatures, select worlds, call OMC/HTTP, or read
reserved evaluator truth. Archives require a distinct trusted authority.
"""
from __future__ import annotations
import base64
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

from scripts.arena_v0_contract import canonical, digest
from scripts.arena_cafe.ct_feedback_bridge import require
from scripts.arena_cafe.ct03_m_construction_diagnostic import (
    _check_manifest, _check_receipt, _sample, sha_bytes,
)
from scripts.arena_cafe.ct03_prospective_lock import verify_locked

SCHEMA = "igc-ct03-signed-boundary-witness/1.0"
REGISTRY = "igc-ct03-external-trust-anchors/1.0"
KINDS = ("PHYSICAL_OMC", "LOCK_ARCHIVE")
SHA = re.compile(r"sha256:[0-9a-f]{64}\Z")
JOB = re.compile(r"[a-zA-Z0-9_-]{8,128}\Z")
RUN = re.compile(r"https://github\.com/yudocyudoc/IGC/actions/runs/[0-9]+\Z")


def sha(x):
    return type(x) is str and SHA.fullmatch(x) is not None


def exact(x, fields, error):
    require(type(x) is dict and set(x) == set(fields), error)


def disjoint(producer_root, *protected_paths):
    """Reject privileged files placed within / above producer workspace."""
    producer = Path(producer_root).resolve(strict=True)
    require(producer.is_dir(), "CT03_PRODUCER_ROOT_REQUIRED")
    for item in protected_paths:
        protected = Path(item).resolve(strict=True)
        require(producer != protected and
                producer not in protected.parents and
                protected not in producer.parents,
                "CT03_TRUST_OR_EVALUATOR_BYTES_INSIDE_PRODUCER_BOUNDARY")


def _verify_detached(statement, signature64, public_key: Path):
    require(type(signature64) is str and len(signature64) < 10000,
            "CT03_SIGNATURE_FORMAT")
    try:
        signature = base64.b64decode(signature64, validate=True)
    except (ValueError, base64.binascii.Error) as ex:
        raise ValueError("CT03_SIGNATURE_BASE64_INVALID") from ex
    require(0 < len(signature) <= 4096, "CT03_SIGNATURE_LENGTH_INVALID")
    # OpenSSL is used as an external verifier, never as a signer in this module.
    # Temporary files are not produced beneath a repository or producer root.
    with tempfile.TemporaryDirectory(prefix="ct03-verify-") as folder:
        data = Path(folder) / "statement.json"
        sig = Path(folder) / "witness.sig"
        data.write_bytes(canonical(statement))
        sig.write_bytes(signature)
        try:
            process = subprocess.run(
                ["openssl", "dgst", "-sha256", "-verify", str(public_key),
                 "-signature", str(sig), str(data)],
                capture_output=True, text=True, timeout=15, check=False)
        except (OSError, subprocess.TimeoutExpired) as ex:
            raise ValueError("CT03_SIGNATURE_VERIFIER_UNAVAILABLE") from ex
    require(process.returncode == 0 and
            "Verified OK" in process.stdout, "CT03_SIGNATURE_NOT_VERIFIED")


def verify_witness(witness, *, trust_registry, public_key, producer_root, kind):
    """Typed detached-signature boundary; never trust a self-supplied key alone."""
    require(kind in KINDS, "CT03_INVALID_WITNESS_KIND")
    disjoint(producer_root, trust_registry, public_key)
    exact(witness, ("schema", "purpose", "authority_id", "statement",
                    "statement_sha256", "signature_base64"), "CT03_WITNESS_FIELDS")
    require(witness["schema"] == SCHEMA and witness["purpose"] == kind and
            type(witness["authority_id"]) is str and
            type(witness["statement"]) is dict and
            witness["statement_sha256"] == digest(witness["statement"]),
            "CT03_WITNESS_SCOPE_OR_DIGEST_MISMATCH")
    cfg = json.loads(Path(trust_registry).read_text(encoding="utf-8"))
    exact(cfg, ("schema", "authorities"), "CT03_TRUST_REGISTRY_FIELDS")
    require(cfg["schema"] == REGISTRY and
            type(cfg["authorities"]) is list and cfg["authorities"],
            "CT03_NO_EXPLICIT_EXTERNAL_TRUST_ANCHOR")
    seen = set()
    key_roles = {}
    matches = []
    for authority in cfg["authorities"]:
        exact(authority, ("id", "purpose", "public_key_sha256"),
              "CT03_TRUST_AUTHORITY_FIELDS")
        require(type(authority["id"]) is str and authority["purpose"] in KINDS and
                sha(authority["public_key_sha256"]), "CT03_INVALID_TRUST_AUTHORITY")
        key = (authority["id"], authority["purpose"])
        require(key not in seen, "CT03_DUPLICATE_TRUST_AUTHORITY")
        seen.add(key)
        # Separating labels without separating key material is not a
        # distinct trust boundary. Reject an authority key reused by roles.
        fingerprint = authority["public_key_sha256"]
        require(fingerprint not in key_roles or
                key_roles[fingerprint] == authority["purpose"],
                "CT03_RUNNER_AND_ARCHIVIST_SHARE_SIGNING_KEY")
        key_roles[fingerprint] = authority["purpose"]
        if key == (witness["authority_id"], kind):
            matches.append(authority)
    require(len(matches) == 1, "CT03_SIGNER_NOT_REGISTERED_FOR_ROLE")
    pem = Path(public_key).read_bytes()
    require(sha_bytes(pem) == matches[0]["public_key_sha256"],
            "CT03_SIGNER_PUBLIC_KEY_NOT_PINNED")
    # Credential configuration alone is not proof of separate actor or runner.
    _verify_detached(witness["statement"], witness["signature_base64"],
                     Path(public_key))
    return witness["statement"]


def verify_runner(*, witness, trust_registry, public_key, producer_root,
                  manifest, parent, receipt, modelica_file, script_file,
                  csv_file, solver_log):
    statement = verify_witness(
        witness, trust_registry=trust_registry, public_key=public_key,
        producer_root=producer_root, kind="PHYSICAL_OMC")
    _check_manifest(manifest, parent)
    mo = Path(modelica_file).read_bytes()
    script = Path(script_file).read_bytes()
    csv = Path(csv_file).read_bytes()
    log = Path(solver_log).read_bytes()
    require(len(log) > 0, "CT03_RUNNER_SOLVER_LOG_REQUIRED")
    _check_receipt(receipt, parent, manifest, mo, csv, script,
                   Path(csv_file).name)
    _sample(csv, "deliveredTotal")
    exact(statement, ("case_id", "world_public_id", "arm", "round_kind",
                      "candidate_id", "parent_hash", "receipt_sha256", "script_sha256",
                      "modelica_sha256", "csv_sha256", "solver_log_sha256",
                      "command", "csv_filename", "solver_image",
                      "runner_job_id", "workflow_run_url", "exit_code"),
          "CT03_RUNNER_STATEMENT_FIELDS")
    require(statement["case_id"] == "CT-03" and
            type(statement["world_public_id"]) is str and
            re.fullmatch(r"[A-Za-z0-9_-]{1,64}", statement["world_public_id"]) and
            statement["arm"] == "M" and
            statement["round_kind"] == "initial" and
            statement["candidate_id"] == parent["canonical_sha256"] and
            statement["parent_hash"] == parent["full_ast_sha256"] and
            statement["receipt_sha256"] == digest(receipt) and
            statement["script_sha256"] == sha_bytes(script) and
            statement["modelica_sha256"] == sha_bytes(mo) and
            statement["csv_sha256"] == sha_bytes(csv) and
            statement["solver_log_sha256"] == sha_bytes(log) and
            statement["command"] == receipt["simulation_command"] and
            statement["csv_filename"] == Path(csv_file).name and
            statement["solver_image"] ==
                "openmodelica/openmodelica:v1.26.5-minimal" and
            type(statement["runner_job_id"]) is str and
            JOB.fullmatch(statement["runner_job_id"]) and
            type(statement["workflow_run_url"]) is str and
            RUN.fullmatch(statement["workflow_run_url"]) and
            type(statement["exit_code"]) is int and
            statement["exit_code"] == receipt["exit_code"] == 0,
            "CT03_RUNNER_SIGNED_COMMAND_LOG_OR_PARENT_MISMATCH")
    return {
        "status": "THIRD_PARTY_SIGNATURE_AND_BYTES_VERIFIED_DEPLOYMENT_INDEPENDENCE_NOT_CERTIFIED",
        "authority_id": witness["authority_id"], "case_id": "CT-03",
        "world_public_id": statement["world_public_id"],
        "candidate_id": statement["candidate_id"],
        "parent_hash": statement["parent_hash"],
        "round_kind": statement["round_kind"],
        "native_sha256": statement["modelica_sha256"],
        "trace_sha256": statement["csv_sha256"],
        "receipt_sha256": statement["receipt_sha256"],
        "signed_statement_sha256": witness["statement_sha256"],
        "runner_job_id_claim": statement["runner_job_id"],
        "workflow_run_url_claim": statement["workflow_run_url"],
        "external_identity_verification": "REQUIRES_OUT_OF_BAND_RUNNER_CONTROL",
        "authentic_solver_execution_proven": False,
        "provider_calls": 0, "omc_executed_by_verifier": 0,
    }


def verify_archive(*, lock, witness, trust_registry, public_key, producer_root):
    """Archive attests locked bytes before any evaluator-only reveal is allowed."""
    statement = verify_witness(
        witness, trust_registry=trust_registry, public_key=public_key,
        producer_root=producer_root, kind="LOCK_ARCHIVE")
    verify_locked(lock)
    exact(statement, ("case_id", "world_public_id", "lock_sha256",
                      "protocol_sha256", "world_commitment_sha256",
                      "archive_id", "archived_before_evaluator_access"),
          "CT03_ARCHIVE_STATEMENT_FIELDS")
    require(statement["case_id"] == "CT-03" and
            statement["world_public_id"] == lock["world_public_id"] and
            statement["lock_sha256"] == lock["lock_sha256"] and
            statement["protocol_sha256"] == lock["protocol_sha256"] and
            statement["world_commitment_sha256"] ==
                lock["world_commitment_sha256"] and
            type(statement["archive_id"]) is str and
            JOB.fullmatch(statement["archive_id"]) and
            statement["archived_before_evaluator_access"] is True,
            "CT03_ARCHIVE_SIGNED_LOCK_MISMATCH")
    return {
        "status": "LOCK_ARCHIVE_SIGNATURE_AND_BYTES_VERIFIED_NO_TRUTH_READ",
        "archive_id": statement["archive_id"],
        "lock_sha256": lock["lock_sha256"],
        "archive_authority": witness["authority_id"],
        "operator_custody_independence": "NOT_ESTABLISHED_BY_SIGNATURE_ALONE",
        "reserved_truth_opened": False, "provider_calls": 0, "omc_executed": 0,
    }
