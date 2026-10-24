# Arena IGC · ATMS/Memoria M0 — implementación inicial

**Fecha:** 2026-10-24. **Estado:** código en rama, pendiente de CI/revisión.
**Base apilada:** fm-12-13-atms-llm-ablation (no integrada en main).
**Mandato:** ATMS se implementa para memoria y recuperación de hipótesis, no se vuelve a discutir su adopción.

## Código

- scripts/arena_atms.py: motor de entornos mínimos, reglas OR/AND, nogoods, soporte grounded sin ciclos autosustentados, trazas de explicación con fuente, límites explícitos y what-if sin modificar el canon.
- project(): reconstruye un snapshot as_known_at desde eventos versionados, desactiva/restaura supuestos o justificaciones en revisiones posteriores y filtra permisos antes del razonamiento.
- scripts/arena_memory.py: recuperación lexical de información, hipótesis y fuente con explicaciones ATMS y hash de manifiesto. Restringe por investigación, fecha y vía D/S/P/B0.
- Integración al scripts/ledger.py F1a por Ledger.snapshot y revisiones KnowledgeItem. No se crea otro ledger.
- Selección F3 (propuestas RDF/SPARQL) y selección FM-B2 (candidatos moleculares) usan ahora el mismo engine Arena ATMS, con verificador independiente anterior y regresiones existentes.
- El workflow ejecuta la cadena FM-B3 con OpenModelica real, balances y contraste sintético de estructuras admitidas (CS-01/CS-02); CS-03 no se simula.
- data/synthetic/arena_memory_m0.json: dos justificaciones de una hipótesis parcial, un nogood, controles hidden/future. Sin modelo de abandono ejecutable.
- tests/test_arena_atms_memory.py: conjunto adversativo para retraction/restitution, mínimos, ciclos, límites, procedencia, filtros temporales y permisos.
- .github/workflows/arena-atms-memory.yml: pruebas y artefacto recuperable de M0.

## Ejecutar

~~~bash
python -m unittest discover -s tests -p 'test_arena_atms_memory.py' -v
python -m scripts.arena_memory --events data/synthetic/arena_memory_m0.json \
  --case INV-CAF-M0 --as-known-at 2026-10-20T10:00:00Z \
  --lane D --query "abandono espera" \
  --output artifacts/arena-memory-m0/retrieval.json
~~~

Para consumir directamente el ledger F1a, utilizar --db RUTA.sqlite en lugar de --events.

## Aceptación acotada

| Contrato | Estado de implementación |
|---|---|
| ATMS-01/02/03: soportes alternativos, desactivar/restaurar, nogoods | IMPLEMENTADO; CI PENDIENTE |
| ATMS-05/08: ciclos sin anclaje y límites | IMPLEMENTADO; CI PENDIENTE |
| RET-01: recuperar hipótesis y soporte | IMPLEMENTADO; CI PENDIENTE |
| LRN-02: reconstrucción temporal | IMPLEMENTADO; CI PENDIENTE |
| SEC-01: sin gold, sin futuro, sin cruce de vía | IMPLEMENTADO; CI PENDIENTE |
| ATMS-C1..C8 integral | INCOMPLETO (C1 ampliado con oráculo enumerativo, C2/C3/C6 parcialmente cubiertos) |
| V0 Modelica/baseline/holdout | REGRESIÓN OpenModelica FM-B3 integrada; baseline B0/LOCK/custodia ciega aún NO IMPLEMENTADOS |

## Límites no disimulados

1. El motor de esta iteración es un cierre por recomputación total; **la optimización incremental** y su ensayo de equivalencia están pendientes. El ATMS F0 sigue como referencia y no se renombra producción.
2. Los permisos aquí son un modelo sintético de ámbito, no autorización multiusuario certificada.
3. La búsqueda es LEXICAL_V0. FTS5, RDF/SPARQL, recuperación vectorial T/G/D, KGE y fuentes independientes son fases siguientes, no funciones supuestas.
4. No existe todavía custodia privada verificable, ronda sellada, baseline B0 ni evaluación externa ciega.
5. No afirmar que el catálogo representa abandono como egreso material; FM-A señala NO_NATIVE_CONSERVATIVE_SPLIT.
6. No usar el CI verde como prueba de superioridad científica o causal.
7. Cloudflare no coordina nada: no se han modificado tokens, Workers, D1/R2 ni callbacks.

## Siguientes pasos de la Arena

- Integrar la memoria ATMS versionada con la procedencia semántica y justificaciones de F3 y FM-B2 sin mezclar los experimentos M0 y B3; esas selecciones ya comparten el motor, pero no un expediente causal unificado.
- Completar registros LinkML de conocimiento, procedencia de fuente y justificación, semántica RDF/SPARQL y búsqueda temporal/híbrida.
- Implementar vías D/S/P selladas, baseline B0, G1/G2/G3, OpenModelica, presupuesto y manifiestos.
- Implementar custodia privada antes de generar mundos nuevos, LOCK, consumo de holdout y evaluación independiente.
- Probar retractación, restitución, recuperación de hipótesis y actualización selectiva después de nuevas observaciones.
