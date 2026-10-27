# Arena Buffalo — contraste de mecanismos congelados B2 versus B3 a baja utilización

**Fecha:** 2026-10-26. **Estado:** simulación OpenModelica completada y auditada. [Ejecución #40396917502](https://github.com/yudocyudoc/IGC/actions/runs/40396917502), todos los pasos **SUCCESS**. [Artefacto #12687650066](https://github.com/yudocyudoc/IGC/actions/runs/40396917502/artifacts/12687650066), ZIP con fuentes `.mo`, `b2_res.csv`, `b3_res.csv`, `manifest.json`, `comparison.json` y el log original.

## Por qué hacía falta

Astra R2 observó que la revisión B3 —recibió una pista sobre la utilización al cuadrado— mejoró ligeramente el RMSE sobre el pulso original, pero solo desplazó las tres entregas acumuladas registradas. Con entradas suficientemente grandes la función de utilización llega a 1 y las expresiones `u` y `u²` resultan indistinguibles. Era necesario consultar las **predicciones divergentes** del mismo par de ecuaciones manteniendo la utilización parcial.

Este experimento no usa observaciones para seleccionar una estructura; sirve para diseñar una **condición de discriminación** entre dos mecanismos previamente producidos, sin inferencia adicional.

## Métodos y autenticación

1. Se recuperaron los **archivos nativos reales** Buffalo B2 y B3 desde los artefactos históricos:
   - B2: SHA-256 `d7630830b4812c8880dc88c5f93f821707a75d22e0ecdf2cc1e9b5d8ec0889b9`, respuesta de [#40259178852](https://github.com/yudocyudoc/IGC/actions/runs/40259178852).
   - B3: SHA-256 `dfe45d3128bbf9aaa91a2d0be0028f4b8be29610b42d9114e4dae09fc4a14c2b`, respuesta completa de [#40290192821](https://github.com/yudocyudoc/IGC/actions/runs/40290192821).
2. **La única modificación autorizada en cada archivo nativo** es la tasa de entrada exógena: `arrival rate = 1.7` → `0.4 items/hour`. La función pulso, su duración nominal de 2 h, la capacidad nominal 0.6/h, las ecuaciones endógenas, relaciones nativas, lookups, condiciones iniciales y resto del modelo permanecen iguales. La operación inversa restituye ambos modelos originales.
3. El adaptador Buffalo→Modelica traduce ambos sin subtipos inventados, con las **mismas hipótesis condicionales** de lookup lineal, clamp de extremos y división segura. **No está demostrada la equivalencia con un simulador nativo Buffalo.**
4. Los dos se simulan mediante **OpenModelica 1.27.1 pinned**, Euler, \(\Delta t=0.125\) h, horizonte 0–8 h. No hay cambio de solver entre condiciones.
5. Antes de consultar resultados se fijó la ventana **t=0–2 h** y un umbral mínimo de separación máxima **0.025 elementos**. Se verifica conservación contra la **integral discreta real** de `arrivals` en cada CSV y que ambas entradas discretizadas sean idénticas. No se utilizan datos externos, holdout ni D/M.

Los mecanismos contrastados son:
- **B2:** `completion_capacity = nominal_capacity * capacity_utilization`; `completions = completion_capacity * capacity_utilization`, luego utilización al cuadrado.
- **B3:** `completion_capacity = nominal_capacity * capacity_utilization`; `completions = completion_capacity`, luego utilización simple.

## Trayectorias medidas desde CSV OpenModelica real

| Tiempo (h) | B2 entregados | B3 entregados | B3 − B2 | Ingreso discreto acumulado |
|---:|---:|---:|---:|---:|
| 0.00 | 0.000000 | 0.000000 | 0.000000 | 0.000 |
| 0.50 | 0.010073 | 0.034375 | +0.024302 | 0.150 |
| 0.75 | 0.049499 | 0.097461 | +0.047962 | 0.250 |
| 1.00 | 0.111565 | 0.175459 | +0.063895 | 0.350 |
| 1.50 | 0.277546 | 0.350292 | **+0.072746** | 0.550 |
| 2.00 | 0.467858 | 0.538634 | +0.070776 | 0.750 |
| 3.00 | 0.695808 | 0.770449 | +0.074641 | 0.800 |
| 4.00 | 0.740281 | 0.797042 | +0.056760 | 0.800 |
| 6.00 | 0.767310 | 0.799970 | +0.032660 | 0.800 |
| 8.00 | 0.777393 | 0.800000 | +0.022606 | 0.800 |

Dentro de la **ventana predeclarada** (t ≤ 2 h) la separación máxima fue **0.072746484163141 items**, superior al umbral predefinido 0.025. El intervalo t=2–3 presenta una separación ligeramente mayor (**0.074641**), **fuera** de la ventana fijada; no se usa para adjudicar el criterio previo.

La conservación material real fue:
- B2: máximo \(|pending + delivered - integrated(arrivals)|\) **5.55×10⁻¹⁶ items**.
- B3: máximo **2.22×10⁻¹⁶ items**.
- Diferencia entre las dos integrales discretas de entrada: **cero**.

## Distinción entre pulso ideal y pulso discretizado

El lookup de pulso vale cero en t=0 y OpenModelica Euler registra `arrivals(t=0)=0`. Por esa convención de frontera, en t=2 h la integral discreta de entrada es **0.75 items**, 0.05 por debajo del pulso rectangular ideal \(0.4 × 2 = 0.8\). Al terminar el escalón, la integral discreta llega a **0.8 items** en t=3. Ambas simulaciones reciben exactamente la misma entrada discreta; por eso este detalle **no invalida la comparación dentro del solver**, pero sí prohíbe describirla como una reproducción exacta del pulso rectangular continuo en todo instante.

El primer intento de verificación produjo `NOT_SAME_INPUT_OR_CONSERVATION_FAILED` por comparar la masa del solver con el pulso rectangular **ideal**. No había fallo de masa: el verificador se corrigió para integrar la entrada realmente registrada en ambos CSV. El cambio no modificó ningún modelo ni la excitación fijada.

## Interpretación y límites

**PASS:** los mecanismos congelados B2 y B3 predicen entregas claramente diferentes cuando la utilización permanece parcial. El nuevo estímulo discrimina sus consecuencias en una ventana previamente fijada, bajo el mismo solver.

**NO DEMOSTRADO:** si B2 o B3 corresponde a la cafetería real, si la corrección B3 identifica el verdadero mecanismo, si el simulador Buffalo original implementaría idénticamente las funciones gráficas o si alguno predice mejor un conjunto de observaciones reservadas. **No hay ganador, no hay holdout y no se da retroalimentación al LLM.**

El resultado ilustra una función futura del revisor: ante hipótesis que coinciden en un régimen saturado, solicitar una medición en un régimen de utilización parcial que revele cuál ecuación es más compatible con el campo real.
