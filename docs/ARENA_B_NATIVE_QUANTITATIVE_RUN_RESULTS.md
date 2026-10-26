# IGC Arena — B original NodeJS quantitative: primera ejecución directa

**Corte:** 2026-10-25 (CDMX) · **Repositorio IGC:** PR #25, rama `feature/arena-b-native-node-engine-v01`, `main` intacta.

## Proveniencia
- Upstream real: `UB-IAD/sd-ai`, SHA `5199f7b45f3a7ae4a773cb0dd8542940aabe9edc`, MIT.
- En GitHub Actions se descargó `git fetch ... SHA` y se confirmó `git rev-parse HEAD`. Dependencias instaladas mediante `npm ci` con lockfile original y sin postinstall.
- Se ejecutó el **código NodeJS original** `engines/quantitative/engine.js` → `QuantitativeEngineBrain` → `LLMWrapper` → `processResponse`, **sin editar upstream**. IGC solamente proporcionó entrada visible, capturador de evidencias y proxy de transporte a Cloudflare (alias `glm-5.3-flash`→`@cf/zai-org/glm-5.3-flash`).
- **No es una ejecución directa con proveedor nativo Buffalo (Gemini/OpenRouter).** Tampoco es el `prompt-port` de PR #24 ni un experimento de D.

## Prueba 1: engine + wrapper originales, offline (PASS)

GitHub Actions [#40253959879](https://github.com/yudocyudoc/IGC/actions/runs/40253959879), artefacto [#12621796789](https://github.com/yudocyudoc/IGC/actions/runs/40253959879/artifacts/12621796789).

- El motor invocó una petición OpenAI-compatible hacia un stub local; éste verificó que `response_format.type=json_schema` incluyera variables y relaciones. Petición SHA256 `4eb8ec1abe89875fc2e90173b58b772555aeeea5bd399e294c19b294b62f433d`.
- El stub devolvió un JSON sintético válido. El **procesamiento de Buffalo** devolvió 4 variables/3 relaciones y añadió `Arrivals` como entrada del stock `Backlog` a partir de la relación `Arrivals → Backlog`. Esto prueba una capacidad real del código nativo y su normalización, NO generación de hipótesis por un LLM.
- Una petición al stub, **cero peticiones externas**, no hay prueba de identificabilidad o adecuación.
- Estado: `ORIGINAL_ENGINE_OFFLINE_PATH_PASS`.

## Prueba 2: engine original + proveedor real Cloudflare (TIMEOUT, sin modelo)

- Misma versión del motor, mismo hash de petición estructurada y mismo problema visible; transporte local remapeó el nombre del modelo hacia Cloudflare Workers AI.
- **Se inició exactamente una petición HTTPS saliente**, sin reintentar desde el puente.
- El límite de 135 segundos del puente expiró: `The operation was aborted due to timeout`. El puente devolvió error local HTTP 400 `BRIDGE_FAILURE` al SDK, no un código HTTP 400 devuelto por Cloudflare. El resultado de Buffalo es `Error: 400 BRIDGE_FAILURE`.
- **No hubo respuesta utilizable de Cloudflare, tokens reportados, `sd-json` nativo ni modelo ejecutable**; tampoco hubo CSV de OpenModelica. No afirmar éxito G1/G2/G3. El costo real o actividad tardía del proveedor no puede inferirse de este recibo.
- Recibo explícito: `mode=live`, `provider_calls=1`, `proxy_requests=1`, `quant_schema_seen=true`, `model_returned=false`, `raw_provider_saved=false`.
- El paso live de CI terminó con fallo, por diseño; el artefacto de evidencia sí fue conservado. No lanzar reintentos automáticos.

## Diagnóstico y decisión

El ensayo demuestra que el **motor original cuantitativo de Buffalo y su proceso de estructuración/posprocesamiento son ejecutables** en nuestra infraestructura. El intento con Cloudflare no determina si la respuesta estructurada sería válida: expiró sin respuesta. **No atribuir el resultado al algoritmo de Buffalo**, ni declarar que Cloudflare rechazó el esquema.

**Siguiente prueba recomendada:** ejecutar el mismo SHA original con un proveedor admitido por `LLMWrapper` sin proxy de compatibilidad (Gemini u OpenRouter), usando credenciales legítimas y registrando salida nativa intacta, sin mezclar D/M. Solo después evaluar el `sd-json` resultante y su traducción a OpenModelica. No modificar el motor ni optimizar prompts para arreglar este timeout.

[PR #25](https://github.com/yudocyudoc/IGC/pull/25) · [CI y artifact](https://github.com/yudocyudoc/IGC/actions/runs/40253959879).
