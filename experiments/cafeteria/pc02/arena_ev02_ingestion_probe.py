#!/usr/bin/env python3
"""EV-02: synthetic exports shaped like POS/KDS/CRM, not actual provider data.

Operational adapter reuses EV-01 source events only as an evaluator fixture.
The ingestion core never imports the underlying cafeteria physical model.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime,timedelta,timezone
from fractions import Fraction as Q
from hashlib import sha256
from io import StringIO
import json
from pathlib import Path

from scripts import arena_operational_ingestion as op
from scripts import arena_event_observability as prior
import arena_ev01_event_views as ev01

SCHEMA="igc-arena-ev02-ingest-evidence-probe/0.1"
PROTO="b836e46138aad231a5595a1b429ea69407e786f8"
SECRET_SYNTHETIC=sha256(b"ARENA EV-02 synthetic regression pseudonym seed only").digest()
ORIGIN=datetime(2026,1,1,tzinfo=timezone.utc)
CSV_FIELDS=("order_id","event_id","action","occurred_at","clock_id")
CRM_FIELDS=("lead_id","event_id","action","occurred_at","clock_id")


def require(ok,msg):
    if not ok:
        raise ValueError(msg)


def iso(t,offset_hours=0):
    """Round exact EV-01 minute time to nearest microsecond, EXPLICIT."""
    micros=int(Q(t)*60000000+Q(1,2))
    dt=ORIGIN+timedelta(microseconds=micros)
    dt=dt.astimezone(timezone(timedelta(hours=offset_hours)))
    return dt.isoformat(timespec="microseconds")


def csv_rows(rows,fieldnames=CSV_FIELDS):
    out=StringIO()
    writer=csv.DictWriter(out,fieldnames=fieldnames,lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def example_exports():
    """External-looking CSVs; no FULL physical trace enters ingest."""
    full,_=ev01.trace_generator()
    pos=prior.project_events(full,"POS")
    kds_view=prior.project_events(full,"POS_KDS")
    kds=[r for r in kds_view if r["event_type"] in prior.KDS_TYPES]
    pos_mapping={
        "pedido_creado":"created","pago_confirmado":"paid",
        "pedido_entregado":"handed_off",
    }
    kds_mapping={"servicio_inicio":"prep_started",
                 "servicio_fin":"prep_done"}
    pos_rows=[{
        "order_id":r["case_id"],
        "event_id":"P-"+str(i),
        "action":pos_mapping[r["event_type"]],
        "occurred_at":iso(r["t_minutes_exact"],0),
        "clock_id":"POS_CLOCK",
    } for i,r in enumerate(pos)]
    kds_rows=[{
        "order_id":r["case_id"],
        "event_id":"K-"+str(i),
        "action":kds_mapping[r["event_type"]],
        "occurred_at":iso(r["t_minutes_exact"],-6),
        "clock_id":"KDS_CLOCK",
    } for i,r in enumerate(kds)]
    require(len(pos_rows)==45 and len(kds_rows)==30,
            "EV02_FIXTURE_EVENT_COUNT_DRIFT")
    return csv_rows(pos_rows),csv_rows(kds_rows)


def crm_example():
    rows=[
        ("L-001","C1","created","2026-01-02T10:00:00-06:00"),
        ("L-001","C2","qualified","2026-01-02T10:10:00-06:00"),
        ("L-002","C3","created","2026-01-03T09:00:00Z"),
        ("L-002","C4","demo_requested","2026-01-03T09:20:00Z"),
    ]
    return csv_rows([{
        "lead_id":lead,"event_id":event_id,"action":action,
        "occurred_at":when,"clock_id":"CRM_CLOCK",
    } for lead,event_id,action,when in rows],CRM_FIELDS)


def specs(kds_clock_status="verified_utc_sync"):
    return (
        op.SourceSpec("pos_export_v1","POS_EXAMPLE","orders:synthetic",
                      "POS_CLOCK","verified_utc_sync",1,
                      "SYNTHETIC_POS_CLOCK_DECLARATION_NOT_MEASURED"),
        op.SourceSpec("kds_export_v1","KDS_EXAMPLE","orders:synthetic",
                      "KDS_CLOCK",kds_clock_status,
                      1 if kds_clock_status=="verified_utc_sync" else None,
                      "SYNTHETIC_KDS_CLOCK_DECLARATION_NOT_MEASURED"),
    )


def adversarial_export(pos_body):
    rows=list(csv.DictReader(StringIO(pos_body)))
    malformed=[
        {**rows[0],"event_id":"BAD-NAIVE",
         "occurred_at":"2026-01-01T00:00:00"},
        {**rows[0],"event_id":rows[0]["event_id"]}, # duplicate
        {**rows[0],"event_id":"BAD-ACTION","action":"hidden_stage_found"},
        {**rows[0],"event_id":"BAD-CASE","order_id":""},
    ]
    return csv_rows(rows+malformed)


def run(out,checkout_sha,head_sha):
    import re
    require(bool(re.fullmatch("[0-9a-f]{40}",checkout_sha)) and
            bool(re.fullmatch("[0-9a-f]{40}",head_sha)),
            "EV02_GIT_SHA_REQUIRED")
    path=Path(out).resolve()
    require(not path.exists(),"EV02_REFUSE_OVERWRITE")
    path.mkdir(parents=True,exist_ok=False)

    def save(name,doc):
        p=path/name
        require(not p.exists(),"EV02_REFUSE_OVERWRITE_FILE")
        if isinstance(doc,str):
            p.write_text(doc,encoding="utf-8")
        else:
            p.write_text(json.dumps(doc,ensure_ascii=False,sort_keys=True,
                                    indent=2,allow_nan=False)+"\n",encoding="utf-8")

    save("00_PLAN_BEFORE_EVAL.json",{
        "schema":SCHEMA,"protocol_first_commit":PROTO,
        "checkout_sha":checkout_sha,"pr_head_sha":head_sha,
        "input_kind":"SYNTHETIC_EXTERNAL_FORMAT_FIXTURE_NOT_REAL_DATA",
        "declared_profiles":tuple(op.ACTION_MAP),
        "declared_accuracy_ms":1,
        "clock_verified_is_only_unchecked_source_declaration":True,
        "expected_pos_kds_events":(45,30),
        "no_grid":True,
        "no_unknown_mechanism_detection":True,
        "quarantine_adversarial_count":4,
        "raw_personal_data_must_not_be_exported":True,
        "scientific_gate":op.GATE,
    })
    pos,kds=example_exports()
    pos_spec,kds_spec=specs()
    a=op.ingest_csv(pos,pos_spec,SECRET_SYNTHETIC)
    b=op.ingest_csv(kds,kds_spec,SECRET_SYNTHETIC)
    require((a["n_accepted"],b["n_accepted"])==(45,30),
            "EV02_EXPECTED_VALID_EVENTS")
    known=op.summarize_cases([a,b])
    require(known["n_cases"]==15 and
            all(r["cycle_status"]=="RECORDED_ADMIN_CYCLE_NOT_PHYSICAL_SOJOURN"
                for r in known["cases"]) and
            all(r["admin_interval_status"]==
                "RECORDED_KDS_CLICK_INTERVAL_NOT_PHYSICAL_SERVICE"
                for r in known["cases"]) and
            all(r["cross_source_status"]==
                "RECORDED_CROSS_SOURCE_ELAPSED_NOT_PHYSICAL_SERVICE"
                for r in known["cases"]),"EV02_VALID_FIXTURE_REGRESSION")

    spec_unverified=specs("unverified")[1]
    b_unverified=op.ingest_csv(kds,spec_unverified,SECRET_SYNTHETIC)
    uncertain=op.summarize_cases([a,b_unverified])
    require(all(r["cross_source_status"]==
        "CROSS_SOURCE_TEMPORAL_COMPARISON_BLOCKED" for r in uncertain["cases"]),
        "EV02_CLOCK_TRUST_BLOCKER_FAILED")

    bad=op.ingest_csv(adversarial_export(pos),pos_spec,SECRET_SYNTHETIC)
    require(bad["n_accepted"]==45 and bad["n_quarantined"]==4,
            "EV02_QUARANTINE_DRIFT")
    reject_schema=False
    try:
        op.ingest_csv(pos.replace("clock_id\n","clock_id,email\n",1),
                      pos_spec,SECRET_SYNTHETIC)
    except ValueError as ex:
        reject_schema=str(ex)=="EV02_FILE_SCHEMA_REJECTED"
    require(reject_schema,"EV02_PII_SCHEMA_FAIL_CLOSED")

    crm_spec=op.SourceSpec("crm_export_v1","CRM_EXAMPLE","crm:synthetic",
            "CRM_CLOCK","unverified",None,
            "SYNTHETIC_CRM_CLOCK_STATUS_UNKNOWN")
    crm_batch=op.ingest_csv(crm_example(),crm_spec,SECRET_SYNTHETIC)
    crm=op.summarize_cases([crm_batch])
    require(crm["n_cases"]==2 and crm["n_recorded_events"]==4 and
            all(c["cycle_status"]=="NOT_APPLICABLE_TO_CRM_ORDER_CYCLE"
                for c in crm["cases"]),"EV02_CRM_REGRESSION")

    # Exact raw export inputs are NOT retained: outputs contain only hashed
    # identifiers, administrative labels and synthetic record timestamps.
    result={
        "schema":SCHEMA,"protocol_first_commit":PROTO,
        "checkout_sha":checkout_sha,"pr_head_sha":head_sha,
        "n_physical_worlds":1,"n_synthetic_orders":15,
        "source_profiles":["pos_export_v1","kds_export_v1","crm_export_v1"],
        "normal_ingest":{
            "pos_accepted":a["n_accepted"],
            "kds_accepted":b["n_accepted"],
            "n_valid_cases":known["n_cases"],
            "n_administrative_cycles":sum(
                x["cycle_status"]=="RECORDED_ADMIN_CYCLE_NOT_PHYSICAL_SOJOURN"
                for x in known["cases"]),
            "n_kds_admin_intervals":sum(
                x["admin_interval_status"]==
                "RECORDED_KDS_CLICK_INTERVAL_NOT_PHYSICAL_SERVICE"
                for x in known["cases"]),
            "n_declared_synchronized_cross_source_intervals":sum(
                x["cross_source_status"]==
                "RECORDED_CROSS_SOURCE_ELAPSED_NOT_PHYSICAL_SERVICE"
                for x in known["cases"]),
        },
        "unverified_clock":{
            "pos_accepted":a["n_accepted"],
            "kds_accepted":b_unverified["n_accepted"],
            "n_cross_source_intervals_blocked":sum(
                x["cross_source_status"]==
                "CROSS_SOURCE_TEMPORAL_COMPARISON_BLOCKED"
                for x in uncertain["cases"]),
        },
        "adversarial_quality":{
            "accepted_original":bad["n_accepted"],
            "quarantined":bad["n_quarantined"],
            "quarantine_counts":dict(sorted(
                __import__("collections").Counter(
                    x["code"] for x in bad["quarantine"]).items())),
            "pii_extra_column_rejected_entire_file":reject_schema,
        },
        "crm_separate_namespace":{
            "n_leads":crm["n_cases"],
            "n_recorded_events":crm["n_recorded_events"],
            "physical_service_claims":sum(
                r["physical_service_time_identified"] for r in crm["cases"]),
        },
        "analyst_visible_normalized_events":[
            {"profile":batch["profile"],"accepted":batch["n_accepted"],
             "source_digest":batch["source_digest"],
             "no_raw_identifiers":batch["no_raw_identifier_fields_retained"]}
            for batch in (a,b,crm_batch)],
        "n_unknown_topologies_detected":0,
        "no_physical_service_or_wait_claims":True,
        "no_external_data_used":True,
        "no_parameter_grid_or_structure_catalog":True,
        "promotion_gate":op.GATE,
    }
    save("01_RESULTS.json",result)
    lines=[
        "# ARENA EV-02 — Ingestión con semántica, calidad y abstención",
        "",
        "**Todos los archivos de entrada fueron fabricados a partir del mundo",
        "sintético EV-01; no se conectó ningún POS, KDS ni CRM real.**",
        "",
        "| Prueba | Eventos aceptados | Casos | Resultado de semántica |",
        "|---|---:|---:|---|",
        "| POS + KDS, relojes declarados sincronizados | 75 | 15 | 15 ciclos y 15 intervalos KDS **administrativos**, ningún servicio físico |",
        "| POS + KDS, reloj KDS sin verificar | 75 | 15 | 15 comparaciones POS↔KDS bloqueadas |",
        "| POS malformado, 4 filas adversas | 45 | 15 | 4 filas en cuarentena (sin corregirlas ni inferir actividad) |",
        "| CRM sintético | 4 | 2 | Estados de leads, ningún servicio físico |",
        "",
        "La ingestión no detecta cuellos ni etapas latentes. Normaliza fechas",
        "con offset a UTC, preserva procedencia y pseudonimiza identificadores",
        "con secreto suministrado por el operador. El registro fuente completo",
        "**no** se entrega a inferencia ni se adjunta a la auditoría.",
        "",
        "## Compuertas y limitaciones",
        "",
        "- Una marca ISO con zona **no prueba que el dispositivo tenga reloj",
        "  sincronizado**. verified_utc_sync es una DECLARACIÓN de fuente,",
        "  no una medición independiente del reloj.",
        "- `prep_started` y `prep_done` son clicks administrativos por",
        "  defecto. Su diferencia es un intervalo de registro, NO servicio físico.",
        "- Un campo extra (p. ej. email) rechaza el CSV entero por esquema",
        "  cerrado; datos de identificador se devuelven como pseudónimos.",
        "- Filas inválidas quedan en cuarentena con código y número de fila,",
        "  nunca se mapean automáticamente a actividades conocidas.",
        "- Una relación POS/KDS requiere namespace de identidad declarado.",
        "  No unir por coincidencia de nombre, teléfono o tiempo cercano.",
        "- Aún no hay datos de proveedor, evidencia de precisión de reloj,",
        "  auditoría de tiempo entre click y acción, ni validación externa.",
        "- No conecta D/B/M ni ATMS; el próximo paso es validar un ejemplo",
        "  real autorizado con su diccionario de hitos.",
        "",
        "Gate: "+op.GATE,
    ]
    save("02_REPORT.md","\n".join(lines)+"\n")
    sha={p.name:"sha256:"+sha256(p.read_bytes()).hexdigest()
         for p in sorted(path.iterdir()) if p.is_file()}
    save("03_MANIFEST.json",{
        "schema":SCHEMA,"checkout_sha":checkout_sha,"pr_head_sha":head_sha,
        "files_sha256":sha,"all_data_synthetic":True})
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--checkout-sha",required=True)
    p.add_argument("--head-sha",required=True)
    args=p.parse_args()
    report=run(args.out,args.checkout_sha,args.head_sha)
    print(json.dumps({
        "normal_ingest":report["normal_ingest"],
        "unverified_clock":report["unverified_clock"],
        "adversarial_quality":report["adversarial_quality"],
        "gate":report["promotion_gate"]},sort_keys=True))
