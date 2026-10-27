# Arena M2 — ejecución real, revisión molecular por feedback propio

**Ejecución adjudicable:** [GitHub Actions #40273515543](https://github.com/yudocyudoc/IGC/actions/runs/40273515543) — SUCCESS. Artefacto [#12628124619](https://github.com/yudocyudoc/IGC/actions/runs/40273515543/artifacts/12628124619). SHA del commit ejecutado: `eb3210611e150146dee7e88958852c043a63c83f`. Fecha UTC: 2026-10-26.

**Resultado:** `M2_CONSTRUCTION_RMSE_IMPROVED` (reducción sobre los **mismos datos de construcción** de M1). G2 PASS, conservación PASS, topología idéntica; G3 de reserva NOT_RUN; no es identificación causal.

## Encadenamiento M1 → feedback → M2

| Campo | Observado en artefactos |
|---|---|
| M1 anterior | `M-f250c7b99b2c:r0` |
| Salida original M1 | [Actions #40271768284](https://github.com/yudocyudoc/IGC/actions/runs/40271768284) |
| Hash nativo M1 | `sha256:e5ac7877243c8cd7a5b0addbfe66e55fb2853f2e1a6cfd3e3bece69194dc6ce0` |
| M2 actual | `M-f250c7b99b2c:r1` |
| Hash nativo M2 | `sha256:d226cc4930b2c3ebef53c93ace1ce0c63b939bcdb26ef27485d6efa7e3a67fa1` |
| Topología canónica | `sha256:f250c7b99b2c33c53c2df542d1ba0137adcc5544b77f098003fbacf11b84bb6e`, **sin cambios** |
| Propuesta de parámetros | `preparation0.responseTime: 0.5 → 1.0 h`; `dispatch0.responseTime: 0.5 → 1.0 h` |
| Capacidad | `maxThroughput=20 items/hour` en ambas colas; sin cambios |
| Lógica | `LATE_OVERSHOOT_BOTH_POINTS_DOUBLE_SHARED_RESPONSE_TIME_ONCE` |
| Nuevas simulaciones Modelica | Exactamente una |
| LLM/Cloudflare | Ninguna llamada |

La política estaba **fijada antes de correr M2** en código y en [ARENA_M2_OWN_FEEDBACK_EXPERIMENT.md](ARENA_M2_OWN_FEEDBACK_EXPERIMENT.md). El paso ocurrió porque M1 sobreestimó las entregas en t=2 (0.6934 items) y t=4 (0.8094 items), ambas sobre el umbral 0.1. La regla duplicó los dos tiempos de respuesta por igual, respetando los límites del catálogo E1 `0.1–5 h`. No optimizó ni seleccionó otra estructura entre las seis del catálogo.

El replay comprobó el SHA256 **de bytes** de `native-graph.json`, `submission.json`, `memory-event.json`, `g2-construction-report.json` y `m-visible_res.csv` M1. Reprodujo también el reporte de observaciones desde el CSV real y el hash del modelo y evento anterior. El feedback es exclusivo del brazo M; conserva `G2=PASS`, `G3=PARTIAL` (construcción, no reserva). Los eventos `FEEDBACK_DELIVERED` y `HYPOTHESIS_REVISED` están encadenados por hashes, pero **no constituyen ATMS completo**.

## Resultados sobre las observaciones de construcción

| Hora | Observado items | M1 predijo | M2 predijo | M1−obs | M2−obs |
|---:|---:|---:|---:|---:|---:|
| 0 | 0.000000 | 0.000000 | 0.000000 | +0.000000 | +0.000000 |
| 1 | 0.350000 | 0.460140 | 0.176185 | +0.110140 | −0.173815 |
| 2 | 1.100000 | 1.793410 | 0.920280 | +0.693410 | −0.179720 |
| 4 | 2.500000 | 3.309442 | 2.666540 | +0.809442 | +0.166540 |

**RMSE t=1,2,4:** M1 `0.6186392941375638 items` → M2 `0.17344197594789604 items`. Cambio `−0.4451973181896678 items`, reducción relativa `71.96 %`. Estas cifras provienen del **CSV real OpenModelica**, no de la heurística ni de una fórmula Python que reemplace el solver.

M2 ya no sobreestima las horas 1–2: ahora las **subestima**; a t4 sigue sobreestimando ligeramente. Por tanto mejora el criterio global de RMSE en construcción, **pero no elimina las discrepancias ni identifica mecanismos únicos**.

El resultado M2 tiene 81 muestras temporales únicas; el residuo máximo de conservación global, reconstruido desde stocks materiales `preparation0.waiting + dispatch0.waiting + deliveredTotal`, es `6.825207066185612e-12 items`. La simulación y verificación numérica independiente pasaron.

## Puertas de adjudicación

| Puerta | Veredicto |
|---|---|
| Identidad del modelo y cinco archivos M1 | PASS, con hashes y reconstrucción |
| Independencia D/B | Procedimiento M solo, sin importar mecanismos o resultados de otros brazos; aislamiento lógico, no certificación ACL |
| Generador molecular Short E1 | Original sin modificación; backend original renderiza M2 |
| G0 de estructura y puertos | Topología intacta, cambio explícito de parámetros; mapeo semántico Order/Shipment aún PROVISIONAL |
| G1 acotado | Contratos y reconstrucción numérica de conservación PASS, no certificado dimensional general |
| G2 OpenModelica | PASS |
| Cambio de RMSE sobre construcción | Mejora 0.619→0.173, condicionada a mismos datos |
| Identificabilidad estructural y paramétrica | NOT_DEMONSTRATED |
| G3 predictivo sobre reserva | NOT_RUN |
| ATMS productivo | NOT_IMPLEMENTED; ledger elemental trazable |
| Evaluación equitativa D/B/M | NOT_RUN: grados de libertad, condiciones y presupuestos aún no equiparados |

## Qué implica

Este experimento demuestra una capacidad técnica concreta: **el brazo molecular puede recibir el diagnóstico de su versión anterior, producir una revisión nativa limitada y ejecutarla en OpenModelica sin modificar su biblioteca de moléculas, su topología ni las propuestas de los otros brazos**.

No demuestra que los valores `responseTime=1 h` sean verdad, que el mecanismo real contenga precisamente esas dos colas o que M2 predecirá mejor otro estímulo. Un futuro ensayo de predicción genuina necesitará un nuevo pulso, nuevas observaciones bajo custodia separada y un sello anterior a su apertura; no reciclar el pulso de construcción.

PRs M0 [#27](https://github.com/yudocyudoc/IGC/pull/27), M1 [#28](https://github.com/yudocyudoc/IGC/pull/28), M2 [#29](https://github.com/yudocyudoc/IGC/pull/29) siguen apilados y Draft, sin merge automático a `main`.
