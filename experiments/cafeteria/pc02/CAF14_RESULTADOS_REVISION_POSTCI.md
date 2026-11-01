# CAF-14 — Informe canónico post-CI y revisión adversativa

**Fecha de protocolo:** 2026-10-31 local; protocolo congelado en el **primer commit** `153e4e18de83c35609b64abd98f958c796ecd11a` ANTES de código, CI o evaluación. **Este documento se escribe DESPUÉS de conocer resultados**, sin cambiar criterios, universos, sensores o programas. PR #126 Draft apilado sobre PR #125, a su vez sobre #124 y #123. Ninguno fusionado.

## Evidencia y reproducibilidad

- **[GitHub Actions #41258457124](https://github.com/yudocyudoc/IGC/actions/runs/41258457124)**: **7/7 tests PASS**, ejecución del factorial completo **32 mundos × 18 programas × 6 familias = 3,456 filtros**, comparación de 18×15 = 270 parejas estructurales.
- Head experimental probado `7d49d14c4e9db5a8ab6af1adc5e058c6bc3f5941`; **checkout del merge sintético** `8c93320f275ade482fc2ee3fc99bd029d8a8eea2`. Son SHA distintos, guardados por separado en el plan y el informe.
- **[Artefacto canónico](https://github.com/yudocyudoc/IGC/actions/runs/41258457124/artifacts/13062959512)**, 6 archivos: `00B_EXACT_SIGNATURES_BEFORE_EVAL.json`, `00_PLAN_BEFORE_EVAL.json`, `00C_GLOBAL_GRAPH_BEFORE_EVAL.json`, `01_RESULTADOS.json`, `02_INFORME.md`, `03_MANIFIESTO.json`. Verificado: **5/5 hashes SHA256 de archivos previos coinciden** con el manifiesto.
- El plan registra `new_world_DES_calls_before_plan=0`. El catálogo de 108 firmas continuas exactas y el grafo de 270 parejas se calcularon y guardaron ANTES de llamar al DES evaluador de mundos, aunque usan la misma física pública de CAF-01.
- Tests cubren prefijo de llegadas antes de t20, conservación de pedidos, la equivalencia de la recurrencia simbólica con snapshots DES nativos en 6 estructuras × 3 tasas × 5 instantes × 6 capacidades (incluida fraccionaria), continuidad de familia y BASE respecto de CAF-13, y ventanas T1/T2 con el mismo parámetro físico.

## Hallazgo principal: la excitación puede cambiar la separabilidad GLOBAL

En CAF-13, bajo todas las ocho observaciones que se estudiaron, **15/15 pares de seis familias eran CONFUSABLE_EXISTENTIAL**. En CAF-14, introducir una tasa de demanda **150/h**, superior a TODO el dominio de capacidad nominal `[55,110]/h`, y observar colas+stocks a **t20 o t25**, reduce a **4/15 pares confundibles**, y hace **11/15 globalmente separables** bajo la banda ±1 y los programas congelados.

**Resultados del factorial, sin declarar óptimo de política**:

| Demanda (pedidos/h) | t10: separables/15 | t15 | t20 | t25 | t40 |
|---|---:|---:|---:|---:|---:|
| 90 | 0 | 0 | 0 | 0 | 0 |
| 108 | 0 | 0 | 0 | 0 | 0 |
| **150** | 0 | 0 | **11** | **11** | 0 |

Los **dos programas multiventana** de 150/h `W_R25_T10_T20` y `W_R25_T15_T20`, que observan dos momentos del MISMO pulso, también alcanzan **11/15**, pero **no superan** la firma única a t20 bajo la métrica global. Dos instantes no son dos réplicas estadísticas independientes. El valor de una medición depende del tiempo de acumulación de colas/stock, no del número bruto de canales.

Es incorrecto afirmar que “se identifican todos los mecanismos” o que la excitación de 150/h sea necesaria/suficiente para otros modelos. La garantía global se refiere exclusivamente al menú de seis familias, los intervalos de capacidades, sensores de conteos y ±1 que fijamos.

## Cuatro pares que siguen confundibles pese a la presión extrema

En los programas `F_R25_T20`, `F_R25_T25` y los dos de ventanas múltiples siguen existiendo testigos de confusión para EXACTAMENTE estas parejas:

1. `preparacion` frente a `preparacion+despacho`;
2. `preparacion` frente a `preparacion+entrega`;
3. `despacho` frente a `despacho+entrega`;
4. `preparacion+despacho` frente a `preparacion+entrega` (**doble contra doble**).

En `F_R25_T20` los testigos hallados están en **c=110 pedidos/hora para AMBAS familias**. Ejemplo último par (firma ordenada `K0,K1,waiting_p,waiting_d,waiting_e,stock_p,stock_d,stock_e`):

- `preparacion+despacho`, c=110/h: `[9,27,13,0,0,14,1,2]`.
- `preparacion+entrega`, c=110/h: `[9,27,13,0,0,14,2,1]`.

Se diferencian solamente en los stocks de despacho y entrega por **una unidad**. Sus cajas de observación ±1 **se intersectan**; por tanto NO son globalmente robustas a esa tolerancia. Nótese que **no son firmas idénticas**, sino confundibles bajo error acotado. Para afirmar separabilidad con sensores de mayor precisión es necesario un experimento distinto, con tolerancias predeclaradas y justificadas físicamente.

## Distinguibilidad global ≠ diagnóstico único en mundos concretos

Aunque once pares sean separables globalmente, NO significa que todas las seis familias sean mutuamente separables; un mundo aún puede conservar un rival del catálogo. Sobre **27 mundos in-family**, incluyendo **18 dobles**:

- `F_R25_T20` y `F_R25_T25`: **3/27 clases únicas correctas y robustas ±1**, exclusivamente `SINGLE_68_2`, `SINGLE_83_2` y `SINGLE_97_2` (todas cuello único en entrega).
- **0/18 dobles únicos**, y 0/18 dobles robustamente únicos, aun con presión elevada. La clase y capacidad verdaderas siguieron contenidas en **27/27 en TODOS los 18 programas**, autoconsistencia de la misma física DES.
- Los controles de **cinco mundos con cuarta etapa fuera de catálogo** quedaron **5/5 fuera de todas las seis familias** en `F_R25_T15`, `F_R25_T20`, `F_R25_T25` y ambos programas multiventana: no hubo diagnóstico único falso en estos escenarios. Esto **no demuestra la cuarta etapa específica**, ni proporciona sensibilidad universal ante estructuras desconocidas; la regla sigue siendo incompatibilidad de la familia bajo supuestos.
- `F_R25_T10`: todos los 32 mundos tienen alguna cola no nula, pero sigue habiendo 15/15 pares globalmente confundibles. **Ver cola ≠ obtener separabilidad.**
- `F_R25_T40`: sólo **9/32 mundos** tienen colas no nulas y 15/15 pares vuelven a ser globalmente confundibles. Bajo 90/h y 108/h la sonda t40 devuelve cero colas en **32/32** mundos, reproduciendo pérdida de información temporal. No inferir que *todos* los mundos y regímenes siempre drenen a t40.
- Comparar promedio final de clases también es útil pero no equivale a certificación: para `F_R25_T20`, media **2.4444** clases entre los 27 mundos in-family.

## Física, causalidad y crítica al modelo

Se puede afirmar que variar la **demanda controlada del simulador** cambia las respuestas observadas; eso no proporciona por sí mismo un mecanismo causal descubierto independientemente, dado que el algoritmo conoce y utiliza las leyes físicas de CAF-01.

La persistencia del último par doble (`preparacion+despacho` vs `preparacion+entrega`) está ligada a la posibilidad de colocar una segunda etapa limitada aguas abajo con casi ningún stock diferencial visible por la granularidad ±1 y la secuencia FIFO. La explicación física se propone como hipótesis: CAF-14 demuestra testigos concretos y exhaustividad de firmas **dentro del modelo**, no un teorema sobre redes de colas en general.

**Riesgos de extrapolación:**
- El umbral 150/h puede exceder infraestructura/demanda admisible de un negocio real; no es una receta operacional.
- Los sensores completos `waiting+stage_stock` en todas las etapas pueden ser caros o inviables. No tienen costo económico validado y **no pertenecen al menú original CAF-07B**.
- La banda ±1 no representa error instrumental calibrado ni una distribución probabilística. Una mejora al disminuirla sin medición física sería autoengaño.
- Familias con dos cuellos comparten exactamente la misma capacidad c por construcción; capacidades independientes multiplicarían los grados de libertad y podrían restaurar confusibilidad.
- Las estructuras desconocidas podrían imitar firmas dentro de las seis familias aunque los cinco controles actuales hayan sido rechazados bajo presión.

## Próximo paso recomendado, para deliberación ANTES de nuevo código

**No realizar otro torneo de selectores.** Abordar si la última ambigüedad estructural se puede reducir mediante **mediciones de tiempos por pedido y etapas**, y evaluar si el efecto persiste cuando el servicio tenga variación física plausible y sensores tengan precisión justificada. La estimación de dos capacidades independientes por doble cuello sería una prueba de fragilidad necesaria antes de considerar una arquitectura general.

Secuencia sugerida: (1) revisión adversativa de las cuatro parejas residuales, (2) modelo de sensor con resolución/error explícito y medición temporal realista, (3) doble capacidad continua independiente y/o servicio estocástico sobre nuevos mundos no utilizados, (4) pruebas con generador independiente. Cada fase debe evitar ajustar mundos y métricas después de resultados.

**Gate permanente:** `BLOCKED_SAME_DES_PHYSICS_UNCALIBRATED_TOLERANCE_NO_EXTERNAL_VALIDATION`. Mantener PR #126 Draft, sin merge, despliegue ni certificación científica.
