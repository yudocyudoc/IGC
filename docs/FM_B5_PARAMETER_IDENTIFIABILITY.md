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

Se informa el RMSE de calibración, la comparación entre estructuras durante el ajuste, el conjunto de parámetros compatible y su envolvente de predicción para el pulso. El RMSE reservado se calcula sobre la media no ponderada de los puntos de rejilla compatibles con la calibración para evitar que un desempate arbitrario del mejor punto en una meseta de throughput determine la evaluación. Esa media no es una estimación bayesiana. La regla predeclarada solo marca `DISTINGUISHED_ON_HELD_OUT_PULSE` si las envolventes se separan por al menos dos desviaciones de ruido en tres o más observaciones y la ventaja de RMSE reservado alcanza una desviación de ruido. De lo contrario informa `NOT_DISTINGUISHED_ON_HELD_OUT_PULSE`; no se trata como error de software.

## Límites científicos

- Los datos de calibración y evaluación son generados por una de las mismas estructuras que se están comparando. El resultado no demuestra identificabilidad frente a estructuras desconocidas ni frente a discrepancia del modelo.
- El ruido es gaussiano, independiente y con desviación conocida por construcción; no representa todavía un proceso de medición real.
- La rejilla es discreta y gruesa. Los conjuntos al 95% son aproximaciones condicionales al simulador, la rejilla y el ruido declarados.
- El simulador RK4 de este experimento implementa el contrato de las moléculas auditadas; no es el ejecutor OpenModelica. B4 ya verifica por separado la composición y ejecución de las estructuras con OpenModelica.
- El pulso y sus resultados no son óptimos, empíricos ni causales.
- No amplía el catálogo ni el motor ATMS. El estado de licencias sigue diferido.

La evidencia responderá una pregunta más acotada que «¿qué estructura es verdadera?»: **¿cuánta separación predictiva conserva el pulso reservado cuando cada topología puede compensar parte de su estructura ajustando parámetros dentro de estos rangos?**
