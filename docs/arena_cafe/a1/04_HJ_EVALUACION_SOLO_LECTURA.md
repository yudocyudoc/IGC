# A1 · Cuarto incremento: operadores `H_j` evaluables sin sustituir D ni Short E1

**Fecha:** 2026-11-02  
**PR:** [#135](https://github.com/yudocyudoc/IGC/pull/135), apilado sobre [F0-HIST #134](https://github.com/yudocyudoc/IGC/pull/134).  
**Estado:** contrato de comparación **implementado**; no hay traza de modelo nativo alimentado legítimamente con esta evidencia de cafetería; `INTERFACE-01=PARTIAL`, `CONDITION-01=PARTIAL`, `MODEL-01=NOT_RUN` y `A1=PARTIAL`.

## Qué significa «operador ejecutable»

`scripts/arena_cafe/observation_eval.py` es una capa **de observación posterior a la simulación**, no un motor de hipótesis ni un adaptador que invente entradas. Recibe una única evidencia visible, su `observation_ports.py` validado y, **solo si existe**, un CSV de trayectoria de candidato. Valida nuevamente que el puerto corresponde exactamente al `input_hash`, condición y reglas de la evidencia.

Sin CSV devuelve `ABSTAIN_NO_ADMISSIBLE_NATIVE_TRAJECTORY`, cero comparaciones, sin seleccionar ni fabricar un modelo. Con CSV ofrece solo un `DESCRIPTIVE_HJ_PROBE_ONLY_UNVERIFIED_TRACE`, porque un archivo CSV por sí solo **no** acredita procedencia del solver ni compatibilidad del estímulo. Una prueba numérica con un fixture tampoco es una corrida de OpenModelica.

## Correspondencias ejecutadas

| Brazo | Observación POS o física | `H_j` sobre una trayectoria explícita |
|---|---|---|
| D | pedidos creados acumulados | integral numérica de `inputRate` desde t=0 hasta cada muestra, en pedidos; **no suministra ni estima `inputRate`** |
| D | pedidos entregados acumulados | muestra directa de `delivered(t)` |
| M | pedidos creados acumulados | integral numérica del puerto `<id_source>.outflow` validado desde el AST E1; `units/hour` convertidos a pedidos/minuto |
| M | pedidos entregados acumulados | muestra `deliveredTotal(t)`, del backend Short E1 |
| M/O1 | servicios instrumentados completos en preparación | integral del puerto `<id_preparation>.completed`, con `FLOW<U>` resuelto por `role_bindings` a `FLOW<ReadyOrder>`. Contraste **descriptivo** de un conteo discreto contra un flujo continuo; no asume igualdad de mecanismos |
| D/O1 o M/O1 | espera y duración media | **NO COMPARABLE**: ninguna correspondencia validada a una duración física nativa todavía |

Para M se usa el **compositor E1 original**, no un parser propio de topologías: el AST debe satisfacer `composer.check_graph`, coincidir en SHA canónico con un miembro del universo enumerado del registro aprobado, y poseer exactamente un `source`, un `preparation` y un `receipt`. Los IDs de puerto se resuelven desde las instancias reales del AST. Para D no se acepta un AST E1 ajeno a su gramática.

## Política numérica y límites

- Las muestras observadas son acumulados estrictamente anteriores a t sobre `[0,10)`. En el modelo se exige muestra exactamente disponible en cada t solicitado; **no hay interpolación** ni imputación de tiempos individuales de llegada. Un CSV con tiempos posteriores al cutoff, ausencia de muestras o contradicciones entre duplicados se rechaza.
- Los CSV de D usan **minutos**; los CSV nativos Short E1 usan **horas**; para estos últimos `t_minutes=60×time_hours` y `rate_orders/min=rate_units/hour/60`. **Una unidad E1 por pedido es una hipótesis de mapeo, no validación empírica**.
- Los integrales se aproximan por trapecios sobre la malla real del CSV; una discontinuidad puede inducir error de cuadratura. Se devuelven predicciones y residuos **sin umbral, ranking, selección ni inferencia G2/G3**. El signo del residuo es predicho menos observado.
- Números no finitos, material negativo, tiempo no monótono, valores acumulados decrecientes, columna ambigua y tiempo futuro se rechazan.
- Se usa `sha256` del archivo para trazabilidad de bytes, no para autenticar procedencia. No hay firma de corrida, evidencia de fuente original o mandato de ejecución; `input_trace_provenance=NOT_AUTHENTICATED_BY_THIS_EVALUATOR`.

## Evidencia y ensayos

Las pruebas `tests/test_arena_cafe_a1_observation_eval.py` usan **fixtures numéricos de ingeniería explícitamente identificados**; comprueban operadores, unidades, correspondencias del AST original, 10 minutos de ventana y casos negativos. No se publican como predicciones del motor. En la matriz CI, los trabajos D y M invocan esta capa **sin CSV** y la salida obligatoria es abstención; la adjudicación revisa esos recibos. Buffalo conserva su ejecutor original en modo mock y no usa este operador.

Los archivos D `scripts/arena_d_v01.py` y M `scripts/arena_m_short_e1.py`, E1 `composer.py` / `backend.py` y la física del DES **no se modifican**.

## Siguiente decisión de implementación

Para lograr `SUPPORTED_AND_CONSUMED` aún se necesita **una trayectoria verdaderamente originada en el motor nativo con estímulo admisible**, acompañada de manifiesto de solver/candidato y observaciones compatibles. Eso exige un contrato de estímulo observado por intervalo para D y E1 con control de incertidumbre, no sustituir los datos POS por un pulso uniforme supuesto. Alternativamente, registrar una abstención científicamente justificada para la condición que no permita simular, **sin presentar la prueba de operadores como una inferencia**.

`BASELINE-01` registrado; `EVIDENCE-01` PASS offline; `INTERFACE-01` y `CONDITION-01` **PARTIAL**; `MODEL-01`, `MEMORY-01`, F2 y F3 **NOT_RUN**. Ninguna llamada Buffalo live ni fusion de PR.
