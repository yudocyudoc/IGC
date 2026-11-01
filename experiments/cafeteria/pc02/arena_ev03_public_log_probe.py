#!/usr/bin/env python3
"""ARENA EV03: run a disclosed externally produced XES audit.

No raw rows, event values or cases are stored in generated artifacts. CI
downloads an official public log separately; this file never performs
network requests or uses private-provider access.
"""
from __future__ import annotations

import argparse
from collections import OrderedDict
from hashlib import sha256
import json
from pathlib import Path
import re

from scripts import arena_public_eventlog_intake as core

SCHEMA="igc-arena-ev03-real-public-records-probe/0.1"
PROTO="70707877e0a010270833600f972594447a5f914c"
BPI12_URL=("https://data.4tu.nl/file/533f66a4-8911-4ac7-8612-"
           "1235d65d1f37/3276db7f-8bee-4f2b-88ee-92dbffb5a893")
GATE=core.GATE


def require(ok,code):
    if not ok: raise ValueError(code)


def save(root,name,content):
    target=root/name
    require(not target.exists(),"EV03_REFUSE_OVERWRITE_ARTIFACT")
    if not isinstance(content,str):
        content=json.dumps(content,ensure_ascii=False,indent=2,
                           sort_keys=True,allow_nan=False)+"\n"
    target.write_text(content,encoding="utf-8")


def run(output,input_xes,source_url,kind,checkout_sha,head_sha):
    for x in (checkout_sha,head_sha):
        require(re.fullmatch(r"[0-9a-f]{40}",x) is not None,
                "EV03_GIT_SHA_REQUIRED")
    require(kind in ("PUBLIC_REAL_BPI12","SYNTHETIC_XES_FIXTURE"),
            "EV03_BAD_SOURCE_KIND")
    if kind=="PUBLIC_REAL_BPI12":
        require(source_url==BPI12_URL,"EV03_WRONG_PUBLIC_SOURCE")
    else:
        require(source_url.startswith("https://example.invalid/"),
                "EV03_SYNTHETIC_SOURCE_URL_REQUIRED")
    root=Path(output).resolve()
    require(not root.exists(),"EV03_REFUSE_OVERWRITE")
    root.mkdir(parents=True,exist_ok=False)
    plan={
        "schema":SCHEMA,"first_protocol_commit":PROTO,
        "checkout_sha":checkout_sha,"pr_head_sha":head_sha,
        "source_kind":kind,"origin_url":source_url,
        "source_record_type":"XES_EVENT_LOG",
        "no_republication_of_source_rows":True,
        "no_raw_cases_resources_activities_or_amounts":True,
        "compressed_byte_limit":core.MAX_COMPRESSED_BYTES,
        "xml_byte_limit":core.MAX_DECOMPRESSED_BYTES,
        "max_events":core.MAX_EVENTS,"max_traces":core.MAX_CASES,
        "source_bytes_digest_not_precommitted":True,
        "external_is_not_cafeteria_validation":True,
        "no_hidden_stage_inference":True,
        "scientific_gate":GATE,
    }
    save(root,"00_PLAN_BEFORE_PARSE.json",plan)
    result=core.audit_xes_file(input_xes,source_url)
    if kind=="SYNTHETIC_XES_FIXTURE":
        result["status"]="SYNTHETIC_PARSER_TEST_ONLY"
    artifact={
        "schema":SCHEMA,
        "first_protocol_commit":PROTO,
        "checkout_sha":checkout_sha,"pr_head_sha":head_sha,
        "source_kind":kind,
        "external_audit":result,
        "readiness_example":core.readiness_gate({}),
        "no_mechanism_discovery_claim":True,
        "public_log_is_not_business_connector_validation":True,
        "no_unauthorized_business_records_used":True,
        "scientific_gate":GATE,
    }
    save(root,"01_RESULTS.json",artifact)
    summary=result["summary"]
    report=[
        "# Arena EV-03 — auditoría de un registro externo de eventos",
        "",
        "**Origen:** "+kind+".",
        "**Naturaleza:** eventos registrados en un sistema; no cronómetros",
        "físicos certificados. Su fecha/hora y etiquetas no prueban esperas,",
        "duraciones efectivas de servicio, topologías o causalidad.",
        "",
        "| Métrica de calidad | Conteo |",
        "|---|---:|",
    ]
    for key,value in summary.items():
        report.append("| `"+key+"` | "+str(value)+" |")
    report +=[
        "| `n_distinct_activities` | "+str(result["n_distinct_activities"])+" |",
        "",
        "## Procedencia e integridad",
        "",
        "- URL de versión de fuente: "+source_url,
        "- SHA256 de bytes recibidos: `"+result["received_file_sha256"]+"`",
        "- La **URL está fijada**, pero su SHA de bytes no se había",
        "  precomprometido antes del primer acceso. El resultado exige",
        "  nueva auditoría de esa identidad de datos.",
        "- No se publican eventos, nombres de actividades, IDs, cantidades,",
        "  recursos ni CSV original en el paquete.",
        "",
        "## Respuestas que la Arena NO está autorizada a emitir",
        "",
        "- No se conoce semántica del instante físico de inicio/fin de servicio.",
        "- No están comprobadas la sincronía, resolución y latencia de captura.",
        "- Un evento `START` y `COMPLETE` no certifican por sí solos",
        "  tiempo efectivo de trabajador.",
        "- No afirmar etapa oculta por latencia residual.",
        "- No extrapolar este proceso de solicitudes de crédito a cafeterías.",
        "- No se han integrado D/B/M, ATMS ni un POS/KDS/CRM privado.",
        "",
        "Gate: "+GATE,
        "",
    ]
    save(root,"02_REPORT.md","\n".join(report))
    hashes={x.name:"sha256:"+sha256(x.read_bytes()).hexdigest()
            for x in sorted(root.iterdir()) if x.is_file()}
    save(root,"03_MANIFEST.json",{
        "schema":SCHEMA,
        "checkout_sha":checkout_sha,
        "pr_head_sha":head_sha,
        "files_sha256":hashes,
        "no_source_rows_stored":True,
    })
    return artifact


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--input-xes",type=Path,required=True)
    p.add_argument("--source-url",required=True)
    p.add_argument("--source-kind",choices=("PUBLIC_REAL_BPI12","SYNTHETIC_XES_FIXTURE"),
                   required=True)
    p.add_argument("--checkout-sha",required=True)
    p.add_argument("--head-sha",required=True)
    x=p.parse_args()
    report=run(x.out,x.input_xes,x.source_url,x.source_kind,
               x.checkout_sha,x.head_sha)
    print(json.dumps({
        "status":report["external_audit"]["status"],
        "traces":report["external_audit"]["summary"]["n_traces"],
        "events":report["external_audit"]["summary"]["n_events"],
        "gate":report["scientific_gate"],
    },sort_keys=True))
