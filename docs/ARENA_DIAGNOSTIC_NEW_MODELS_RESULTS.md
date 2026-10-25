# Diagnóstico IGC V0 — comparación de DeepSeek 4.1 y GLM 5.3 Flash

**Estado:** EXECUTED_EXPLORATORY_WITH_MISSING_OR_INCOMPLETE_RECORDS. Comparación NO ciega: cuatro casos Q7/R4/M9/T2 previamente usados con GLM-4.7; la verdad generadora ya fue revelada en el PR #18, aunque no figura en los prompts. No se debe presentar como replicación independiente.

## Diseño preexistente

Las ocho solicitudes exactas (dos modelos × cuatro casos) se escribieron en `data/diagnostics/arena_s_new_model_comparison_requests.json` antes de consultar al proveedor. Los cuerpos de los prompts se copiaron íntegros de la comparación anterior y solo cambiaron parámetros de inferencia. Se usaron `temperature=0.1`, `reasoning_effort=low`, `max_completion_tokens=1400`, sin reintentos. GLM-4.7 original utilizó `enable_thinking=false` y 600 tokens máximos; comparar estas configuraciones **no identifica exclusivamente el efecto del modelo**. Ejecutadas vía Cloudflare Workers AI con conexión autenticada; no son capturas nativas `arena_s_real` ni incluyen el recorrido Arena→Modelica→Lock.

## Resultado por caso

| Caso | GLM 4.7 previo | DeepSeek 4.1 | GLM 5.3 | Referente determinista G3 |
|---|---|---|---|---|
| Q7 | CS-01 y CS-02 | CS-01 y CS-02 (JSON OK) | Respuesta obtenida, **no archivada**; excluir | CS-01 y CS-02 |
| R4 | CS-01 y CS-02 | CS-01 y CS-02 (JSON OK) | CS-01 y CS-02 (JSON OK) | CS-02 |
| M9 | CS-01 y CS-02 | **Respuesta truncada** (`finish_reason=length`), no parseable; no selección formal válida | **Solo CS-02** (JSON OK) | CS-01 y CS-02 |
| T2 | CS-01 y CS-02 | CS-01 y CS-02 (JSON OK) | CS-01 y CS-02 (JSON OK) | CS-02 (pero generador de tres etapas, fuera del catálogo) |

Regla: una respuesta truncada puede contener texto parcial con `selected_candidate_ids`, pero no es una selección válida ni un éxito del flujo. La llamada de GLM 5.3 Q7 fue exitosa en Cloudflare pero su archivo fue bloqueado por la herramienta de GitHub; NO se conoce un contenido archivado verificable y no se reintentó.

## Interpretación

- **Ninguna poda estructural confirmada como correcta frente a G3 en R4**: los dos modelos nuevos conservaron ambas estructuras cuando el ajuste G3 descarta CS-01. No sustituir esa decisión de S por G3 para atribuirle crédito.
- **M9 GLM 5.3 eligió solo CS-02**, coincidiendo con el generador revelado, pero **G3 admitía ambas**, y en el diagnóstico anterior la predicción puntual RK4 de CS-01 fue mejor que CS-02. El razonamiento usa ratios de incrementos y supuesta firma gamma; puede ser sugerente, no es una falsación numérica ni demuestra identificabilidad. En particular no existe evidencia de separación de envolventes que apoye descartar CS-01.
- **DeepSeek Q7 identificó explícitamente la no monotonía en una variable acumulada** y planteó incertidumbre de medición/calendario en lugar de explicar la caída como respuesta física de un acumulador. GLM 5.3 también identificó explícitamente una caída en R4 y su conflicto con la semántica acumulada; eso mejora la calidad de la explicación respecto del GLM 4.7 anterior.
- **T2 no identificado como fuera de catálogo** por ambos; conservar los dos candidatos no prueba que generaron la serie.
- DeepSeek gasta más tokens (ej. Q7 1564 vs GLM 5.3 R4 1076) y truncó M9 pese a 1400 de salida. No comparar latencias: no se registraron tiempos homólogos.
- Hay 3 respuestas JSON completas DeepSeek y 3 GLM 5.3; uno truncado y uno no archivado. No son 8/8 rondas exitosas.

## Conclusión y siguiente decisión

No se obtuvo una ventaja sólida en **selección estructural** de ninguno de los modelos nuevos frente a la enumeración CS-01/CS-02 y G3. DeepSeek y GLM 5.3 muestran mejoras de **crítica física** y propuesta de observaciones respecto de GLM 4.7, pero no demostrarían H-IGC con este ensayo.

**Decisión operativa tentativa:** priorizar GLM 5.3 para el próximo ensayo informativo por respuestas compactas y completas entre los 3 casos archivados; no tratar M9 como acierto demostrado. No descartar DeepSeek por falta de capacidad —hay riesgo de truncamiento y consumo alto para este prompt—, pero no gastar ahora rondas corrigiendo sus salidas. Mantener esta comparación como exploratoria y pasar a un protocolo de prueba discriminante.

El siguiente piloto formal necesita mundos **no reciclados**, captura uniforme y reserva abierta solo tras predicciones congeladas. Guardar por separado respuestas crudas, costos reportados y fallas de formato. No invocar al mismo modelo repetidamente para elegir la mejor respuesta.
