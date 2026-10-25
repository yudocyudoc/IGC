# NW2 — Diagnóstico del prompt system/user desde Short (2026-10-25)

**Estatus:** `VALID_DIAGNOSTIC_JSON_NOT_ARENA_SUBMISSION`.

**Procedencia verificable:** Short GitHub Actions run [40174313889](https://github.com/yudocyudoc/short/actions/runs/40174313889), job `diagnose`; artefacto [12591826389](https://github.com/yudocyudoc/short/actions/runs/40174313889/artifacts/12591826389), archivo `provider-result.json`. El resultado fue leído directamente del ZIP descargado de GitHub Actions después de confirmar el job exitoso.

Se usó la solicitud **congelada** en `data/diagnostics/glm53_nw2_config_probe_request.json`, replicada en Short: modelo `@cf/zai-org/glm-5.3-flash`, mensajes `system` y `user` separados, `temperature=0`, `reasoning_effort=low`, `max_completion_tokens=4096`.

## Resultado observado

| Campo | Valor |
|---|---|
| HTTP | 200 |
| Terminación | `stop` |
| Respuesta | JSON completo y validado |
| Llamadas | 1 |
| Reintentos | 0 |
| Tokens entrada | 565 |
| Tokens generación | 409 |
| Tokens total | 974 |
| ID respuesta Cloudflare | `3bea8c7896fd4cf590aedb8f85aa0948` |
| SHA-256 del cuerpo de solicitud | `sha256:0426e743b2119bf656d0670cade3aba185f67fd4591c8a7884b0247fda96c29f` |

**Selección declarada por GLM:** `urn:igc:candidate:CS-01` y `urn:igc:candidate:CS-02`. No abstuvo, no descartó ninguna y no generó trayectorias. La justificación de GLM dice que cinco observaciones escasas de salida acumulativa son compatibles con ambos mecanismos, sin prueba de identificación. Incertidumbres citadas: ruido y su correlación, parámetros/constantes de tiempo, alineación relativa de los dos ensayos y posible degeneración de etapas.

**Prueba sugerida por GLM:** ensayo con reset y muestreo denso del transitorio, ajuste de ambas estructuras y contraste con criterios de residuos/información preregistrados. La respuesta propone rechazo de CS-02 por parsimonia si CS-01 basta: esto **no equivale a falsación física** de CS-02. La justificación menciona otro perfil de entrada pero `next_test` vuelve al pulso declarado; se requiere fijar la perturbación antes de cualquier nuevo estudio.

## Adjudicación

- El cambio de configuración resolvió en **esta única llamada** el problema de salida vacía que ocurrió con `max_completion_tokens=1400` y un solo mensaje `user`. No hay réplica ni aislamiento causal de cuál cambio mejoró el formato.
- **No hay ventaja demostrada de selección estructural**: GLM retuvo todo el catálogo. No se ha ejecutado el comparador D ni simulaciones OpenModelica de esta nueva llamada.
- El archivo de Short es **diagnóstico de configuración**. No se debe convertir retrospectivamente en un recibo nativo `arena_s_real`, ni computar como ronda S de NW2, ni fabricar PredictionLock ni consultar reserva. Su origen, costo y hash quedan disponibles para diseñar un nuevo ensayo preregistrado.
- La respuesta íntegra se conserva en el artefacto de GitHub Actions; esta nota registra interpretación y procedencia, no sustituye la respuesta cruda.

**Siguiente paso científico recomendado:** mantener estas opciones de inferencia para un mundo **nuevo** con selección sellada, ajuste G3, ejecución S/D verificable en OpenModelica y PredictionLock antes de abrir reserva. No repetir NW2 para buscar una selección diferente.
