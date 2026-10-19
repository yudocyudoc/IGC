# IGC — Estado del laboratorio

**Corte:** 2026-10-19  
**Fase:** F0 — Inventario y laboratorio  
**Estado:** EN CURSO; spike de cableado sintético ejecutada y bloqueada por componentes ausentes.

## Rama y alcance

- Repositorio destino: `yudocyudoc/IGC`.
- Rama remota de trabajo: `f0-inventario-spike`, derivada de la línea base documental en `main`.
- Esta fase audita antecedentes y prepara contratos/entorno local. No implementa capacidades científicas ni declara gates integrados.
- Checkout local de esta sesión aún no sincronizado con los refs remotos; el acceso de GitHub Connector sí permite registrar documentos en la rama.

## Evidencia actual

- Especificación integral v0.2 y plan por fases disponibles en `docs/`.
- Auditoría inicial de los PR #20, #39 y #40 del repo histórico `yudocyudoc/short`: `docs/F0_AUDITORIA_INICIAL.md`.
- Seguimiento de inicialización de `IGC`: `docs/F0_SEGUIMIENTO_2026-10-19.md`.
- Python 3.13.1, Node.js 22.13.1 y Git 2.51.0.windows.1 detectados en PATH.
- `omc` y Docker no detectados. `rdflib`, `pyshacl`, `linkml`, `pykeen` y `owlrl` no detectados por el intérprete Python consultado. `jsonschema`, `pytest` y `networkx` sí están instalados, sin considerarlos todavía dependencias del proyecto.
- Cinco pruebas contractuales pasan; el runner confirma `BLOCKED` y código de salida 2. La ingesta/anclaje sintético sí corre; Web Annotation formal, RDF/SHACL, SPARQL, ATMS, candidato/handoff y OpenModelica permanecen `PENDING`/`STUB`.
- Reporte y borrador Web Annotation de la corrida actual: `artifacts/f0/run.json` y `artifacts/f0/annotation-draft.json`; ambos se regeneran con `python scripts/f0_spike.py`.

## Pendientes / bloqueos

1. Abrir la rama remota en un checkout local escribible para implementar y reproducir la spike.
2. Auditar y fijar versiones, licencias y huellas de dependencias desde fuentes oficiales.
3. Verificar disponibilidad/versión de OpenModelica y bibliotecas Modelica en el checkout de desarrollo.
4. Acordar contratos mínimos y artefactos del recorrido vertical.
5. Repetir la corrida tras habilitar motores reales; conservar logs, hashes, límites y resultados negativos.

## Veredicto de fase

`F0_AUDIT_PARTIAL — SOURCE_ANCHOR_PASS — RDF_ATMS_OM_PENDING`.

No hay `PASS` de RDF, SHACL, ATMS, OpenModelica, Cloudflare, integración vertical ni hipótesis científica. Ningún recurso Cloudflare real fue consultado.
