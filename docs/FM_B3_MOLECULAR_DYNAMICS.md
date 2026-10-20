# FM-B3 — evaluación dinámica de alternativas moleculares

**Estado:** `B3_MOLECULAR_DYNAMICS_PASS_SYNTHETIC`, GitHub Actions run #14; correcciones de auditoría independientes verificadas.

## Pregunta

¿Puede IGC conservar varias explicaciones estructurales con soporte consistente, ejecutar cada una, excluir de la ejecución una alternativa que ATMS rechaza y evaluar si las trayectorias respetan los balances de existencias y flujos inducidos por sus moléculas?

## Qué añade B3

B3 compone tres estructuras de cadenas seriales (una, dos y tres etapas). El plan de soportes es explícitamente sintético: CS-01 y CS-02 retienen entornos compatibles; los dos entornos de CS-03 quedan cubiertos por `nogoods`. El probe ATMS mantiene CS-01 y CS-02 y rechaza CS-03. El generador de ejecuciones deriva sus clases exclusivamente de la selección verificada. El workflow comprueba que CS-03 no se simula ni produce CSV.

La salida JSON participa en una cadena de evidencia, pero no es el criterio de éxito. Cada modelo admisible se envuelve con sondas dinámicas que observan, sin alterar las ecuaciones de las moléculas:

- input acumulado, entregas acumuladas y stock total en espera;
- arrivals, completions y stock de cada cola;
- balance terminal entre entradas al contador y entregas.

Cada trayectoria debe tener 102 muestras finitas en el intervalo del plan; las marcas de tiempo pueden repetirse, pero no retroceder. La evidencia informa cuántas repeticiones hay y las filas/instantes donde aparecen. Stocks y cantidades acumuladas deben ser no negativos; entregas e input acumulado, monótonos.

Python reconstruye independientemente en cada muestra `ε(t) = acceptedTotal(t) - delivered(t) - Σ waiting_i(t)`. También reconstruye cada balance de cola a partir de entradas acumuladas, salidas acumuladas y stock exportado; los campos de error generados por Modelica se usan como comprobación cruzada, no como fuente del veredicto. Los errores absolutos independientes deben ser menores que `1e-5`.

## Evaluación comparativa

B3 informa diferencias de trayectoria y métricas de coherencia por candidato. Si dos estructuras distintas tienen trayectorias observables iguales dentro de tolerancia, se conservan y la pareja se informa como `NON_DISCRIMINATING`, con una sugerencia para probar una entrada pulsada y observar la recuperación. No ajusta parámetros a observaciones, no ordena candidatos, no infiere causalidad ni declara qué topología corresponde a un sistema real.

## Evidencia reproducible

GitHub Actions fija el runtime de OpenModelica y recupera revisiones inmutables de SystemDynamics y MSL. El artefacto registra hashes de plan, catálogo, composición, soportes, selección, evaluador, modelos, guion de ejecución y CSV. El verificador vuelve a calcular los soportes ATMS y revisa que el guion simule exactamente las alternativas admitidas. [Actions run #14 y artefactos](https://github.com/yudocyudoc/IGC/actions/runs/39495902441).

La corrida aceptó CS-01 y CS-02 y no simuló CS-03. Cada candidato tuvo 102 muestras y 30 unidades de input acumulado al final de 10 horas. Las entregas finales fueron 19.098606 para CS-01 y 17.098766 para CS-02; el máximo residuo global reconstruido independientemente fue `2.14e-14` y los de cola también quedaron por debajo de `3e-14`. La diferencia máxima entre las series de entrega fue 1.999840. Hubo un timestamp repetido en `t=10`, entre las filas 100 y 101. Estos valores son resultados del escenario sintético, no estimaciones empíricas.

Las pruebas negativas modifican en CSV solo `acceptedTotal` o las entradas acumuladas de una cola y conservan los campos de error Modelica; Python rechaza ambos archivos usando los balances reconstruidos. La prueba de comparación también conserva alternativas estructuralmente distintas cuando sus salidas son indistinguibles y las reporta como `NON_DISCRIMINATING`, con una perturbación sugerida.

## Límites

- Las tres topologías pertenecen a la familia `serial_chain`; B3 no descubre estructuras.
- Los soportes y `nogoods` son una fixture de ingeniería, no se derivan de RDF/CRMinf/SPARQL ni de evidencia empírica.
- La coherencia de stock y flujo confirma propiedades internas de estas ejecuciones sintéticas; no demuestra validez de un modelo de un caso real.
- El ATMS continúa siendo `f0-atms-feasibility/0.1`, sin retractación/versionado de producción.
- Los wrappers recuperados siguen siendo `POC_ONLY_NOT_ADMITTED`; el estado de licencias sigue `DEFERRED_BY_RESEARCHER`.

## Gate propuesto

`B3_MOLECULAR_DYNAMICS_PASS_SYNTHETIC` requiere: conservar y ejecutar CS-01 y CS-02; rechazar y no ejecutar CS-03; verificar de forma independiente procedencia y selección; pasar balances por cola y sistema; y reportar trayectorias distintas sin ranking ni afirmación empírica. La corrida #6 satisface estos criterios dentro del alcance sintético definido.
