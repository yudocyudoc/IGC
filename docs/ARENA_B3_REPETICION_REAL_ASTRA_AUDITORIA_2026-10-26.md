# Arena B3 · Repetición real auditable para Astra (2026-10-26)

**Motivo:** la ejecución B3 real anterior [#40288518137](https://github.com/yudocyudoc/IGC/actions/runs/40288518137) generó y simuló un modelo nativo, pero el paquete no se pudo descargar por permisos de un archivo OpenModelica creado con Docker. El investigador autorizó explícitamente volver a ejecutar para que Astra pudiera auditar el modelo completo. No se recuperaron ni se inventaron los bytes perdidos de aquel ensayo.

## Ejecución nueva y conservación verificadas

- **GitHub Actions:** [#40290192821](https://github.com/yudocyudoc/IGC/actions/runs/40290192821), commit de autorización `d3481740e096eec32c637010af1be44f7ddec954`, **SUCCESS en todos los steps**.
- **Antes de OpenModelica:** [artefacto nativo y Cloudflare crudo #12635881351](https://github.com/yudocyudoc/IGC/actions/runs/40290192821/artifacts/12635881351) (**existe, descargado y leído**; 10 archivos, 2026-12-10 fecha de expiración del proveedor).
- **Después de OpenModelica:** [artefacto completo #12635856513](https://github.com/yudocyudoc/IGC/actions/runs/40290192821/artifacts/12635856513) (**existe, descargado y leído**, contiene Modelica, CSV, adjudicación, recibos y manifiesto).
- SHA256 bytes nativos B2: `d7630830b4812c8880dc88c5f93f821707a75d22e0ecdf2cc1e9b5d8ec0889b9`.
- SHA256 bytes nativos B3: `dfe45d3128bbf9aaa91a2d0be0028f4b8be29610b42d9114e4dae09fc4a14c2b`.
- Se verificaron **73 entradas de hash** en el manifiesto del artefacto completo: 0 faltantes, 0 discrepancias. El manifiesto emitido por la CI contiene un sufijo final literal `\\n` que impide `json.load` estricto; se pudo validar con `JSONDecoder.raw_decode` más comprobación del sufijo, conservando sus bytes. El paquete para Astra entrega adicionalmente un manifiesto JSON bien formado.
- **Proveedor:** `@cf/zai-org/glm-5.3-flash` vía Cloudflare Workers AI, HTTP 200, una llamada, `finish_reason=stop`; 5385 tokens entrada, 3617 tokens salida. El motor Buffalo original es `UB-IAD/sd-ai@5199f7b45f3a7ae4a773cb0dd8542940aabe9edc`, llamado con el `currentModel` anterior. No hay nuevo dato reservado ni salida de D/M.

## Cambio observado en los dos documentos nativos

- B2: 15 variables, **19** relaciones. B3: 15 variables, **18** relaciones.
- La ecuación de `completions` pasó de **`completion_capacity * capacity_utilization`** a **`completion_capacity`**.
- No se añadieron ni eliminaron variables. Solo cambió el cálculo de `completions`, además de textos de documentación de diversos nodos. El enlace causal directo `capacity utilization → completions` fue eliminado. Se reescribió la justificación textual de `completion capacity → completions`. El camino de stocks no cambió.
- `nominal capacity = 0.6 items/hour`, `completion time = 1 hour` y funciones gráficas de utilización se mantuvieron.
- Buffalo documentó que su propia fórmula anterior multiplicaba la utilización dos veces (una dentro de la capacidad efectiva y otra dentro de completions). Lo interpretó como doble conteo y corrigió solo esa ecuación, **sin optimizar parámetros**.

## Modelica real y comparación de construcción

**G0:** `TRANSLATED_CONDITIONALLY_LOOKUPS_REQUIRE_EQUIVALENCE_CHECK`, no prueba de paridad Buffalo-native/Modelica para funciones gráficas.

**G2:** `PASS_REAL_OPENMODELICA_OWN_CANDIDATE`, verificado sobre CSV real con conservación material.

| Hora | Entregado observado | Simulado B2 | Simulado B3 |
|---:|---:|---:|---:|
| 0 | 0.000000 | 0.000000 | 0.000000 |
| 1 | 0.350000 | 0.387606 | 0.412150 |
| 2 | 1.100000 | 0.987606 | 1.012150 |
| 4 | 2.500000 | 2.187606 | 2.212150 |

**RMSE t=1,2,4:** B2 `0.19290471909474044` → B3 `0.17742395144560083` items; **−8.025%**. Incluyendo t=0: `0.1670603872459463` → `0.1536536491917071` items.

No es un G3 certificado: son **los mismos datos de construcción usados para dar feedback**, sin cota instrumental predeclarada. Reserva predictiva: **NOT_RUN**. Causalidad e identificabilidad: **NOT_DEMONSTRATED**.

## Qué debe revisar Astra

1. Examinar `native-output.json` de B2 y B3, la respuesta cruda de Cloudflare, y el registro del feedback. No aceptar resúmenes en sustitución del modelo original.
2. Distinguir el único cambio de ecuación y eliminación del enlace semántico de los cambios puramente explicativos/documentales.
3. Verificar Modelica generado, CSV y `adjudication.json` contra los observables de construcción, y el supuesto de interpolación de funciones gráficas.
4. Evaluar si la hipótesis de «doble aplicación de utilización» tiene fundamento mecanístico, si el modelo respeta flujos, unidades y límites, y qué experimentos permitirían falsarla.
5. No inferir ventaja frente a D/M a partir de esta prueba no equiparada.

**Paquete portátil generado para Astra en esta conversación:** `ASTRA_B3_EVIDENCIA_REAL_2026-10-26.zip`, con B2, B3, respuesta original, Modelica, ambos CSV, adjudicación y manifiesto SHA validado. No es un nuevo resultado de inferencia; es copia selectiva de los artefactos reales y una comparación independiente.
