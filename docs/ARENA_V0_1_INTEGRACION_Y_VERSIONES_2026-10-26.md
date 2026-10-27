# Arena V0.1 — integración incremental, versiones y cierre de deuda de PRs

**Fecha del corte:** 2026-10-26  
**Rama de preparación:** `integration/arena-v0.1.0` desde `IGC/main`.  
**Base P0 integrada:** `d216a9dd49a200209f90bc740bc28e6df4ad7022` (PR #22, fusionado; CI `40240192807` = SUCCESS).  
**Plan vigente:** `docs/ARENA_IGC_ATMS_PLAN_IMPLEMENTACION_V1_3_2026-10-25.md`; reemplaza decisiones incompatibles de v1.1/v1.2.  
**Estado:** este documento **inicia la promoción**; no afirma que los brazos ni ATMS estén integrados, ni que exista tag/release GitHub.

## Decisión de repositorio

1. **`main` es la única línea estable integrada.** Solo entra código cuya capacidad está probada por CI, G0–G3 según corresponda, revisión de diffs, procedencia, versiones y licencias; la base actual es P0/V0.0 (contratos, no generadores).
2. **`integration/arena-v0.1.0` es efímera**, no reemplaza main: permite auditar trasplantes selectivos y conflictos entre fuentes. No se vacían PRs apilados dentro de esta rama indiscriminadamente.
3. **La unidad de promoción es la capacidad**, no el PR histórico. Traer fuentes/adaptadores validados con SHAs, tests y documentación, en PRs pequeños; si se transforma código, conservar ambos hashes y la explicación.
4. **Experimentos versus producto:** PRs de inferencia real, controles sintéticos, resultados negativos y variantes de prompts son evidencia histórica, no todos componentes de runtime. No copiar workflows que activan Cloudflare automáticamente a main.
5. **Después de integrar una capacidad**, etiquetar los PRs viejos como `integrated-selectively`, `experimental-evidence` o `superseded-with-lineage` y cerrar solo los realmente sustituidos, explicando la nueva ruta. Cerrar no borra commits, discusiones ni links. Mantener abiertos los que aún aporten cambios independientes.
6. **No se borra ni reescribe historia**. No `force push` a main, no fusionar cadenas enteras para hacer desaparecer borradores, no desplazar base de PRs existentes sin comprobar efectos y sin revisión.

## Estrategia de versiones

| Identificador | Se refiere a | Condición y acción |
|---|---|---|
| `v0.0.1-p0` | Corte inicial P0 integrado en `d216a9d…` | **Tag retrospectivo propuesto; no creado**. Solo marcar el commit existente, jamás etiquetar como Arena funcional. |
| `v0.1.0-rc.1` | Primer candidato reproducible de V0 en rama de integración | **NO EMITIR** hasta que se ejecuten todos los gates mínimos V0 y se selle el SHA del RC; puede necesitar RC.2, etc. |
| `v0.1.0` | Primer vertical con tres brazos independientes, G0–G3 reales, retroalimentación propia y memoria de iteraciones trazable | **NO EMITIR** antes de fusionar a `main`, pasar el mismo conjunto de CI en ese commit y publicar limitaciones científicas. |
| `v0.2.0` | Expansión futura ATMS/medición/robustez, si hay nuevo alcance aprobado | **Solo horizonte, no compromiso ni fecha.** |

**Semántica:** `v0.x` denota software experimental; la existencia de un tag no demuestra identificación causal, predictividad externa ni separación real de holdout. Una tag identifica el commit exacto, no un artifact de Actions que expira. Para cada release, acompañar enlaces a artefactos archivados, versiones upstream, pruebas, SHAs y advertencias. No usar `v1.0.0` hasta definición y aceptación específica.

**GitHub hoy:** repositorio sin releases ni refs `tags` encontradas; `main` no protegido (consultado al 2026-10-26). Antes de una versión liberada, activar en Settings → Branches/Rulesets: PR obligatorio a main, CI requerido, bloquear force-push/deletions y una revisión si hay otro revisor humano disponible. Si una regla no puede exigirse técnicamente, declarar el límite y usar gate manual, nunca presentar la rama como protegida.

**Secuencia concreta del primer tag cuando se apruebe:** checkout del repositorio, verificar que `git rev-parse main` apunta al SHA aprobado, ejecutar `git tag -a v0.0.1-p0 d216a9dd49a200209f90bc740bc28e6df4ad7022 -m "P0: contrato V0, sin brazos integrados"`, `git push origin v0.0.1-p0`. Esto es instrucción de operación **no ejecutada**. El tag final `v0.1.0` se crea en el merge de main, no en un head de PR experimental.

## Inventario de líneas abiertas para V0.1

Datos y versiones exactas en `data/arena/v0.1-integration-sources.json`. Las ramas de experimentación tienen PRs apilados; **ninguna ha sido fusionada por esta rama de preparación**.

| Línea | Fuente de promoción (conservar linaje) | Introducir en runtime V0.1 | Mantener como evidencia, no runtime |
|---|---|---|---|
| **D, sin moléculas** | PR #23 `feature/arena-d-pure-stockflow-v01`, correcciones PR #32 | generador independiente, salida nativa, Modelica y ensayos en CI | ajustes al pulso/hypotheses de D, ejecuciones históricas |
| **B, Buffalo** | PR #25→#26→#30→#33→#34→#36→#40 | adaptador original SD-AI cuantitativo, captura auténtica con autorización, G0 y simulación; opción de realimentación al propio B | B2–B5 como ensayos de revisión; nunca suponer independencia de B3 con pistas |
| **M, molecular** | PR #27→#28→#29→#31→#35→#41 | compositor Short E1, catálogo validado, salida molecular, Modelica, selección con abstención | M3 con parámetros fijos y los seis M3-P negativos (muestran falta de búsqueda paramétrica) |
| **ATMS / memoria** | P0 ledger F1a y módulos selectivos de PR #5–#17 | eventos bitemporales, hypotheses/revisions, soportes alternativos, qué cambió/por qué, control de vista por brazo | experimentos ATMS/LLM y rutas S/P con contratos anteriores v1.1 sin copiar roles |
| **C / Clef** | PR #39 y EPI-03..EPI-06 | **INACTIVE V0** por decisión rector v1.3 | piloto semántico, falsos soportes numéricos, comparación posterior C |
| **Evidencia de discriminación** | PR #37, #38 | añadir *tests* de separación y de NO ganador al evaluador común | CSV históricos; no reusar como holdout ciego ni como nueva verdad |
| **B0 sencillo** | comparador fuerte aún pendiente de incorporación integrada | misma evidencia primaria, sin variantes de inferencias de rivales | B2/B3/B4/B5 son nombres de revisiones Buffalo; **NO** confundir con baseline B0 |

## Gates de promoción: V0.1.0

Todos los gates deben reportar explícitamente PASS/FAIL/BLOCKED/NOT_RUN en un manifiesto de release, con enlace a run y SHA; ningún `PASS` se deduce de la existencia de este documento.

- **INT-01 reproducibilidad:** P0 contract tests y regresiones F0/F1a sobre el SHA de integración; runtime sin secretos para tests rápidos.  
- **INT-02 independencia:** evidencia pública idéntica D/B/M en una ronda, sin propuestas ajenas ni revelación de reserva. La privacidad lógica de JSON por sí sola no prueba aislamiento de secretos.
- **INT-03 generación:** cada brazo genera al menos una propuesta **desde su técnica original** o un bloqueo/abstención legítimos; D no utiliza M; B original no utiliza el compositor M.
- **INT-04 fidelidad/ejecución:** G0 nativo→Modelica explícito, G1 verificaciones formales, G2 OpenModelica real, G3 adecuación y límites por candidato; no simular el mundo generador en lugar de la hipótesis.
- **INT-05 revisión:** un brazo recibe solamente sus propios residuos/diagnósticos y puede producir revisión nativa enlazada; histórico B4/B5 es regresión, no ensayo nuevo.
- **INT-06 memoria ATMS:** evento hipótesis→modelo→simulación→feedback→revisión append-only y `as_known_at`; retractación selectiva con dos soportes alternativos, sin volver a escribir pasado.
- **INT-07 no falsar evidencia:** ABSTAIN/PARTIAL, parámetro desconocido, no ganador, fallo de G0, modelos equivalentes y fuente fuera del catálogo permanecen posibles; los seis M3-P quedan preservados como negativos.
- **INT-08 presupuesto:** tiempos de CPU, número de simulaciones y llamadas IA efectivas por brazo, sin confundir costos de los tres métodos.
- **INT-09 corte V0:** ejercicio nuevo con evidencia de construcción, estructuras generadas en aislamiento, perturbación de comparación y `PredictionLock`; toda evaluación reservada se marca `NOT_RUN` si el custodio independiente/holdout no está efectivamente implementado. Nunca disfrazar reserva pública dentro del repo como ceguera.

## Orden mínimo de PRs de promoción

1. **Este PR de gobierno/linaje**: P0→plan actual, política de versionado, inventario de fuentes y gate offline reproducible. No inferencias ni Modelica nuevas.
2. **D → V0 común**: extraer solo D autónomo y regresiones reproducibles, manteniendo sus modelos nativos.
3. **M → V0 común**: importar compositor molecular fiel y tests de abstención/variación de parámetros; no corregir con datos de evaluación.
4. **B → V0 común**: integrar SD-AI original y el puente condicionado Buffalo→OpenModelica; inferencia real solo por ejecución autorizada.
5. **Evaluador G0–G3 + ATMS de iteraciones**: ejecutar ronda integradora, comparar contra B0, emitir registros versionados y diagnosticar faltantes. Preparar RC y hacer revisión independiente antes del merge final.
   
Pueden hacerse pruebas D/M/B en paralelo en PRs pequeños, pero **no** se mezclan las propuestas durante una misma ronda. No introducir Clef como cuarto brazo por ahora. No ampliar catálogo para bucles de abandono/retorno antes de poder verificar modelos pequeños.

## Actualización de estado

Al iniciar este trabajo: `main`=**P0 integrada**, V0.1=**EN INTEGRACIÓN**, tags/releases=**NO CREADOS**, PRs experimentales=**ABIERTOS**. Cambiar este estado solo después de una acción GitHub y prueba correspondiente. Las tasas de éxito publicadas de modelos sintéticos no equivalen a un `ARENA_INTEGRATED_PASS`.
