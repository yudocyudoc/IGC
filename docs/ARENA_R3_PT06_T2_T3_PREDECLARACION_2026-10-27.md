# R3 PT-06: predeclaración T2/T3 (2026-10-27)

**Estado: PREPARADO; NO SIMULADO.** Continúa el plan y la hoja de ruta v2.0, PT-06/STR-03. El resultado negativo de R3-T1 permanece intacto.

## Invariantes
C00/C01/C02, 27 candidatos y parámetros {0.25, 0.50, 1.00} h; umbral RMSE 0.020 items; M3 original con margen 0.035. Misma fuente rectangular 1.7 items/h durante t=0–2 y mismos comprobadores físicos E1. No se amplía grilla, arquitectura ni bibliotecas. Los 27 CSV de [R3-T1](https://github.com/yudocyudoc/IGC/actions/runs/40578550337) se pueden reutilizar **solo después** de autenticarlos y verificar G2; su manifiesto tiene hash `d33cc4ca8c253226ff50efa6c47e40b9b8c32d0436f370907db2579c9dc0fde5`.

## Casos independientes, previstos antes del solver

| | T2 — Observabilidad temprana | T3 — Incompatibilidad finita |
|---|---|---|
| Hipótesis, no resultado | Dos o más estructuras compatibles | Ninguna estructura compatible |
| Mundo generador | C01, parámetros E1 nominales | C02, responseTime 4.0 h en preparación, despacho y tránsito |
| Tiempos publicados (h) | 0, 0.05, 0.10, 0.15 | 0, 1, 2, 3 |
| Ruido (items) | 0, 0, 0, 0 | 0, +0.002, −0.003, +0.004 |
| Ventana máxima del mundo | t=0–0.15 | t=0–3 |

T2 deliberadamente reduce la información temporal; incluso si aparece ambigüedad, será un **control negativo de observabilidad**, no prueba de equivalencia estructural global. T3 genera una dinámica permitida por el catálogo E1 (0.1–5 h) pero fuera de la grilla de búsqueda; un posible rechazo solo significa incompatibilidad **con esa grilla**, no con E1 en general. Resultados distintos de las hipótesis también se conservarán.

## Presupuesto y frontera

**Este PR solo genera modelos, protocolo, programa de simulación y pruebas offline.** No produce mediciones ni consume solver. Próximo presupuesto por autorizar: **dos simulaciones de mundos, cero simulaciones de candidatos, cero llamadas IA**. El evaluador usará los 27 CSV autenticados, calculará mínimos por estructura, reportará conjunto compatible / único condicional / abstención, preservará M3 congelado y no recibirá topologías verdaderas ni puntos futuros del generador. La separación de verdad es procedimental, no ceguera criptográfica. No se inicia R4, REF, Clef ni Clairic.

**Implementación:** `scripts/arena_r3_pt06_t23_preregister.py`, `arena_r3_pt06_t23_worlds.py`, `arena_r3_pt06_t23_extract.py` y `arena_r3_pt06_t23_evaluate.py`. Los mundos y su procedencia quedan en archivos separados del contrato de selección.
