# F1a — Ledger bitemporal mínimo

**Estado:** corte inicial integrado en `main`; prototipo sintético local, no ledger de producción ni D1.
**Alcance:** LinkML fuente y JSON Schema derivado; migración SQLite; revisiones append-only, idempotencia, digests y consulta bitemporal local.

## Contrato

- `recorded_at` es tiempo del sistema; `valid_from/valid_to` son tiempos válidos del fenómeno. `as_known_at` reconstruye el estado conocido a ese corte.
- Timestamps con zona horaria se normalizan a UTC; se rechazan ventanas invertidas.
- PR #4 añade la regla de que `recorded_at` no retroceda para una misma entidad; tiempos iguales se desempatan con número de revisión.
- Escrituras `BEGIN IMMEDIATE`; comandos idénticos con la misma idempotency key son idempotentes; orden distinta con igual clave falla.
- Triggers impiden UPDATE/DELETE en tablas canónicas.

## Evidencia

- [F0/F1a Actions #252](https://github.com/yudocyudoc/IGC/actions/runs/39362255158): 39 pruebas combinadas.
- [F1a LinkML #15](https://github.com/yudocyudoc/IGC/actions/runs/39362255202): schema reproducible y fixture validado.
- [PR #4 Actions #253](https://github.com/yudocyudoc/IGC/actions/runs/39362587500): 40 pruebas combinadas; merge `1d706e6847ad03c0cb6a026aa49f8b7214dbcfb0`.

## Pendiente

SQLite es temporal dentro del runner. Falta validación completa de payloads por clase LinkML; no hay D1, API persistente, outbox/proyectores, R2, Vectorize, borrado regulatorio ni autorización por caso. Este corte no es productivo.