# IGC — Prueba factorial SD v2 vs v2.1, con y sin ecuaciones (2026-10-25)

**Veredicto:** `PARTIAL_STOP_AT_CALL_5`; 8 llamadas planificadas, **5 efectuadas, 4 JSON válidos, 1 terminación `length`, 3 sin ejecutar, 0 reintentos**. No demuestra que v2.1 mejore la selección estructural; sí registra mayor economía de tokens en las dos comparaciones por pares disponibles.

## Procedencia y preinscripción

- Prompt v2: [`data/prompts/arena_sd_system_v2.txt`](../data/prompts/arena_sd_system_v2.txt).
- Prompt v2.1: [`data/prompts/arena_sd_system_v21.txt`](../data/prompts/arena_sd_system_v21.txt).
- [Manifiesto factorial congelado](../data/diagnostics/arena_sd_system_v21_factorial_manifest.json), con condiciones, órdenes, métricas de auditoría, construcciones nuevas WC/WD y contratos mecanísticos explícitos (`dq/dt`, flujos, parámetros admisibles, dimensiones).
- Compromiso del material generador no enviado al proveedor: `sha256:5be58a4af0521da7b0f975ddb2908a9675d11734fadb7c3a3da542cf1f6fc89a`. Los dos mundos fueron generados por el equipo investigador: **no existe custodia externa ni independencia ciega demostrada**.
- [GitHub Actions run 40180937268](https://github.com/yudocyudoc/IGC/actions/runs/40180937268), job `sd-system-v21-factorial`; [artefacto JSON de los resultados originales 12594302320](https://github.com/yudocyudoc/IGC/actions/runs/40180937268/artifacts/12594302320).
- Autorización única: commit `75b3a7d1d3516cd22b42123bf5f6db586040bba2`; se verificó el archivo ADDED en ese commit antes de inferir. Cinco tests offline aprobados y solicitudes construidas con hash antes de la llamada.
- Todas las solicitudes: `@cf/zai-org/glm-5.3-flash`, `temperature=0`, `reasoning_effort=low`, `max_completion_tokens=4096`. Mismo user entre variantes de system con igual caso y tratamiento de ecuaciones. Ningún valor de reserva fue enviado.

## Ejecución real en orden congelado

| Orden | Caso | System | Contratos de ecuaciones | HTTP / finish | Selección | Tokens entrada | Tokens salida | Total |
|---:|---|---|---|---|---|---:|---:|---:|
| 1 | WC | v2.1 | No | 200 / stop | CS-01 y CS-02 | 795 | 671 | 1466 |
| 2 | WD | v2 | Sí | 200 / stop | CS-01 y CS-02 | 1528 | 2709 | 4237 |
| 3 | WC | v2 | No | 200 / stop | CS-01 y CS-02 | 1110 | 1529 | 2639 |
| 4 | WD | v2.1 | Sí | 200 / stop | CS-01 y CS-02 | 1213 | 2044 | 3257 |
| 5 | WC | v2 | Sí | 200 / length | JSON no adjudicable | 1508 | 4096 | 5604 |
| 6–8 | Otros tratamientos | — | — | **NO EJECUTADOS** | — | — | — | — |

Total gastado en la ejecución incompleta: **17,203 tokens**, incluyendo la respuesta truncada. El archivo registra la quinta solicitud como `INVALID_OR_TRANSPORT_NO_RETRY` por `NON_STOP_FINISH`: se recibió HTTP 200, pero se agotaron los 4,096 tokens de salida. Esto **no** es una abstención científica del modelo ni un error de credenciales. No repetir call 5 dentro de la misma prueba.

### Comparaciones por pares disponibles (misma construcción y mismo contrato)

- **WC sin ecuaciones:** v2.1 = 1466 tokens vs v2 = 2639 (reducción del 44.4 %); ambos JSON válidos, ambos conservaron ambos IDs.
- **WD con ecuaciones:** v2.1 = 3257 tokens vs v2 = 4237 (reducción del 23.1 %); ambos JSON válidos, ambos conservaron ambos IDs.
- No existe pareja completa para WC con ecuaciones ni WD sin ecuaciones. **No atribuir interacción causal entre factores, superioridad general ni tasa de éxito a partir de celdas ausentes**.

## Auditoría física concreta de las respuestas (a posteriori)

1. Ambos sistemas con contratos, en **WD**, calcularon correctamente la masa del pulso `1.45 × 1.8 = 2.61 unidades` y distinguieron el output acumulado de una tasa. Ambos retuvieron las estructuras por incertidumbre no cuantificada. La secuencia observada `0.04968 → 0.010033` entre 0.25 y 0.5 h es no monótona; ambos la trataron como indicio de **ruido de medición** y no como flujo físico negativo.
2. **WC v2 sin contratos:** afirma que CS-01 tiene salida acumulada `concave throughout with nonzero initial slope`, y que la curva acumulada arranca lineal. **Error:** stocks inicialmente vacíos implican `delivered'(0+)=0` en CS-01; para pulso rectangular la curva acumulada inicia `~ t²`, convexa. En CS-02 inicia `~ t³`, no lineal.
3. **WC v2.1 sin contratos:** evita declarar un intervalo de tiempo muerto exacto y verifica la masa total `1.1×1.75=1.925`, pero presenta de forma ambigua o incorrecta la forma temprana de CS-02 (`quadratic-then-linear early growth`). **v2.1 sin ecuaciones tampoco garantiza razonamiento dinámico correcto.**
4. **WD v2.1 con contratos:** explica correctamente el contraste de orden temprano (CS-01 `~t²` frente a CS-02 `~t³`). Pero su afirmación `delivered(1 h) ≥ ~0.4 units` bajo todas las `responseTime ≤ 1.6` es demasiado fuerte. Con amplitud 1.45 y sin saturación, el mínimo exacto de CS-01 en `tau=1.6` es **`1.45[1 - 1.6(1-e^(-1/1.6))] ≈ 0.37181` unidades**. Dar la fórmula o rangos correctos al modelo no hace infalibles sus desigualdades.
5. **WD v2 con contratos:** usa una cota aproximada `u t²/(2τ) ≈ 0.453` como si fuera cota inferior exacta a t=1 h. La aproximación de orden bajo **sobreestima** el valor exacto 0.37181 para los parámetros límite. Su falsación propuesta no está matemáticamente justificada en esa cifra.
6. Los dos mundos tienen construcción visible compatible con más de una hipótesis según el nivel desconocido de ruido; que el modelo conserve ambos no constituye error ni beneficio probado. Tampoco hay validación sobre nueva perturbación retenida, G3 ni ventaja sobre D.

**Chequeo exploratorio posterior, NO preinscrito:** ajuste simple de la construcción mediante rejilla de `maxThroughput ∈ [1.2,2.4]` (paso 0.2) y `responseTime ∈ [0.4,1.6]` (paso 0.1), integración RK4 local de cola saturable, da RMSE WC `CS-01=0.0134, CS-02=0.0634` y WD `CS-01=0.1109, CS-02=0.0342`. Este ajuste no se suministró a GLM, no evalúa holdout y no constituye puntuación formal de S/D.

## Decisión

- **No declarar ganador**: no hay evidencia suficiente para que v2.1 supere v2 científicamente, pero v2.1 consumió menos tokens en las dos parejas observables.
- El contrato explícito de stocks, flujos, ecuaciones, parámetros y unidades parece orientar mejor algunas explicaciones, pero **no impidió errores matemáticos**: fórmulas de aproximación no son cotas de falsación.
- **Experimento detenido correctamente** después de una salida truncada; preservar los tres tratamientos no ejecutados sin rellenar respuestas, sin reintentos ni selección retrospectiva de la mejor.
- En un siguiente diseño distinto, considerar salida más austera, verificador determinista de cotas físicas y medición de idoneidad por predicción sellada, no solo verbosidad. Cualquier nueva prueba requiere su propio plan y autorización; no reabrir esta prueba como si fuera un único factorial completo.

**Límites:** estudio de razonamiento sobre dos mundos sintéticos construidos por el equipo. No sustituyó la comparación D, no ejecutó OpenModelica en esta investigación, no preparó PredictionLock, **no abrió reserva** y no estableció inferencia causal independiente.
