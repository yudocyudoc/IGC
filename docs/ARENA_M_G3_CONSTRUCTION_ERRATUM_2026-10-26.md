# Corrección de métricas G3 de construcción en M — revisión Astra, 2026-10-26

El [dictamen de Astra](https://github.com/yudocyudoc/IGC/pull/29) detectó que los informes de los brazos usaban distintas convenciones de RMSE y en algunos casos llamábamos indebidamente «G3 de holdout» a la reserva. El plan Arena v1.3 **define G3 como adecuación sobre observaciones de construcción**, y la evaluación reservada es otra etapa.

Esta corrección **no ejecuta un nuevo generador molecular ni cambia M1/M2**. Conserva los recibos y las trazas reales de OpenModelica y agrega métricas de construcción comparables en futuros reportes del verificador y comparador M:

- `rmse_all_observations_items` incluye los tiempos 0,1,2,4; divisor 4.
- `rmse_noninitial_observations_items` excluye t=0; divisor 3.
- `rmse_denominators` expone ambos divisores.
- `g3_construction_status = DESCRIPTIVE_ONLY_NO_INSTRUMENT_BOUND` (M1), y `DESCRIPTIVE_IN_SAMPLE_FEEDBACK_NO_INSTRUMENT_BOUND` (M2).
- `reserved_evaluation_status = NOT_RUN`, **separado** de G3.
- Se conservan claves históricas `rmse_items`, `g3_heldout` y `holdout_status` por compatibilidad de lectura con artefactos M1/M2 congelados; no cambian sus bytes, modelos, hashes ni resultados.

Si el punto inicial tiene residuo cero, el RMSE con los 4 puntos es \(\sqrt{3/4}\) veces el RMSE de los 3 tiempos positivos. El paso de 0.618639 (M1, divisor 3) a 0.173442 (M2, divisor 3) no constituye validación independiente. La comparación D/B/M debe usar la **misma convención de puntos, mismas unidades, el mismo instrumento/error asumido y condiciones de prueba comparables**; no basta con cambiar el denominador.

**Otros hallazgos de Astra que NO resuelve este PR:** M aún elige la topología más simple sin observar los datos; M2 usa una regla heurística escrita después de ver M1; D y M2 son dinámicamente equivalentes bajo el pulso actual; B debe recibir feedback físico de su simulación y D2 debe emitir/simular su revisión. Corresponden a nuevos ensayos, no a una edición de números históricos.
