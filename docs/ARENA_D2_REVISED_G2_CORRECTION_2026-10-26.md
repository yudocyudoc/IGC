# Arena D2 — cierre de G2 para los MODELOS REVISADOS del propio brazo D

**Fecha:** 2026-10-26. **Corrección al dictamen Astra del 26/10/2026.** **Rama:** `fix/arena-d2-revised-modelica-g2-20261026`, apilada sobre el PR #23 (`feature/arena-d-pure-stockflow-v01`). **No se cambia main, ni el evaluador, ni D0/D1/D2, ni Buffalo, ni el brazo molecular.**

## Defecto confirmado y solución

D2 ya registraba `revised_best_parameters`, estatus de compatibilidad y nuevos soportes ATMS después de recibir una observación sintética de otro ensayo con reinicio. Pero su workflow solo simulaba el `D2IndependentWorld` que proporcionaba la nueva medición: **esa simulación no ejecutaba ningún candidato revisado por D2**.

La nueva ruta añade **únicamente** una capa explícita D2→Modelo D original→OpenModelica:

1. Recupera [el paquete real D-only #12619352557](https://github.com/yudocyudoc/IGC/actions/runs/40248817463/artifacts/12619352557) de [Actions #40248817463](https://github.com/yudocyudoc/IGC/actions/runs/40248817463); no descarga el paquete `arena-d-v2-evaluator-only-synthetic-world`. Verifica el SHA-256 de bytes de `screen.json`, `d2-revision.json`, `d2-trial-visible.json` y `memory-events.json`.
2. Reconstruye el D1 anterior con `assess`, verifica D0/D1/D2, fuente, paquete de medición, `event_hash`/parent-event, soporte D2 y resultado del ATMS. El paquete entregado a D no contiene ecuaciones del evaluador.
3. Para **cada uno de los seis candidatos originales**, conserva el mismo `structure_hash` y grafo D0, pero emite Modelica con los **`revised_best_parameters` de D2**; no reutiliza indiscriminadamente `best_grid` D1 ni el nominal original. La función de generación es `scripts/arena_d_v01.modelica` original. Se generan `D2fit_*.mo`, `manifest.json`, `d2.mos`.
4. Compila/simula las **seis** revisiones en el OpenModelica fijado de D1, versión `v1.27.1-minimal` digest `sha256:ac9a0223...`, horizonte 0–8 h, 160 intervalos, DASSL.
5. A cada CSV **real**, aplica la verificación original de conservación `D0.verify_csv` (stocks + entregado + perdido = integral del pulso), compara con el integrador D1 RK4 (`compare_omc_csv`, tolerancia 0.012) y calcula RMSE de construcción con/sin t=0. La nueva medición de t=8 es un **ensayo visible** sobre el mismo pulso con reinicio, y el máximo residuo conjunto se informa sin llamarlo reserva ciega.
6. Los resultados de soporte son **condicionados** a la rejilla y cota instrumental ±0.20. Una comprobación adicional exige que el máximo residuo del CSV OpenModelica (con margen numérico ≤0.012) coincida con la etiqueta condicional que D2 registró en su memoria. No borra topologías sin testigos: `UNRESOLVED_GRID_NOT_FALSIFIED` permanece.

El nuevo script `scripts/arena_d2_revised_g2.py` y su CI **no** modifican el historial D2 ya persistido. Ofrecen una reproducción real del modelo revisado, con artefacto, hashes de Modelica, CSV, balance y paridad; las comprobaciones negativas prueban contaminación de brazo, cambios de parámetros/topología y archivos manipulados.

## Resultado de OpenModelica — primera corrida completa

[Actions #40284519574](https://github.com/yudocyudoc/IGC/actions/runs/40284519574), artifact [#12633279593](https://github.com/yudocyudoc/IGC/actions/runs/40284519574/artifacts/12633279593): **SUCCESS**, seis Modelica revisados simulados, seis balances G2 PASS y seis paridades D-RK4/OpenModelica PASS. La compuerta adicional de consistencia soporte/CSV fue incorporada posteriormente y requiere verificación por CI del commit siguiente.

| Candidato revisado | Stocks | Pérdida | Capacidad | Tau | RMSE construcción n=4 | RMSE construcción n=3 |
|---|---:|---|---:|---:|---:|---:|
| `D-1b03f4d80336` (único soporte D2) | 2 | No | 2.0 | 1.0 | **0.150205** | **0.173442** |
| `D-5bc57655500f` | 1 | Sí | 1.2 | 1.0 | 0.379304 | 0.437983 |
| `D-5f8781847cb6` | 1 | No | 1.2 | 1.5 | 0.295471 | 0.341181 |
| `D-9a46b6a3ba32` | 3 | No | 1.2 | 0.5 | 0.248249 | 0.286653 |
| `D-b4030cf49cc3` | 3 | Sí | 1.2 | 0.5 | 0.167122 | 0.192976 |
| `D-ba433938dfc8` | 2 | Sí | 1.2 | 0.5 | 0.316624 | 0.365605 |

**Dato crucial:** el único candidato que conserva soporte D2, `D-1b03f4d80336`, **no cambió** sus parámetros de D1 a D2; su soporte se redujo por el nuevo ensayo que discrimina entre modelos. Otros candidatos sí cambiaron parámetros, pero quedaron sin testigo bajo la rejilla. No decir que el ajuste mejoró en el candidato superviviente; aquí la capacidad demostrada es **ejecutar realmente sus propios modelos revisados y corroborar su evaluación condicional**.

El candidato D2 de dos stocks, sin pérdida, `capacidad=2` y `tau=1`, coincide prácticamente con la dinámica publicada para M2 bajo este pulso: a las horas t=1,2,4 produce la misma curva dentro de la precisión del solver. Sus RMSE publicados eran aparentemente distintos por una diferencia de denominador (D n=4, M n=3). Esta coincidencia **no** demuestra equivalencia general de métodos ni discriminación estructural: ambas capacidades permanecen inactivas en el ensayo.

## Estados honestos y próximos límites

| Concepto | Estado |
|---|---|
| D2→propio Modelica→simulación | **PASS** en seis revisiones |
| Paridad D-RK4/OpenModelica | PASS, tolerancia acotada |
| Conservación stock/entregado/perdido | PASS, CSV de OpenModelica real |
| G3 construcción | Solo compatibilidad condicional a cota sintética ±0.20, no identificación causal |
| Nuevo ensayo t=8 | Evidencia visible usada para revisar; NO holdout de validación después de revisión |
| G3 reservada | **No es la nomenclatura correcta**: evaluación reservada aparte, NOT_RUN |
| ATMS | Mantiene soportes condicionales/historia D1→D2, no demuestra veracidad |
| Inferencia fuera de gramática fija | NOT_DEMONSTRATED |

Quedan como **correcciones posteriores**, y no se adelantan aquí: feedback de residuos físicos al motor Buffalo original; selección estructural del brazo molecular guiada por evidencia; estímulo D/M que active saturación; cotejo G0 de semántica nativa Buffalo y ronda con protocolos de evaluación/solvers equiparados.

**Procedencia:** [PR #23 D original](https://github.com/yudocyudoc/IGC/pull/23), [revisión Astra adjunta 2026-10-26] (informe recibido por el investigador), [PR #32](https://github.com/yudocyudoc/IGC/pull/32).
