"""CT-00: fail-closed gate for the inherited 14-simulation M3 regression.

Compare numerical Git blobs AND the workflow's solver/library configuration
against the historically audited main commit. Do not use PR changed-file lists:
they include old commits unrelated to the current numerical identity.
No solver or provider is invoked by this module.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

BASELINE = "5e2b5505a9224effe1b5242a3af61663b53aaa5d"
WORKFLOW = ".github/workflows/arena-recovered-capabilities.yml"
EXACT = frozenset({
    "requirements-f0.lock.txt",
    "scripts/arena_m3_prepare.py",
    "scripts/arena_m3_param_shift.py",
    "scripts/arena_m3_adjudicate.py",
    "scripts/arena_m3_select.py",
    "scripts/arena_m3_common.py",
    "scripts/arena_m_visible_pulse.py",
    "scripts/arena_m_visible_verify.py",
    "scripts/arena_v0_first_round.py",
    "scripts/arena_v0_common_evidence.py",
    "scripts/arena_v0_contract.py",
    "scripts/arena_d_v01.py",
    "experiments/e0/catalog.json",
    "experiments/e1/composer.py",
    "experiments/e1/backend.py",
    "experiments/e1/registry.base.json",
    "data/synthetic/arena_v0_primary_construction.json",
    "data/synthetic/arena_v0_declared_d_assumptions.json",
})
PREFIXES = ("src/modelica/",)
RUNTIME_PATTERNS = (
    r"openmodelica/openmodelica:v[0-9.]+-minimal",
    r"--branch v[0-9.]+",
    r"method=\\\"[A-Za-z0-9]+\\\"",
    r"tolerance=[0-9.eE-]+",
    r"stopTime=[0-9.]+",
    r"numberOfIntervals=[0-9]+",
)


def git(*args: str, cwd: Path | None = None) -> bytes:
    return subprocess.check_output(["git", *args], cwd=cwd, stderr=subprocess.PIPE)


def dependencies(ref: str, repo: Path) -> dict[str, str]:
    raw = git("ls-tree", "-rz", ref, cwd=repo)
    found = {}
    for entry in raw.split(b"\0"):
        if not entry:
            continue
        left, path = entry.split(b"\t", 1)
        name = path.decode("utf-8")
        if name in EXACT or any(name.startswith(p) for p in PREFIXES):
            found[name] = left.rsplit(b" ", 1)[1].decode("ascii")
    if not EXACT.issubset(found) or not any(k.startswith("src/modelica/") for k in found):
        raise ValueError("CT00_INCOMPLETE_NUMERICAL_DEPENDENCY_CLOSURE")
    wf = git("show", f"{ref}:{WORKFLOW}", cwd=repo).decode("utf-8")
    tokens = []
    for pattern in RUNTIME_PATTERNS:
        terms = re.findall(pattern, wf)
        if not terms:
            raise ValueError("CT00_SOLVER_RUNTIME_CONFIG_UNRECOGNIZED:" + pattern)
        tokens += sorted(terms)
    found["@runtime_omc_libraries_solver_settings"] = hashlib.sha256(
        json.dumps(tokens, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return found


def decision(repo: Path, baseline: str = BASELINE, head: str = "HEAD", *,
             requested: bool = False, budget: int = 0) -> dict:
    before = dependencies(baseline, repo)
    after = dependencies(head, repo)
    changed = sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))
    if not changed:
        status = "REUSE_HISTORICAL_NUMERIC_IDENTITY_NO_OMC"
    elif requested and budget == 14:
        status = "PHYSICAL_M3_AUTHORIZED_EXACTLY_14"
    else:
        status = "BLOCKED_NUMERICAL_DRIFT_REQUIRES_EXPLICIT_BUDGET"
    return {
        "schema": "igc-ct00-numeric-gate/1.0",
        "reference": baseline, "head": head, "numerical_changed": bool(changed),
        "changed_dependencies": changed,
        "reference_digest": hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest(),
        "head_digest": hashlib.sha256(json.dumps(after, sort_keys=True).encode()).hexdigest(),
        "physical_authorized": status == "PHYSICAL_M3_AUTHORIZED_EXACTLY_14",
        "status": status,
        "planned_simulations": 14 if status == "PHYSICAL_M3_AUTHORIZED_EXACTLY_14" else 0,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--baseline", default=BASELINE)
    p.add_argument("--head", default="HEAD")
    p.add_argument("--repo", type=Path, default=Path("."))
    p.add_argument("--run-physical", action="store_true")
    p.add_argument("--budget", type=int, default=0)
    p.add_argument("--report", type=Path)
    a = p.parse_args()
    result = decision(a.repo, a.baseline, a.head, requested=a.run_physical, budget=a.budget)
    if a.report:
        a.report.parent.mkdir(parents=True, exist_ok=True)
        a.report.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    output = os.getenv("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as f:
            f.write("physical_authorized=" + str(result["physical_authorized"]).lower() + "\n")
            f.write("status=" + result["status"] + "\n")
    print(json.dumps(result, sort_keys=True))
    return 1 if result["status"].startswith("BLOCKED_") else 0


if __name__ == "__main__":
    raise SystemExit(main())
