# IGC · Arena PT-07 / R4-A · Protocolo prospectivo T2 (preflight)

**Fecha:** 2026-10-27 · **Etapa:** PT-07/R4, PR preparatorio. **Estado:** solo **PREDICCIONES BLOQUEADAS**, ningún resultado futuro revelado. **No es** aún la aceptación completa de R4 ni un holdout externo independiente.

## 1. Pregunta y fuente de evidencia

PT-06 estableció que en R3-T2 una ventana de 0–0.15 h permite tres clases materiales compatibles (C00, C01 y C02), mientras que el selector M3 original se abstiene. El contraste prospectivo pregunta: **¿pueden las hipótesis compatibles producir predicciones suficientemente diferentes para escoger una nueva medición y, al contrastarla, reducir el conjunto sin perder el origen generador?**

El paquete usa solo los **27 CSV físicos reales** del [ensayo T1, Actions #40578550337](https://github.com/yudocyudoc/IGC/actions/runs/40578550337) y el archivo público de las **cuatro observaciones T2** junto con el veredicto R3 previo de [Actions #40582633807](https://github.com/yudocyudoc/IGC/actions/runs/40582633807). Los CSV se vuelven a verificar con el comprobador físico E1 G2 y su manifiesto congelado SHA256 `d33cc4ca8c253226ff50efa6c47e40b9b8c32d0436f370907db2579c9dc0fde5`. El preflight **no abre** el CSV del mundo T2 ni la etiqueta de su estructura generadora, y no obtiene observaciones posteriores a t=0.15 h.

**Limitación científica:** el generador E1 es público y comparte catálogo con los candidatos. La separación operativa de archivos no constituye cegamiento criptográfico. Este primer contraste R4-A sería una **comprobación sintética intrafamilia** de predicción y selección de información, **no** generalización externa ni identificación causal.

## 2. Qué se congela antes de pedir nueva observación

1. **Conjunto de configuraciones, no ganadores:** entre las 27 configuraciones `C00P00..C02P08` se admiten **todas** las de RMSE de construcción **≤ 0.020 items**, calculado exclusivamente en t=`0,0.05,0.10,0.15` h. Se conservan sus IDs, topologías, RMSE, SHA del CSV fuente y predicción física. El límite es una **regla de política**, no una incertidumbre instrumental medida.
2. **Bandas por estructura:** mínimo, mediana y máximo de todas las predicciones compatibles de cada clase en tiempos candidatos `0.5,1.0,1.5,2.5,3.0` h. Esas bandas representan **cobertura de esta grilla**, no intervalos de confianza probabilísticos. Se excluye t=2 exactamente para evitar ambigüedad de salida en el borde del pulso.
3. **Tiempo único de medición:** maximizar lexicográficamente (a) el **menor** hueco positivo entre las tres bandas, (b) si hay empate, la menor separación entre medianas de estructuras y (c) si persiste empate, escoger el tiempo **más temprano**. Si las bandas se solapan se declara y no se afirma que exista un tiempo inequívocamente discriminante. Los puntajes se derivan **solo de los CSV de candidatos**, nunca de futuros datos del mundo.
4. **Predicciones y REF:** al tiempo elegido se guardan las predicciones de **todos** los IDs compatibles. Para un pronóstico puntual agregado se toma la mediana de las tres medianas estructurales (peso idéntico por topología, no por número de configuraciones). La referencia determinista REF es `LAST_OBSERVED_DELIVERED_PERSISTENCE`: repetir el último `deliveredTotal` observado en t=0.15 h; no equivale ni invade el brazo D.
5. **Sellado:** `forecast-lock.json` completo y SHA256 de sus **bytes originales** en `forecast-lock.sha256`. El lock contiene tiempos alternativos considerados, criterio de elección, todas las predicciones, REF, SHA de los 27 CSV y hashes del caso público/decisión. Contiene explícitamente `future_observation_value=null`, `R4_complete=false`.

## 2A. Resultado real del preflight offline, todavía sin observación futura

La reconstrucción [CI #40614154705](https://github.com/yudocyudoc/IGC/actions/runs/40614154705) verificó los 27 CSV E1 y encontró **27/27 configuraciones compatibles** con los cuatro puntos T2: **9 de C00, 9 de C01 y 9 de C02**. La regla prospectiva eligió **t = 1.0 h**. Se selló el archivo completo con SHA256 `94b1231c33f605cbca4efb81aa6a6f31883e628e4303eae9cbdbd53eb78811d8`; el certificado con hash y resultados numéricos también queda versionado en `data/diagnostics/ARENA_R4_PT07_T2_FROZEN_FORECAST_CERTIFICATE_20261027.json`.

Bandas del observable `deliveredTotal` a la hora elegida, en items, calculadas **exclusivamente de las curvas candidatas**:

| Estructura | Mínimo | Mediana | Máximo |
|---|---:|---:|---:|
| C00 | 0.176185 | 0.406265 | 0.896705 |
| C01 | 0.026637 | 0.067112 | 0.164708 |
| C02 | 0.003259 | 0.008751 | 0.023100 |

Los tres intervalos **no se superponen**, pero la separación positiva **más pequeña** es solo **0.003536 items** (C01/C02), **inferior** al umbral de decisión futuro **0.020 items**. Por tanto, **una predicción con bandas disjuntas no garantiza por sí sola que la nueva observación elimine todas las estructuras rivales** bajo la tolerancia fijada. No se recalcula el tiempo por este hallazgo: fue elegido con la regla predeclarada.

Predicción puntual agregada (mediana de medianas estructurales, peso igual por topología): **0.0671117253 items**. REF persistencia (último valor T2 en t=0.15): **0.00007814994 items**. Estos números son **pronósticos sellados**, no valores medidos de t=1.0 h.

El sello no certifica independencia del generador público, solo integridad y precedencia operativa del pronóstico respecto de la nueva simulación, que **no se ha hecho**.

## 3. Regla de evaluación posterior, fijada de antemano

Se autorizaría **una única ejecución nueva** del mismo generador T2 **sin cambiar ecuaciones, parámetros o estímulo**, hasta el tiempo elegido. La nueva observación deberá extraerse desde su CSV físico y su procedencia/hash deberán verificarse **después** de demostrar que el forecast-lock existía; una respuesta manuscrita de ejemplo o un JSON de prueba **no cuenta** como medición.

Para cada configuración congelada se calcula el error absoluto respecto de esa **única** nueva observación. Sobrevive si `abs(predicho–observado) ≤ 0.020 items`; es el mismo corte operativo de selección, no una precisión metrológica. Una estructura sobrevive si **al menos una** configuración congelada sobrevive. No se permiten ajuste de parámetros, cambio de tiempo ni ingreso de nuevas configuraciones después de revelar el dato.

Se registran simultáneamente: conjunto previo de tres estructuras; conjunto posterior; cantidad reducida; sobrevivientes por ID; error absoluto de la predicción agregada; error absoluto de REF; y resultado de si el agregado mejora REF. Resultado válido: estructura única **condicional**, conjunto ambiguo, o conjunto vacío. **Nunca** se declara identificación causal únicamente por sobrevivencia de una estructura.

La verificación de si el **generador sintético** permanece en el conjunto debe hacerse en una **adjudicación separada, posterior** al scoring, sin entregar la etiqueta generadora a los mecanismos de selección. Para medir beneficios generales, deberá diseñarse después una evaluación que no comparta generador conocido ni decisiones de ajuste con R3.

## 4. Compromisos y compuertas

| Actividad | Este PR | Próxima ejecución (por autorizar) |
|---|---:|---:|
| Revalidar los 27 CSV existentes | Sí, solo lectura | Reutilizables |
| Sellar todos los pronósticos compatibles | Sí, offline | Inmutables |
| Elegir un tiempo por separación prevista | Sí, offline | No cambiarlo |
| Crear REF persistencia | Sí, offline | No reentrenarlo |
| Ejecutar mundo T2 para nueva observación | **0** | **Máximo 1 nueva simulación OpenModelica**, con consentimiento aparte |
| Simular candidatos, modificar modelos, llamar IA | **0** | **0** |
| Usar futuro observado para elegir modelo/tiempo | **Prohibido** | **Prohibido** |
| Demostrar reserva externa o causalidad | No | Fuera del alcance R4-A |

El módulo `scripts/arena_r4_pt07_t2_forecast.py` solo recibe el caso público T2, su decisión R3 y los 27 CSV originales. `scripts/arena_r4_pt07_t2_score.py` define la regla futura y rechaza tiempos, campos de verdad o cambios de umbral; **todavía no procesa ninguna medición real**. El workflow de preparación **no contiene** ninguna llamada OpenModelica ni proveedor. Una etapa de ejecución posterior deberá verificar completamente el CSV del mundo y su relación con el modelo original antes de invocar el evaluador.

**Estado de la hoja de ruta:** PT-07/R4-A **preparado**, R4 aún **no probado**. PT-06 cerrado; sin introducir nuevas estructuras, sin rediseñar ATMS, sin R4 independiente, sin Clef/Clairic.
