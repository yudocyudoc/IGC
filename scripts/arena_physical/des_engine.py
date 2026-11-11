#!/usr/bin/env python3
"""CAF-01 generic, independent event-calendar engine: PREPARATORY CODE ONLY.

NO CAF-01 world is configured, sealed or executed by this module or its CI.
No source/reliance on the D grammar, Buffalo, E1, Modelica or candidate fits.
The proposed event order is COMPLETIONS -> ACCEPTANCES -> SERVICE_STARTS
(downstream to upstream); this policy requires researcher/Astra approval.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
from hmac import compare_digest
from heapq import heappop, heappush
from pathlib import Path
import json

SCHEMA = "igc-caf01-des-private-world/0.1"
TIE_POLICY = "COMPLETE_THEN_ACCEPT_THEN_START_DOWNSTREAM_FIRST"
ENGINE_STATUS = "PREPARATION_ONLY_NO_PRIVATE_WORLD_SELECTED"
MAX_STAGES = 6
MAX_EVENTS = 10000


class DESBlocked(ValueError):
    pass


def require(ok, code):
    if not ok:
        raise DESBlocked(code)


def quantity(value):
    """Exact rational numeric input; strings allow explicit fractions."""
    require(type(value) in (int, str, Fraction), "DES_BAD_EXACT_QUANTITY")
    try:
        result = Fraction(value)
    except (ValueError, ZeroDivisionError, TypeError, OverflowError) as exc:
        raise DESBlocked("DES_BAD_EXACT_QUANTITY") from exc
    require(result >= 0, "DES_NEGATIVE_QUANTITY")
    return result


def validate_private_config(config):
    """Structural validation only: no real parameters are selected here."""
    require(type(config) is dict and
            set(config) == {"schema", "tie_policy", "stages"},
            "DES_PRIVATE_CONFIG_SCHEMA")
    require(config["schema"] == SCHEMA, "DES_PRIVATE_SCHEMA_VERSION")
    require(config["tie_policy"] == TIE_POLICY, "DES_UNAPPROVED_TIE_POLICY")
    stages = config["stages"]
    require(type(stages) is list and 1 <= len(stages) <= MAX_STAGES,
            "DES_STAGE_COUNT_OUT_OF_SCOPE")
    for entry in stages:
        require(type(entry) is dict and
                set(entry) == {"servers", "service_minutes"},
                "DES_STAGE_KEYS")
        require(type(entry["servers"]) is int and 1 <= entry["servers"] <= 20,
                "DES_SERVERS_OUT_OF_SCOPE")
        duration = quantity(entry["service_minutes"])
        require(duration > 0, "DES_ZERO_SERVICE_TIME")
    return tuple((x["servers"], quantity(x["service_minutes"])) for x in stages)


def half_open_arrivals(rate_per_minute, duration_minutes):
    """t_j = (j+1/2)/rate, strictly earlier than pulse end.

    The schedule is exactly rational, not rounded to a floating point grid.
    """
    rate, duration = quantity(rate_per_minute), quantity(duration_minutes)
    require(rate > 0 and duration > 0, "DES_BAD_PULSE")
    result = []
    j = 0
    while True:
        t = Fraction(2*j+1, 2) / rate
        if t >= duration:
            break
        require(j < MAX_EVENTS, "DES_ARRIVAL_BUDGET_EXCEEDED")
        result.append(t)
        j += 1
    return tuple(result)


@dataclass(frozen=True)
class Snapshot:
    t_min: Fraction
    accepted_cum_orders: int
    delivered_cum_orders: int
    pending_orders: int
    stage_waiting: tuple[int, ...]
    stage_in_service: tuple[int, ...]


def run_toy_engine(config, arrivals, observations):
    """Pure event simulation for *test fixtures*, not a CAF-01 run command.

    Future authorized CAF-01 execution needs a separate sealed, gated runner.
    All returned per-stage data is PRIVATE diagnostic material, never public
    production evidence. No randomness or hidden state inferred from arms.
    """
    spec = validate_private_config(config)
    arrivals = tuple(quantity(t) for t in arrivals)
    observations = tuple(quantity(t) for t in observations)
    require(len(arrivals) <= MAX_EVENTS, "DES_TOO_MANY_ARRIVALS")
    require(all(b > a for a, b in zip(arrivals, arrivals[1:])),
            "DES_NONINCREASING_ARRIVALS")
    require(observations and observations[0] == 0 and
            all(b > a for a, b in zip(observations, observations[1:])),
            "DES_INVALID_OBSERVATIONS")
    require(all(t <= observations[-1] for t in arrivals), "DES_ARRIVAL_AFTER_HORIZON")

    n = len(spec)
    waiting = [deque() for _ in spec]
    active = [set() for _ in spec]
    events = []
    serial = 0
    for order, time in enumerate(arrivals):
        # priority 0=completion, 1=acceptance at identical time.
        heappush(events, (time, 1, serial, "accept", -1, order))
        serial += 1

    accepted = delivered = 0
    completed_orders = set()
    now = Fraction(0)
    snapshots = []

    def check_balance():
        material = sum(len(q) + len(busy) for q, busy in zip(waiting, active))
        require(accepted == delivered + material, "DES_NATIVE_MASS_BALANCE_FAILED")
        require(accepted - delivered >= 0, "DES_NEGATIVE_PENDING")
        require(all(len(active[i]) <= spec[i][0] for i in range(n)),
                "DES_SERVER_LIMIT_EXCEEDED")
        ids = [v for q in waiting for v in q]
        ids += [v for busy in active for v in busy]
        require(len(ids) == len(set(ids)), "DES_DUPLICATE_ACTIVE_ORDER")
        require(not set(ids).intersection(completed_orders),
                "DES_REDELIVERY_OR_ACTIVE_COMPLETED_ORDER")
        require(len(completed_orders) == delivered, "DES_DELIVERED_COUNT_MISMATCH")
        return material

    def service_starts():
        nonlocal serial
        # Downstream-first start ordering fixes resource contention deterministically.
        for stage in reversed(range(n)):
            servers, service_time = spec[stage]
            while waiting[stage] and len(active[stage]) < servers:
                order = waiting[stage].popleft()
                active[stage].add(order)
                heappush(events, (now + service_time, 0, serial,
                                  "complete", stage, order))
                serial += 1
            check_balance()

    for target in observations:
        while events and events[0][0] <= target:
            now = events[0][0]
            # Exhaust all already scheduled events at now; starts happen after
            # the complete acceptance batch. Positive service times preclude
            # newly started service from completing at this same timestamp.
            batch = []
            while events and events[0][0] == now:
                batch.append(heappop(events))
            for _, _, _, kind, stage, order in batch:
                if kind != "complete":
                    continue
                require(order in active[stage], "DES_UNSCHEDULED_COMPLETION")
                active[stage].remove(order)
                if stage + 1 < n:
                    waiting[stage+1].append(order)
                else:
                    require(order not in completed_orders, "DES_DUPLICATE_DELIVERY")
                    completed_orders.add(order)
                    delivered += 1
                check_balance()
            for _, _, _, kind, _, order in batch:
                if kind != "accept":
                    continue
                waiting[0].append(order)
                accepted += 1
                check_balance()
            service_starts()
        pending = check_balance()
        snapshots.append(Snapshot(
            t_min=target, accepted_cum_orders=accepted,
            delivered_cum_orders=delivered, pending_orders=pending,
            stage_waiting=tuple(len(q) for q in waiting),
            stage_in_service=tuple(len(busy) for busy in active)))
    return tuple(snapshots)


def canonical_private_bytes(config):
    validate_private_config(config)
    return json.dumps(config, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def private_commitment(config, nonce):
    """Commit to a private config; nonce MUST remain private until reveal.

    Hashes of low-entropy operational parameters alone are vulnerable to
    guessing. This requires 32+ private random bytes; it never stores them.
    No private configuration is provided or generated in this repository.
    """
    require(type(nonce) is bytes and len(nonce) >= 32,
            "DES_PRIVATE_NONCE_REQUIRED_32_BYTES")
    return "sha256:" + sha256(
        b"IGC-CAF01-DES-PRECOMMIT-v1\x00" + nonce + b"\x00"
        + canonical_private_bytes(config)).hexdigest()


def verify_private_commitment(config, nonce, commitment):
    require(type(commitment) is str and commitment.startswith("sha256:"),
            "DES_BAD_COMMITMENT")
    return compare_digest(private_commitment(config, nonce), commitment)
