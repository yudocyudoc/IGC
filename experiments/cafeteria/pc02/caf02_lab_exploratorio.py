#!/usr/bin/env python3
"""CAF-02 EXPLORATORY LAB: one complete DES -> M/D -> K1 -> K2 run.

This deliberately does NOT execute the formal independently witnessed CAF-02
campaign. All world parameters are visible in source and output. It reuses
the fixed M/D policy and the independent discrete-event *mechanism*, but is
a single publicly defined toy-world experiment. No retries, no parameter
search, no external G5, no providers, no real-world validation.

Ordering is enforced in code and files: 02 G4a before K1, 04 G4b and
05 forecasts+checkpoint fully fsynced BEFORE K2 is simulated. This local
write ordering is reproducible, NOT tamper-proof external custody.
"""
from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import io
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
for path in (str(ROOT),str(HERE)):
    if path not in sys.path:
        sys.path.insert(0,path)

from experiments.cafeteria.pc01 import caf01_des_engine as des
import caf02_private_source_boundary as masks
import caf02_public_cut_bridge as bridge
import caf02_d_k0k1k2_adapter as d
import caf02_k2_adjudicator_boundary as adjudicator

SCHEMA="igc-caf02-exploratory-lab-one-world/0.1"
LABEL="EXPLORATORY_PUBLIC_TOY_WORLD_NOT_INDEPENDENT_CONFIRMATION"
VERSION="CAF02_LAB_WORLD_A_v1"

# Fixed BEFORE any exploratory observations, openly inspectable in this PR.
# Two preparers, each 1.5 min; one dispatcher, 0.75 min; two handoff servers,
# each 1.5 min. Shared nominal bottleneck is 4/3 orders per minute. A
# saturated-but-moderate delivery system, never selected from model fit.
WORLD={
    "schema":des.SCHEMA,
    "tie_policy":des.TIE_POLICY,
    "stages":[
        {"servers":2,"service_minutes":"3/2"},
        {"servers":1,"service_minutes":"3/4"},
        {"servers":2,"service_minutes":"3/2"},
    ],
}
RATES={"K0":"6/5","K2":"27/20"}
FORECAST_FILE="05_PRONOSTICOS_K2_ANTES_DE_VER_VERDAD.json"


class LabBlocked(ValueError):
    pass


def need(condition,reason):
    if not condition:
        raise LabBlocked(reason)


def sha(data):
    return "sha256:"+sha256(data).hexdigest()


def canonical(obj):
    return bridge.canonical(obj)


def write_new(folder,name,data):
    """Exclusive, durable writes; never overwrite even after an interrupted run."""
    target=folder/name
    raw=canonical(data) if isinstance(data,(dict,list)) else data.encode("utf-8")
    with target.open("xb") as f:
        f.write(raw)
        f.flush()
        import os
        os.fsync(f.fileno())
    return sha(raw)


def snapshot_run(config,rate,times):
    """Fresh discrete-event reset; last observation at t40 includes all arrivals.

    Runs at most once for each of K0, chosen K1 and K2. No source parameter
    tuning or retry. Only the masked information is passed to M/D.
    """
    need(type(times) is tuple and times and
         all(type(t) is int and 0<t<=40 for t in times),
         "LAB_SAMPLE_TIMES_INVALID")
    arrivals=des.half_open_arrivals(rate,20)
    desired=(0,*times)
    if times[-1]<40:
        desired=(*desired,40)
    snapshots=des.run_toy_engine(config,arrivals,desired)
    return snapshots[1:len(times)+1]


def public_world():
    stages=des.validate_private_config(WORLD)
    need(len(stages)==3 and stages==((2,des.Fraction(3,2)),
                                    (1,des.Fraction(3,4)),
                                    (2,des.Fraction(3,2))),
         "LAB_PUBLIC_WORLD_CHANGED")
    world_ref=sha(b"CAF02-EXPLORATORY-PUBLIC-WORLD-V1\n"+
                  canonical({"world":WORLD,"version":VERSION}))
    return {
        "schema":SCHEMA,"label":LABEL,"world_name":VERSION,
        "world_precommitment_ref":world_ref,
        "world_parameters_are_public_not_secret":True,
        "world_parameters":WORLD,
        "source_engine":"experiments/cafeteria/pc01/caf01_des_engine.py",
        "source_engine_sha256":sha((ROOT/"experiments/cafeteria/pc01/caf01_des_engine.py").read_bytes()),
        "policy_source":d.POLICY.name,
        "policy_sha256":sha(d.POLICY.read_bytes()),
        "model_selection_did_not_use_observed_K2":True,
        "external_G5_witness":False,
        "formal_CAF02_trial_authorized_or_executed":False,
    }


def predictions_only(g4a,g4b):
    bridge.checked_receipt(g4a)
    bridge.checked_receipt(g4b)
    need(g4b["parent_G4a_candidate_sha256"]==g4a["candidate_sha256"],
         "LAB_WRONG_G4A_G4B_PARENT")
    return {
        "schema":"igc-caf02-exploratory-locked-predictions/0.1",
        "status":"LOCALLY_WRITTEN_BEFORE_FIRST_K2_ENGINE_CALL",
        "world_ref":g4a["world_precommitment_ref"],
        "g4a_candidate_sha256":g4a["candidate_sha256"],
        "g4b_candidate_sha256":g4b["candidate_sha256"],
        "K1_chosen_before_observing_K1":g4a["K1_preselected_common"]["proposed_measurement"],
        "K1_used":g4b["K1_used"],
        "times_minutes":list(bridge.TIMES),
        "M_K0_by_family":g4a["K2_prior_M_by_family"],
        "M_K1_by_family":g4b["K2_revised_M_by_family"],
        "D_K0_by_family":g4a["K2_prior_D_by_family"],
        "D_K1_by_family":g4b["K2_revised_D_by_family"],
        "references_only_K0":g4a["K2_K0_only_references"],
        "K2_truth_read":False,
        "external_custody_claim":False,
    }


def counts(envelopes):
    return {family:(None if record is None else record["candidate_count"])
            for family,record in envelopes.items()}


def mean_text(value):
    return "— (abstención)" if value is None else f"{value:.5f}"


def report_md(result):
    a,b=result["G4a_summary"],result["G4b_summary"]
    scores=result["scores"]
    lines=[
        "# CAF-02 · Primera ejecución exploratoria completa",
        "",
        "**Clasificación:** laboratorio DES público, no ensayo confirmatorio.",
        f"**Mundo:** {VERSION}, preparación 2×1.5 min; despacho 1×0.75 min; entrega 2×1.5 min.",
        "**Límite nominal:** 4/3 pedidos/minuto (80/h); sin cancelaciones, stocks vacíos por corte.",
        "**Mecanismo:** simulador discreto de servidores y colas; no son observaciones de una cafetería real.",
        "**Integridad:** pronósticos y hashes guardados antes de simular K2; sin testigo externo.",
        "",
        "## Observaciones del mundo DES",
        "",
        f"- K0 público: entregados t5={result['K0']['delivered_t5']}, t10={result['K0']['delivered_t10']}.",
        f"- K1 común: {result['K1'] if result['K1'] is not None else 'no ejecutado (sin hipótesis)'}",
        f"- K2 DES: {result['K2']['delivered']} a t={list(bridge.TIMES)} minutos.",
        f"- Corridas DES del **laboratorio exploratorio**: {result['exploratory_DES_runs']}; corridas del ensayo confirmatorio: **0**.",
        "",
        "## Hipótesis y pronósticos por brazo",
        "",
        "| Brazo | K0 por familia | K1 por familia | L(K0) | L(K1) | Ganancia K0−K1 | Veredicto |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for arm in ("M","D"):
        row=scores[arm]
        lines.append(
            f"| {arm} | {a[arm]} | {b[arm]} | "+
            f"{mean_text(row['K0']['set_loss_mean'])} | "+
            f"{mean_text(row['K1']['set_loss_mean'])} | "+
            f"{mean_text(row['paired_set_loss_gain_orders'])} | "+
            f"{'mejora >= 0.25' if row['revision_predictive_improvement_pass'] is True else 'no mejora >= 0.25' if row['revision_predictive_improvement_pass'] is False else 'no emparejable / abstención'} |")
    lines+=["",
        "La pérdida de conjuntos es **no probabilística**: mitad de amplitud media más distancia fuera de envolvente.",
        "No se imputa error cero si hay abstención. Menor pérdida es mejor.",
        "",
        "## Predicción por tiempo",
        "",
        "| t (min) | K2 observado DES | M K0 intervalo | M K1 intervalo | D K0 intervalo | D K1 intervalo |",
        "|---:|---:|---|---|---|---|",
    ]
    def interval(arm,cut,i):
        from caf02_k2_set_scoring import combine_family_envelopes
        env=result["predictions"][f"{arm}_{cut}_by_family"]
        low,high=combine_family_envelopes(env,arm=arm)
        return "abstención" if low is None else f"[{low[i]:.2f}, {high[i]:.2f}]"
    for i,t in enumerate(bridge.TIMES):
        lines.append(f"| {t} | {result['K2']['delivered'][i]} | "+
                     " | ".join(interval(arm,cut,i)
                                for arm,cut in (("M","K0"),("M","K1"),
                                                ("D","K0"),("D","K1")))+" |")
    lines+=["",
        "## Referencias K0-only y límites",
        "",
        f"- REF_CAF: {mean_text(scores['M']['REF_CAF']['set_loss_mean'])}; "+
          f"REF_SCALE: {mean_text(scores['M']['REF_SCALE']['set_loss_mean'])}.",
        "- Las referencias usan **solo K0**, así que no establecen ventajas a igualdad de información frente a un método actualizado con K1.",
        "- No se identifica la estructura verdadera por un ajuste de rejilla; son candidatos compatibles.",
        "- Un solo mundo DES diseñado y visible **no** demuestra generalización ni separación causal.",
        "- Los parámetros y el K2 ya se conocen tras esta ejecución; **no reutilizar esta misma corrida como confirmación ciega**.",
        "- G2 nativo previo: 15/15 en un experimento de correspondencia distinto; aquí no se invocó OpenModelica.",
        "- ATMS D persistido: no acreditado. Buffalo/proveedores: cero.",
        "",
        "## Huellas locales de orden",
        "",
        f"- G4a: \`{result['g4a_sha256']}\`.",
        f"- G4b: \`{result['g4b_sha256']}\`.",
        f"- Archivo de pronósticos pre-K2: \`{result['predictions_file_sha256']}\`.",
        f"- Checkpoint pre-K2: \`{result['checkpoint_sha256']}\`.",
        "",
        "*Estas huellas son reproducibles, no firmas independientes ni garantías frente a reescritura maliciosa.*",
        "",
    ]
    return "\n".join(lines)


def csv_table(result):
    from caf02_k2_set_scoring import combine_family_envelopes
    buf=io.StringIO(newline="")
    w=csv.writer(buf)
    w.writerow(["minute","DES_K2_integer","M_K0_lo","M_K0_hi",
                "M_K1_lo","M_K1_hi","D_K0_lo","D_K0_hi",
                "D_K1_lo","D_K1_hi"])
    ranges={}
    for arm in ("M","D"):
        for cut in ("K0","K1"):
            ranges[arm,cut]=combine_family_envelopes(
                result["predictions"][f"{arm}_{cut}_by_family"],arm=arm)
    for i,t in enumerate(bridge.TIMES):
        row=[t,result["K2"]["delivered"][i]]
        for arm,cut in (("M","K0"),("M","K1"),("D","K0"),("D","K1")):
            lo,hi=ranges[arm,cut]
            row.extend(["",""] if lo is None else [lo[i],hi[i]])
        w.writerow(row)
    return buf.getvalue()


def run_lab(out,*,after_checkpoint_hook=None):
    """One public toy world only; no search/automated retry or G5 bypass.

    Hook is for software tests to verify ordering and fail-before-K2.
    A crashed run is left incomplete. Use a NEW output directory to repeat,
    marked as a new exploratory run.
    """
    folder=Path(out).resolve()
    need(not folder.exists(),"LAB_OUTPUT_ALREADY_EXISTS")
    policy=json.loads(d.POLICY.read_text(encoding="utf-8"))
    need(policy["status"]=="DRAFT_FOR_REVIEW_NOT_FROZEN_NOT_AUTHORIZED"
         and policy["no_world_runs_authorized"] is True,
         "LAB_MUST_NOT_OVERWRITE_FORMAL_POLICY")
    des.validate_private_config(WORLD)
    world=public_world()
    folder.mkdir(parents=True,exist_ok=False)
    hashes={}
    runs=0
    hashes["00_MUNDO_PUBLICO.json"]=write_new(folder,"00_MUNDO_PUBLICO.json",world)

    k0=masks.masked_k0(
        snapshot_run(WORLD,RATES["K0"],(5,10)),
        world["world_precommitment_ref"])
    runs+=1
    hashes["01_K0_PUBLICO.json"]=write_new(folder,"01_K0_PUBLICO.json",k0)
    g4a=bridge.create_g4a_candidate(k0,policy)
    hashes["02_G4a_PRE_K1.json"]=write_new(folder,"02_G4a_PRE_K1.json",g4a)

    selection=g4a["K1_preselected_common"]["proposed_measurement"]
    k1=None
    if selection is not None:
        rate=str(selection["rate_per_minute"])
        snaps=snapshot_run(WORLD,rate,(selection["t_min"],))
        runs+=1
        k1=masks.masked_k1(
            snaps[0],selection,world["world_precommitment_ref"])
    hashes["03_K1_PUBLICO.json"]=write_new(folder,"03_K1_PUBLICO.json",
                                          {"K1_was_used":k1 is not None,
                                           "public_observation":k1})
    g4b=bridge.create_g4b_candidate(g4a,k1,policy)
    hashes["04_G4b_PRE_K2.json"]=write_new(folder,"04_G4b_PRE_K2.json",g4b)

    predictions=predictions_only(g4a,g4b)
    hashes[FORECAST_FILE]=write_new(folder,FORECAST_FILE,predictions)
    checkpoint={
        "schema":"igc-caf02-exploratory-local-pre-k2-checkpoint/0.1",
        "status":"WRITTEN_AND_FSYNCED_BEFORE_FIRST_K2_ENGINE_CALL",
        "forecast_sha256":hashes[FORECAST_FILE],
        "g4a_sha256":g4a["candidate_sha256"],
        "g4b_sha256":g4b["candidate_sha256"],
        "file_hashes_pre_k2":dict(hashes),
        "DES_K2_runs_so_far":0,
        "K2_truth_seen":False,
        "cryptographic_custody":False,
    }
    checkpoint_hash=write_new(folder,"05B_CHECKPOINT_PRE_K2.json",checkpoint)
    hashes["05B_CHECKPOINT_PRE_K2.json"]=checkpoint_hash

    if after_checkpoint_hook is not None:
        after_checkpoint_hook(folder,checkpoint)  # test-only injection, before K2
    # First and ONLY K2 DES call. All forecasts are already durable on disk.
    k2=masks.reserved_k2_inside_evaluator(
        snapshot_run(WORLD,RATES["K2"],tuple(bridge.TIMES)),
        world["world_precommitment_ref"])
    runs+=1
    hashes["06_K2_OBSERVADO.json"]=write_new(folder,"06_K2_OBSERVADO.json",k2)
    scores=adjudicator.score_both_arms_after_external_release(k2,g4a,g4b,
                                                               policy)
    # This is explicitly a local exploratory unsealing, NOT an external K2.
    scores["lab_exploratory_not_independent_custody"]=True
    scores["source_DES_lab_runs"]=runs
    hashes["07_PUNTUACION.json"]=write_new(folder,"07_PUNTUACION.json",scores)

    result={
        "schema":SCHEMA,"status":"EXPLORATORY_RESULTS_NOT_CONFIRMATORY",
        "G4a_summary":{
            arm:counts(g4a["K2_prior_"+arm+"_by_family"])
            for arm in ("M","D")},
        "G4b_summary":{
            arm:counts(g4b["K2_revised_"+arm+"_by_family"])
            for arm in ("M","D")},
        "K0":k0,"K1":k1,"K2":k2,
        "scores":scores,
        "predictions":{
            f"{arm}_{cut}_by_family":
                (g4a["K2_prior_"+arm+"_by_family"] if cut=="K0" else
                 g4b["K2_revised_"+arm+"_by_family"])
            for arm in ("M","D") for cut in ("K0","K1")},
        "exploratory_DES_runs":runs,"confirmatory_DES_runs":0,
        "g4a_sha256":g4a["candidate_sha256"],
        "g4b_sha256":g4b["candidate_sha256"],
        "predictions_file_sha256":hashes[FORECAST_FILE],
        "checkpoint_sha256":checkpoint_hash,
    }
    hashes["08_RESUMEN_RESULTADOS.json"]=write_new(folder,"08_RESUMEN_RESULTADOS.json",result)
    hashes["09_TABLA_K2.csv"]=write_new(folder,"09_TABLA_K2.csv",csv_table(result))
    hashes["10_INFORME.md"]=write_new(folder,"10_INFORME.md",report_md(result))
    manifest={
        "schema":"igc-caf02-exploratory-local-artifacts/0.1",
        "status":"ONE_PUBLIC_WORLD_EXPLORATORY_COMPLETE",
        "world_ref":world["world_precommitment_ref"],
        "files_sha256":hashes,
        "G2_native_calls_in_this_run":0,
        "DES_lab_runs":runs,
        "DES_confirmatory_runs":0,
        "external_custody_verified":False,
        "ATMS_persisted":False,
        "K2_priors_written_before_K2":True,
        "avoid_using_this_world_as_blind_confirmatory_sample":True,
    }
    write_new(folder,"11_MANIFIESTO.json",manifest)
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out",required=True,type=Path,
                    help="NEW folder; never overwrite an old experiment")
    args=ap.parse_args()
    value=run_lab(args.out)
    print(json.dumps({
        "status":value["status"],
        "DES_lab_runs":value["exploratory_DES_runs"],
        "K0":[value["K0"]["delivered_t5"],
              value["K0"]["delivered_t10"]],
        "K1":value["K1"],
        "K2":value["K2"]["delivered"],
        "M":{k:value["scores"]["M"][k] for k in
             ("status","paired_set_loss_gain_orders",
              "revision_predictive_improvement_pass")},
        "D":{k:value["scores"]["D"][k] for k in
             ("status","paired_set_loss_gain_orders",
              "revision_predictive_improvement_pass")},
    },sort_keys=True))


if __name__=="__main__":
    main()
