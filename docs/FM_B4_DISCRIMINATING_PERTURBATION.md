# FM-B4 — explicación estructural y perturbación discriminante

**Estado:** experimento sintético en revisión; no implica admisión de wrappers ni evaluación empírica.

## Pregunta

¿Puede IGC conservar varias explicaciones moleculares admitidas por ATMS, describir qué cambia en su estructura, ejecutar ambas ante una perturbación finita y relacionar esa diferencia estructural con sus trayectorias y saturaciones?

## Escenario

El plan declara tres cadenas seriales candidatas. ATMS conserva CS-01 (una cola) y CS-02 (dos colas) y excluye CS-03 por el `nogood` sintético de la fixture. Ambas candidatas admitidas reciben 3 unidades/h durante 2 h y luego 0 durante 14 h. OpenModelica simula las dos; CS-03 no se ejecuta.

La prueba no se reduce a pasar una selección JSON al simulador. Antes de simular, el evaluador verifica hashes de procedencia y deriva una caracterización acotada desde las estructuras compuestas y las firmas de `IGCMolecules.mo`. Para cada candidato informa moléculas, stocks, conexiones, número de bucles internos de balance, límites de throughput, parámetros de respuesta, ciclos entre moléculas y tiempos de saturación observados.

## Explicación estructural prevista

La fuente aceptada transmite la tasa de entrada. Cada `BoundedQueue` contiene un stock y un flujo de liberación acotado. En el código fuente fijado, el nivel alimenta una respuesta proporcional (`1/responseTime`), que gobierna la liberación y reduce el mismo stock: un bucle interno de balance negativo por etapa. El contador terminal acumula entregas y no devuelve una señal a las colas.

CS-02 agrega una instancia de cola serial: frente a CS-01 tiene un stock, un bucle de balance y una etapa de respuesta adicionales. El grafo externo de conexiones permanece acíclico; no hay feedback entre moléculas. La suma de parámetros `responseTime` se reporta como descriptor de composición, no como retardo total calculado del sistema. La capacidad indicada es un límite declarado por cola; la saturación se informa solo cuando la tasa exportada alcanza ese límite.

La auditoría no pretende ser un parser general de Modelica. Requiere coincidencia exacta con firmas de moléculas del snapshot cuya suma SHA-256 aparece en `provenance.json`; si la fuente cambia, el diagnóstico falla hasta revisar sus reglas.

## Qué se observa y qué pregunta sugiere

El verificador reconstruye de forma independiente los balances de sistema y de cada cola según el contrato B3. Conserva la malla temporal planeada y permite muestras adicionales producidas por eventos del pulso; informa marcas repetidas y falla si falta un punto de la malla o el tiempo retrocede. Además compara entregas acumuladas durante la cola de recuperación, entregas al terminar el pulso, stock en espera por etapa y saturación observada. La relación puede ser `DISCRIMINATING` o `NON_DISCRIMINATING`; en el segundo caso se conservan ambas explicaciones sin ranking.

La pregunta experimental sugerida para un sistema observado es: **tras una entrada finita y conocida, ¿cómo se distribuyen las entregas y los stocks de espera entre las etapas durante la recuperación?** Medir la trayectoria acumulada de entregas y los stocks por etapa permitiría contrastar estas topologías. El pulso de 2 h es una propuesta exploratoria de este escenario sintético, no una perturbación óptima ni validada empíricamente.

## Evidencia de Actions

GitHub Actions [run #6](https://github.com/yudocyudoc/IGC/actions/runs/39497848876), sobre el commit `bad8a37d3f24b89a6a1c52efed66a229d06a918c`, pasó todas las etapas. Cada CSV tuvo 165 muestras: 160 intervalos planeados más registros adicionales de eventos. Se simularon CS-01 y CS-02; CS-03 no produjo CSV.

Ambas estructuras recibieron 6 unidades y terminaron con aproximadamente 6 entregadas (CS-01: 5.999997; CS-02: 5.999959). Al finalizar el pulso, CS-01 había entregado 3.098606 y CS-02 1.544656. La entrega adicional durante la recuperación fue 2.901391 frente a 4.455303; la diferencia máxima de trayectoria durante esa cola fue 1.734993 unidades. En la primera cola se observó saturación de 2 unidades/h en 16 muestras, entre t=1.1 y t=2.4; la segunda cola de CS-02 no llegó al límite en esta corrida. Las métricas satisfacen los balances reconstruidos independientemente por B3. Son resultados de esta ejecución sintética.

## Límites

- Estructuras, parámetros, soporte ATMS y entrada son sintéticos.
- Las moléculas son PoC, siguen `POC_ONLY_NOT_ADMITTED` y la revisión de licencias queda diferida.
- La detección de bucles se limita a firmas fuente verificadas de estas moléculas.
- La simulación caracteriza consecuencias de las estructuras implementadas; no demuestra cuál representa un sistema real ni establece causalidad.
- Si dos trayectorias son indistinguibles, el resultado es informativo y no un fallo de investigación.

## Gate propuesto

`B4_DISCRIMINATING_ANALYSIS_PASS_SYNTHETIC` requiere: procedencia íntegra; selección ATMS reproducible; ejecución de todas y solo las alternativas admitidas; caracterización estructural basada en fuente; balances B3; saturación calculada de tasas observadas; comparación de las trayectorias de pulso y recuperación; y una pregunta de medición explícita sin ranking ni afirmación empírica.
