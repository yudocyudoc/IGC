# Arena IGC · F4 / B2 · Períodos de procesamiento y sensibilidad a una intervención

**Fecha:** 2026-11-03 · **Naturaleza:** control **retrospectivo** del evaluador con física sintética EV-01 conocida. No es inferencia de los brazos D/B/M ni reserva G5. Se apoya en los dos mundos **ya publicados** en F4 [simetría FIFO](03_SIMETRIA_CUELLO_LATENTE_O0_O1.md). Ningún parámetro del mundo fue ajustado para lograr un resultado de APM.

## Pregunta de trabajo

¿Una referencia de períodos activos identificada desde B2 permite distinguir, en el evaluador, **qué estación procesa de manera ininterrumpida durante más tiempo** antes y después de la misma intervención? ¿Y cómo se relaciona esa referencia con la **sensibilidad del número de entregas**? No es lo mismo detectar un período ocupado largo que demostrar la causa de un cuello de botella.

**Restricción metodológica decisiva:** B2 observa `PROCESSING` directamente, pero, **sin telemetría explícita de disponibilidad**, cataloga tiempo sin servicio como `UNKNOWN`, no `IDLE_AVAILABLE`. Además no observa `SETUP`, `CLEANING`, `BREAKDOWN` ni `BLOCKING`. Por tanto implementamos **un proxy de APM definido como el mayor período continuo en `PROCESSING` por recurso individual**, no un Active Period Method completo ni una etiqueta de verdad causal. No atribuir resultados del proxy a fuentes que no son observables en O0/O1.

## Origen y trazabilidad de los dos mundos existentes

Los mismos mundos del PR #152:
- A: original EV-01, caja con 2 servidores, preparación con 1, despacho con 1, transferencia final con 1.
- B: misma caja y preparación; tiempos de servicio de despacho y transferencia **intercambiados** por la simetría FIFO demostrada en F4.
- Ambas condiciones conservan **todas las 15 fechas de entrega terminal** y el mismo O0/O1. La restricción inicial común es preparación. La identidad de las salidas tiene alcance restringido a FIFO, un solo servidor en esas dos estaciones, sin bloqueo, buffers ilimitados y tiempos constantes.
- Intervención adversa común **+1/2 minuto de trabajo por pedido en despacho desde t=0**, con los mismos 15 arribos y estados iniciales vacíos. No es una recomendación comercial ni una intervención ensayada con personal.

El nuevo evaluador reconstruye **intervalos de servicio** mediante recurrencias FIFO racionales; no introduce un motor de eventos alternativo, no ajusta configuraciones y no produce entradas para los brazos. Verifica la secuencia original de eventos FULL del mundo A contra `ev01.trace_generator()` y su paridad CAF-01. Verifica, además, por todas las marcas temporales originales, que los intervalos de los cuatro escenarios **coinciden exactamente con `des_engine.run_toy_engine()` en entregas, espera y ocupación**.

Luego transforma los intervalos a los eventos físicos que ya espera `f2_physical_controls.resource_periods`; B2 calcula sus segmentos con **`available=None`**, conservando `UNKNOWN` fuera de cada servicio. La instrumentación resultante en B no es un nuevo sensor ni una observación real: es salida del **mundo sintético evaluador**.

## Proxy operacional y sensibilidad

Para cada recurso individual `r`, se unen segmentos adyacentes marcados `PROCESSING`, sin convertir `UNKNOWN` en ociosidad. Se define:

\[
L_r=\max_{[a,b)\,\text{continuamente PROCESSING de }r}(b-a).
\]

El indicador por estación es `max_r L_r`: en caja, sus **dos servidores no se fusionan** para crear uno ficticio. El ganador es la estación con mayor `L_r`, no la que tenga necesariamente más espera, ni una causa identificada. Registramos por separado la suma de tiempos realmente procesando y el número de períodos, con unidades racionales.

Para sensibilidad mantenemos exactamente los resultados del DES original en `t=10`:

| Mundo | Entregas base | Entregas con el mismo estrés | Diferencia |
|---|---:|---:|---:|
| A | 8 | 6 | −2 |
| B | 8 | 8 | 0 |

La comparación incluye el ganador del **proxy** antes/después, pero **una coincidencia de ganador con la sensibilidad no valida causalidad general**. Para una etiqueta causal más fuerte harían falta intervenciones de aumento de capacidad, condiciones relevantes de disponibilidad, y pruebas independientes. Ninguno de esos experimentos se abre aquí.

## Hallazgo sobre horizonte de observación: evitar fuga temporal

El diagnóstico de mayor período `PROCESSING` se computa de **dos maneras**, ambas procedentes del mismo B2 físico sintético: limitado estrictamente a **[0,10)**, para coincidir con el momento en que se mide el efecto en entregas; y sobre el ciclo completo **[0,30)**, una observación **retrospectiva posterior**.

| Mundo/condición | Ganador por períodos PROCESSING hasta t=10 | Ganador a t=30 (retrospectivo) | Entregas t=10 |
|---|---|---|---:|
| A, base | Preparación | Preparación | 8 |
| B, base | Preparación | Preparación | 8 |
| A, +30 s/pedido en despacho | **Preparación** | **Despacho** | **6** |
| B, +30 s/pedido en despacho | Preparación | Preparación | 8 |

En [0,30), el mayor período individual observado de preparación es **225/17 minutos (≈13.2353)** en ambos mundos. Bajo el estrés en A, despacho procesa ininterrumpidamente durante **1545/86 minutos (≈17.9651)**, y supera al de preparación. En B la preparación permanece como ganadora. Los dos cajeros se analizan **como recursos diferentes**; la longitud mayor de uno es 8 minutos, no la suma de sus 15 minutos de ocupación total.

**Consecuencia:** A **ya perdió dos entregas al minuto 10** aun cuando el proxy de procesamiento acotado al minuto 10 seguía identificando preparación. El cambio hacia despacho se reconoce **a posteriori** al permitir que la observación continúe hasta t=30. **Utilizar el ganador a t=30 para explicar una supuesta predicción emitida en t=10 introduciría fuga de información futura.** Este ejemplo no valida APM como predictor temprano de restricciones latentes, ni obliga a declarar que una estación sea el cuello causal verdadero.

## Salidas y pruebas

- `scripts/arena_cafe/f4_b2_processing_intervention.py`: construcción y comprobación del evaluador. Reporta **dos cortes** (t10 y t30) sobre los mismos segmentos B2; impide usar información posterior a t10 en el diagnóstico recortado. No crea modelos nativos ni acceso a proveedores.
- `tests/test_arena_cafe_f4_b2_processing_intervention.py`: unión de episodios `PROCESSING` adyacentes, rechazo de `IDLE_AVAILABLE` sin disponibilidad, consistencia B2 por recurso, caja con dos servidores, eventos originales FULL, paridad DES, alteración del calendario, misma intervención y frontera científica.
- `.github/workflows/arena-cafe-f4-b2-processing-intervention.yml`: reutiliza los artefactos públicos originales de O0/O1 y ejecuta el DES original y B2. Publica **estadísticas del evaluador**, nunca el log por pedido ni su configuración como insumos de D/B/M.
- El informe muestra **por estación y recurso** la longitud máxima de procesamiento continuo, su duración total y el número de episodios, además del resultado de la intervención. Distingue claramente que la referencia APM aquí es un **proxy limitado**, no el método completo.

## Qué no demostraría esta campaña

1. Que O0 u O1 permitan recuperar la identidad del cuello. Ambos mundos son indistinguibles con esas observaciones y los datos de B2/FULL **no se entregan** a D/B/M.
2. Que la estación que más tiempo procesa sea la causa exclusiva o suficiente de las diferencias de producción.
3. Que el método completo de períodos activos funcione bajo equipos bloqueados, recursos compartidos, prioridades o limpieza no instrumentada.
4. Que las perturbaciones de servicio sean físicamente viables o económicamente deseables.
5. Que exista ventaja incremental de minería de procesos, identificación nativa de Buffalo, calibración de E1, G4, G5 o un nuevo conjunto prospectivo. Estos estados **permanecen sin ejecutar**.

**Decisión:** conservar este test como comparación descriptiva de **ocupación observable** frente a **consecuencia intervencional condicionada al DES**. EV-01 y los dos mundos derivados ya son controles conocidos; no reutilizarlos como «prueba ciega» para favorecer ningún brazo.
