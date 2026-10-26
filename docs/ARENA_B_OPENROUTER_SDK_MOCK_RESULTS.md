# Arena Buffalo — simulación del transporte OpenRouter con motor NodeJS original

**Fecha:** 2026-10-25 CDMX (registro CI en UTC del 26)  
**PR:** [IGC #25](https://github.com/yudocyudoc/IGC/pull/25), rama `feature/arena-b-native-node-engine-v01`. `main` intacta.  
**Upstream original:** `UB-IAD/sd-ai`, commit `5199f7b45f3a7ae4a773cb0dd8542940aabe9edc`, licencia MIT.  

## Decisión

Se pregunta si puede **simularse una conexión OpenRouter** para probar el motor oficial de Buffalo sin tener que pagar una inferencia ni instalar un servidor MCP.

**Sí.** `scripts/arena_b_openrouter_mock.mjs` no reemplaza el motor ni sus clases: importa directamente `engines/quantitative/engine.js`, el cual invoca `QuantitativeEngineBrain` y `LLMWrapper` originales, incluido `@openrouter/sdk`. Solo intercepta `globalThis.fetch` en el borde HTTP de la SDK, con política **deny-by-default** para otros destinos y exactamente una solicitud admitida al endpoint `openrouter.ai/.../chat/completions`. No cambia sus prompts, schema, normalización de stocks y flujos ni ecuaciones.

Usa el slug nativo `z-ai/glm-5.3` que Buffalo reconoce como proveedor OpenRouter, no el alias Cloudflare del ensayo anterior. El test instala el SDK original desde el `package-lock.json` de la universidad, sin parchear ni editar upstream.

## Resultados ejecutados

[GitHub Actions #40255203314](https://github.com/yudocyudoc/IGC/actions/runs/40255203314): **SUCCESS**.

| Ensayo | Resultado observable | Límite |
|---|---|---|
| Ruta cuantitativa nativa + respuesta HTTP sintética válida | **PASS**: se interceptó 1 solicitud OpenRouter, con schema cuantitativo `json_schema` (`variables`, `relationships`), y volvió un modelo de 4 variables / 3 relaciones | Respuesta escrita por nosotros, **no generada por IA** |
| Normalización Buffalo | **PASS**: el motor infirió `Arrivals` como inflow del stock `Backlog` a partir de la relación causal y preservó un SFD | No demuestra que otro mecanismo sea correcto |
| Respuesta HTTP con contenido que no es JSON | **PASS como negativo**: el motor devolvió `ResponseFormatError: Bad JSON returned by underlying LLM`, sin modelo nuevo ni reemplazo | No es un diagnóstico de una respuesta real |
| Salida fuera del destino OpenRouter / múltiples peticiones | **Bloqueo codificado** en el interceptor | No se probó autenticación remota real |
| G2 OpenModelica | **NO EJECUTADA** con este output simulado | El siguiente paso es un modelo realmente generado por un LLM |

Recibo positivo: `OFFLINE_OPENROUTER_NATIVE_ENGINE_PASS`, `intercepted_http_calls=1`, `live_provider_calls=0`, `structured_request_seen=true`, `original_upstream_modified=false`, `buffalo_inferred_arrivals_as_inflow=true`.

Recibo negativo: `ORIGINAL_ENGINE_RETURNED_NO_MODEL`, `ResponseFormatError`, sin sustituir salida; también exactamente 1 solicitud interceptada y cero llamadas externas.

El primer intento de fixture HTTP falló en `ResponseValidationError` porque el esquema de respuesta validado por la **SDK original de OpenRouter** exigía `system_fingerprint`; se corrigió únicamente la respuesta **simulada**. La prueba definitiva pasó. Se preservan ambos eventos en GitHub Actions.

**Evidencia completa:** [artefacto de la CI #40255203314](https://github.com/yudocyudoc/IGC/actions/runs/40255203314/artifacts/12621943365). Incluye recibos de las pruebas, estructura de salida original, hashes de solicitud y de esquema, y los datos controlados usados para simular respuesta, sin credenciales de proveedor.

## MCP frente a la API directa

OpenRouter dispone de [un servidor MCP remoto](https://mcp.openrouter.ai/mcp) que permite buscar modelos, compararlos y realizar llamadas de prueba mediante `send-message`. Según su propia documentación, el MCP es una **herramienta de desarrollo** que se autentica por OAuth con una clave acotada y **no sustituye la API para aplicaciones**: https://openrouter.ai/blog/announcements/openrouter-mcp-server/

Si la intención fuera exponer **Buffalo como herramienta de IGC** (`generate_quantitative_model`, `explain_model`), un MCP **propio** es factible más adelante, pero no hace falta para probar su camino de inferencia ni garantiza salida estructurada. Un MCP tampoco da inferencias reales sin una identidad/cuenta válida ante el proveedor.

## Próximo ensayo correcto

1. Conservar este `openrouter_mock` como regresión de compatibilidad del SDK original.
2. Ejecutar el mismo Buffalo SHA y `@openrouter/sdk` **sin interceptor**, con un modelo y una clave OpenRouter real en secreto de GitHub, una llamada controlada y archivo completo de respuesta/costo.
3. Recién entonces aplicar validaciones nativas de `sd-json` y adaptación fiel a Modelica, distinguiendo fallo Buffalo/proveedor del límite de nuestro adaptador.
4. Mantener independencia de D y molecular; ATMS registrará después el historial propio B.

**No se realizó una nueva inferencia externa en este experimento.** No se ha probado un resultado real OpenRouter ni identificado una causa verdadera.
