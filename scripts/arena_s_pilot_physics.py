"""Bounded physical-input and loaded-composer contracts for S/D pilot.

This validates input identity, not empirical adequacy or independent provenance.
Requires the actual Modelica source loaded at /composer to be supplied at verify.
"""
from __future__ import annotations

import csv
from hashlib import sha256
import math
from pathlib import Path

from .arena_sp_producers import ProviderError
from .compose_molecular_candidates import render_modelica

COMPOSER = "GeneratedMolecularCandidates.mo"
INPUT_ABS_TOL = 0.005


def require(ok: bool, code: str) -> None:
    if not ok:
        raise ProviderError(code)


def composer_bytes(plan: dict, composed: dict) -> bytes:
    return render_modelica(plan, composed).encode("utf-8")


def composer_hash(plan: dict, composed: dict) -> str:
    return "sha256:" + sha256(composer_bytes(plan, composed)).hexdigest()


def verify_loaded_composer(path: Path | None, expected_hash: str,
                           plan: dict, composed: dict) -> None:
    require(path is not None and path.is_file(),
            "LOADED_COMPOSER_FILE_REQUIRED")
    require(path.name == COMPOSER and path.read_bytes() == composer_bytes(plan, composed)
            and expected_hash == composer_hash(plan, composed),
            "LOADED_COMPOSER_NOT_CALIBRATED_MODEL")


def pulse_expected_accepted(plan: dict, time: float) -> float:
    """Only the pilot's single rectangular pulse with known zero initial input."""
    profile = plan.get("external_input", {}).get("profile")
    sim = plan.get("simulation", {})
    require(isinstance(profile, dict) and profile.get("kind") == "pulse",
            "PILOT_REQUIRES_PULSE_INPUT")
    try:
        amplitude = float(profile["amplitude"])
        offset = float(profile["offset"])
        period = float(profile["period"])
        width = float(profile["width_percent"])
        start = float(profile["start_time"])
        stop = float(sim["stop_time"])
        initial = float(sim["start_time"])
        declared = float(plan["external_input"]["value"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ProviderError("PILOT_INVALID_PULSE_DECLARATION") from exc
    vals = [amplitude,offset,period,width,start,stop,initial,declared,time]
    require(all(math.isfinite(v) for v in vals)
            and amplitude > 0 and offset == 0 and start == 0
            and initial == 0 and stop > 0 and period > stop
            and 0 < width < 100 and amplitude == declared
            and (duration := period * width / 100) < stop,
            "PILOT_PULSE_OUTSIDE_VERIFIED_CLASS")
    return amplitude * min(max(time, 0.0), duration)


def verify_physical_input(trace_path: Path, plan: dict) -> None:
    with trace_path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    require(bool(rows), "PILOT_EMPTY_TRACE")
    # assess_trace has already verified time progression, physical stocks and
    # finite values. This independently validates the declared exogenous input.
    for row in rows:
        t = float(row["time"])
        actual = float(row["acceptedTotal"])
        expected = pulse_expected_accepted(plan, t)
        require(math.isfinite(actual) and
                abs(actual - expected) <= INPUT_ABS_TOL,
                "PILOT_INPUT_TRACE_MISMATCH")
