# RF-01 · Respuesta técnica a la revisión independiente de Astra del PR #138

**Fecha de corte:** 2026-11-02. **Revisión recibida:** `REVISION_PR138_REPARACION_FIDELIDAD_2026-11-02.md` (Astra), sobre PR #138 / HEAD `da4ec9fc020357f2176c43555df785cd8dd8fbd2`.
**Estado:** los hallazgos son pertinentes y no se disputan. **R0 favorable; R1=PARTIAL HASTA REVISIÓN INDEPENDIENTE DEL HEAD CORREGIDO.** A3=PARTIAL; G4/G5=NOT_RUN. No activado D-POS, Buffalo live ni nuevos modelos.

## Matriz: hallazgo → cambio → prueba → límite

| Astra | Cambio implementado | Test y veredicto admisible |
|---|---|---|
| **RF138-01 P1**: `verify_manifest` no protege entrada, fuente, seis IDs/hashes, consumo | Manifiesto **v1.1** con variantes tipadas `NATIVE_METHOD` y `PARITY`, igualdad estricta de campos requeridos (incluidos ausencias y extras), entrypoint exacto por brazo, SHA original desde F0, contrato de entrada, listas de seis grafos base **completas y sin duplicados** frente a `composer.enumerate_graphs`, actor y operación por campo comprobados. El build vincula cada manifiesto al recibo, hash público, `f3._worker` y ledger SQLite; PARITY vinculado al F3 anterior. | `test_astra_six_pure_validator_reproductions_now_fail_individually`: six subtests independientes que deben rechazar exactamente los seis cambios enumerados por Astra, más pruebas de omisión/extra y falsificación de lectura. Ningún hash se «actualizó» para aprobar |
| **RF138-02 P2**: atribución falsa de lectura D | `input_fields_read` ambiguo eliminado. Nuevos `adapter_fields_read`, `native_fields_read`, `transport_fields_submitted`. D: serie leída por **puerto Arena**, no por `D.generate` (bloqueado). M: campos interpretados por puerto, enumerador no seleccionado por los datos. B: prompt fixture transmitido sin consumo cognitivo demostrado. Cada campo clasifica `actor/operation/status/evidence_level`. | `test_original_D_rejects_before_native_read_but_adapter_reads_series`; `test_strict_variant_rejects_undeclared_fields_or_false_consumption`. Son comprobaciones de declaraciones contra rutas conocidas, no instrumentación del razonamiento LLM |
| **RF138-03 P2**: enumerador vs selección | `native_component_execution_complete` separado de `arena_task_complete` y `method_complete`. M completa su enumeración **6/6**, sin obligar a crear un selector E1 que no existe. La abstención de M0 es del wrapper. | `test_m_own_enumerator_complete_but_arena_task_not_complete`; se mantiene A3=PARTIAL por el contrato de la Arena, no por una falsa incompletitud de enumeración |
| **RF138-04 P2**: D-A diferente de D-C | Documentación corregida: **D-A** D estricto y fixture válido externo, EV-01 sigue no soportado; **D-B** extensión D-POS RFC; **D-C** mundo/pulso nuevo con protocolo propio. | Revisión textual; no se elige ni se ejecuta ninguna opción |
| **RF138-05**: F3 y T-07 | PARITY registra `source_f3_run_id=41575917332`, `source_f3_report_artifact_id=13202639585`, `source_native_csv_rehashed_this_rf01_run=false`. T-07 es validación declarativa del manifiesto, no prueba real de ACL. | El workflow RF-01 continúa descargando únicamente reporte F3, O0/O1 y SQLite/worker recibos. Nada de nuevos OpenModelica/Cloudflare; R6/CONDITION-01 pendiente |
| **RF138-06**: hashes y 15 POS | Hash de identidad **no** significa firma de autor. Los 15 son **eventos de creación de pedidos** antes del cutoff, no todo el log POS. | Revisión textual y baseline; sin nuevas afirmaciones empíricas |

## Límites y garantías

1. El validador puro tipado autentica la **coherencia de campos contra especificaciones fijadas**. El modo enlazado del `build()` autentica adicionalmente la igualdad con recibos originales, SQLite y el reporte F3. Ninguno es una firma externa: quien pueda manipular todas las fuentes/recibos confiados a la vez podría eludir una comparación hash no firmada.
2. La ejecución de `E1.enumerate_graphs` es **enumeración estructural**, no una simulación, ajuste, búsqueda de datos, selección de grafos ni experimento nuevo.
3. El `fidelity-readonly` no descarga CSV nativos ni revalida sus bytes: hereda el reporte anterior. Esa procedencia se registra explícitamente por fila.
4. `G2` de paridad y buenas métricas internas **nunca** promueven `G3`, `arena_task_complete` ni `method_complete`.
5. El experimento EV-01 sigue sin inferencia real Buffalo; sus inferencias Cloudflare históricas se reconocen y **no** se acreditan retrospectivamente a EV-01.
6. La corrección se realizó en **PR #138 Draft**, sin modificar las fuentes originales de D/B/M, el workflow A1 congelado, otros PR apilados, ni `main`.

## Comp puertas de revisión

- **R0:** favorable según Astra.
- **R1:** nueva implementación y nuevos tests; **no debe declararse cerrado** antes de repetición de RF-01 y F0 al HEAD corregido y aprobación independiente de Astra.
- **R2:** D-A / D-B / D-C **pendientes de decisión**, no delegados automáticamente al código.
- **R3–R7:** no ejecutadas.
- **A3=PARTIAL, G4/G5=NOT_RUN**.

Esta enmienda preserva, sin borrar, los runs previos que fallaron mientras evolucionaba el verificador. El run que acredita la corrección es solamente el nuevo run exitoso ligado al HEAD definitivo.
