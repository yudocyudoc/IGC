# Arena IGC · F3/M × O1 · Comparación por ventanas de eventos y flujo molecular

**Fecha:** 2026-11-03 · **Estado:** ingeniería de observación **solo del evaluador**, sobre el control sintético EV-01 conocido. **No es una ley de observación validada ni una ronda científica G3/G4/G5.**

## Pregunta precisa

Después de PR #154 y la corrección #155 ya sabemos que declarar `FLOW<ReadyOrder>` no hace equivalentes las terminaciones discretas físicas y el flujo continuo Short E1. La identidad de unidades y la igualdad de acumulados al corte necesitan justificación propia.

Este incremento deja de comparar solamente **un número al minuto 10** y construye un objeto reproducible de **comparación por ventanas**, con dos medidas explícitamente diferentes y correctamente fechadas. No intenta decidir qué mecanismo es verdadero ni hacer encajar ambas escalas mediante una calibración retrospectiva.

## Operador descriptivo (no inferencia estadística)

Para las ventanas **ya existentes** en O0/O1, sin buscar tamaños de ventana ni seleccionar parámetros:

`[0,2), [2,4), [4,6), [6,8), [8,10)` minutos.

Se computan dos objetos distintos:

1. **Medida de eventos observados** `N([a,b)) = # {servicio_fin físicos en preparación, a ≤ t < b}`, con tiempos racionales exactos del FULL del **evaluador**; suma total **9** antes de t=10.
2. **Masa de flujo molecular** `M([a,b)) = ∫[a,b] preparation.completed_E1(t) dt`, usando la serie numérica `native_res.csv` de **la ejecución original OpenModelica M/O1**. No se redondea a pedidos; la integral reutiliza el operador de trapecios de `observation_eval.py` (aproximación numérica con tratamiento de discontinuidades). El modelo original limitado a **20 unidades/hora** no puede producir más de **2/3 unidad de masa en cada ventana de 2 minutos**, ni más de **10/3 unidades** durante los primeros 10 minutos.

La comparación publica ambos números por separado, así como su diferencia **solo descriptiva**. **No califica esa diferencia como error instrumental, incompatibilidad causal, estimador de fidelidad ni evidencia de un puente estadístico.** Un contador con saltos y una integral continua no deben empatar punto a punto. Incluso su igualdad integrada en un corte es una hipótesis aún sin prueba.

Las entradas internas FULL se controlan en el evaluador, **no** en el generador Short E1 y **no** en O1 público. Su procedencia se verifica por consistencia con POS y el agregado físico exacto de O1 (número, media de espera, media de servicio); esto **no es una firma independiente de la fuente**. El archivo OpenModelica conserva su hash autenticado por F3/G2. El reporte solo retiene hash del FULL y **conteos agregados**, no IDs, recursos ni fechas de casos individuales.

## Implementación y comprobaciones

- `scripts/arena_cafe/m_o1_window_measures.py`: función determinista de comparación por ventanas; usa la proyección original de EV-01 y los operadores nativos originales; no genera otro DES o modelo.
- `f3_adjudicate.py`: reconstruye el FULL original exclusivamente **dentro del evaluador ya situado después de los trabajadores** y verifica **paridad con el DES CAF-01 original**; llama al comparador solo para M/O1 con el CSV OpenModelica reaudidato y el certificado del catálogo Short E1. El trabajador de M sigue viendo únicamente el sobre visible O1.
- `tests/test_arena_cafe_m_o1_window_measures.py`: pruebas directas de **frontera interior exacta** (evento en `t=2` pertenece a [2,4), no [0,2)), **rampa lineal** de caudal distinta del flujo constante, rechazo de **30/h por encima de capacidad**, estado censurado inconsistente por caso, trazabilidad de las condiciones y rechazo de manipulación física/CSV. El fixture de rampa es una sonda analítica **no** una segunda ejecución OpenModelica; las masas de OpenModelica real se comprueban aparte en la adjudicación final CI.
- CI existente A1/A3: reejecuta las cuatro soluciones D/M auténticas y las dos verificaciones Buffalo offline, compara fuentes, vuelve a adjudicar F3 y publica únicamente un JSON resumido de la auditoría.

## Resultados efectivos del control EV-01, versión actual

[CI reproducible del corte documentado](https://github.com/yudocyudoc/IGC/actions/runs/41755789084) y [reporte F3 de ese HEAD](https://github.com/yudocyudoc/IGC/actions/runs/41755789084/artifacts/13287678009), que contiene `arms.O1.M.native.metrics.preparation.evaluator_only_window_measures`.

| Ventana [a,b) min | Eventos físicos `servicio_fin` | Masa `ReadyOrder` integrada del OMC M/O1 (aprox.) | Cota exacta nominal E1 |
|---|---:|---:|---:|
| [0,2) | 0 | 0.1550978568 | 2/3 |
| [2,4) | 3 | 0.4675602033 | 2/3 |
| [4,6) | 2 | 0.6628212075 | 2/3 |
| [6,8) | 2 | 0.6666666667 | 2/3 |
| [8,10) | 2 | 0.6666666667 | 2/3 |
| **Total** | **9** | **2.6188126009** | **10/3** |

Al corte hay **cinco visitas a preparación esperando servicio** y **una en servicio**, todas censuradas por la ventana [0,10), por lo cual no se suman a las nueve terminaciones.

**Interpretación exclusivamente descriptiva y límite estructural condicional:** la rampa de tasa molecular explica **solo una parte de la forma temporal inicial**, no la discrepancia completa. En [6,8) y [8,10) el modelo ya se encuentra prácticamente en su techo nominal de **2/3 unidad de masa por ventana**, frente a **dos terminaciones físicas** por ventana. La brecha es de **al menos tres veces la capacidad máxima nominal** si, y solo si, se exige el puente de equivalencia entre terminación y masa completada.

Además, las terminaciones sucesivas en preparación del control físico corresponden al servicio constante **15/17 minutos por pedido** (≈68 terminaciones/hora), mientras la tasa E1 nominal está limitada a 20 unidades/hora. Por tanto, **ni cambiar la ubicación de las cinco ventanas ni ajustar su ancho resolvería el límite integral global del candidato fijo**: bajo una correspondencia exacta de acumulados en el mismo corte, siempre habría 9 terminaciones contra una cota total de 10/3. Este es un límite de capacidad bajo una **hipótesis de medición no validada**, no evidencia de que la cafetería real incumpla esa capacidad ni de que el brazo M en general esté refutado.

Estos objetos tienen unidades y geometría temporal diferentes: los conteos son saltos unitarios y las integrales son masa continua aproximada numéricamente. **La diferencia de 9 contra 2.6188 no es una estimación de error de sensores ni una métrica causal**. Tampoco se infiere un factor de conversión entre unidades sin evidencia independiente.

## Decisión explícita sobre reutilización ciega de EV-01

Los cinco conteos por ventana **proceden del FULL privado conocido del evaluador**. Publicarlos en el repositorio y en los artefactos vuelve a EV-01 **no ciego a esta granularidad**, aunque el código no publique IDs ni marcas temporales individuales. **La decisión es consciente: el escenario queda etiquetado permanentemente como control de desarrollo, regresión y auditoría, no como conjunto independiente G5 ni reserva prospectiva futura.** Las nuevas pruebas adversariales de fronteras sintéticas no revierten esta contaminación ni validan sensores reales.

La implementación conserva distancias entre dos tipos de guardas: los guardas **alcanzables** (techo de caudal, censura por caso, misma fuente física, hash, tiempos cortados y entrada O1) tienen pruebas negativas específicas; los controles redundantes después de la validación del parser (por ejemplo, flujo integrado negativo tras haber rechazado una tasa negativa) se mantienen solo como **defensa en profundidad**, sin afirmar que todos sean disparables independientemente.

## Lo que permite concluir

Se observa **cómo difiere la geometría temporal de ambas medidas** sin esconder sus tipos. Podemos investigar qué escala temporal hace coherente una comparación y qué información necesitamos para justificarla; **no** inferir tolerancias cambiando ventanas hasta que coincidan los resultados.

Las ventanas de dos minutos **son heredadas** del experimento EV-01 y no fueron elegidas para optimizar la concordancia. Una familia nueva con eventos, retrabajos o estaciones compartidas podría requerir un operador diferente: no se extrapola este resultado de desarrollo.

**Límites vigentes:** correspondencia material `NO VALIDADA`; correspondencia de acumulados en el corte `NO VALIDADA`; errores de reloj/sensores `NO CALIBRADOS`; aproximación continua versus completados discretos `NO VALIDADA`; F3 `PARTIAL`; método Buffalo EV-01 live `NOT_RUN`; M/O1 no genera/selecciona/ajusta modelos; G3 científico `NOT_ESTABLISHED`; G4/G5 `NOT_RUN`; valor incremental PM-14 `NO DEMOSTRADO`. Este trabajo no utiliza la reserva F5 ni pretende abrirla.
