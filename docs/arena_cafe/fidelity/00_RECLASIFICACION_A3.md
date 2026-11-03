# RF-01 · Reclasificación obligatoria de A3 (R0–R1)

**Fecha:** 2026-11-02. **Contrato rector:** `PLAN_ACCION_CORRECCION_FIDELIDAD_ARENA_IGC_V1_2026-11-02.md`, §§0–3 R0/R1.  
**Baseline auditable:** [F0_FIDELITY_BASELINE.json](F0_FIDELITY_BASELINE.json), corte PR #137 `589a4b8604753b8ab5d0adf3f0606f6c30ae6e45`.  
**Código de verificación:** `scripts/arena_cafe/method_fidelity_manifest.py`.  
**Estado:** IMPLEMENTACIÓN DE R0–R1; firma del revisor independiente **PENDIENTE**. **A3 = PARTIAL**. Ningún motor/solver/proveedor nuevo se ejecuta para esta reparación; los trabajos originales se rehacen por la regresión A1 existente si CI los dispara, pero se clasifica solamente su salida previa.  
**Ramas:** nuevo PR apilado encima de #137, sin fusión a `main`, sin tocar #134–137 retrospectivamente.

## 1. Hallazgo vinculante

La presencia de un fichero `native.mo`, un CSV OpenModelica auténtico o un hash de fuente original no acredita una ejecución del **método completo**. En A3 se usaron funciones originales para crear un control de equivalencia cuyos candidatos y parámetros eligió el controlador. Se preserva la legitimidad de la simulación, pero se retira de la categoría de evaluación metodológica independiente.

El nuevo expediente genera dos pistas físicamente separadas en JSON:

| Pista | Alcance autenticado | Actor de selección | Veredicto |
|---|---|---|---|
| `PARITY_BENCHMARK_D2_EQUIVALENT_E1_C00` | Cuatro CSV reales D/M × O0/O1; stock/flujo conservado; RMSE descriptivo | **ARENA_POLICY**: D `topology(2,False)`; M `choose_one(minimal)` | **PARITY_ONLY; NO competitiva**, sin convergencia de métodos |
| `NATIVE_METHOD` | Seis workers D/B/M × O0/O1 y SQLite originales; sin nueva inferencia | **NONE** en construcción nativa EV-01 | Ningún brazo ejecutó su ruta generadora completa para este caso |

**Punto de independencia:** los parámetros de D en Pista I fueron deliberadamente fijados de acuerdo con E1. La columna `cross_arm_prior_imports` lo registra, y un test rechaza su ocultación. D/M casi idénticos no son evidencia de descubrimiento independiente.

## 2. Seis resultados históricos EV-01 clasificados sin promoción de estados

| Brazo | O0 | O1 | ¿Qué se ejecutó y qué falta? |
|---|---|---|---|
| D | `BLOCKED_BEFORE_RUN` | `BLOCKED_BEFORE_RUN` | `D.validate_case` original rechazó entrada POS sin pulso/nominal; `D.generate` no ejecutado en ruta de hipótesis de EV-01. La topología D2 en Pista I es elección Arena |
| Buffalo | `BLOCKED_BEFORE_RUN` | `BLOCKED_BEFORE_RUN` | Se invocó transporte/motor SD-AI original con **mock**, 0 inferencias Cloudflare para EV-01. Las llamadas reales históricas R1/R2 no son estas ejecuciones |
| Moléculas | `METHOD_ABSTAINED` (solo **M0 Bridge**) | `METHOD_ABSTAINED` (solo **M0 Bridge**) | `E1.enumerate_graphs` original sí produjo los 6 grafos base y M0 declaró `candidate_selection=UNRESOLVED`; **NO** significa que Short E1 haya seleccionado o validado un modelo nativo para EV-01 |

`METHOD_ABSTAINED` de M0 no cuenta como cierre completo del brazo. El expediente conserva `method_route_complete=false` para **todos los casos**, de forma explícita. Los seis `g0/g1/g2/g3` permanecen `NOT_RUN_NATIVE_METHOD`, aunque la pista separada de ingeniería haya aprobado `G2`.

## 3. Pruebas de seguridad metodológica

El validador comprueba los blobs nativos protegidos contra el propio archivo `tests/test_arena_native_provenance.py`, no actualiza SHA a posteriori. Verifica cada recibo original y reconstruye cada ledger desde la SQLite del caso usando la función auditora anterior `f3._worker`. Para M vuelve a derivar **los seis AST con parámetros** mediante el compositor Short E1 base y exige paridad byte-lógica de `candidate_graphs_hash`; no ejecuta ni elige un candidato.

Pruebas adversariales en `tests/test_arena_cafe_rf01_fidelity.py`:

- T-01: marcar D2/C00 como `METHOD_COMPLETE` y fingir `D.generate` debe fallar;
- T-02: insertar prior de M en Pista II debe fallar; en Pista I debe mostrarse;
- T-03: marcar C00 como elección de M o recortar la enumeración de 6 a 1 debe fallar;
- T-04: M0 `UNRESOLVED` conserva su naturaleza de abstención restringida;
- T-05/T-06: mock o corrida histórica Buffalo etiquetada `EV01 live` debe fallar;
- T-07: O0 anunciando lectura de preparación O1 debe fallar;
- T-12/T-16: G2/CSV/RMSE positivos no habilitan G3 ni método completo;
- T-24: alteración de SHA original congelado debe fallar.

`RF01` no reemplaza la suite F0, F1, F2 ni F3. Un `PASS` de CI es `R0/R1 TECHNICAL READY FOR INDEPENDENT REVIEW`, nunca una decisión científica `CONFORME`.

## 4. Entrypoints, universo y límites

Véase [02_METHOD_ENTRYPOINT_MATRIX.md](02_METHOD_ENTRYPOINT_MATRIX.md) para la matriz original, operadores y condiciones. El manifiesto `igc-arena-method-fidelity/1.0` registra por fila:

`track, arm_id, condition_id, method_version, original_entrypoint, original_source_sha, native_input_contract, source_snapshot_hash, visible_input_sha, input_fields_present/read/used_or_rejected, method_capabilities_in_scope/out_of_scope, original_candidate_universe, native_candidate_ids/hashes, selection_decision_owner, selection_policy_sha, parameters_origin, cross_arm_prior_imports, calibration_policy, abstention_origin, execution_state, provider_calls, omc_invocations, gates_by_candidate, source_exposure, unsupported_observables, ledger_case_id`.

No existe `null` ambiguo para las compuertas G0–G3: se declaran explícitamente `NOT_RUN_NATIVE_METHOD`. El universo `D.generate` conocido (hasta 6 para su contrato válido) **no se finge enumerado sobre EV-01**. Las 15 composiciones M extendidas **no** se añaden a la candidatura base después de ver sus resultados; el espacio registrado en esta prueba fue **6 base**.

## 5. Próximas compuertas — bloqueadas por decisión y revisión

**RF-02/R2** requiere elegir entre (A) escenario controlado admisible por D original, sin decir que es medición POS, o (B) RFC explícito de **extensión versionada D-POS**; ninguna opción se aprueba automáticamente. Debe fijarse también qué colección molecular se permite (**base 6 o extended 15**) antes de otra selección y la política de equivalencia de observación O1. En ausencia de decisión, `R2=BLOCKED_SCIENTIFIC_POLICY_DECISION` y `A3=PARTIAL`.

**RF-03/R3:** cuando R2 sea revisado, D deberá llamar su generación auténtica o documentar el rechazo; M deberá conservar todo el universo y abstenciones; Buffalo solo saldrá de `BLOCKED_BEFORE_RUN` con llamada Cloudflare *nueva* previamente autorizada, no con mock.

**RF-04–06/R4–R7:** sin reescribir ecuaciones nativas, sin traducir Buffalo 0–8 h como si fuera EV-01 0–10 min, sin G2/G3 para traducibilidad no demostrada, sin G4/G5, sin usar FULL como dato de O0 y sin promover memoria de procedencia a «razonamiento causal».

**Prohibición de promoción:** hasta revisión independiente, `scientific_method_fidelity=NOT_ESTABLISHED`, `native_method_complete_count=0`, `A3=PARTIAL`, `G4=G5=NOT_RUN`.

## 6. Trazabilidad

- [A1/A3/B offline, CI de origen #41575917332](https://github.com/yudocyudoc/IGC/actions/runs/41575917332) — 15/15 PASS en el commit de corte.
- [F0 fuente original #41575917359](https://github.com/yudocyudoc/IGC/actions/runs/41575917359) — PASS, blob nativo protegido.
- [Buffalo histórico real #40255975864](https://github.com/yudocyudoc/IGC/actions/runs/40255975864), [R1 #40452596916](https://github.com/yudocyudoc/IGC/actions/runs/40452596916), [R2 7K #40486060023](https://github.com/yudocyudoc/IGC/actions/runs/40486060023) y [R2 16K #40490534985](https://github.com/yudocyudoc/IGC/actions/runs/40490534985) — **NO** cuentan como EV-01 live.
- [Auditoría FID-01 a FID-15](../../../../AUDITORIA_FIDELIDAD_METODOLOGICA_ARENA_IGC_2026-11-02.md): referencia **externa al repositorio** en este PR; no se añade como fuente histórica de runtime.
