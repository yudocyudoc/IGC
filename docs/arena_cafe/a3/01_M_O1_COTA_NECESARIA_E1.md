# F3 / Moléculas Short E1 · Certificado condicional de capacidad frente a O1

**Fecha:** 2026-11-03 · **Corte de implementación:** posterior al PR #153, dentro del F3/A3 parcial del plan cafetería v3.2. **Tipo:** contraste analítico de la capacidad nominal de Short E1 **a través de una correspondencia de medición expresamente NO VALIDADA**. No es G3 científico, no identifica el mecanismo causal, no ajusta parámetros, no selecciona un candidato.

## 1. Problema concreto que resolvemos

La auditoría F3 encontró cuatro soluciones OpenModelica D/M × O0/O1 auténticas sobre el POS reconstruido, pero **ningún generador D/M utiliza la evidencia adicional de preparación O1** al construir su modelo. E1 posee el puerto tipado `preparation.completed: FLOW<ReadyOrder>` (`units/hour`). O1 observa **9 eventos individuales de servicio de preparación completados antes de t=10 minutos**, con duración media **15/17 min** y espera media **1204/765 min** sobre los nueve terminados. La igualdad entre ese conteo discreto y la integral de un flujo continuo *no fue validada*: por eso el H_j previo no computó un G3 comparable.

Sin convertirlo en una igualdad establecida, podemos estudiar una **implicación necesaria condicional** de una hipótesis de correspondencia. Con ello O1 informa un **diagnóstico de incompatibilidad de la parametrización nominal**, sin ser un parámetro secreto importado ni alimentar la generación del modelo.

## 2. Regla exacta y límite físico de la molécula original

El catálogo original E0 `experiments/e0/catalog.json` registra `bounded-queue`, y la implementación en `src/modelica/IGCMolecules.mo` implementa `SystemDynamics.Rates.RRate release(minFlow=0,maxFlow=maxThroughput)`. La salida `release.y` está conectada al puerto `completed`. El registro original Short E1 `experiments/e1/registry.base.json` fija **`maxThroughput=20 units/hour` en la etapa `preparation`** y `responseTime=0.5 hours`. Los gráficos de E1 se generan por su compositor original, no por un banco nuevo de parámetros; sus composiciones publicadas mantienen una etapa de preparación con la misma parametrización.

Bajo el puente hipotético **una preparación física completada = una unidad ReadyOrder salida de la molécula**, el modelo tendría que satisfacer

\[
N_{\mathrm{fin,prep}}([0,T)) \leq \int_0^T \mathrm{completed}_{E1}(t)\,dt
\leq \mathrm{maxThroughput}_{E1}\cdot T.
\]

Para el control EV-01 `T=10/60=1/6 h`:

\[
9 \;\not\leq\;20\cdot\frac16=\frac{10}{3}\approx3.333.
\]

El faltante, **si se impone ese puente**, es `9−10/3=17/3` unidades. Se requeriría una capacidad de salida media de **al menos 54 unidades/h** para satisfacer únicamente esa condición necesaria. **54 NO es una capacidad estimada, calibración recomendada, parámetro ajustado ni límite suficiente** para reproducir el proceso: no se modifica `maxThroughput`, `responseTime` ni las moléculas. La desigualdad ignora explícitamente restricciones dinámicas adicionales y nunca acredita un modelo cuando se satisface.

**Significado correcto:** todos los candidatos con **los mismos parámetros congelados** de ese registro fallarían **si** adoptáramos la equivalencia de una unidad de flujo por cada preparación física terminada. **No significa** que toda la familia E1, una variante con nuevos parámetros, ni la física empresarial estén falsadas. También puede fallar la correspondencia entre una unidad abstracta y una terminación física. Es un `MODEL_GAP` *condicional a un supuesto de medición*, no un diagnóstico causal incondicional.

## 3. Qué cambia realmente en la Arena

`scripts/arena_cafe/m_o1_capacity_certificate.py` ejecuta un control sobre **solo el sobre O1 público y el candidato E1 auténtico**. Verifica:

- fuente O1, su digest y su corte; clase física Modelica `BoundedQueue` con salida efectivamente limitada;
- gramática y candidatos del compositor original E1, AST **íntegro y parámetros congelados**, tipo del puerto `FLOW<ReadyOrder>` y ausencia de candidatos reparametrizados;
- la cota racional de tiempo y caudal y la diferencia respecto a los nueve servicios terminados, con estado `EXCLUDED_BY_NECESSARY_CAPACITY_BOUND_IF_ONE_TO_ONE_BRIDGE`;
- `bridge_empirically_verified=false`; `method_level_scientific_G3=NOT_ESTABLISHED`; `candidate_selected_or_fitted_using_O1=false`.

El diagnóstico se integra en `scripts/arena_cafe/f3_adjudicate.py` para **M/O1 solamente, en el evaluador**. No alimenta el generador E1 y por ello la salida de Modelica M sigue siendo idéntica en O0/O1. Eso ahora está **expresamente documentado**, no oculto detrás de una comparación numérica. El reporte mantiene la comparación integrada `preparation.completed` previa como `PROVISIONAL_NON_EQUIVALENT_MEASUREMENT_NO_G3_SCORE` y añade el certificado como razón analítica adicional.

D no recibe este certificado como si tuviera una preparación explícita ni se le exige simular O1 sin puerto correspondiente. Buffalo sigue con preflight offline y sin inferencia nueva EV-01; ninguna evidencia FULL del evaluador es enviada a los productores. Todos los metadatos se mantienen por brazo/condición/linaje.

## 4. Qué falta para un consumo científico legítimo de O1

El control que hoy sí puede hacerse es **una prueba condicional de incompatibilidad**. Para que M pueda construir o seleccionar una alternativa con base en O1, necesitamos antes:

1. **Un puente de medición válido y explícito** entre terminaciones físicas (evento discreto, completado pre-cutoff, posible censura) y flujo/stock molecular continuo. No declarar la identidad por el nombre del puerto ni por igualdad aproximada de números; documentar población, unidades, mecanismos de servicio y temporalidad.
2. **Una vía nativa para variar una hipótesis de forma justificada**, conservando su gramática original y declarando reglas y presupuesto de estimación/selección. No parchear parámetros del grafo para forzar nueve terminaciones.
3. **Un H_j compatible y un criterio G3 predeclarado** que trate el error instrumental/variación si procede. El certificado aquí solo prueba una condición necesaria **bajo un supuesto**, no proporciona una función de verosimilitud ni sensibilidad empírica.
4. **Experimento independiente** posterior a G4 para evaluar predicciones/abstenciones legítimas. Ni este EV-01 conocido ni la inferencia Buffalo de otros trabajos constituyen dicha reserva.

### Decisión

**No modificar la clase `IGCMolecules.BoundedQueue` ni su catálogo para que el número 9 «encaje».** Registrar en el estado de la Arena que, **con el puente uno a uno asumido**, sus candidatos fijos no pueden representar la carga observada O1. Si no puede defenderse el puente, **no** promover el resultado a una falsación científica ni a una selección por evidencia.

**Estado:** A3 `PARTIAL`; D/M generación nominal O0/O1 sin asimilación nativa extra de O1; Buffalo EV-01 live `NOT_RUN`; G4/G5 `NOT_RUN`; PM-14 `NOT_TRIGGERED_FOR_EV01`; F5 independiente `NOT_CREATED`. No rejilla, nuevo DES, otro motor M, ni proveedor autorizado.
