# Arena D + ATMS — memoria persistente de hipótesis, simulaciones y soportes (M1)

**Fecha:** 2026-10-25 · **Estado:** integrado en el [PR #23](https://github.com/yudocyudoc/IGC/pull/23), todavía **draft**, sin modificar `main`. La evidencia final de CI debe corresponder al último commit del PR.

## Frontera metodológica

- **D** conserva generación y cribado deterministas autónomos: `arena_d_v01.py` y `arena_d_v1_screen.py`. Ni el generador ni la rejilla consultan ATMS.
- **ATMS** es la memoria lógica de los soportes de hipótesis D, no un generador ni un árbitro empírico. El núcleo `scripts/arena_atms.py` se recuperó del trabajo previamente probado en [PR #16](https://github.com/yudocyudoc/IGC/pull/16); no se importaron sus integraciones moleculares ni otras vías experimentales.
- **Ledger F1a** (`scripts/ledger.py`, `migrations/0001_ledger.sql`) persiste el historial de revisiones y los artefactos originales. ATMS proyecta una vista *as-of*, contextual y retractable; su cálculo es reproducible a partir de la fuente. El ledger, no ATMS, conserva los bytes fuente y las versiones.
- **OpenModelica** sigue siendo verificador físico. El puente **solo admite** el paquete D1 cuando revalida los hashes y enlaces D0→D1, reproduce `assess()` a partir de los mismos datos públicos, coteja el código Modelica generado, compara CSV con predicción e inspecciona no negatividad, monotonicidad y balance. Ello no demuestra procedencia criptográfica del proceso OpenModelica ni verdad causal.

## Contratos y artefactos

`scripts/arena_d_atms_bridge.py` enlaza exactamente:
1. `D0/candidates.json`, `D0/submission.json`, `D0/memory-event.json`, archivos nativos Modelica y sus hashes.
2. `D1/screen.json`, `D1/memory-events.json`, modelos Modelica con mejores parámetros de la rejilla, CSV reales de OpenModelica y los chequeos de balance/paridad.
3. Registros append-only `ArenaDNativeBundle`, `ArenaDSubmission`, `ArenaDScreen`, `ArenaDG2Proof`, `ArenaTraceEnvelope`, `ArenaATMSNode` en F1a SQLite con política `lane:D` y ámbito de investigación/ronda.
4. Nodos ATMS de **supuestos**: existencia de propuesta `DSTRUCT`, observaciones `DOBS`, cota del instrumento `DINSTR`, rejilla de parámetros `DGRID`. Las justificaciones `DWITNESS` sustentan `DCOMPATIBLE` únicamente si D1 encontró testigos dentro de la cota declarada. Un conflicto de balance/monotonicidad observacional explícito puede crear un `nogood` para la combinación de observación y cota, **sin atribuir falsedad automática a la estructura**.
5. `snapshot(as_known_at)`: proyección ATMS con entornos mínimos, huellas y estado de soporte. `retract_assumption(...)`: inserta nueva versión inactiva preservando la anterior, con motivo y hash de revisión. `ATMS.what_if()`: bifurcación lógica temporal, sin mutar evidencia. El adaptador sólo lee revisiones `lane:D` para esa investigación y ronda; compartir SQLite **no equivale** a aislamiento criptográfico ni a un control de accesos multiusuario.

## Pruebas

`tests/test_arena_d_atms_bridge.py`: alternativas lógicas, explicación, `nogoods`, `what-if`, persistencia, relectura *as-of*, retractación selectiva, procedencia de evento D0/D1, campos externos y adulteraciones. La CI nueva se añadió al workflow D1 para consumir **CSV realmente producidos** en el mismo run y publicar la SQLite y la proyección. Las pruebas sin OpenModelica fallan explícitamente si faltan archivos G2; **no** forjan evidencias simuladas.

## Estado científico: lo que NO demuestra

- Dos soportes condicionados no son dos mecanismos identificados ni siquiera dos mecanismos observacionalmente equivalentes fuera de esta rejilla. ATMS evalúa **consistencia de justificaciones**, no probabilidades, parámetros verdaderos ni validez causal.
- `GRID_COMPATIBLE_NOT_IDENTIFIED` no convierte a los demás candidatos en hipótesis descartadas. No se emiten `nogoods` por el simple hecho de que el mejor ajuste de la rejilla exceda el límite.
- La memoria incluye la **propuesta D0 y la evaluación D1 de la primera iteración**. Se demostró retractación histórica en pruebas; **no existe todavía una segunda hipótesis generada automáticamente ni un ciclo de revisión D2/ATMS → D**.
- Los datos son sintéticos, de construcción visible, sin *holdout*; no hay inferencia GLM, comparativa Buffalo/M ni ejecución de Clef.
- El adaptador revalida ecuaciones y series, pero su prueba de integridad no sustituye custodia fuerte por permisos, firma de fuente o una auditoría externa del solver.

## Dirección posterior, sin implementarla aquí

Incorporar retroalimentación física nueva y la segunda revisión D en una ronda cerrada, conservando F1a como historial y ATMS como memoria contextual. Después se podrá reproducir la misma interfaz de memoria para B y M, con **políticas estrictas de aislamiento entre brazos**; no se compartirán los mecanismos propuestos entre ellos. Clef continúa como cuarto brazo futuro.

**Decisión:** D sigue **metodológicamente puro** mientras ATMS proporciona memoria de contexto, revisiones, supuestos retractables y rutas explicables de soporte. Sin moléculas.
