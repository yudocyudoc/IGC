# IGC — P0 · Consolidación no destructiva de `main`

**Corte auditado:** 25 de octubre de 2026. **Estado:** inventario de procedencia + primera interfaz aislada, **NO** tres brazos implementados.  
**SHA base de `IGC/main` al crear el trabajo:** `95dcf731294ebe0eb8be888412c78e61d0da2f98`.

## Decisión de consolidación

1. `main` conserva F0 (contratos, RDF/CRMinf sintéticos, handoff y prueba OpenModelica) y F1a (ledger SQLite y bitemporalidad inicial). El documento [`STATUS.md`](../STATUS.md) sigue reconociendo que la plataforma no está completa. Solo existen dos workflows en `main`: `f0-ci.yml`, `f1a-linkml-bootstrap.yml`.
2. Los **17 PR abiertos de IGC** (al corte) no están integrados en `main`; la mayoría forman una **pila** con bases experimentales. No cambiar bases, fusionar la pila, reescribir SHAs, borrar ramas ni cerrar PRs por el mero objetivo de limpiar visualmente el repositorio.
3. Migrar por pieza auditada, preservando **archivo/commit de origen → contrato → test → run/artefacto → límite**. Un PR de proveedor o experimental no debe correr inferencias automáticamente en `main`.
4. El primer incremento hacia `main` es **aditivo**: plan v1.3, inventario, contrato de entrada/salida y feedback, pruebas offline y CI barata. No altera el algoritmo ATMS F0, el ledger F1a, los esquemas LinkML ni las simulaciones ya aprobadas.
5. **Brazo D / B / M primero**; **Clef (C) después** como comparación posterior sobre tareas que pueda efectuar nativamente. La presencia de Clef en experimentos previos **no** demuestra que genere estructuras simulables.

## Mapa de trabajo en IGC al corte

| PR | Rama y base | Uso posible / precaución |
|---|---|---|
| [#5](https://github.com/yudocyudoc/IGC/pull/5) | `f3-atms-candidate-selection` → `main` | Handoff de candidatos con ATMS F0, prueba sintética, no memoria ATMS iterativa de producción |
| [#6](https://github.com/yudocyudoc/IGC/pull/6) | `f2-f3-rdf-atms-handoff` → `f3-atms-candidate-selection` | Propuestas desde RDF/SPARQL, rama apilada |
| [#7–#9](https://github.com/yudocyudoc/IGC/pull/7) | FM-A/arquitectura/wrappers; PRs sucesivos apilados | Contratos tipados, diseños, procedencia y wrappers; auditar licencias, clases y conflictos |
| [#10–#14](https://github.com/yudocyudoc/IGC/pull/10) | FM-B1 a FM-B5; PRs apilados | **Brazo M**: compositor, candidatos, ATMS de soporte, OpenModelica y calibración condicionada |
| [#15](https://github.com/yudocyudoc/IGC/pull/15) | `fm-12-13-atms-llm-ablation` → FM-B5 | Experimentos ATMS vs reglas simples: no declarar mejora general de ATMS |
| [#16](https://github.com/yudocyudoc/IGC/pull/16) | `feature/arena-atms-memory-core` → #15 | Memoria ATMS/ledger, captura S/P y otras piezas **experimentalmente ensambladas**, mezcla metodologías v1.1; auditar y separar |
| [#17](https://github.com/yudocyudoc/IGC/pull/17) | `feature/arena-s-real-pilot-v0` → #16 | Una llamada S real independiente de P y calibración; `arena_s_pilot_enumeration.py` es **antecedente del posible D autónomo**; verificar dependencia molecular |
| [#18–#19](https://github.com/yudocyudoc/IGC/pull/18) | Experimentos 4 casos y modelos, apilados | Diagnósticos de prompts/inferencia; no confundir con tres generadores independientes |
| [#20–#21](https://github.com/yudocyudoc/IGC/pull/20) | NW1/NW2 experimentales sobre #17 | Captura GLM/Modelica/locks y pruebas v2/v2.1; **no fusionar como nueva arquitectura** |

**Observación de capacidad D:** `scripts/arena_s_pilot_enumeration.py` existe en la rama del PR #17, no en `main`. Enumera CS-01/CS-02 ya declarados y calibra contra construcción: **todavía no demuestra un generador determinista autónomo general que formule hipótesis sin moléculas**. Su algoritmo puede ser reutilizable solo después de separar dependencias e identificar su alcance.

## Historial externo preservado

- [`yudocyudoc/short`](https://github.com/yudocyudoc/short), `main`, conserva wrappers moleculares originales y archivo histórico descrito en [`FOUNDATION.md`](https://github.com/yudocyudoc/short/blob/main/FOUNDATION.md). El proyecto `short` no reemplaza a `IGC`.
- Clef: [Short EPI-03 #45](https://github.com/yudocyudoc/short/pull/45) clasificaciones/probabilidades y pruebas numéricas; [EPI-04 #47](https://github.com/yudocyudoc/short/pull/47) triangulación lógica con oráculos deterministas; [EPI-05 #49](https://github.com/yudocyudoc/short/pull/49) diagnóstico de falsos soportes reportados en EPI-04; [EPI-06 #51](https://github.com/yudocyudoc/short/pull/51) factorial 2×2 **diseñado, no ejecutado según el PR**. No aplanar estos cuatro estudios como un único resultado positivo; respetar las advertencias del estudio.
- [`UB-IAD/sd-ai`](https://github.com/UB-IAD/sd-ai), motores `qualitative` y `quantitative`, licencia **MIT** en `LICENSE`; implementan generación a partir de texto y uso de `currentModel`. **Todavía no integrados en IGC**; reproducir metodología y formato nativo sin enviar el output a un compositor molecular.

## Contratos implementados en este incremento (V0.0)

- `scripts/arena_v0_contract.py`: forma única **de evidencia visible**, misma instantánea para brazos `D/B/M`, envíos con artefactos nativos, feedback G0–G3 exclusivo de cada brazo y sobre mínimo de eventos enlazables por hash.
- `C` no puede activarse en V0: rechazo determinista explícito; no se llama a Clef, Buffalo, GLM ni OpenModelica por disponer de un contrato.
- `tests/test_arena_v0_contract.py`: pruebas de identidad de evidencia, mutación/cross-arm, campos ocultos, límites de iteración, rechazo de una afirmación falsa de ejecutabilidad y hash de evento. **No** prueban aislamiento ACL de procesos ni memoria ATMS real.
- `.github/workflows/arena-v0-contract.yml`: verificación offline en PR/main sin Secrets, red de IA, paquetes externos, ni apertura de reserva.

## Brechas abiertas — no declarar implementadas

1. D autónomo con sus reglas y generador, separado de las moléculas.
2. Buffalo reproducido en sus dos motores metodológicos y adaptador fiel a Modelica.
3. Moléculas integradas selectivamente desde FM-A/FM-B.
4. Tres adaptadores y ejecución real OpenModelica común con G0–G3.
5. Memoria ATMS que reconstruye iteraciones/retractaciones a partir del ledger, con vistas aisladas por brazo.
6. Custodia de reserva realmente independiente, predicción sellada y comparación científica.
7. Cuarto brazo Clef **posterior** al corte de D/B/M, con métricas apropiadas a su capacidad.

**Norma de avance:** abrir PRs pequeños por capacidad; solo fusionar en `main` tras pruebas, revisión y delimitación de alcance. El historial experimental permanece accesible por SHA y PR.
