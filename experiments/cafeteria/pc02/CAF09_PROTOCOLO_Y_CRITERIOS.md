# CAF-09 — Ablación de la política de segunda medición y separabilidad del menú

**Fecha y estado:** 2026-10-31. Exploratorio y retrospectivo; los 11 mundos de CAF-07B son conocidos. No es preregistro ciego, ni demuestra validez externa. **Base:** main después de #118. Independiente de los PR Draft #119 y #120. No modificar el código de CAF-07B.

## Pregunta exacta

¿Cuánta abstención procede del requisito *normativo* de aislar robustamente **al menos una hipótesis por cada clase sobreviviente** y cuánta procede de que el menú de segundas mediciones no logra separar ciertas hipótesis?

**Advertencia:** separabilidad de pares bajo el modelo no equivale a tener un diagnóstico completo; incluso cuando una medición elimina hipótesis, todas las clases pueden seguir siendo compatibles.

## Diseño congelado antes de la ejecución CI (no antes de conocer mundos)

Comparar **tres reglas de elegir la segunda medición** con los bancos de 12 y 24 hipótesis, conservando:
- Los mismos 11 mundos físicos DES de `caf07b_umbral_secuencial.scenarios()`.
- Las predicciones **DES originales**, idénticas en los tres brazos y con hipótesis y capacidades ya establecidas en CAF-07B.
- Las lecturas K0 (1.2 pedidos/min, minuto 10), K1 fija (1.5/min, minuto 20), el mismo menú, los mismos costos ordinales, presupuesto acumulado 8 y compatibilidad **±1 pedido**.
- Las mismas funciones de filtrado y actualización posterior a mediciones (`eligible`, `update`) y ningún acceso del selector a la configuración de los mundos de evaluación.
- A lo sumo **una** medición condicional posterior a K1. No transformar el problema en optimización multi-etapa.

**Políticas comparadas**:

1. `STRICT_ORIGINAL`: llamada directa a `b.evaluate_case()` y `b.choose_second()`; si todas las clases no reciben al menos una hipótesis robustamente garantizada bajo una acción, no mide.
2. `ANY_GUARANTEED`: requiere al menos **una hipótesis** con separación robusta contra *todas* las hipótesis de otras clases por algún canal de una misma acción; elige mayor número de hipótesis garantizadas, luego número de pares de clases separables, luego menor costo y luego identificador.
3. `PAIRWISE_ANY`: requiere al menos **un par de hipótesis de clases distintas** con predicciones que difieren **>2 pedidos** en un canal de la acción; elige mayor número de esos pares, luego menor costo y luego identificador. Esta regla es intencionalmente más débil que garantía completa de una hipótesis y puede medir sin resolver ninguna clase.

Para las tres políticas, si no sobreviven hipótesis o queda una sola clase, no se ejecuta una segunda observación. Las alternativas solo cambian la **decisión de medir**, no la tolerancia ±1 ni el criterio de diagnóstico final. Se asigna `MODEL_GAP` si no queda ninguna hipótesis compatible. Si queda una clase y se decide, el resultado sigue siendo **condicional al banco finito**.

**Prioridades por desempate predeclaradas**, sin mirar los mundos: discriminación robusta máxima, luego menor costo, luego ID lexicográfico. No ajustar al resultado.

## Resultados que deberán guardarse

22 pares mundo×banco, **66 evaluaciones** (tres políticas × dos bancos × 11 mundos). Por mundo y brazo:
- Estado previo a K2 y número de clases/hipótesis compatibles; candidatos de acción y scores premedición.
- Acción elegida **antes** de leer el DES de K2; costo y canales.
- Reducción real de hipótesis y clases después de K2, y veredicto del evaluador separado del selector.
- Correctos, **falsos cuellos únicos**, clase errónea, abstenciones, brechas, cantidad de segundas mediciones, decisiones que cambiaron contra la política estricta.
- **Separabilidad del menú entre clases** a K1: cuenta de pares separables; cuenta de hipótesis aislables; casos sin pares separables vs casos con pares pero sin garantías completas.

**No inferir** que cero pares separables en este catálogo significa equivalencia física global; el repertorio de acciones y observaciones es limitado.

## Gates y límites

- Pruebas de que STRICT_ORIGINAL reproduce el resultado de CAF-07B y el selector no recibe las verdades del mundo; pruebas negativas para que `ANY_GUARANTEED` y `PAIRWISE_ANY` seleccionen acciones distintas en un banco artificial pequeño construido para distinguir las reglas, **sin introducirlo al conjunto de evaluación**.
- Auditoría sobre lectura, costo, escrituras de decisiones antes del DES, integridad de SHA, consistencia y conteos.
- Comparación **no ciega**, sin variación de servicio, sin costos reales ni medición de ruido; ninguna promoción diagnóstica. Nuevos experimentos de perturbación o tiempos estocásticos se estudiarán **después** de adjudicar esta ablación.
