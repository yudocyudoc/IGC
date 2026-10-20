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

La corrida [#205](https://github.com/yudocyudoc/IGC/actions/runs/39348542070) terminó en verde con 25 pruebas totales; las 11 pruebas F1a cubren corrección posterior, corte `as_known_at`, filtro de tiempo válido, idempotencia, conflicto de clave, timestamps zonificados, intervalos, registro/checksum de migración, detección de cambios, estructura del esquema e inmutabilidad.

## Pendiente dentro de F1a

LinkML está escrito como fuente de esquema, pero todavía no se fija su cierre de dependencias ni se ejecutan sus generadores. No se declara que las salidas JSON Schema/RDF/Python estén derivadas de forma verificada. La siguiente iteración debe fijar `linkml` y dependencias con hash, generar el JSON Schema/SQL artifacts en Actions y hacer que CI compare los outputs para detectar drift.

D1 batch, outbox transaccional/proyectores, R2 snapshot, borrado y privacidad permanecen fuera de este corte y requieren gates propios antes de integrar recursos reales.
