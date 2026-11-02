#!/usr/bin/env python3
"""Post-hoc CAF-01 M/C00 representability: PUBLIC CONSTRUCTION ONLY.

Exactly the existing E1 two BoundedQueue stock/release equations:
release_i = min(capacity_i, stock_i / responseTime_i).
No Modelica compilation, Buffalo, DES, G4 package, evaluation truth,
new molecules, provider, private parameters, or prospective claim.

Heun convergence is explicitly checked; it is an exploratory numerical
approximation, NOT native G2 and NOT a new pre-registered forecast.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "public_inputs/run_40915090599/CAF01.json"
PIN = "727501a3b5b33a63ab5a5d5f0f907d5431d0ee4f0d8b24ffd6f97758d59386fb"
WORLD = "sha256:26ca23076a44410bcafc4a7a944a5d5f6c6528dd59c96e7459e43c93a68812ad"
TIMES = (5, 10, 15, 20, 30, 40)
RATE = 1.2  # public construction input in orders/minute, NOT future input
DURATION = 20
HORIZON = 40
# The baseline E1 uses 30 minutes per queue. Historical R3 explored
# 15/30/60 minutes. Shorter hypothetical times have NO operational approval.
HISTORICAL_TAU_MIN = (15.0, 30.0, 60.0)
HYPOTHETICAL_TAU_MIN = (1.0, 2.0, 3.0, 5.0, 7.5, 10.0)
CAPACITIES_PER_HOUR = (20, 72, 100)  # existing grid, not increased
DT_COARSE = 0.05
DT_FINE = 0.025
NUMERICAL_TOLERANCE = 0.005
COMPARABILITY_TOLERANCE = 0.25


class Blocked(ValueError):
    pass


def require(ok, why):
    if not ok:
        raise Blocked(why)


def load_construction():
    raw = SOURCE.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == PIN,
            "CONSTRUCTION_PINNED_SOURCE_SHA_CHANGED")
    e = json.loads(raw)
    require(e["case"] == "CAF01" and e["source_snapshot_sha256"] == WORLD
            and e["public_pulse"] == {
                "kind": "pulse", "rate_per_minute": RATE,
                "duration_minutes": DURATION
            } and e["schema"] == "igc-caf01-g3-decision/0.1",
            "UNEXPECTED_PUBLIC_CONSTRUCTION_IDENTITY")
    rows = e["observations"]
    require(type(rows) is list and [row["t_min"] for row in rows] ==
            [0, *TIMES] and rows[0]["delivered"] == 0,
            "UNEXPECTED_PUBLIC_CONSTRUCTION_TIMES")
    observed = [r["delivered"] for r in rows[1:]]
    require(observed == [3, 8, 13, 18, 24, 24],
            "CONSTRUCTION_VALUES_DIFFER_FROM_PINNED_RECORD")
    return observed


def reference_caf_in_sample(observed):
    """REF-CAF construction-domain diagnostic, NOT the frozen future score."""
    series = [0, *observed]
    clock = [0, *TIMES]
    candidates = []
    for i in range(4):  # [0,5], [5,10], [10,15], [15,20]
        a, b = clock[i:i+2]
        if RATE*a - series[i] > 1 and RATE*b - series[i+1] > 1:
            candidates.append((series[i+1] - series[i]) / (b-a))
    require(len(candidates) >= 2, "IN_SAMPLE_REF_CAF_NOT_IDENTIFIABLE")
    mu = float(median(candidates))
    pred = [min(RATE*min(t, DURATION), mu*t) for t in TIMES]
    return {"label": "REF_CAF_IN_SAMPLE_DIAGNOSTIC_NOT_G4_FORECAST",
            "effective_rate_orders_per_min": mu,
            "predicted_delivered": pred, "MAE": mae(pred, observed)}


def mae(pred, observed):
    require(len(pred) == len(observed) == len(TIMES), "SCORE_WRONG_SIX_POINTS")
    return sum(abs(p-y) for p, y in zip(pred, observed))/6


def analytic_equal_uncapped(t, tau_min, rate=RATE, duration=DURATION):
    """Exact 2-stage linear response for equal tau, only IF cap is inactive."""
    def integrated_step(x):
        if x <= 0:
            return 0.0
        u = x/tau_min
        return x-2*tau_min+(x+2*tau_min)*math.exp(-u)
    return rate*(integrated_step(t)-integrated_step(t-duration))


def analytic_uncapped_two_stage(t, tau_p, tau_d, rate=RATE, duration=DURATION):
    """Analytic pulse deliveries for the EXISTING LINEAR nonbinding C00 case.

    H(s) = 1 / ((1 + tau_p*s)*(1 + tau_d*s)); its factors commute.
    The integrated step response is exact for unequal as well as equal taus.
    """
    require(t >= 0 and tau_p > 0 and tau_d > 0, "INVALID_ANALYTIC_INPUT")
    if tau_p == tau_d:
        return analytic_equal_uncapped(t, tau_p, rate=rate, duration=duration)

    def integrated_step(x):
        if x <= 0:
            return 0.0
        qp = -math.expm1(-x / tau_p)
        qd = -math.expm1(-x / tau_d)
        return x - (tau_p*tau_p*qp - tau_d*tau_d*qd) / (tau_p-tau_d)

    return rate*(integrated_step(t) - integrated_step(t-duration))


def comparable_output_key(row):
    """Observable-equivalence key, never a unique stage assignment.

    Stage-time swapping is justified ONLY when capacities are inactive:
    72/100 items/hour are >= this public construction pulse's 72/hour.
    Below input (capacity=20), nonlinear saturation may BREAK symmetry.
    """
    tau_p = row["tau_preparation_minutes"]
    tau_d = row["tau_dispatch_minutes"]
    cap = row["shared_capacity_orders_per_hour"]
    require(cap in CAPACITIES_PER_HOUR, "UNKNOWN_CAPACITY_CLASS")
    if cap in (72, 100):
        return (72, *sorted((tau_p, tau_d)))
    return (cap, tau_p, tau_d)


def integrate_c00(tau_p, tau_d, capacity_per_hour, step_minutes):
    """Finite-capacity two-stock Heun, deterministic, with mass audit.

    Two original molecule roles: preparation -> dispatch -> delivery counter.
    Both roles have the same capacity setting; response times can vary
    separately for THIS exploration, unlike the original frozen candidates.
    """
    require(all(math.isfinite(x) and x > 0 for x in
                (tau_p, tau_d, capacity_per_hour, step_minutes)),
            "BAD_EXPLORATORY_PARAMETERS")
    steps = HORIZON / step_minutes
    require(abs(steps-round(steps)) < 1e-9 and
            abs(DURATION/step_minutes-round(DURATION/step_minutes)) < 1e-9,
            "STEP_MUST_SPLIT_AT_INPUT_DISCONTINUITY")
    cap = capacity_per_hour/60
    stock_p = stock_d = deliveries = 0.0
    out = []
    read_steps = {int(round(t/step_minutes)): t for t in TIMES}
    def derivatives(p, d, incoming):
        outp = min(cap, max(0.0,p)/tau_p)
        outd = min(cap, max(0.0,d)/tau_d)
        return (incoming-outp, outp-outd, outd)
    for idx in range(1, round(steps)+1):
        t0 = (idx-1)*step_minutes
        incoming = RATE if t0 < DURATION-1e-9 else 0.0
        deriv1 = derivatives(stock_p, stock_d, incoming)
        predictor_p = stock_p+step_minutes*deriv1[0]
        predictor_d = stock_d+step_minutes*deriv1[1]
        deriv2 = derivatives(predictor_p, predictor_d, incoming)
        stock_p += step_minutes*(deriv1[0]+deriv2[0])/2
        stock_d += step_minutes*(deriv1[1]+deriv2[1])/2
        deliveries += step_minutes*(deriv1[2]+deriv2[2])/2
        accepted = RATE*min(idx*step_minutes, DURATION)
        require(min(stock_p, stock_d, deliveries) >= -1e-8 and
                abs(accepted-stock_p-stock_d-deliveries) < 1e-6,
                "M_C00_EXPLORATORY_MATERIAL_BALANCE_FAILED")
        if idx in read_steps:
            require(0 <= deliveries <= accepted+1e-6, "NONPHYSICAL_DELIVERIES")
            out.append(deliveries)
    require(len(out) == 6 and
            all(a <= b+1e-9 for a,b in zip(out,out[1:])),
            "BAD_EXPLORATORY_OUTPUT")
    return out


def campaign():
    observed = load_construction()
    baseline = reference_caf_in_sample(observed)
    tau_all = (*HYPOTHETICAL_TAU_MIN, *HISTORICAL_TAU_MIN)
    rows = []
    for tau_p in tau_all:
        for tau_d in tau_all:
            for cap in CAPACITIES_PER_HOUR:
                coarse = integrate_c00(tau_p,tau_d,cap,DT_COARSE)
                fine = integrate_c00(tau_p,tau_d,cap,DT_FINE)
                diff = max(abs(a-b) for a,b in zip(coarse,fine))
                require(diff <= NUMERICAL_TOLERANCE,
                        "NUMERICAL_CONVERGENCE_NOT_VERIFIED")
                stage = ("HISTORICAL_15_30_60_MIN"
                         if tau_p in HISTORICAL_TAU_MIN
                         and tau_d in HISTORICAL_TAU_MIN
                         else "HYPOTHETICAL_SHORT_TIME_NOT_OPERATIONALLY_APPROVED")
                row = {
                    "tau_preparation_minutes": tau_p,
                    "tau_dispatch_minutes": tau_d,
                    "shared_capacity_orders_per_hour": cap,
                    "tier": stage,
                    "predicted_delivered_construction": fine,
                    "MAE_construction": mae(fine,observed),
                    "numerical_coarse_fine_max_abs_orders": diff,
                    "native_G2_certification": False,
                    "operational_parameter_justification_provided": False,
                }
                rows.append(row)
    rows.sort(key=lambda x:(x["MAE_construction"],
                            x["tier"] != "HISTORICAL_15_30_60_MIN",
                            x["tau_preparation_minutes"],
                            x["tau_dispatch_minutes"],
                            x["shared_capacity_orders_per_hour"]))
    historical = [x for x in rows if x["tier"]=="HISTORICAL_15_30_60_MIN"]
    original = next(x for x in rows if x["tau_preparation_minutes"] ==
                    x["tau_dispatch_minutes"] == 30.0 and
                    x["shared_capacity_orders_per_hour"] == 72)
    # An original frozen configuration with cap 72 never binds under the
    # physical upper bound: at most 24 orders / 0.5 h = 48 orders/h.
    expected = [analytic_equal_uncapped(t,30) for t in TIMES]
    require(max(abs(a-b) for a,b in zip(original["predicted_delivered_construction"],
                                       expected)) < 0.002,
            "C00_NUMERIC_DOES_NOT_MATCH_KNOWN_UNCAPPED_EQUATIONS")
    best_historical = min(historical,key=lambda x:x["MAE_construction"])
    best = rows[0]
    comparable = [x for x in rows
                  if x["MAE_construction"] <=
                  baseline["MAE"] + COMPARABILITY_TOLERANCE]
    # For the construction pulse (72/h, empty initial states), each stage
    # has inflow <= 72/h. Capacities 72 and 100 therefore cannot bind.
    # These are nominal parameter aliases, NOT independent model solutions.
    for tau_p in tau_all:
        for tau_d in tau_all:
            c72=next(x for x in rows if
                     x["tau_preparation_minutes"]==tau_p
                     and x["tau_dispatch_minutes"]==tau_d
                     and x["shared_capacity_orders_per_hour"]==72)
            c100=next(x for x in rows if
                      x["tau_preparation_minutes"]==tau_p
                      and x["tau_dispatch_minutes"]==tau_d
                      and x["shared_capacity_orders_per_hour"]==100)
            require(max(abs(x-y) for x,y in zip(
                c72["predicted_delivered_construction"],
                c100["predicted_delivered_construction"]))<1e-8,
                "CONSTRUCTION_CAPACITY_ALIAS_72_100_INVALID")
    unique_comparable = {
        (x["tau_preparation_minutes"],x["tau_dispatch_minutes"],
         72 if x["shared_capacity_orders_per_hour"]==100
         else x["shared_capacity_orders_per_hour"])
        for x in comparable
    }
    # Linear two-stage transfer is invariant to tau_p <-> tau_d. Verify that
    # symmetry numerically for the two explicitly nonbinding capacities.
    for tau_p in tau_all:
        for tau_d in tau_all:
            for cap in (72, 100):
                a = next(x for x in rows
                         if x["tau_preparation_minutes"]==tau_p
                         and x["tau_dispatch_minutes"]==tau_d
                         and x["shared_capacity_orders_per_hour"]==cap)
                b = next(x for x in rows
                         if x["tau_preparation_minutes"]==tau_d
                         and x["tau_dispatch_minutes"]==tau_p
                         and x["shared_capacity_orders_per_hour"]==cap)
                require(max(abs(u-v) for u,v in zip(
                    a["predicted_delivered_construction"],
                    b["predicted_delivered_construction"])) < 1e-8,
                    "NONBINDING_STAGE_TIME_PERMUTATION_MISMATCH")
    groups = {}
    for row in comparable:
        groups.setdefault(comparable_output_key(row), []).append(row)
    # Verify every merged class is an equivalent DELIVERY response, not
    # simply similar MAE. We do not merge saturated capacity=20 by swapping.
    for members in groups.values():
        reference = members[0]["predicted_delivered_construction"]
        require(all(max(abs(u-v) for u,v in zip(
            x["predicted_delivered_construction"], reference)) < 1e-8
            for x in members), "INVALID_OBSERVABLE_EQUIVALENCE_CLASS")
    group_representatives = [members[0]["predicted_delivered_construction"]
                             for members in groups.values()]
    require(all(max(abs(u-v) for u,v in zip(a,b)) > 1e-6
                for i,a in enumerate(group_representatives)
                for b in group_representatives[i+1:]),
            "OUTPUT_CLASSES_NOT_DISTINCT_ON_OBSERVED_GRID")
    expected_pairs = {(1.0,1.0),(1.0,2.0),(1.0,3.0),(1.0,5.0),
                      (2.0,2.0),(2.0,3.0),(3.0,3.0)}
    require(len(comparable)==22 and len(unique_comparable)==11
            and set(groups)=={(72,*p) for p in expected_pairs},
            "COMPARABLE_CLASS_COUNTS_OR_SYMMETRY_CHANGED")
    # Analytic demonstration for the original C00 molecules in the fast regime.
    for tau_p,tau_d in ((1.0,3.0),(3.0,1.0)):
        curve = next(x for x in rows
                     if x["tau_preparation_minutes"]==tau_p
                     and x["tau_dispatch_minutes"]==tau_d
                     and x["shared_capacity_orders_per_hour"]==72)
        exact = [analytic_uncapped_two_stage(t,tau_p,tau_d) for t in TIMES]
        require(max(abs(u-v) for u,v in zip(
            exact, curve["predicted_delivered_construction"])) < 0.002,
            "FAST_C00_ANALYTIC_NUMERICAL_DISCREPANCY")
    return {
        "schema": "igc-caf01-m-c00-representability-exploratory/0.1",
        "status": "POSTHOC_CONSTRUCTION_ONLY_NOT_A_FORECAST",
        "input": "PINNED_PUBLIC_CAF01_CONSTRUCTION_ONLY",
        "construction_file_sha256": "sha256:"+PIN,
        "source_snapshot_public_commitment": WORLD,
        "observed_construction_delivered": observed,
        "times_minutes": list(TIMES),
        "model": "EXISTING_E1_C00_TWO_BOUNDED_QUEUE_MOLECULES",
        "equations": "release_i=min(capacity,stock_i/responseTime_i)",
        "response_times_minutes_explored": list(tau_all),
        "historical_response_times_minutes": list(HISTORICAL_TAU_MIN),
        "hypothetical_short_response_times_minutes": list(HYPOTHETICAL_TAU_MIN),
        "capacities_orders_per_hour_explored": list(CAPACITIES_PER_HOUR),
        "numerical_method": "HEUN_CONVERGENCE_0.05_VS_0.025_MIN",
        "max_coarse_fine_difference_orders":
            max(x["numerical_coarse_fine_max_abs_orders"] for x in rows),
        "original_frozen_C00_cap72_tau30": original,
        "reference_CAF_in_sample_only": baseline,
        "best_historical_range": best_historical,
        "best_across_all_hypothetical": best,
        "comparable_definition":
            "EXPLORATORY_CONSTRUCTION_MAE <= REF_CAF_IN_SAMPLE_MAE + 0.25",
        "historical_comparable_count": sum(x in historical for x in comparable),
        "all_comparable_count": len(comparable),
        "unique_comparable_classes_after_capacity_alias": len(unique_comparable),
        "unique_comparable_delivery_responses_after_tau_permutation": len(groups),
        "comparable_delivery_response_classes": [
            {"nonbinding_capacity_class_orders_per_hour": key[0],
             "unordered_response_times_minutes": list(key[1:]),
             "nominal_combinations": len(members),
             "members": [{
                 "tau_preparation_minutes": x["tau_preparation_minutes"],
                 "tau_dispatch_minutes": x["tau_dispatch_minutes"],
                 "shared_capacity_orders_per_hour": x["shared_capacity_orders_per_hour"]
             } for x in members],
             "delivered_curve_construction": members[0]["predicted_delivered_construction"],
             "MAE_construction": members[0]["MAE_construction"]}
            for key,members in sorted(groups.items())
        ],
        "cap_72_100_are_equivalent_during_72_per_hour_construction": True,
        "stage_specific_tau_from_deliveries_identifiable": False,
        "near_best_count_plus_0_25_orders":
            sum(x["MAE_construction"] <= best["MAE_construction"]+.25 for x in rows),
        "complete_grid": rows,
        "limitations": [
            "The six construction samples are not independent holdout data.",
            "REF-CAF diagnostic is in-sample; it is NOT the G4 future MAE.",
            "Short response times are mathematical hypotheses without operational justification.",
            "A good fit is representability, not identifiability or structural recovery.",
            "In nonbinding linear C00, swapping preparation/dispatch response times leaves deliveries identical but can change internal inventories.",
            "Seven distinct responses count only this discrete comparison grid; unordered tau pairs need not be identifiable from six samples.",
            "Saturated capacity=20 is not assumed stage-swap symmetric.",
            "responseTime is stock-to-outflow response scale, not automatically service duration per order.",
            "Heun approximates existing molecule equations but is not an OpenModelica G2 run.",
            "C01/C02 transit topologies not tested; no global M-family impossibility follows.",
            "Original G3/G4/evaluation data are never read or scored here.",
            "CAF-01 first-round forecasts and negative M evaluation remain immutable.",
            "Posthoc representability cannot be presented as prospective predictive victory.",
        ],
    }


def markdown(r):
    baseline = r["reference_CAF_in_sample_only"]
    original = r["original_frozen_C00_cap72_tau30"]
    h = r["best_historical_range"]
    best = r["best_across_all_hypothetical"]
    def description(row):
        return (f"{row['tau_preparation_minutes']:g}/{row['tau_dispatch_minutes']:g} min, "
                f"cap {row['shared_capacity_orders_per_hour']}/h; "
                f"MAE {row['MAE_construction']:.4f}")
    lines = [
        "# CAF-01 M/C00 — Representabilidad exploratoria SOLO construcción",
        "",
        "**No es una nueva evaluación ni una corrección del G4.** Solamente lee "
        "el archivo público de construcción (hash fijado), no utiliza "
        "ninguna observación del holdout.",
        "",
        f"REF-CAF ajustada en construcción: MAE {baseline['MAE']:.4f} pedidos "
        "(comparador diagnóstico, no la puntuación G4).",
        "",
        f"Original M C00 (30/30 min, cap 72/h): {description(original)}.",
        f"Mejor dentro del rango histórico 15/30/60 min: {description(h)}.",
        f"Mejor entre todos los escenarios hipotéticos: {description(best)}.",
        "",
        f"Configuraciones históricas comparables con REF-CAF (+0.25): "
        f"{r['historical_comparable_count']}.",
        f"Configuraciones totales comparables (+0.25): "
        f"{r['all_comparable_count']} combinaciones nominales, "
        f"{r['unique_comparable_classes_after_capacity_alias']} clases distintas "
        "tras agrupar capacidades 72/100 durante construcción.",
        f"Al agrupar también el intercambio de tiempos entre etapas sin "
        f"saturación, quedan **{r['unique_comparable_delivery_responses_after_tau_permutation']} "
        "respuestas distintas** en esta cuadrícula. Esto NO identifica "
        "individualmente tau de preparación y despacho.",
        "",
        "Parejas de tiempos sin orden (min): "
        + ", ".join(str(tuple(c["unordered_response_times_minutes"]))
                    for c in r["comparable_delivery_response_classes"]) + ".",
        "",
        "| Minuto | Entregados construcción | Mejor M exploratoria | Error firmado |",
        "|---:|---:|---:|---:|",
        *[
            f"| {t} | {obs:g} | {p:.4f} | {p-obs:+.4f} |"
            for t, obs, p in zip(
                TIMES, r["observed_construction_delivered"],
                best["predicted_delivered_construction"])
        ],
        "",
        f"Máxima diferencia entre integraciones Heun: "
        f"{r['max_coarse_fine_difference_orders']:.6f} pedidos.",
        "",
        "## Interpretación obligatoria",
        "",
        "En régimen lineal sin saturación, H(s)=1/((1+tau_p*s)(1+tau_d*s)): "
        "intercambiar tau_p y tau_d conserva la respuesta de entregas. "
        "No necesariamente conserva los stocks de cada etapa. "
        "El parámetro responseTime representa escala de vaciado "
        "stock/flujo, no un tiempo de servicio individual certificado.",
        "",
        "Los tiempos menores de 15 minutos no cuentan con justificación "
        "operativa aportada: encontrar un ajuste bueno en esa banda "
        "demuestra posibilidad matemática de una parametrización C00, "
        "pero NO representabilidad dentro de un rango operacionalmente "
        "aprobado ni identificación estructural. La familia C01/C02 no "
        "se ha examinado. No se ejecutaron DES, OpenModelica, Buffalo "
        "ni RK4 de CAF-01; no se utilizaron datos de evaluación.",
        "",
        "El resultado negativo original de M frente a REF-CAF sigue cerrado. "
        "Para evaluar una variante revisada hace falta una campaña "
        "independiente y condiciones operativas justificadas ex ante.",
        "",
    ]
    return "\n".join(lines)


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--output-dir",required=True)
    args=cli.parse_args()
    folder=Path(args.output_dir)
    require(not folder.exists(),"OUTPUT_ALREADY_EXISTS")
    result=campaign()
    folder.mkdir(parents=True)
    (folder/"C00_CONSTRUCTION_GRID.json").write_text(
        json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+"\n",
        encoding="utf-8")
    report=markdown(result)
    (folder/"C00_CONSTRUCTION_REPORT.md").write_text(report,
        encoding="utf-8")
    print(report)
    print("C00_EXPLORATORY_CONSTRUCTION_ONLY_PASS_NO_DES_NO_OMC_NO_BUFFALO")


if __name__=="__main__":
    main()
