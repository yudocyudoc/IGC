# IGC — GLM-5.3 authentication and inference diagnostic V4

**Fecha:** 2026-10-25. **Estatus:** `VALID_DIAGNOSTIC_JSON_NOT_ARENA_SUBMISSION`.

## Procedencia

- [IGC Actions run 40177963815](https://github.com/yudocyudoc/IGC/actions/runs/40177963815); job `glm53-one-shot-probe`, cinco pruebas de contrato aprobadas.
- [Artefacto 12593082911](https://github.com/yudocyudoc/IGC/actions/runs/40177963815/artifacts/12593082911), `provider-result.json`. Archivo generado directamente en GitHub Actions, no reconstruido desde texto.
- Marcador en el commit `89c1a8124a877374d9616d7c156d5f2592078ef4` (`data/diagnostics/GLM53_GITHUB_PROBE_TRIGGER_V4.json`), puerta de ejecución por creación del archivo.
- Solicitud: `data/diagnostics/glm53_nw2_config_probe_request.json`, hash `sha256:0426e743b2119bf656d0670cade3aba185f67fd4591c8a7884b0247fda96c29f`.

## Resultado del proveedor

| Campo | Valor |
|---|---|
| Modelo | `@cf/zai-org/glm-5.3-flash` |
| Transporte | Workers AI REST desde los Secrets propios de `IGC` |
| HTTP | 200 |
| finish_reason | `stop` |
| Formato | JSON completo y validado |
| Prompt tokens | 565 |
| Completion tokens (incluye razonamiento) | 560 |
| Total tokens | 1125 |
| Provider request ID | `6c96c07925864384afa1513e5c7b2cbb` |
| Intentos de proveedor | 1 |
| Reintentos | 0 |
| Reserva | No abierta |
| PredictionLock | No creado |

Configuración: `system` / `user` separados, `temperature=0`, `reasoning_effort=low`, `max_completion_tokens=4096`.

Selección GLM: **`urn:igc:candidate:CS-01` y `urn:igc:candidate:CS-02`**. Según su JSON, las cinco observaciones ruidosas de salida acumulada no permiten distinguir inequívocamente una cola de una etapa de otra de dos etapas. Propone un nuevo ensayo con reset, el mismo pulso y muestreo denso temprano para ver retraso/forma S, más evaluación retenida de tiempos tardíos.

**Cautela interpretativa:** que CS-01 prediga una entrega temprana y CS-02 muestre un retraso puede ser una distinción teórica dependiente de tasas, observables y fronteras, no una falsación conseguida en este experimento. El modelo **no** descubrió un candidato fuera del catálogo ni podó ninguno. Su propuesta de ensayo no demuestra utilidad incremental de S sobre enumeración D.

## Comparación con Short

El diagnóstico previo [Short Actions 40174313889](https://github.com/yudocyudoc/short/actions/runs/40174313889) ejecutó el mismo cuerpo con idéntico hash SHA-256, HTTP 200 y JSON válido. Short consumió 565 tokens de entrada y 409 de salida (974 total), mientras que IGC consumió 565 y 560 (1125 total). Ambos conservaron **CS-01 y CS-02**. Temperatura 0 no garantiza identidad de respuestas de una corrida a otra.

## Límites metodológicos

Esta fue una prueba **expresamente autorizada** de acceso y generación desde los Secrets de IGC, no una nueva ronda ciega: reutiliza el mismo escenario NW2 ya probado. Ninguna inferencia debe trasladarse retrospectivamente al recibo formal S, no se crea ATMS ni simulación OpenModelica ni PredictionLock, y **no se consulta la reserva**. No hubo reintentos por error ni selección de la respuesta preferida. Los resultados completos están en los artefactos enlazados.

**Conclusión:** la conexión IGC→Cloudflare puede ejecutar GLM-5.3 con salida JSON útil. El riesgo de credenciales y formato para esta configuración está reducido; aún falta evaluar ventaja metodológica de S frente a D en un mundo verdaderamente nuevo y sellado.
