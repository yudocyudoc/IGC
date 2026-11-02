#!/usr/bin/env python3
"""CAF-01: certificado estático CONSERVADOR para el tope de BoundedQueue.

No simula modelos, no inspecciona DES privado y no declara identificabilidad
de estructuras. Solo demuestra que ciertas capacidades no pueden activarse
bajo las hipótesis explícitas del contrato y la ecuación stock/responseTime.
"""
import json
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONTRACT = HERE / "ARENA_PC01_CAF01_CONTRATO_REVISION_v0_3_2026-10-28.json"


def certificate(contract):
    boundary = contract["boundary"]
    m = contract["methods"]["M"]
    src = contract["source_proposal"]
    worlds = contract["worlds"]
    if not (boundary["initial_accepted"] == 0
            and boundary["initial_delivered"] == 0
            and boundary["initial_pending"] == 0
            and boundary["losses_allowed"] is False
            and boundary["cancellations_allowed"] is False):
        raise ValueError("NO_CERTIFICATE: nonempty initial state or losses/cancellations")
    if src["kind"] != "independent_discrete_event_calendar":
        raise ValueError("NO_CERTIFICATE: source type changed")
    if m["capacity_application"] != "simultaneously_to_preparation_and_dispatch_not_independent_fit":
        raise ValueError("NO_CERTIFICATE: capacity policy changed")
    if m["structural_classes"] != ["C00", "C01", "C02"]:
        raise ValueError("NO_CERTIFICATE: structural classes changed")
    times = m["frozen_response_time_hours"]
    if not (Decimal(str(times["preparation"])) == Decimal("0.5")
            and Decimal(str(times["dispatch"])) == Decimal("0.5")):
        raise ValueError("NO_CERTIFICATE: response times changed")
    if len(worlds) != 2 or any(w["start_state"] != "EMPTY_RESET" for w in worlds):
        raise ValueError("NO_CERTIFICATE: worlds/reset changed")
    counts = src["expected_event_counts_given_half_open_pulse"]
    n = [int(counts["construction"]), int(counts["evaluation"])]
    if n != [24, 30]:
        raise ValueError("NO_CERTIFICATE: expected event counts changed")
    if any(w["arrival"]["kind"] != "pulse" for w in worlds):
        raise ValueError("NO_CERTIFICATE: pulse changed")
    # El integral de cada pulso también debe concordar exactamente con los conteos.
    for world, count in zip(worlds, n):
        proposed = (Decimal(str(world["arrival"]["rate"]))
                    * Decimal(str(world["arrival"]["duration_minutes"])))
        if proposed != Decimal(count):
            raise ValueError("NO_CERTIFICATE: pulse/count mismatch")
    # Conservación: cada stock individual <= todas las órdenes aceptadas.
    # release=min(capacity, stock/responseTime). Si capacity >= max(N/tau),
    # el límite de capacidad nunca altera la salida, en todo t.
    max_release = max(Decimal(count) / Decimal("0.5") for count in n)
    caps = [Decimal(str(c)) for c in m["proposed_bounded_capacity_grid_items_per_hour"]]
    if len(caps) != m["per_structure_max"] or len(caps) != len(set(caps)):
        raise ValueError("NO_CERTIFICATE: grid shape changed")
    # Alcance de este contrato: capacidades estrictamente enteras y positivas.
    # Rechazar no enteros evita colisiones/truncamiento al serializar miembros.
    if any(not c.is_finite() or c <= 0 or c != c.to_integral_value() for c in caps):
        raise ValueError("NO_CERTIFICATE: capacities must be positive finite integers")
    inactive = sorted(c for c in caps if c >= max_release)
    classes = []
    for structure in m["structural_classes"]:
        for c in caps:
            if c not in inactive:
                classes.append({"structure": structure, "capacities": [int(c)],
                                "kind": "singleton_not_proven_distinct"})
        if inactive:
            classes.append({"structure": structure,
                            "capacities": [int(c) for c in inactive],
                            "kind": "proven_inactive_capacity"})
    return {
        "status": "STATIC_UPPER_BOUND_ONLY",
        "max_orders_any_world": max(n),
        "max_proportional_release_items_per_hour": int(max_release),
        "inactive_capacities": [int(c) for c in inactive],
        "nominal_configurations": len(caps) * len(m["structural_classes"]),
        "within_structure_upper_bound_classes": len(classes),
        "classes": classes,
        "limitations": [
            "Other behavioral equivalences may exist; class count is only an upper bound.",
            "No equivalence between different structural classes is certified.",
            "No candidate ranking, averaging, forecast, or structural recovery is certified.",
            "Depends on BoundedQueue release=min(capacity, stock/responseTime) and material conservation.",
            "Do not use for DES world parameter inference or choose grid after seeing hidden results."
        ]
    }


if __name__ == "__main__":
    print(json.dumps(certificate(json.loads(CONTRACT.read_text(encoding="utf-8"))),
                     indent=2, ensure_ascii=False))
