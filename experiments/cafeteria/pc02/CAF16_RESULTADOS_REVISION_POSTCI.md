# CAF-16 — Resultados canónicos de robustez estocástica y revisión adversativa POST-CI

**Estado:** interpretación escrita DESPUÉS de la ejecución, sin modificar los 30 mundos, las semillas, las tolerancias, los 12 ciclos, los programas, el catálogo ni el criterio de inferencia. Fecha local 2026-10-31 (registros de GitHub Actions en UTC 2026-11-01). PR #129 Draft sobre CAF-15B #128 Draft. No merge.

## Proveniencia verificable

- **Primer commit experimental ANTES del código:** `5f7299dea32b9eec654b3f4a43f237b88b1f392c`, con `CAF16_PROTOCOLO_ROBUSTEZ_ESTOCASTICA.md`.
- **[CI canónica #41265916316](https://github.com/yudocyudoc/IGC/actions/runs/41265916316)**: **7/7 tests PASS**, paridad nativa de generador CV0, ensayos reproducibles por SHA256, sensor E0/E1 emparejado, analista congelado y **4,320 lecturas procesadas**. HEAD probado `ff4cdadea6546abcee636153e35954afb9c7eed7`, checkout SHA sintético registrado por separado en los archivos.
- **[Evidencia íntegra de cinco archivos](https://github.com/yudocyudoc/IGC/actions/runs/41265916316/artifacts/13066864741)**: `00B_CATALOGO_PRE_EVALUACION.json`, `00_PLAN_PRE_EVALUACION.json`, `01_RESULTADOS.json`, `02_INFORME.md`, `03_MANIFIESTO.json`. Descargado y verificados **4/4** SHA256 contra manifiesto.
- Banco de **720 configuraciones deterministas** con firmas HIGH_T20 y SHAPED_T14_T20, guardado ANTES de evaluar mundos. Semilla maestra `IGC-CAF16-20261031-v1` y derivación por `sha256` congeladas. El archivo de resultados conserva lectura física SIN error, lectura reportada CON error y conjunto de clases para cada caso.
- **No son dos simuladores físicos independientes en sentido empírico.** CAF-16 implementa un nuevo motor de eventos en vez de reusar `run_toy_engine` como generador, pero su estructura FIFO, los recursos y la política de empates siguen el modelo de CAF-01. La paridad exacta del CV0 es control de implementación; no evidencia de generalidad real.

## Diseño y denominadores

- **27 mundos in-family** (9 cuello single, 18 doble con capacidades distintas) y **3 controles extra de cuarta etapa** (64,106,220/h). Todos sintéticos; las capacidades nominales se incluyeron deliberadamente en la malla del analista.
- Factores de servicio equiprobables, aplicados i.i.d. a todos los servicios: `CV0={1}`, `CV25={3/4,5/4}`, `CV50={1/2,3/2}`. No estimados de ninguna cafetería; media del factor 1 y CV verdadero 0, 0.25, 0.50 respectivamente.
- Dos observaciones por canal: `E0` sin error instrumental; `E1` agrega perturbación independiente uniforme en `{-1,0,+1}`, truncada a cero. Ambos conservan analista determinista con banda fija **±1 pedido en TODOS los canales simultáneamente**.
- `HIGH_T20`: K0/K1 + seis contadores a t20 bajo carga 150/h constante en [0,20). `SHAPED_T14_T20`: K0/K1 + seis contadores en t14 y t20 sobre UNA trayectoria [0,6) a 72/h, [6,14) a 150/h y [14,20) a 72/h. Dos instantes del mismo pulso **NO son réplicas**.
- 12 réplicas por mundo×CV×programa; E0 y E1 **reutilizan las mismas trayectorias**. 27×12=324 lecturas in-family por programa×CV×E, y 3×12=36 controles externos por estrato. Total 30×3×2×2×12=**4,320** lecturas (3,888 in-family y 432 desconocidas). Réplicas no equivalen a negocios independientes.
- Filtro del analista: mantiene una clase si hay AL MENOS un vector de capacidades de los 720 puntos que satisface `|y_j−pred_j|≤1` para cada componente observado. Los conjuntos vacíos son `NO_MATCH_ON_DETERMINISTIC_LATTICE`, **no diagnóstico de topología desconocida ni rechazo global del modelo en el continuo**.

## Resultado completo por estrato (denominador in-family 324, extra 36)

| Programa | CV | Sensor | Clase correcta retenida /324 | Conocidos sin ajuste /324 | Clases únicas correctas /324 | Clases únicas falsas /324 | Clases medias | Extras sin ajuste /36 | Extras falsos únicos /36 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| HIGH_T20 | 0% | E0 | **324** | 0 | 72 | 0 | 2.2593 | 36 | 0 |
| HIGH_T20 | 0% | E1 | **324** | 0 | 93 | 0 | 2.0833 | 36 | 0 |
| HIGH_T20 | 25% | E0 | **235** | **67** | 89 | **21** | 1.5432 | 35 | 1 |
| HIGH_T20 | 25% | E1 | **133** | **171** | 61 | **16** | 0.8611 | 36 | 0 |
| HIGH_T20 | 50% | E0 | **130** | **164** | 73 | **25** | 0.7994 | 34 | 2 |
| HIGH_T20 | 50% | E1 | **66** | **241** | 38 | **15** | 0.4043 | 35 | 1 |
| SHAPED_T14_T20 | 0% | E0 | **324** | 0 | 12 | 0 | 2.8148 | **12** | **24** |
| SHAPED_T14_T20 | 0% | E1 | **324** | 0 | 85 | 0 | 2.1821 | 28 | 4 |
| SHAPED_T14_T20 | 25% | E0 | **251** | **48** | 88 | **23** | 1.7531 | 28 | 6 |
| SHAPED_T14_T20 | 25% | E1 | **78** | **217** | 32 | **24** | 0.5710 | 36 | 0 |
| SHAPED_T14_T20 | 50% | E0 | **92** | **200** | 46 | **29** | 0.6327 | 35 | 1 |
| SHAPED_T14_T20 | 50% | E1 | **32** | **285** | 15 | **7** | 0.1944 | 35 | 0 |

### Falsador principal: la física variable rompe la cobertura del analista nominal

En HIGH con sensor sin perturbación instrumental:
- La retención de clase correcta cae de **324/324** para CV0 a **235/324** para CV25 y **130/324** para CV50.
- La ausencia de ajuste del banco determinista sube de 0 a **67** y luego **164** casos; en CV50, **25/324** lecturas generan una **clase única falsa**, incluso cuando el error instrumental es cero.
- Con CV50 y E1 la retención baja a **66/324**, y los no-ajustes ascienden a **241/324**. El deterioro del conjunto de clases medias **NO es mayor precisión**: gran parte de la reducción es por conjuntos vacíos e inferencias erróneas.
- Bajo HIGH CV50 E0, **singles**: clase verdadera retenida **26/108**, no-ajuste **66/108**, falso único **13/108**; **doubles**: retención **104/216**, no-ajuste **98/216**, falso único **12/216**. Por tanto, fallar no es exclusivo de los dobles.

En SHAPED CV50 E1, retención de clase correcta **32/324** y ausencia de ajuste **285/324**. **No concluir que la forma de demanda es causalmente responsable de toda la diferencia respecto de HIGH:** SHAPED cambia simultáneamente el perfil de llegadas, el horizonte de lectura disponible y el número de componentes observados (14 frente a 8). Aumentar canales bajo la misma banda ±1 puede disminuir el número de modelos admisibles sin aumentar información utilizable para un diagnóstico fiable.

### Falsador OOD: falsa confianza incluso sin variabilidad de servicio

La demanda modulada SHAPED con **CV0 y E0** asigna una **única clase equivocada 24/36 veces a controles de cuarta etapa**: en `EXTRA_106` **12/12** y `EXTRA_220` **12/12** aparece etiqueta **`preparacion`**, mientras `EXTRA_64` queda sin coincidencia **12/12**. Esas 24 repeticiones son copias deterministas de dos mundos, NO 24 topologías distintas.

Con error instrumental E1, para esos mismos mundos el número de falsos únicos baja de 24 a **4/36**, pero suben las incompatibilidades de 12 a **28/36**. **Esto no implica que añadir ruido sea beneficioso**: las perturbaciones pueden desplazar una firma a fuera de la malla sin revelar la topología verdadera. La respuesta adecuada ante NO_MATCH_ON_LATTICE es «catálogo insuficiente o observación fuera de tolerancia», no declarar cuarta etapa con certeza.

HIGH bajo CV0/E0 rechaza 36/36 controles con conjunto vacío, pero esta aparente buena detección depende de la presión artificial, canales ideales y tres topologías escogidas. Un solo protocolo OOD no permite afirmar sensibilidad general.

## Interpretación disciplinada

1. **CAF-15B permanece correcto bajo su enunciado matemático**: separabilidad global de 11 pares dentro de un DES determinista. CAF-16 no puede refutar un teorema CONDICIONAL cambiando las premisas. Lo que sí demuestra es que un analista determinista con filtro ±1 NO preserva cobertura bajo algunos servicios aleatorios sintéticos.
2. **Error instrumental y variabilidad física son mecanismos distintos**; E0/E1 comparte trayectoria, lo que permite comparaciones pareadas sin introducir una nueva realización de servicio. La restricción fija de ±1 en 8 o 14 canales amplifica riesgo de rechazo conjunto.
3. Un analista determinista que pierde la verdad **no necesariamente identificó mal la estructura física**: puede perderla porque el vector de conteos de una realización estocástica no pertenece a la imagen de ninguna capacidad determinista del banco. Debe aprender a reconocer incertidumbre/misfit sin generar falsa certeza.
4. La distribución de dos puntos tiene media correcta pero no pretende representar servicio real de un barista, cambios de turno, ausentismo, variabilidad de insumos, aprendizaje ni fatiga. Falta un generador empírico, medición de errores reales, timestamp y datos reales de ventanas de carga.
5. Un segundo motor de eventos independiente de código **no garantiza independencia de la hipótesis estructural**, pues también implementa FIFO homogéneo sin bloqueo y con recursos idealizados. No calificar como holdout real.
6. Con 12 réplicas por mundo, no calcular intervalos de confianza que presupongan 324 unidades empresariales independientes ni caracterizar cobertura poblacional; pueden reportarse promedios puramente descriptivos bajo este experimento.
7. La carga constante HIGH de 150/h no constituye una recomendación para inducir sobrecarga en una PYME. SHAPED es solo pulso sintético, **no** observación de sobrecarga natural ni datos históricos de una cafetería real.

## Decisión y siguiente fase científica

CAF-16 logra un **resultado adverso central**: aun cuando familias sean separables por matemáticas de servicio determinista, un filtro exacto con banda no calibrada puede producir una gran cantidad de conjuntos vacíos y etiquetas únicas falsas al cambiar la distribución del servicio. La dirección prudente ya no es aumentar el número de experimentos o selectores sino diseñar un **modelo explícito de variabilidad, censura y error de sensor**, con un protocolo de recolección por etapas y marcas temporales de inicio/fin si se cuenta con acceso instrumentado. Idealmente evaluar en datos externos y con un generador físicamente distinto (bloqueo/fin de inventario, cambios de ritmo, descansos).

**Gate científico PERMANENTE**: `BLOCKED_SYNTHETIC_STOCHASTIC_SERVICE_UNCALIBRATED_SENSORS_NO_EXTERNAL_VALIDATION`. PR #129 Draft sin merge; revisar externamente antes de promover cualquier intervención comercial, diagnóstico o recomendación.
