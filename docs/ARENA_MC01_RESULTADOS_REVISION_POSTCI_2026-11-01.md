# ARENA MC-01 — Cierre post-CI y revisión metodológica sin rejilla

**2026-11-01, POST-CI, no parte del protocolo previo.** [PR #130 Draft](https://github.com/yudocyudoc/IGC/pull/130), base CAF-16 #129 Draft. No fusionado. Documento de fuente: *Identificación robusta de mecanismos en sistemas dinámicos parcialmente observados* (deep research, fuente aportada al proyecto); se adopta su arquitectura conservadora, no el informe general sobre automatización de SD.

## Registro de implementación

- **Primer commit de protocolo PRE-CÓDIGO:** `24b7fbf7deeffb162bc5abf88addf7cb16c9f084`, `docs/ARENA_MC01_PROTOCOLO_NUCLEO_CONTINUO_SIN_REJILLA_2026-11-01.md`.
- Código genérico `scripts/arena_methodology_continuous.py`: objetos `Family`, `Observation`, puerto `BoundedPredictionBackend`, búsqueda por partición racional de regiones continuas, verificador de cobertura, falsificación y alternativas de observación. **NO contiene CAF ni enumeración de capacidades físicas**.
- Adaptador CAF `experiments/cafeteria/pc02/arena_mc01_caf_adapter.py`: 6 estructuras nominales × dominios `[6/11,12/11]` de duración continua (1 o 2 por estructura), reutilizando la recurrencia exacta y el cálculo de cotas de CAF-15B. No crea un catálogo con 24/720 capacidades ni usa `CAF15A.compute_bank` en inferencia.
- [CI canónica #41352854974](https://github.com/yudocyudoc/IGC/actions/runs/41352854974): **9/9 unit tests PASS + ejecución completa PASS**, head evaluado `875e404cbb47af8b19a4578faa5d5ba23c873361`; checkout de merge sintético `ce51a2a599f270ef2d1dfca55248c5c277a6acd6` — **no confundir head con checkout**.
- [Artefacto canónico de cinco archivos](https://github.com/yudocyudoc/IGC/actions/runs/41352854974/artifacts/13102370226): `00_PLAN_BEFORE_EVAL.json`, `00B_A_PRIORI_BEFORE_EVAL.json`, `01_RESULTADOS.json`, `02_INFORME.md`, `03_MANIFIESTO.json`. Descargado y **4/4 archivos SHA256 verificados** frente al manifiesto. Protocolos/pares a priori guardados antes de ejecutar fixtures.
- **Incidente CI documentado:** corrida anterior [#41352800675](https://github.com/yudocyudoc/IGC/actions/runs/41352800675) completó 9/9 pruebas y falló en comando CLI por `ModuleNotFoundError: scripts` (PYTHONPATH en ejecución directa). Commit `875e404` corrige SOLO entorno `PYTHONPATH` del workflow. No modifica modelo ni inferencia.

## Las cuatro capas reales en este primer vertical slice

1. **Identificabilidad/Distinguibilidad a priori:** por cada uno de los programas `F_R25_T20` y `F_R25_T25`, con capacidades independientes continuas, el backend CAF-15B certifica **11/15 pares separables**, **4/15 con testigos de confusión**, **0 indeterminados**. Esto es **distinguibilidad entre familias**, no estimación de la verdad en un caso.
2. **Set-membership continuo:** el conjunto de compatibilidad para una observación fija `y` queda definido matemáticamente como `F_M(y)={d∈Θ_M: |h_M(d)_j−y_j|≤1 en todos los canales}`. Branch-and-bound NO itera por rejilla de capacidades: elimina cajas del continuo si alguna cota por canal contradice a `y±1`, conservando cajas racionales aún posibles y testigos racionales cuando se hallan. **Los puntos testigo no constituyen el espacio de hipótesis.** Un conjunto de cajas retenidas es una **sobreaproximación**, NO la descripción exacta de `F_M(y)`.
3. **Falsificación por existencia:** solo llama `CERTIFIED_EMPTY` cuando toda la región de una estructura fue excluida y revalidada por el verificador; otros estados son `WITNESS_FEASIBLE_WITH_OUTER_COVER` y `UNRESOLVED_WITH_OUTER_COVER`. Los seis vacíos significan `KNOWN_FAMILIES_INADEQUATE_UNDER_DECLARED_MODEL_AND_ERROR`, NO «se detectó una cuarta etapa».
4. **Diseño experimental no ejecutable aún:** dos ventanas de 150/h observadas solo como candidatos del laboratorio. Sin costo de sensores, ventanas de saturación natural medidas y función de pérdida para decisión, se registra `DESIGN_NOT_OPTIMIZABLE_MISSING_COST_AND_FEASIBILITY`, **sin ranking ni acción empresarial**. No optimización experimental validada.

## Pruebas de integración observables (NO holdout independiente)

### Fixture conocido: dos capacidades **69 y 101 pedidos/hora** (no una rejilla histórica)

Observaciones deterministas generadas con `CAF15B.physical_signature` sobre el modelo nominal `preparacion+despacho` a 150/h t20, capacidad continua independiente.

| Familia continua | Estado | Cajas externas retenidas |
|---|---|---:|
| preparación | `WITNESS_FEASIBLE_WITH_OUTER_COVER` | 129 |
| despacho | `CERTIFIED_EMPTY` | 0 |
| entrega | `CERTIFIED_EMPTY` | 0 |
| preparación + despacho (estructura nominal real) | `WITNESS_FEASIBLE_WITH_OUTER_COVER` | 125 |
| preparación + entrega | `WITNESS_FEASIBLE_WITH_OUTER_COVER` | 119 |
| despacho + entrega | `CERTIFIED_EMPTY` | 0 |

**Interpretación:** `INDETERMINATE_MULTIPLE_OR_UNRESOLVED_FAMILIES`. El motor retiene la clase verdadera, junto con otras dos explicaciones. **No** certifica una estructura única ni declara «hay 125 regiones factibles»: 125 son cajas conservadoras externas de una exploración de 256 nodos, no un conteo de soluciones físicas.

La prueba unitaria confirma que la pareja `(69,101)` continúa dentro de la cubierta de la familia verdadera, sin discretizar ni acceder a la verdad en `inference_only`. Testigos positivos encontrados en otros valores racionales ilustran confusibilidad estructural, no error del solver.

### Fixture de control: cuarta etapa rápida 220/h

Observación externa de cuarta etapa no representada, generada por el DES de CAF-15A. Las **seis familias** conocidas son `CERTIFIED_EMPTY` (se excluyeron en **una caja cada una**); verificación de exclusión PASS.

**Interpretación permitida:** `KNOWN_FAMILIES_INADEQUATE_UNDER_DECLARED_MODEL_AND_ERROR`. Este único control sintético **no identifica de manera universal una cuarta etapa**, ni valida sensibilidad OOD real. Al menos una de estructura, física, observación o cotas podría estar mal declarada en un negocio verdadero.

## Revisión de solidez y límites

- La técnica de **análisis por intervalos/set-membership** y el resultado ternario son métodos existentes, no una metodología nueva. El núcleo adopta operadores y contratos que preservan esa semántica.
- El verificador vuelve a recorrer de manera separada el árbol de subdivisiones y recalcula exclusiones, **pero comparte el backend matemático de cotas con el buscador**. Es auditoría reproducible y verificación estructural, no certificación por dos implementaciones independientes ni prueba formal mecanizada.
- **No se obtiene el conjunto factible exacto**: la interfaz pública declara predicado exacto, cubierta externa certificada y, ocasionalmente, testigos internos. Un tope de 256 nodos puede dejar cajas grandes; el límite es intencional y no reajustado tras resultados.
- `ε=±1` es una suposición de conteo **NO calibrada**. El ejemplo es determinista y con misma familia FIFO que el backend; CAF-16 mostró que el filtro determinista puede deteriorarse con servicio estocástico. NO se han incorporado estas incertidumbres al backend continuo.
- Las seis estructuras conocidas no constituyen un catálogo universal. No hay interfaz conectada aún a modelos de los brazos D/B/M; tampoco se escriben hechos a ATMS, ni se recolectaron datos de una PYME. Se preservan sin modificación los módulos ya existentes para integración posterior.
- **Sin puntuaciones de probabilidad de estructura, sin datos reales, sin política de inducir saturación**. El flujo de cuatro capas está integrado como vertical slice CAF; no equivale al producto completo.

## Estado y siguiente paso

**Gate permanente:** `BLOCKED_METHOD_CONTRACT_SYNTHETIC_DES_UNCALIBRATED_ERROR_NO_REAL_DATA`. Mantener PR Draft sin merge. Revisión adversativa enfocada en sonido de cotas, calidad de las cubiertas y contratos de incertidumbre. Siguiente tarea: integrar fuentes de medición y modelos de error calibrados, y luego construir adaptadores físicos reales a D/B/M bajo contrato existente. No regresar a rejillas de capacidad, ni convertir falsificaciones relativas en afirmaciones de topología demostrada.
