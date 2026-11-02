# A1 · 00_EVIDENCE_MATRIX — hechos, fuentes y nivel de comprobación

**Fecha:** 2026-11-02. Este registro distingue código fuente, CI y afirmaciones históricas. **Un resultado sintético no es evidencia de una cafetería real.**

| Afirmación / cifra | Evidencia precisa | Clasificación | Límite |
|---|---|---|---|
| Archivo F0-HIST: **137** archivos CAF + **50** workflows, **187** blobs | Manifiesto `historico/manifest_cafeteria_2026-11-02.json`; CI [41533062612](https://github.com/yudocyudoc/IGC/actions/runs/41533062612) | **VERIFIED_ENGINEERING**: SHA de blobs y ausencia de rutas fuente | No clasifica exhaustivamente otras ramas R1–R4 |
| DES promovido blob Git `8cadbc1f9489c3e1cd7eecd020009978873822ba` | `tests/test_arena_physical_clone.py`; CI 41533062612 | **VERIFIED_ENGINEERING** | Fixture ≠ prueba científica de inferencia |
| EV-01: **15 pedidos; vistas POS/POS_KDS/FULL 45/75/225 filas** | `scripts/arena_cafe/ev01.py`, `experiments/arena_cafe/test_ev01.py`; CI [41533062609](https://github.com/yudocyudoc/IGC/actions/runs/41533062609) | **VERIFIED_SYNTHETIC_REGRESSION** | Un solo mundo conocido; no validación de modelo real |
| EV-01: **nueve checkpoints de paridad DES** | `verify_des_parity` en `scripts/arena_cafe/ev01.py`; CI 41533062609 | **VERIFIED_SYNTHETIC_REGRESSION** | Paridad física de dos implementaciones de control, no identificación |
| Cifras **2.723 min** espera media preparación; **80.7 %** de espera; ocupación **87.0 %** | Diagnóstico histórico reportado en plan v3.2 §1.1; fuente CI [41359501903](https://github.com/yudocyudoc/IGC/actions/runs/41359501903) | **DOCUMENTED_HISTORICAL_NOT_RERUN_HERE** | La ocupación no es porcentaje de espera; no extrapolar |
| Dos módulos `arena_event_observability.py` / `arena_operational_ingestion.py` son copias idénticas | `historico/manifest_ev_recovery_2026-11-02.json`; `tests/test_f0_historico_active_boundary.py`; CI 41533062612 | **VERIFIED_BLOB** | Los otros módulos y pruebas se reubicaron con imports adaptados |
| Fuentes nativas D/B/M sin modificación en F0-HIST | `tests/test_arena_native_provenance.py`, CI 41533062609; diferencial PR #134 | **VERIFIED_SOURCE_INTEGRITY** | No hubo nueva inferencia de los tres métodos |
| `common()` requiere `pulse` y observaciones `{t,delivered}` | `scripts/arena_v0_common_evidence.py` fuente `2e86b2d...`, test A1 negativo | **VERIFIED_CODE_CONTRACT** | Ninguna evidencia POS se convierte automáticamente en pulso calibrado |
| D requiere `nominal_parameters` declarados y `observable=cumulative_delivered` | `scripts/arena_d_v01.py` `validate_case` | **VERIFIED_CODE_CONTRACT** | Representabilidad/identificabilidad de O1 aún no evaluada por ejecución nativa |
| Buffalo original usa `question` y JSON `construction/observability` como contexto | `scripts/arena_b_native_runner.mjs` | **VERIFIED_CODE_TRANSPORT_PATH** | No hay traza live de lectura/uso de O0/O1; **NOT_VERIFIED** |
| Short E1 compone desde roles/registry fijo | `scripts/arena_m_short_e1.py` `prepare`; `experiments/e1/composer.py` | **VERIFIED_CODE_CONTRACT** | No vincula ni calibra O1 desde eventos; **UNSUPPORTED_DOCUMENTED** |
| Checkouts efectivos de CI históricas / IDs de artifacts | Reportes GitHub Actions sin inspección explícita del checkout/artefacto | **NOT_VERIFIED** | No equiparar automáticamente `head_sha` y `checkout_sha` |
| Modelo físico de una cafetería real, clocks sincronizados y sensores calibrados | Ninguna fuente aportada | **NOT_VERIFIED** | No usar como evidencia empresarial |

## Control de procedencia experimental

- O0: agregados de eventos **POS autorizados anteriores al cutoff**.
- O1: O0 más **intervalos físicos agregados de preparación** observados por FULL y **completos** antes del cutoff; no se publica el cuarto tramo, recurso individual ni verdad física del generador.
- Los conteos en cada instante `t` consideran exclusivamente eventos con marca temporal **menor que t**; toda la ronda usa `[0,cutoff)`.
- `source_snapshot_hash` se obtiene de la construcción **visible por condición**, nunca de la verdad o datos posteriores al cutoff.
- Dentro de una condición, los tres `arm_view` tienen el mismo hash; entre O0/O1, sus hashes y contextos son distintos.
- No hay prueba de proceso/caché/ACL de ledger entre condiciones. Lo identificado como `INTERFACE-01` no certifica custodia ni consumo.
