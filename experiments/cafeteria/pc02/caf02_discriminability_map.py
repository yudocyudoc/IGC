#!/usr/bin/env python3
"""CAF02 finite-grid discrimination mapping with the EXISTING E1 molecules.

All cases and synthetic truths are predeclared in this script, before its
calibration and K1 design outputs exist. Source SAME as candidate equations:
INTERNAL software discrimination probe, not an independent scientific test.
No DES, no Modelica, no third-party inference, no CAF01 holdout, no K2 truth.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import caf02_structural_k0k1k2 as s

SCHEMA="igc-caf02-structural-discriminability-synthetic-map/0.1"
# Fixed before seeing results. Some cases are not on either grid.
CASES=(
    {"id":"C00_ON_GRID","true_family":"C00","tp":1.0,"td":3.0,
     "capacity":72,"transit":None},
    {"id":"C01_ON_GRID_VISIBLE","true_family":"C01","tp":1.0,"td":1.0,
     "capacity":72,"transit":6.0},
    {"id":"C00_OFF_GRID","true_family":"C00","tp":1.7,"td":2.4,
     "capacity":90,"transit":None},
    {"id":"C01_OFF_GRID","true_family":"C01","tp":1.7,"td":2.4,
     "capacity":90,"transit":4.0},
    {"id":"C01_NEAR_INVISIBLE_EXTRA_STAGE","true_family":"C01",
     "tp":1.0,"td":3.0,"capacity":72,"transit":0.1},
)
GRIDS={
    "COARSE":{
        "preparation_tau":[1.0,3.0],
        "dispatch_tau":[1.0,3.0],
        "shared_cap":[72],
        "transit_tau":[0.25,6.0],
    },
    "REFINED":{
        "preparation_tau":[1.0,1.5,2.0,3.0],
        "dispatch_tau":[1.0,1.5,2.0,3.0],
        "shared_cap":[72,100],
        "transit_tau":[0.25,1.0,6.0],
    },
}
K0_MASKS={
    "SPARSE":[0,1],      # t=5, 10
    "RICHER":[0,1,3],     # t=5, 10, 20
}
MENU=(
    {"rate_per_minute":1.0,"t_min":10},
    {"rate_per_minute":1.5,"t_min":20},
    {"rate_per_minute":1.8,"t_min":30},
)
PARAMS={
    "construction_rate_per_minute":1.2,
    "k0_absolute_max_MAE_orders":0.8,
    "k0_relative_mae_allowance_orders":0.4,
    "k1_absolute_residual_max_orders":0.20,
    "k1_numerical_guard_orders":0.02,
    "minimum_expanded_k1_nonoverlap_orders":0.05,
    "k2_public_rate_for_unscored_proposals":1.35,
}


def process_case(case,grid_name,mask_name):
    model=s.params(case["true_family"],case["tp"],case["td"],
                   case["capacity"],case["transit"])
    observed=list(s.curve(model,PARAMS["construction_rate_per_minute"]))
    k0=s.k0_calibrate(
        observed,PARAMS["construction_rate_per_minute"],
        K0_MASKS[mask_name],GRIDS[grid_name],
        PARAMS["k0_absolute_max_MAE_orders"],
        PARAMS["k0_relative_mae_allowance_orders"])
    chosen=s.select_k1_measurement(
        k0,list(MENU),
        PARAMS["minimum_expanded_k1_nonoverlap_orders"],
        PARAMS["k1_absolute_residual_max_orders"],
        PARAMS["k1_numerical_guard_orders"])
    truth_family_k0=bool(k0[case["true_family"]]["eligible"])
    count={name:len(k0[name]["eligible"]) for name in s.FAMILIES}
    result={
        "case":case["id"],"true_family_label_for_synthetic_audit":case["true_family"],
        "true_params_disclosed_synthetic_only":case,
        "grid":grid_name,"k0_mask":mask_name,
        "k0_time_points":[s.T_VALUES[i] for i in K0_MASKS[mask_name]],
        "observed_k0_generated_by_same_equations_not_independent":observed,
        "k0_candidate_counts":count,
        "k0_best_mae_by_family":{
            name:k0[name]["best_k0_mae"] for name in s.FAMILIES},
        "true_family_retained_at_K0":truth_family_k0,
        "k1_design_status":chosen["status"],
        "k1_chosen":chosen.get("proposed_measurement"),
        "k1_best_expanded_robust_gap_orders":
            max((x["robust_nonoverlap_gap_orders"]
                 for x in chosen["all_menu_scores"]),default=None),
        "k1_best_raw_gap_orders":
            max((x["raw_nonoverlap_gap_orders"]
                 for x in chosen["all_menu_scores"]),default=None),
        "k1_menu_full":chosen["all_menu_scores"],
        "k1_policy_precommitted":chosen["precommitted_policy"],
        "k1_actual_evidence_used":False,
        "k1_revision_status":"NOT_APPLICABLE_NO_DISCRIMINATING_MENU",
        "k1_candidate_counts_after":None,
        "true_family_retained_after_K1":None,
        "truth_family_excluded_after_K1_despite_surviving_K0":None,
        "k2_proposals_formed_no_truth":False,
    }
    if chosen["status"]=="K1_DESIGN_HAS_PREDICTED_ROBUST_SEPARATION":
        option=chosen["proposed_measurement"]
        truth_y=s.curve(model,option["rate_per_minute"])[
            s.T_VALUES.index(option["t_min"])]
        # K1 truth is fabricated from the same equation FAMILY, only AFTER
        # menu selection. It does not influence menu choice or K0 calibration.
        evidence={**option,"delivered":truth_y}
        revision=s.k1_revise(
            k0,chosen,evidence,
            PARAMS["k1_absolute_residual_max_orders"])
        k2=s.prepare_k2_comparison(
            k0,revision,PARAMS["k2_public_rate_for_unscored_proposals"])
        s.need(k2["K2_truth_included"] is False
               and k2["K2_DES_runs"]==0,"K2_MUST_BE_UNSCORED")
        result.update({
            "k1_actual_evidence_used":True,
            "k1_synthetic_evidence":evidence,
            "k1_revision_status":revision["status"],
            "k1_candidate_counts_after":{
                name:revision["updated"][name]["count_after"]
                for name in s.FAMILIES},
            "true_family_retained_after_K1":
                case["true_family"] in revision["surviving_families"],
            "truth_family_excluded_after_K1_despite_surviving_K0":
                truth_family_k0 and
                case["true_family"] not in revision["surviving_families"],
            "k2_proposals_formed_no_truth":True,
            "k2_unscored_compatible_counts":{
                "K0":{n:(k2["K0_frozen"][n] or {}).get("candidate_count",0)
                      for n in s.FAMILIES},
                "K1":{n:(k2["K1_frozen"][n] or {}).get("candidate_count",0)
                      for n in s.FAMILIES}
            }
        })
    return result


def run():
    s.verify_existing_repertoire()
    reports=[process_case(case,grid,mask)
             for case in CASES
             for grid in GRIDS
             for mask in K0_MASKS]
    s.need(len(reports)==len(CASES)*len(GRIDS)*len(K0_MASKS),
           "CASE_GRID_MASK_MISMATCH")
    summary={
        "total_cases_x_grids_x_masks":len(reports),
        "K0_both_families_survive":sum(
            all(v>0 for v in r["k0_candidate_counts"].values())
            for r in reports),
        "K0_true_family_retained":sum(
            r["true_family_retained_at_K0"] for r in reports),
        "K1_robust_designs":sum(
            r["k1_design_status"]=="K1_DESIGN_HAS_PREDICTED_ROBUST_SEPARATION"
            for r in reports),
        "K1_menu_not_discriminating":sum(
            r["k1_design_status"]=="K1_MENU_CANNOT_ROBUSTLY_DISCRIMINATE"
            for r in reports),
        "K1_did_not_have_two_adequate_families":sum(
            r["k1_design_status"]=="K0_NO_TWO_ADEQUATE_STRUCTURES"
            for r in reports),
        "false_exclusion_of_true_family_after_K1_conditional_on_K0":sum(
            r["truth_family_excluded_after_K1_despite_surviving_K0"] is True
            for r in reports),
        "distinct_K1_measurements_selected":sorted({
            (r["k1_chosen"]["rate_per_minute"],r["k1_chosen"]["t_min"])
            for r in reports if r["k1_chosen"] is not None
        }),
    }
    return {
        "schema":SCHEMA,
        "status":"DETERMINISTIC_INTERNAL_SOFTWARE_MAPPING_NOT_PROSPECTIVE",
        "case_declarations":list(CASES),
        "finite_grids":GRIDS,"K0_masks":K0_MASKS,
        "K1_menu_declared_before_results":list(MENU),
        "tolerances_declared_before_results":PARAMS,
        "summary":summary,
        "case_results":reports,
        "limitations":[
            "Truth and candidates are generated by the SAME equations; NOT an independent world.",
            "Synthetic continuous delivered values; not the discrete-event or integer cafe output.",
            "Only two E1 structural classes and a finite grid; no continuous-space theorem.",
            "The numerical margin is a declared conservative operational allowance, not a proven global error bound.",
            "No joint-K1 multivariate measurement study; each K1 menu option is one delivered count.",
            "An overlapping expanded interval means no guaranteed single-measurement separation; may still reduce candidates.",
            "No claim that an off-grid true parameter should be recovered within grid.",
            "CAF01 holdout, any new DES, OpenModelica and providers never accessed.",
            "No K2 truth is generated or scored; K2 packages are only illustrative.",
        ],
        "resource_use":{"DES":0,"OpenModelica":0,
                        "Buffalo":0,"external_holdout":0},
    }


def markdown(report):
    stats=report["summary"]
    rows=report["case_results"]
    out=[
        "# CAF-02 — mapa sintético de discriminabilidad C00/C01",
        "",
        "**NO ES VALIDACIÓN INDEPENDIENTE:** la verdad sintética y los "
        "candidatos comparten exactamente las mismas ecuaciones. "
        "Se examina el funcionamiento y límites del criterio K0→K1; "
        "no existe K2 observado.",
        "",
        "## Dominio declarado",
        "",
        "Casos: "+", ".join(x["id"] for x in CASES)+".",
        "Cuadrículas: COARSE y REFINED; máscaras K0: SPARSE (5,10 min) "
        "y RICHER (5,10,20 min). Menú K1 igual para todos: "
        +", ".join(str(x) for x in MENU)+".",
        "Tolerancias exactas: "+str(PARAMS)+".",
        "",
        "## Recuentos",
        "",
        "| Indicador | Recuento |",
        "|---|---:|",
        *[f"| {key} | {val} |" for key,val in stats.items()
          if type(val) is int],
        "",
        "## Casos K0→K1 (K2 no observado)",
        "",
        "| Caso | Rejilla | K0 | Sobreviven C00/C01 | Separación K1 ampliada | K1 | Familia real descartada injustamente tras K1* |",
        "|---|---|---|---|---:|---|---|",
    ]
    for x in rows:
        gap=x["k1_best_expanded_robust_gap_orders"]
        out.append("| "+x["case"]+" | "+x["grid"]+" | "+x["k0_mask"]+" | "
            +str(x["k0_candidate_counts"]["C00"])+"/"
            +str(x["k0_candidate_counts"]["C01"])+ " | "
            +(f"{gap:.3f}" if gap is not None else "—")+" | "
            +x["k1_design_status"].replace(
                 "K1_DESIGN_HAS_PREDICTED_ROBUST_SEPARATION",
                 "Diseño separador").replace(
                 "K1_MENU_CANNOT_ROBUSTLY_DISCRIMINATE",
                 "Menú no separa").replace(
                 "K0_NO_TWO_ADEQUATE_STRUCTURES",
                 "Sin dos familias adecuadas")
            +" | "+str(x["truth_family_excluded_after_K1_despite_surviving_K0"])+" |")
    out.extend([
        "",
        "*Se define descarte condicional únicamente cuando la familia "
        "generadora sobrevivió K0 y se excluye tras K1; un caso off-grid "
        "podría fallar por falta de representabilidad en la rejilla.",
        "",
        "Una brecha K1 igual a cero tras ampliar tolerancias significa "
        "**sin separación garantizada por esa medición individual**. "
        "No significa que los candidatos no puedan reducirse con una "
        "observación concreta o con varias observaciones en conjunto.",
        "Un tránsito con τ=0.1 min es casi invisible en relación con "
        "los tiempos medidos; no prueba imposibilidad matemática "
        "de distinción con otra resolución o instrumento.",
        "",
        "## Siguiente decisión",
        "",
        "El mapa es diagnóstico para fijar **qué condiciones** admiten "
        "discriminación conservadora. No sustituye una validación "
        "independiente ni justifica cambiar E1. Los resultados "
        "negativos no autorizan reajustar el menú retrospectivamente.",
        "",
    ])
    return "\n".join(out)


def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--output-dir",required=True)
    args=cli.parse_args()
    out=Path(args.output_dir)
    s.need(not out.exists(),"OUTPUT_ALREADY_EXISTS")
    report=run()
    out.mkdir(parents=True)
    data=s.canonical(report)+b"\n"
    (out/"DISCRIMINABILITY_SYNTHETIC_GRID.json").write_bytes(data)
    (out/"DISCRIMINABILITY_SYNTHETIC_REPORT.md").write_text(
        markdown(report),encoding="utf-8")
    (out/"DISCRIMINABILITY_SYNTHETIC_GRID.sha256").write_text(
        hashlib.sha256(data).hexdigest()
        +"  DISCRIMINABILITY_SYNTHETIC_GRID.json\n")
    print(markdown(report))
    print("CAF02_DISCRIMINABILITY_SYNTHETIC_ONLY_PASS_NO_DES_NO_K2_TRUTH")


if __name__=="__main__":
    main()
