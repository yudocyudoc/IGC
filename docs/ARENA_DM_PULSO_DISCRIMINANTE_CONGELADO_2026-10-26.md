# Arena — pulso discriminante D2/M2 congelados, sin ajuste

**Fecha:** 2026-10-26. **Estado:** experimento terminado, [CI OpenModelica #40395128012](https://github.com/yudocyudoc/IGC/actions/runs/40395128012) **SUCCESS**, [artefacto completo #12686660602](https://github.com/yudocyudoc/IGC/actions/runs/40395128012/artifacts/12686660602).

## Motivación (Astra R2)

D2 y M2 podían producir prácticamente la misma trayectoria bajo pulso **1.7 elementos/hora**, sin que las diferencias de capacidad se activaran. Astra propuso condiciones que separasen sus predicciones, sin usar las mismas observaciones para seleccionar el estímulo y adjudicar un ganador.

## Congelamiento y contrato

D2 corresponde a la hipótesis **única condicionalmente soportada** `D2fit_1b03f4d80336` (dos stocks, sin pérdida, capacidad **2 items/hour**, `responseTime=1 h`), proveniente exclusivamente de [#40284851680](https://github.com/yudocyudoc/IGC/actions/runs/40284851680). SHA256 exacto del archivo original Modelica `c0bec9482f045b9f5cfc652c08d72eb1f0492ecf31865073d530094d26de3750`.

M2 corresponde a la revisión de propia retroalimentación Short E1 `MolecularArenaM2_f250c7b99b2c` (dos colas materiales, `maxThroughput=20 items/hour`, `responseTime=1 h`), de [#40283319745](https://github.com/yudocyudoc/IGC/actions/runs/40283319745). SHA256 exacto del archivo original Modelica `8c7dfad2d9e3b4ef2619f4d9bb468bbab5dbd7c3cb3f30801b84f050df85f2f9`.

La única modificación del texto de ambos modelos es la **amplitud del estímulo público de 1.7 a 4 items/hour**, duración original **2 h**. Las demás líneas —ecuaciones de flujos, variables, stocks, componentes, tiempos y capacidades— son byte-reconstruibles por la operación inversa y se verifican en el script. No se ejecuta ningún nuevo LLM, ajuste de parámetros ni reconstrucción de mundos sintéticos.

Los dos motores usan OpenModelica real con DASSL 160 intervalos sobre 0–8 h y librerías originales. D2 mantiene **OpenModelica 1.27.1** y M2 **OpenModelica 1.26.5 + SystemDynamics 2.1.2 + MSL 4.0.0**; se registran esas diferencias de versión, no se presume identidad semántica numérica absoluta.

Antes de mirar resultados se eligió un pulso de 4/h porque supera la capacidad nominal D2=2 y está por debajo de M2=20. Diferencia discriminante preestablecida: máximo de |entregas M−D| en t=2,4,6,8 superior a **0.05 elementos**.

## Resultado real

| Tiempo (h) | Entregado D2 | Entregado M2 | Diferencia M2 − D2 |
|---:|---:|---:|---:|
| 0 | 0.000000 | 0.000000 | 0.000000 |
| 1 | 0.406273 | 0.414553 | +0.008280 |
| 2 | 1.761523 | 2.165365 | +0.403841 |
| 4 | 5.357635 | 6.274211 | **+0.916576** |
| 6 | 7.371724 | 7.639745 | +0.268021 |
| 8 | 7.878341 | 7.934098 | +0.055758 |

**La separación máxima es 0.916576 elementos**, lo que supera ampliamente el umbral predeclarado. Los dos modelos comparten un ingreso integrado de **8 elementos** (4/h durante 2 horas) y conservaron masa en todas las muestras verificadas (D2 residuo máximo `1.61e-11`; M2 `1.60e-11` elementos). En t=1 las curvas son casi iguales; la diferencia aparece cuando la saturación de D2 comienza a restringir el flujo.

## Límites de interpretación

Esta prueba distingue **predicciones de dos configuraciones congeladas**. No valida cuál corresponde a una cafetería real: **no se dispone de resultados observados independientes a este pulso**. No es un holdout predictivo con resultado conocido, no compara de forma justa cada método en todo su espacio de búsqueda, ni identifica estructura causal auténtica. En una cafetería habría que registrar pedidos, entregas, trabajo acumulado y disponibilidad efectiva de capacidad bajo cambios comparables para adjudicar mecanismos.

La experiencia es relevante porque muestra por qué el pulso previo no discriminaba la saturación. Si los modelos reciben datos de otra carga, un revisor puede pedir esa condición concreta antes de escoger entre hipótesis. **No seleccionar el ganador por plausibilidad o RMSE de construcción**.

## Reproducción

Código: `scripts/arena_dm_frozen_pulse.py emit/verify`; CI: `.github/workflows/arena-dm-frozen-pulse.yml`; evidencia: `manifest.json`, ambos `.mo`, CSV y `comparison.json`. Solo descargan artefactos de origen firmados con SHA; ninguna rama D o M necesita intercambiar con la otra durante su inferencia.
