# F0 — Auditoría inicial y bloqueo de aislamiento

**Estado:** auditoría inicial parcial; F0 no está cerrado.  
**Fecha de corte:** 2026-10-19  
**Alcance:** checkout `IGC`, remoto GitHub `yudocyudoc/IGC` y antecedentes referenciados de `yudocyudoc/short`.  
**Base normativa:** especificación IGC v0.2 y plan de implementación.

## Resumen

La auditoría confirma que `yudocyudoc/IGC` es un repositorio remoto vacío y accesible mediante el conector GitHub. El checkout local contiene sólo documentos de planificación/especificación, no una implementación ni locks de dependencias. Por ello no hay commit base para crear la rama aislada de F0. La creación de rama local y de worktree falló: Git no pudo crear `.git/HEAD.lock` y el gestor de worktrees no encontró una revisión `main`.

Se revisaron los estados y contratos de PR #20, #39 y #40 en el repositorio histórico `yudocyudoc/short`. Sus descripciones y documentos dejan claro que varios elementos son propuestas o IR conceptual; no prueban que la arquitectura integral v0.2 esté integrada en el nuevo repositorio. No se copiaron código ni datos desde `short`.

**F0 queda bloqueado antes de los cambios de implementación** hasta establecer una base Git y poder trabajar en una rama aislada. Esta limitación no impide continuar el inventario documental y la evaluación de referencias en una siguiente pasada.

## Evidencia y hallazgos

### Checkout y remoto de destino

| Elemento | Hallazgo | Evidencia/alcance |
|---|---|---|
| Remoto | `origin` → `https://github.com/yudocyudoc/IGC.git` | Verificado con `git remote -v`. |
| Repositorio remoto | Existe, default branch `main`, tamaño reportado 0; permisos conectados `pull` y `push` | Metadatos obtenidos mediante GitHub Connector. Tamaño 0 indica que no hay contenido Git actualmente. |
| PRs en `IGC` | Ninguno | Búsqueda de PRs del repositorio devolvió lista vacía. |
| Checkout local | Sólo documentos en `docs/`; no se encontraron fuentes de aplicación, manifiestos de dependencias ni configuración de runtime | Inventario local inicial. Los documentos aún no están en un commit. |
| Aislamiento Git | No creado | `git switch -c f0-inventario-spike` no pudo actualizar `HEAD`; creación de worktree con `ref=main` falló con `Needed a single revision`. |

No se intentó crear un commit inicial en `main`: hacerlo publicaría contenido en la rama estable y contradiría el aislamiento exigido para F0. Tampoco se modificó `yudocyudoc/short`.

### PRs de referencia en `yudocyudoc/short`

| PR | Estado actual observado | Qué aporta | Límites que deben conservarse |
|---|---|---|---|
| [#20 — IGC-SL v0.1](https://github.com/yudocyudoc/short/pull/20) | Cerrado, no fusionado; documento de diseño | Gramática tipada conceptual; referencia a Hines, SystemDynamics, MSL y BusinessSimulation/BSL; contrato `LINK/SENSE/GOVERN`, evidencia e hipótesis. | No es implementación validada. BSL 2.2.0 y adaptadores no se declaran compilados/verificados. Sus afirmaciones de código histórico son antecedentes del repo `short`, no del repo nuevo `IGC`. |
| [#39 — sondas de límites P1](https://github.com/yudocyudoc/short/pull/39) | Abierto, draft, no fusionado | Registra 11 regresiones E1 y seis sondas; identifica falso rechazo de split de stock, incapacidad de distinguirlo de duplicación y omisiones semánticas. | La ejecución de CI se reporta en el PR; no se reprodujo en este checkout. No validó modelos nuevos ni simuló una cafetería. |
| [#40 — IR/linter P2](https://github.com/yudocyudoc/short/pull/40) | Abierto, draft, no fusionado | IR conceptual con tipos `FLOW/STOCK/SIGNAL/CONTROL`, procedencia, hipótesis y `POLICY_UNIMPLEMENTED`; tests estructurales. | Estado declarado: `P2_CONCEPTUAL_IR_ENGINEERING_ONLY`. Conservación sólo topológica; no ecuaciones de red, política/feedback nativo, simulación OM ni prueba causal. Revisión independiente del código nuevo pendiente. |

El PR #20 contiene datos de versión y licencia como afirmaciones de su propio diseño. Se registran como pistas de auditoría, no como dependencias instaladas, compatibles o admitidas en `IGC`.

### Dependencias y herramientas

- **IGC local:** no hay `package.json`, `pyproject.toml`, lockfile, Dockerfile/Compose, Makefile ni código Modelica inventariado hasta este corte.
- **OpenModelica (`omc`):** instalación y versión no verificadas en este entorno.
- **RDF/SPARQL/SHACL, ATMS, LinkML:** no hay dependencias locales aún; versiones y licencias pendientes de fijación.
- **Cloudflare D1/R2/Vectorize:** no hay bindings ni recursos configurados en este checkout; no se accedió ni se incurrió en gastos.
- **Hines, SystemDynamics, MSL y BusinessSimulation:** se identifican como candidatos/antecedentes en la especificación y PR #20; deben pasar verificación independiente de fuente, versión, licencia, adaptadores y compilación antes de admitirlos al stack del nuevo repo.

## Registro de intentos de aislamiento

1. `git switch -c f0-inventario-spike` — falló al crear `.git/HEAD.lock` con `Permission denied`; `HEAD` quedó en `main`.
2. Gestor de worktrees, `ref=main` — falló con `fatal: Needed a single revision`, consistente con un remoto vacío sin commit.
3. GitHub Connector — confirmó que el remoto no tiene PRs y que el repositorio está vacío. No se crearon ramas ni commits remotos.

## Pendientes F0

1. Crear una base inicial autorizada para `IGC` y una rama aislada sin trabajar directamente en `main`. El repositorio vacío no permite aún una rama derivada; la política del proyecto debe determinar cómo sembrar el primer commit.
2. Resolver la escritura de metadatos Git locales para poder crear/sincronizar la rama de trabajo. Los permisos del conector GitHub habilitan la API del repositorio, pero no dan escritura local en `.git`.
3. Confirmar inventario real de `omc` y librerías Modelica después de habilitar una rama de trabajo.
4. Verificar manifiestos oficiales, versiones, licencias y compatibilidad del stack propuesto; generar `stack.lock.yaml` sólo después de comprobarlo.
5. Producir ADR de responsabilidades, ERD conceptual y matriz completa existente/documentado/faltante.
6. Preparar laboratorio local y spike sintética con artefactos y comandos reproducibles; etiquetar componentes ausentes como stub y dejar los gates correspondientes pendientes.

## Veredicto

`F0_AUDIT_PARTIAL — ISOLATED_BRANCH_BLOCKED — NO_IMPLEMENTATION_STARTED`.

No se declara completo ningún gate. No se ha compilado o ejecutado OpenModelica en el checkout nuevo, no se han instalado dependencias y no se ha demostrado integración vertical.
