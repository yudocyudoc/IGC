# CAF-13 — Precompromiso: distinguibilidad estructural en la familia paramétrica DES

**Fecha local:** 2026-10-31. **Primer commit de CAF-13 antes de código/CI.** Rama `experiment/caf13-structural-distinguishability-20261031`, basada en PR Draft #124 (CAF-12, head `b72255f9bb52b2fa5798c87a7ca4b98abaeb1cde`). PR #123 y #124 permanecen Draft. No modificar módulos anteriores, motor DES, D/M/Buffalo ni ATMS.

## Pregunta científica

CAF-12 retuvo 27/27 clases y capacidades verdaderas, pero no distinguió **ninguno de 18 dobles** como una clase única mediante un K2; distintos sensores redujeron clases y a veces dieron falsos únicos en controles con cuarta etapa. Preguntamos:

**¿Cuáles pares de familias estructurales son robustamente distinguibles con un conjunto FIJO de observaciones, una capacidad continua por familia y error independiente de ±1 pedido por canal? ¿Qué cambia al modificar granularidad del sensor, horizonte y tasa de llegadas?**

Aquí *distinguibilidad* es propiedad del **programa de mediciones completo y del catálogo de familias**, no de la verdad de los 32 mundos. No confundir pares robustamente separables con identificar automáticamente todas las instancias; tampoco confundir un test en un DES determinista con diagnosabilidad de cafeterías reales.

## Familia y parámetros congelados

- Seis clases: tres cuellos únicos y tres dobles (pares de etapas), todas con **una capacidad común `c∈[55,110]` pedidos/h** en etapas limitadas. Las otras etapas: 2 servidores, 1 minuto por pedido. Tándem FIFO y tiempos de servicio homogéneos deterministas. `d=60/c` en rango racional cerrado `[6/11,12/11]`.
- Reusar SIN CAMBIOS `CAF-11 Clock`, `CAF-12 build_parametric_calendar`, `predict_channels`, `exact_atomic_regimes`, `merge_compatible`. Las salidas enteras solo cambian en cortes racionales de eventos; evaluar todos los intervalos abiertos y cada singleton de corte.
- K0 entregas acumuladas con demanda 6/5/min t=10, K1 entregas acumuladas con demanda 3/2/min t=20, **reinicios independientes del mismo proceso y capacidad**. K2 es una medición experimental adicional de un nuevo reinicio (o del mismo snapshot que K1 cuando coincide tasa/horizonte). La demanda ocurre solo en pulso de minutos `[0,20)`, como en CAF-01, y los horizontes extra pueden observar drenaje hasta t=40.
- Error de compatibilidad ±1 **formal NO calibrado** por canal de conteo. No asignar probabilidades, pesos, distribuciones, costos monetarios ni tiempos de inspección real.

## Ocho programas FIJOS, no selector ni ranking de costos

Cada programa contiene K0 y K1 más una sonda nominal T (excepto BASE). Los nuevos operadores combinados de stock/colas **son sondas EXPLORATORIAS** de observabilidad, no acciones autorizadas del menú CAF-07B; no atribuirles costo ordinal o recomendación de despliegue.

| ID programa | Sonda T (rate/min, instante, canales) | Propósito |
|---|---|---|
| BASE | ninguna | referencia CAF-11 |
| Q20_15 | 3/2, t20, waiting tres etapas | reproducción ALL_QUEUES de CAF-12 |
| STOCK20_15 | 3/2, t20, stage_stock tres etapas | colas vs inventarios físicos |
| FULL20_15 | 3/2, t20, waiting + stage_stock tres etapas | contraste de canal en mismo snapshot |
| Q40_15 | 3/2, t40, waiting tres etapas | efecto de horizonte de drenaje |
| FULL40_15 | 3/2, t40, waiting + stage_stock tres etapas | efecto de horizonte + canal |
| Q20_18 | 9/5, t20, waiting tres etapas | mayor presión de campo |
| FULL40_18 | 9/5, t40, waiting + stage_stock tres etapas | presión, horizonte y sensor conjuntamente |

**No atribuir el efecto combinado de FULL40_18 solo a un mecanismo; cambia simultáneamente tasa, horizonte y canales**. Añadir observaciones no equivale a intervención que modifique físicamente recursos. Aunque no haya costos, mantener identidad de programas y reportar número de canales.

## Definición matemática exacta de la auditoría estructural

Para cada estructura `M` y programa fijo `P`, definir su conjunto de firmas de observación enteras

`S(M,P)={ (K0(d), K1(d), T(d)): d∈[6/11,12/11] }`.

**La misma d debe gobernar TODAS las mediciones de la firma.** Se obtiene exactamente por la enumeración de todas las regiones atómicas racionales de CAF-12, no por sampling ni interpolación. Las firmas pueden repetirse a lo largo de intervalos; conservar testigo con parámetro racional de un singleton o punto interior de la región atómica.

Para dos estructuras `M,N`, con capacidades **posiblemente distintas** d_M y d_N, existe una lectura entera compatible con ambas bajo ±1 por canal SI Y SOLO SI hay firmas `x∈S(M,P)`, `z∈S(N,P)` tales que

`|x_j-z_j|≤2` para **cada componente**. Esto implica intersección de cajas de observación ±1; como x,z son enteros, existe lectura común entera. Guardar testigos de **ambas capacidades** y salidas x,z cuando un par sea confundible.

Definir:
- `CONFUSABLE_EXISTENTIAL`: existe al menos una pareja de capacidades/firmas con coincidencia de cajas; es una **arista**, no relación transitiva de equivalencia, y **no** prueba que el par sea inidentificable para todos los parámetros.
- `ROBUSTLY_SEPARABLE_GLOBAL`: NO existe tal pareja para ninguna capacidad de ambas estructuras; bajo supuestos y cotas indicadas la lectura común es imposible.
- `robustly_singleton_true_state`: para el **vector real** exacto del evaluador y todas las hipótesis alternativas con cualquier capacidad, ninguna salida alternativa difiere ≤2 por canal; esto es una garantía de separación para TODAS las realizaciones de ruido ±1 alrededor de la salida verdadera, más fuerte que una etiqueta única obtenida con la lectura exacta. Distinguir de `singleton_at_exact_reading` (filtrar con error ±1 a la observación exacta).
- Grafo de confusibilidad de familias con 6 vértices / 15 aristas potenciales; reportar siempre separaciones por pareja de clases y también 3 dobles vs 3 únicas y dobles vs dobles.
- La existencia de firmas coincidentes bajo ±1 a diferentes capacidades **no demuestra dinámica idéntica** ni imposibilidad absoluta bajo otros experimentos, horizontes o sensores.

## Mundos y controles FROZEN antes de análisis

Reusar exactamente 32 mundos ya definidos por CAF-12 (**27 nominalmente in-family; cinco controles de cuarta etapa fuera de catálogo**). No añadir ni elegir nuevos mundos usando resultados. Ninguno es independiente físicamente; 20 ya estaban expuestos en CAF-11, 12 adicionales sintéticos en CAF-12.

**8 programas × 32 mundos × 6 familias = 1536 filtrados de región** y 8×15 comparaciones de familias. Guardar JSON de 48 conjuntos completos de firmas con testigos paramétricos antes de **cualquier evaluación DES nueva**; plan con SHA256 y dos SHAs distintos de head y checkout. No volver a calcular ni modificar programas a posteriori.

## Gates y métricas

1. Paridad de firma BASE con CAF-11 y Q20_15 con CAF-12; paridad de TODOS los nuevos operadores/tasas/horizontes con CAF-01 DES nativo (también capacidades racionales intermedias, puntos de evento, frontera t40).
2. Para cada familia, toda firma generada por intervalos abiertos y singletons debe corresponder a un `d` racional dentro del dominio y a lecturas del calendario del propio modelo; todas las firmas son enteras no negativas; cada valor real de d cae en exactamente una región atómica (partición).
3. La lógica de par-confundible debe pasar tests sintéticos: escalares 0 y 2 con ±1 COMPARTEN lectura; 0 y 3 NO; grafos con 0,2,4 confusibles adyacentes pero 0/4 no, sin partición transitoria; dos vectores que discrepen en un canal >2 no comparten lectura.
4. Si en cualquiera de los 27 mundos in-family no se retiene el **parámetro real dentro de su familia verdadera** con TODAS las observaciones del programa, gate ROJO. No imponer éxito de identificación.
5. Separar `singleton_at_exact_reading` y `robustly_singleton_true_state`; informar si ambos se dan o divergen.
6. Reportar por programa 15 aristas potenciales/robustas, cuáles de los dobles permanecen confundibles con un único, número de casos in-family resueltos, cardinalidad de clases y falso único para cinco controles externos. No promediar 27 y 5 como población.
7. No afirmar probabilidad ni prevalencia; ni «identificabilidad estructural universal» más allá de estos programas finitos, esta familia y el modelo de error.
8. **GATE PERMANENTE:** `BLOCKED_SAME_DES_PHYSICS_UNCALIBRATED_TOLERANCE_NO_EXTERNAL_VALIDATION`. PR Draft sin merge. Los hallazgos adversos no autorizan reajustar métodos, mundos o criterio después de ver resultados.

**Objetivo científico:** separar nítidamente (a) no separabilidad existencial de dos familias, (b) distinción robusta en un estado verdadero dado, (c) identificación con una lectura exacta y (d) exclusión errónea/falsa certidumbre por catálogo estructural incompleto. No es una búsqueda de un «sensor ganador».
