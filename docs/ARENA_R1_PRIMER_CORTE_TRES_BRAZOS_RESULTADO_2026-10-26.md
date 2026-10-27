# R1 — Primer corte conjunto D/B/M: resultado físico negativo de Buffalo

**Corte experimental:** evidencia primaria R0 común ya ejecutada por D/M en PR #53. **Buffalo:** una única inferencia real en [Actions #40452596916](https://github.com/yudocyudoc/IGC/actions/runs/40452596916) con el motor cuantitativo original `UB-IAD/sd-ai@5199f7b45f3a7ae4a773cb0dd8542940aabe9edc` y Cloudflare `@cf/zai-org/glm-5.3-flash`. Ningún otro modelo fue enviado a Buffalo; el join D/M se hizo después.

## Resumen del resultado observable

| Brazo | Ensayo inicial | Diagnóstico |
|---|---|---|
| D | 6 estructuras propias simuladas físicamente | G2 comprobado; RMSE menor de construcción 0.150205 items en 4 tiempos, no identificación |
| M3 | 3 estructuras propias simuladas físicamente | G2 comprobado; menor RMSE 0.316560, política original emite ABSTAIN |
| Buffalo inicial R1 | 1 modelo nativo generado con 17 variables, 17 relaciones; G0 traduce condicionalmente | **G1 negativo** por bucle algebraico sin anclaje; OpenModelica no construye modelo; G2 no ejecutado, G3 no calculable |

**La ejecución de Buffalo fue real, no mock**. `live_provider_calls=1`, `intercepted_http_calls=1`, HTTP 200, respuesta cruda guardada antes de traducirla, `raw_cloudflare_preserved=true`. Tokens reportados: 1477 de entrada y 3300 de salida, por debajo de 7000 de salida. Costo indicativo **USD 0.00187155**, calculado con las tarifas publicadas Cloudflare Flash: $0.15/M entrada y $0.50/M salida. Son costos estimados basados en tokens reportados, no una factura auditada.

Identidad SHA256 de **bytes del JSON nativo**: `8097496d8033bfe8b5a93eeb7d391f7c98f6bb315bdfb9e63f62b6910b437eac`. Registro bruto en el [artefacto pre-G0 #12710838968](https://github.com/yudocyudoc/IGC/actions/runs/40452596916/artifacts/12710838968). Paquete completo inicial: [#12710958258](https://github.com/yudocyudoc/IGC/actions/runs/40452596916/artifacts/12710958258). Sin segundo llamado y sin alterar el JSON.

## Por qué G2 no funcionó

Buffalo genera dos auxiliares **sin ecuación que determine su valor**:

```modelica
congestion_multiplier = product_of_capacity_effects;
product_of_capacity_effects = congestion_multiplier;
```

Estas dos igualdades son linealmente dependientes. Constituyen una identidad circular sin anclaje, no un feedback dinámico con una ecuación de estado. Aunque `checkModel` informó 17 ecuaciones y 17 variables, `simulate()` devolvió `Failed to build model`. Por tanto, el resultado no puede etiquetarse G2 PASS y no hay CSV del cual calcular RMSE.

Una segunda anomalía separada: `capacity_constrained_throughput` representa conceptualmente el cuello de botella descrito en la explicación, pero `completion_rate = work_in_process / processing_time` nunca utiliza esa capacidad. El mecanismo anunciado no restringe efectivamente el flujo de terminación. Además la ecuación del pulso tiene una rampa lineal desde t=1 a 2 horas: en t=1.5 el factor es 0.5, cuando la descripción textual afirma un pulso rectangular hasta t=2. Son discordancias de la propuesta original.

El diagnóstico está reproducido por `scripts/arena_r1_buffalo_postonly.py` sobre **los mismos bytes nativos**. No se elimina la variable circular ni se reemplaza ninguna ecuación para obtener un ajuste favorable. La existencia de la incongruencia y el error del solver son observables; no se deduce que Buffalo sea incapaz de producir mejores modelos en otros intentos ni que toda la arquitectura sea insuficiente.

## Veredicto R1 y paso a R2

**R1 cerrado como primera ronda de propuestas/intentos D/B/M con un resultado negativo propio**: D y M llegaron a G2, Buffalo produjo una hipótesis nativa pero quedó detenido en G1/G2. La afirmación `tres modelos/métodos físicamente exitosos` sería falsa; tampoco existe ganador científico, error instrumental conocido, holdout independiente o comparación estadística justa.

**Siguiente experimento R2:** entregar a Buffalo el problema que presenta su propia propuesta y evidencia de su propio fallo de compilación, sin indicarle la reparación ni compartir candidatos rivales. Conservar R1 intacto y considerar revisión o abstención. M3 permanece sin candidato elegido; D conserva sus alternativas y supuestos. La memoria temporal debe poder reconstruir este estado previo.
