# Arena IGC · F4 · Una observación adicional que separa dos mecanismos compatibles con O0/O1

**Fecha:** 2026-11-03 · **Corte:** PR #157 / mundo A EV-01 original y mundo B con servicios de despacho y transferencia permutados, del PR #152. **Tipo de resultado:** testigo retrospectivo del evaluador, con verdad física sintética conocida. **No es una nueva condición de observación autorizada ni una prueba ciega G5.**

## Pregunta

En el caso F4 conocido, **O0 y O1 no separan** dos mundos que tienen exactamente las mismas quince fechas terminales de entrega y los mismos servicios de preparación, pero reaccionan de modo diferente a un aumento de 30 segundos de trabajo por pedido en despacho. El proxy parcial APM de PR #157 tampoco anticipa al minuto 10 la pérdida de entregas.

¿Cuál es una *medición adicional suficientemente informativa* **dentro de este par conocido y de la rejilla ya establecida** sin entregar el log FULL ni obligar a los brazos a conocer la configuración del evaluador?

## Testigo: un único conteo de despacho a t=6

El evaluador inspeccionó **después de construir y conocer ambos mundos** los conteos acumulados de servicios `servicio_fin` **en la estación explícitamente identificada como despacho**, estrictamente anteriores a cada corte temporal **ya existente** en O0/O1:

| Corte (min) | Mundo A, preparaciones de despacho terminadas | Mundo B, terminaciones en despacho | ¿Separa el par? |
|---|---:|---:|---|
| 0 | 0 | 0 | No |
| 2 | 0 | 0 | No |
| 4 | 2 | 2 | No |
| **6** | **4** | **5** | **Sí, en este par** |
| 8 | 6 | 7 | Sí, en este par |
| 10 | 9 | 9 | No |

**Precisión de vocabulario:** los números de la tabla son **terminaciones en despacho**, no entregas terminales ni terminaciones de preparación. Los dos mundos tienen la misma entrega terminal acumulada `[0,0,2,4,6,8]` y el mismo O1. Por eso solo un conteo en una estación adicional aporta la discriminación.

El **candidato de instrumentación** es una fuente capaz de informar **un solo escalar agregado**: `n_completados_despacho([0,6))`, con etiqueta de estación, tipo de evento y definición de corte. No se afirma que esto requiera un solo dispositivo físico: necesita un registro confiable de terminaciones de despacho y reloj común. El conteo acumulado a t=10, por sí solo, **no** discrimina el par; tomar la misma observación en un instante distinto puede cambiar la identificabilidad.

La condición `[0,6)` se computa para **un recorrido base sin intervención**. El resultado de aplicar después el estrés de +1/2 minuto por pedido desde `t=0` pertenece a **otro recorrido contrafactual desde estado inicial vacío**, no a una acción realizada a mitad del mismo recorrido. En un negocio real habría que diseñar un protocolo temporal distinto.

## Lo que esto demuestra y lo que NO demuestra

La regla finita de compatibilidad se puede escribir como:

- Si se observaran **exactamente 4** servicios en despacho terminados antes de t=6, solo el mundo A de **estos dos** sería compatible.
- Si fueran **exactamente 5**, solo el mundo B de **estos dos** sería compatible.
- Con un valor diferente, **ninguno de esos dos candidatos** sería compatible; no se deduce automáticamente cuál es el mecanismo verdadero.
- Si solo se midiera el mismo contador al minuto 10, ambos producirían 9, por lo que persistiría la ambigüedad.

**La regla solo distingue las dos hipótesis ya presentadas al evaluador.** No excluye ninguna tercera configuración de cafetería, no identifica causalmente una estructura arbitraria y no compara la inferencia nativa D/B/M.

Importante: se seleccionó la estación y el minuto **después de conocer los mecanismos y sus eventos privados**. Aunque el minuto 6 pertenece a la rejilla original, elegirlo de forma retrospectiva **contamina la evaluación**; no constituye selección predeclarada ni optimización de sensores en condiciones independientes. En un nuevo mundo se deberá precomprometer **antes de ver los resultados** la fuente, variable, corte, incertidumbre y criterio de adjudicación.

## Sensibilidad del registro temporal: cota matemática retrospectiva

En este par conocido, la distancia más pequeña entre el instante de t=6 y **cualquier terminación de despacho de los dos mundos** es **108/935 minutos ≈6.93 segundos**. Es una propiedad **del cronograma verdadero sintético del evaluador**, derivada incluso de eventos posteriores al corte, no una precisión medida de sensores.

Solo bajo los supuestos de **captura completa, ninguna duplicación ni clasificación de estación incorrecta y cada marca temporal con error absoluto estrictamente menor que esa distancia**, los conteos respectivos seguirían siendo 4 y 5. El límite es post-hoc y no debe prometerse para una cafetería real. En particular, una tolerancia de reloj sin controles de eventos perdidos o mala etiquetación no convierte el contador en evidencia fiable.

Tampoco se valida aquí la correspondencia conteo–fluido de Moléculas E1: el testigo es un **conteo discreto de una etapa física**, analizado solo por el evaluador.

## Implementación y trazabilidad

- `scripts/arena_cafe/f4_single_dispatch_count_observability.py`: valida las condiciones originales O0/O1, reutiliza **la pareja exacta del PR #152** y las trazas matemáticas y paridad DES/FULL de PR #157. Construye registros con la interfaz física existente B2 del evaluador, comprueba los pares de `servicio_inicio/servicio_fin` con recurso y caso, y agrega en las seis marcas temporales **sin publicar casos ni marcas individuales**. Emite compatibilidad únicamente entre dos hipótesis previamente declaradas.
- `tests/test_arena_cafe_f4_single_dispatch_count_observability.py`: prueba cortes `[0,t)` incluyendo un evento exactamente en t=6, registros duplicados o incompletos, cambios de estación/recurso, conteos a t6/t10, controles negativos de preparación/entregas y rechazo de inferencia fuera de dos mundos.
- `.github/workflows/arena-cafe-f4-single-dispatch-count.yml`: ejecuta sobre los **sobres públicos originales** y el DES original. Solo publica el resumen agregado del evaluador; no reutiliza las configuraciones privadas como insumo de D, Buffalo o Moléculas.

El artefacto puede contener resultados agregados de **ambos** mundos, porque esos mecanismos ya fueron publicados para desarrollo. Esto hace explícita y permanente la pérdida de ceguera prospectiva de EV-01 y de sus derivados. **No crea O2 en el contrato A1 de los métodos** ni modifica la evidencia que reciben D/B/M.

## Decisión

Este es un **testigo de identificabilidad de un par bajo una observación adicional**, no prueba de que sea la instrumentación más barata o la más informativa globalmente. La siguiente etapa científica tendría que evaluar en **mundos independientes precomprometidos** qué observación seleccionaría un método bajo límites reales de costo, precisión y disponibilidad, y si logra mejorar la decisión antes de intervenir.

**Estados inalterados:** F3/A3 `PARTIAL`; D/B/M no evaluados con O2; Buffalo live EV-01 `NOT_RUN`; F5 reserva independiente `NOT_CREATED`; G4/G5 `NOT_RUN`; PM-14 sin activación; costo y factibilidad física no medidos; llamadas proveedor `0`.
