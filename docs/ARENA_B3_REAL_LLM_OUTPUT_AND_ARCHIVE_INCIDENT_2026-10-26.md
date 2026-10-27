# Arena B3 — inferencia real con feedback físico, ejecución y auditoría de archivado

**Fecha:** 2026-10-26. **Rama:** `feature/arena-b-physical-feedback-v01`; PR #33. **Fuente:** [GitHub Actions push #40288518137](https://github.com/yudocyudoc/IGC/actions/runs/40288518137), job `121457830647`. Ejecución remota **efectuada**, no simulación offline. **Conclusión del job: FAILURE exclusivamente en empaquetado final**, después de que inferencia y simulación pasaron.

## Cadena de evidencia observada en GitHub Actions

1. Se descargaron y autenticaron tres evidencias Buffalo B2 originales: modelo nativo, CSV OpenModelica y diagnóstico físico de construcción (SHA-256 comprobados). El mensaje a Buffalo contiene **solo** su `currentModel` y sus resultados físicos propios, sin D/M, mundo del evaluador ni reserva.
2. Se verificó la petición anterior, [Actions push #40286989747](https://github.com/yudocyudoc/IGC/actions/runs/40286989747): un HTTP 200 real, `live_provider_calls=1`, `finish_reason=length`, `completion_tokens=3500`, `ResponseFormatError: Bad JSON returned by underlying LLM`. El intento y la respuesta truncada fueron archivados en [artefacto #12634402053](https://github.com/yudocyudoc/IGC/actions/runs/40286989747/artifacts/12634402053). **No se completó una revisión nativa B3 válida en aquel intento.**
3. Una autorización expresa y un nuevo marcador `BUFFALO_B_PHYSICAL_FEEDBACK_OUTPUT_BUDGET_RETRY.json` habilitaron **una sola llamada nueva** tras validar la respuesta truncada. En esta extensión, y únicamente para esta, se elevó la salida máxima de **3500 a 7000 tokens**. Los experimentos originales conservan el límite 3500 y no se alteró el motor universitario ni el esquema cuantitativo.
4. La llamada real a Workers AI `@cf/zai-org/glm-5.3-flash` informó **HTTP 200**, exactamente `live_provider_calls=1` y `intercepted_http_calls=1`, entrada **5385 tokens** y salida **4166 tokens**. El motor Node original Buffalo `UB-IAD/sd-ai@5199f7b45f3a7ae4a773cb0dd8542940aabe9edc` devolvió **un modelo nativo completo** (`model_returned=true`, `native_error=null`, **15 variables y 19 relaciones**, `revision_changed_model=true`, `revised_g1_issue_count=0`).
5. El step **`Adjudicate REAL Buffalo revision through strict G0 and real OpenModelica G2`** también concluyó **SUCCESS**. Imprimió exactamente:
   ```
   BUFFALO_OWN_PHYSICAL_MODEL_ADJUDICATED TRANSLATED_CONDITIONALLY_LOOKUPS_REQUIRE_EQUIVALENCE_CHECK PASS_REAL_OPENMODELICA_OWN_CANDIDATE IMPROVED_IN_SAMPLE
   ```
   Es decir, la versión de Buffalo sí fue traducida bajo las mismas hipótesis de funciones gráficas, se ejecutó en OpenModelica real y presentó **menor RMSE sobre los mismos datos de construcción**.

## Incidente de conservación de evidencia

El último step, `Archive complete diagnostic and all transport receipts including failure`, terminó **FAILURE** por falta de permisos sobre un archivo generado como root por Docker:

```
EACCES: permission denied, open 'artifacts/b-physical-evaluation/BuffaloNative_8d42ff8563bc.log'
```

El artefacto completo de esa ejecución **NO se creó** (Actions devuelve lista de artefactos vacía). Por tanto, pese al éxito comprobado de inferencia y G2, **no están recuperables en esta sesión los bytes de la respuesta B3 real ni el CSV/modelo revisado**. No deben inventarse valores por tiempo, valores finales de parámetros, puntos de lookup ni RMSE B3 exacto. Tampoco es legítimo reconstruirlos a mano a partir de la respuesta truncada del intento anterior: aquella no es esta nueva salida.

El RMSE de referencia B2 era `0.19290471909474044 items` con tres observaciones posteriores a t=0 y `0.1670603872459463 items` incluyendo t=0; la mejora B3 solo está certificada **cualitativamente por el comparador ya ejecutado** como `IMPROVED_IN_SAMPLE`. No existe aquí el número exacto B3 ni una reserva evaluada.

## Remediación de la infraestructura (sin gasto adicional)

Se actualizó `.github/workflows/arena-b-physical-feedback.yml` **después del run** para:

- Subir **primero** los archivos originales `b-physical-live/` como artefacto separado **antes de iniciar Docker**, evitando que un fallo posterior en OpenModelica destruya la evidencia del LLM.
- Corregir permisos/propietario de `artifacts/b-physical-evaluation` con `sudo chown -R` y `chmod -R u+rX` **antes del empaquetado final**.
- Mantener la autorización de llamadas remotas por un marcador **añadido en el commit HEAD**, primer intento del workflow, rama exacta, verificación retrospectiva del fallo anterior y sin reintentos automáticos. **Ningún commit de remediación reautoriza Cloudflare.**

No se llama otra vez al proveedor para «recuperar» el artefacto perdido. Cualquier ensayo adicional requiere una nueva autorización y debe dejar constancia del consumo previo.

## Veredictos

| Criterio | Resultado |
|---|---|
| Real Buffalo original recibió feedback físico propio | **PASS** |
| Respuesta real completa de Cloudflare aceptada por Buffalo | **PASS** |
| Cambio de modelo nativo (15 variables/19 relaciones) | **PASS observado**; detalle preciso no conservado |
| G0 bajo adaptador estricto con lookups | **CONDICIONAL**, no paridad nativa certificada |
| G2 OpenModelica sobre la versión revisada B3 | **PASS**, demostrado por ejecución |
| RMSE sobre construcción B3 vs B2 | **MEJORA IN-SAMPLE**, magnitud exacta no recuperable |
| G3 con tolerancia instrumental y causalidad | **NO CERTIFICADO** |
| Evaluación reservada/holdout | **NOT_RUN** |
| Disponibilidad del artefacto B3/CSV | **FALLO DE ARCHIVADO** |

**Límite central:** demuestra capacidad técnica de revisión dinámica y mejora *en los mismos datos utilizados como feedback*. No demuestra inferencia causal, capacidad predictiva nueva ni ventaja comparativa sobre los brazos D/M.
