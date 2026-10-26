# Arena B3 — Buffalo recibe los residuos físicos de su propio modelo

**Fecha:** 2026-10-26. **PR:** #33, rama `feature/arena-b-physical-feedback-v01` (base del PR #30). **Método generador:** motor NodeJS original `UB-IAD/sd-ai@5199f7b45f3a7ae4a773cb0dd8542940aabe9edc`, sin modificar el código universitario.

## La nueva pregunta experimental

Ya sabíamos que Buffalo puede generar un modelo (B1), recibir un diagnóstico G1 y corregir sus ecuaciones (B2), y que un adaptador estricto lo traduce y simula en OpenModelica. **Eso no demostraba que Buffalo supiera revisar su dinámica al recibir desacuerdos físicos con los datos.**

B3 prueba la siguiente ruta: `native-output.json B2 → OpenModelica real Euler → diagnóstico físico y residuos de construcción → original Buffalo Engine.generate(currentModel) → revisión nativa nueva → traducción Modelica fail-closed → OpenModelica real → comparación de construcción`.

## Fuentes protegidas

Únicas fuentes admitidas:
- Salida B2 real del motor Buffalo+Cloudflare, [Actions #40259178852](https://github.com/yudocyudoc/IGC/actions/runs/40259178852), `revision-live/native-output.json` bytes SHA256 `d7630830b4812c8880dc88c5f93f821707a75d22e0ecdf2cc1e9b5d8ec0889b9`.
- CSV **real** OpenModelica B2 y su informe de diagnóstico, [Actions #40283017108](https://github.com/yudocyudocyudoc/IGC/actions/runs/40283017108) (la ruta correcta es `yudocyudoc/IGC`), CSV bytes SHA256 `9de161b6d55bd24f4e4d839d3665abede8dbb39b7174b8a35b0a75bfd7eded05`, informe bytes SHA256 `ba3c66d2a7b662e8a008262b459a7e920aa4c92b9630907a6e231c101b2d34a6`.
- Entrada visible B inicial `data/synthetic/arena_b_native_visible.json`, observaciones de construcción `(0,0),(1,.35),(2,1.1),(4,2.5)`, pulso público `1.7 items/h` durante dos horas.

**Los tres archivos fuente deben coincidir byte por byte**. El informe G3 archivado contiene un sufijo histórico literal `\\n` fuera del documento JSON; se acepta solo ese sufijo exacto y solo después de comprobar el SHA. No se reescribe ni se acepta un informe arbitrario.

## Feedback realmente entregado

`scripts/arena_b_physical_feedback.py` calcula de nuevo sobre el CSV y compara el informe B2; produce `igc-b-own-physical-construction-feedback/0.1` con:
- Residuales `simulado−observado`: t0 `0`, t1 `+0.0376059`, t2 `−0.1123941`, t4 `−0.3123941` elementos.
- Stocks `pending_work`, `delivered_work`; flujos `arrivals`, `completions`; `completion_capacity` y `capacity_utilization` en esos cuatro tiempos, extraídos del CSV **real**.
- Conservación Euler global: desbalance máximo `1.33e−15 items`; G2 PASS y G3 **descriptivo**, sin cota instrumental declarada, sin reserva.
- Una identidad algebraica **del propio modelo**: `completion_capacity = nominal_capacity × capacity_utilization` y `completions = completion_capacity × capacity_utilization` implican que la utilización figura al cuadrado. Es una observación a examinar, **no una instrucción de repararla** ni prueba de error causal.
- Las interpolaciones de lookup `PIECEWISE_LINEAR_CLAMPED_ENDPOINTS` siguen siendo **supuestos del adaptador**; la paridad con la simulación nativa de Buffalo no está verificada.

**NO se entrega:** salida de D, M, estructura del evaluador, verdad del generador, parámetros de otro brazo, respuestas ocultas ni datos reservados. La observación y su error son de construcción, no una nueva validación.

## Restricción presupuestaria explícita

La entrada original Buffalo tenía `max_llm_calls=1` y `iteration_limit=2`. B1/B2 ya consumieron ese experimento; **B3 no puede fingir ser un paso dentro del presupuesto original**. Se crea una **extensión diagnóstica independiente y explícita**: B2 se considera origen histórico, no se recalcula; se autoriza **a lo sumo una llamada nueva Cloudflare, sin reintentos**, únicamente mediante el marcador exclusivo `data/diagnostics/BUFFALO_B_PHYSICAL_FEEDBACK_ONE_CALL.json` añadido en un commit de tipo `push` en la rama exacta, primer intento GitHub Actions. Un fallo de proveedor se registra como fallo, no se suple con salida sintética.

## Límites y gates

1. CI offline ejecuta la ruta verdadera `Engine.generate → QuantitativeEngineBrain → LLMWrapper → OpenRouter virtual → mock Cloudflare`, verificando `currentModel` previo exacto y que el diagnóstico físico llegue en la última petición. En esa ruta **la respuesta es simulada y no prueba mejora de B**.
2. Si se autoriza una llamada real y retorna un modelo Buffalo, se conserva la respuesta sin repararla.
3. `scripts/arena_b_physical_outcome.py` intenta G0 de modo **fail-closed**. Subtipos `conveyor` no implementados, módulos o dinámica distinta de los contratos se registran como bloqueo; no se transforman silenciosamente.
4. Si G0 admite el documento, se compila/simula con OpenModelica 1.27.1 Euler, 0–8h y 64 intervalos y se reconstruyen conservación y RMSE con n=4/n=3. Un G2 fallido es un dato experimental útil.
5. Si B3 modifica el modelo, el cambio puede ser paramétrico o estructural; **un mejor RMSE sobre los mismos datos usados para revisar es una mejora in-sample**, no evidencia nueva, verdad causal, ventaja sobre D/M ni identificación.
6. G3 corresponde a adecuación de construcción; el holdout/reserva genuino es otro experimento **NOT_RUN**.

**Decisión:** no arreglar ni optimizar B3 desde el adaptador. Registrar lo que devuelve Buffalo, incluso si es inejecutable o empeora.
