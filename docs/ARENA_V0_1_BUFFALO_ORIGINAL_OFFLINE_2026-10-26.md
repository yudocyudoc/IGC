# Arena V0.1 · Promoción Buffalo: conexión fiel con SD-AI cuantitativo original

**Fecha:** 2026-10-26. **Origen:** PR #25 `feature/arena-b-native-node-engine-v01`, fuente HEAD `1588d210e7741755cd9152941fa9611dcaed3452`.
**Motor original externo:** `UB-IAD/sd-ai` commit `5199f7b45f3a7ae4a773cb0dd8542940aabe9edc`, licencia **MIT**; motor original sin modificar.

## Alcance de este corte B

Se trasladan exactamente `scripts/arena_b_native_runner.mjs`, `scripts/arena_b_openrouter_mock.mjs`, `scripts/arena_b_cf_protocol_adapter.mjs`, `scripts/arena_b_openrouter_cloudflare.mjs`, `tests/test_arena_b_cf_protocol_adapter.mjs` y el mismo input visible sintético empleado en la campaña Buffalo original.

El flujo es: entrada pública → `Engine.generate` cuantitativo original, `LLMWrapper` → esquema cuantitativo Buffalo → posprocesamiento del propio SD-AI → JSON nativo. Los puentes solo representan el API de OpenRouter mediante un transporte local y, cuando se autorice, Cloudflare; **no sustituyen el motor cuantitativo**.

CI ejecuta **solo pruebas sin secretos**: respuesta local válida e inválida, esquema estructurado, rechazo de JSON corrupto, ruta de SDK OpenRouter y adaptación sintética a Cloudflare. Todos los resultados deben declarar `live_provider_calls=0`. No se copian los antiguos archivos de marcadores que autorizaban llamadas facturables ni se ejecuta Cloudflare al abrir este PR.

## Límite científico

Esta importación comprueba **que el motor nativo sigue ejecutando y respeta el esquema bajo datos sintéticos**. No es inferencia viva, no demuestra que los mecanismos propuestos sean adecuados a la cafetería, no traduce todavía a OpenModelica ni ejecuta G2. Las inferencias Buffalo B2/B3/B4/B5, las revisiones con o sin pistas y el puente G0→G3 permanecen en PRs #26/#30/#33/#34/#36/#40 y se promoverán selectivamente con otro gate. El primer brazo Buffalo integrado debe poder responder `PARTIAL`/bloqueo si un modelo no es formalizable.

## Licencia y origen

`UB-IAD/sd-ai` declara licencia MIT con copyright University at Buffalo – Institute for Artificial Intelligence and Data Science (2026). La CI comprueba `LICENSE` del commit exacto. IGC no copia ese proyecto en su árbol de fuentes: lo descarga de manera reproducible durante CI. Si un paquete distribuido incluyera código de Buffalo, debe conservar el aviso y la licencia MIT correspondiente. El adaptador IGC conserva autoría y su procedencia.

## Próximos gates

- Fidelidad G0 Buffalo→Modelica, detección de subtipos/funciones no traducibles y reparación prohibida; fuente principal PR #30.
- G1/G2 reales sobre la **salida nativa** original, no sustitutos de un mundo evaluador, y G3 de construcción con errores y límites explícitos.
- Feedback por brazo con modelo nativo propio, como B4→B5; conservar los fallos históricos como datos de laboratorio.
- Registro ATMS de las propuestas, revisiones y contradicciones, sin acceso del brazo B a decisiones D/M.

**Estado release:** este incremento no basta para `v0.1.0`. Clef permanece inactivo. `main` solo recibirá fuentes si las pruebas offline B y F0 pasan.
