# A1 · 05 — PR #135: eventos POS → D/E1 originales → OpenModelica → H_j

**Fecha:** 2026-11-02. **Tipo:** corrección funcional de A1 conforme a revisión Astra del PR #135.  
**Dependencia:** PR #134 F0-HIST (no fusionado), PR #135 Draft. **Plan rector:** cafetería v3.2; no abrir F2/F3/G5.  
**Corrida nativa comprobada:** [GitHub Actions #41546648950](https://github.com/yudocyudoc/IGC/actions/runs/41546648950), commit `13fb39b9d13a96a1b382a583aa6fe5c4a6ca04e7`, doce trabajos PASS. El commit documental posterior se verifica por separado.  
**Origen:** datos EV01 **sintéticos**, no POS de un negocio real.

## 1. Corrección central de entrada

Anteriormente O0/O1 entregaban solo acumulados en t={0,2,4,6,8,10} minutos. Se había perdido una señal POS observable: cada evento público `pedido_creado` ya contiene `case_id` y `t_minutes_exact`. Ahora `scripts/arena_cafe/evidence.py` v0.2 preserva, **dentro del cutoff [0,10)**, exactamente esos pares; conserva también los agregados anteriores. El validador `native_handoff.validate_a1_visible` comprueba: allowlist de campos, IDs únicos, orden temporal, tiempo anterior al cutoff, paridad exacta en cada muestra y digest del snapshot visible.

**No sale:** configuración física `ev01.SPEC`, servidores, eventos o recursos de la etapa privada `transferencia_final`, otras condiciones ni eventos futuros. La proyección O1 mantiene sus agregados físicos autorizados de preparación, además de los mismos POS O0. Los adaptadores anteriores de `observation_ports.py` siguen siendo un **puerto agregado legado**, que no consume esos timestamps: esa diferencia está explicitada.

## 2. Entrada continua, sin falsa tasa observada

El nuevo `scripts/arena_cafe/native_pos_scenario.py` recibe solo el archivo público de UNA condición, no importa EV01 ni DES y construye un **escenario conservativo explícito**:

- Ventana [0,10) minutos; bins fijos predeclarados de 1/2 minuto.
- Cada pedido real observado en POS aporta una unidad de masa al bin que contiene su timestamp. Dicha masa se distribuye **uniformemente dentro de ese bin**, como una aproximación de simulación, no una inferencia de la tasa verdadera.
- 15 pedidos POS hasta el cutoff → **15 pedidos integrados** en ambos modelos. Las condiciones O0 y O1 comparten el mismo calendario público, por lo que los *inputs* de simulación y las curvas nativas son iguales: O1 añade una **medición para comparar**, no otro estímulo ni un parámetro calibrado.
- Se guardan bins exactos como racionales, unidades, evidencia, candidato, SHA256 del modelo, SHA256 del script del solver y marca del estado `NOT_ESTABLISHED` para calibración/identificación.

No hay ajuste de parámetros desde POS o desde los tiempos internos del evaluador. Los supuestos nominales de ingeniería se eligen **antes** de comparar salidas:

| Método | Topología y parámetros del ensayo de conectividad |
|---|---|
| **D** | Gramática original D, `topology(2, False)`, 2 stocks genéricos sin pérdidas. `capacity=20/60` pedidos/min, `response_time=30` min por etapa, `loss_time=30` min sin efecto al no tener pérdidas |
| **M** | Compositor + backend **originales** Short E1, registro base, topología mínima C00 de preparación y despacho. `maxThroughput=20` pedidos/h por etapa, `responseTime=0.5` h por etapa |

El hecho de que estas dos configuraciones compartan ecuaciones de cadena/capacidad nominal sirve de **control de paridad numérica**, no demuestra descubrimiento de mecanismos. Se sustituyen exclusivamente las expresiones de estímulo externo de los `.mo` que produjeron los métodos originales; no se alteran stocks, conexiones, ecuaciones moleculares, el compositor ni los archivos de fuentes originales.

## 3. Correcciones puntuales detectadas por Astra

**Discontinuidades de H_j.** `observation_eval._numeric_samples` conserva continuidad del stock y los lados izquierdo/derecho de tasas en tiempos duplicados. OpenModelica emitió **tres filas** en varios eventos de cambio de bin; el lector conserva la primera y última tasa, acepta repetición intermedia sin un segundo cambio, y la cuadratura integra desde la tasa derecha al inicio hasta la izquierda al final. Rechaza discontinuidad del stock, tiempos futuros, valores negativos y cambios de tasa repetidos no resueltos. El registro de la aproximación se preserva: las integrales se aproximan por trapecios; en estos CSV la reconstrucción por eventos coincide numéricamente con la masa permitida.

**Identidad M.** `observation_eval._candidate_roles` mantiene el SHA canónico estructural del compositor, **pero además exige igualdad íntegra con el AST original enumerado**, incluidos los parámetros. La prueba adversarial cambia `preparation.maxThroughput` de 20 a 21; conserva el mismo SHA de estructura, pero queda **rechazada**. Una futura calibración necesitará contrato de parámetros y procedencia propio; no se acepta una mutación silenciosa como candidato fijo.

**Trazabilidad de modelo y script.** Se cotejan SHA256 de los bytes `.mo` y `.mos` y la marca `INVOCATION_STARTED` con el código de salida 0; ambos comprobados en CI. La ejecución original de prueba reveló un error del manifiesto `.mos`, corregido y protegido con un test. También se eliminaron `loadModel` redundantes que producían mensajes de error pese a que la simulación terminaba exitosamente. Estos incidentes no se eliminaron del historial CI.

## 4. Resultado físico del control de conectividad, sin calibración

**Fuente medida:** 15 pedidos creados y **8 entregados** al minuto 10.  
**Escenario nominal:** 20 pedidos/h de capacidad por etapa y 30 min de tiempo de respuesta, hipótesis **NO medidas ni ajustadas**. Ambos modelos compilaron y produjeron CSV auténticos de OpenModelica DASSL 1.26.5 con 1026 filas, incluyendo instantes repetidos de eventos; el auditor independiente verificó conservación del material.

| Indicador al minuto 10 | D (2 stocks) | M (C00 E1) |
|---|---:|---:|
| Pedidos de entrada reconstruidos | 15.000000000003 | 15.000000000014 |
| Entregas acumuladas predichas | **0.3211608540** | **0.3211608558** |
| Entregas POS observadas | **8** | **8** |
| Residuo de entregas, predicho − observado | **−7.6788391460** | **−7.6788391442** |
| Máximo residuo conservación, pedidos | 3.19×10⁻¹² | 1.36×10⁻¹¹ |

En O1 el observador de preparación medía **9 servicios completados**; el flujo integrado `preparation.completed` del escenario M predijo **2.6188126009**. Esa comparación es **descriptiva**, además de sujeto a la distinta semántica de servicio discreto frente a flujo continuo. Los tiempos medios observados de espera y servicio aún **no** se mapean a parámetros/observables E1: hacerlo sin contrato equivaldría a asumir lo que se quiere probar.

**Interpretación:** la **conservación G2 de ingeniería pasa**, pero el escenario nominal está lejos de reproducir las entregas observadas. El parecido casi exacto de D y M surge del control de topologías y parámetros similares, no de una identificación convergente. No seleccionar ni retocar los parámetros usando este dato y después llamar al mismo contraste evidencia predictiva.

## 5. Procedencia verificable

Para cada uno de `D×O0`, `M×O0`, `D×O1`, `M×O1`, GitHub Actions ejecuta un trabajo independiente con *sparse checkout* sin `scripts/arena_cafe/ev01.py`, sin DES y con **una única condición pública**. Produce `native.mo`, `simulate.mos`, `manifest.json`, marcas de intento y salida del solver, `omc.log`, `native_res.csv`, `g2-report.json` y `hj.json`. Se conserva incluso el expediente de un fallo de solver.

Run que acreditó las 4 simulaciones y las 8 pruebas heredadas (12/12 jobs): [#41546648950](https://github.com/yudocyudoc/IGC/actions/runs/41546648950). Artefactos de las cuatro corridas y sus hashes están asociados al propio run. Los tests específicos incluyen fuga temporal, paridad POS, integridad de `.mo/.mos`, salto de tasa stock-continuo, rechazo de candidata M con hash estructural válido y parámetro modificado.

Una CI con commit y logs acredita ejecución verificable en el entorno configurado; **no acredita por sí sola un compromiso externo de mundo privado, ACL formal o origen empírico**.

## 6. Gates y límite de esta entrega

- `BASELINE-01`: expediente existente; pendientes de entorno conocidos explícitos.
- `EVIDENCE-01`: PASS en control sintético; POS individual preservado y conteos validados.
- `INTERFACE-01`: **avance de ingeniería**: D/M originales consumen la **reconstrucción POS** como estímulo y sus resultados se leen y comparan con H_j. No hay selección/calibración con O1, ni inferencia Buffalo live.
- `CONDITION-01`: PARTIAL; workers separados sin ACL completa de artifacts/cache/ledger.
- `MODEL-01`/F3: **NO COMPLETO**; la Arena con tres brazos y G0–G3 no se ejecutó. El G2 de estos dos controles nominales no lo sustituye.
- `MEMORY-01`: NOT_RUN, sin ATMS productivo.
- `F2 B0/B1/B2`: NOT_RUN, sin validación de recursos operativos.
- `F4–F7`, G4/G5 y cualquier evaluación futura: NO autorizados.

**Próximo trabajo real:** política **predeclarada de búsqueda de parámetros/candidatos** D y M desde construcción, con bandas y abstención; incorporación de observabilidad O1 sin confundir duración de servicio con tiempo de vaciado de stocks; memoria canónica con custodia por condición; F2 y F3 según plan v3.2. Buffalo live requeriría autorización separada. La evaluación ya conocida de CAF-01 no puede reabrirse ni puntuar otra vez como holdout independiente.
