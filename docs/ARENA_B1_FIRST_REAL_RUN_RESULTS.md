# Arena B1 — primer ensayo real del proceso cuantitativo Buffalo (prompt-port) en GLM-5.3-Flash

**Fecha de ejecución:** 2026-10-25 (CDMX) / 2026-10-26 UTC  
**Estado:** primer intento terminado, respuesta real preservada; **modelo NO admitido a G1/G2**.  
**PR independiente:** [#24](https://github.com/yudocyudoc/IGC/pull/24).  
**Fuente primaria:** [GitHub Actions #40251276848](https://github.com/yudocyudoc/IGC/actions/runs/40251276848), [archivo íntegro de la llamada](https://github.com/yudocyudoc/IGC/actions/runs/40251276848/artifacts/12620730952).

## Contrato y procedencia

- Prompt de proceso cuantitativo de `UB-IAD/sd-ai`, commit `5199f7b45f3a7ae4a773cb0dd8542940aabe9edc`, ensamblado en modo profesional escalar. **No es el runtime NodeJS original:** usamos un *prompt-port* y nuestro transporte Cloudflare. Esto impide atribuir directamente la calidad de la respuesta al motor oficial SD-AI.
- Proveedor real: `@cf/zai-org/glm-5.3-flash`; una llamada, **cero reintentos**; HTTP **200**, `success=true`, `finish_reason=stop`, modelo devuelto correctamente.
- Uso reportado: **1412 tokens de entrada + 1761 de salida = 3173**. Tiempo medido: **35 269 ms**. Los campos de uso provienen de la respuesta del proveedor, no de una estimación nuestra.
- Respuesta cruda guardada en `response-raw.json`, solicitud y prompt original en el artefacto; no se consultó información reservada ni estructuras de los otros brazos.
- El primer marcador de autorización no efectuó llamada por problema de checkout de merge commit; el segundo marcador (exact PR head) efectuó **exactamente una llamada**. No repetirla automáticamente.

## Hipótesis conceptual que realmente produjo el modelo

GLM sugirió un mecanismo de **trabajo pendiente / llegadas / tasa de terminación / trabajo completado**, con drenaje proporcional al trabajo pendiente y un tiempo de procesamiento cercano a 2 horas. Sugirió un pulso de llegadas mediante función gráfica temporal, y afirmó que la acumulación, no las pérdidas, explica el retardo. Es **una hipótesis del modelo**, no evidencia de que ese mecanismo sea verdadero ni de que su calibración sea correcta.

La respuesta contiene una explicación en texto, seguida de un bloque delimitado como JSON, después más comentarios. Ese JSON es legible, pero el sobre de salida **no es** el contrato `sd-json` puro esperado por nuestro primer lector.

## Diagnóstico por niveles, sin reparar el modelo

| Verificación | Resultado | Evidencia |
|---|---|---|
| Inferencia remota | **PASS** | HTTP 200, un resultado con modelo correcto, `finish_reason=stop` |
| JSON aislable | **PARCIAL** | Existe un bloque JSON bien formado dentro de texto explicativo |
| Conformidad al `sd-json` de Buffalo | **FAIL** | Introduce campos `name/version/simulation`; usa `unit` en vez de `units`, `graphical_function` en vez de `graphicalFunction`, y puntos de lookup en formato diferente |
| Consistencia stock–flow | **FAIL** | El stock `pending work` no incluye `work arrivals` como inflow; el flujo usa `outflows` como si fuera un stock |
| Referencias ecuacionales | **FAIL** | `pending_work / processing time` y `arrival rate profile(TIME)` no cumplen el nombre de símbolos o la sintaxis de la formulación declarada |
| Adaptación a Modelica | **NOT_RUN** | El parser inicial rechazó la respuesta antes de construir un candidato admitido |
| Simulación física / adecuación | **NOT_RUN** | No hay CSV del modelo generado ni medida de adecuación |
| Validez causal | **NO DEMOSTRADA** | No hay simulación válida ni evidencia independiente |

**El veredicto del workflow B1 es FAIL por `PROVIDER_CONTENT_NOT_JSON`, no un juicio causal.** El diagnóstico adicional de estructura se realizó sobre el bloque JSON aislado del artefacto, sin modificar ni simular su contenido. El estado `PROVIDER_OR_PARSE_FAILURE_NO_RETRY` expresa que la respuesta no atravesó el contrato, no que la API no respondiera.

## Implicación metodológica

Este ensayo demuestra que el *prompt-port* produce una **explicación conceptual**, pero no una salida estructurada utilizable. No equivale a evaluar el motor oficial de Buffalo: su `LLMWrapper` utiliza un esquema de respuesta estructurada y un posprocesamiento que aquí no fueron ejecutados. **El siguiente incremento científico debe conectar ese contrato original o su runtime**, no optimizar el prompt ni rellenar las estructuras con técnicas del determinista o moléculas. Si el motor oficial produce un modelo incompleto, registrarlo como tal.

Los tests del adaptador B0 siguen pasando: [CI B0 #40251276855](https://github.com/yudocyudoc/IGC/actions/runs/40251276855) y [regresión F0 #40251277159](https://github.com/yudocyudoc/IGC/actions/runs/40251277159): **SUCCESS**. El ejemplo B0 escrito a mano simulado en OpenModelica no debe contarse como generación exitosa de Buffalo.

## Relación con la deliberación futura

El resultado ya aporta una **hipótesis sobre el mecanismo del sistema**. Sin embargo, el laboratorio todavía no debe compararla numéricamente con D hasta formalizarla sin alteraciones. La deliberación con varias perspectivas requiere conservar los desacuerdos, registrar con precisión las insuficiencias y evitar que un brazo transforme el resultado del otro.

**Ninguna rama D/B/M fue fusionada; `main` permanece intacta.**
