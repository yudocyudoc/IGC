# V0.1 · Promoción selectiva del generador determinista D

**Fecha:** 2026-10-26  
**Base:** `IGC/main` tras PR #42 (política de releases y fuentes).
**Origen exacto:** PR #23, branch `feature/arena-d-pure-stockflow-v01`, commit `ddd80e0cdbf4cf5af7a9d5cbd752ded04a32322d`.

## Qué se importa (sin modificar sus algoritmos)

| Ruta | Blob GitHub SHA original |
|---|---|
| `scripts/arena_d_v01.py` | `099dba3f995bae08310f80385384599d2b63518e` |
| `tests/test_arena_d_v01.py` | `77575f194f57ded588c25720e9496c0aaceb3970` |
| `data/synthetic/arena_d_v01_visible.json` | `f24ead387563733593ea6d8b0b3877b51c313676` |

Se conserva la lógica **D independiente** y el contrato común `scripts/arena_v0_contract.py` ya presente en main. Enumera hasta tres stocks en serie, con/sin un flujo de pérdida simple; emite seis estructuras bajo el presupuesto de ejemplo; registra entrega nativa, hashes y evento con procedencia. Sus ecuaciones Modelica se generan mediante el propio algoritmo D, **sin moléculas ni LLM**.

## Qué significa PASS aquí

- Datos visibles sometidos al contrato V0; rechazo de `gold`, `holdout` y resultados de otro brazo.
- Comprobación de conectividad/conservación por linter estructural y sintaxis de balances.
- Seis candidatos nominales de gramática acotada en el ejemplo, sin premiar un top-1.
- Archivos Modelica emitidos con `status=PROPOSED`, sin fingir simulación.
- Pruebas herméticas negativas sobre masa, frontera, mutación de entrada y datos ausentes.

**Esto es un PR de promoción D-G0/G1. No acredita G2/G3, ajuste o selección D2, loops complejos, identificación causal ni integración D+B+M.** Para integrar D2, preparar un **segundo PR** importando el corrector propio D y sus tests con los artefactos históricos atestados del PR #32. No mezclar en este incremento ajustes del mundo evaluador con el generador nativo.

## Próximas dependencias

- D2 G2 y auditoría de fidelidad desde #32.
- M: compositor y moléculas desde #27...#35, sin alterar parámetros del catálogo por el fallo M3-P.
- B: motor original Buffalo y adaptador propio, no al compositor M.
- ATMS: eventos de hipótesis/propuesta/diagnóstico/revisión desde ledger; no declarar soporte de retractación con el simple `trace_event`.
- Nueva ronda común de construcción, simulación real y evaluación con B0 conforme al plan rector v1.3.

**Estado release:** `v0.1.0` permanece `NOT_RELEASED`; este incremento D no es por sí solo motivo para publicar versión. PR experimental #23 no se cierra hasta verificar que su parte no importada está trazada en el inventario y se decida el destino de las pruebas adicionales.
