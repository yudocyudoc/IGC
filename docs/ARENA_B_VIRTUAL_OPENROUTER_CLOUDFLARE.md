# B — OpenRouter virtual sobre Cloudflare Workers AI

**Fecha:** 2026-10-25 (CDMX) · **Rama:** `feature/arena-b-native-node-engine-v01` · **PR:** [#25](https://github.com/yudocyudoc/IGC/pull/25). `main` sin modificar.

## Decisión y razón

Se **simula OpenRouter**, pero el proveedor que genera el contenido es **Cloudflare Workers AI**, con `@cf/zai-org/glm-5.3-flash`. No se busca pagar OpenRouter, instalar un servidor MCP o reescribir el `LLMWrapper` de la Universidad de Buffalo.

```
UB-IAD/sd-ai commit 5199f7b
  quantitative/engine.js -> QuantitativeEngineBrain -> LLMWrapper
  -> @openrouter/sdk [virtual model: cloudflare/glm-5.3-flash]
  -> IGC fetch interceptor [one request, zero retries]
  -> Cloudflare Workers AI REST /ai/run/@cf/zai-org/glm-5.3-flash
  <- unmodified model-generated JSON/content
  <- OpenRouter-compliant response ENVELOPE (bridge provenance explicit)
  -> original Buffalo response schema handling and processResponse
```

Se eligió el alias deliberadamente ficticio `cloudflare/glm-5.3-flash` porque Buffalo enruta cualquier slug `proveedor/modelo` por su SDK de OpenRouter. Así no se presenta falsamente el modelo alojado en Cloudflare como un modelo contratado a OpenRouter. No hay tráfico hacia la API de OpenRouter.

## Adaptador y garantías

`scripts/arena_b_cf_protocol_adapter.mjs` convierte exclusivamente el **contrato de transporte**:

- Reenvía sin alterar las cadenas de los mensajes system/user creados por Buffalo.
- Mantiene el **JSON Schema original** con `variables` y `relationships`, pero transforma su envoltura `response_format.json_schema:{name,schema,strict}` de la SDK al esquema **desnudo** `response_format:{type:'json_schema',json_schema:schema}` del REST de Workers AI.
- Rutea a modelo real `@cf/zai-org/glm-5.3-flash` y registra ajustes de **transporte/uso** (`reasoning_effort:'low'`, `max_completion_tokens<=3500`); no son cambios a la metodología SD-AI. Limita a una única llamada real, sin reintentos de aplicación; si la solicitud falla no sustituye una hipótesis.
- A partir de `{success:true,result:{response:...}}` devuelve el **sobre OpenRouter requerido por la SDK** (`id,created,model,choices,system_fingerprint`), con metadatos explícitamente construidos por el puente. El **contenido del modelo no se corrige ni reestructura**. Si Cloudflare devuelve un objeto de JSON Mode, solo se serializa literalmente para que Buffalo lo procese. El recibo y la respuesta cruda permiten detectar metadatos inferidos por el puente.
- Cualquier rechazo estructural posterior sigue siendo resultado de Buffalo; no se rellenan automáticamente `stocks`, `flows`, unidades ni ecuaciones.
- Solo entran evidencias visibles de B, sin D/M, sin `gold` ni salida del mundo generador.

`scripts/arena_b_openrouter_cloudflare.mjs` intercepta el `fetch` HTTP utilizado por la SDK original, valida host y esquema, envía a Cloudflare mediante el fetch sin interceptor y, en modo `offline`, devuelve un resultado **sintético** del proveedor para probar el recorrido sin token ni coste.

## Resultado de pruebas y controles

- `tests/test_arena_b_cf_protocol_adapter.mjs`: prueba que los prompts y el esquema se preservan, que la información numérica del proveedor no se fabrica y que el contenido inadecuado se mantiene inadecuado.
- `.github/workflows/arena-b-native-node.yml`: ejecuta código original Buffalo fijado en SHA, tests y modo offline; el modo `live` requiere la incorporación **nueva en el último commit** de un marcador de autorización de una sola llamada.
- Validación del SDK original OpenRouter (previamente probada en la misma rama): respuesta simulada debe satisfacer `system_fingerprint` y los campos de su SDK; si devuelve texto no JSON el motor rechaza la hipótesis. No se generan hipótesis a partir de una fixture cuando la llamada real falla.

**Ejecución offline:** [CI #40255907686](https://github.com/yudocyudoc/IGC/actions/runs/40255907686) — verificación del adaptador y de ruta Buffalo→OpenRouter virtual→Cloudflare sintético: **PASS**.

**Ejecución real:** [CI #40255975864](https://github.com/yudocyudoc/IGC/actions/runs/40255975864) — **SUCCESS** con llamada real a Cloudflare: exactamente una petición, HTTP 200, `success=true`, respuesta cruda preservada, `REAL_CLOUDFLARE_NATIVE_BUFFALO_MODEL_RETURNED`, salida del motor Buffalo de **15 variables (2 stocks, 2 flujos y 11 auxiliares), 18 relaciones**. Uso reportado por Cloudflare: **1 392 tokens entrada, 2 412 salida, 3 804 total**. El motor usó el alias virtual `cloudflare/glm-5.3-flash`, pero quien generó fue `@cf/zai-org/glm-5.3-flash`, **sin tráfico a OpenRouter**. Duración visible entre arranque y resultado ≈ 75 segundos. [Evidencia real completa, ZIP](https://github.com/yudocyudoc/IGC/actions/runs/40255975864/artifacts/12622810831).

**Primer análisis de admitibilidad semántica:** el SFD llegó al procesador Buffalo y declaró entradas/salidas correctas a nivel de nombres, pero contiene fórmulas no ejecutables tal como están, como `PULSE profile over time` y `pending_work // processing_signal`. La relación dimensional entre `processing_signal` (declarada en `items`) y `completions` (`items/hour`) también requiere comprobación. **G0/transporte: PASS. Motor NodeJS y salida estructurada: PASS. G1 semántico y dimensional: NO ACREDITADO. G2 OpenModelica: NO EJECUTADO. G3 identificación: NO DEMOSTRADA.** No corregir la hipótesis mediante técnicas de D o M ni presentar el recibo del proveedor como validación causal.

## Límites científicos y de implementación

La prueba offline únicamente valida transporte + lógica original. La variante real es una generación de GLM-5.3-Flash bajo el procedimiento Buffalo, **no** la ejecución de un proveedor admitido nativamente por Buffalo ni del OpenRouter real. Diferencias de características del modelo (schema, truncamiento, latencia) deben registrarse. El éxito de `json_schema` **no es** sinónimo de simulación OpenModelica o identificación causal. No se fusionan los brazos.

Documentación Cloudflare: https://developers.cloudflare.com/workers-ai/features/json-mode/ y https://developers.cloudflare.com/workers-ai/models/glm-5.3-flash/
