# RF-01 · METHOD_ENTRYPOINT_MATRIX, autoría y evidencia (R1)

**Rol de este documento:** enumera capacidades y entradas auténticas; no crea funciones nuevas. Registros de referencias: `tests/test_arena_native_provenance.py` y [F0_FIDELITY_BASELINE.json](F0_FIDELITY_BASELINE.json). R1 permaneció **PARTIAL según Astra** en el corte `da4ec9f`: esta enmienda propone su corrección y requiere revisión nueva para cerrarse. `CI PASS` no sustituye dictamen.

| Componente | Método / función que existe | Ejecutado sobre O0/O1 con datos POS | Método con candidato libre para EV-01 | Parámetros y estructura elegidos por quién |
|---|---|---|---|---|
| D | `scripts/arena_d_v01.py::validate_case → generate`, `topology`, `lint_structure`, `modelica` | **No:** `validate_case` rechaza falta de pulso y nominal | **NO**. En entrada original válida enumera 1–3 stocks, con/sin pérdida, máximo 6 según presupuesto | **Pista I:** Arena elige D2 sin pérdidas y parámetros 20/h, 0.5 h a partir del registro E1. **Pista II:** ninguna selección |
| Buffalo | `UB-IAD/sd-ai@5199f7b...`, `Engine.generate → QuantitativeEngineBrain.generateModel`, con `scripts/arena_b_openrouter_cloudflare.mjs` | **Mock offline:** entrypoint de motor sí, inferencia LLM auténtica NO | **NO para EV-01**. R1/R2 históricos sí generaron modelos con GLM-5.3-Flash; fuentes/cutoffs diferentes | Solo el LLM podría generar nuevos stocks/flujos/ecuaciones. No hay propuesta EV-01 live |
| Moléculas | `scripts/arena_m_short_e1.py::prepare → experiments/e1/composer.py::enumerate_graphs`; `backend.render_model` para grafos tipados | **Enumera base 6: componente E1 completo para su capacidad enumeradora.** M0 registra abstención de elección, no falta del enumerador. No calibra con POS | **NO** en Pista II; M0 `UNRESOLVED`. **Pista I:** `choose_one` toma el grafo mínimo | **Pista I:** Arena prioriza C00; base E1 ya fija roles `source,preparation,dispatch,receipt`, 20/h, responseTime 0.5h. No son descubrimientos sobre mundo físico |

## El contrato original sí importa

**D:** `generate` requiere `construction.input_profile.kind="pulse"`, `nominal_parameters` numéricos y `observations[{t,delivered}]`. POS por timestamps discretos no cumple. Reemplazar el problema por un pulso o imponer valores nominales es un nuevo supuesto experimental, no el funcionamiento de D sobre el dato original. Para R2 hay **tres rutas distintas**: **D-A** mantiene D estricto, rechaza EV-01 y verifica conformidad sobre un fixture válido separado; **D-B** requiere RFC y una extensión D-POS versionada; **D-C** es un experimento nuevo con pulso conocido y protocolo propio. D-A no reemplaza EV-01, D-C no es un test de conformidad y ninguna ruta se autoriza sin decisión del investigador.

**Buffalo:** el upstream original admite `backgroundKnowledge`, `problemStatement`, `currentModel` para revisiones. `supportsArrays/supportsModules/supportsSubTypes=false` aparecen apagados de forma predeterminada en la versión fijada; no se califican como alteración causada por la Arena. Una petición en modo offline, incluso con prompt distinto, demuestra **transporte**, no razonamiento ni candidata nativa real. El puente está congelado, sin modificación y con 3500 tokens de salida en este modo inicial. El traductor histórico usa 0–8 h; se requiere contrato EV-01 0–10 min aparte, sin tocar ecuaciones.

**Moléculas:** el compositor Short E1 forma grafos por tipos y restricciones de su catálogo E0; el backend renderiza instancias y conexiones, no nuevas ODE. El original permite enumerar seis grafos en `registry.base.json` y quince en `registry.extended.json` según los límites fijados. El registro base **ya obliga** los roles de preparación y despacho; jamás llamarlos «etapas físicas descubiertas». La selección simplificadora de `scripts/arena_m_visible_pulse.py::choose_one` es un prior del controlador y pertenece a Pista I.

## Puertos y uso por condición

| Fuente visible | O0 | O1 | Estado para Pista II |
|---|---|---|---|
| POS timestamps `pos_arrival_events` | Sí | Sí | D requiere extensión/control de estímulo. B solo ha visto mock; M enumerador no utiliza timestamps para seleccionar |
| POS `orders_created_cumulative` | Sí | Sí | `observation_ports.py` define operador de integración, no prueba de selección por D/M |
| POS `delivered_cumulative` | Sí | Sí | Observable para `H_j`; falta política G3 predeclarada |
| `physical_observation` preparación completada | No | Sí | Censura por completados; un servicio físico discreto no se iguala automáticamente a integral de flujo E1 |
| Medias de espera y servicio preparatorio | No | Sí | Sin operador semántico equivalente establecido para D/M/B |
| FULL, configuración DES, `transferencia_final`, recursos individuales y futuro | **NO** | **NO** | Evaluador solamente; nunca se promueven a dato compartido |

En EV-01 se publicaron 15 eventos POS de **creación de pedidos** antes de los 10 minutos, no 15 eventos del log POS completo. La igualdad de resultados D/M entre O0 y O1 en Pista I **no** implica que los métodos consumieron correctamente O1. Tampoco se requiere que una inferencia verdadera de Pista II cambie de salida si recibe más información; se exige traza de campo → operación interna o rechazo documentado.

## Autoría de las lecturas y alcance de las pruebas

El manifiesto tipado v1.1 distingue `adapter_fields_read`, `native_fields_read` y `transport_fields_submitted`. Para D, `observation_ports.d_port` usa la serie como **restricción del adaptador**, mientras `arena_d_v01.validate_case` rechaza la forma de entrada: **D.generate no leyó ni utilizó esas observaciones**. En M, el adaptador crea operadores de observación (y en O1 lee el agregado de preparación); el compositor E1 enumera desde el registro fijo. En B, los campos fueron preparados/transportados en un prompt mock, lo cual no demuestra uso cognitivo del LLM.

Cada operación tipada registra actor, operación, estado y nivel de evidencia de código y recibos. El verificador de RF-01 impide que una mutación individual atribuya al motor una lectura/selección no acreditada. No sustituye trazas instrumentadas de uso causal de información ni tests OS/ACL, reservados a R6.

La pista PARITY **no reabre** cuatro CSV para rehacer sus hashes: referencia un **reporte F3 previamente autenticado** del run fijo `41575917332`, artefacto `13202639585`. Se añade `source_native_csv_rehashed_this_rf01_run=false` para evitar una afirmación engañosa.

## Estados aceptados y propietarios de decisión

- `BLOCKED_BEFORE_RUN`: entrada incompatible o proveedor no autorizado; **no cuenta** como ejecución científica.
- `METHOD_ABSTAINED` de M0: señal de **su wrapper acotado**; el componente `E1.enumerate_graphs` completó su universo base, pero no posee un selector/calibrador observacional acreditado. Se mantiene `native_component_execution_complete=true`, `arena_task_complete=false` y no se exige crear capacidad que el motor original no tiene.
- `ARENA_POLICY`: candidato seleccionado externamente; se registra, puede ser control de paridad, **nunca** `NATIVE_METHOD` como autor de decisión.
- `COMPLETED_METHOD`: requiere evidencia de entrada auténtica al generador original, productos genuinos y vínculo de datos, **ausente** para EV-01 en este corte.
- `G2_PASS` es conservación/simulador; **no** habilita `G3_PASS` o selección si no se han aprobado equivalencia semántica, observables, protocolo y ámbito de modelo.

**Reglas de ruptura:** si una candidata D2 aparece como salida de D.generate sobre POS sin generar seis alternativas, si M se atribuye C00, si Buffalo mock se etiqueta live, o si un test promueve G3 por la presencia de CSV, RF-01 FAIL.

**Estado siguiente:** RF-02 precisa decisión científica y revisión independiente RF-01; no altera `main`, no abre evaluación de reserva y no consume Cloudflare.
