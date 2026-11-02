#!/usr/bin/env python3
"""CAF-02 post-hoc K0 pruning diagnosis on EXISTING A-E public DES outputs.

Never changes the official K0/K1 policy, never executes DES, never selects a
new K1, and never turns retrospective scoring into prospective validation.
Compare ORIGINAL K0 [absolute<=1 AND family best+0.4] against diagnostic
ABSOLUTE-ONLY K0 [absolute<=1] on the exact observed K1 and K2 already used.
"""
from __future__ import annotations
import argparse
import csv
from hashlib import sha256
import io
import json
from pathlib import Path

import caf02_structural_k0k1k2 as m
import caf02_d_k0k1k2_adapter as d
import caf02_k2_set_scoring as scoring
import caf02_joint_md_k1_design as joint
import caf02_lab_exploratorio as lab

SOURCE_RUN="https://github.com/yudocyudoc/IGC/actions/runs/41157842109"
SOURCE_ARTIFACT="CAF02-DES-FIVE-PUBLIC-WORLDS-41157842109"
SCHEMA="igc-caf02-existing-output-k0-pruning-diagnostic/0.1"
# EXPLICIT replay of ORIGINAL public observations from PR #110, not fresh DES.
# Three UNIQUE observable signatures; B/C/D are not independent evidence.
WORLDS={
    "A":{"K0":(2,8),"K1":22,"K2":(2,8,15,22,27,27),
         "M0":48,"M1":1,"D0":16,"D1":2,
         "loss":(0.9067570000382051,0.5462947166479473,
                 1.8191731857133897,1.006392564045072)},
    "B":{"K0":(2,7),"K1":17,"K2":(2,7,12,17,27,27),
         "M0":38,"M1":0,"D0":12,"D1":0,
         "loss":(1.128626559903897,None,1.829286825593656,None)},
    "C":{"K0":(2,7),"K1":17,"K2":(2,7,12,17,27,27),
         "M0":38,"M1":0,"D0":12,"D1":0,
         "loss":(1.128626559903897,None,1.829286825593656,None)},
    "D":{"K0":(2,7),"K1":17,"K2":(2,7,12,17,27,27),
         "M0":38,"M1":0,"D0":12,"D1":0,
         "loss":(1.128626559903897,None,1.829286825593656,None)},
    "E":{"K0":(2,8),"K1":26,"K2":(3,9,16,23,27,27),
         "M0":48,"M1":4,"D0":16,"D1":3,
         "loss":(0.8987285904762992,0.1405720256608662,
                 1.8266474912270843,0.1881715319525468)},
}
CHOICE={"rate_per_minute":1.5,"t_min":20}
TOL=0.77


def need(cond,why):
    if not cond:raise ValueError(why)


def family_rows_m(k0,absolute):
    policy=json.loads(d.POLICY.read_bytes())
    grid=policy["candidate_parameters"]
    pgrid={
        "preparation_tau":grid["preparation_tau_minutes"],
        "dispatch_tau":grid["dispatch_tau_minutes"],
        "shared_cap":grid["shared_preparation_dispatch_capacity_orders_per_hour"],
        "transit_tau":grid["transit_tau_minutes_C01"],
    }
    return m.k0_calibrate([*k0,0,0,0,0],1.2,[0,1],pgrid,
                          1.0,3.0 if absolute else .4)


def family_rows_d(k0,absolute):
    policy=json.loads(d.POLICY.read_bytes())
    obs=[{"t_min":5,"delivered":k0[0]},
         {"t_min":10,"delivered":k0[1]}]
    official=d.calibrate_k0(obs,policy)["compatible"]
    if not absolute:return official
    ds=policy["d_method"]
    families={}
    for stocks in (1,2,3):
        fam="D"+str(stocks)
        rows=[]
        for cap in ds["capacity_items_per_hour"]:
            for tau in ds["shared_response_time_minutes"]:
                curve=d.predicted(stocks,cap,tau,1.2,(5,10))
                mae=sum(abs(x-y) for x,y in zip(curve,k0))/2
                if mae<=1.+1e-12:
                    rows.append({
                        "id":d.candidate_id(stocks,cap,tau),
                        "stocks":stocks,
                        "capacity_per_hour":cap,
                        "shared_response_time_minutes":tau,
                        "K0_mae_orders":mae,
                    })
        families[fam]=rows
    return families


def k1_survive_m(rows,value):
    return {fam:[p for p in cand
                 if abs(m.curve(p,1.5)[3]-value)<=TOL+1e-12]
            for fam,cand in rows.items()}


def k1_survive_d(rows,value):
    return {fam:[p for p in cand
                 if abs(d.predicted(p["stocks"],p["capacity_per_hour"],
                      p["shared_response_time_minutes"],1.5,(20,))[0]
                        -value)<=TOL+1e-12]
            for fam,cand in rows.items()}


def envelope(rows,arm):
    if arm=="M":
        return {f:(
            None if not items else {
                "lower":[min(m.curve(p,1.35)[i] for p in items)
                         for i in range(6)],
                "upper":[max(m.curve(p,1.35)[i] for p in items)
                         for i in range(6)],
                "candidate_count":len(items),
            }) for f,items in rows.items()}
    return {f:d.family_envelope(items,1.35)
            for f,items in rows.items()}


def loss(rows,arm,truth):
    low,high=scoring.combine_family_envelopes(envelope(rows,arm),arm=arm)
    return scoring.summarize_envelope(low,high,list(truth),2.0)


def ids_m(rows):
    return {(f,r["tau_preparation_minutes"],r["tau_dispatch_minutes"],
             r["capacity_per_hour"],r["tau_transit_minutes"])
            for f,items in rows.items() for r in items}


def ids_d(rows):
    return {r["id"] for items in rows.values() for r in items}


def count(rows):
    return {fam:len(items) for fam,items in rows.items()}


def total(rows):
    return sum(len(x) for x in rows.values())


def run_diagnostic():
    policy=json.loads(d.POLICY.read_bytes())
    need(policy["k0"]["model_adequacy_absolute_MAE_orders"]==1.
         and policy["k0"]["model_adequacy_relative_to_family_best_MAE_orders"]==.4
         and policy["k1"]["effective_revision_tolerance_orders"]==TOL,
         "ORIGINAL_POLICY_DRIFT")
    need(list(WORLDS) == list("ABCDE"),"SOURCE_WORLDS_CHANGED")
    results=[]
    memo={}
    for name,obs in WORLDS.items():
        # K0 and K1 are the only evidence used to choose survivors; K2 is
        # passed ONLY to scoring after both policies have been evaluated.
        k0=obs["K0"]
        key=(k0,obs["K1"])
        if key not in memo:
            row={}
            for arm in ("M","D"):
                calibrate=family_rows_m if arm=="M" else family_rows_d
                filt=k1_survive_m if arm=="M" else k1_survive_d
                original=({f:v["eligible"] for f,v in
                           calibrate(k0,False).items()}
                          if arm=="M" else calibrate(k0,False))
                alternative=({f:v["eligible"] for f,v in
                              calibrate(k0,True).items()}
                             if arm=="M" else calibrate(k0,True))
                pre_original=filt(original,obs["K1"])
                post_absolute=filt(alternative,obs["K1"])
                ids=ids_m if arm=="M" else ids_d
                need(ids(original).issubset(ids(alternative)) and
                     ids(pre_original).issubset(ids(post_absolute)),
                     "ABSOLUTE_ONLY_NOT_SUPERSET_OF_ORIGINAL")
                row[arm]={
                    "original_K0":original,
                    "absolute_K0":alternative,
                    "original_K1":pre_original,
                    "absolute_K1":post_absolute,
                    "new_at_K0":len(ids(alternative)-ids(original)),
                    "rescued_at_K1":len(ids(post_absolute)-ids(pre_original)),
                }
            memo[key]=row
        record=memo[key]
        metrics={}
        for arm in ("M","D"):
            row=record[arm]
            low=loss(row["original_K0"],arm,obs["K2"])
            high=loss(row["original_K1"],arm,obs["K2"])
            absolute_k0=loss(row["absolute_K0"],arm,obs["K2"])
            absolute_k1=loss(row["absolute_K1"],arm,obs["K2"])
            expected=obs["loss"][:2] if arm=="M" else obs["loss"][2:]
            for actual,exp in zip((low["set_loss_mean"],
                                   high["set_loss_mean"]),expected):
                need(actual is None if exp is None else
                     actual is not None and abs(actual-exp)<1e-7,
                     "ORIGINAL_PR110_SCORE_MISMATCH")
            metrics[arm]={
                "original_K0_count_by_family":count(row["original_K0"]),
                "original_K1_count_by_family":count(row["original_K1"]),
                "absolute_only_K0_count_by_family":count(row["absolute_K0"]),
                "absolute_only_K1_count_by_family":count(row["absolute_K1"]),
                "new_from_disabling_relative_at_K0":row["new_at_K0"],
                "extra_K1_survivors":row["rescued_at_K1"],
                "original_K0_loss":low["set_loss_mean"],
                "original_K1_loss":high["set_loss_mean"],
                "absolute_only_K0_loss_posthoc":absolute_k0["set_loss_mean"],
                "absolute_only_K1_loss_posthoc":absolute_k1["set_loss_mean"],
                "original_K1_coverage":high["coverage_count"],
                "absolute_only_K1_coverage_posthoc":absolute_k1["coverage_count"],
                "absolute_only_K1_width_mean":absolute_k1.get("mean_envelope_width_orders"),
                "is_retrospective_diagnostic":True,
            }
            need(sum(metrics[arm]["original_K0_count_by_family"].values())
                 ==obs[arm+"0"] and
                 sum(metrics[arm]["original_K1_count_by_family"].values())
                 ==obs[arm+"1"],"ORIGINAL_PR110_CANDIDATE_COUNT_MISMATCH")
        results.append({
            "world":name,
            "public_K0":[*obs["K0"]],
            "reused_K1_measurement":CHOICE,
            "reused_K1_observed":obs["K1"],
            "already_known_K2_used_for_POSTHOC_scoring":[*obs["K2"]],
            "M":metrics["M"],"D":metrics["D"],
        })

    # Astra's specific claim: trace original C01 candidate in world A.
    a=record if False else memo[((2,8),22)]["M"]
    target=[
        x for x in a["absolute_K0"]["C01"]
        if (x["tau_preparation_minutes"],x["tau_dispatch_minutes"],
            x["capacity_per_hour"],x["tau_transit_minutes"])
            ==(1.5,1,72,.25)
    ]
    need(len(target)==1,"ASTRA_C01_CANDIDATE_NOT_IN_GRID")
    match=target[0]
    prediction=m.curve(match,1.5)[3]
    rel_max=min(1.,min(x["k0_mae"] for x in
                       a["absolute_K0"]["C01"])+.4)
    need(match["k0_mae"]<=1. and
         match["k0_mae"]>rel_max and
         abs(prediction-22)<=TOL and
         match in a["absolute_K1"]["C01"],
         "ASTRA_C01_PRUNING_CAUSAL_PATH_NOT_REPRODUCED")
    witness={
        "candidate_parameters":{
            "tau_preparation_minutes":1.5,
            "tau_dispatch_minutes":1,
            "capacity_per_hour":72,
            "tau_transit_minutes":.25,
        },
        "world":"A",
        "family":"C01",
        "K0_mae":match["k0_mae"],
        "C01_relative_K0_cutoff":rel_max,
        "absolute_K0_limit":1.,
        "predicted_K1_deliveries":prediction,
        "observed_K1_deliveries":22,
        "K1_abs_residual":abs(prediction-22),
        "K1_limit":TOL,
        "rejected_only_by_original_K0_relative_pruning":True,
        "would_survive_both_absolute_limits":True,
    }
    return {
        "schema":SCHEMA,
        "classification":"POST_HOC_DIAGNOSTIC_NOT_AN_AUTHORIZED_REANALYSIS",
        "source_public_run":SOURCE_RUN,
        "source_public_artifact":SOURCE_ARTIFACT,
        "worlds":results,
        "unique_K0_K1_signatures":len(memo),
        "no_new_DES_simulations":True,
        "no_change_to_official_policy_or_K1_choice":True,
        "no_external_witness_or_claim":True,
        "original_policy_relative_plus_absolute":True,
        "counterfactual_absolute_K0_only":True,
        "A_C01_candidate_case":witness,
    }


def markdown(data):
    lines=[
        "# CAF-02 — Diagnóstico posterior: poda relativa de K0",
        "",
        "**Solo lectura / post hoc.** Se usan exactamente las observaciones",
        "públicas de PR #110, sin ejecutar DES, sin volver a elegir K1 y",
        "sin cambiar las reglas vigentes de M y D.",
        "",
        f"Origen: {data['source_public_run']}",
        "",
        "Dos políticas comparadas: **original** (MAE K0 ≤1 y ≤mejor",
        "de familia+0.4) frente a **diagnóstica** (MAE K0 ≤1 sin poda",
        "relativa). K1 utiliza la misma observación t20/r=1.5 y",
        "el mismo umbral residual 0.77.",
        "",
        "| Mundo | M candidatos K0 original→absoluto | M tras K1 original→absoluto | D candidatos K0 original→absoluto | D tras K1 original→absoluto |",
        "|---|---:|---:|---:|---:|",
    ]
    def count(x):return sum(x.values())
    for row in data["worlds"]:
        m,d=row["M"],row["D"]
        lines.append(
            f"| {row['world']} | "+
            f"{count(m['original_K0_count_by_family'])}→{count(m['absolute_only_K0_count_by_family'])} | "+
            f"{count(m['original_K1_count_by_family'])}→{count(m['absolute_only_K1_count_by_family'])} | "+
            f"{count(d['original_K0_count_by_family'])}→{count(d['absolute_only_K0_count_by_family'])} | "+
            f"{count(d['original_K1_count_by_family'])}→{count(d['absolute_only_K1_count_by_family'])} |")
    lines+=["","## K2: pérdida retrospectiva (no es nueva predicción prospectiva)","",
        "| Mundo | M original L1 | M absoluto L1 | D original L1 | D absoluto L1 |",
        "|---|---:|---:|---:|---:|",
    ]
    def f(v):return "abstención" if v is None else f"{v:.5f}"
    for row in data["worlds"]:
        m,d=row["M"],row["D"]
        lines.append(f"| {row['world']} | {f(m['original_K1_loss'])} | "+
                     f"{f(m['absolute_only_K1_loss_posthoc'])} | "+
                     f"{f(d['original_K1_loss'])} | "+
                     f"{f(d['absolute_only_K1_loss_posthoc'])} |")
    w=data["A_C01_candidate_case"]
    lines+=["","## Caso individual C01 señalado por Astra","",
        f"- C01 con τ_preparación=1.5, τ_despacho=1, cap=72/h, τ_tránsito=.25.",
        f"- MAE K0={w['K0_mae']:.5f}; corte relativo C01={w['C01_relative_K0_cutoff']:.5f}; límite absoluto=1.",
        f"- K1 predicho={w['predicted_K1_deliveries']:.5f}; observado=22; residuo={w['K1_abs_residual']:.5f} ≤0.77.",
        "- El candidato está en la rejilla original. Su rechazo ocurre **antes** de K1 por la poda relativa.",
        "","## Interpretación y límites","",
        "- El contraste es **retrospectivo**: K1 fue diseñado para los",
        "conjuntos originales, NO rediseñado ex ante para la alternativa.",
        "- Cambiar la política K0 también podría cambiar la elección K1",
        "y el coste/valor de la medición: **no** estamos estimando eso aquí.",
        "- La ampliación de soporte puede ensanchar las envolventes K2",
        "y empeorar L_set aun cuando rescate una familia estructural.",
        "- B/C/D comparten exactamente las mismas observaciones y constituyen",
        "una sola firma observable, no tres evidencias independientes.",
        "- Todos los valores K2 usados aquí ya eran conocidos; ninguna",
        "mejora de pérdida retrospectiva acredita rendimiento prospectivo.",
        "- No modificar la política original en función de esta comparación.",
        "Si después se prueban otros mundos, declarar ambas reglas ANTES",
        "de producir sus nuevas observaciones.",
        "",
    ]
    return "\n".join(lines)


def csv_summary(data):
    buf=io.StringIO(newline="")
    w=csv.writer(buf)
    w.writerow(["world","arm","K0_original_n","K0_absolute_n",
                "K1_original_n","K1_absolute_n","rescued_after_K1",
                "original_K1_loss","absolute_K1_posthoc_loss"])
    for row in data["worlds"]:
        for arm in ("M","D"):
            r=row[arm]
            w.writerow([row["world"],arm,
                        sum(r["original_K0_count_by_family"].values()),
                        sum(r["absolute_only_K0_count_by_family"].values()),
                        sum(r["original_K1_count_by_family"].values()),
                        sum(r["absolute_only_K1_count_by_family"].values()),
                        r["extra_K1_survivors"],
                        r["original_K1_loss"],
                        r["absolute_only_K1_loss_posthoc"]])
    return buf.getvalue()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    need(not a.out.exists(),"POSTHOC_OUTPUT_EXISTS")
    report=run_diagnostic()
    a.out.mkdir(parents=True)
    lab.write_new(a.out,"POSTHOC_01_RESULTADOS.json",report)
    lab.write_new(a.out,"POSTHOC_02_COMPARACION.csv",csv_summary(report))
    lab.write_new(a.out,"POSTHOC_03_INFORME.md",markdown(report))
    print(json.dumps({
        "classification":report["classification"],
        "no_new_DES_simulations":report["no_new_DES_simulations"],
        "unique_signatures":report["unique_K0_K1_signatures"],
        "comparison":[{
            "world":row["world"],
            "M_after_K1":[sum(row["M"]["original_K1_count_by_family"].values()),
                          sum(row["M"]["absolute_only_K1_count_by_family"].values())],
            "D_after_K1":[sum(row["D"]["original_K1_count_by_family"].values()),
                          sum(row["D"]["absolute_only_K1_count_by_family"].values())],
        } for row in report["worlds"]],
    },sort_keys=True))


if __name__=="__main__":
    main()
