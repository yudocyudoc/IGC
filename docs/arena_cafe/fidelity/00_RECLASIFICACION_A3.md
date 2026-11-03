# RF-01 · Reclasificación obligatoria de A3 (R0–R1)

**Fecha:** 2026-11-02. **Contrato rector:** `PLAN_ACCION_CORRECCION_FIDELIDAD_ARENA_IGC_V1_2026-11-02.md`, §§0–3 R0/R1.  
**Baseline auditable:** [F0_FIDELITY_BASELINE.json](F0_FIDELITY_BASELINE.json), corte PR #137 `589a4b8604753b8ab5d0adf3f0606f6c30ae6e45`.  
**Código de verificación:** `scripts/arena_cafe/method_fidelity_manifest.py`.  
**Estado:** IMPLEMENTACIÓN DE R0–R1; firma del revisor independiente **PENDIENTE**. **A3 = PARTIAL**. El workflow definitivo RF-01 **no** ejecuta ni generador DES, ni motor/solver, ni proveedor: lee exclusivamente los artefactos inmutables de [A1/A3 run #41575917332](https://github.com/yudocyudoc/IGC/actions/runs/41575917332).  
**Ramas:** nuevo PR apilado encima de #137, sin fusión a `main`, sin tocar #134–137 retrospectivamente.

## 1. Hallazgo vinculante

La presencia de un fichero `native.mo`, un CSV OpenModelica auténtico o un hash de fuente original no acredita una ejecución del **método completo**. En A3 se usaron funciones originales para crear un control de equivalencia cuyos candidatos y parámetros eligió el controlador. Se preserva la legitimidad de la simulación, pero se retira de la categoría de evaluación metodológica independiente.

El nuevo expediente genera dos pistas **lógicamente separadas** en el reporte JSON (no dos repositorios o sistemas de permisos separados):

| Pista | Alcance autenticado | Actor de selección | Veredicto |
|---|---|---|---|
| `PARITY_BENCHMARK_D2_EQUIVALENT_E1_C00` | Clasificación del **reporte F3 preexistente**, que verificó cuatro CSV reales D/M × O0/O1; **RF-01 no descarga ni rehashea los CSV originales** | **ARENA_POLICY**: D `topology(2,False)`; M `choose_one(minimal)` | **PARITY_ONLY; NO competitiva**, sin convergencia de métodos |
| `NATIVE_METHOD` | Seis workers D/B/M × O0/O1 y SQLite originales; sin nueva inferencia | **NONE** en construcción nativa EV-01 | Ningún brazo ejecutó su ruta generadora completa para este caso |

**Punto de independencia:** los parámetros de D en Pista I fueron deliberadamente fijados de acuerdo con E1. La columna `cross_arm_prior_imports` lo registra, y un test rechaza su ocultación. D/M casi idénticos no son evidencia de descubrimiento independiente.

## 2. Seis resultados históricos EV-01 clasificados sin promoción de estados

| Brazo | O0 | O1 | ¿Qué se ejecutó y qué falta? |
|---|---|---|---|
| D | `BLOCKED_BEFORE_RUN` | `BLOCKED_BEFORE_RUN` | `D.validate_case` original rechazó entrada POS sin pulso/nominal; `D.generate` no ejecutado en ruta de hipótesis de EV-01. La topología D2 en Pista I es elección Arena |
| Buffalo | `BLOCKED_BEFORE_RUN` | `BLOCKED_BEFORE_RUN` | Se invocó transporte/motor SD-AI original con **mock**, 0 inferencias Cloudflare para EV-01. Las llamadas reales históricas R1/R2 no son estas ejecuciones |
| Moléculas | `METHOD_ABSTAINED` (solo **M0 Bridge**) | `METHOD_ABSTAINED` (solo **M0 Bridge**) | `E1.enumerate_graphs` original sí produjo los 6 grafos base y M0 declaró `candidate_selection=UNRESOLVED`; **NO** significa que Short E1 haya seleccionado o validado un modelo nativo para EV-01 |

`METHOD_ABSTAINED` de M0 indica que el **wrapper** no selecciona una hipótesis; el **componente enumerador original sí completó** sus seis composiciones permitidas. El nuevo esquema distingue `native_component_execution_complete=true` (M), `arena_task_complete=false` y `method_route_complete=false`: no se exige fabricar un selector que E1 no posee. Una abstención genuina tras recorrer la capacidad propia puede ser una salida válida, sin que por sí sola cierre todas las tareas exigidas por A3. Los seis `g0/g1/g2/g3` permanecen `NOT_RUN_NATIVE_METHOD`, aunque la pista separada de ingeniería haya aprobado `G2`.

## 3. Pruebas de seguridad metodológica

El validador comprueba los blobs nativos fijados en el baseline F0 y la regresión independiente `tests/test_arena_native_provenance.py`; identifica y enlaza contenido mediante hashes, **no son firmas criptográficas de autoría**. No actualiza SHA a posteriori. Verifica cada recibo original y reconstruye cada ledger desde la SQLite del caso usando la función auditora anterior `f3._worker`. Para M vuelve a derivar **los seis AST con parámetros** mediante el compositor Short E1 base y exige paridad byte-lógica de `candidate_graphs_hash`; no ejecuta ni elige un candidato.

Pruebas adversariales en `tests/test_arena_cafe_rf01_fidelity.py`:

- T-01: marcar D2/C00 como `METHOD_COMPLETE` y fingir `D.generate` debe fallar;
- T-02: insertar prior de M en Pista II debe fallar; en Pista I debe mostrarse;
- T-03: marcar C00 como elección de M o recortar la enumeración de 6 a 1 debe fallar;
- T-04: M0 `UNRESOLVED` conserva su naturaleza de abstención restringida;
- T-05/T-06: mock o corrida histórica Buffalo etiquetada `EV01 live` debe fallar;
- T-07: una **declaración en el manifiesto** que atribuya a O0 lectura de preparación O1 debe fallar; **no es un test real de permisos GitHub/cache/SQLite**, que permanece pendiente de R6;
- T-12/T-16: G2/CSV/RMSE positivos no habilitan G3 ni método completo;
- T-24: alteración de SHA original congelado debe fallar.

`RF01` no reemplaza la suite F0, F1, F2 ni F3. Un `PASS` de CI es `R0/R1 TECHNICAL READY FOR INDEPENDENT REVIEW`, nunca una decisión científica `CONFORME`.

## 4. Entrypoints, universo y límites

Véase [02_METHOD_ENTRYPOINT_MATRIX.md](02_METHOD_ENTRYPOINT_MATRIX.md) para la matriz original, operadores y condiciones. El manifiesto `igc-arena-method-fidelity/1.0` registra por fila:

`track, arm_id, condition_id, method_version, original_entrypoint, original_source_sha, native_input_contract, source_snapshot_hash, visible_input_sha, input_fields_present, adapter_fields_read, native_fields_read, transport_fields_submitted, input_fields_used_or_rejected (actor, operación, estatus y nivel de evidencia), method_capabilities_in_scope/out_of_scope, native_component_execution_complete, arena_task_complete, original_candidate_universe, native_candidate_ids/hashes, selection_decision_owner, selection_policy_sha, parameters_origin, cross_arm_prior_imports, calibration_policy, abstention_origin, execution_state, provider_calls, omc_invocations, gates_by_candidate, source_exposure, unsupported_observables, ledger_case_id`. El verificador tipado v1.1 no admite campos obligatorios ausentes ni campos extra; comprueba los seis IDs/hashes E1 originales con orden, contenido y unicidad.

No existe `null` ambiguo para las compuertas G0–G3: se declaran explícitamente `NOT_RUN_NATIVE_METHOD`. El universo `D.generate` conocido (hasta 6 para su contrato válido) **no se finge enumerado sobre EV-01**. Las 15 composiciones M extendidas **no** se añaden a la candidatura base después de ver sus resultados; el espacio registrado en esta prueba fue **6 base**.

## 4 bis. Alcance preciso de procedencia y gates

Los **15 eventos POS** del control son **15 eventos de creación de pedidos** visibles antes del corte [0,10) min, no las 15 filas de todo el log POS (que incluye otras clases de eventos). Las seis muestras de acumulados representan otra proyección y no deben confundirse con «15 observaciones».

La columna `adapter_fields_read` registra los campos consumidos por las funciones de proyección/puerto de la Arena. `native_fields_read=[]` afirma que **no hay lectura de tales observables acreditada por los motores generadores** en esta campaña: D rechaza la entrada; E1 enumera solo desde su registro; Buffalo usa un prompt mock. `transport_fields_submitted` distingue la oferta de campos al transporte mock Buffalo de cualquier razonamiento LLM. `input_fields_used_or_rejected` enumera actor, operación, estado y nivel de evidencia **estática de código/recibo**; no es una sonda dinámica del razonamiento interno. El validador rechaza cambios de actor u operaciones, pero no prueba por sí solo un aislamiento OS/ACL.

El workflow RF-01 clasifica los **hashes y las métricas del reporte F3 previo**: su éxito indica continuidad de ese reporte, **no nueva autenticación byte a byte de los cuatro CSV de OpenModelica**. Los tests T-07 son validaciones de declaraciones del manifiesto, no intentos de acceso a los artefactos ajenos. `CONDITION-01=PARTIAL` hasta R6.

## 5. Próximas compuertas — bloqueadas por decisión y revisión

**RF-02/R2** distingue tres rutas independientes: **D-A** conserva D estricto, deja **EV-01 no soportado** y certifica la conformidad del generador con un fixture válido separado (sin sustituir EV-01); **D-B** propone una extensión D-POS versionada mediante RFC científico; **D-C** crea una ronda experimental nueva con pulso exógeno realmente conocido y protocolo independiente. Ninguna se aprueba automáticamente. Debe fijarse también qué colección molecular se permite (**base 6 o extended 15**) antes de otra selección y la política de equivalencia de observación O1. En ausencia de decisión, `R2=BLOCKED_SCIENTIFIC_POLICY_DECISION` y `A3=PARTIAL`.

**RF-03/R3:** cuando R2 sea revisado, D deberá llamar su generación auténtica o documentar el rechazo; M deberá conservar todo el universo y abstenciones; Buffalo solo saldrá de `BLOCKED_BEFORE_RUN` con llamada Cloudflare *nueva* previamente autorizada, no con mock.

**RF-04–06/R4–R7:** sin reescribir ecuaciones nativas, sin traducir Buffalo 0–8 h como si fuera EV-01 0–10 min, sin G2/G3 para traducibilidad no demostrada, sin G4/G5, sin usar FULL como dato de O0 y sin promover memoria de procedencia a «razonamiento causal».

**Prohibición de promoción:** hasta revisión independiente, `scientific_method_fidelity=NOT_ESTABLISHED`, `native_method_complete_count=0`, `A3=PARTIAL`, `G4=G5=NOT_RUN`.

### Incidente de implementación y corrección comprobable

La primera CI de esta PR, [#41580640572](https://github.com/yudocyudoc/IGC/actions/runs/41580640572), fue **16/16 PASS** pero el job RF-01 estaba encadenado al workflow A1, por lo que se reejecutaron **cuatro controles OpenModelica D2/C00**. Esto **violó el requisito operativo R0 «sin nueva simulación»**, aunque no produjo ninguna inferencia Buffalo live, candidato nuevo, calibración ni G4/G5. No se borran ni se reetiquetan esas corridas.

**Corrección:** restaurado byte por byte `.github/workflows/arena-cafe-a1-evidence.yml` de PR #137; RF-01 se movió a `.github/workflows/arena-cafe-rf01-fidelity.yml` con permisos `actions: read`, que descarga *por run ID fijo* los dos sobres públicos, seis worker artifacts/SQLite y el **reporte de adjudicación F3 ya verificado** de la ejecución anterior, no los cuatro archivos `.mo/.mos/CSV` del solver. Los tests adversariales RF-01 también leen los sobres descargados y no generan otra traza DES. Es una corrección de procedimiento, no de los resultados. La nueva CI debe verificarse al HEAD final: un PASS de #41580640572 **no sirve** como cumplimiento de la condición «sin nueva simulación».

## 6. Trazabilidad

- [A1/A3/B offline, CI de origen #41575917332](https://github.com/yudocyudoc/IGC/actions/runs/41575917332) — 15/15 PASS en el commit de corte.
- [F0 fuente original #41575917359](https://github.com/yudocyudoc/IGC/actions/runs/41575917359) — PASS, blob nativo protegido.
- [Buffalo histórico real #40255975864](https://github.com/yudocyudoc/IGC/actions/runs/40255975864), [R1 #40452596916](https://github.com/yudocyudoc/IGC/actions/runs/40452596916), [R2 7K #40486060023](https://github.com/yudocyudoc/IGC/actions/runs/40486060023) y [R2 16K #40490534985](https://github.com/yudocyudoc/IGC/actions/runs/40490534985) — **NO** cuentan como EV-01 live.
- Auditoría externa original: `AUDITORIA_FIDELIDAD_METODOLOGICA_ARENA_IGC_2026-11-02.md` (archivo del proyecto, no copiado al código ejecutable).
