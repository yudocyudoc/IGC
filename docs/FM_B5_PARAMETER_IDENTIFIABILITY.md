# FM-B5 — identificabilidad con parámetros inciertos

**Estado:** `B5_PARAMETER_IDENTIFIABILITY_EVALUATED_SYNTHETIC`; PR #14 en borrador, pendiente de revisión científica.

## Pregunta

¿Puede un pulso reservado para evaluación distinguir una cadena de una etapa de otra de dos etapas después de que ambas ajusten sus parámetros a observaciones ruidosas de calibración?

## Separación de datos

El plan declara los rangos de ajuste: `maxThroughput` entre 1.2 y 2.4 unidades/h, en pasos de 0.2; `responseTime` entre 0.4 y 1.6 h, en pasos de 0.1. Son rangos didácticos de este escenario, no límites inferidos de un sistema ni recomendaciones para un caso real.

La calibración observa una entrada baja de 0.8 unidades/h durante 2 h y una ventana total de 8 h, con observaciones cada 2 h. El evaluador genera datos sintéticos con ruido gaussiano de desviación estándar 0.08 y ajusta **cada estructura por separado**, usando una búsqueda sobre la misma rejilla de parámetros. El límite de capacidad no se alcanza con esa entrada, de modo que su incertidumbre debe permanecer explícita.

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

GitHub Actions [run #10](https://github.com/yudocyudoc/IGC/actions/runs/39512750432) pasó las tres pruebas y ejecutó el ajuste y la evaluación reservada. La calibración favoreció CS-02 (RMSE 0.02259 frente a 0.06743 para CS-01). Aun así, el conjunto compatible dejó `maxThroughput` sin identificar en el rango completo [1.2, 2.4] para ambas estructuras; `responseTime` quedó entre 1.2–1.6 h para CS-01 y 0.6–0.9 h para CS-02.

Para el pulso reservado, el RMSE de la media predictiva fue 0.26187 para CS-01 y 0.09392 para CS-02. El log factor de Bayes predictivo CS-02/CS-01 fue 65.714, frente al umbral predeclarado ln(10) ≈ 2.303, por lo que el resultado fue `DISTINGUISHED_ON_HELD_OUT_PULSE`. CS-02 también recibió mayor densidad predictiva en los datos reservados. Las envolventes predictivas marginales de los dos modelos se solaparon en las 33 observaciones: la separación aparece al considerar la verosimilitud conjunta de toda la trayectoria, no al exigir que los rangos en un instante aislado sean disjuntos.

La conclusión es condicional a este gemelo sintético, a la prior uniforme de rejilla, al ruido conocido y a estas dos estructuras. La verdad generadora es CS-02 por construcción; no es conocimiento descubierto sobre un sistema externo. La calibración ya favorecía CS-02, mientras que el pulso reservado confirma su capacidad predictiva fuera de la entrada baja, aunque `maxThroughput` permanece incierto.
