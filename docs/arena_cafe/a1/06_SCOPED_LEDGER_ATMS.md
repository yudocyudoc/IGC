# A1 · 06 — Ledger/ATMS original, memoria por linaje y fronteras de consulta

**Fecha:** 2026-11-02. **Plan rector:** cafetería v3.2, F1 antes de A2/F2.  
**PR:** #135 (Draft; depende del PR #134). **Estado:** integración real de SQLite/ATMS en control conocido, **MEMORY-01 y CONDITION-01 PARCIALES**; no ACL general ni persistencia central multi-worker.

## Problema preciso

La cadena A1 ya creaba recibos y un `trace_event` en algunos métodos originales, pero un JSON con nombre «memoria» no es persistencia real. Además, `Ledger.snapshot(case_id=...)` permite seleccionar otro caso si la invocación es libre: por sí solo NO constituye una autorización. La integración se construyó sobre **los motores existentes** `scripts/ledger.py`, `scripts/arena_atms.py` y `scripts/arena_memory.py`; no se duplicó su implementación ni se infirió verdad empírica desde ATMS.

## Incremento de código

`scripts/arena_cafe/scoped_memory.py` declara un único alcance de lectura y escritura:

`experiment_id × world_public_id × replica_id × arm_id × condition_id × iteration_id × run_kind`

Para el control A1: `cafe-a1 × w001 × r0 × D/B/M × O0/O1 × i0 × worker/native`. El `case_id` exclusivo de cada combinación se determina desde un **único input visible validado**; D/O0 y D/O1 nunca comparten caso, tampoco M/O0 y D/O0 ni un trabajador legacy y una simulación G2. Antes de *proyectar* ATMS o ejecutar recuperación lexical/FTS se consulta `Ledger.snapshot(case_id=<caso autorizado>,as_known_at=<corte>)`. Se verifica integridad de revisiones y `access_policy=lane:<arm>`.

Cada proceso registra cuatro revisiones persistentes con `append_revision` y claves idempotentes:

| Registro real en ledger | Dato permitido | Función |
|---|---|---|
| `fact`: fuente | hashes de evidencia, condición, cutoff y declaración de origen sintético | Verificar qué fuente se vio, **no** declarar verdadero un mecanismo |
| `assumption` | naturaleza de supuesto nominal o worker/mocking | Distinguir un escenario de una inferencia |
| `justification` | enlace fuente + supuesto → salida | ATMS muestra dependencia con contexto; **no** prueba empírica |
| `KnowledgeItem` | resultado original y estado epistémico | Recuperación lexical filtrada por linaje |

Solo se almacenan metadatos y **hashes** de los recibos, manifest y H_j, no la verdad reservada ni copia de observaciones O1 dentro de la memoria O0. La salida `inspect` confirma soporte condicionado en ATMS, resumen de recuperación e integridad, siempre `empirical_truth_from_ATMS=NOT_ESTABLISHED`.

### Dos recorridos que sí escriben en memoria

1. **Seis workers D/B/M × O0/O1:** tras crear su `worker-receipt.json`, escriben `scoped-ledger.sqlite`, `memory-receipt.json` y reconstruyen desde la misma SQLite a `memory-rebuild.json`. El D legado conserva su estado original `BLOCKED_NOMINAL_PULSE_MISSING`; Buffalo conserva **mock**; M conserva enumeración sin selección. Ninguno se promociona a inferencia real.
2. **Cuatro trabajadores nativos D/M × O0/O1:** tras la ejecución real OMC, verificación G2 y comparación H_j, escriben `native/ledger.sqlite`, manifiesto con hashes y lectura ATMS. G2 sigue siendo **control de ingeniería** con parámetros no calibrados, no G3 científico.

**El evaluador sigue recibiendo recibos permitidos**; no se añade una entrada O1 a los trabajadores O0 ni se usa el ledger para dar retroalimentación cruzada. Las SQLite por proceso son individuales: **no representan aún un almacenamiento global compartido** ni una política central de credenciales.

## Regresión adversarial

`tests/test_arena_cafe_a1_scoped_memory.py` utiliza **SQLite real y los módulos originales**, no un diccionario sustituto. Comprueba:

- cuatro linajes simultáneos en un mismo archivo de prueba: lectura D/O0 devuelve solo D/O0, jamás D/O1, M/O0 o B/O1;
- corte temporal `as_known_at` anterior a escritura ⇒ rechazo; scope sin revisiones ⇒ rechazo;
- rechazo del recibo de otra condición, estado científico falsificado o cambio de estado no emitido por el método original;
- repetición idempotente del mismo lote; cambio de contenido bajo idéntica clave ⇒ conflicto;
- el recibo G2 debe coincidir con el hash del candidato en manifiesto y H_j con el mismo brazo, condición e input.

Al crear informes ATMS por corte se conservan explícitamente los supuestos en el entorno mínimo; `supported=True` equivale a **soporte lógico condicionado**, no a prueba causal.

## Límites y próxima fase

**La seguridad verificada es a nivel de aplicación en un proceso invocado por un controlador confiable**, junto con separación de trabajos en CI y checkout que omite EV01 privado. No hay autenticación de un atacante con acceso directo a SQLite, ni denegación formal del token GitHub Actions, consultas de API de artifacts, cachés externas, FS de runners o ledger central compartido. Tampoco se certifican S0/S1 y ramas con/sin P que corresponden a fases posteriores. No se declara `CONDITION-01=PASS` general.

**F1:** la persistencia de procedencia, escenarios negativos y resultados por ámbito ya es ejecutable; `INTERFACE-01` sigue parcial por Buffalo y porque no hay selección/calibración nativa. **A1 sigue PARTIAL.** A2/F2 debe proceder con los controles B0/B1/B2 y los escenarios de recursos bajo el plan v3.2, **sin iniciar búsqueda paramétrica adicional**. F3 mantiene la exigencia de tres métodos auténticos.
