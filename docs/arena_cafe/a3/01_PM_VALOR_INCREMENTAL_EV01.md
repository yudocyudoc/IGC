# Arena IGC · F3 · Valor informativo incremental de minería P en EV-01

**Fecha:** 2026-11-03. **Plan:** `REVISION_Y_PLAN_IMPLEMENTACION_CAFETERIA_V3_2_2026-11-02`, F3/F4 y F6 condicional. **Pregunta central:** ¿la minería de procesos descubre una regularidad *no recuperable mediante B1/B2* que ayude a resolver la no identificabilidad de cuellos de botella?

**Este incremento NO implementa otro motor PM, no usa mallas de parámetros, no llama a Buffalo y no inicia una campaña de identificación.** Reutiliza la minería PM4Py **ya ejecutada** en EV-01 y contrasta sus resultados con B1/B2 de la **misma fuente FULL instrumentada**. Solo tiene validez descriptiva sobre EV-01 conocido; no es un resultado F6 ni una evaluación G4/G5.

## Evidencia original, sin repetir métodos

- [EV-01 — CI histórica 41356387093](https://github.com/yudocyudoc/IGC/actions/runs/41356387093) / artefacto `arena-ev01-pos-kds-full-evidence` (incluye el resultado original `02_RESULTS.json` con `pm4py_discovery`, generado mediante `PM4Py.discover_dfg` y las vistas separadas). 15 pedidos; POS 45 eventos, POS+KDS 75, FULL 225.
- [F2 — CI 41552216315](https://github.com/yudocyudoc/IGC/actions/runs/41552216315) / artefacto `a2-cafe-f2-evaluator-physical-controls`: B0 POS, B1 mediciones físicas FULL, B2 períodos por `resource_id`. B1 ya observa directamente el orden de cuatro etapas, sus entradas, inicios y finales; no adivina etapas privadas desde POS.
- [A1 — CI 41575917332](https://github.com/yudocyudoc/IGC/actions/runs/41575917332) / artefacto `a1-cafe-public-evidence`: O0 incluye tiempos de creación POS y entregas acumuladas; O1 agrega **solamente** estadísticos censurados de preparación, no trayectorias FULL por pedido.
- F3 previo: D y M tienen generación/solución nativa comprobada, con alcance y parámetros nominales declarados; Buffalo sigue sin inferencia auténtica **de EV-01 O0/O1** por falta de autorización para llamadas live. A3 permanece PARTIAL.

## Comparación sobre la misma información

| Evidencia | Lo que puede observar | Lo que no puede concluir |
|---|---|---|
| Productor O0 | Llegadas POS y entregas acumuladas | Rutas físicas internas, cuellos individuales o etapas privadas |
| Productor O1 | O0 + agregado autorizado de servicios completos de preparación | Ruta completa por caso; identidad de recursos y otros stages |
| B1 (evaluador FULL) | Orden físico de cuatro etapas y tiempos de cola y servicio por cada una | Cuello causal único por usar solo máximos de espera |
| B2 (evaluador FULL) | Estados/actividad de cinco recursos instrumentados | Cuello causal únicamente por ocupación o `ALL_ACTIVE` |
| PM4Py histórico FULL | Secuencia de actividades y DFG, **observadas** | Causa del cuello, topología causal latente desde datos POS |

El script `f3_pm_incremental.py` **no ejecuta PM4Py de nuevo**. Recalcula de manera independiente las sucesiones directas desde los eventos FULL cronológicos por `case_id`, exige igualdad **exacta** con las aristas, extremos y frecuencias de la minería ya realizada, y valida con el analizador físico existente los intervalos y recursos. También exige que la ruta observada en FULL coincida con el orden registrado por B1, sin consultar los parámetros privados del generador.

La capa FULL queda en el **job del evaluador**, jamás en los productores O0/O1; el artefacto publicado contiene exclusivamente resumen descriptivo, hashes de entradas y estado. No hay extracción de topología privada del modelo a partir del `case_id` público.

## Hallazgo acotado

Los DFG históricos muestran:

| Vista histórica | Actividades observadas | Aristas |
|---|---:|---:|
| POS | 3 | 2 |
| POS + KDS | 5 | 4 |
| FULL | 15 | 14 |

Para los 15 casos FULL, las 14 relaciones de sucesión del DFG completo se repiten 15 veces; las entradas por etapa son una sola ruta por pedido: **caja → preparación → despacho → transferencia final**. Esa etapa adicional es **observada directamente** en FULL, nunca inferida desde O0/O1. No hay variantes de ruta ni repetición de etapas en este control. La física por etapas ya está observada por B1; sus períodos de recurso ya están contabilizados por B2.

**Dictamen solo sobre este control:** `NO_INCREMENTAL_ROUTE_VARIATION_OVER_B1_IN_KNOWN_EV01`. No existe aquí un requisito nuevo de variación procesual que justifique una ablación `con P / sin P` ni la promoción de PM. Eso **no significa** que PM no pueda aportar valor en otra cafetería con retrabajos, rutas variables, lotes, recursos compartidos o excepciones realmente observables. Tampoco significa que B1 identifique de forma única el cuello causal.

La implementación original de PM4Py ya señala sucesiones observadas, **no relaciones causales**. Tampoco entrega las mismas evidencias a un productor O0 como si se hubiera instrumentado el negocio entero. Un DFG obtenido desde FULL evaluador no es evidencia legítima para D/B/M bajo O0.

## Qué sigue, sin desviaciones

**F3 sigue siendo la prioridad de integración.** No se puede cerrar A3 usando stubs o resultados históricos de Buffalo. El estado sin autorización de proveedor se mantiene explícito; ninguna ejecución de este incremento lo transforma en abstención del método.

La pregunta sobre no-identificabilidad de cuellos permanece abierta. El plan v3.2 reserva F4/F5 para hipótesis rivales bajo idéntica información y nuevas observaciones/acciones prospectivas. **Solo si aparece una regularidad procesual concreta no recuperada por B1/B2** se justifica someter P a una ablación controlada por cada brazo, con la misma evidencia y una reserva independiente cuando corresponda.

**Estados:** A3=PARTIAL; F6=NOT_ADJUDICATED; G4=NOT_RUN; G5=NOT_RUN; ninguna afirmación de sensor óptimo, ganador D/B/M, descubrimiento causal ni validez empírica.
