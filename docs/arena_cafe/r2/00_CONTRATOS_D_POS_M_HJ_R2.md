# RF-02 · R2 contratos observacionales — alcance y criterios de aceptación

**Fecha:** 2026-11-02. **Base:** RFC de Astra `RFC_R2_D_POS_MOLECULAS_OBSERVABLES_2026-11-02.md`, cierre R0–R1 PR #138 `fc1a55a187fb6991adc8638e030b85b2c00fdfe5`.  
**Estado inicial:** implementación del **contrato R2**, no cierre de R2 científico: `R2=PARTIAL_CONTRACT_AND_GRAMMAR_NO_NUMERICAL_POLICY`; `R3=NOT_RUN`, `A3=PARTIAL`, `G4/G5=NOT_RUN`.
**Pista de ejecución:** `.github/workflows/arena-cafe-rf02-contracts.yml`; únicamente Python con vista O0/O1 original de [run #41575917332](https://github.com/yudocyudoc/IGC/actions/runs/41575917332), sin `ev01.py`, DES, OpenModelica, RK4, Cloudflare ni gasto.
**Implementación:** `scripts/arena_cafe/r2_observational_contracts.py`; **fuentes históricas D y Short E1 no modificadas**.

## 1. Decisiones distintas, ninguna confundida

| Ruta | Contenido e implementación | Resultado atribuible |
|---|---|---|
| **D-A** | Fixture D original de pulso conocido. `legacy_generate` admite la entrada, y el wrapper reconstruye de forma independiente la **enumeración estructural** con `topology()`/`lint_structure()`. Se compara por orden, identificadores, hashes, estructura, linter y bytes de cada salida `modelica()` en la intersección válida | **Conformidad de gramática y payload** con fuente original. Ambos caminos usan el **mismo renderer original**, no prueba independiente de semántica del renderer, ni simulación/identidad de trayectorias |
| **D-B** | Frontera nueva `igc-arena-d-observed-pos-extension/0.1`: acepta vista POS auténtica y genera **todas** las estructuras del presupuesto original con `topology`/`lint_structure`; no invoca `legacy_generate(POS)` ni finge un pulso | Extensión de gramática/composición fiel a D, **sin convertir POS a tasa**, sin `.mo` EV-01 ni parámetros arbitrarios |
| **D-C** | Otra ronda nueva con pulso verdaderamente conocido | **NO** aprobada/implementada. Un fixture D-A no la sustituye |
| **M** | Fuente original Short E1 `registry.base.json` y `composer.enumerate_graphs`, seis AST completos. Conserva todos y agrupa de modo descriptivo su **proyección material estructural** | Capacidad enumeradora completada, **selección e identificación no ejecutadas**; agrupación material no significa equivalencia dinámica |
| **H_j** | Matriz O0/O1 por observable y brazo | **Contrato semántico propuesto**, operadores efectivos sobre las nuevas trayectorias aún `NOT_RUN` |

## 2. Frontera D-B y parámetros: bloqueo real de simulación

Entrada = un solo sobre visible validado de O0/O1, con timestamps de eventos **`pedido_creado`** anteriores al cutoff y serie acumulada; **la serie de entregas jamás reconstruye las llegadas**. El contrato preserva por cada línea `event_times_minutes_exact`, hash de eventos y conteo, con unidades/cutoff rastreables. Un cambio de entregas (con fuente re-hasheada) deja intacta la frontera de llegadas y el universo D.

La política numérica permanece `POLICY_NOT_SELECTED_NO_RATE_INFERRED` y `arrival_signal_hash=null`. **No se ha aprobado** ni el viejo uniforme de medio minuto ni una dispersión posterior al timestamp ni un híbrido de eventos discretos. Se registra el riesgo físico del benchmark previo: distribuir un evento de forma uniforme dentro del bin puede adelantar parte de su masa **antes** del evento real. Esta entrega no lo convierte en una tasa observada ni lo repara escogiendo otra señal sin decisión.

Las alternativas D respetan: 1–3 stocks; pérdidas permitidas según presupuesto; orden del original; truncamiento por `max_candidates`; el linter original; ninguna cuarta etapa ni buffers/equipos nuevos; mismos límites de capacidad y ecuaciones del generador original. El presupuesto por defecto para el expediente es `max_stocks=3, allow_loss=true, max_candidates=6, max_simulations=0`. **Esto no es una selección por desempeño**, sino el alcance de conformidad completo, sujeto a revisión.

Nominales: por defecto `NO_PARAMETERS_DECLARED`. El esquema admite **solo si se proporcionan expresamente** tres valores positivos con `unit/status/actor/source_kind/source_ref`; asunción del investigador e inferencia operacional externa están separadas. Rechaza una procedencia E1, otra rama o DES privado. Incluso nominales formalmente declarados **no autorizan** G2 o emisión Modelica antes de una decisión separada sobre señal y equivalencia. Ningún valor EV-01 se crea por defecto.

> **Alcance de conformidad importante:** esta entrega acredita identidad de **universo estructural, orden y construcción nominal dentro de la gramática original**, pero la prueba del renderer comparte implementación con D original. No hay dos traductores independientes ni validación Modelica/rutas de ejecución en el POS. No se debe presentar como `R4=PASS` o `G2=PASS`.

## 3. Moléculas: seis grafos, tres proyecciones materiales estructurales

Usamos `experiments/e1/registry.base.json` cuyo Git blob es `956eb9636046165b827275a822f37f3643dc1e59`; el catálogo E0 y compositor del origen siguen sin mutarse. `M` conserva el AST **completo por candidata** (instancias, enlaces y parámetros) y `full_ast_sha256`.

La función de proyección **solo para inspección** conserva instancias que tienen puertos de flujo material y enlaces de material; omite las capas auxiliares de señal del recibo. Bajo la fuente fija aquí se identifican tres grupos de proyección, dos AST por grupo. **Es agrupación estructural bajo este registro, no un operador de equivalencia observacional o dinámica**. No reducir los seis a tres candidatos ni obtener seis predicciones diferentes por decreto.

Roles `preparation` y `dispatch` y nominales E1 son **priors del registro**; no se descubren de O0/O1. `extended` 15 no es parte del alcance prospectivo R2 de este corte. Ninguna candidata se convierte en ganador ni recibe una puntuación G3 por existir en el catálogo.

## 4. Matriz H_j y condiciones de comparabilidad

| Magnitud | O0 | O1 | Uso legítimo |
|---|---|---|---|
| Creaciones POS, acumulado A(t) | Publicado | Publicado | **Entrada conocida**, no puntuar como predicción |
| Entregas acumuladas D(t) | Publicado | Publicado | Candidata primaria si cada brazo tiene **mismo objeto, frontera, unidad, horizonte y trayectoria semánticamente admitida**; B requiere modelo live y traducción legítima |
| A(t)−D(t) | Derivado | Derivado | Balance de no entregados, **no equivale a WIP** si hay pérdidas/cancelaciones |
| Preparaciones completadas | No publicado | Publicado | Propuesta de puerto E1; D genérico no posee «preparación» identificada. Comparación discreto/continuo admisible **solo si se prueba equivalencia de la magnitud** |
| Tiempo de espera y servicio de preparación | No publicado | Publicado, censura por finalización | `NOT_COMPARABLE` en D/B/M hasta establecer operador. No estimar `response_time` ni `responseTime` directamente de estas medias |

**O1 no obliga a que una estructura D/B/M posea la misma etapa.** El hecho de que el contexto sea igual no obliga a generar trayectorias diferentes. `not comparable` no puntúa cero y no se contabiliza como ausencia de esfuerzo.

## 5. Pruebas adversariales y criterios

- D-A: cruza **36 variantes de fixture** (`n={1,2,3}`, pérdida sí/no, `max_candidates={1,3,6}`, pulso en dos tasas) y exige equivalencia de estructura, orden, hash, linter y textos del mismo renderer original, sin solver ni mundo nuevo.
- D-B: **6 grafos** para cada O0/O1, ningún D2 preseleccionado; presupuesto/rangos originales (incluye truncamiento); no `modelica_sha256`, señal o G2 sin aprobación.
- POS: 15 creaciones observadas en el *fixture EV-01 congelado* antes de 10 minutos; cambiar entregas no cambia eventos ni estructura; O0 no puede contener preparaciones o futuro; O0 no adquiere O1.
- Parámetros: se rechazan cero/NaN, fuente de otra rama, status de estimación fingido, parámetros faltantes, unidades inválidas y presupuestos fuera del contrato.
- M: seis grafos con AST completo, tres grupos materiales estructurales sin afirmar equivalencia dinámica; O0 y O1 preservan el mismo universo E1.
- H_j: entregas condicionadas; cero scoring del input; sin WIP falso; sin tiempos de espera/servicio comparados sin operador.

El verificador original de RF-01 y F0-HIST continúan siendo compuertas de procedencia independientes. Los outputs R2 **no** sustituyen sus expedientes ni cambian los estados previos.

## 6. Pendientes de decisión antes de cualquier ejecución científica

1. **Política temporal POS**: ¿reconstrucción causal posterior, esquema de eventos híbrido, otra opción? Precisar integración, resolución y tratamiento de masa/cutoff antes de simular.
2. **Parámetros D-B EV-01**: cada valor con base operacional no derivada de E1; o abstención de simulación. Decidir si se permite calibración externa, su rango y presupuesto; no fingir estimación nativa.
3. **G2/G3 y traductor**: comparación Modelica y trayectorias por candidata a escala 0–10 min, pruebas de balance, discontinuidades, no-anticipación y salida H_j. **No** certificadas por esta entrega.
4. **M/H_j**: aprobación de equivalencia de unidad material y preparación; `extended` queda fuera.
5. **Revisión independiente de RF-02** y decisión explícita de investigador sobre R2. Hasta entonces `R2=PARTIAL`, `A3=PARTIAL`, `G4/G5=NOT_RUN`.

**Prohibiciones:** no gastar en Cloudflare, no nuevos mundos DES, no evaluar holdout, no ejecutar OMC, no copiar nominales del registro E1 hacia D, no convertir 6 AST en 6 mecanismos empíricos.

**Aclaración temporal:** las pruebas D-A generan textos Modelica de fixture válido **sin ejecutarlos**; esto comprueba que los candidatos construidos con estructuras D nativas se renderizan igual por la **misma función original**, no por dos implementaciones independientes.
