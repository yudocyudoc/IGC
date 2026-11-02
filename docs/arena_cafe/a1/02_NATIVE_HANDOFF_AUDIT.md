# A1 · F1 · Segundo incremento: interfaces nativas y aislamiento por trabajador

**Fecha:** 2026-11-02  
**Estado:** `ENGINEERING_PASS` sobre control sintético, `INTERFACE-01=PARTIAL`, `CONDITION-01=PARTIAL`, `A1=PARTIAL`.  
**PR:** [#135](https://github.com/yudocyudoc/IGC/pull/135), apilado sobre F0-HIST [#134](https://github.com/yudocyudoc/IGC/pull/134).  
**Código evaluado:** `684edc2e840b550d4319957b2d4d37fb52eaa281`.  
**CI de resultados:** [41539110918](https://github.com/yudocyudoc/IGC/actions/runs/41539110918) · **8/8 trabajos PASS**; [regresiones EV-01/02 41539111018](https://github.com/yudocyudoc/IGC/actions/runs/41539111018) PASS.  
**Recibo consolidado:** [artifact a1-cafe-native-six-worker-audit / 13186025799](https://github.com/yudocyudoc/IGC/actions/runs/41539110918/artifacts/13186025799). El comparador corrió sobre recibos de seis jobs, no sobre los inputs de los productores.

## Fronteras de procedencia

`scripts/arena_cafe/native_handoff.py` recibe únicamente uno de los sobres públicos `O0_VISIBLE.json`/`O1_VISIBLE.json` existentes. Revalida el contrato `igc-arena-visible-input/0.1`, condición, pregunta original, identificador de ronda, ventana temporal, conteos acumulados, unidades y hash del `source_snapshot`. Rechaza campos extra y cruces entre condición y solicitud. **Un SHA sin firma no autentica frente a un productor malicioso que puede reescribir datos y SHA**.

La exportación individual `D/B/M × O0/O1` no puede sobreescribir su carpeta y solo crea `handoff.json`; para B/M añade `visible.json`. D no recibe un input nativo falso.

### Motor nativo, separado de su transporte

| Brazo | Acción realmente ejecutada | Evidencia | Límite epistemológico |
|---|---|---|---|
| **D** | La validación del código D original `arena_d_v01.validate_case` rechaza el sobre de eventos; el trabajador D conserva `BLOCKED` y no ejecuta generador | Prueba `test_actual_d_native_contract_fails_without_invented_pulse`; 2 jobs D PASS | **No inferencia**. El método exige `pulse` y parámetros nominales que la evidencia POS/O1 no identifica |
| **Buffalo** | `scripts/arena_b_native_runner.mjs` llama `Engine.generate` y `LLMWrapper` **originales**, obtenidos de `UB-IAD/sd-ai@5199f7b45f3a7ae4a773cb0dd8542940aabe9edc`; `BUFFALO_MODE=mock` | 2 jobs B PASS; `provider_calls=0`; las huellas de los mensajes de usuario **son distintas** entre O0/O1 | El modelo devuelto es el **stub fijo**. La variación de hashes prueba sensibilidad de la solicitud al contexto, **no** uso causal ni que el LLM entendió las mediciones |
| **Moléculas** | `scripts.arena_m_short_e1` ejecuta el compositor Short E1 original con registro base | 2 jobs M PASS; entrada validada por hash; `candidate_graphs_hash` **idéntico** entre condiciones; `candidate_selection=UNRESOLVED` | La enumeración es independiente de observaciones; **no** traduce O1 a roles ni estima parámetros |

No se modificaron el motor Buffalo original, las gramáticas D ni el compositor E1. Este resultado es distinto de simular un método sustituto. Tampoco constituye G3, identificación causal o una evaluación empresarial.

## Segregación de condiciones: qué quedó y qué falta

`native-isolated` usa una **matriz de 6 jobs independientes en GitHub Actions** (`O0/O1 × D/B/M`). Cada uno:

1. Hace *sparse checkout* solo de los scripts/registries necesarios; comprueba la **ausencia** del generador EV-01, su `SPEC`, el DES y la historia CAF.
2. Descarga únicamente el artefacto público de **una** condición y afirma que existe exactamente un JSON de entrada.
3. Verifica identidad de brazo, condición, `source_snapshot_hash`, `visible_input_hash` y `scope_hash`; no construye referencias a la condición hermana.
4. Ejecuta solo su método permitido, sin provider live, y sube únicamente un **recibo mínimo**, no prompts completos ni datos privados.
5. En `native-comparison`, un evaluador separado verifica seis `scope_hash` diferentes, fuente idéntica entre D/B/M dentro de cada condición, dos prompts Buffalo diferentes, y estructura E1 sin selección nueva.

**Nivel demostrado:** segregación técnica en puestos de trabajo/entradas, ausencia de acceso por rutas de checkout a la verdad física, y verificación de no mezcla accidental de condiciones. **NO demostrado:** aislamiento formal contra acceso malicioso a la API de artifacts, seguridad de credenciales compartidas, ACL de ledger/ATMS, seguridad de red/cache, ni acceso a archivos externos a la ruta controlada bajo otro mecanismo de ejecución. `CONDITION-01` sigue **PARTIAL**.

## Resultados negativos útiles

- **D:** inventar un `pulse` o derivar `capacity` de O1 para saltarse la validación sería una sustitución de supuestos no autorizada; se conserva el bloqueo.
- **B:** una invocación native con mock que devuelve los mismos candidatos no puede acreditar selección pertinente desde O1. La siguiente comprobación de *uso* requeriría un diseño autorizado y poder observar respuesta nativa a variación de datos; no se hizo llamada live.
- **M:** integrar evidencia en el `input_hash` sin usarla para elegir moléculas no equivale a resolver el puente causal; el resultado igual en O0/O1 evita promover enumeración a inferencia.
- **ATMS/ledger:** todavía no reciben eventos de nueva inferencia y no deben reconstruirse/alterarse para fabricar una iteración exitosa.

## Qué sigue para completar A1 y habilitar A2/A3

**Trabajo próximo acotado:** especificar un adaptador de observación nativo para D que preserve el estímulo POS como observado (sin representar una tasa conocida), y un contrato de traducción tipado `observación → roles/puertos` para M sin cambiar las moléculas originales ni forzar selección. Para B, decidir una prueba discriminante de uso con autorización separada de cualquier llamada live. F2 seguirá evaluando límites materiales y B0/B1/B2; F3 estará condicionado al uso real, posibilidad de abstención, comparación G0–G3 y memoria segregada.

**Gates hasta ahora:** `BASELINE-01` documentado, `EVIDENCE-01` PASS offline, `INTERFACE-01` PARTIAL, `CONDITION-01` PARTIAL, `MODEL-01` y `MEMORY-01` NOT_RUN.
