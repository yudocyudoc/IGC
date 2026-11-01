# CAF-11 — Protocolo previo a CI: inversión paramétrica exacta de un DES determinista

**Fecha:** 2026-10-31. **Estado:** primer commit del laboratorio, anterior al ejecutor y su evaluación. **Rama:** `experiment/caf11-parametric-des-inversion-20261031`, basada directamente en `main` donde CAF-07B (#118) ya está fusionado. No depende de los PR Draft #119–#122 y no modifica sus resultados.

## Pregunta científica acotada

En el modelo DES exacto de CAF-01, con una estructura conocida condicional y **una capacidad común real y continua** en un rango físico, ¿es posible recuperar el **conjunto completo de capacidades compatibles** con dos observaciones de entregas acumuladas (K0 y K1) sin perder capacidades intermedias por la cuadrícula discreta `60/75/90/105` de CAF-07B?

**No investigamos todavía selección de K2, servicio estocástico, timestamps ni optimización de política.** Primero validar el inversor bajo hipótesis físicas explícitas.

## Modelo físico y dominio

- Seis estructuras predeclaradas: único cuello nominal en preparación, despacho o entrega; doble nominal en pares (preparación, despacho), (preparación, entrega), (despacho, entrega).
- Para etapa limitada, `servers=1`, tiempo de servicio constante exacto `d=60/c` minutos; para las demás, `servers=2`, servicio 1 minuto.
- **Un único parámetro continuo compartido `c∈[55,110]` pedidos/hora**, equivalente a `d∈[6/11,12/11]`. Para los dobles se comparte el mismo `d`. Esto NO modela velocidades independientes por etapa ni variabilidad estocástica.
- Llegadas racionales `DES.half_open_arrivals`; K0 entregas acumuladas a minuto 10 con tasa 6/5 pedidos/min, K1 entregas acumuladas a minuto 20 con tasa 3/2 pedidos/min. Cada prueba reinicia el mismo sistema físico; no se asume una trayectoria continua entre K0 y K1.
- Banda original **±1 pedido**, considerada tolerancia formal de robustez **no calibrada** (NO distribución de ruido ni sensor validado). Compatibilidad conjunta con las dos observaciones y el **mismo `c`** para ambas. No permitir cambiar c entre K0 y K1.
- Las leyes de conservación, orden FCFS, eventos simultáneos y `DES.TIE_POLICY` permanecen intactos.

## Algoritmo de inversión y alcance de la garantía

Para **esta subfamilia determinista de colas en tándem con servidores paralelos idénticos y servicio de duración constante**, la terminación del pedido `i` en etapa `s` puede modelarse mediante la recurrencia de tiempos de salida:
`D[s,i](d)=max(D[s-1,i](d),D[s,i-m_s](d))+t_s(d)`,
donde `D[-1,i]=arrival[i]`, `D[s,j]=0` si `j<0`, `m_s` es el número de servidores y `t_s(d)` es `d` o `1`. La recurrencia asume explícitamente que los pedidos no se adelantan con tiempos homogéneos por etapa y FIFO; **debe verificarse su paridad con el motor DES original incluyendo empates**.

Las expresiones generadas por constantes, sumas y máximos de funciones afines de `d` son **continuas y lineales por tramos, con quiebres racionales**. Implementar una representación racional exacta con `fractions.Fraction`; calcular todos los puntos de corte de cada `D[last,i](d)` con los horizontes K0/K1. Entre los cortes, los conteos enteros son constantes; evaluar un representante racional de **cada intervalo abierto** y también **cada punto de corte como singleton** (por convención el DES procesa terminaciones con tiempo ≤ observación).

Para cada estructura, conservar la unión de regiones `c` donde **ambas** lecturas cumplen simultáneamente la banda ±1. Representar extremos exactos, apertura/cierre y regiones desconectadas si ocurren. **No declarar matemáticamente certificados intervalos que provengan solo de una malla arbitraria o muestreo**. Si no se logra demostrar/implementar la recurrencia y el aislamiento exhaustivo de raíces bajo esta familia, la salida debe llevar `CONTINUUM_NOT_CERTIFIED` y no interpretarse como cobertura exacta.

**Límites:** la demostración, si se obtiene, es sobre la familia construida y su DES determinista, no sobre cafeterías reales, otros regímenes de servicio, múltiples capacidades libres, colas con prioridades ni topologías desconocidas.

## Baseline y mundos, predeclarados antes de evaluar

**Baseline:** banco de 24 hipótesis puntuales de CAF-07B: cuatro capacidades `60,75,90,105`, seis estructuras, compatibilidad conjunta K0/K1 ±1. Importar las funciones originales; no adaptar el baseline a los mundos.

**Mundos de evaluación, 20 casos conocidos explícitamente (todos sintéticos):**
- 9 únicos: cada cuello nominal (0,1,2) a capacidades `(68,83,97)` pedidos/h.
- 9 dobles: cada par (01,02,12) a capacidades `(69,83,97)` pedidos/h.
- 2 controles con cuarta etapa oculta: capacidad `(64,86)` pedidos/h en la cuarta etapa, primeras tres etapas no limitadas (`servers=2`, servicio 1 minuto). **No exponer estructura de verdad al inversor.** La etiqueta verdadera NO existe en el catálogo y la cobertura de clase es `N/A`, nunca 0.
- Total **20 mundos × 6 familias = 120 inversiones**; dos lecturas físicas K0/K1 por mundo, más pruebas internas de paridad del motor. Los mundos replican patrones ya examinados en otros PR; son nuevos valores seleccionados aquí pero **NO holdout independiente**, ni resultado generalizable.

## Métricas y falsadores

Por mundo y familia:
- conjunto factible de capacidades/duraciones con extremos racionales e inclusión de extremos;
- si contiene la capacidad física verdadera cuando la familia corresponde a la clase (contención del parámetro verdadero);
- clases estructurales compatibles, cantidad de clases y `MODEL_INCONSISTENT_UNDER_SPECIFIED_BOUNDS` cuando ninguna; **nunca interpretar directamente como cuarta etapa**;
- baseline puntual vs conjunto continuo: cobertura de clase y `false_empty` en mundos in-family;
- tamaño del conjunto (puede ser un intervalo ancho), y equivalencias entre estructuras aun con regiones no vacías;
- tiempo/costo de cálculo de inversión, separado de beneficios de diagnóstico.

**Falsadores y gates:**
1. Paridad de predicciones exactas del calendario simbólico vs DES nativo en capacidades racionales y en puntos de corte.
2. Comprobación de masa y tratamiento de simultaneidad originales conservados.
3. Si al evaluar un mundo con estructura y c dentro de la familia, pero observaciones exactas y ±1, la región del modelo verdadero no contiene ese c: **error real de algoritmo/representación**, gate rojo.
4. Ningún estado `UNKNOWN_TOPOLOGY_CONFIRMED` está permitido; el conjunto vacío demuestra únicamente incompatibilidad bajo supuestos.
5. Los cortes, los singleton y la apertura de extremos deben auditarse: un evento exactamente en t puede cambiar el conteo puntual respecto de un lado.
6. La alternativa no puede usar verdad del mundo durante el filtrado, y el resultado no puede ser optimizado a posteriori.
7. Registro de precompromiso y SHA de workflow (head PR distinto a checkout merge), manifest SHA256, persistencia del plan **antes** de simular mundos de evaluación.
8. El gate `BLOCKED_SAME_DES_PHYSICS_UNCALIBRATED_TOLERANCE` permanece activo aun si el método mejora la cobertura. Revisión adversativa antes de fusionar.

El objetivo es determinar si una primera inversión paramétrica exacta y físicamente acotada **resuelve el artefacto de la rejilla discreta**, no afirmar que identifica topologías en general. Un fallo informativo es perfectamente aceptable.
