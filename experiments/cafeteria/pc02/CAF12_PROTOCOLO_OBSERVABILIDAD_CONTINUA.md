# CAF-12 — Precompromiso: observabilidad estructural con capacidades continuas

**Fecha local:** 2026-10-31. **Estado:** primer commit nuevo de rama CAF-12 antes de implementar o ejecutar la evaluación. **Base:** PR #123, CAF-11, `3d0a2447b5deffe1a5c3be64d2667731f0f4e56d`, Draft no fusionado. CAF-12 no modifica código de CAF-11 ni ningún DES/CAF-07B previo.

## Pregunta y falsadores

CAF-11 demostró cobertura paramétrica **18/18** dentro de la misma familia física, pero mantuvo las **seis clases estructurales** tras observar solamente entregas K0/K1, mientras dos controles de cuarta etapa también resultaron compatibles con familias de tres etapas. **¿Cambian el conjunto de estructuras compatibles y las regiones continuas de capacidad al añadir observaciones de colas y stocks de etapa en lugar de nuevas políticas de selección?**

Se examinan todos los esquemas de observación PREDECLARADOS; **no se ajustan acciones a resultados ni se declara un mejor selector**. El objetivo no es maximizar aciertos, sino medir *qué es observable* bajo sensores y supuestos explícitos. Un caso de seis clases supervivientes o un falso conocido fuera de familia es resultado válido, no fracaso de CI.

## Física y dominio invariantes

- Misma familia restringida de CAF-11: tres etapas en serie FIFO; por estructura, etapas limitadas tienen `1` servidor y tiempo determinista de servicio `d=60/c` min, otras tienen `2` servidores y servicio fijo 1 min; **una capacidad común** `c∈[55,110]` pedidos/h para todas las etapas limitadas. Seis familias: 3 cuellos únicos nominales y 3 pares nominales; no independencia de capacidades por etapa.
- Reusar sin alterar `caf11_parametric_des_inversion.Clock`, `clean_knots`, cotas y conversión racional; ampliar *en módulo nuevo* la recurrencia simbólica del calendario para almacenar tanto **inicio de servicio** como **terminación** por pedido/etapa. Comparar contra snapshots del motor DES nativo CAF-01, en particular en empates.
- Para una etapa s, en tiempo t: `arrived_s(t) = arrivals(t)` si s=0 o `completed_(s-1)(t)` si s>0; `waiting_s(t)=arrived_s(t)-started_s(t)`; `stock_s(t)=arrived_s(t)-completed_s(t)`; `delivered(t)=completed_last(t)`. Todos los conteos incluyen eventos en `t≤observación` conforme a la política DES (terminaciones→aceptaciones→comienzos). No introducir nuevas clases de sensor.
- Las mismas tasas, horizonte, presupuesto ordinal y bandas ±1 de CAF-07B/11. **±1 es tolerancia artificial no calibrada**; costes 1–8 son ilustrativos, no dinero ni duración real. Los experimentos de K0/K1/K2 son reinicios independientes con la misma configuración y capacidad; no continuidad temporal de una sola operación.
- **Identificabilidad que se evalúa: solamente clases nominales dentro de esta familia de tres etapas bajo una medición extra K2; no inferencia causal o validez externa.**

## Ocho esquemas FIJOS, sin selector adaptativo

Todos reciben **K0** (entregas t=10, tasa 6/5) y **K1** (entregas t=20, tasa 3/2); K1 tiene costo 1.

| Esquema | K2 de CAF-07B, o ninguna | Costo total ordinal |
|---|---|---:|
| BASE | ninguna | 1 |
| PREP_Q | `prep_queue_15_t20`, waiting preparación | 3 |
| DISPATCH_Q | `dispatch_queue_15_t20`, waiting despacho | 3 |
| DELIVERY_Q | `delivery_queue_15_t20`, waiting entrega | 3 |
| DISPATCH_STOCK | `dispatch_stock_15_t20`, stock despacho (en servicio + esperando) | 3 |
| PREP_DISPATCH_Q | `prep_dispatch_15_t20`, waiting preparación + despacho | 5 |
| ALL_QUEUES | `all_queues_15_t20`, tres waiting | 7 |
| STRESS_PREP_DISPATCH | `prep_dispatch_18_t20`, mismas dos waiting pero tasa 9/5 | 8 |

`all_queues_18_t20` cuesta 9 más K1 y no cabe. **La comparación entre esquemas no es un ranking de calidad**, porque cambia simultáneamente sensor, costo y, en STRESS, la tasa de campo. Todos los esquemas están al alcance de un presupuesto ≤8, sin elegir acciones según verdad. Compartir tasa/horizonte entre K1 y algunas sondas K2 no crea una réplica estocástica independiente.

## Mundo de evaluación congelado

**20 mundos históricos de CAF-11 (ya conocidos):** 9 únicos (cap 68/83/97, tres etapas), 9 dobles (cap 69/83/97, tres pares), 2 topologías con cuarta etapa (cap 64/86).

**12 escenarios adicionales sintéticos:** 9 dobles a capacidades `(61,79,107)` × pares `((0,1),(0,2),(1,2))`, y 3 topologías de cuarta etapa a capacidades `(62,78,106)`. No presentarlos como independientes de la física CAF-01. Los 3 nuevos valores dobles no fueron los 8 valores dobles de CAF-10, pero no se infiere holdout externo.

Total **32 mundos × 8 esquemas × 6 familias = 1536 inversiones conjuntas**. De los 32 mundos, **27 son representados en el catálogo estructural (9 únicos + 18 dobles)**; **5 cuarta etapa** con cobertura `N/A` (nunca contar 0 como si su clase existiera).

**Evaluador:** ve verdad solo para generar observaciones físicas DES y verificar cobertura; la inversión recibe *únicamente las lecturas*, las familias, y la tolerancia fija. Mantener el mismo parámetro c en K0/K1/K2 para una hipótesis. No filtrar c por partes usando distintas capacidades independientes por canal.

## Inversión exacta y controles

El mapa de eventos inicio/fin es una función continua racional por tramos del tiempo de servicio `d`, construida por `max` y sumas. Calcular todas las raíces de cada clock de llegada a etapa, inicio y finalización relevantes con los horizontes K0/K1/K2, incluyendo las discontinuidades de conteos en instantes exactos; evaluar tanto intervalos abiertos entre cortes como singletons de cada corte. Todas las regiones devueltas tienen extremos racionales exactos e inclusión correcta. **No reemplazar por una rejilla ni por interpolación.**

- Test de paridad de conteos por cada canal (`waiting`, `stage_stock`, `delivered`) entre expresión simbólica y DES nativo, en las seis estructuras, varias capacidades enteras y fraccionarias y en puntos de empate.
- Test de conservación por etapa, de K0/K1 común y presupuesto; reproducir exactamente BASE de CAF-11 para los mismos 20 mundos. Test de positividad de intervalos y cobertura del dominio sin huecos entre regiones atómicas.
- **Gate rojo de ingeniería** si un mundo in-family pierde su capacidad o clase verdadera con cualquiera de los ocho esquemas y las observaciones exactas (dentro de ±1) bajo el mismo DES. Test de falsificación de esta propiedad. Reportar cobertura estructural y paramétrica **por esquema, nunca solo agregada**.
- Comparar por esquema: `n` clases supervivientes, cuántos mundos in-family quedan con clase única, cuántos abstienen con 2–6 clases, falsos conocidos en 5 de cuarta etapa (cualquier clase única errónea), cuántos conservan todas las seis clases y cuántos vacían totalmente la familia; anchura y número de componentes paramétricas, además de costo ordinal.
- **No imponer en CI una métrica de mejora** (por ejemplo, más diagnósticos), solo invariantes y conteos; cero falsos positivos por abstención universal no es un éxito. Con bandas ±1 no calibradas, ninguna tasa es extrapolable a cafeterías reales.

### Riesgos, exclusiones y límites

- Las colas por etapa pueden volverse altamente discriminantes **por construcción** si tiempos de servicio son constantes; no se interpreta como garantía bajo aleatoriedad o precisión instrumental real.
- Un resultado estructural único dentro del catálogo aún puede ser falso ante cuarta etapa o recursos compartidos.
- Un resultado nulo con K2 no implica indistinguibilidad para árboles adaptativos, múltiples mediciones, horizonte más largo o timestamps.
- No usar sensores ajenos a CAF-07B, fuga de stage count, verdad, ni log interno del simulador para selección; tampoco modificar CAF-11 o CAF-07B.
- Sin pruebas sobre D/M/Buffalo/ATMS, sin pronunciarse sobre precios ni intervención empresarial.
- **Puerta permanente:** `BLOCKED_SAME_DES_PHYSICS_UNCALIBRATED_TOLERANCE_NO_EXTERNAL_VALIDATION`. PR Draft, sin merge, requiere revisión externa de matemáticas, simultaneidad y riesgo de sensor artificial.
