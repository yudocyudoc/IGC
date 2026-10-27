# Arena M0 — brazo molecular independiente, recuperación reproducible de Short E1

**Fecha:** 2026-10-25 | **Rama:** `feature/arena-m-short-e1-independent-v0` (rama nueva desde `IGC/main`) | **Alcance:** ingeniería molecular recuperada; no inferencia causal.

## Decisión del investigador y ruta escogida

El brazo 3 de la Arena V0 aplica composición molecular autónoma, no procedimientos de Buffalo ni búsqueda del brazo D. Como primer incremento, recuperamos **literalmente** del repositorio histórico `yudocyudoc/short` el compositor tipado E1, su compilador por instanciación, dos registros, tests y clases Modelica. El experimento E1 pasó [Actions #39104098853](https://github.com/yudocyudoc/short/actions/runs/39104098853), con 6 grafos base y 15 extendidos ejecutados en OpenModelica. El resultado histórico es `COMPOSITION_ENGINEERING_ONLY`, no descubrimiento del mundo.

### Procedencia exacta

`docs/ARENA_M_SHORT_E1_PROVENANCE.json` contiene el Git **blob SHA-1 original** de cada fuente copiada, desde `short/experiment/igc-v3-e1-registry-composer-v1` (E1/E0) y `short/main` (wrappers Modelica). La CI verifica el Git blob calculado a partir de bytes en IGC: **no se parchearon** `composer.py`, `backend.py`, `verify_native.py`, `test_composition.py`, registros, catálogo ni las dos clases propias del proyecto. Las ecuaciones físicas derivan de las bibliotecas externas declaradas, no del algoritmo de generación. El código y los originales `.mdl` de Jim Hines **no** se vendorean; sigue pendiente resolver permisos/licencias para cualquier uso más allá del experimento.

Los experimentos complementarios de `short` siguen **sin ser integrados todavía**:
- P1 [#39](https://github.com/yudocyudoc/short/pull/39): sondas adversativas de E1 (split válido también bloqueado); no puede reivindicarse generalidad para redes físicas.
- P2 [#40](https://github.com/yudocyudoc/short/pull/40): tipado conceptual FLOW/STOCK/SIGNAL/CONTROL y SENSE/GOVERN, pero `P2_EXECUTABLE_NETWORK_PASS=NOT_RUN`.
- IA-1 [#35](https://github.com/yudocyudoc/short/pull/35): 4/18 AST formalmente admitidos; no selección semántica fiable demostrada.
- FM-B de IGC (#10–#14): composición, simulación y discriminación sintética bajo catálogo acotado, con incertidumbre/licencias pendientes. No trasplantar toda la pila ATMS a M0.

## Qué se ejecuta ahora

1. **Sin cambios de código E1:** la regresión exacta Python del compositor comprueba 6/15 estructuras canónicas, tipos, puertos, presupuesto y negativos; se generan `IGCE1Generated.mo` y scripts `omc` desde clases registradas.
2. **Ruta OpenModelica de E1 independiente:** MSL 4.0.0, SystemDynamics 2.1.2, OMC `v1.26.5-minimal`, igual que el experimento histórico. Se conservan verificación del contador de resultados y efecto informacional sin alterar flujos físicos. Las dependencias externas no se incorporan al repo.
3. **Contrato de Arena independiente:** `scripts/arena_m_short_e1.py` consume `ArenaVisibleInput` y crea una biblioteca nativa M de estructuras, hashes, `ArmSubmission` y evento trazable compatible con `scripts/arena_v0_contract.py`.
4. **Misma evidencia pública (en contenido) que la primera generación Buffalo:** `data/synthetic/arena_m_v0_visible.json` es copia **exacta** del archivo original `arena_b_native_visible.json`, Git blob `94fb9e853d1fd0f5623d759fb7b8408756eacf0c`. Esto **no** significa que se haya usado el mismo estímulo para simular los componentes originales de E1: el backend E1 usa cuatro entradas sintéticas fijas de su prueba anterior.

## Límite de independencia y honestidad

El registro E1 expresa `Order → ReadyOrder → Shipment`, colas acotadas y filtros informativos. La pregunta de Arena habla de trabajo pendiente y entregas. La equivalencia semántica **no está probada**: no inferimos que `Shipment` sea el mismo observable que `cumulative_delivered` sin documentar una correspondencia de roles, escalas y sensores.

Los parámetros E1 `maxThroughput=20`, `responseTime=0.5`, `responseTime=1.6`, etc., son **valores fijos del experimento**, no ajuste al pulso de 1.7 items/h durante 2h del caso común. Sería inválido contar las simulaciones históricas como ajuste de esos cuatro puntos observados.

**Por esa razón `ArmSubmission(M)` queda `PARTIAL`, con `hypothesis_ids=[]`, `candidate_selection=UNRESOLVED` y `common_stimulus_translation=NOT_IMPLEMENTED`.** Las 6/15 estructuras se archivan como universo de **candidatos de ingeniería**, no 6/15 explicaciones elegidas desde evidencia. Se conserva el presupuesto público de 1 propuesta sin violarlo. Un evento `ABSTENTION_RECORDED` señala que todavía no existe elección fundada, no que el método molecular haya demostrado ser incapaz de proponer un modelo en general.

## Próximas puertas (no asumir completadas)

- **M1:** contrato de correspondencia entre observables de la evidencia común y puertos/roles; rechazar `NO_MATCHING_MOLECULE` en ausencia de coincidencia semántica, sin elegir por catálogo oculto o nombres de mundo.
- **M1→G2 común:** inyectar pulso público idéntico a D/B como **condición experimental**, no como mecanismo de la hipótesis; ejecutar en OpenModelica y comprobar balances con verificador independiente (no solo `checkModel`).
- **M2:** selección/conjunto `PARTIAL/UNRESOLVED` justificado entre alternativas, y diagnóstico a M sobre su propio resultado. No pasar AST sugeridos por Buffalo ni D, no devolverle `gold`, no consumir reserva antes de lock.
- **M3:** capa ATMS como **memoria de revisiones y soportes**, cuando el flujo M genere decisiones y justificaciones reales; no importar selector F0 de otra rama y presentarlo como ATMS completo.
- **Fuente y licencias:** revisar explícitamente licencias de SystemDynamics y cualquier molécula derivada de Hines/BSL antes de circulación/productización.

**Veredicto admisible en M0:** `SHORT_E1_COMPOSITION_AND_OM_ENGINEERING_REPRODUCED` solo si la CI de IGC confirma los resultados originales. `M_EVIDENCE_BASED_MODEL_SELECTED`, G3, ventaja sobre D/B, feedback causal y ATMS productivo: **NOT_RUN**.
