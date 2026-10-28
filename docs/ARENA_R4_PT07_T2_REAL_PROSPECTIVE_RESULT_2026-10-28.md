# IGC · Arena R4-A / PT-07 — Primer contraste prospectivo T2 realmente ejecutado

**Fecha:** 2026-10-28 (UTC; campaña iniciada 2026-10-27). **Estado:** un ensayo prospectivo sintético intrafamilia ejecutado; no es validación independiente ni identificación causal. **Expediente:** PR #68.

## Pregunta congelada antes de medir

¿Se puede convertir la ambigüedad estructural de R3-T2 en una medición prospectiva que reduzca las estructuras compatibles, conservando al generador? En R3-T2 había **3 estructuras y 27 configuraciones compatibles** dentro de la ventana de construcción t=0–0.15 h. La estrategia R4-A (PR #67 ya fusionado) eligió **t = 1.0 hora** comparando únicamente las curvas de los 27 candidatos originales E1. Quedaron predeclarados y almacenados sus pronósticos, el tiempo elegido, el umbral de eliminación de **0.020 items** y la referencia **REF = persistencia del último dato en t=0.15**.

**Bloqueo verificable anterior a la medición:** certificado versionado en `data/diagnostics/ARENA_R4_PT07_T2_FROZEN_FORECAST_CERTIFICATE_20261027.json`, commit [e3b22a540928](https://github.com/yudocyudoc/IGC/commit/e3b22a540928f932617f2d70c278e8abf1e9e36f); SHA256 de bytes originales del `forecast-lock.json`: `94b1231c33f605cbca4efb81aa6a6f31883e628e4303eae9cbdbd53eb78811d8`. Evidencia original del lock: [Actions #40614473892](https://github.com/yudocyudoc/IGC/actions/runs/40614473892). El resultado futuro era aún desconocido en ese corte.

## Ejecución física con presupuesto único

Autorizada por el usuario **una nueva simulación OpenModelica, ningún candidato nuevo ni llamadas a IA, sin reintentos**. Ejecutada [Actions #40618493022](https://github.com/yudocyudoc/IGC/actions/runs/40618493022) por una compuerta de un solo uso (solo adición original del marcador, `GITHUB_RUN_ATTEMPT=1`). El programa `one-world.mos` contiene exactamente **un** `simulate()` de `ArenaR3T23Worlds.R3T2World`, usando E1 original, MSL 4.0.0, SystemDynamics 2.1.2 y OpenModelica 1.26.5 DASSL. Se simularon t=0–1 h a paso de salida 0.00125 h, sin t>1 ni una trayectoria independiente del catálogo.

Los bytes del paquete generador fueron verificados contra el original de [R3-T2, Actions #40582633807](https://github.com/yudocyudoc/IGC/actions/runs/40582633807). **Los cuatro valores anteriores t={0,0.05,0.10,0.15} se reprodujeron con discrepancia absoluta máxima 0.0 items**. El nuevo CSV verificó balances G2; se extrajo únicamente el valor físico solicitado en t=1.0 h.

## Resultado medido y pronóstico sellado

Medición física sintética nueva, t=1 hora: **`deliveredTotal=0.07506397335646263 items`**.

| Indicador | Valor (items) |
|---|---:|
| Predicción agregada R4 (mediana de medianas estructurales, congelada) | 0.06711172531961446 |
| Observación recién medida (única) | **0.07506397335646263** |
| Error absoluto R4 | **0.007952248036848172** |
| REF persistencia t=0.15 (congelada) | 0.00007814994299197591 |
| Error absoluto REF | **0.07498582341347065** |

**R4 superó a REF en error absoluto en este caso único.** No se cambió el pronóstico al recibir el valor real, ni se reestimó un parámetro.

Al aplicar a **cada una de las 27 predicciones congeladas** la regla `|pronóstico−observación| ≤ 0.020 items`, sobrevivieron **tres configuraciones, todas de C01**. El conjunto estructural pasó de **{C00,C01,C02}** a **{C01}**. El selector guardó esta decisión **antes** de que la adjudicación sintética revelara que el mundo generador era precisamente **C01**, y quedó constatado que la estructura fuente se conserva.

## Qué demuestra y qué no

Este es un resultado positivo **de procedimiento predictivo dentro de un universo sintético compartido**: una medición elegida por los modelos y posterior al sello permitió disminuir ambigüedad de tres estructuras a una, y una predicción agregada tuvo menor error absoluto que la referencia simple. La persistencia de tres configuraciones C01 muestra que la estructura única **no implica parámetros únicos**.

No se demostró identificación causal, mecanismo nuevo, victoria general de R4 sobre REF, robustez fuera del repertorio, ni poder predictivo independiente del generador que diseñamos. La separación entre mundo generador y selector es de protocolo, **no cegamiento técnico absoluto**. El corte de 0.020 items es un **criterio operacional predeclarado, no precisión instrumental**. El generador comparte física/biblioteca con las estructuras candidatas; este resultado no equivale a validación sobre datos reales.

**Evidencia original:** [Actions #40618493022](https://github.com/yudocyudoc/IGC/actions/runs/40618493022), archivo de programa, paquete Modelica, CSV nuevo, `omc.log`, fuente física privada, observación pública, decisión bloqueada y adjudicación posterior.

**Auditoría separada:** [Actions #40618707472](https://github.com/yudocyudoc/IGC/actions/runs/40618707472); volvió a verificar hashes, fuente nativa, G2, mediciones tempranas, el pronóstico anterior a la nueva respuesta, REF, tres configuraciones sobrevivientes y la adjudicación, **con 0 simulaciones y 0 proveedores nuevos**.

**Continuidad del plan:** R4-A/T2 es **un primer contraste favorable ya ejecutado**, no cierre de la validez predictiva general de PT-07. Cualquier nuevo ensayo o expansión del campo experimental debe pasar por su propio protocolo y presupuesto; no se ha iniciado REF como brazo complejo, ni Clef ni Clairic, ni se han modificado D/B/M, R3 o ATMS.
