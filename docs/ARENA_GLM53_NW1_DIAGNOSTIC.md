# IGC NW1 — GLM‑5.3 Flash, nuevo mundo: primera ronda exploratoria con congelación temporal

**Veredicto: NO IDENTIFICÓ UNA ESTRUCTURA, NI SUPERÓ LA ENUMERACIÓN.** Se completó una llamada auténtica a GLM-5.3 (Cloudflare Worker AI), se conservó su respuesta, se ajustaron por separado CS-01/CS-02, se comprometieron ambas trayectorias RK4 en GitHub ANTES de generar la evaluación y se calculó RMSE posterior.

## Procedencia y límite metodológico

- Compromiso criptográfico previo de generador privado `sha256:5c9baec2beb43724d3a8552527d847066be2a18efdf2758e58d940419988acee`, hecho público en `glm53_nw1_commitment.json`, ANTES de enviar a GLM. La semilla/verdad completa se verificó tras congelar, con nonce público en reporte final.
- GLM recibió solo `glm53_nw1_primary.json`, especificación, catálogo neutral y `glm53_nw1_request.json`; su respuesta real `glm53_nw1_response.json` fue archivada antes de calcular y publicar el archivo de predicciones.
- Compromiso explícito de predicciones en `glm53_nw1_predictions_frozen.json`, commit `d245225cb644a00495035601b0e59411d094b78b`. Contiene las dos trayectorias S/D a 13 tiempos, ajustes de parámetros y adecuación G3. La reserva se generó y publicó **después**, commit `51d42672c54743cfc3349070a4dcc2e52d4f3826`.
- Los compromisos y commits documentan orden/integridad, pero **no** independencia del custodio (el operador conoce y puede reescribir datos fuera del repositorio).
- **NO se ejecutó el pipeline Arena nativo con recibo `arena_s_real.py`, verificaciones de `s_submission`, simulación OpenModelica para NW1 ni `arena_s_pilot_lock`.** Las predicciones se generaron con formulación RK4 de FM‑B5; son compatibles con la construcción pero no equivalen a predicciones numéricas verificadas para el escenario NW1 mediante OpenModelica. Por tanto no se le debe asignar un estado formal `LOCKED_NOT_EVALUATED` de Arena.

## Respuesta del modelo y G3

GLM‑5.3 eligió ambas: `CS-01`, `CS-02`. Reconoció que 5 mediciones ruidosas no son suficientes para distinguirlas y pidió muestreo temprano denso. No eligió ni programó autónomamente el pulso: se fijó en el protocolo.

| Candidato | RMSE de construcción | G3 (umbral 0.24) | Parámetros ajustados (capacidad, tiempo) | RMSE nuevo pulso |
|---|---:|---|---|---:|
| CS-01 | 0.126196 | ADECUADO | 1.2, 1.6 | **0.223818** |
| CS-02 | 0.025462 | ADECUADO | 1.2, 1.0 | 0.555564 |

La verdad revelada tras congelar fue un generador **CS-02**, capacidad 1.6, tiempo 0.85. La estimación puntual de ambos modelos llevó la capacidad al mínimo de la cuadrícula (1.2). A pesar de que CS-02 ajustó mucho mejor construcción, **CS-01 predijo mejor el ensayo nuevo**. Esto es un contraejemplo a equiparar mejor ajuste observado, identificación de estructura y éxito predictivo. Se preserva la incertidumbre de parámetros: 14 y 28 puntos de rejilla compatibles, respectivamente; las envolventes no son intervalos frecuentistas validados.

## Hallazgo

GLM‑5.3 no aportó discriminación estructural en NW1. El sistema S mantuvo el mismo conjunto que D por enumeración y los mismos parámetros ajustados, por tanto **no existe diferencia de predicciones entre S y D** en esta ronda. Tampoco se demostró que ATMS aportara ventaja sobre una enumeración que no descarta ninguno.

Lo significativo es el desacoplamiento empírico entre la estructura generadora conocida, la calidad del ajuste a construcción y el error de predicción en pulso externo. Debe investigarse identificabilidad con perturbaciones y representación de incertidumbre, no sustituirlo por un acierto aparente de GLM.

**Decisión:** cerrar como ensayo exploratorio negativo con integridad temporal de respuestas/predicciones. No convertirlo en victoria formal de IGC, ni reiterar llamadas al mismo mundo para seleccionar la respuesta favorable. Próxima ronda formal: nuevo generador + captura S nativa + Modelica S/D + `PredictionLock` real antes de reserva con custodia independiente.
