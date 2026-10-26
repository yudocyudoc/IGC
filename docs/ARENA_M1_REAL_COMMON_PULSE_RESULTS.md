# Arena M1 — primer candidato molecular independiente sobre estímulo común

**Fecha del ensayo:** 2026-10-25/26 · **Estado:** código en PR #28, apilado sobre M0/PR #27, ambos Draft. **Método:** Short E1 íntegro (compositor de puertos tipados + clases Modelica) con una frontera exclusiva de presentación/evaluación de la Arena.

## Procedencia verificable

- Fuentes moleculares: copias byte-a-byte de `short`, blobs SHA fijados y CI M0 [40270828174](https://github.com/yudocyudoc/IGC/actions/runs/40270828174): 11 tests E1, 6 modelos base, 15 extendidos, OpenModelica real. NO nuevas moléculas Hines/BSL vendoreadas. Licencias externas pendientes de revisión.
- Contrato Arena: el input `data/synthetic/arena_m_v0_visible.json` es copia exacta de `arena_b_native_visible.json` de la primera generación Buffalo (Git blob `94fb9e853d1fd0f5623d759fb7b8408756eacf0c`). Contiene un pulso público a tasa **1.7 items/h durante 2 horas** y entregas acumuladas a t=0,1,2,4.
- Selección M1: `scripts/arena_m_visible_pulse.py` llama al compositor E1 original, encuentra **6 estructuras tipadas** y elige una sola mediante `MIN_INSTANCES_THEN_LINKS_THEN_CANONICAL_HASH`, **antes de observar** los valores de las entregas. Presupuesto de 1 propuesta, 1 simulación. No usa D, Buffalo, LLM, ATMS selector, `gold` ni reserva.
- Hipótesis `M-f250c7b99b2c`, `ArmSubmission.status=PROPOSED`. AST/hash nativo, recibo de traducción y evento almacenados. Grafo mínimo: fuente → cola de preparación → cola de despacho → contador de entrega, **sin tránsito opcional ni filtro informativo**.
- Correspondencias explícitas (no identificadas empíricamente): `Order→abstract work item`, `ReadyOrder→latent prepared item`, `Shipment→abstract delivered item`. Las dos colas intermedias son hipótesis **latentes**, no observaciones.
- Parámetros `maxThroughput=20`, `responseTime=0.5` para preparación y despacho **proceden del registro Short E1**, no de ajuste al caso. No son estimaciones óptimas.

## Contrato de traducción

No se modifica `experiments/e1/composer.py`, `backend.py` ni `src/modelica/IGCMolecules.mo`. Se llama a `backend.render_model` original; la transformación delimitada reemplaza exclusivamente el bloque externo de estímulos de prueba `Pulse/Step/Ramp` por `RealExpression(y=if time < 2 then 1.7 else 0)`. **No** se añaden/quitan stocks, puertos, relaciones, ecuaciones dinámicas internas, parámetros de moléculas ni roles. Si el bloque histórico no coincide byte por byte, se bloquea la traducción.

La versión OMC usada para esta reproducción y M1 es `v1.26.5-minimal`, con MSL 4.0.0 y SystemDynamics 2.1.2, congruente con E1. Para una comparación formal simultánea D/B/M, deberá fijarse **un mismo runtime y protocolo de comparación**, sin reinterpretar una corrida previa como igualada.

## Resultado real

[GitHub Actions 40271768284](https://github.com/yudocyudoc/IGC/actions/runs/40271768284) — SUCCESS. Artefacto `12628453364`, `m-visible_res.csv` y `g2-construction-report.json`. Salida OpenModelica real con 81 tiempos únicos (antes de eliminar eventos repetidos había 84 filas). `checkModel` admitió 91 ecuaciones y 91 variables. No es una simulación sintética escrita por Python.

| t hora | Observado entregado | M OpenModelica entregado | Error M−obs |
|---:|---:|---:|---:|
| 0 | 0.000000 | 0.000000 | 0.000000 |
| 1 | 0.350000 | 0.460140 | +0.110140 |
| 2 | 1.100000 | 1.793410 | +0.693410 |
| 4 | 2.500000 | 3.309442 | +0.809442 |

**RMSE descriptivo t=1,2,4:** `0.6186392941375638 items`, sin calibración. `G3_heldout=NOT_RUN`.

**Conservación:** el modelo utiliza **dos** stocks de material de trabajo en curso: `preparation0.waiting` y `dispatch0.waiting`. La variable original de backend `inTransit` solo suma estados tipados `STATE<Shipment>`, y para el grafo sin `transit` vale cero; **no** es el total de todas las colas. `scripts/arena_m_visible_verify.py` descubre todos los puertos materiales `STATE` desde catálogo+AST, excluye el contador terminal ya recogido en `deliveredTotal`, y contrasta:

`sum(material_stock_ports) + deliveredTotal − 1.7 * min(time,2)`

**Residuo máximo:** `6.834977028802314e-12 items`. Ningún stock material negativo en la trayectoria. Pruebas negativas alteran entregas, quitan puertos, crean stock negativo y retroceden tiempos.

## Historial de fallos conservado

1. Primer M1: `checkModel` compiló, pero el ejecutable se buscó en `/repo//repo/` porque el adaptador asignó `fileNamePrefix` absoluto; falla técnica de ruta, no del mecanismo.
2. Segundo M1: el solver ejecutó y produjo CSV, pero el verificador asumió incorrectamente que `inTransit` equivalía a todas las colas; denunció un balance falso.
3. Se corrigió únicamente la ruta y el verificador externo; los archivos Short E1 no se editaron. La CI final **PASS** con reconstrucción completa de material desde los puertos originales.

## Veredicto y siguiente puerta

| Gate | Veredicto |
|---|---|
| Recuperación de fuente Short E1 | PASS |
| Propuesta M independiente | Una estructura por prior explícito; PASS técnico |
| G0 — fidelidad de composición y estímulo | Wrapper e input auditables; **proyección de roles provisional** |
| G1 — formal y material | Tipos/puertos acotados y balance independientes PASS; no dimensionalidad universal |
| G2 — Modelica + conservación | PASS en el experimento M1 |
| G3 — ajuste sobre construcción | RMSE descriptivo 0.619, sin criterio estadístico de aceptación ni calibración |
| Reserva ciega/identificabilidad | NOT_RUN |
| ATMS memoria y revisión del propio brazo M | Pendientes |

**Siguiente paso razonable para M:** usar exclusivamente el diagnóstico del candidato `M-f250c7b99b2c` para decidir una iteración molecular interna sobre parámetros, alternativa de tránsito o abstención. Cualquier criterio/selección debe registrarse antes de ejecutar nuevas variantes; no usar la estructura Buffalo ni la respuesta generadora. **No elegir post hoc entre las 15 estructuras históricas porque una coincida mejor** sin declararlo como búsqueda/calibración de construcción y contabilizar el presupuesto. No afirmar que B es superior a M basándose en este contraste no pareado ni con los mismos grados de libertad.
