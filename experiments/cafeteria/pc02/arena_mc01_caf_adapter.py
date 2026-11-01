#!/usr/bin/env python3
"""ARENA MC-01 vertical slice: six CAF structural families with continuous c.

CAF adapter only. Generic core has no CAF assumptions or capacity grid.
Every physical model uses 1 or 2 independent continuous durations.
"""
from __future__ import annotations
from fractions import Fraction as Q
from hashlib import sha256
from itertools import combinations
from pathlib import Path
import argparse
import json

from scripts import arena_methodology_continuous as mc
import caf07b_umbral_secuencial as b
import caf11_parametric_des_inversion as v11
import caf15b_certified_2d_exclusion as v15b
import caf15a_two_capacity_witnesses as v15a

SCHEMA="igc-arena-mc01-four-layer-continuous-core/0.1"
PROTO="24b7fbf7deeffb162bc5abf88addf7cb16c9f084"
PROGRAMS=("F_R25_T20","F_R25_T25")
ERROR_SOURCE="SYNTHETIC_DECLARED_PLUS_MINUS_ONE_UNCALIBRATED"
NO_GRID=True


def families():
    return tuple(
        mc.Family(
            id=model["label"],
            parameter_names=tuple("duration_"+b.STAGES[s] for s in model["stages"]),
            duration_domains=tuple((v15b.D_LOW,v15b.D_HIGH)
                                   for _ in model["stages"]),
        ) for model in v11.models()
    )


class CAFContinuousBackend:
    def __init__(self):
        self.by_name={z["label"]:tuple(z["stages"]) for z in v11.models()}

    def stages(self,family):
        mc.need(family.id in self.by_name,"MC01_ADAPTER_UNKNOWN_FAMILY")
        stages=self.by_name[family.id]
        mc.need(len(family.parameter_names)==len(stages)
                and tuple(family.duration_domains)==
                tuple((v15b.D_LOW,v15b.D_HIGH) for _ in stages),
                "MC01_ADAPTER_DOMAIN_DRIFT")
        return stages

    def bounds(self,family,box,program):
        mc.need(program in PROGRAMS,"MC01_UNSUPPORTED_PROGRAM")
        return v15b.bounds(self.stages(family),box,program)

    def predict(self,family,point,program):
        mc.need(program in PROGRAMS,"MC01_UNSUPPORTED_PROGRAM")
        return v15b.signature(self.stages(family),point,program)


def prior_structural_analysis():
    models=v11.models()
    result={}
    for pid in PROGRAMS:
        pairrows=[]
        for m,n in combinations(models,2):
            res=v15b.run_pair(tuple(m["stages"]),tuple(n["stages"]),pid)
            if res["verdict"]=="CONFUSABLE_WITNESS_CERTIFIED":
                mc.need(v15b.verify_witness(tuple(m["stages"]),
                                            tuple(n["stages"]),pid,res["witness"]),
                        "MC01_BAD_APRIORI_WITNESS")
            elif res["verdict"]=="SEPARABLE_EXHAUSTIVE_BOX_CERTIFIED":
                mc.need(v15b.verify_exclusion_tree(
                    tuple(m["stages"]),tuple(n["stages"]),pid,
                    res["certificate_tree"]),
                    "MC01_BAD_APRIORI_EXCLUSION")
            pairrows.append({
                "family_a":m["label"],"family_b":n["label"],
                "verdict":res["verdict"],
                "certificate_verified":res["verdict"]!="UNRESOLVED_NOT_CERTIFIED",
                "witness":res["witness"],
                "n_box_nodes":res["stats"]["nodes"],
            })
        mc.need(len(pairrows)==15,"MC01_APRIORI_BAD_PAIR_COUNT")
        result[pid]=pairrows
    return result


def fixture_observations():
    """Only laboratory fixtures, no hidden labels passed into solver."""
    return (
        {"id":"KNOWN_DOUBLE_OFFGRID_69_101",
         "source_EVALUATOR_ONLY":"CAF15B_DETERMINISTIC_SAME_PHYSICS",
         "truth_structure_EVALUATOR_ONLY":"preparacion+despacho",
         "truth_capacities_EVALUATOR_ONLY":["69","101"],
         "values":list(v15b.physical_signature(
             (0,1),(Q(60,69),Q(60,101)),"F_R25_T20")),
         "program":"F_R25_T20"},
        {"id":"UNKNOWN_FOURTH_STAGE_FAST_220",
         "source_EVALUATOR_ONLY":"CAF15A_FOURTH_STAGE_DES_SAME_ASSUMPTIONS",
         "truth_structure_EVALUATOR_ONLY":"outside_3stage_family",
         "truth_capacities_EVALUATOR_ONLY":["220"],
         "values":list(
            v15a.native_readings(v15a.extra_config(220))["F_R25_T20"]),
         "program":"F_R25_T20"},
    )


def inference_only(obs,backend,ff):
    """Truth-hidden interface: no model labels, capacities or generator passed."""
    output=[mc.solve(f,obs,backend) for f in ff]
    decision=mc.falsify(ff,output)
    return {"observed":list(obs.values),
            "observation_error":{
                "max_integer_count_error":obs.error_radius,
                "source":obs.error_provenance,
                "physically_calibrated":False},
            "program":obs.program,
            "per_family":output,
            "interpretation":decision}


def summarize_without_truth(assessment):
    return {
        "program":assessment["program"],
        "per_class_status":{x["family_id"]:x["status"]
                            for x in assessment["per_family"]},
        "interpretation":assessment["interpretation"]["conclusion"],
        "all_covers_rechecked":all(x["certificate_verified"]
                                   for x in assessment["per_family"]),
    }


def run(out,checkout_sha,head_sha):
    mc.need(b.SOURCE_COMMIT_PATTERN.fullmatch(checkout_sha) and
            b.SOURCE_COMMIT_PATTERN.fullmatch(head_sha),
            "MC01_SHA_REQUIRED")
    out=Path(out).resolve()
    mc.need(not out.exists(),"MC01_REFUSE_OVERWRITE")
    ff=families()
    backend=CAFContinuousBackend()
    # No grid, no physical worlds examined in structure/model prior analysis.
    prior=prior_structural_analysis()
    out.mkdir(parents=True,exist_ok=False)
    def save(path,data):
        return b.lab.write_new(out,path,data)
    save("00_PLAN_BEFORE_EVAL.json",{
        "schema":SCHEMA,"protocol_first_commit":PROTO,
        "checkout_sha":checkout_sha,"pr_head_sha":head_sha,
        "n_structural_families":len(ff),
        "continuous_parameter_domains":[
            {"id":f.id,"parameters":list(f.parameter_names),
             "duration_intervals":mc.qbox(f.duration_domains)}
            for f in ff],
        "not_parameter_grid":True,
        "no_24_or_720_point_hypotheses":True,
        "max_box_nodes":mc.MAX_BOX_NODES,"max_depth":mc.MAX_DEPTH,
        "programs":PROGRAMS,"error_source":ERROR_SOURCE,
        "scientific_gate":mc.GATE,
        "no_truth_access_from_solver":True,
    })
    save("00B_A_PRIORI_BEFORE_EVAL.json",{
        "schema":SCHEMA,
        "pairwise_structural_results_continuous":prior,
        "all_pairs_checked_before_worlds":True,
    })
    outrows=[]
    for fixture in fixture_observations():
        obs=mc.Observation(
            program=fixture["program"],values=tuple(fixture["values"]),
            error_radius=1,error_provenance=ERROR_SOURCE,
            physical_provenance=fixture["source_EVALUATOR_ONLY"])
        inferred=inference_only(obs,backend,ff)
        outrows.append({
            "fixture_EVALUATOR_ONLY":fixture,
            "inference":inferred,
            "compact_result":summarize_without_truth(inferred),
        })
    options=mc.design_options(PROGRAMS,prior)
    report={
        "schema":SCHEMA,"protocol_first_commit":PROTO,
        "checkout_sha":checkout_sha,"pr_head_sha":head_sha,
        "n_structural_families":len(ff),
        "n_finite_parameter_grid_points":0,
        "n_synthetic_fixtures":len(outrows),
        "a_priori":prior,
        "evaluations":outrows,
        "design_experimental":options,
        "all_six_families_continuous":True,
        "all_feasible_sets_are_exact_predicates_not_grid":True,
        "outer_boxes_are_not_exact_feasible_regions":True,
        "falsification_never_proves_unknown_topology":True,
        "gate":mc.GATE,
    }
    save("01_RESULTADOS.json",report)
    lines=[
        "# ARENA MC-01 — Cuatro capas con parámetros continuos SIN rejilla",
        "",
        "Esta implementación **no clasifica entre 24/720 capacidades fijas**.",
        "Seis estructuras CAF; cada una con 1 o 2 parámetros continuos.",
        "Cuatro capas: distinguibilidad a priori, set-membership,",
        "falsificación y opciones experimentales condicionadas.",
        "",
        "## A priori — sobre el dominio continuo de cada estructura",
        "",
        "| Programa | Pares con certificado de separación /15 | Pares con testigo de confusión /15 | Indeterminados /15 |",
        "|---|---:|---:|---:|",
    ]
    for pid in PROGRAMS:
        entries=prior[pid]
        lines.append("| "+" | ".join(map(str,(
            pid,
            sum(x["verdict"]=="SEPARABLE_EXHAUSTIVE_BOX_CERTIFIED" for x in entries),
            sum(x["verdict"]=="CONFUSABLE_WITNESS_CERTIFIED" for x in entries),
            sum(x["verdict"]=="UNRESOLVED_NOT_CERTIFIED" for x in entries),
        )))+" |")
    lines +=["","## Set membership y falsificación sobre observaciones fijas",
        "| Fixture sintético | Familia | Resultado continuo | Cajas externas retenidas | Testigo racional |",
        "|---|---|---|---:|---|"]
    for item in outrows:
        for x in item["inference"]["per_family"]:
            w=x["witness"]
            lines.append("| "+" | ".join((
                item["fixture_EVALUATOR_ONLY"]["id"],x["family_id"],
                x["status"],str(x["n_retained_boxes"]),
                ",".join(w["parameter_durations"]) if w else "ninguno probado"
            ))+" |")
    lines +=["",
        "## Interpretación de cada fixture",
        ""]
    for item in outrows:
        lines.append("- **"+item["fixture_EVALUATOR_ONLY"]["id"]+
          "**: "+item["compact_result"]["interpretation"]+
          "; evidencia sintética. Un conjunto vacío NO demuestra topología desconocida.")
    lines +=["",
        "## Diseño experimental",
        "",
        options["status"]+
        ": no existe evidencia de ventana natural de 150/h ni costos de sensores o función de pérdida.",
        "Se muestran opciones de escritorio, **sin ranking ni política de inducción de sobrecarga**.",
        "",
        "## Límites",
        "- Las cajas retenidas son sobreaproximación rigurosa del conjunto",
        "  definido por predicado continuo, NO región factible exacta.",
        "- Un punto testigo es evidencia de existencia, NO volumen factible.",
        "- La prueba a priori no prueba unicidad de clase en un caso individual.",
        "- 150/h, FIFO y error ±1 son condiciones sintéticas no calibradas.",
        "- El core es agnóstico al simulador, pero el backend actualmente",
        "  solo admite CAF-15B y dos programas deterministas.",
        "- D/B/M, ATMS, Z3, inferencia estocástica y datos reales no están",
        "  integrados aún.",
        "",
        "Gate: "+mc.GATE]
    save("02_INFORME.md","\n".join(lines))
    manifest={f.name:"sha256:"+sha256(f.read_bytes()).hexdigest()
              for f in out.iterdir() if f.is_file()}
    save("03_MANIFIESTO.json",{
        "schema":SCHEMA,
        "checkout_sha":checkout_sha,"pr_head_sha":head_sha,
        "files_sha256":manifest,"no_parameter_grid":True})
    return report


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True,type=Path)
    parser.add_argument("--checkout-sha",required=True)
    parser.add_argument("--head-sha",required=True)
    args=parser.parse_args()
    r=run(args.out,args.checkout_sha,args.head_sha)
    print(json.dumps({
        "n_structural_families":r["n_structural_families"],
        "n_finite_parameter_grid_points":r["n_finite_parameter_grid_points"],
        "per_fixture":[x["compact_result"] for x in r["evaluations"]],
        "design_state":r["design_experimental"]["status"],
        "gate":r["gate"],
    },sort_keys=True))
