# CAF-10 — Protocolo previo a CI: adquisición PAIRWISE vs minimax, certificación en banco ampliado

**Fecha:** 2026-10-31. **Estado:** precompromiso de implementación para una prueba sintética determinista, antes de escribir el ejecutor/ejecutar sus mundos desde este PR. **Base:** rama Draft del PR #121 (CAF-09), commit `7f78a0c027b0ce780bc8e383a992623fba4614d2`; fuente original CAF-07B (#118) en `main`. No modifica ninguna de ellas.

## Hipótesis y propósito

Separar la decisión de **adquirir una medición** de la de **certificar una única clase**. Contrastar:
- `STRICT_ORIGINAL`: `caf07b_umbral_secuencial.choose_second` sin cambios.
- `PAIRWISE_FROZEN`: `caf09_policy_observability.choose_relaxed(...,"PAIRWISE_ANY")` **sin cambios** respecto a #121.
- `MINIMAX_WORST_CLASSES`: regla alternativa propuesta por GLM; **minimiza el peor número de clases de decisión supervivientes** tras una sola lectura K2 asequible, sobre todos los vectores enteros admitidos por las bandas ±1 de *alguna* hipótesis superviviente. No usa probabilidades ni el mundo real para elegir.

**No asumimos** que minimax mejore precisión diagnóstica: podría empatar o medir menos y conservar más clases. La hipótesis de Claude (adquisición flexible + certificación contra banco ampliado) se conserva separando selección de reporte de clases; no se declara probada.

## Estados y sensores invariables

- Banco **único de certificación ampliado**: `b.bank(True)` (24 hipótesis en 6 clases estructurales; cuatro capacidades discretas 60/75/90/105 pedidos/h).
- Predicciones `b.precompute(bank)` por **DES nativo** CAF-01 (sin fluido); configuración física privada solo para el evaluador. No se añade ninguna hipótesis conociendo los mundos.
- Primera observación K0 (entregadas, 1.2/min al min 10) y primera acción fija K1 (`delivered_15_t20`), candidatas K2 del catálogo CAF-07B, mismo presupuesto acumulado **8 unidades ordinales**, tolerancia **±1 pedido**, no más de **una K2**; no timestamps nuevos, no servicio estocástico.
- `b.eligible`, `b.classes`, `b.update`, `b.read_physical`, y **la función original de veredicto `b.evaluate_case`** se usan para el brazo estricto; para las otras ramas se conserva su mismo contrato y veredicto, con prueba de paridad que evite drift.
- En todas las ramas, `MODEL_GAP` si conjunto vacío; `ABSTAIN` con más de una clase; clase única **únicamente dentro de banco** (específica, no certificación física general). **Ninguna política afirma validez de mundo real.**

## Minimax: definición exacta y desempate congelados

En el estado posterior a K1, sea `H` el conjunto de hipótesis supervivientes y `A` las acciones del menú que caben en presupuesto restante, excluida K1. Para cada acción y cada `h∈H`, su predicción `p_h(a)` es un vector entero no negativo. Se enumeran **exactamente todos los vectores enteros** del rectángulo `[p-1,p+1]` por canal (recortando en cero), y se toma la unión de rectángulos de todas las `h`. Para cada vector hipotético `y` se filtra `H_y={h∈H: |y_c-p_h(a)_c|≤1, ∀c}`. Por construcción es no vacío para cada y de la unión.

`W_C(a) = max_{y} |clases(H_y)|`, `W_H(a)=max_{y}|H_y|`. Son números enteros calculados sin pesos y sin observar la verdad. Se consideran acciones con **al menos un par interclase robustamente separable** bajo diferencia >2: gate de medición compartido con PAIRWISE para no medir sondas sin separación robusta en el catálogo. Se elige minimizando lexicográficamente `(W_C, W_H, costo, action_id)`. **No se exige** que `W_C` sea menor que el número actual de clases: la acción puede aportar información según la lectura aunque su garantía de peor caso no mejore. Reportar también `W_C` antes y después, sin atribuir probabilidad a los posibles vectores.

Si `H=∅`, hay una sola clase, no hay acciones asequibles o ninguna tiene pares separables: **no K2**. Desempate independiente de mundos evaluados. No cambiar el gate después de ver resultados.

**Grafo de confusibilidad como referencia no selectora:** para cada estado post K1, contar pares de hipótesis de clases distintas cuyas predicciones difieren ≤2 pedidos en **todos los canales de cada acción individual asequible**; no es transitivo y por ello **no es una partición de equivalencia**. Esta línea base estructural no usa K2 ni sustituye las políticas; solo caracteriza el límite del menú de un paso con ±1.

## Mundos de evaluación, congelados antes de correr CAF-10

**Cohorte H — histórica/expuesta en #117 (no llamar inédita):**
- `H_SINGLE_{cap}_{ix}`, `cap = 55,...,110` inclusive (56 capacidades enteras), `ix ∈ {0,1,2}` (cuello único en preparación/despacho/entrega): **168 mundos**.
- Hay solapamiento deliberado con exploraciones previas. Es una prueba de cobertura de rejilla, **no** holdout.

**Cohorte N — nueva cuadrícula sintética de dobles (fresca respecto a los 11 mundos de #118/#121):**
- Capacidades `(57,63,69,77,83,97,103,109)` pedidos/h, con pares de etapas `((0,1),(0,2),(1,2))`: **24 mundos**. Identificador `N_DUAL_{cap}_{i}{j}`.
- Los pares de cuello doble se representan nominalmente con capacidades iguales; no se presume que las colas crezcan en ambas etapas, ni son independientes de los supuestos DES compartidos. No ajustar capacidades después.

**Cohorte S — controles fuera de taxonomía:**
- `S_EXTRA_{cap}`, `cap ∈ (64,86,108)`: **3 mundos** con cuarta etapa no visible, pero simulada físicamente. No incluir en denominador de cobertura estructural; reportar `MODEL_GAP`, abstención o falsa certificación.

**Total: 195 mundos × 3 políticas = 585 evaluaciones**; 168 históricas + **24 nuevas dobles** + 3 sentinelas nuevas. Las capacidades 55 y 90 de dobles originales #118 NO aparecen en la cohorte N. **Nuevos en este protocolo** solo significa no usados previamente como los 11 casos de CAF-09; no es dato natural independiente ni validez externa.

## Criterios antes del resultado

**Ingeniería (gates que pueden fallar):** 195 mundos exactos, 585 evaluaciones, plan persistido antes de leer los nuevos mundos, **585 decisiones guardadas antes de cada K2**, ninguna lectura de topología/capacidad del mundo en las funciones de selección, cobertura de canales, presupuesto ≤8, no desviar K0/K1, no alterar política de #118 ni `PAIRWISE_ANY` de #121. Test negativo artificial para minimax y su desempate; verificación de enumeración exhaustiva sin usar el DES. Auditoría con SHA256 de cada archivo y `checkout_sha` de merge vs `head_sha` separado. Atribuir cero ejecuciones DES antes del plan solo a **mundos de evaluación**; el banco hipotético sí se precalcula con DES.

**Métricas descriptivas, sin gate de rendimiento preseleccionado:** por cohorte y brazo: cobertura de **etiqueta de clase verdadera** entre mundos representados, tamaño de conjunto de clases final (incluida cardinalidad cero), clases eliminadas tras K2, diagnósticos únicos correctos y falsos, abstenciones, `MODEL_GAP`, costo ordinal y frecuencia de acción, casos con K2, confusibilidad por pares. Reportar denominadores exactos por estrato: H=168, N=24, S=3; además H+N=192 representados. **Mundo representado por clase no significa capacidad numérica exacta representada en banco**. Para controles S, usar cobertura `N/A` y reportar riesgos de falsa certificación por separado.

**Adjudicación:** no seleccionar ganador por (pocas) diferencias retrospectivas. Si las alternativas difieren, describir por capacidad, etapa, estrato, volumen de clases y errores. Con 195 mundos deterministas construidos por nosotros, ni diferencias con numerador grande justifican tasas poblacionales o recomendación operativa. `BLOCKED_SYNTHETIC_SAME_PHYSICS_NO_EXTERNAL_VALIDATION` **siempre**. Sin impacto sobre D/M/Buffalo, ATMS, costos empresariales, sensores o DES existentes.
