# FM-B5 — identificabilidad con parámetros inciertos

**Estado:** experimento sintético pequeño; pendiente de evidencia de Actions y revisión científica.

## Pregunta

¿Puede un pulso reservado para evaluación distinguir una cadena de una etapa de otra de dos etapas después de que ambas ajusten sus parámetros a observaciones ruidosas de calibración?

## Separación de datos

El plan declara los rangos de ajuste: `maxThroughput` entre 1.2 y 2.4 unidades/h, en pasos de 0.2; `responseTime` entre 0.4 y 1.6 h, en pasos de 0.1. Son rangos didácticos de este escenario, no límites inferidos de un sistema ni recomendaciones para un caso real.

La calibración observa una entrada baja de 0.8 unidades/h durante 2 h y una ventana total de 8 h. El evaluador genera observaciones sintéticas con ruido gaussiano de desviación estándar 0.04 y ajusta **cada estructura por separado**, usando una búsqueda sobre la misma rejilla de parámetros. El límite de capacidad no se alcanza con esa entrada, de modo que su incertidumbre debe permanecer explícita.

Después del ajuste se reserva un segundo conjunto, con una semilla de ruido distinta: entrada de 3 unidades/h durante 2 h y seguimiento de la recuperación hasta 16 h. Ese conjunto no participa en el ajuste, la selección de parámetros ni la construcción de los intervalos predictivos. Se compara contra las predicciones de los puntos de rejilla compatibles con el ajuste dentro de `Δχ² = 5.991` (aproximación de perfil de verosimilitud al 95% para dos parámetros, con ruido conocido y rejilla discreta).

## Cálculo y regla de interpretación

El cálculo usa RK4 sobre las ecuaciones stock-flujo de las moléculas fuente auditadas: cada etapa acumula entradas menos terminaciones; la terminación es `min(stock/responseTime, maxThroughput)`; las entregas acumulan la terminación de la última etapa. El snapshot de `IGCMolecules.mo` y el commit fijado de SystemDynamics se registran en el reporte.

Se informa el RMSE de calibración, la comparación entre estructuras durante el ajuste, el conjunto de parámetros compatible y su envolvente de predicción para el pulso. Para comparar las trayectorias completas del conjunto reservado, el evaluador integra la verosimilitud de los datos de pulso sobre los pesos posteriores de cada punto de la rejilla, calculados exclusivamente con calibración y una prior uniforme declarada. Se informa el factor de Bayes predictivo con probabilidades previas iguales para ambas estructuras. La regla predeclarada solo marca `DISTINGUISHED_ON_HELD_OUT_PULSE` si el valor absoluto del log factor alcanza ln(10), es decir, odds predictivos de al menos 10:1. El solapamiento de envolventes marginales por tiempo se conserva como diagnóstico adicional, no como regla de decisión. De lo contrario informa `NOT_DISTINGUISHED_ON_HELD_OUT_PULSE`; no se trata como error de software.

## Límites científicos

- Los datos de calibración y evaluación son generados por una de las mismas estructuras que se están comparando. El resultado no demuestra identificabilidad frente a estructuras desconocidas ni frente a discrepancia del modelo.
- El ruido es gaussiano, independiente y con desviación conocida por construcción; no representa todavía un proceso de medición real.
- La rejilla es discreta y gruesa. Los conjuntos al 95% son aproximaciones condicionales al simulador, la rejilla y el ruido declarados.
- El simulador RK4 de este experimento implementa el contrato de las moléculas auditadas; no es el ejecutor OpenModelica. B4 ya verifica por separado la composición y ejecución de las estructuras con OpenModelica.
- El pulso y sus resultados no son óptimos, empíricos ni causales.
- No amplía el catálogo ni el motor ATMS. El estado de licencias sigue diferido.

La evidencia responderá una pregunta más acotada que «¿qué estructura es verdadera?»: **¿cuánta separación predictiva conserva el pulso reservado cuando cada topología puede compensar parte de su estructura ajustando parámetros dentro de estos rangos?**

## Resultado de la corrida sintética

GitHub Actions [run #4](https://github.com/yudocyudoc/IGC/actions/runs/39512219936) pasó las tres pruebas de B5 y ejecutó el ajuste/evaluación. Con la semilla declarada, la calibración favoreció CS-02 (RMSE 0.04345 frente a 0.08044 para CS-01). En ambos modelos la rejilla compatible dejó `maxThroughput` sin identificar dentro del rango completo [1.2, 2.4]; `responseTime` quedó en 0.8 h para CS-02 y en 1.6 h para CS-01.

En el pulso reservado, la media predictiva sobre los conjuntos de parámetros compatibles tuvo RMSE 0.08056 para CS-02 y 0.21464 para CS-01. Las envolventes se separaron por más de dos desviaciones de ruido en t=0.5, 1.0 y 1.5 h; la regla declarada produjo `DISTINGUISHED_ON_HELD_OUT_PULSE`, y CS-02 tuvo el menor error reservado. La evaluación de solo el punto de mejor ajuste dio un resultado peor para CS-02 debido a que el desempate escogió el throughput mínimo en una meseta no identificada. Por eso se reporta también el conjunto compatible y su media no ponderada, sin presentarla como posterior estadístico.

Este resultado muestra identificabilidad condicional dentro de un gemelo sintético con verdad CS-02 conocida por construcción. No es un descubrimiento sobre un sistema externo, y la calibración ya favorecía CS-02 antes de evaluar el pulso. El valor del pulso aquí es comprobar la predicción fuera de la condición de baja entrada y exponer la incertidumbre de capacidad que la calibración no resolvió.
