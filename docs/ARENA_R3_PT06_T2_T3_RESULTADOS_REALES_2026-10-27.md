# IGC · R3 PT-06 STR-03 — Resultados físicos T2/T3

**2026-10-27.** Experimento real: [Actions #40582633807](https://github.com/yudocyudoc/IGC/actions/runs/40582633807). Auditoría sin simulación adicional: [#40582958825](https://github.com/yudocyudoc/IGC/actions/runs/40582958825). Protocolo anterior: PR #64, SHA256 `50cd8313a1a41cfca43391e105948c929122599b04ae70a375e255cd026b6064`.

**Alcance consumido:** 2 simulaciones generadoras E1 con OpenModelica DASSL (T2 hasta 0.15 h, T3 hasta 3 h). **0 nuevas simulaciones candidatas, 0 llamadas IA, 0 reintentos**. Se reutilizaron y verificaron físicamente los 27 CSV originales de R3-T1, manifest `d33cc4ca8c253226ff50efa6c47e40b9b8c32d0436f370907db2579c9dc0fde5`. Se conservaron la grilla C00/C01/C02 × 9 parámetros, el pulso 1.7 items/h durante t=0–2, el umbral RMSE 0.020 y M3 original (margen 0.035).

## T2 — ventana de observación temprana

Mundo C01 nominal, mediciones solo en t=0, 0.05, 0.10, 0.15 h; ruido nulo. Entregas acumuladas (items): `[0, 0.00000105725748653, 0.0000161523873544, 0.0000781499429920]`.

| Estructura | Mejor candidato | RMSE (items) |
|---|---|---:|
| C00 | C00P08 | 0.000424456706 |
| C01 | C01P04 | **0** |
| C02 | C02P00 | 0.000037202539 |

- **M3 congelado:** `ABSTAIN` (el margen no permite seleccionar).
- **R3:** `AMBIGUOUS_MULTIPLE_COMPATIBLE_STRUCTURES`; compatibles **C00, C01 y C02**.
- **G2 material del generador:** residuo máximo 3.0531133×10⁻¹⁶ items.

Se observó **ambigüedad bajo una ventana intencionalmente escasa**, no equivalencia global de las tres estructuras. C01 es el generador y tiene ajuste exacto, pero otras dos estructuras también satisfacen el criterio predeclarado.

## T3 — incompatibilidad con la grilla

Mundo C02 con `responseTime=4.0 h` para preparación, despacho y tránsito, permitido por el catálogo E1 pero fuera de la grilla de 27. Mediciones t=0,1,2,3 h con ruido predeclarado `[0,+0.002,-0.003,+0.004]` items y truncamiento de observaciones negativas a cero: `[0,0.002046893454,0,0.012183923699]` items.

| Estructura | Mejor candidato | RMSE (items) |
|---|---|---:|
| C00 | C00P08 | 1.074799014 |
| C01 | C01P08 | 0.433916770 |
| C02 | C02P08 | **0.143833612** |

- **M3 congelado:** `ABSTAIN`.
- **R3:** `ABSTAIN_ADMISSIBLE_GRID_HAS_NO_COMPATIBLE_STRUCTURE`; **ninguna** estructura compatible.
- **G2 material del generador:** residuo máximo 6.8789419×10⁻¹² items.

C02 es la estructura generadora y tiene el menor RMSE, pero **no** cumple 0.020. Esto refuta la adecuación de la grilla a este caso, **no** la capacidad del catálogo E1 completo.

## Conclusiones y límites

La auditoría posterior reconstruyó las dos decisiones desde los CSV originales, sin llamadas de solver. El selector solo recibió cuatro observaciones de construcción por caso; la estructura verdadera se reveló después, para adjudicación. La separación es procedimental, no un holdout externo.

Tras T1 (ambos abstienen), T2 (tres compatibles) y T3 (ninguna compatible), **STR-03 muestra que la salida del sistema discrimina ambigüedad e incompatibilidad finita sin forzar selección**. No demuestra identificación causal, ventaja general frente a M3, ni predicción R4. No ajustar estos casos ex post ni adelantar PT-07, REF, Clef o Clairic. Siguiente operación: consolidación interna de PT-06 y memoria de estas decisiones.
