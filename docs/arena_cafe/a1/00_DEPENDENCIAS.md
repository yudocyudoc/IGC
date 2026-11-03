# A1 · 00_DEPENDENCIAS — selección mínima para cafetería

**Corte de referencia:** `main@5e2b5505a9224effe1b5242a3af61663b53aaa5d`, preparación F0-HIST **PR #134**, revisión exacta `9465b669027df6aae06db05b1261a02adff18472`. Esta rama de A1 depende del PR #134, **no** arrastra los PR Draft #131/#132 ni toma `historico/` como import.

| Fuente seleccionada (SHA de código de referencia) | Función real | Motivo / frontera |
|---|---|---|
| `scripts/arena_physical/des_engine.py@9465b669` | DES genérico clonado byte-idéntico de CAF-01 | Control físico **del evaluador**; no es cuarto brazo ni nativo D/B/M |
| `scripts/arena_cafe/ev01.py@9465b669` | Traza y vistas sintéticas EV-01 | Conservar el generador **solo en evaluación**; no importar `SPEC` ni verdad privada al productor |
| `scripts/arena_event_observability.py@9465b669` | Proyección por allowlist POS/POS_KDS/FULL | Separar eventos públicos de internos; FULL es un *origen instrumental*, no permiso automático de revelar todo |
| `scripts/arena_operational_ingestion.py@9465b669` | Ingestión sintética POS/KDS/CRM | No equiparar clic administrativo KDS con medición de servicio; no afirmar telemetría real |
| `scripts/arena_v0_contract.py@9465b669` | Sobre común, digest y `arm_view` | Valida claves superiores; **no** garantiza semántica física ni ACL |
| `scripts/arena_v0_common_evidence.py@9465b669` | Preparador y adaptadores V0 tipo pulso | Solo admite `kind=pulse`, `rate`, `duration` y observaciones `{t,delivered}`; **no** forzar POS a pulso conocido |
| `scripts/arena_d_v01.py@9465b669` | Gramática D original | Requiere `nominal_parameters` declarados, pulso y `cumulative_delivered` en formato propio; no estima parámetros de POS |
| `scripts/arena_b_native_runner.mjs@9465b669` | Buffalo cuantitativo original | La construcción visible entra como `backgroundKnowledge`; prueba de transporte **no equivale** a lectura/uso; ninguna llamada live en A1 |
| `scripts/arena_m_short_e1.py@9465b669`, `experiments/e1/composer.py@9465b669` | M original y compositor Short E1 | Enumera por roles configurados; todavía no hay puente tipado desde O0/O1 a selección molecular |
| `scripts/ledger.py@9465b669`, `scripts/arena_atms.py@9465b669`, `scripts/arena_memory.py@9465b669` | Memoria existente | No reconstruirla; filtrado lane existente **no** demuestra aislamiento por `condition_id`, caché o revisión |

SHAs completos de blobs y ejecuciones verificadas: [00_BASELINE_MANIFEST.json](00_BASELINE_MANIFEST.json). Los archivos recuperados por F0-HIST conservan su manifiesto de origen en `historico/manifest_ev_recovery_2026-11-02.json`.

## Cadena F1 (sin sustituir motores)

`EV-01 evaluación → proyecciones POS/FULL allowlisted → filtro temporal [0,cutoff) → O0 conteos / O1 agregados físicos autorizados → sobre V0 por condición → arm_view D/B/M → INTERFACE-01`.

La rama de A1 **no invoca** la inferencia de los productores ni usa resultados reservados. Su `evidence.py` consume las proyecciones ya públicas que prepara el evaluador; no importa el generador EV-01 ni el DES. No se utiliza PM4Py para inventar causalidad.

## Decisiones expresas de alcance

1. Dejar `scripts/arena_v0_common_evidence.py` y los métodos nativos D/B/M intactos hasta tener un mapa de consumo sustentado.
2. A1 en esta rama crea proyecciones O0/O1, regresiones y matriz de compatibilidad; **el consumo real permanece incompleto**.
3. A2 seguirá siendo el control físico (B0/B1/B2, RESOURCE-01); A3 será la ejecución de los tres generadores con G0–G3 y registro íntegro.
4. No hay presupuesto ni autorización para llamada Buffalo live, G4/G5 o gasto externo.
