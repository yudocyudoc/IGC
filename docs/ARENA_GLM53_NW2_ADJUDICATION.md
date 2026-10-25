# NW2 — Adjudicación tras reconexión Cloudflare (2026-10-25 UTC)

**Resultado:** CAPTURA SIN PROPUESTA S VÁLIDA; no pasó a ATMS, simulación, LOCK ni evaluación.

La preparación de NW2 terminó exitosamente en [CI 40167148525](https://github.com/yudocyudoc/IGC/actions/runs/40167148525), con solicitud congelada SHA-256 `a784a3b4b731e4e9e428620a5f64306da747aacadab176a778f2a0a571783893`.

Intento 1: Cloudflare devolvió HTTP 401, sin ejecución del modelo ni respuesta; registrado en `arena_glm53_nw2_auth_blocker.json`.

Tras reconectar por acción explícita del investigador, se intentó una vez más la solicitud **idéntica**, sin consultar la reserva. La API respondió HTTP 200 pero con `finish_reason=length`, `content=""`; utilizó 564 tokens de entrada y los 1400 tokens máximos de generación en `reasoning_content`, sin objeto JSON final. Se preservaron los metadatos, estado, coste en tokens y el hecho de que hubo razonamiento interno, sin archivar su contenido. Ver `arena_glm53_nw2_provider_truncated.json`.

**Interpretación:** fracaso de producción/contrato de respuesta; NO equivale a abstención razonada de S ni a una decisión estructural. No rellenar S con ambas alternativas, no cambiar a mock, no simular D para disfrazar un LOCK del experimento. El informe sigue siendo `NOT_LOCKED_NOT_EVALUATED`.

El workflow actual permite preparar y ejecutar la segunda fase solo cuando existe `arena_glm53_nw2_response.json`. Ese archivo no se creó y no debe generarse sintéticamente. El job de preparación verde no es éxito del ensayo S.

**Decisión siguiente:** si se desea seguir, abrir campaña independiente NW3 preregistrando *antes* de inferencia un contrato de respuesta que reserve suficiente espacio al JSON (p.ej. desactivar pensamiento, si el proveedor admite la opción, o incrementar presupuesto de generación), junto con prueba de esquema y fail-closed. No reejecutar NW2 hasta obtener selección favorable; tratar NW2 como intento terminado y registrar el coste observado.
