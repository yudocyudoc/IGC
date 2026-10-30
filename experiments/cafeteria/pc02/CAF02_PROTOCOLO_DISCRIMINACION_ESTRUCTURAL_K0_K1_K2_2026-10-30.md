# CAF-02 — Recuperación del objetivo estructural K0 → K1 → K2

**30 de octubre de 2026. Estado: DISEÑO PREPARATORIO, NO PREREGISTRO, NO AUTORIZACIÓN DE NUEVO DES.**

**Fuente rectora:** docs/ARENA_PLAN_CAMPANA_CAFETERIA_V3_0_2026-10-27.md, sección 7. La pregunta de CAF-02 es si ARENA distingue mecanismos rivales y revisa sus hipótesis con evidencia pertinente. El PR #99 solo probaba calibración C00 y queda como componente auxiliar; no sustituye el objetivo estructural original.

## Rivales existentes, no moléculas nuevas

- C00 = fuente → preparación BoundedQueue → despacho BoundedQueue → contador de entregas.
- C01 = fuente → preparación BoundedQueue → despacho BoundedQueue → **tránsito BoundedQueue adicional** → contador de entregas.

Son grafos materiales distintos ya previstos en el registro E1. El componente nuevo no altera bibliotecas ni fórmulas: cada etapa usa release = min(capacidad, stock/responseTime). C00 y C01 deben tener oportunidad de ajustar los parámetros en K0 con reglas declaradas y presupuestos contabilizados. No basta demostrar diferencias entre dos configuraciones nominales fijadas arbitrariamente; deben contrastarse **conjuntos calibrados**.

La integración numérica de este PR es una sonda sintética de las ecuaciones existentes. No equivale a G2 de OpenModelica; antes de inferencia competitiva deberá comprobarse paridad nativa y tener los mismos contratos observables para los brazos que participen.

## Tres niveles de restricciones

1. **Matemáticas/materiales: obligatorias.** Tiempos efectivos positivos, unidades y fronteras coherentes, conservación, stocks no negativos, capacidades finitas; rangos exploratorios y criterios de adecuación absoluta fijados **antes de nuevos datos**.
2. **Operacionales: condicionadas a afirmaciones reales.** Justificar tiempos y capacidades contra una cafetería concreta si se pretende hablar de esa operación. No confundir el responseTime efectivo (stock/salida) con los minutos físicos de preparación por pedido.
3. **Identificación: objeto de prueba.** No dar por identificados tiempos de cada etapa ni la estructura si observaciones de entregas admiten equivalencias.

**Corrección científica del calibrador PR #99:** ahora la admisión exige simultáneamente MAE del candidato menor o igual a (a) el mejor de la familia más tolerancia relativa y (b) un máximo absoluto declarado. Si todas las configuraciones explican mal K0, el calibrador publica NO_ADEQUATE_CANDIDATE_ABSTAIN_ALL_FORECASTS; no crea una envolvente estrecha engañosa. Los umbrales de CI son **ilustrativos**, no rangos aprobados para la campaña.

## Protocolo K0 → K1 → K2

| Corte | Información permitida | Acción | Resultado obligatorio |
|---|---|---|---|
| **K0** | Perfil de llegada y mediciones limitadas de construcción | Calibrar **ambas estructuras** en rejillas declaradas. Conservar todas las alternativas suficientemente adecuadas. | Conjuntos C00 y C01, calidad absoluta por familia, denominadores y posibles abstenciones |
| **Diseño de K1** | Solo hipótesis K0 y menú público de mediciones | Calcular el rango predicho de **todos** los miembros de cada estructura para cada alternativa del menú. Elegir la mayor separación **robusta** y fijar la opción antes de conocer el resultado. | Opción elegida o MENU_CANNOT_ROBUSTLY_DISCRIMINATE |
| **K1** | Una medición/intervención seleccionada y anunciada antes | Filtrar rivales por contradicción con K1 sin cambiar estructura de búsqueda ni regla. Etiquetar revisión paramétrica, epistémica o estructural, o ninguna. | Linaje con alternativas retenidas y descartadas; sin fabricar una conclusión |
| **Pre-K2** | K0, K1 y pulso público K2, sin su respuesta | Congelar por separado las predicciones **K0 anteriores** y **K1 revisadas** bajo las mismas condiciones futuras; referencias REF-CAF y REF-SCALE comparables. | Dos versiones selladas, abstenciones visibles y custodia independiente |
| **K2** | Solo tras sello y autorización específica | Evaluar contra observaciones nuevas no usadas en K0/K1, sin reajustar. | MAE/RMSE de K0 vs K1 y de referencias, cobertura/anchura de alternativas y costos |

**Menú K1 implementado inicialmente:** entregas acumuladas en uno de los tiempos permitidos, bajo un pulso alternativo público con reinicio vacío. Este menú utiliza un observable que ya contempla el contrato; **no** asegura que discrimine. La separación robusta es la distancia positiva entre los intervalos de salida que contienen todos los miembros calibrados de ambas estructuras; intervalo solapado = separación cero. Se exige un mínimo de separación elegido con anterioridad.

Si ninguna de esas medidas separa las familias tras calibración, reportar INSUFFICIENT_OBSERVABILITY_FROM_MENU. Podrá estudiarse después una medición de stock intermedio o tiempos de paso, pero **no** añadirla retroactivamente para forzar éxito. Ejecutar K1 con reinicio constituiría una invocación adicional de mundo y exige presupuesto propio; el CI actual no invoca ningún DES.

## Desenlaces negativos o no identificables que deben registrarse

- **Ninguna familia adecuada en K0:** familia de modelos insuficiente dentro del rango probado; no emitir punto ni intentar K1 como si existiera rivalidad.
- **Solo una familia adecuada en K0:** no se activó la pregunta de discriminación con evidencia adicional; no declarar éxito K1.
- **Ambas adecuadas pero el menú K1 no separa:** observabilidad insuficiente bajo los estímulos y observables ensayados. No demuestra imposibilidad global.
- **K1 elimina ambas:** evidencia contradictoria para ambas familias dentro del espacio probado, no permiso para cambiar estructura después de ver la verdad.
- **K1 conserva ambas:** hay revisión limitada o incertidumbre persistente; no exigir una identificación falsa.
- **K1 deja una:** reducción de conjunto estructural compatible, no necesariamente identificación del generador verdadero.
- **K2 no mejora:** una buena revisión en K1 no transfiere predictivamente. Conservar resultado negativo.

## Éxito científico: condiciones acumulativas propuestas, no aprobadas

1. **Calibración justa:** C00 y C01 superaron en K0 una compuerta de adecuación absoluta con información idéntica; se conservaron todas las configuraciones compatibles. Deben declararse sus diferencias en dimensión del espacio y presupuestos.
2. **Discriminación de evidencia pertinente:** medida K1 seleccionada antes de su respuesta, con separación robusta de los conjuntos K0; la revisión observada concuerda con reglas congeladas. Reducir rivales injustificadamente es error, no éxito.
3. **Revisión predictiva:** en K2, la predicción K1 debe superar a la predicción K0 anterior sobre **los mismos seis puntos**, respetando las abstenciones; comparar también con REF-CAF y REF-SCALE. El conjunto de K1 no gana por abarcar todo mediante una envolvente enorme; reportar anchura y cobertura juntas.
4. **Clasificación correcta:** cambiar conexiones/estados es revisión estructural; seleccionar entre grafos ya existentes es revisión de hipótesis estructurales, no creación de arquitectura; cambiar capacidad/τ es parametrización. Separar identificación estructural de pronóstico preciso.
5. **Validez acotada:** una sola realización sintética no prueba utilidad real, ni inferencia estadística general. Publicar los falsos descartes, abstenciones, criterios incumplidos y cualquier desviación de custodia.

El éxito no requiere conocer de antemano qué estructura es la verdad; una posterior adjudicación de verdad requerirá separación real de la fuente evaluadora y mecanismos observacionalmente distinguibles.

## Frontera de implementación y trabajo pendiente

Se implementa únicamente una **sonda sintética**, sin K2 observado: caf02_structural_k0k1k2.py verifica repertorio E1, simula C00/C01 con balances, calibra K0, selecciona evidencia K1 entre opciones públicas, revisa tras K1 fabricada y produce un paquete K2 **sin verdad**. Sus tests usan casos inventados, nunca el DES de CAF-01.

Próximas compuertas antes de ciencia prospectiva: fijar espacio paramétrico como supuesto sintético y compuerta absoluta, declarar menú y decisión K1, confirmar paridad nativa y presupuesto K0/K1/K2 por motor, preparar **otro** mundo con sello y custodia externa **antes de construir K0**, producir K0/K1 independientes, congelar K2 (incluyendo referencias) con sello externo y **después** una sola evaluación autorizada.

**El requisito de justificación operacional externa de cada parámetro se retira como bloqueo para la prueba sintética.** Permanece pendiente solo si se desea afirmar plausibilidad en una cafetería real.

**No se cambió E1, no se reabrió CAF-01 y no se ejecutó un nuevo mundo experimental.**
