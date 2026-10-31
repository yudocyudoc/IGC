# CAF-10 — Resultados ejecutados y adjudicación provisional de Claude/GLM

**Estado:** ensayo DES sintético determinista, no validación empírica ni estudio prospectivo independiente. **PR:** #122, apilado sobre #121. **Protocolo congelado antes del ejecutor/CI:** commit `c683d6cbdf7055b7f664b1c7fc64b7e4f0f4eea8`, `CAF10_PROTOCOLO_PRECOMPROMISO.md`. Reglas no modificadas después de ejecutar los mundos.

**Evidencia canónica:** [GitHub Actions #41250330932](https://github.com/yudocyudoc/IGC/actions/runs/41250330932), **6/6 tests PASS** y ejecución `CAF10_ENGINEERING_PASS_NO_SCIENTIFIC_PROMOTION`. [Descargar audit trail completo de 589 archivos](https://github.com/yudocyudoc/IGC/actions/runs/41250330932/artifacts/13061106429): plan, **585 decisiones previas a K2**, resultados con 585 evaluaciones y clases sobrevivientes, informe y manifiesto SHA256. **Head del PR evaluado:** `c7b4c8c3f29a21a7289d2dab3ac6766a541b64dc`; **SHA de checkout de merge sintético** registrado en JSON: `fac197c593e0c5b54659f698282a99b11c8aa55b`. No confundir los dos; el historial del PR incluye después documentación de resultados.

## Por cohorte, sin mezclar denominadores

**H: 168 cuellos únicos, históricamente examinados en #117.**

| Política | K2 elegidas | Correctos | Falsos únicos | Abstenciones | MODEL_GAP | Clase verdadera aún representada | Clases supervivientes medias | Costo ordinal total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Estricta original | 0 | 0 | 0 | 138 | 30 | **138/168** | 4.7143 | 168 |
| Claude: PAIRWISE | 138 | **25** | 0 | 98 | 45 | 123/168 | **2.381** | 954 |
| GLM: minimax | 138 | 5 | 0 | 119 | 44 | **124/168** | 2.75 | **834** |

**N: 24 dobles en cuadrícula nueva, construida y elegida por los investigadores.**

| Política | K2 | Correctos | Falsos únicos | Abstenciones | MODEL_GAP | Clase verdadera sobrevive | Media de clases |
|---|---:|---:|---:|---:|---:|---:|---:|
| Estricta | 0 | 0 | 0 | 18 | 6 | **18/24** | 4.5 |
| PAIRWISE | 18 | 0 | 0 | 15 | 9 | 15/24 | 2.25 |
| Minimax | 18 | 0 | 0 | 15 | 9 | 15/24 | 2.375 |

Ninguna de las tres políticas logra **ninguna** clase doble única correcta, incluso con el banco ampliado nominalmente incluyendo esas clases. Las brechas del banco ampliado en los nuevos dobles ocurren en las tres combinaciones de `cap=69`, `cap=83` desde K1, y en `cap=97` solo tras K2 de los dos brazos flexibles. **No son prueba de mecanismo oculto:** esas clases están representadas nominalmente; falla el ajuste de capacidad y observación a los cuatro puntos numéricos de entrenamiento, bajo ±1.

**S: 3 controles con cuarta etapa, fuera de catálogo; cobertura N/A.**

| Mundo | PAIRWISE (acción; veredicto) | Minimax (acción; veredicto) |
|---|---|---|
| `S_EXTRA_64` | prep_dispatch_15_t20; **FALSE_SINGLE_DIAGNOSIS** (entrega) | prep_queue_15_t20; ABSTAIN |
| `S_EXTRA_86` | prep_dispatch_15_t20; **FALSE_SINGLE_DIAGNOSIS** (entrega) | prep_queue_15_t20; ABSTAIN |
| `S_EXTRA_108` | prep_dispatch_18_t20; ABSTAIN | prep_dispatch_18_t20; ABSTAIN |

La estricta se abstuvo en los tres, sin medir. **Certificación con banco ampliado NO protege por sí sola contra topologías fuera del catálogo**. Que minimax haya evitado esos dos falsos diagnósticos en tres casos no demuestra una garantía de seguridad general.

## Comparación apareada del mecanismo de selección

- En H, **60/168** acciones cambian: PAIRWISE elige `prep_dispatch_15_t20` (costo 4) mientras minimax elige `prep_queue_15_t20` (costo 2). En 78 mundos ambos eligen `prep_dispatch_18_t20` (costo 7), y en 30 ninguno mide. **21/168** veredictos difieren: 20 correctos de PAIRWISE se vuelven abstenciones bajo minimax; un `MODEL_GAP` de PAIRWISE (`H_SINGLE_81_1`) se vuelve abstención de minimax. Sus dos acciones no difieren en las observaciones K0/K1.
- En N, **9/24** acciones cambian, pero 0/24 veredictos difieren, y en 3 mundos cambia solo el conjunto de clases sobrevivientes.
- En S, cambian dos acciones y dos veredictos, precisamente los falsos únicos anteriores.
- Minimax optimiza explícitamente el **peor número de clases entre todas las lecturas posibles de cada acción**, luego peor número de hipótesis y costo; PAIRWISE maximiza número de pares separados y luego costo. **Ninguno optimiza riesgo real, utilidad empresarial ni posterior bayesiano**.
- Las 168 configuraciones de un cuello de H son viejas y el resultado no es un holdout. Las 24 dobles N son nuevas respecto de los 11 casos anteriores, pero siguen siendo combinaciones diseñadas del mismo motor/axiomas.

## Primer diagnóstico metodológico

La cobertura de la clase verdadera en H fue **138/168 sin K2**, y bajó a 123–124/168 tras adquirir observaciones. No confundir menos hipótesis/clases con inferencia más correcta: el mismo filtrado `±1` puede excluir la clase real cuando el **banco solo contiene capacidades discretas** `60,75,90,105`, aunque el mundo real simulado tiene otra capacidad dentro de `55..110`. Esta tensión de **calibración/parametrización del banco** es más decisiva que escoger un score de K2 en varios regímenes.

Especialmente: H pierde representación con K1 en **65–71/h y 82–84/h** para las tres etapas (30 mundos). Más tarde, K2 puede eliminar la clase real en otros mundos. El modelo físico está parcialmente representado por clase, pero **no es un modelo robusto de parámetros continuos**.

**Lo que NO se desprende:**
- No hay prueba independiente de que PAIRWISE sea preferible o que minimax sea seguro.
- Un `MODEL_GAP` no es prueba de cuarta etapa; ocurre en mundos **dentro de las seis clases nominales**.
- Una clase única no es una certificación válida fuera de catálogo, como demuestran los sentinelas.
- Los costos ordinales no son pérdidas reales ni estimaciones de retorno.
- La minimización del peor número de clases no garantiza mejor precisión en datos sin probabilidades.

## Revisión adversativa solicitada a Claude/GLM

1. Verificar desde los **585 JSON** que la política original, PAIRWISE de #121 y la enumeración minimax no recibieron la configuración del mundo salvo en el lector físico/evaluador.
2. Auditar la enumeración de todos los vectores posibles (incluye bordes 0 y ±1) y la regla lexicográfica; el peor caso no asigna probabilidades.
3. Identificar por qué el banco discreto elimina hipótesis correctas por clase cuando capacidades son intermedias; distinguir **error de especificación**, cobertura de clase y tolerancia instrumental.
4. Formular alternativas que preserven la cobertura de clase sin producir falsos certificados: banco de capacidades continuas/discretización refinada, intervalo/calibración por parámetro, categoría `UNKNOWN`, abstención condicional, etc. **No seleccionar valores usando los 195 resultados** sin nuevo ensayo.
5. Separar explícitamente decisión de medir, conjunto de clases sobrevivientes, emisión de etiqueta única y decisión/intervención operativa.
6. Estudiar en fase aparte servicio estocástico, timestamps y resolución real: este ensayo es determinista y con sensores ideales.

**Gate final (inalterado):** `BLOCKED_SYNTHETIC_SAME_PHYSICS_NO_EXTERNAL_VALIDATION`. Mantener PR Draft, sin alterar D/M/Buffalo/ATMS.
