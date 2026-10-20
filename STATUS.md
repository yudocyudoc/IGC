# IGC — Estado del laboratorio

**Corte:** 2026-10-20  
**F0:** ACEPTADA CON LIMITACIONES E INTEGRADA  
**F1a:** CORTE INICIAL INTEGRADO; LEDGER LOCAL SINTÉTICO EN PROGRESO  
**Plataforma completa:** INCOMPLETA

## Integración en `main`

- PR #1 — inventario y laboratorio; merge `b5fd6a3364cd7da232a0af51f76592a7d7decdef`.
- PR #3 — handoff sintético; merge `83b9ebffb437382adee94c36bb8e17476d5aa9c8`.
- PR #2 — LinkML y ledger SQLite inicial F1a; merge `acd17fbd7fe5ce8d39b208b492607936090f6d11`.
- PR #4 — `recorded_at` monótonico; merge `1d706e6847ad03c0cb6a026aa49f8b7214dbcfb0`.

## Integraciones abiertas

- PR #5 — probe sintético ATMS → selección → OpenModelica; abierto sobre `main`.
- PR #6 — puente sintético Web Annotation/RDF/CRMinf/PROV-O/SPARQL → propuestas ATMS → OpenModelica; abierto y apilado sobre #5. Las propuestas y `nogoods` son datos del fixture, la topología sigue siendo `single_stock` y no hay inferencia empírica.
- PR #7 — FM-A molecular; draft apilado sobre #6. Añade auditoría, factibilidad y contratos declarativos. Actions F1a #23 y F0 #274 pasaron sobre HEAD `5cccaee39d0e08630b439f98a60c7c6bb0227fb7`; S0 produce la misma selección que ATMS y registra `ATMS_VALUE_ADDED=NOT_DEMONSTRATED`. No supone moléculas admitidas ni autoriza FM-B.

## Verificación integrada

- F0-VERTICAL: [Actions #250](https://github.com/yudocyudoc/IGC/actions/runs/39360426366), 27 pruebas.
- F1a inicial: [Actions #252](https://github.com/yudocyudoc/IGC/actions/runs/39362255158), 39 pruebas combinadas; [LinkML #15](https://github.com/yudocyudoc/IGC/actions/runs/39362255202).
- F1a temporal: [Actions #253](https://github.com/yudocyudoc/IGC/actions/runs/39362587500), 40 pruebas combinadas.
- La evidencia de #5/#6 está acotada a sus SHAs y workflows; no acredita F3 completo ni H-IGC.

## Límites y siguiente secuencia

F0-VERTICAL es sintético, con estructura `single_stock`; no demuestra fidelidad empírica ni causalidad. F1a es SQLite temporal en Actions, no D1 ni API desplegada. PR #6 conecta una representación RDF/CRMinf/PROV explícita y una consulta SPARQL con propuestas sintéticas para ATMS y OpenModelica; no descubre mecanismos desde las fuentes. FM-A está autorizado y en curso en su propia rama apilada. Su auditoría encontró una pareja serial de una/dos etapas factible solo en forma declarativa y con restricciones; el abandono queda bloqueado por falta de split conservativo admitido. Licencias y admisión de clases de `short` no están resueltas. FM-B, merges, datos reales y gasto cloud siguen requiriendo autorización. H-IGC permanece `NOT_EVALUATED`.
