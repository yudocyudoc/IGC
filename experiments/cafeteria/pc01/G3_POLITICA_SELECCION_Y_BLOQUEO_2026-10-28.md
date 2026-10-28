# ARENA · CAF-01 / PC-01 · G3-01 — Regla ejecutable de selección y bloqueo previo a evaluación

**Fecha:** 2026-10-28 · **Estado:** implementación preparatoria para dictamen de Astra. NO modifica ni congela v0.3, NO autoriza PC-02, DES, RK4, OpenModelica ni llamadas a Buffalo. Se implementa como `caf01_g3.py` con pruebas adversariales.

## 1. Universo y presupuesto — decisión previa a datos

El contrato PC-01 v0.3 contiene **18 ajustes D** por RK4 en construcción: 3 topologías sin pérdidas × capacidades 48/72/96 × tiempos 0.125/0.25 h, y otras 18 integraciones exclusivamente en CAF-N. El G3 exige rendir cuentas por los 18 puntos, incluyendo bloqueos, sin transformarlos en 18 simulaciones OpenModelica. De los resultados de construcción se propone **un representante por topología** para las siguientes comprobaciones nativas: D máximo 3 OM de construcción y 3 de evaluación, condicionadas a G2 y autorización.

En M, el certificado E1 del PR #72 (integrado) reduce las nueve etiquetas nominales a **seis clases de comportamiento como cota superior**, manteniendo separadas C00/C01/C02: por cada estructura `20` y `[72,100]`. El representante de la segunda clase es 72 por regla anterior al holdout. La equivalencia depende de la ecuación original de BoundedQueue, estados iniciales vacíos, conservación sin pérdidas, pulsos con totales 24/30 y tiempos 0.5 h; **no puede reinterpretarse como equivalencia entre topologías o evidencia de que todas las seis clases son distintas**. El G3 no acepta una fila adicional para 100.

B puede presentar una sola propuesta propia de CAF-01, o un bloqueo auditable del adaptador/proveedor. No se sustituye por D ni M. El visor 2 stocks/2 flows puede bloquear la medición sin invalidar por sí solo el modelo Buffalo.

| Cuenta | Máximo propuesto, condicionado | Máximo v0.3 vigente |
|---|---:|---:|
| OpenModelica D por mundo | 3 | 3 |
| OpenModelica M por mundo | 6 | 9 |
| OpenModelica B por mundo | 1 | 1 |
| OpenModelica total ambos mundos | **20** | **26** |
| Integraciones RK4 D CAF-01 + CAF-N | 18 + 18 | 36 |
| Corridas DES construcción + evaluación | 1 + 1 | 2 |
| Inferencias Buffalo CAF-01 + CAF-N | 1 + 1 | 2 |

**Los 20 no son presupuesto gastado ni autorización:** son un techo futuro **condicional** de deduplicación de M. Hasta comprobar dinámicamente las hipótesis de conservación y aprobar la deduplicación, el techo escrito de v0.3 sigue siendo 26. Si falla la condición de equivalencia, bloquear G3 y revisar el contrato; no reasignar gastos automáticamente ni elegir por resultados del mundo.

## 2. Evidencia de construcción y puertas

La entrada a `select()` contiene exactamente la construcción pública, su hash y 25 filas de inventario: 18 D, 6 M y 1 B. La máscara CAF-01 exige `t_min=0,5,10,15,20,30,40`; CAF-N exige **solo 0 y 40**. El pulso prescrito de construcción sigue siendo 1.2 pedidos/min durante 20 min. **No hay un campo admitido para entregas reales de evaluación.** El hash de evidencia acompaña a cada propuesta para impedir reutilización accidental entre muestras, aunque el G3 no es en sí mismo un custodio externo.

Cada fila debe declarar G0/G1/G2 como PASS, BLOCKED, PENDING o FAIL. **Excepción expresamente acotada a D:** los 18 puntos de cribado RK4 pueden declarar G0=G1=PASS y G2=RK4_SCREEN, adjuntar un recibo RK4 y una curva de construcción, **sin fingir 18 ejecuciones OpenModelica**. En B y M esa etiqueta es inválida. Para participar como candidato verificado nativamente se exigen los tres PASS, hash de fuente nativa, hash de recibo G2 y residual máximo del balance material nativo ≤ **0.008 pedidos**. Para el cribado RK4 de D, el residual adjunto pertenece al integrador Python; no se presenta como residuo de una traza nativa. **En la fase de G2 del representante D** se exige adicionalmente paridad `RK4↔OpenModelica` con error absoluto máximo ≤ **0.012 pedidos**, heredado del comparador `arena_d_v1_screen.compare_omc_csv`; no es un margen de error instrumental. Esta tolerancia numérica está tomada como criterio de ingeniería conservador próximo al verificador histórico D; **no es un error de sensor, intervalo de confianza ni demostración física automática**. Si falta verificación de stock material, queda pendiente. G3 **no abre** ni valida por sí mismo los recibos: el custodio/runner futuro debe autenticar que corresponden a la misma entrada y modelos. Un SHA autodeclarado no acredita G2; el resultado lo advierte expresamente.

Una fila no lista para decisión debe tener resultados nulos y motivo del bloqueo. No se eliminan silenciosamente candidatos: ausencia, duplicación o incorporación de configuraciones ajenas al inventario impiden seleccionar. El numerador de búsqueda y el denominador de fallos quedan trazables. El algoritmo no vuelve a ejecutar RK4 ni solvers.

## 3. Selección, bandas y abstención

Se calcula **MAE de entregas acumuladas en construcción excluyendo t=0**. El RMSE se conserva como diagnóstico pero **no** rompe empates del MAE. Se mantienen tres conceptos diferentes:

- **Igualdad numérica de curvas:** máximo `1e-6 pedidos` por punto (tol. de comparación computacional, no error instrumental).
- **Banda de alternativa competitiva:** hasta **0.25 pedidos MAE** sobre el mínimo, un margen **decisional predeclarado** para evitar declarar identificación por mejoras insignificantes. No equivale a compatibilidad estadística y no se interpreta como cota de sensor o ruido.
- **Balance físico:** residual nativo máximo **0.008 pedidos** bajo verificación independiente posterior.

D realiza primero el cribado de **18 RK4** y selecciona determinísticamente **un representante por estructura** por menor MAE; si hay igualdad, desempata con el identificador canónico lexicográfico **únicamente para decidir qué candidato podría simularse**, no para afirmar que los otros parámetros fueron identificados o descartados. Guarda todos los parámetros dentro de la banda por estructura. Compara a continuación los mejores de cada estructura y conserva todos los que estén dentro de la banda del campeón global. M procede de igual modo, pero cada clase certificada de capacidad ocupa un único lugar, sin doble voto de 72/100. B, sin repertorio enumerado comparable, se acepta condicionalmente si superó G0–G2; un bloqueo del visor nativo debe ser reportado separadamente. **No se promedian candidatos ni se asignan probabilidades implícitas por cantidad de variantes.**

Los representantes D elegidos en ese primer paso permanecen con G2 nativo pendiente; al preparar el lock se exige un recibo G2, un balance material dentro de 0.008 y una paridad RK4/OM dentro de 0.012 para cada ganador previamente elegido que solo contaba con cribado RK4. Se prohíbe sustituirlo por otra configuración si no supera el solver. Este segundo paso no modifica los rankings ni permite reabrir la banda. En CAF-N no se requiere otro G2: su presupuesto OpenModelica adicional es cero y la abstención sobre la trayectoria interna es obligatoria.

Si ninguna propuesta supera las puertas, `NO_VALID_CANDIDATE`. Si existe más de una estructura competitiva, o varias parametrizaciones no equivalentes dentro de la banda de la estructura ganadora, `STRUCTURE_OR_PARAMETER_NOT_IDENTIFIABLE`: se conservan alternativas sin declarar identidad. El pronóstico puntual se abstiene si falta un representante, quedan parámetros alternativos no resueltos o las estructuras seleccionadas pronostican curvas distintas. Si varias estructuras mantienen una **única curva futura numéricamente igual**, se puede publicar esa curva común, pero con la etiqueta `SHARED_FORECAST_MULTIPLE_STRUCTURES_NOT_IDENTIFIED` y sin declaración de mecanismo único.

La comparación con REF-CAF y REF-SCALE pertenece a G4 y debe bloquearse por separado antes del holdout. El umbral descriptivo propuesto de ventaja de ≥1 pedido MAE frente a REF-CAF se aplica **después** y no participa en esta selección. No elegir al ganador usando el escenario de 1.5 pedidos/min.

## 4. CAF-N, aislamiento y bloqueo

Para CAF-N se toman **solo los dos extremos de la construcción** y se preparan los 18 ajustes RK4 propios de su máscara. El G3 rechaza un arreglo de siete observaciones y requiere un manifiesto de 25 filas generado bajo la evidencia enmascarada; nunca puede puntuar con las lecturas intermedias del CAF-01 original. M puede reutilizar las curvas nativas preexistentes como computación, pero debe producir *scores* únicamente de la máscara, sin utilizar rangos del ensayo completo. La segunda consulta Buffalo debe tener contexto independiente y no comparte respuesta histórica, sujeto a autorización separada.

En CAF-N, independientemente del resultado de ranking, **se declara no identificable** la trayectoria interna, hora del pico de pendientes y tiempos individuales de espera. Un pronóstico matemático condicional puede conservarse en el manifiesto, pero `lock_forecasts()` se abstiene de publicarlo como una trayectoria inferida.

`lock_forecasts()` recibe exclusivamente las series de evaluación **de los representantes ya seleccionados con construcción**, un hash verificable del reporte previo y el pulso público futuro (1.5/min, 20 min). No admite ni utiliza observaciones reales futuras. Produce un hash de contenido, las curvas por candidato, rango por tiempo y estados de abstención. **Este hash no es sellado suficiente:** requiere publicación/recepción inmutable por custodio externo con marca temporal anterior a revelar evaluación, más cierre de G4, y autorización experimental separada. No activar la lectura del DES de evaluación con la mera presencia del hash.

## 5. Uso técnico, pruebas y fronteras

`plan(contract)` prepara el inventario, equivalencias y límites sin datos. `select(contract,evidence,rows)` inspecciona únicamente construcción. `lock_forecasts(contract,selection,submission)` genera el contenido de compromiso, no publica un sello externo.

Pruebas adversariales: manifiestos incompletos, duplicados, capacidad 100 duplicada, cambios del contrato, recibos G2 inexistentes, balance excesivo, contaminación entre casos, acceso a futuros, enmascaramiento CAF-N, empates estructurales, parámetros ambiguos, pronósticos compartidos, pronósticos divergentes, manipulación del reporte de selección, cotas físicas y ausencia de candidatos. Son pruebas con números inventados; **cero simulaciones e inferencias experimentales**.

**Condiciones para considerar G3 formalmente cerrado:** dictamen puntual de Astra sobre bandas, bloqueos y conmutación M 72/100; recepción independiente de hashes y trazas G2 cuando existan; definición del custodio inmutable de pronósticos; coordinación con G4 antes de abrir una sola evaluación. Hasta entonces: `G3_IMPLEMENTED_PROPOSED_NOT_FROZEN`.
