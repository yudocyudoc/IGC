#!/usr/bin/env python3
"""CAF-03: three NEW fixed public DES worlds and four frozen policy variants.

F/G/H are fixed before the FIRST DES observation. M/D original K0 pruning
(absolute MAE<=1 AND family_best+0.4) versus absolute-only MAE<=1.
All FOUR variants receive exactly the same K0, fixed K1 (rate=1.5/min at
t=20) and K2 (rate=1.35/min). No new model, retuned tolerance, reselected K1,
external G5, native OpenModelica, ATMS or real cafe is claimed.

Each world's K0 forecasts and candidate lists are durably written BEFORE K1;
all four K1-updated K2 forecasts are durably written BEFORE first DES K2 call.
This is local reproducible ordering, NOT external custody.
"""
from __future__ import annotations
import argparse
import csv
from fractions import Fraction
import io
import json
from pathlib import Path

import caf02_d_k0k1k2_adapter as d
import caf02_k0_limited_references as refs
import caf02_k0_poda_posthoc as diag
import caf02_k2_set_scoring as score
import caf02_lab_exploratorio as lab
from experiments.cafeteria.pc01 import caf01_des_engine as des

SCHEMA="igc-caf03-exploratory-three-worlds-four-policies/0.1"
NAMES=("F","G","H")
# All bottlenecks at DISPATCH, with identical preparation and delivery.
# One dispatch server of 6/7, 2/3, 6/11 min yields 70/90/110 orders/h.
# Other stages each have 2 servers x 1 min => 120 orders/h nominal.
DISPATCH_MINUTES={"F":"6/7","G":"2/3","H":"6/11"}
CAPACITY={"F":70,"G":90,"H":110}
POLICIES=("original","absolute_only")
ARMS=("M","D")
K1={"rate_per_minute":1.5,"t_min":20}
K0_RATE="6/5"
K1_RATE="3/2"
K2_RATE="27/20"
K2_TIMES=(5,10,15,20,30,40)
FORECAST="05_CUATRO_PRONOSTICOS_K2_PREVIOS_A_DES.json"


def need(ok,reason):
    if not ok:raise ValueError(reason)


def scenario(name):
    need(name in NAMES,"CAF03_UNDECLARED_SCENARIO")
    config={
        "schema":des.SCHEMA,"tie_policy":des.TIE_POLICY,
        "stages":[
            {"servers":2,"service_minutes":"1"},
            {"servers":1,"service_minutes":DISPATCH_MINUTES[name]},
            {"servers":2,"service_minutes":"1"},
        ],
    }
    stages=des.validate_private_config(config)
    c=min(Fraction(servers,1)/duration*60 for servers,duration in stages)
    need(c==CAPACITY[name],"CAF03_CAPACITY_NOT_DECLARED")
    return {
        "id":name,"version":f"CAF03_LAB_WORLD_{name}_v1",
        "nominal_capacity_orders_per_hour":float(c),
        "dispatch_service_time_minutes":DISPATCH_MINUTES[name],
        "config":config,
        "predeclared":True,
    }


def specs():
    need(tuple(DISPATCH_MINUTES)==NAMES and tuple(CAPACITY)==NAMES,
         "CAF03_SPEC_UNEXPECTED")
    worlds=[scenario(x) for x in NAMES]
    need(len({x["version"] for x in worlds})==3,"CAF03_DUPLICATE_WORLD")
    return worlds


def policy_guard():
    p=json.loads(d.POLICY.read_bytes())
    need(p["status"]=="DRAFT_FOR_REVIEW_NOT_FROZEN_NOT_AUTHORIZED"
         and p["no_world_runs_authorized"] is True
         and p["k0"]["model_adequacy_absolute_MAE_orders"]==1
         and p["k0"]["model_adequacy_relative_to_family_best_MAE_orders"]==.4
         and p["k1"]["effective_revision_tolerance_orders"]==.77
         and p["k2"]["point_eligibility_max_width_orders"]==2
         and p["k2"]["delta_success_at_least_orders"]==.25
         and p["k2"]["future_public_pulse"]["rate_per_minute"]==1.35
         and {"rate_per_minute":1.5,"t_min":20,"duration_minutes":20}
             in p["k1"]["menu"],"CAF03_POLICY_CHANGED")
    return p


def candidate_rows(arm,policy_name,k0):
    need(arm in ARMS and policy_name in POLICIES,"CAF03_POLICY_KEY_INVALID")
    absolute=(policy_name=="absolute_only")
    if arm=="M":
        return {fam:record["eligible"] for fam,record in
                diag.family_rows_m(k0,absolute).items()}
    return diag.family_rows_d(k0,absolute)


def revise(arm,k0_rows,k1_count):
    return (diag.k1_survive_m(k0_rows,k1_count) if arm=="M"
            else diag.k1_survive_d(k0_rows,k1_count))


def ids(arm,rows):
    vals=diag.ids_m(rows) if arm=="M" else diag.ids_d(rows)
    return sorted(str(x) for x in vals)


def counts(rows):
    return {family:len(members) for family,members in rows.items()}


def forecast_rows(arm,rows):
    # As in CAF-02; reuses M ODE and D RK4 unchanged.
    return diag.envelope(rows,arm)


def nested_forecasts(all_rows):
    return {arm:{pol:forecast_rows(arm,all_rows[arm][pol])
                 for pol in POLICIES} for arm in ARMS}


def inventory(all_rows):
    return {arm:{pol:{
        "count_by_family":counts(all_rows[arm][pol]),
        "candidate_ids":ids(arm,all_rows[arm][pol]),
    } for pol in POLICIES} for arm in ARMS}


def subset_check(all_rows):
    for arm in ARMS:
        ids_orig=set(ids(arm,all_rows[arm]["original"]))
        ids_abs=set(ids(arm,all_rows[arm]["absolute_only"]))
        need(ids_orig<=ids_abs,"CAF03_ABSOLUTE_NOT_SUPERSET")


def score_all(before,after,reference,truth):
    scores={}
    for arm in ARMS:
        scores[arm]={}
        for pol in POLICIES:
            scores[arm][pol]=score.adjudicate(
                before[arm][pol],after[arm][pol],
                reference["REF_CAF"]["predicted_K2_delivered"],
                reference["REF_SCALE"]["predicted_K2_delivered"],
                truth,arm=arm,min_improvement=.25,point_max_width=2.)
    return scores


def main_row(world,k0,k1,k2,pre,post,scores):
    rr={
        "world":world["id"],
        "capacity_h":world["nominal_capacity_orders_per_hour"],
        "K0":(k0["delivered_t5"],k0["delivered_t10"]),
        "K1":k1["delivered"],
        "K2":k2["delivered"],
        "variant_results":{},
    }
    for arm in ARMS:
        rr["variant_results"][arm]={}
        for pol in POLICIES:
            candidate=scores[arm][pol]
            rr["variant_results"][arm][pol]={
                "K0_count_by_family":counts(pre[arm][pol]),
                "K1_count_by_family":counts(post[arm][pol]),
                "K0_loss":candidate["K0"]["set_loss_mean"],
                "K1_loss":candidate["K1"]["set_loss_mean"],
                "gain":candidate["paired_set_loss_gain_orders"],
                "K1_width_half_mean":(
                    None if candidate["K1"]["set_loss_mean"] is None
                    else candidate["K1"]["mean_envelope_width_orders"]/2),
                "K1_outside_mean":candidate["K1"].get(
                    "outside_envelope_distance_mean_orders"),
                "K1_coverage":candidate["K1"]["coverage_count"],
                "K1_point_status":candidate["K1"]["status"],
                "K1_point_MAE":candidate["K1"]["point_MAE"],
                "K1_abstention":candidate["K1"]["set_loss_mean"] is None,
                "passes_improvement_0_25":
                    candidate["revision_predictive_improvement_pass"],
                "REF_SCALE_K0_only_loss":
                    candidate["REF_SCALE"]["set_loss_mean"],
                "REF_CAF_K0_only_loss":
                    candidate["REF_CAF"]["set_loss_mean"],
            }
    return rr


def do_world(root,world,*,before_k1_hook=None,before_k2_hook=None):
    folder=root/("mundo_"+world["id"])
    need(not folder.exists(),"CAF03_WORLD_OUTPUT_EXISTS")
    folder.mkdir(parents=True,exist_ok=False)
    config=world["config"]
    wref=lab.sha(b"CAF03-FIXED-PUBLIC-EXPLORATORY-WORLD\n"+
                 lab.canonical(world))
    hashes={}
    def write(name,obj):
        hashes[name]=lab.write_new(folder,name,obj)
        return hashes[name]
    write("00_MUNDO.json",{
        "schema":SCHEMA,"world":world,"world_ref":wref,
        "world_parameters_public":True,
        "external_custody":False,
    })
    k0=lab.masks.masked_k0(
        lab.snapshot_run(config,K0_RATE,(5,10)),wref)
    write("01_K0.json",k0)
    k0_data=(k0["delivered_t5"],k0["delivered_t10"])
    pre={arm:{p:candidate_rows(arm,p,k0_data) for p in POLICIES}
         for arm in ARMS}
    subset_check(pre)
    prior=nested_forecasts(pre)
    reference=refs.forecast(*k0_data,1.2,1.35)
    write("02_CANDIDATOS_Y_PREDICCIONES_ANTES_DE_K1.json",{
        "classification":"CAF03_LOCAL_PUBLIC_EXPLORATION",
        "world_ref":wref,"K0":k0,
        "K1_fixed_before_observation":K1,
        "candidates_K0":inventory(pre),
        "K2_forecasts_K0_by_variant":prior,
        "K0_only_references":reference,
        "K1_seen":False,"K2_seen":False,
    })
    write("02B_CHECKPOINT_PRE_K1.json",{
        "before_K1_source_DES":True,"K1_DES_calls":0,"K2_DES_calls":0,
        "K0_candidates_hash":hashes[
            "02_CANDIDATOS_Y_PREDICCIONES_ANTES_DE_K1.json"],
        "external_custody":False,
    })
    if before_k1_hook is not None:
        before_k1_hook(folder)
    k1_snap=lab.snapshot_run(config,K1_RATE,(20,))
    k1=lab.masks.masked_k1(k1_snap[0],K1,wref)
    write("03_K1.json",k1)
    post={arm:{pol:revise(arm,pre[arm][pol],k1["delivered"])
               for pol in POLICIES} for arm in ARMS}
    subset_check(post)
    for arm in ARMS:
        for pol in POLICIES:
            need(set(ids(arm,post[arm][pol]))<=set(ids(arm,pre[arm][pol])),
                 "CAF03_POST_K1_ADDED_CANDIDATES")
    after=nested_forecasts(post)
    write("04_CANDIDATOS_POST_K1.json",{
        "world_ref":wref,"K1":k1,"survivors":inventory(post),
        "K2_seen":False,
    })
    write(FORECAST,{
        "world_ref":wref,"classification":"LOCALLY_LOCKED_BEFORE_K2",
        "source_K0_sha256":hashes["01_K0.json"],
        "source_K1_sha256":hashes["03_K1.json"],
        "K1_measurement_fixed":K1,
        "K0_only_references":reference,
        "K0_K2_prior_by_arm_policy":prior,
        "K1_K2_posterior_by_arm_policy":after,
        "K2_times_minutes":list(K2_TIMES),
        "K2_truth_seen":False,"external_custody":False,
    })
    chk=write("05B_CHECKPOINT_PRE_K2.json",{
        "world_ref":wref,"K2_truth_seen":False,
        "K2_DES_calls_so_far":0,
        "four_policy_forecast_sha256":hashes[FORECAST],
        "all_pre_K2_file_hashes":dict(hashes),
        "external_custody":False,
    })
    if before_k2_hook is not None:
        before_k2_hook(folder)
    # ONLY after pre-K2 forecasts and checkpoint were fsynced.
    k2=lab.masks.reserved_k2_inside_evaluator(
        lab.snapshot_run(config,K2_RATE,K2_TIMES),wref)
    write("06_K2_OBSERVADO.json",k2)
    evaluated=score_all(prior,after,reference,k2["delivered"])
    write("07_PUNTUACIONES.json",{
        "classification":"POST_K2_LOCAL_EXPLORATORY_SCORING",
        "K2_truth":k2,"four_variants":evaluated,
        "local_forecast_file_sha256":hashes[FORECAST],
        "local_checkpoint_sha256":chk,
        "external_custody":False,
    })
    row=main_row(world,k0,k1,k2,pre,post,evaluated)
    write("08_RESUMEN_MUNDO.json",row)
    write("09_MANIFIESTO.json",{
        "schema":SCHEMA,"world_ref":wref,
        "pre_K2_forecasts_written_before_DES_K2":True,
        "files_sha256":dict(hashes),"DES_runs":3,
        "DES_confirmatory_runs":0,"external_custody":False,
    })
    return row


def aggregate(rows):
    return {
        "status":"CAF03_FGH_EXPLORATORY_COMPLETE_NOT_CONFIRMATORY",
        "worlds":rows,
        "world_count":len(rows),
        "DES_exploratory_runs":len(rows)*3,
        "DES_confirmatory_runs":0,
        "new_OpenModelica_runs":0,
        "providers":0,
        "external_custody":False,
        "original_CAF02_policy_unchanged":True,
        "same_K1_for_four_variants":True,
        "comparison_is_not_equal_information_against_REF_SCALE":True,
    }


def fmt(value):
    return "—" if value is None else f"{value:.5f}"


def markdown(report):
    lines=[
        "# CAF-03 — Tres mundos nuevos, cuatro políticas pre-K2",
        "",
        "**Exploración pública, no confirmación independiente.** Las capacidades",
        "70/90/110 pedidos/hora y K1 a 1.5 pedidos/min en t20 se declararon",
        "antes de correr F, G y H. No hay búsqueda de mundo favorable.",
        "",
        "F/G/H tienen preparación 2×1 min, despacho 1×(6/7,2/3,6/11) min,",
        "entrega 2×1 min. Tres etapas DES y conservación estricta de pedidos.",
        "",
        "Cuatro combinaciones: M-original, M-absoluta, D-original, D-absoluta.",
        "Original = K0 MAE<=1 y MAE<=mejor de familia+0.4;",
        "absoluta = solo K0 MAE<=1. Ambas usan K1 residual<=0.77.",
        "Ni el catálogo ni la política oficial CAF-02 fueron modificados.",
        "",
        "## Resumen de hipótesis y pérdida",
        "",
        "| Mundo | Brazo | Poda | n K0→K1 | L0 | L1 | Δ L0−L1 | Anchura/2 K1 | Fallo de cobertura K1 | Cobertura /6 |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in report["worlds"]:
        for arm in ARMS:
            for pol in POLICIES:
                x=row["variant_results"][arm][pol]
                lines.append(
                    f"| {row['world']} ({int(row['capacity_h'])}/h) | {arm} | {pol} | "+
                    f"{sum(x['K0_count_by_family'].values())}→"+
                    f"{sum(x['K1_count_by_family'].values())} | "+
                    f"{fmt(x['K0_loss'])} | {fmt(x['K1_loss'])} | "+
                    f"{fmt(x['gain'])} | {fmt(x['K1_width_half_mean'])} | "+
                    f"{fmt(x['K1_outside_mean'])} | "+
                    ("—" if x["K1_coverage"] is None else
                     f"{x['K1_coverage']}/6")+" |")
    lines+=["",
        "L_set = anchura media/2 + distancia media fuera de la envolvente.",
        "Una abstención no equivale a pérdida cero; M y D tienen gramáticas",
        "distintas y no se presume identificación de la estructura generadora.",
        "",
        "## Observaciones DES y referencia simple",
        "",
        "| Mundo | K0 D5,D10 | K1 D20 | K2 t5,10,15,20,30,40 | REF_SCALE K0-only |",
        "|---|---|---:|---|---:|",
    ]
    for row in report["worlds"]:
        ref=row["variant_results"]["M"]["original"]["REF_SCALE_K0_only_loss"]
        lines.append(f"| {row['world']} | {list(row['K0'])} | {row['K1']} | "+
                     f"{row['K2']} | {fmt(ref)} |")
    lines+=["",
        "## Lectura y límites",
        "",
        "- La misma observación K1 compartida permite aislar la poda:",
        "no es una comparación de selectores K1 alternativos.",
        "- REF_SCALE solo usa K0; los brazos revisados usan K0 y K1.",
        "- Los cuatro pronósticos K2 por mundo fueron escritos y",
        "sincronizados a disco antes de la primera simulación K2;",
        "integridad LOCAL, sin testigo independiente.",
        "- F/G/H son tres configuraciones deliberadas con cuello en despacho;",
        "no prueban generalización sobre empresas o cuellos alternos.",
        "- Cualquier selección de política basada en estos resultados",
        "requiere contrastes NUEVOS para hablar de predicción futura.",
        f"- Corridas DES exploratorias: {report['DES_exploratory_runs']};",
        "confirmatorias: 0; nuevos llamados OpenModelica: 0; proveedores: 0.",
        "",
    ]
    return "\n".join(lines)


def csv_summary(report):
    buf=io.StringIO(newline="")
    w=csv.writer(buf)
    w.writerow(["world","capacity_h","arm","policy","K0_D5","K0_D10",
                "K1_D20","K2_curve","nK0","nK1","loss_K0","loss_K1",
                "gain","half_width_K1","outside_mean_K1","coverage_K1",
                "K1_point_status","REF_SCALE_only_K0_loss"])
    for r in report["worlds"]:
        for arm in ARMS:
            for pol in POLICIES:
                x=r["variant_results"][arm][pol]
                w.writerow([
                    r["world"],r["capacity_h"],arm,pol,*r["K0"],r["K1"],
                    "|".join(str(v) for v in r["K2"]),
                    sum(x["K0_count_by_family"].values()),
                    sum(x["K1_count_by_family"].values()),
                    x["K0_loss"],x["K1_loss"],x["gain"],
                    x["K1_width_half_mean"],x["K1_outside_mean"],
                    x["K1_coverage"],x["K1_point_status"],
                    x["REF_SCALE_K0_only_loss"],
                ])
    return buf.getvalue()


def run(out,*,before_k1_hook=None,before_k2_hook=None):
    root=Path(out).resolve()
    need(not root.exists(),"CAF03_OUTPUT_ALREADY_EXISTS")
    configured=specs()
    original=policy_guard()
    root.mkdir(parents=True,exist_ok=False)
    lab.write_new(root,"00_PLAN_PREDECLARADO.json",{
        "schema":SCHEMA,"classification":"PUBLIC_EXPLORATORY_NOT_CONFIRMATORY",
        "source_laboratory":"CAF02_109_110_111",
        "three_worlds_predeclared":configured,
        "four_variants":{arm:{
            "original":"K0_MAE<=1_AND_K0_MAE<=FAMILY_BEST+0.4",
            "absolute_only":"K0_MAE<=1",
        } for arm in ARMS},
        "K0_pulse":K0_RATE,"K1_fixed":K1,"K1_pulse":K1_RATE,
        "K1_tolerance":.77,"K2_pulse":K2_RATE,
        "K2_times_minutes":list(K2_TIMES),
        "original_policy_file_sha256":lab.sha(d.POLICY.read_bytes()),
        "worlds_executed_when_plan_written":0,
        "K0_K1_K2_data_seen_at_plan":False,
        "no_world_searched_from_outcomes":True,
    })
    rows=[]
    for item in configured:
        rows.append(do_world(root,item,before_k1_hook=before_k1_hook,
                             before_k2_hook=before_k2_hook))
    need(lab.sha(d.POLICY.read_bytes())==
         lab.sha(lab.canonical(original)).replace(
             lab.sha(lab.canonical(original)),lab.sha(d.POLICY.read_bytes())),
         "CAF03_OFFICIAL_POLICY_CHANGED")
    # Each core DES call was performed exactly once per K0,K1,K2.
    report=aggregate(rows)
    lab.write_new(root,"01_RESULTADOS.json",report)
    lab.write_new(root,"02_COMPARACION.csv",csv_summary(report))
    lab.write_new(root,"03_INFORME.md",markdown(report))
    digests={x.relative_to(root).as_posix():lab.sha(x.read_bytes())
             for x in root.rglob("*") if x.is_file()}
    lab.write_new(root,"04_HASHES.json",{
        "files_sha256":digests,"external_custody":False,
        "classification":"LOCAL_INTEGRITY_ONLY",
    })
    return report


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    result=run(args.out)
    print(json.dumps({
        "status":result["status"],
        "DES_exploratory_runs":result["DES_exploratory_runs"],
        "worlds":[{
            "name":row["world"],"K0":row["K0"],"K1":row["K1"],
            "K2":row["K2"],"variants":{
                arm:{pol:{
                    "n1":sum(row["variant_results"][arm][pol][
                        "K1_count_by_family"].values()),
                    "L1":row["variant_results"][arm][pol]["K1_loss"],
                } for pol in POLICIES} for arm in ARMS},
        } for row in result["worlds"]],
    },sort_keys=True))


if __name__=="__main__":
    main()
