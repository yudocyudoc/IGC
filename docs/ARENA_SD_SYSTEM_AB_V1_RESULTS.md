# IGC — Comparación congelada A/B del System Prompt SD (2026-10-25)

**Veredicto:** `FOUR_VALID_JSON_NO_HOLDOUT`, **mejora mixta; no activar automáticamente v2**.

## Procedencia

- Manifiesto previo: [`data/diagnostics/arena_sd_system_ab_v1_manifest.json`](../data/diagnostics/arena_sd_system_ab_v1_manifest.json), manifiesto `sha256:274d7dc3993d2ae6b211adf4c1a8945f0a82de4283c1807e18a0267ef54a9d6c`. Incluye criterios, evidencia de construcción y orden de ejecución.
- [GitHub Actions 40179435584](https://github.com/yudocyudoc/IGC/actions/runs/40179435584), job `sd-system-ab-v1`, cuatro llamadas Cloudflare reales, cero reintentos, cinco pruebas de contrato correctas. [Artefacto original 12594355221](https://github.com/yudocyudoc/IGC/actions/runs/40179435584/artifacts/12594355221), `results.json`.
- El `user` fue byte-idéntico entre ambos brazos de cada mundo; `temperature=0`, `reasoning_effort=low`, `max_completion_tokens=4096`, mismo GLM-5.3 Flash.
- Orden congelado: WA/v2, WA/baseline, WB/baseline, WB/v2. El mundo sintético fue generado por el equipo y el compromiso sobre los parámetros se registró con hash; **no existe custodio externo ni ceguera independiente probada**. No se leyó ni puntuó ninguna reserva. Estas llamadas no son propuestas nativas S, ni constituyen resultados de G3 u OpenModelica.

## Resultados exactos del proveedor

| Caso | System | JSON/HTTP | Estructuras retenidas | Prompt tokens | Completion tokens | Total |
|---|---|---|---|---:|---:|---:|
| WA | v2 | válido / 200, stop | CS-01, CS-02 | 1080 | 852 | 1932 |
| WA | baseline | válido / 200, stop | CS-01, CS-02 | 562 | 453 | 1015 |
| WB | baseline | válido / 200, stop | **CS-02** | 590 | 594 | 1184 |
| WB | v2 | válido / 200, stop | CS-01, CS-02 | 1108 | 1263 | 2371 |
| **Total** | **baseline** | **2/2 válidas** | — | **1152** | **1047** | **2199** |
| **Total** | **v2** | **2/2 válidas** | — | **2188** | **2115** | **4303** |

La versión v2 utilizó **1.96×** los tokens de baseline. Ninguna versión descubrió estructuras fuera del catálogo. En WA ambas retuvieron dos candidatas; en WB divergen.

## Auditoría cualitativa según criterios congelados

1. **Conservación / dimensión:** v2 en WA y WB calculó correctamente áreas del pulso (`0.85 × 1.5 = 1.275`, `1.2 × 2 = 2.4` unidades). Baseline en WA habló de meseta próxima a «amplitud más crecimiento residual», confusión dimensional. **v2 mejor** en esta dimensión.
2. **Stock vs. flujo y perfil de entrada:** baseline en WB afirmó que una etapa con pulso «debería mostrar la pendiente máxima inmediatamente y decaer». Para un pulso **rectangular de duración finita**, el caudal entregado en una cola de primer orden con stock inicialmente vacío empieza en cero y aumenta durante la entrada; la salida acumulada puede mostrar curvatura sigmoidea. Su justificación de exclusión es por tanto **insuficiente**, aunque CS-02 resulte favorecida por un ajuste numérico. Baseline WB también escribió que CS-01 estaba «down-weighted, not eliminated» pero omitió su ID de la selección.
3. **Falsación física:** v2 en WB afirmó que dos etapas producirían un «measurable initial dead interval» y que una cola de dos etapas necesariamente tendría un hombro discernible. Una **cascada continua** de dos etapas de primer orden con parámetros positivos no presenta un intervalo de salida exactamente cero tras el inicio de un pulso; presenta una derivada temprana de orden superior y un retardo **aparente**, que puede ser inobservable con muestreo/noise. **Error de v2**. La propuesta de impulso ideal en WA v2 es más específica pero debe diferenciar impulso ideal de pulso finito en el experimento.
4. **Identificabilidad:** v2 mantuvo ambos candidatos sin afirmar causalidad; baseline WB discriminó, pero no justifica una falsación universal. Ninguno recibió parámetros, ecuaciones completas ni ruido instrumentado en el prompt; sólo etiquetas/etapas, observaciones y perfil de pulso. Por ello ambas decisiones son condicionales.
5. **Experimento siguiente:** ambas versiones propusieron un pulso más breve y muestreo temprano. v2 formuló con mayor detalle la comparación de forma, repeticiones y contraste de tasas, **pero su terminología de dead time debe corregirse**.

## Comprobación física *exploratoria*, NO preinscrita y NO puntuación sobre la reserva

Para revisar la plausibilidad de los argumentos, se ajustaron **después de ver las respuestas** las ecuaciones continuas de colas lineales en serie (stock inicial cero, salida = stock / `responseTime`; flujo sin saturación para las amplitudes de estos casos), al **pulso rectangular** visible, minimizando RMSE de los puntos de construcción. Se restringió `responseTime` al intervalo público de laboratorio [0.4,1.6] horas. No se usaron observaciones reservadas ni parámetros de la verdad oculta.

| Mundo | Mejor CS-01, RMSE | Mejor CS-02, RMSE | Observación |
|---|---:|---:|---|
| WA | **0.0185** | 0.0425 | CS-01 ajusta mejor bajo esta familia |
| WB | 0.0705 | **0.0186** | CS-02 ajusta mucho mejor bajo esta familia |

Esto **favorece CS-02 en WB dentro de esta familia parametrizada**, no convierte el argumento de la forma de S en falsación genérica ni prueba que GLM haya realizado dicho ajuste. Los resultados son *post hoc* y no forman parte de un criterio preinscrito para declarar ganador.

## Decisión

**No adoptar todavía el prompt v2 sin ajustes.** Tiene razonamiento más explícito sobre masa, retardos y unidades, pero produce aproximadamente el doble de tokens y al menos una afirmación física errónea. Tampoco hay evidencia con dos casos de que supere a D (enumeración + calibración). Se recomienda un v2.1 **más corto**, que:
- Distinga respuesta al **impulso ideal** frente a pulso rectangular y «retardo aparente» frente a «tiempo muerto exacto».
- Pida un contraste de **capacidad de ajuste** dentro de rangos admisibles cuando el contrato incluya ecuaciones/ruido, sin inferir un descarte a partir de etiquetas.
- Mantenga verificación dimensional de integral del pulso y tratamiento cuidadoso de observables acumulados.
- Mantenga salida JSON estable y prohíba inventar causalidad, eventos o parámetros.
- Se congele y evalúe en **nuevos** casos; no iterar el prompt sobre WA/WB para maximizar su acierto aparente.

**No se abrieron reservas, no se ejecutó el comparador D formal, no se construyó PredictionLock ni se realizaron simulaciones OpenModelica asociadas a estas cuatro respuestas.**
