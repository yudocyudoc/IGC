# F1a — Ledger bitemporal mínimo (spike)

**Estado:** implementación inicial para datos sintéticos; no es el ledger de producción ni D1.  
**Base:** rama `f1a-ledger-core`, apilada sobre F0.  
**Alcance de este corte:** esquema LinkML fuente, migración SQLite reproducible en Actions y eventos/revisiones append-only con idempotencia y consulta bitemporal local dentro del runner.

## Contrato implementado

- La identidad de entidad persiste entre revisiones; cada revisión nueva crea un evento y una fila histórica, nunca sobrescribe el contenido canónico anterior.
- `recorded_at` es el tiempo del sistema y `valid_from/valid_to` delimitan validez en el mundo. Las consultas primero reconstruyen la revisión que se conocía en `as_known_at`; después pueden filtrar por un intervalo de validez independiente.
- Los timestamps aceptan ISO-8601 con zona horaria y se normalizan a UTC. Se rechazan tiempos sin zona o ventanas invertidas.
- Las escrituras insertan evento y revisión bajo `BEGIN IMMEDIATE`; una clave idempotente repetida con la misma orden devuelve la revisión existente, y una clave reutilizada con contenido distinto falla. Cada migración se registra por versión/SHA-256 y rechaza cambios retrospectivos; las revisiones tienen un digest verificable para detectar cambios de contenido.
- Los triggers impiden UPDATE/DELETE de las tablas canónicas. El ledger local no implementa aún outbox/proyecciones, política de borrado regulatorio ni autorización por caso.

## Validación

El commit `15803a99e94330b957249514b3db1365ca7ff34a` pasó las verificaciones de GitHub Actions:

- [F0 synthetic spike, run 229](https://github.com/yudocyudoc/IGC/actions/runs/39349618174): 26 pruebas totales, incluidas 12 de F1a; validó append y consulta por CLI en un ledger temporal. El reporte científico F0 sigue `BLOCKED` por el candidato de modelo marcado como stub; D1/R2 no se ejecutaron.
- [F1a LinkML schema, run 13](https://github.com/yudocyudoc/IGC/actions/runs/39349618179): instalación con hashes, regeneración/diff del JSON Schema y validación del fixture sintético pasaron.
- Artefactos: F0 `12232706276`; evidencia de esquema LinkML `12232537715`.

## Pendiente dentro de F1a

El fuente LinkML está fijado en `schema/source/igc.yaml`. LinkML 1.12.1 y su cierre de 90 paquetes están en `requirements-f1a-linkml.lock.txt`; el workflow de Actions reinstala todo con `--require-hashes`, regenera `schema/derived/igc.schema.json` y compara los bytes contra el artefacto comprometido. Un fixture sintético ClaimOccurrence se valida con el JSON Schema generado. El entorno LinkML es una herramienta de generación separada del lock de ejecución F0; el SPDX de ese toolchain conserva `NOASSERTION` para licencias transitivas.

D1 batch, outbox transaccional/proyectores, R2 snapshot, borrado y privacidad permanecen fuera de este corte y requieren gates propios antes de integrar recursos reales.
