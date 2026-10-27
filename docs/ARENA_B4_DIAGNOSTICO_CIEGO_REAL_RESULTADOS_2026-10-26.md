# Arena Buffalo B4 — diagnóstico sin pistas, inferencia real y adjudicación física

**Fecha:** 2026-10-26. **Motivo:** Astra detectó que Buffalo B3 recibió explícitamente en el feedback la identidad algebraica `completions = nominal_capacity * capacity_utilization^2`, y por tanto B3 no demostraba localización autónoma del problema. B4 repite el razonamiento con **B2 exacto y las mismas observaciones y simulación**, eliminando ese señalamiento previo.

## Ejecución comprobada

- [Inferencia real Workers AI #40393509770](https://github.com/yudocyudoc/IGC/actions/runs/40393509770): motor Buffalo original `UB-IAD/sd-ai@5199f7b45f3a7ae4a773cb0dd8542940aabe9edc`, `currentModel=B2`; Cloudflare `@cf/zai-org/glm-5.3-flash`. **HTTP 200**, `finish_reason=stop`, una llamada en esa ejecución, sin retry, **5058 tokens de entrada y 4165 de salida**.
- [Artefacto original crudo previo a Modelica #12685206485](https://github.com/yudocyudoc/IGC/actions/runs/40393509770/artifacts/12685206485) y [artefacto completo de la ejecución #12685882079](https://github.com/yudocyudoc/IGC/actions/runs/40393509770/artifacts/12685882079). Ambos retienen el feedback neutral, **prompt exacto**, respuesta cruda de Cloudflare, salida nativa B4 y recibos.
- **SHA-256 original B2:** `d7630830b4812c8880dc88c5f93f821707a75d22e0ecdf2cc1e9b5d8ec0889b9`. **SHA-256 nativo B4:** `c3662f90d7fb7a6211b62f35e13739000d2f6b90bcbb6d44cabc131dd45e7bbb`.
- [Adjudicación sin nueva inferencia #40394222878](https://github.com/yudocyudoc/IGC/actions/runs/40394222878), **SUCCESS**, artefacto [#12686097180](https://github.com/yudocyudoc/IGC/actions/runs/40394222878/artifacts/12686097180). El primer intento del job real terminó `FAILURE` únicamente en el paso de adjudicación porque el lector heredado esperaba `no_cross_arm_information` en lugar del contrato B4 `scope.competing_arm_data_included`. Se corrigió el verificador y **se reutilizó la respuesta archivada**, sin repetir Cloudflare.

El modo B4 tiene controles de esquema, SHA, residual firmado y columnas de estado, y bloquea la inclusión de deducciones algebraicas, nombres de la ecuación sospechosa, otros brazos y datos reservados. La condición es una **extensión diagnóstica** posterior al presupuesto original ya consumido, no otra iteración dentro del diseño original.

## Contenido entregado a Buffalo (y lo excluido)

El input neutral contiene t={0,1,2,4}, valores observados y simulados de entregas, residuos, `pending_work`, `delivered_work`, `arrivals`, `completions` y conservación material verificada del CSV B2. Buffalo recibe su **propio modelo nativo B2** por el parámetro `currentModel`. **No se adjunta:** `candidate_mechanism_observation`, `utilization^2`, deducción de doble multiplicación, restricción de capacidad ya resuelta, respuesta previa B3, resultados de D/M, generador sintético ni datos reservados.

La tarea solicita que evalúe autónomamente si es necesario modificar parámetros, estructura o ecuaciones y justifique la incertidumbre. El modelo original B2 inevitablemente contiene sus propias ecuaciones; no se oculta esa información legítima.

## Propuesta real del LLM

Buffalo devuelve **16 variables y 20 relaciones**, frente a 15/19 en B2. Realiza estos cambios materiales:

1. `nominal capacity:` `0.6 → 0.7 items/hour`. El texto de Buffalo lo vincula a las tasas de entrega observadas en la etapa tardía.
2. Añade una variable `capacity ramp` dependiente de `TIME` con puntos `(0,0.5), (1,0.5), (3,1), (8,1)`. Sugiere capacidad que se incorpora gradualmente.
3. `completion capacity = nominal_capacity * capacity_utilization * capacity_ramp`.
4. Conserva **`completions = completion_capacity * capacity_utilization`**. Por tanto, **no detectó ni eliminó** la aplicación doble de utilización de B2.

Se conservaron los dos stocks y se añadió un mecanismo de capacidad temporal; no fue un cambio meramente estilístico.

## Resultado numérico real en OpenModelica

B4 pasó el traductor estricto con supuestos expresos de lookup, OpenModelica G2 y conservación global `1.11e-15` items. La paridad exacta del lookup con una simulación nativa Buffalo **NO se certificó**.

| t (h) | Observado | B2 | B3 (con pista) | **B4 (sin pista)** |
|---:|---:|---:|---:|---:|
| 1 | 0.350000 | 0.387606 | 0.412150 | **0.218986** |
| 2 | 1.100000 | 0.987606 | 1.012150 | **0.645549** |
| 4 | 2.500000 | 2.187606 | 2.212150 | **1.947111** |

RMSE de construcción sobre **n=3** (t>0):
- B2: `0.19290471909474044` items.
- B3 con pista mecanística: `0.17742395144560083` items.
- **B4 sin pista: `0.4200698982977454` items**.

B4 **empeora** el ajuste de B2 en ~118 % respecto al RMSE inicial. Su nuevo factor de rampa reduce las primeras entregas, produce residuos negativos en los tres tiempos y no recupera el mecanismo que explicaría mejor el patrón.

**Incompatibilidad condicional residual:** los dos factores `capacity_ramp` y `capacity_utilization` están en [0,1] y se mantiene utilización al cuadrado, por lo que `completions ≤ 0.7 items/hour`; el incremento observado de la hora 1 a 2 es **0.75 items**. Para un ajuste exacto de esos dos puntos, aun suponiendo que el resto de la dinámica fuese correcto, se necesitaría ruido absoluto simétrico por punto de al menos `(0.75−0.70)/2 = 0.025 items`. **Sin cota de ruido empírica no constituye falsación definitiva.**

## Veredicto limitado

- **PASS observado:** dado un modelo previo y evidencia física neutral, el motor Buffalo original produjo *autónomamente* una revisión no trivial (parámetro de capacidad + mecanismo de rampa), nativa y ejecutable.
- **NO DEMOSTRADO:** localización correcta de la anomalía física, explicación causal mejor o identificación del mecanismo generador.
- **Resultado negativo útil:** la revisión **empeoró** la adecuación de construcción y no resolvió el límite de flujo en t=1–2. El hecho de que B3 (con pista) ganara en RMSE y B4 (sin pista) perdiera no estima confiabilidad estadística ni permite adjudicar entre hipótesis físicas con una muestra de una respuesta por condición.
- **NO ejecutar otro LLM automáticamente** para «reparar» el B4; conservarlo como evidencia de los límites actuales del razonamiento. La próxima acción experimental debe distinguir opciones mediante nuevas observaciones/pulsos y revisión adversarial.

Este PR permanece como **draft**; no se fusiona con D/M ni con main.
