# NW2 GLM-5.3 — prueba de configuración desde GitHub Actions

**Propósito:** comprobar si el modelo produce JSON completo tras separar `system`/`user`, usar temperatura 0, razonamiento `low` y permitir hasta 4096 tokens. **No equivale a inferencia estructural válida de NW2** ni alimenta automáticamente S/ATMS, OpenModelica, PredictionLock o reserva.

## Ejecución

- Solicitud previa congelada: `data/diagnostics/glm53_nw2_config_probe_request.json`. Su contenido es exclusivamente construcción, catálogo y la pregunta; ninguna reserva.
- Un único disparador de push: `data/diagnostics/GLM53_GITHUB_PROBE_TRIGGER_NW2.json` creado en la rama `experiment/arena-glm53-nw2-e2e` después del workflow.
- Workflow: `.github/workflows/arena-glm53-github-probe.yml`; pruebas sin red antes de la llamada; un POST sin reintento a Workers AI.
- Dependencias: secretos **del repositorio IGC** `CLOUDFLARE_API_TOKEN` (o `CF_API_TOKEN`) y `CLOUDFLARE_ACCOUNT_ID` (o `CF_ACCOUNT_ID`); la ID de cuenta también puede ser variable Actions. Secretos de otro repositorio o entorno no son automáticamente accesibles. Jamás guardar credenciales en código, logs o artefactos.
- Los secretos no se leen hasta que la prueba de contrato y el marcador son correctos. Si faltan, el job falla SIN llamar al proveedor.
- La ejecución del workflow usa `github.run_attempt == 1`; rerun del mismo run se bloquea. No hay cron, polling ni reintentos HTTP. Cambiar de nuevo el marcador puede producir otra ejecución, por lo que queda prohibido actualizarlo como método de reintento de esta campaña.

## Resultados

- Artefacto (cuando el job ejecuta): `nw2-glm53-github-probe-once` → `provider-result.json`; registra `status`, HTTP status, tokens, `finish_reason`, cuerpo final, validez de JSON y selección. No guarda razonamiento interno ni secretos.
- `VALID_DIAGNOSTIC_JSON_NOT_ARENA_SUBMISSION`: completó JSON parseable con los cinco campos y IDs declarados. **No** cuenta como resultado S/Arena.
- `RATE_LIMITED_NO_RETRY`: HTTP 429 (el entorno de GitHub no elimina la saturación en Cloudflare).
- `PROVIDER_HTTP_ERROR_NO_RETRY`: otros HTTP, incluidos 401.
- `UNUSABLE_S_JSON`: respuesta vacía, truncada, sin estructura o con candidatos inventados. Tampoco equivale a abstención científica.
- `CONFIG_MISSING_*`: secret o variable ausentes/mal formados. Falla sin solicitud.

**Importante:** un workflow `workflow_dispatch` nuevo puede no aparecer en la UI si el archivo no está en `main`; esta campaña se activa por el commit explícito del archivo marcador. No volver a disparar para buscar respuestas favorables. La consulta de runs por commit del conector GitHub disponible aquí muestra solo runs de pull request; no confirma el estado del job disparado por `push`. Verificar en la pestaña Actions de GitHub y abrir el artefacto si existe.
