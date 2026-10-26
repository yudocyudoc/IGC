# Arena · Dos pilotos reales de Clef sobre Short E1/M3: selección numérica y evidencia operativa

**Fecha:** 2026-10-26. **Estado:** EJECUTADOS, evidencia descargada y verificada. **No promover Clef a brazo C todavía**.

## Ejecución y garantías

- **Inferencia real:** [GitHub Actions #40411486685](https://github.com/yudocyudoc/IGC/actions/runs/40411486685), **SUCCESS**. Cloudflare Workers AI `@cf/cloudflare/clef`: **17 solicitudes reales HTTP 200**, 8 casos numéricos y 9 semánticos. Máximo 17 solicitudes autorizado una vez por archivo de marcador añadido en HEAD; no retries, ninguna salida de D/B/M pasada como decisión, ninguna verdad-oráculo en el `state` entregado al modelo.
- **Respuesta cruda por caso, archivada ANTES de calificar:** [#12693212795](https://github.com/yudocyudoc/IGC/actions/runs/40411486685/artifacts/12693212795). **Paquete completo original:** [#12692873012](https://github.com/yudocyudoc/IGC/actions/runs/40411486685/artifacts/12692873012).
- **Postevaluación determinista sin ninguna llamada adicional:** [Actions #40412036620](https://github.com/yudocyudoc/IGC/actions/runs/40412036620), **SUCCESS**, [artefacto con resultados corregidos y 17 archivos reales #12692863688](https://github.com/yudocyudoc/IGC/actions/runs/40412036620/artifacts/12692863688).
- **Incidente del lector:** la primera calificación ignoró los valores aunque la inferencia real y el archivo fueran correctos. Cloudflare devuelve probabilidades de pregunta binaria en `answers.path_CXX.noul`, no `answers.path_CXX.probability`. La primera salida mostró `parseable=0` y **no es científicamente interpretable**. Se corrigió solo la lectura y se reprocesaron los mismos 17 archivos byte-exactos. Los **23 archivos originales** del primer paquete fueron comprobados por SHA-256 antes de la recalificación; la nueva distribución incluye **24 hashes verificados** más un manifiesto nuevo. No se volvió a llamar al modelo.
- Fuente cuantitativa real: tres trayectorias `deliveredTotal` tomadas de los CSV reales de **Short E1/M3** [Actions #40298421985](https://github.com/yudocyudoc/IGC/actions/runs/40298421985), tres caminos materiales C00 (2 colas), C01 (3) y C02 (4). La existencia de un filtro informativo independiente **no es distinguible** desde `deliveredTotal`, como estableció M3.
- Todos los casos semánticos son **notas operativas sintéticas escritas para el ensayo**, no observaciones de cafetería real. La referencia léxica predeclarada utiliza exactamente el mismo texto que Clef. No se modifica el compositor ni las ecuaciones.

## Política fija, antes de abrir la clave

Clef recibió tres preguntas binarias independientes por caso: para cada candidato, ¿continúa siendo físicamente posible con la evidencia suministrada? No se fuerza una única elección. Su `noul` se interpreta como juicio de compatibilidad, **no probabilidad calibrada de verdad causal**:

- p ≥ 0.70: inclusión firme.
- p ≤ 0.30: exclusión firme.
- 0.30 < p < 0.70: conservar como posibilidad incierta, sin confirmar.
- Conjunto conservador: **todos los candidatos que NO fueron excluidos**.

Se evalúan por separado: exactitud del conjunto firmemente incluido, exactitud del conjunto conservador, falsos descartes de estructuras realmente compatibles y apoyos firmes a incompatibles. La clave de respuestas se abrió **después** de haber archivado la respuesta real.

## Piloto A — Clef frente a M3 / comparación numérica

Misma familia de candidatos, trayectorias públicas de OpenModelica y observaciones. Casos alpha/beta originales M3, C02 generado desde el CSV real y perturbaciones predefinidas; además casos de entrega nula, ausencia de datos, observaciones ambiguas con cota absoluta de error declarada (0.76), incertidumbre muy amplia (cota 3.0) y fuera de repertorio por trayectoria alta.

| Caso | Conjunto compatible según referencia por intervalos | Clef: posibilidades no excluidas | Observación |
|---|---|---|---|
| N01 alpha | C00 | C00 | Correcto |
| N02 beta | C01 | C01 | Correcto |
| N03 tercer camino | C02 | C01, C02 | Conservador; no falsa exclusión |
| N04 entrega siempre 0 | Ninguno | C00, C01, C02 | **Error grave de fuera de catálogo**: soporte firme C00 y C01 |
| N05 sin medidas | Los tres posibles | Los tres | Conserva alternativas |
| N06 mezcla y cota 0.76 | C00, C01 | C00 | **Falso descarte de C01** |
| N07 alpha y cota 3.0 | Los tres posibles | C00 | **Falsos descartes de C01 y C02** |
| N08 entrega excesiva fuera de catálogo | Ninguno | Ninguno | Correcto |

**Totales:** 8/8 respuestas interpretables; 5/8 conjuntos de **apoyo firme** exactamente correctos; **4/8 conjuntos conservadores** exactos; **3 falsos descartes** y **2 apoyos firmes falsos**. Brier binario exploratorio sobre 24 juicios = **0.179217** (sobre esta muestra pequeña, no calibración externa).

**Comparador M3:** la política original de RMSE y sus umbrales, sin calibrar a las cotas cambiantes de los casos, seleccionó correctamente C00/C01/C02 en N01–N03 y se abstuvo ante N04 y N08. En N06 se abstuvo pese a la doble compatibilidad real. En N07 **seleccionó C00 por RMSE** aunque la cota de observación ampliada dejaba las tres estructuras posibles: tampoco es una decisión sobre un conjunto compatible bien fundamentada bajo incertidumbre distinta. Este caso no es un fallo del experimento M3 original, que fijaba una tolerancia diferente. Una referencia de intervalos deterministas, usando las mismas curvas y cotas suministradas a Clef, recupera todos los conjuntos por definición, porque la tarea está matemáticamente especificada. **No hay ventaja numérica atribuible a Clef** en este piloto.

## Piloto B — Clef con evidencia operativa sintética

Sin curvas físicas suministradas al proveedor. Mismo catálogo C00/C01/C02 con descripciones simétricas, evidencia textual de tránsito material después del despacho, ausencia de material observado, una o dos etapas seriadas, dos estaciones paralelas fuera del catálogo, testigos en conflicto, pantalla informativa sin almacenamiento y permutación de orden de candidatos en S09.

| Caso | Evidencia sintética | Posibilidades correctas | Posibilidades no excluidas por Clef | Resultado |
|---|---|---|---|---|
| S01 | Entrega inmediata con traza exhaustiva | C00 | C00 | Correcto |
| S02 | Una espera física exhaustiva | C01 | C01 | Correcto, p(C01)=0.3278 incierto |
| S03 | Dos esperas físicas en serie | C02 | C02 | Correcto, p(C02)=0.4336 incierto |
| S04 | Pantalla digital, sin rastrear objetos físicos | Todos | Todos | Correcto |
| S05 | Dos almacenes **en paralelo** | Ninguno | Ninguno | Detectó fuera de familia |
| S06 | Testigos incompatibles, al menos una espera física | C01, C02 | C01, C02 | Conservó ambas posibilidades |
| S07 | Un carrito físico entre despacho y retiro | C01 | C01 | Correcto, p(C01)=0.4345 incierto |
| S08 | Cola mostrada en tablet sin observación física | Todos | Todos | Correcto |
| S09 | Única repisa, orden C02–C00–C01 permutado | C01 | C01 | Correcto y sin dependencia obvia de orden |

**Totales:** 9/9 respuestas interpretables; **9/9 conjuntos conservadores correctos**, **0 falsos descartes**, **0 falsos apoyos firmes**, pero solamente **4/9 conjuntos de apoyo firme exactos**. Brier binario exploratorio sobre 27 juicios = **0.078707**. Por ejemplo, S02, S03 y S07 **mantuvieron** la solución, pero no le asignaron una probabilidad ≥0.70; esta capacidad conservadora no equivale a identificar con alta certeza cada estructura.

La **regla léxica simple**, fijada antes de ver a Clef y con **el mismo texto**, reconstruyó **6/9 conjuntos**; falló S06, S07 y S09 por carecer de reglas para testigos, carrito y paráfrasis. Esa línea base es deliberadamente estrecha, no una comparación frente a un sistema semántico de calidad equiparable. Tampoco se entrenó el modelo en estos ejemplos. El resultado favorece una investigación futura, **no demuestra superioridad general ni tasa de éxito del 100 % en cafeterías reales**.

## Qué prueba la comparación y qué no

**Probado:** el proveedor Clef respondió preguntas estructurales binarias sobre el repertorio E1; en casos cuantitativos simples recuperó tres estructuras conocidas, pero mostró falsa certeza y eliminaciones incorrectas al cambiar incertidumbre y fuera de catálogo. En nueve notas semánticas creadas para esta prueba conservó todos los conjuntos compatibles, incluidos ambigüedad y fuera de repertorio, y aventajó a una regla léxica básica. Cambiar el orden de los tres candidatos en S09 no produjo fallo en ese caso.

**No probado:** que Clef infiera mecanismos nuevos, supere M3 como selector basado en curvas, ahorre llamadas OpenModelica a igual exactitud, calibre probabilidades causales, generalice a notas genuinas de una cafetería, o mantenga exactitud ante otras redacciones y casos. Tampoco se usó una misma situación física con y sin notas semánticas para aislar causalmente el efecto de añadir esa fuente. Los ocho casos numéricos y nueve semánticos son **dos conjuntos distintos**, por lo que su diferencia de desempeño no estima por sí sola el beneficio de la modalidad.

**Decisión metodológica:** no convertirlo aún en cuarto brazo de inferencia dinámica. Conservar la arquitectura D/B/M y considerar Clef un candidato a selector semántico/priorizador anterior a la simulación; mantener cálculo, RMSE, balances y verificación de exclusiones objetivas en código. Para un experimento más fuerte, combinar casos paramétricos fuera de plantilla, una misma evidencia numérica con/sin nota verificable, comparador semántico de igual acceso y selección con presupuesto limitado. No introducir Clairic en este piloto.

## Reproducibilidad

- Código productor, predeclaración, auditoría y evaluador: `scripts/arena_clef_dual_pilot.py`.
- CI real con autorización de un solo commit: `.github/workflows/arena-clef-dual-pilot.yml`.
- Adjudicación offline de mismos 17 archivos: `.github/workflows/arena-clef-postonly-regrade.yml`.
- Artefactos para Astra: `public.json` (las 17 solicitudes exactas), `private-oracle.json` (clave NO entregada al modelo), `raw/N01..S09.json` (17 respuestas crudas), `deterministic-baselines.json`, `results.json`, `freeze.json`, `postonly-regraded-manifest.json` y `sha256-manifest.json` (manifiesto original de la inferencia).

El PR es borrador; **main no se modifica**. Ninguna llamada nueva al proveedor está autorizada por añadir documentación o repetir la adjudicación.
