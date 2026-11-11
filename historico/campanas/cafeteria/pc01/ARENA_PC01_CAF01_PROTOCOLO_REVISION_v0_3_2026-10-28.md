# ARENA · V3.0 · PC-01 — Protocolo preparatorio de CAF-01

**Versión:** borrador PC-01/0.3, revisión técnica posterior a Astra (no autorizado) · **Corte de referencia:** `yudocyudoc/IGC@6f0ba57d175c10d31f762237287cb1e79cdaea41` · **Estado:** propuesta de diseño revisable, NO preinscripción experimental congelada. **Fecha original:** 27 de octubre de 2026 · **Revisión:** 28 de octubre de 2026 (America/Mexico_City).

**Mandato:** desarrollar solo PC-01 del plan rector `ARENA_PLAN_CAMPANA_CAFETERIA_V3_0_2026-10-27.md`: caso, fuente propuesta, evidencia, D/B/M, REF-CAF, métricas y presupuesto. **No ejecutado:** ningún generador, candidato, solver o inferencia; sin cambios en GitHub, sin flujo de ejecución ni publicación de datos de verdad.

## 1. Pregunta y prueba mínima

**CAF-01:** con observaciones de una operación inicial, ¿puede cada método anticipar entregas y pedidos pendientes ante **otra tasa de llegadas**, conservando su incertidumbre, y superar o complementar un análisis convencional con la **misma información**?

- **Unidad de análisis:** pedidos equivalentes (una clase de servicio), desde su aceptación hasta entrega. Sin mezcla de bebidas, recetas, ventas, inventario ni rentabilidad.
- **Conservación:** pedidos aceptados = entregados + pendientes + cancelados; en esta primera propuesta, *cancelación prohibida por diseño y conocida como política*, con iniciales vacías. Así `P(t)=A(t)-D(t)` es **derivado**, no una segunda medición independiente.
- **Mecanismos estructurales en comparación:** una o más etapas materiales de espera/servicio y posibles dependencias de flujo; diferencias de velocidad con el mismo grafo se reportan como variación **paramétrica**, no como estructura nueva. Las clases que realmente puedan producir D/B/M quedan limitadas por sus interfaces y se identifican antes de evaluarlas.

## 2. Dos condiciones con reinicio, no una intervención continua disfrazada

| Dimensión | Condición de construcción | Condición de evaluación |
|---|---|---|
| Unidad temporal | Minutos | Minutos |
| Ventana de llegadas | `0 ≤ t < 20 min` | `0 ≤ t < 20 min` |
| Tasa prescrita | **1.20 pedidos/min** | **1.50 pedidos/min** |
| Horizonte total | **40 min** | **40 min** |
| Tiempos de lectura | 0, 5, 10, 15, 20, 30 y 40 min | Iguales |
| Estado inicial | A=D=P=0 | A=D=P=0 (reinicio explícito) |
| Datos visibles antes del cierre de modelos | Entradas prescritas, conteos aceptados y entregas de construcción | **Solo el perfil de entrada**, ninguna respuesta observada |
| Observaciones posteriores para evaluar | No se reutilizan como evaluación independiente | A, D y P observados en los tiempos fijados, **después del sello** |

**Por qué este diseño:** el adaptador común de `scripts/arena_v0_common_evidence.py` admite actualmente **un único pulso** (`kind=\"pulse\"`, tasa, duración) y observaciones `{t, delivered}`. Por eso se proponen **dos escenarios reiniciados** con distintas tasas, en lugar de fingir que el código ya admite un flujo temporal irregular arbitrario. Esta es una **perturbación de entrada**; no prueba el efecto de contratar personal o comprar equipo.

**Precisión de calendario DES (preliminar, no secreto del generador):** la llegada programada número `j≥0` se propone en `t_j=(j+1/2)/λ`, con λ en pedidos/min y `t_j<20 min` (pulso semiabierto). Esto produce exactamente **24** llegadas para 1.20/min y **30** para 1.50/min; ninguna llega exactamente a t=0 o t=20. El orden de desempate entre salida y llegada simultáneas sigue **pendiente de fijar** junto con la especificación privada del mundo, antes de crear observaciones. Las realizaciones son enteras y `A_real(t)` puede diferir hasta una unidad de `A_diseño(t)=λ·min(t,20)`; es una discrepancia de agregación **conocida**, no un error instrumental ni evidencia de un mecanismo omitido. Si se supera la discrepancia declarada, bloquear el caso.

**Comparabilidad de pérdidas:** en la fuente evaluadora la cancelación es cero por política. Si un candidato propone una pérdida, debe pronosticarla como salida material explícita: para ese candidato el balance es `A = D + P + L`; no se le permitirá calcular `P=A-D` mientras su propio `L` sea positivo. La diferencia con la política conocida contará en la evaluación de fidelidad.

**Salida de construcción:** `{t_min, accepted_cum_orders, delivered_cum_orders, pending_orders}` y un adaptador **sin pérdida de procedencia** que convierta `t_min` y `delivered_cum_orders` en el contrato heredado. **Paridad de información:** el núcleo común de predicción para D/B/M, REF-CAF y REF-SCALE será **pulso prescrito + D(t)**. Los conteos reales A(t) y P(t) se conservan en sidecar visible para todos como auditoría y contraste de discretización, **no** se proporcionan exclusivamente al estimador de REF-CAF como información de calibración. Toda diferencia de datos efectivamente consumidos por un brazo se reportará; disponibilidad de un sidecar no implica que el adaptador histórico pueda utilizarlo.

## 3. Fuente evaluadora independiente propuesta (aún no implementada)

Se propone un **simulador de eventos discretos** separado de E1, del compositor, de las plantillas y de cualquier candidato producido por los brazos. Una agenda de eventos controla aceptación, inicio/fin de servicio y entrega; el número de etapas y las reglas de servicio concretas serán **verdad reservada**, fijadas en un protocolo privado antes de publicar construcción y sin ajustarlas según qué brazo funcione mejor. El informe público declarará al menos: implementación/versiones, leyes usadas, restricciones, eventuales reglas de redondeo, agregación, condiciones iniciales, configuración de pérdidas y supuestos conceptuales compartidos.

**Propuesta inicial:** realización determinista (sin aleatoriedad), llegadas uniformemente espaciadas con desplazamiento de medio intervalo conforme al perfil, y contador completo de aceptados/entregados/pendientes. Esto permite un primer ensayo sin introducir el ruido como explicación del resultado. No se asume que esta fuente tenga independencia conceptual plena: conservación de material y familias de colas pueden coincidir con los candidatos aunque se programe en otro lenguaje.

**Separación de responsabilidades:** diseñar/fijar la fuente y su verdad → generar **solo construcción** → exponer el mismo paquete público a D/B/M/REF → producir y sellar predicciones del escenario de evaluación → ejecutar o revelar su respuesta → evaluar → adjudicar usando etiquetas privadas. No publicar la topología/tiempos internos en entradas de productores. Si falla el generador, conservar error y no cambiarlo después de observar predicciones sin abrir protocolo nuevo.

## 4. Referencias: REF-CAF principal y REF-SCALE de proporcionalidad

**REF-CAF — balance de cola de capacidad efectiva, solo construcción.** La entrada para estimar es el **perfil de llegadas prescrito** más `D(t)` público de construcción; la `A_real(t)` del DES se audita por separado y no ofrece una ventaja informativa al comparador. En intervalos [0,5], [5,10], [10,15] y [15,20] minutos, calcular tasas ΔD/5; la estimación operativa propuesta es la **mediana** de intervalos con *pendiente proxy de diseño* `A_diseño(t)−D(t)>1 pedido` tanto al inicio como al final, exigiendo al menos dos. Ese margen de un pedido es un **filtro conservador de discretización predeclarado**, no prueba de saturación ni un límite metrológico; si no se cumplen dos intervalos, abstenerse. Emitir `REF_CAPACITY_NOT_IDENTIFIABLE` si no alcanza esa condición. Esta estimación describe **rendimiento efectivo observado**, no una capacidad física máxima identificada. Incluso si P es positivo, pueden existir etapas aguas arriba; por tanto **NO** equiparar esa tasa con una capacidad exacta del generador. Si no se observa saturación del cuello de botella, la tasa lograda proporciona, a lo sumo, evidencia de rendimiento alcanzado (o un límite inferior bajo hipótesis explícitas). Conservar esa incertidumbre.

**Política condicional de pronóstico REF-CAF:** con estimador válido, aplicar la cola fluida sin pérdidas `dP/dt=λ(t)−q(t)`, `dD/dt=q(t)`, usando `q=μ_eff` cuando haya pendiente disponible y `q=min(λ, μ_eff)` cuando la cola sea cero. `μ_eff` es un **parámetro predictivo empírico**, no el cuello de botella verdadero. Iniciar ambos escenarios vacíos, resolver exactamente por tramos del pulso, producir predicciones A/D/P antes de acceder al escenario de evaluación. Si el estimador falla, **abstención**, no sustituir una tasa secreta ni recuperar un estimador después de observar la evaluación.

**REF-SCALE — referencia de proporcionalidad, adicional y necesaria.** Dado `k=1.50/1.20=1.25`, pronosticar para evaluación `D_scale(t)=min(A_eval_prescrita(t), k·D_construcción(t))` en los **mismos seis instantes de evaluación**, sin refit ni visión del mundo de evaluación. `A_eval_prescrita(t)=1.50·min(t,20)` pedidos ideales con `t` en minutos; `P_scale=A_eval_prescrita−D_scale` es derivado. Si el conteo observado de llegadas difiere de la integral ideal, registrar el desajuste de discretización separado, no filtrar el conteo real del futuro al pronóstico. Esta referencia será **comparador separado**, no se cuenta como un brazo, no necesita un generador adicional y podría explicar perfectamente la transferencia cuando todo sea aproximadamente lineal. Si lo hace, **no atribuir recuperación estructural a D/B/M**.

**REF-CAF** sigue siendo el competidor convencional principal; **REF-SCALE** es un control indispensable de la afirmación científica de transferencia. Ambos reciben exclusivamente el mismo paquete de construcción. El balance `P=A−D` no es una tercera referencia independiente.

## 5. Compatibilidad por brazo, unidades y política de parámetros (sin modificar arquitectura)

**Conversión única desde el contrato público de minutos a los adaptadores heredados en horas**, sin cambiar el significado de los datos: 1.20 pedidos/min → **72 pedidos/h**; 1.50 pedidos/min → **90 pedidos/h**; pulso de 20 min → **1/3 h**; horizonte 40 min → **2/3 h**; instantes de salida `[0,1/12,1/6,1/4,1/3,1/2,2/3]` h. Para D/M usar stock `items` con la equivalencia operacional *un pedido aceptado = un item*; esto es una **proyección semántica declarada**, no identidad empírica de todas las moléculas con servicios reales. No redondear a 0.33 h.

| Brazo | Implementación y restricciones verificadas | Parámetros y adaptación PC-01/0.2 | Compuerta |
|---|---|---|---|
| **D** | Gramática original de 1–3 stocks con variantes sin/con pérdida. **El contrato CAF-01 conoce ausencia de pérdidas:** sus tres grafos con pérdida quedan fuera de la competición por frontera física, no por RMSE; no se reescribe la gramática. | **3 grafos sin pérdida**, cada uno con capacidades `[48,72,96]` pedidos/h × tiempos de respuesta `[0.125,0.25]` h × tiempo de pérdida de relleno `[1.0]` h: **18 integraciones RK4** de construcción; CAF-N permite otras **18 integraciones RK4 sobre su máscara**, sin OpenModelica adicional. **3** gráficos G2 en construcción y **3** en evaluación como máximo. Nominal `{capacity:72,response_time:0.25,loss_time:1}` es **supuesto no estimado**. | `D_LOSS_FREE_POLICY_AND_GRID_NOT_YET_NATIVE_PREFLIGHTED`; selección y abstención pendientes. |
| **B / Buffalo** | El traductor histórico bloquea cualquier `specs` distinto de `0–8 h`, `dt=0.125 h`, Euler; su vista actual admite exactamente dos stocks/dos flujos. | Adaptador **local experimental no implementado** para `0–2/3 h`, `dt=1/120 h`, Euler, comprobando paridad temporal y sin cambiar ecuaciones nativas. Si la propuesta B excede la vista de dos stocks/dos flujos, bloqueo de adaptación, no fallo de Buffalo. **Dos inferencias máximas propuestas**: original CAF-01 y una segunda independiente para CAF-N con información enmascarada, sin historial de la primera. **Solo el modelo original** puede consumir las dos simulaciones OM; CAF-N ninguna. | `B_LOCAL_ADAPTER_NOT_IMPLEMENTED`; `B_CAFN_SECOND_CALL_NOT_AUTHORIZED`. |
| **M / Short E1** | `arena_m_visible_pulse.py` exige `items/hour`, duración ≤8 h, tasa ≤100 items/h: **72 y 90** caben; el comando existente de simulación corre a **4 h**, por lo que necesita una invocación local a `2/3 h` sin alterar moléculas. El registro E1 fija `maxThroughput=20` pedidos/h en preparación/despacho, `responseTime=0.5` h y, cuando existe tránsito, `responseTime=1.6` h. R3 variaba prep/dispatch con rejilla **0.25, 0.5, 1 h** y mantenía el tránsito 1.6 h. | No trasladar parámetros del generador. **Dos políticas separadas**: (i) nominal histórico E1 `{20/h,0.5h,1.6h tránsito}` como **control de portabilidad**, no calibración; (ii) variante CAF-01 acotada a **3 clases × 3 configuraciones**: mantener `responseTime` preparación y despacho a `0.5 h`, tránsito `1.6 h` si corresponde, y variar **juntas las dos capacidades** `[20,72,100]` pedidos/h: **9 modelos**; 20 proviene del registro, 72 de la tasa pública de construcción y 100 es el máximo catalogado. Esto son **hipótesis de diseño**, no estimaciones ni ajustes secretos; la variación conjunta no identifica dos capacidades individuales. El retardo de 96 min en tránsito excede el horizonte de 40 min: puede haber poca observabilidad, **no** un fracaso automático de M. | `M_CAF_PARAMETERS_AND_LOCAL_HORIZON_TO_APPROVE`; no afirmar que `arena_m_short_e1.py` selecciona estos 9 por sí solo. Debe comprobarse que cada grafo y cada parámetro pasan el linter y el backend nativo. |

**Importante:** los números de las grillas D/M **son opciones concretas para revisar**, no preinscripción aprobada. No recalibrar con evaluación. No cambiar ecuaciones de Buffalo, gramática D ni biblioteca Short E1 para ayudar a que una rama alcance al generador. La estructura no presente en el repertorio será `REPRESENTATION_LIMIT`, no un permiso para ampliar arquitectura. Diferencias entre grafo y parámetro deben distinguirse.

**Evidencia común:** `arena_v0_common_evidence.py` sólo acepta pulso `{kind,rate,duration}` y entregas `{t,delivered}`; todo dato A/P nativo extra debe ir como **sidecar de procedencia**, no inyectarse en entradas incompatibles. El `input_hash` del mismo caso debe ser idéntico para las tres vistas; los campos específicos de adaptador pueden ser diferentes por unidad si sus conversiones y hashes se declaran. Los brazos conservan independencia de sus resultados y del mundo privado; ledger/ATMS guarda soporte lógico, no verdad empírica. Clef y Clairic quedan fuera.

## 6. Observables, comparación y reglas de evaluación

- **Independencia estadística:** solo **entregas acumuladas D(t)** es observable primario de desempeño en este diseño. Llegadas realizadas A(t) se registran para comprobar el estímulo, y `P(t)=A(t)−D(t)` es una **transformación determinista** bajo sin pérdidas e inicial vacío. Por tanto `MAE_P` y `RMSE_P` se informan como **métricas derivadas correlacionadas**, nunca como una segunda validación o evidencia independiente. Solo una **medición independiente de pendientes en estados internos** podría añadir evidencia de stocks, y NO está presupuestada como prueba predictiva adicional en CAF-01.
- **Conservación física:** además del balance público `A−D−P=0` computado, verificar de modo independiente en la **traza nativa del generador** `A=D+Σstocks_materiales+L` y en cada candidato, con sus stocks materiales propios y pérdidas explícitas. Rechazar doble conteo de stocks de entrega/información. Si sólo tenemos `P=A−D` y no los estados, declarar `MATERIAL_STOCK_BALANCE_UNVERIFIED`, no afirmar prueba física.
- **Predicción principal:** MAE/RMSE sobre D en t=5,10,15,20,30,40 min, con la misma información para D/B/M/REF-CAF/REF-SCALE y sin utilizar la respuesta futura para elegir modelos. `ΔD` entre escenarios es una transformación derivada, **no un segundo holdout**.
- **Comparaciones:** reportar error frente a **ambas** referencias por separado. Para una ventaja descriptiva frente a REF-CAF, proponer mejora de ≥1 pedido de MAE_D, con consistencia y sin fallo G2; exigir también superar o al menos explicar diferencias frente a REF-SCALE si se afirma *inferencia estructural transferible*. Umbrales operativos tentativos, **no** test estadístico ni cotas de sensor.
- **Denominadores y fallos:** contabilizar todas las propuestas, incompatibilidades de adaptador (especialmente B), validaciones G0/G1/G2, simulaciones efectivas, abstenciones, costo y tiempos. No calificar como fallo científico de un brazo lo que no traduce el adaptador; no calificar como éxito la mera compilación o el menor RMSE de construcción.
- **Incertidumbre y decisión:** conservar conjunto de hipótesis compatibles, supuestos, limitaciones y una página legible para dueño (si no hay dueño real, solo legibilidad técnica). Ningún resultado de este caso único demuestra superioridad general, causalidad o utilidad comercial validada.

## 7. Presupuesto **por fase y por motor** — NO autorización

El presupuesto anterior de **32** era `12 D + 2 B + 18 M` OpenModelica, sobre el que Astra señaló la omisión de los 36 RK4. La revisión v0.3 además elimina las tres variantes con pérdida de D por incompatibilidad con una **frontera sin pérdidas conocida**, reduciendo el subtotal de OpenModelica a **26** (`6 D + 2 B + 18 M`). Se preservan las 36 integraciones RK4 como 18 CAF-01 + 18 CAF-N; las 27 configuraciones de M de R3 no se reactivan (serían 54 corridas solo M en dos mundos).

| Clase de trabajo | Construcción | Pronóstico escenario nuevo (antes de revelar mundo) | Total máximo | Cuenta como |
|---|---:|---:|---:|---|
| Generador DES independiente | 1 | 1 | **2** | runs DES; segundo reservado, no reutilizar para calibrar |
| D: RK4 de grilla **3 sin pérdida ×3×2** | **18** | 0 | **18** | integraciones Python en CAF-01; no se simula pérdida conocida inexistente |
| D: **tres grafos sin pérdida** elegidos tras construcción | **3** | **3** | **6** | ejecuciones OpenModelica, máximo |
| B: una única propuesta admisible | 1 | 1 | **2** | runs OpenModelica; 0 si adaptador bloqueado |
| M: 3 estructuras × 3 capacidades | 9 | 9 | **18** | runs OpenModelica; no 27 por escenario |
| D: CAF-N sobre evidencia enmascarada | **18 adicionales (RK4)** | 0 | **18** | integraciones Python, no nuevo mundo ni OpenModelica |
| REF-CAF y REF-SCALE | 0 | 0 | **0** | cálculo analítico/tabular, **2 algoritmos**, registrar costo de CPU |
| **Subtotal candidatos OpenModelica** | **13** | **13** | **26** | no son todo el presupuesto; ningún mundo de CAF-N |
| **Totales por motor** | **DES 2** | **Python RK4 36** | **OpenModelica 26** | + dos inferencias B máximas; unidades de costo distintas |

**Proveedor:** se proponen **2 inferencias Buffalo** (una CAF-01 y otra CAF-N con contexto aislado), todavía no autorizadas. D/M/REF 0, reintentos 0. Las verificaciones de parseo, linter, hashes y contratos pueden hacerse sin simulador; si alguna invoca un solver, **consume** el rubro correspondiente. No existe presupuesto adicional tácito para prueba de humo, búsqueda oportunista, reevaluación adaptativa o repeticiones. Las 36 integraciones de D se dividen en **18 CAF-01 + 18 CAF-N** como techos de búsqueda RK4; las ejecuciones G2 y cualquier otra integración computacional deben registrarse también, incluso si fracasan. Ninguna cifra constituye autorización automática.

**Gobernanza:** selección por construcción, sello de candidatos y predicciones, custodia del futuro, luego una sola evaluación del mundo. **No** utilizar REF-SCALE para elegir a posteriori parámetros del brazo. La contabilidad es una propuesta preliminar; si los adaptadores requieren acciones adicionales, volver a PC-01 y renegociar antes de gastar. El control CAF-N no usa ninguna simulación OpenModelica nueva; su segunda llamada B no queda implícitamente autorizada.

## 8. Orden de trabajo y compuertas para PC-02

1. **G-0 · Contrato:** verificar tipos, tiempos, unidades, estado inicial, conservación y que el pulso de ambos escenarios se pueda representar en los adaptadores pertinentes. Guardar pruebas negativas para entrada incompatible.
2. **G-1 · Independencia del generador:** fijar implementación/supuesto/versión privada de eventos, parámetros de mundo, horarios reales de aceptación, restricciones y reglas de conteo **antes** de generar construcción. Se evalúa qué comparte conceptualmente con E1. No copiar ecuaciones ni parámetros de candidatos.
3. **G-2 · Adaptación acotada:** documentar y prevalidar D nominal/grilla RK4, 9 modelos M y adaptador B local con alcance separado, y tratamiento de `A,D,P`, sin hacer cambios generales de arquitectura. Si una interfaz no alcanza, emitir bloqueo auditable y decidir una adaptación localizada **antes** de la campaña.
4. **G-3 · Política de selección:** fijar qué candidatas caben en los 26 runs OpenModelica y las 36 integraciones RK4 de D, la regla de selección o abstención por brazo, y procedimiento de congelado sin ver evaluación. No sustituir una predicción ausente por datos del generador.
5. **G-4 · REF-CAF:** fijar estimador y casos de abstención de REF-CAF, REF-SCALE, métricas y tolerancia de agregación, y su independencia de la verdad privada.
6. **G-5 · Autorización separada:** aprobar conteos/versiones finales y mecanismo de custodia antes de abrir PC-02. No iniciar el generador ni pedir a Buffalo hasta cumplir G0–G4 y autorización explícita.

### 8.1. Control negativo CAF-N · También obligatorio en PC-02, no ejecutado

V3.0 exige que PC-02 incluya **CAF-01 y CAF-N**. El diseño v0.2 lo excluía y era una desviación del plan. En la copia enmascarada del **mismo mundo de construcción**, conservar el pulso publicado y únicamente `D(0)` y `D(40 min)`; retirar las lecturas intermedias de entregas, pendientes reconstruidos e información derivada. **Pregunta nula específica:** ¿puede el método reconocer que **no puede observar la hora del máximo de pendientes, la trayectoria de cola ni tiempos individuales de espera** desde solo dos extremos? La salida aceptable reporta totales calculables y abstención respecto de magnitudes no identificables; una curva supuesta puede mostrarse como escenario, nunca como observación identificada.

- D: **18** integraciones RK4 nuevas sobre la máscara, solo para cuantificar la ambigüedad bajo su grilla, sin solver OpenModelica.
- M: análisis de compatibilidad únicamente de puntos terminales contra **las nueve curvas ya simuladas**; no elegir usando el resto de la serie antes de aplicar el enmascaramiento.
- B: **segunda llamada de IA independiente, sin historial ni respuestas del experimento original**, si se aprueba la nueva cota. Nada de simulaciones físicas nuevas para CAF-N.
- REF: REF-CAF probablemente abstendrá si faltan al menos dos intervalos interiores; no inferir una capacidad del mundo privado. REF-SCALE no puede reconstruir el perfil temporal sin D(t) de construcción intermedia.

No suma otro mundo generador, no permite acceso a información oculta ni puede considerarse un holdout independiente. Sus respuestas deben archivarse antes de adjudicarse, con la regla de abstención fijada. **Estas dos inferencias propuestas no están autorizadas por el presente documento.**

## 9. Qué queda deliberadamente fuera de PC-01

CAF-02 (revisión K0/K1/K2), MEM-CAF (memoria C0/C1), producto financiero y elección del brief. **CAF-N sí pertenece a PC-02**, pero se prepara ahora y no se ejecuta en PC-01. Su diseño depende de los resultados del primer caso. **Ninguna fase posterior está autorizada por este borrador.** El brief `ARENA_BRIEF_ASTRA_OPCIONES_IMPLEMENTACION.md` se cita en V3.0 pero no apareció entre los materiales disponibles en esta preparación; no se le atribuyen opciones o conclusiones no consultadas.

## 10. Dictamen de PC-01 (preparación documental)

**Alcanzado documentalmente:** dos pulsos reiniciados, calendario determinista de llegadas con exactitud racional, unidades, bloqueo Buffalo, 9 candidatos M propuestos, 3 grafos D sin pérdida, dos referencias, sidecar sin privilegio informativo de REF, CAF-N predefinido, presupuesto por motor y fase.

**Aún NO alcanzado:** equivalencia ejecutable del adaptador Buffalo, linter/backend real para los nueve M, decisión independiente sobre tiempos de servicio/topología y su sello privado DES, política de selección/abstención, aceptación de parámetros D/M, definición final de límites y autorización de presupuesto, sello de predicciones, y autorización separada para PC-02. **El contrato v0.3 no es una preinscripción y no prueba ejecución científica**.

### Rutas del código inspeccionadas (solo lectura de `main`)

`arena_v0_contract.py`, `arena_v0_common_evidence.py`, `arena_d_v01.py`, `arena_d_v1_screen.py`, `arena_d_v2_revision.py`, `arena_b_openrouter_cloudflare.mjs`, `arena_b_native_to_modelica.py`, `arena_b_native_series.py`, `arena_m_short_e1.py`, `arena_r3_pt06_parametric.py`, `arena_m_visible_verify.py`, `arena_m_visible_pulse.py`, `experiments/e1/registry.base.json`, `experiments/e0/catalog.json`, `arena_r4_pt07_t2_forecast.py`, `ledger.py`, `arena_atms.py`, `arena_memory.py`.
