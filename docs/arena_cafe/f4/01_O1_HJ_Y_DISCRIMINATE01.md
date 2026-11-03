# F4 · O1 como operador de observación y estado DISCRIMINATE-01

**Fecha:** 2026-11-03. **Base:** plan cafetería v3.2, F3→F4→F5; testigo físico F4 del PR #148. **Resultado de esta entrega:** examen retrospectivo de un *dato O1 ya existente* en lugar de suponer que la ambigüedad O0 se conserva después de añadir información. No se usan mallas ni parámetros calibrados por búsqueda. No existe evaluación prospectiva en este incremento.

## El hallazgo que cambia el siguiente paso

El testigo de desarrollo F4 contiene dos explicaciones físicas que dan exactamente el mismo O0 público: **8 entregas al minuto 10**. En el mismo control, O1 publica un agregado con definición precisa: **9 servicios de preparación completados antes de minuto 10, media de servicio `15/17` minutos y media de espera `1204/765` minutos**. Los números proceden del sobre O1 original, no de un archivo FULL suministrado a D/M/B.

| Magnitud | O1 (mundo observado) | Mecanismo F4-A | Mecanismo F4-B |
|---|---:|---:|---:|
| Servicio medio en preparación (minutos exactos) | 15/17 | 1 | 3/5 |
| Estado de coincidencia exacta de la media | Observado | **NO** | **NO** |
| Entregas acumuladas O0 al t=10 | 8 | 8 | 8 |

**Un dato adicional legítimamente observado puede rechazar ambas explicaciones.** No debemos declarar «A o B son las posibilidades reales» solo porque constituyen dos hipótesis O0 compatibles. En el modelo de servicio fijo de ambos mecanismos, el tiempo medio de los *servicios completados* equivale al tiempo fijo de preparación; ése es el operador de observación `H_j` adecuado para dicha magnitud. No corresponde comparar esa medición con una tasa de entregas ni con los stocks de D/M por semejanza de nombre.

El script `scripts/arena_cafe/f4_o1_preparation_operator.py` usa solo **O0 y O1 públicos**, más el testigo F4 congelado. Reejecuta el **DES original** solo para leer en t<10 el conteo de trabajos que dejaron la primera etapa, por balance exacto:
`preparación completada(t) = entradas aceptadas(t) − (esperando_preparación(t)+en_servicio_preparación(t))`.
Comprueba también que el conteo no cambia por un evento exactamente en t=10. Para la media de servicio usa la duración **determinista exacta** declarada en la hipótesis; no infiere ni fabrica esperas por pedido desde snapshots agregados.

La igualdad o desigualdad se interpreta **condicionada a la correspondencia operacional de «preparación» en las hipótesis con el agregado publicado**. Los nombres internos de F4 no fueron identificados a partir de O0; son afirmaciones del constructor. La comparación **no demuestra** que el mundo real tenga esas mismas etapas o que sus tiempos de servicio sean constantes. No se ha medido aquí precisión instrumental, error de reloj ni variabilidad empírica; una falta de igualdad exacta no debe convertirse en un rechazo estadístico fuera de este control sintético.

## DISCRIMINATE-01 · Diseño científico, no congelación G4

**Pregunta única, predictiva:** dadas observaciones iniciales compartidas S0, ¿dos mecanismos con restricciones en distintas etapas pueden generar respuestas diferentes a la **misma intervención viable** y puede una medición adicional con semántica válida reducir la clase de mecanismos compatibles?

**Desarrollo conocido:** en F4, A y B producen igual O0 y ante +1 servidor en preparación desde el inicio, A entrega 14 y B 8 pedidos al minuto 10. Este resultado **es un testigo construido con O0 ya consultado**, no un umbral obtenido en mundos independientes. No hay costes ni viabilidad operativa; no hacer afirmación decisional.

**Nueva comprobación O1:** ambos mecanismos son incompatibles con la media exacta autorizada de preparación. Por lo tanto el par **no cumple** la hipótesis de «ambigüedad también bajo S1=O1» si se quisiera plantear esa pregunta. Elegir retrospectivamente otra tupla para obligar a que sobreviva sería otra forma de sobreajuste. Una nueva pareja solo podría usarse como **desarrollo explícito** y requerir evaluación reservada distinta.

**F5 aún no está listo para ejecutarse.** Antes de congelar G4 deben concretarse y verificarse:

1. **Observabilidad y frontera:** S0/S1 deben ser dos vistas autorizadas del mismo hecho por mundo, con `H_j` por etapa y tiempo definido, censura anterior al cutoff y condiciones aisladas entre brazos y dentro de cada brazo. Ni FULL evaluador ni configuración privada entran inadvertidamente a S0.
2. **Mundos y variabilidad:** generador de desarrollo y reserva independiente con mecanismos rivales y, si procede, demanda, tiempos de servicio y capacidades variables físicamente justificadas. No se reutiliza el par F4 conocido como nuevo mundo «ciego». El tamaño de muestra se elige con piloto **separado de la reserva**, no con un N arbitrario ni después de mirar G5.
3. **Margen físico:** error/tolerancia de reloj, POS, KDS y servicio documentado por instrumento; regla de comparación común predeclarada, abstención y `MODEL_GAP` cuando ninguna hipótesis es compatible. La exactitud del simulador determinista no es error de sensor.
4. **Intervención:** añadir un servidor de preparación requiere verificar espacio, equipo, persona, inventario y factibilidad por mundo; si no, `FEASIBILITY_NOT_ASSESSED` y la propuesta no es consejo de gestión.
5. **Métodos D/B/M auténticos:** F3 sigue A3 `PARTIAL`, pues Buffalo no ejecutó inferencia original sobre EV-01 O0/O1. G4/G5 no pueden recibir un stub como si fuera modelo de B. Cada condición y productor requiere contexto, memoria y artefactos aislados.
6. **Prueba prospectiva:** congelar modelos, `H_j`, acciones, predicciones o abstenciones, margen y regla de falsación **antes** de abrir una reserva nueva. Informar `FALSE_UNIQUE`, `MODEL_GAP` y clases compatibles; un buen ajuste de O0 no es predicción exitosa.

**Estado técnico DISCRIMINATE-01:** `DEVELOPMENT_WITNESS_EXISTS; O1_EXACT_EXCLUDES_BOTH; F5_NOT_READY`. Es un diagnóstico de **diseño**, no una evaluación de hipótesis prospectiva. No congelar G4 todavía.

## Minería de procesos: una pregunta causal, no otra herramienta por instalar

El PR #147 ya encontró que **el DFG de PM4Py en EV-01 FULL no añade variación de rutas a B1**. En esta pareja F4, el observable adicional **no es P**, sino un agregado de servicio ya publicado en O1. Por lo tanto no se le atribuye a PM la distinción ni se recomienda correr PM4Py otra vez.

Solo si un nuevo estudio observa **retrabajo, rutas variables, lotes, prioridad o recursos compartidos** que B1/B2 no pueden recuperar suficientemente se justifica evaluar P; hacerlo requiere idénticos logs/sensores y ablación *dentro* de D, B y M, conservando reserva adicional si se seleccionó P al ver resultados F5. Si no aparece regularidad nueva, `PM_NOT_JUSTIFIED` para ese control, **no «PM inútil siempre»**.

## Verificación y límites

La CI descarga O0/O1 de la ejecución A1 original y el testigo F4 existente; tests adversariales comprueban identidad del mundo, integridad de snapshots, material conservado, regla estricta de cutoff y no asignación de ganador cuando ambos fallan. **No hay eventos FULL ni proveedores live en esta prueba**. No se altera la semántica original de PM4Py, DES, D, M o B.

**Estado:** `A3=PARTIAL` · `G4=NOT_RUN` · `G5=NOT_RUN` · `F5=NOT_READY` · `PM=CONDICIONAL` · no nueva malla ni selector de modelos.
