# CAF-07A · Corrección del selector de evidencia (auditoría de PR #116)

**2026-10-31.** Clasificación: auditoría retrospectiva y nuevos barridos públicos exploratorios. CAF-07 original permanece **sin modificar**. La corrección no convierte el laboratorio en un sistema bayesiano ni integra todavía M/D o ATMS.

## Fallo que corregimos

CAF-07 elegía una acción por `pares de hipótesis de distintas clases robustamente separados − λ·costo`, con `λ=1` arbitrario. No estaba alineado con la regla diagnóstica, que exige **una única clase de cuello** después de observar. Además, tratar cada par de hipótesis con el mismo peso depende de la discretización de capacidades. Los costos eran ordinales e ilustrativos: restarlos de recuentos de pares no es un valor de información económico.

El código guarda, reconstruyendo las 120 predicciones de las 12 hipótesis DES, el **hash exacto del plan original de CAF-07 PR #116**: `sha256:2c34db4649508745acdd5cdae9e398a5a4b660160bbc9ab7d3f0e131e354e8f0`, del artefacto de la ejecución 41234401899. No se aceptan silenciosamente cambios de banco, política, salidas, tolerancias o menú.

## Nuevo criterio de calidad: pureza de decisión robusta

A partir de las 9 hipótesis que sobreviven a la observación inicial t10=9, para **cada acción** y **cada hipótesis** enumeramos todos los posibles valores de medición entera dentro de ±1 pedido de su predicción.

Una hipótesis está **garantizada como resuelta** solo si, para **todas** esas respuestas admisibles, las hipótesis que sobreviven pertenecen exclusivamente a la **misma clase física de cuello**. El resultado se presenta por preparación, despacho y entrega, junto con el peor número de clases todavía compatibles. Este es un criterio determinista de decisión con tolerancia, **no** probabilidad posterior, potencia estadística ni detección causal.

## Costos: no convertir unidades ilustrativas en utilidad económica

Registramos exactamente el ganador de la antigua puntuación para distintos factores `λ ∈ {0, 1/2, 1, 4/3, 3/2, 2, 3, 5}` y enumeramos todos los puntos de cruce entre puntuaciones. El costo se usa ahora **solo como límite presupuestal y eje de dominancia** frente al vector de hipótesis garantizadas por clase. No se utiliza el intercambio arbitrario 1 par ↔ 1 unidad.

Una acción domina a otra si cuesta lo mismo o menos, resuelve al menos tantas hipótesis en **cada una** de las tres clases y mejora estrictamente una de esas condiciones. Si existen varias opciones no dominadas, el selector corregido devuelve `UNRESOLVED_TRADEOFF_PRESENT_PARETO_FRONTIER` y **no ejecuta automáticamente ninguna** sin una preferencia de costo/calidad. Si ninguna medición tiene garantía positiva devuelve `STOP_NO_GUARANTEED_RESOLUTION` (no `STOP_NO_INFORMATION`, que sería una afirmación demasiado amplia). Si no sobrevive ninguna hipótesis, mantiene la brecha de modelo separada.

## Auditoría de combinaciones de mediciones

Se enumeran todos los **pares fijos** de acciones distintas con **presupuesto acumulado ≤8**, evaluando pureza robusta de la decisión bajo las dos observaciones y ±1 por componente. Se compara descriptivamente la mejor pareja y la mejor acción individual, reportando costos y resolución por clase. No se llama planificación secuencial/adaptativa a una pareja fija; **la elección de la segunda medición según el resultado de la primera sigue pendiente**.

## Nuevo barrido: evaluación de fragilidad, no validación independiente

Una vez generada y guardada con escritura exclusiva y `fsync` la auditoría **antes de cualquier nueva evaluación DES**, se ejecuta la siguiente matriz:

- **168 mundos**: cuello único en cada una de las 3 etapas, capacidad entera de **55 a 110 pedidos/h**. Incluye capacidades en la rejilla y entre nodos, y fuera del intervalo 60–105. Permite describir distancia al nodo más cercano, abstenciones y brechas por acción.
- **6 controles negativos**: dos etapas simultáneamente limitantes, con distintas posiciones y capacidades 55 y 90/h. Una etiqueta de cuello único en estos mundos es un *diagnóstico excesivo*, no un acierto.
- **2 mundos de cuatro etapas**: topología incompatible con los tres canales de sensor autorizados. Se devuelve `UNSUPPORTED_TOPOLOGY_FOUR_STAGES` antes de interpretar una lectura: no se truncarán físicamente 4 etapas a 3.

Se evalúan **todas las acciones viables del menú congelado** de CAF-07, como **contrafactuales del mismo selector**; no se afirma que en el barrido el sistema haya escogido y ejecutado una sola política adaptativa. Este barrido es retrospectivo, público, determinista y con el **mismo motor DES** para generar las predicciones de hipótesis y las respuestas de los mundos: no demuestra independencia entre familias de modelos, ni frecuencias generalizables a cafeterías reales. No se simulan tiempos estocásticos, porque el motor actual no los representa.

La decisión sobre qué medir en una empresa real todavía necesitará costos verificables, observaciones accesibles, incertidumbre de medición calibrada y una función de utilidad asociada a decisiones de intervención.

## Integridad y resultados

Antes del primer nuevo mundo se escriben `00_AUDITORIA_Y_PRECOMPROMISO.json` y `00B_CHECKPOINT_PRE_SWEEP.json` (hash verificado del PR #116, predicciones, costos y opciones, fronteras, resultados de pureza, configuración exacta de 176 mundos y acciones a medir). Luego se genera `01_RESULTADOS.json`, `02_BARRIDO_CASOS.csv`, `03_INFORME.md`, `04_MANIFIESTO.json`, con hashes locales y sin custodia externa.

```bash
python -m unittest discover -s experiments/cafeteria/pc02 -p 'test_caf07a_auditoria_decision.py' -v
python experiments/cafeteria/pc02/caf07a_auditoria_decision.py --out artifacts/caf07a-auditoria
```

El protocolo original CAF-07, las gramáticas M/D, los operadores prohibidos del contrato CAF-05 y ATMS permanecen intactos. Esta corrección **no actualiza automáticamente CAF-07 para futuras decisiones**: introduce una nueva API de política explícita que solo elige sola cuando existe una acción dominante en el menú y los supuestos declarados.
