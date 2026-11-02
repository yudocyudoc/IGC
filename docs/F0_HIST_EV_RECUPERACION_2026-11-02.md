# F0-HIST · Recuperación operativa EV-01/EV-02 (PR #134)

**Estado:** recuperación por copia, pruebas sintéticas y controles de procedencia; **no** campaña prospectiva ni conexión completa F3 a los tres brazos. Fuente: `experiment/arena-ev02-ingestion-provenance-20261101@c534203f99405044dc79cae38e6102520f4ae2eb`.

## Qué se recuperó

- `scripts/arena_cafe/ev01.py`: trazas físicas y vistas POS/POS_KDS/FULL, paridad 9 checkpoints contra DES promovido.
- `scripts/arena_cafe/diagnosis.py`: diagnóstico retrospectivo solo FULL; comparaciones DES auxiliares no son una inferencia causal real.
- `scripts/arena_cafe/ev02_probe.py`: ejemplos sintéticos POS/KDS/CRM y errores de semántica/relojes.
- `scripts/arena_event_observability.py` y `scripts/arena_operational_ingestion.py`: **blobs originales idénticos**, independientes del banco CAF-07B.
- Pruebas originales migradas a `tests/test_arena_cafe_*.py`, más prueba de identidad y ruta nativa `tests/test_arena_native_provenance.py`.

## Cambio intencional, acotado y explicado

El EV-01 original importaba `caf07b_umbral_secuencial` por **dos funciones auxiliares**: expresión regular de SHA y escritura canónica exclusiva. Estas dos funciones se recrearon en `scripts/arena_cafe/artifacts.py` con la misma semántica original (`caf02_public_cut_bridge.canonical` y `caf02_lab_exploratorio.write_new`). No se copia ni ejecuta el selector CAF-07B ni sus bancos privados. Los imports del DES ahora apuntan a `scripts/arena_physical/des_engine.py`, que es el **blob exacto** de `caf01_des_engine.py`.

Los cambios en los tres productores EV son solo: cabecera de procedencia, imports a módulos activos y la llamada al escritor auxiliar. El manifiesto JSON registra SHA de cada archivo fuente.

## Evidencia y custodia

EV-01 usa un DES conocido y contiene `SPEC` privado **dentro del código del generador**. Nunca debe cargarse desde un proceso productor D/B/M en una evaluación reservada. Las vistas proyectadas O0/O1 aún requieren contrato de consumo por brazo y separación por corte/condición; no están implementadas en este cambio.

EV-02 conserva hitos **administrativos** (clics POS/KDS), no los convierte en duración física. La prueba de ingestión usa solo datos sintéticos y no acredita sincronización real de relojes ni un POS empresarial.

El DFG PM4Py se ejecuta para verificar redacción y actividad visible; no demuestra que minería aporte valor decisional. PM4Py 2.7.23.11 tiene licencia AGPL-3.0: revisar antes de cualquier uso comercial.

## Gates antes de merge

- [ ] Evidencia CI de la regresión EV-01 (45/75/225; 9/9 paridad) y EV-02 (45+30; reloj incierto bloquea).
- [ ] Prueba de no regresión del origen D/B/M y del DES promovido.
- [ ] CI de capacidades recuperadas de Arena sigue verde.
- [ ] Revisar que ni tests ni código nuevo ejecuten nuevas llamadas Buffalo, recompongan modelos con información reservada o utilicen rutas `historico` como imports.

**Estado F3 no alcanzado:** Buffalo no realizó nueva inferencia autorizada y todavía no existe un adaptador O0/O1 realmente consumido por cada método. Conservar `PARTIAL` / `NOT_RUN` hasta que exista evidencia.
