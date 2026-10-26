# Arena Buffalo B5 — autocorrección de discrepancia entre explicación y simulación

**Fecha:** 2026-10-26. **Estado:** inferencia real y simulación real completadas, [Actions #40419170895](https://github.com/yudocyudoc/IGC/actions/runs/40419170895) **SUCCESS**. Una llamada REAL adicional a `@cf/zai-org/glm-5.3-flash` mediante el motor cuantitativo original `UB-IAD/sd-ai@5199f7b`; no se modifica upstream ni se funde B4 con un experimento posterior.

## Diseño y límite de la pista

B4 fue negativo: [B4 #40393509770](https://github.com/yudocyudoc/IGC/actions/runs/40393509770) generó una rampa de capacidad que empeoró su RMSE a 0.4200698983. Astra observó además que B4 **anticipó verbalmente** entregas cercanas a 0.35, 1.05 y 2.45 items, mientras su propia simulación condicionada a lookup lineal/Euler produjo 0.218986, 0.645549 y 1.947111.

B5 recibe exactamente el mismo archivo nativo B4 como `currentModel`, su explicación textual completa `supportingInfo.explanation`, las observaciones de construcción originales, las tres predicciones de su explicación y **las tres entregas efectivas que produjo el propio modelo**. El feedback:
- No incluye análisis de Astra, ni nombre de la rampa como fallo, ni la identidad de la ecuación sospechosa, ni B2/B3 como respuestas candidatas.
- No incluye datos de reserva ni de otros brazos.
- Autoriza cambiar la explicación, cambiar el modelo o abstenerse. La solicitud **no instruye** eliminar el cuadrado de utilización.
- Autentica por SHA-256 B4 `c3662f90d7fb7a6211b62f35e13739000d2f6b90bcbb6d44cabc131dd45e7bbb` y su G2 B4 `2e97c1f7d87d75c3c91649c340d97c6ff0557bfcc30a1456f1d4bda6cd9e3533`.
- Guarda `b5-user-prompt-exact.json`, el request metadata, respuesta Cloudflare cruda, salida nativa, recibo y modelo ejecutado en un artefacto. Se conservó antes de evaluar físicamente.

**Evidencia original [#12696426738](https://github.com/yudocyudoc/IGC/actions/runs/40419170895/artifacts/12696426738)**, archivo completo con OpenModelica [#12696416795](https://github.com/yudocyudoc/IGC/actions/runs/40419170895/artifacts/12696416795). Recibo: 1 sola llamada HTTP del proveedor, `b5_feedback_seen=true`, `current_model_seen=true`, salida cruda preservada. SHA nativo B5: `ddb92a7cb3c73f6f9861282addce948dcf67587a50f12b3c2140a8fda8231dec`.

## Qué corrigió realmente Buffalo sin la pista explícita

Buffalo B5 informó en su propia explicación que reconoció que su modelo anterior no generaba las entregas anticipadas. Identificó:
1. **Utilización duplicada:** `completions = completion_capacity × capacity_utilization`, mientras `completion_capacity = nominal_capacity × capacity_utilization × capacity_ramp`.
2. Cambió la primera ecuación por **`completions = completion_capacity`**, de modo que la utilización se aplica una sola vez.
3. Cambió los puntos de `capacity ramp` para alcanzar 1 desde t=**1.5 h**, en lugar de t=3. Conservó `nominal capacity=0.7`.

La revisión conserva 16 variables y presenta 19 relaciones; las variables endógenas modificadas fueron `capacity ramp` y `completions`. Es una revisión mecanística autónoma, no un cambio meramente retórico.

## Lo que hizo al ejecutarse su modelo realmente

`G0=TRANSLATED_CONDITIONALLY_LOOKUPS_REQUIRE_EQUIVALENCE_CHECK`, `G2=PASS_REAL_OPENMODELICA_OWN_CANDIDATE`. Consistencia con el motor Buffalo original para lookups sigue sin certificarse.

| Tiempo h | Observado | B4, antes de autocorregir | B5, autocorregido |
|---:|---:|---:|---:|
| 1 | 0.350000 | 0.218986 | **0.235920** |
| 2 | 1.100000 | 0.645549 | **0.826545** |
| 4 | 2.500000 | 1.947111 | **2.226545** |

RMSE de construcción `n=3`:
- **B2:** `0.192904719`.
- **B3 (con pista):** `0.177423951`.
- **B4 (sin pista):** `0.420069898`.
- **B5 (autocorrección de B4):** `0.232787135`, reducción del **44.58 %** frente a B4, pero todavía peor que B2 y B3.

B5 todavía **anticipa verbalmente** aproximadamente 0.35, 0.95–1.0 y 2.35–2.4, pero produce 0.236, 0.827 y 2.227. Su nueva explicación de comportamiento sigue siendo demasiado optimista y conserva residuos negativos sobre todas las mediciones no iniciales. **No declarar ciclo epistemológico cerrado como éxito pleno.**

La tasa entre t=1 y t=2 fue 0.590625 items/h contra los 0.75 items/h observados. Una capacidad nominal 0.7 con multiplicadores limitados a 1 no puede reproducir exactamente este incremento si se asume cero error, aunque la inferencia causal queda indeterminada sin una cota del error instrumental.

## Veredicto científico y próximos pasos

- **PASS capacidad:** B5 encontró y corrigió la doble utilización sin que se le señalara la ecuación ni se le devolviera el cálculo de Astra.
- **PASS físico restringido:** las ecuaciones revisadas compilan y la adecuación de construcción mejora respecto a su propia B4.
- **FAIL calidad suficiente:** el modelo aún es peor que B2/B3 y sus promesas numéricas no concuerdan con el CSV. Tampoco demuestra cuál formulación causal es verdadera.
- **No holdout:** se usaron los mismos tiempos de construcción, ni estimación de fiabilidad estadística de múltiples corridas, ni paridad completa de lookups Buffalo.
- **La arquitectura no requiere un nuevo generador.** Próxima necesidad: un revisor físico que señale la distancia explicación→comportamiento y controle sus consecuencias antes de aceptar revisión como mejora.

**Estado:** PR #40 draft. B4 queda inalterado como resultado negativo histórico; B5 es su siguiente revisión, no una reescritura del primer ensayo.
