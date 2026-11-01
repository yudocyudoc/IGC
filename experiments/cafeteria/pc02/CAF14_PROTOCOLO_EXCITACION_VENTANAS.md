# CAF-14 — Precompromiso: excitación del campo y ventanas temporales de observabilidad

**2026-10-31 local, antes de generar código, resultados o CI.** Rama `experiment/caf14-excitation-temporal-windows-20261031` creada desde PR #125 (CAF-13, head `a3071b98fa40d587a5c94c8d0d41d54809f5ca4c`); PR #125, #124 y #123 siguen Draft y sin fusionar. No modificar código CAF-11/12/13, motor DES, D/M, Buffalo ni ATMS.

## Pregunta científica y límites

CAF-13 demostró que **los quince pares** de seis clases de cuellos únicos/dobles tienen testigos de confusibilidad existencial bajo ocho programas de observación; **ningún doble cuello entre 18 mundos** quedó en clase única. Además, los 32 mundos concretos presentaron cero colas/stocks en el minuto 40. ¿Qué ocurre si se controla separadamente **la tasa de entrada** (excitación) y **el momento de observación**, incluso dentro de un mismo pulso de trabajo, manteniendo capacidad continua exacta y observables ya conocidos?

La pregunta es sobre **identificabilidad observacional condicional** en esta pequeña familia determinista, no sobre descubrimiento causal, modelos reales, ni políticas óptimas.

## Familias y mediciones: invariantes físicos

1. **Seis estructuras** del CAF-11/12/13: cuello nominal único en preparación/despacho/entrega y cuello nominal doble en sus tres pares. Tres etapas FIFO en tándem; una capacidad continua **común** `c∈[55,110]` pedidos/hora para cada etapa con un servidor, servicio determinista de duración `d=60/c` minutos; otras etapas con dos servidores de servicio 1 min. Sin servicio estocástico ni capacidades dobles independientes.
2. Reutilizar sin cambiar el max-plus racional exacto y `Clock` de CAF-11/12, intervalos abiertos y **singleton** en cada raíz de evento. Cada programa exige **un único valor d compartido** en K0, K1 y las sondas T.
3. K0 y K1 se mantienen idénticos: entregas con tasa `6/5` y horizonte 10, y tasa `3/2` y horizonte 20. Cada experimento con tasa distinta **reinicia el mundo** con la misma capacidad/configuración. Si hay dos instantes T1/T2 con la misma tasa, pertenecen a **una sola trayectoria** (un mismo pulso), NO a réplicas independientes.
4. El pulso de llegadas `[0,20)` **no cambia**. Para leer t=10 o t=15, el DES evaluador corre solamente los eventos de llegada de `[0,t]` y produce snapshots a 0 y t, evitando su restricción de no ingresar llegadas posteriores a la última observación; la predicción simbólica puede generar las 20 min completas porque sucesos futuros no afectan el pasado. Para lecturas t≥20, el DES mantiene las llegadas de todo el pulso. Invariantes de conservación y orden `COMPLETE_THEN_ACCEPT_THEN_START_DOWNSTREAM_FIRST`.
5. Observables de T: **seis enteros** (waiting y stage_stock por preparación, despacho y entrega), exclusivamente las primeras tres etapas. No se expone al inversor la existencia de una cuarta. K0/K1 siguen siendo solo entregas. **No añadir timestamps ni sensores mágicos.**
6. Banda de error de comparación **±1 unidad por canal**. Es tolerancia de laboratorio NO calibrada como ruido; la regla de confundibilidad de dos firmas es `|x_j-z_j|≤2` para TODOS los canales. No hay priors, costos reales ni probabilidad de estado.

## Dieciocho programas FIJOS y factoriales

**Factorial completo 3 intensidades × 5 instantes** (15 combinaciones) más BASE y dos programas con dos ventanas temporales, fijado antes de resultados:

- Tasas por minuto `3/2` (90/h), `9/5` (108/h), `5/2` (150/h, **superior incluso al techo de c=110/h**).
- Instantes `t∈{10,15,20,25,40}` min. Las lecturas t<20 ocurren DURANTE el pulso; t=20 justo al terminar; t=25 es drenaje temprano; t=40 drenaje posterior.
- Identificadores `F_R15_T10`, `F_R15_T15`, `F_R15_T20`, `F_R15_T25`, `F_R15_T40`; análogos `F_R18_...` y `F_R25_...`.
- `BASE`: únicamente K0/K1.
- `W_R25_T10_T20`: en el mismo pulso de demanda `5/2`, sondas T1 a t10 y T2 a t20, **las seis variables por snapshot**.
- `W_R25_T15_T20`: idem a t15 y t20.
- No hay selección posterior de la mejor acción ni ajuste a valores obtenidos. Cada programa declara 2 (BASE), 8 (una sonda de 6 canales), o 14 (dos sondas) componentes de conteos.
- No comparar los costos como si fueran costos de CAF-07B. Es una **intervención de laboratorio sobre el campo** (tasa de llegada), no un incremento real garantizado de capacidad ni una operación comercial permitida.

## Dos preguntas separadas y exactas

**A. Confusibilidad GLOBAL entre familias**. Para cada familia M y programa P, enumerar exhaustivamente las firmas enteras observables en todos los valores `d∈[6/11,12/11]` por raíces racionales (y singleton). Para cada par de familias distintas, buscar `d_M, d_N` **potencialmente diferentes** tal que exista una lectura común ±1 en todos los canales. Guardar testigos de **dos capacidades** y las dos firmas. `CONFUSABLE_EXISTENTIAL` NO significa confundibles en todo el espacio; `ROBUSTLY_SEPARABLE_GLOBAL` significa ningún par de capacidades compatible bajo este P.

**B. Identificabilidad de ESTADOS evaluados**. Para los 32 mundos congelados de CAF-12/13, calcular cuántas clases son compatibles después de cada programa, cuántas quedan únicas con lectura exacta dentro de tolerancia ±1 y cuántas son **robustamente únicas** incluso si la lectura real varía adversarialmente hasta ±1 en cada canal. Las pruebas de robustez exigen que cualquier otra firma posible diste más de 2 en por lo menos un canal. No confundir unicidad con cobertura o verdad fuera de catálogo.

## Evaluadores y denominadores precongelados

Reusar **exactamente los 32 mundos CAF-12/13**, sin agregar casos a posteriori: 27 in-family (9 singles y 18 doubles) y 5 de cuarta etapa out-of-family. Todos sintéticos con la misma física; **NO holdout independiente**.

Total **18 programas × 32 mundos × 6 familias = 3456 evaluaciones de compatibilidad**, 18×15 = **270 pares globales**. Guardar catálogo de **108 conjuntos de firmas** y grafo de 270 pares ANTES de consultar el DES de los mundos. Pre-plan de evaluador con denominadores, parámetros y canales fijos. Guardar `head SHA` distinto de `checkout SHA`, archivos y manifest SHA256.

## Métricas, falsadores y controles

1. **Paridad física:** fórmula racional exacta del inicio/término de servicio contra CAF-01 DES para t=10,15,20,25,40, tasas de pulso 1.5/1.8/2.5, seis estructuras y capacidades enteras, fraccionarias y fronteras de eventos. A t<20 recortar llegadas para la llamada de DES y demostrar que es la **misma trayectoria física hasta t**.
2. **BASE igual CAF-13**, y **F_R15_T20** coincide con `FULL20_15` de CAF-13 (mismas seis variables y K0/K1). **F_R18_T20** coincide en entradas/calendario con los canales de `Q20_18`, pero agrega stocks: compararlos solo por subconjunto de canales; no afirmar equivalencia.
3. La función de calendario representa todos los **puntos de corte** del dominio, y cada firma tiene testigo con `Fraction`; comparación de parejas de firmas **sin forzar igual capacidad**.
4. El parámetro real del mundo in-family debe estar contenido en la familia verdadera y su clase debe sobrevivir para **cada programa**, porque generador, sensor y familia coinciden y tolerancia incluye error cero. Falla es **bug/gate rojo**, no descubrimiento.
5. Un programa que observa antes de t20 nunca puede depender físicamente de llegadas posteriores a t; prueba explícita de prefijo.
6. Reportar por programa **número de las quince parejas confundibles**, y particularmente las **tres parejas double-vs-double** y **nueve single-vs-double**, sin agregarlas como una única tasa. Reportar además cuántos singles/doubles del evaluador son únicos y robustamente únicos, y cuántos out-of-family dan **falsa clase única** versus incompatibilidad.
7. Reportar relación por régimen `rate_per_hour / c_true` y recuento de colas no nulas en los 32 mundos: el valor de una sonda puede desaparecer al drenar. **No concluir causalidad ni monotonía general sin controlar el resto de factores.**
8. Ningún umbral forzado de mejora entra a CI; CI valida física, consistencia y evidencia, **no** número de diagnósticos únicos ni que desaparezcan aristas globales.
9. Auditar posibles resultados adversos: **falsa certeza fuera de catálogo**, cero capacidad de distinguir doubles, sensores demasiado ricos sin costos calibrados, régimen de sobrecarga físicamente inviable sostenidamente.

**Gate permanente** `BLOCKED_SAME_DES_PHYSICS_UNCALIBRATED_TOLERANCE_NO_EXTERNAL_VALIDATION`. Permanecer Draft, sin merges ni despliegue. Esta prueba no reemplaza evaluación con llegadas/servicio estocásticos o un generador físico independiente. No usar probabilidades y no extrapolar tasas de acierto a empresas reales.
