# FM-B3 — evaluación dinámica de alternativas moleculares

**Estado:** pendiente de ejecutar en GitHub Actions. La aceptación propuesta es sintética y acotada.

## Pregunta

¿Puede IGC conservar varias explicaciones estructurales con soporte consistente, ejecutar cada una, excluir de la ejecución una alternativa que ATMS rechaza y evaluar si las trayectorias respetan los balances de existencias y flujos inducidos por sus moléculas?

## Qué añade B3

B3 compone tres estructuras de cadenas seriales (una, dos y tres etapas). El plan de soportes es explícitamente sintético: CS-01 y CS-02 retienen entornos compatibles; los dos entornos de CS-03 quedan cubiertos por `nogoods`. El probe ATMS mantiene CS-01 y CS-02 y rechaza CS-03. El generador de ejecuciones deriva sus clases exclusivamente de la selección verificada. El workflow comprueba que CS-03 no se simula ni produce CSV.

La salida JSON participa en una cadena de evidencia, pero no es el criterio de éxito. Cada modelo admisible se envuelve con sondas dinámicas que observan, sin alterar las ecuaciones de las moléculas:

- input acumulado, entregas acumuladas y stock total en espera;
- arrivals, completions y stock de cada cola;
- balance terminal entre entradas al contador y entregas.

Cada trayectoria debe tener 102 muestras finitas en el intervalo del plan; las marcas de tiempo pueden repetirse en eventos de inicialización, pero no retroceder; stocks y cantidades acumuladas no negativos; entregas e input acumulado monótonos; y errores absolutos de balance no superiores a `1e-5`. Para cada cola se comprueba `arrivals acumuladas - completions acumuladas = stock`; para el sistema, `input acumulado = entregas + stocks en cola`. Las trayectorias admitidas deben usar la misma malla temporal y diferir en entregas para no colapsar en una misma explicación dinámica.

## Evaluación comparativa

B3 informa diferencias de trayectoria y métricas de coherencia por candidato. No ajusta parámetros a observaciones, no ordena los candidatos, no infiere causalidad ni declara qué topología corresponde a un sistema real. La comparación comprueba que las explicaciones retenidas son estructuralmente distintas y tienen consecuencias dinámicas diferenciables bajo los mismos parámetros y entrada sintéticos.

## Evidencia reproducible

GitHub Actions fija el runtime de OpenModelica y recupera revisiones inmutables de SystemDynamics y MSL. El artefacto registra hashes de plan, catálogo, composición, soportes, selección, evaluador, modelos, guion de ejecución y CSV. El verificador vuelve a calcular los soportes ATMS y revisa que el guion simule exactamente las alternativas admitidas.

## Límites

- Las tres topologías pertenecen a la familia `serial_chain`; B3 no descubre estructuras.
- Los soportes y `nogoods` son una fixture de ingeniería, no se derivan de RDF/CRMinf/SPARQL ni de evidencia empírica.
- La coherencia de stock y flujo confirma propiedades internas de estas ejecuciones sintéticas; no demuestra validez de un modelo de un caso real.
- El ATMS continúa siendo `f0-atms-feasibility/0.1`, sin retractación/versionado de producción.
- Los wrappers recuperados siguen siendo `POC_ONLY_NOT_ADMITTED`; el estado de licencias sigue `DEFERRED_BY_RESEARCHER`.

## Gate propuesto

`B3_MOLECULAR_DYNAMICS_PASS_SYNTHETIC` requiere: conservar y ejecutar CS-01 y CS-02; rechazar y no ejecutar CS-03; verificar de forma independiente procedencia y selección; pasar balances por cola y sistema; y reportar trayectorias distintas sin ranking ni afirmación empírica.
