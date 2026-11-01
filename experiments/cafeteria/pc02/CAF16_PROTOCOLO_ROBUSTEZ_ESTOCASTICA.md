# CAF-16 — Protocolo previo: robustez a servicio estocástico, error de sensores y pulso de demanda

**2026-10-31 hora de México. PR nuevo apilado sobre CAF-15B PR #128, cabeza `9ed0ab45a72dbac10f18679a023f65068ab29726`, sin fusionar.** Este es el PRIMER commit de CAF-16, ANTES de escribir o ejecutar el código. CAF-11–15B y motor CAF-01 no se modifican.

## Pregunta

CAF-15B demostró, CONDICIONAL a servicio homogéneo determinista y conteos de error ±1, 11/15 pares de familias separables con capacidades independientes c1,c2∈[55,110] bajo demanda constante sintética 150/h y observación t20 o t25. **No** demuestra que un clasificador construido para esa física conserve cobertura bajo variabilidad física. Pregunta de CAF-16: ¿con qué frecuencia un filtro DETERMINISTA congelado **pierde la clase nominal correcta, produce conjunto vacío o falso único** cuando el generador evaluador utiliza duraciones aleatorias físicamente variables y sensores con error de conteo explícito? ¿En qué difieren un pulso alto sostenido y una demanda sintética temporalmente modulada?

**No trasladar certificados globales de CAF-15B al simulador estocástico**. No búsqueda de una tasa o configuración óptima. No afirmación de «natural overload»: la demanda modulada es sintética, no una ventana de una cafetería real.

## Mundos FIJOS, capacidades independientes, controles desconocidos

- 27 mundos representados: **9 singles** (preparación/despacho/entrega × capacidades 68,83,97/h), **18 doubles off-diagonal** (3 pares de etapas × capacidades ordenadas `(68,70),(70,68),(83,86),(86,83),(95,100),(100,95)`). La configuración de las tres etapas mantiene `servers=1` en las limitadas, `servers=2, base_service=1min` en las otras. Cada servicio limitado tiene duración media `60/c_s`, **c1 y c2 independientes**. No inventarios ni recursos compartidos.
- **3 controles topológicos fuera de catálogo**: cuarta etapa adicional `servers=1, mean_service=60/c` con `c=64,106,220/h`; las tres primeras etapas tienen dos servidores y servicio medio 1 minuto. Se mide solamente las primeras tres etapas. Estos controles siguen el esquema de CAF-15A, con constructor explícito que permite 220/h. No afirmar que cuarta etapa rápida sea invisible.
- **30 mundos** y etiquetas/verdades solo disponibles para análisis evaluador, nunca a la inferencia.

## Generador estocástico independiente de CAF-01 y del inversor

- Nuevo motor de eventos local: colas FIFO, llegada y completación exactas con `fractions.Fraction`, servicio positivo, política fija `COMPLETE_THEN_ACCEPT_THEN_START_DOWNSTREAM_FIRST`, número de servidores respetado, pedidos conservados en todo instante. No llamar `caf01_des_engine.run_toy_engine` **para generar** los mundos estocásticos; usarlo solo como **oráculo de paridad** de la versión sin variabilidad. Código del motor deberá ser independiente de la recurrencia de CAF-15B.
- Servicio multiplicativo i.i.d. por **pedido y etapa**, aplicado a TODAS las etapas (incluidas no limitadas y 4ª oculta), con factores equiprobables:
  - `CV0` = `{1}` (control determinista, sin sorteos de servicio);
  - `CV25` = `{3/4,5/4}` (media 1, coeficiente de variación 0.25);
  - `CV50` = `{1/2,3/2}` (media 1, coeficiente de variación 0.50).
- Los factores anteriores son **hipótesis instrumentales**, NO distribuciones empíricas calibradas. Cada trayectoria usa un generador `random.Random` independiente, semilla derivada con `sha256` de una cadena base `IGC-CAF16-20261031-v1`, mundo, réplica, nivel CV, identificador del pulso. Orden de sorteos según inicios reales de servicio; conservar orden de empates. Las réplicas y subexperimentos con distinta tasa se **reinician**, pero comparten capacidades del mismo mundo.

## Programas y sensor, ANTES de evaluar

Para TODOS los programas K0 y K1 se mantienen idénticos a CAF-15B: K0 entregas t10 tasa 6/5/min, K1 entregas t20 tasa 3/2/min (pulso [0,20), K0 observa el prefijo). Un ensayo T adicional:
- `HIGH_T20`: tasa constante 5/2 por minuto durante [0,20), seis canales `waiting_p,d,e`, `stage_stock_p,d,e` a **t20**.
- `SHAPED_T14_T20`: pulso sintético de **tasa segmentada**: [0,6) = 6/5/min; [6,14) = 5/2/min; [14,20) = 6/5/min. Sondas de los MISMOS seis canales en **t14 y t20 de UNA SOLA trayectoria**. La demanda modulada es exógena/sintética, no observada en una PYME.
- En ambos programas K0/K1 son ensayos separados con misma capacidad, no replicación física del ensayo T; las dos lecturas de SHAPED pertenecen a una sola trayectoria.
- Dos condiciones de error instrumental INDEPENDIENTES del servicio: `E0` lectura exacta, `E1` suma de una perturbación entera uniforme en `{-1,0,+1}` para CADA canal y snapshot, recortada inferiormente a 0. Semilla `sha256` independiente por lectura, mundo/réplica/CV/programa para **NO** hacer pasar variabilidad física por error de sensor. Banda de compatibilidad del analista **se mantiene ±1** en ambas E0/E1, sin reajustar el clasificador. `E1` es solo una perturbación simulada acotada, no un modelo calibrado.
- **12 réplicas fijas** por mundo, factor de servicio, condición E y programa. Total `30 mundos×3 CV×2 E×2 programas×12 réplicas=4,320` lecturas programadas. **3,888 lecturas representadas, 432 topologías fuera de familia**. Para E0/E1 de un mismo mundo/réplica/CV/programa reusar exactamente la MISMA trayectoria estocástica y variar solo el sensor.

## Analista congelado: comparar física distinta sin fuga de verdad

- Analista CATEGÓRICO predefinido: catálogo de **720 configuraciones deterministas** de CAF-15A, `C=[55,60,65,68,70,75,80,83,86,90,95,97,100,105,110]`, 45 singles + 675 doubles. No entrenar un nuevo clasificador probabilístico, no elegir parámetros por la verdad, no agregar entradas a la rejilla después de resultados. **La malla NO certifica compatibilidad/separación en el continuo.**
- Generar y guardar catálogo de firmas **antes de cualquier evaluación estocástica**. Para `HIGH_T20` reutilizar las firmas de `CAF15A.compute_bank` o regenerarlas y comprobar igualdad. Para `SHAPED_T14_T20` generar pronósticos DETERMINISTAS con motor independiente y verificar paridad con `caf01_des_engine.run_toy_engine` en ejemplos. Para K0/K1 mantener el mismo vector de capacidades dentro del programa.
- Un modelo determinista explica lectura entera `y` si **`|pred_j−y_j|≤1` en TODOS los canales**. Reportar `n_classes`, `true_class_covered`, `n_zero_classes`, `n_singletons_correct`, `n_singletons_false` por estrato mundo conocido/desconocido, CV, E y programa. **No llamar a conjunto vacío un modelo desconocido demostrado**: solo `NO_LATTICE_MATCH` bajo modelo determinista.
- Todas las capacidades verdaderas de los 27 mundos representados están deliberadamente en la malla: CV0/E0 debe recuperar clase correcta en **27/27 mundos ×12×2 programas**, autoconsistencia. Los demás estratos no tienen requisito de buen resultado; cualquier pérdida de cobertura es hallazgo adverso válido.
- Los resultados de E0/E1 son comparaciones emparejadas de las mismas trayectorias, pero **las 12 réplicas NO son 12 mundos independientes**. No construir intervalos de confianza ni extrapolar tasas sintéticas a mundo real.
- Los controles con cuarta etapa nunca tienen `true_class` representada. Reportar conjunto vacío, clase única falsa y subconjunto compatible por programa, sin fingir sensibilidad universal a unknown.

## Pruebas físicas y compuertas

1. Paridad del motor estocástico con DES CAF-01 cuando CV0 en **ambos programas, K0, K1, HIGH y SHAPED**, con capacidad simple, doble independiente y cuarta etapa; errores de sensor deshabilitados. Mismo orden de eventos en empates.
2. Conservación en cada snapshot: `accepted=delivered+∑waiting+∑in_service`, `active_servers≤available_servers`, id de pedido no duplicado, servicio positivo y FIFO. El pulso de demanda queda abierto en frontera y no acepta llegadas futuras después de observación.
3. Validar la distribución discreta de cada CV (media uno y varianza exacta), independencia de semillas servicio vs sensor, reproducibilidad bit a bit con SHA de los resultados. El observador nunca recibe configuración física ni etiqueta de verdad.
4. Validar igualdad de firma deterministic HIGH con `CAF15A.native_readings` para un subconjunto fijo de configuraciones y de SHAPED con el DES nativo en todos los instantes; no asumir que observaciones t14/t20 de SHAPED son réplicas independientes.
5. Comparar E0 y E1 contra el **mismo** ID de trayectoria y comprobar que cada canal difiera a lo sumo un pedido y sea no negativo.
6. Guardar `00B_CATALOGO_PRE_EVALUACION.json` y `00_PLAN_PRE_EVALUACION.json` ANTES de ejecutar mundos, con SHA256; `01_RESULTADOS.json` de 4320 casos, `02_INFORME.md` y manifiesto. Registrar HEAD y checkout SHA distintos; semillas y esquema sin cambios. No adaptar mundo, malla, tolerancia ni umbral al resultado.
7. No imponer mejora o degradación en CI. CI comprueba causalidad del prefijo, paridad, coherencia y auditabilidad, no «éxito» de un selector.
8. Gate permanente `BLOCKED_SYNTHETIC_STOCHASTIC_SERVICE_UNCALIBRATED_SENSORS_NO_EXTERNAL_VALIDATION`; Draft sobre #128, sin merge, sin desplegar ni recomendar inducir una sobrecarga comercial.

## Después de esta fase

Un fallo del analista determinista ante variabilidad simulada puede motivar un **modelo explícito de ruido y distribuciones** y datos de sensores reales, no una búsqueda post hoc de tolerancia «ganadora». El test de pulso segmentado **NO equivale** a identificar ventanas de sobrecarga natural en empresas. No presentar resultados como prueba de transferencia entre generadores independientes: aunque este motor de eventos se escriba aparte, conserva las mismas hipótesis estructurales FIFO de CAF-01 y no es evidencia de mundo real.
