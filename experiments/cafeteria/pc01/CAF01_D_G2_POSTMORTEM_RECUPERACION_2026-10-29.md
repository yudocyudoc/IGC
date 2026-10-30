# CAF-01 — D G2 · Recuperación de la corrida fallida sin repetir D1

**Fecha:** 2026-10-29. **Estado:** propuesta de reparación técnica, no autorización autónoma para nuevas simulaciones.

## Diagnóstico contrastado con el artefacto real

Run original [40982542200](https://github.com/yudocyudoc/IGC/actions/runs/40982542200), rama `main`, intento 1, commit `eba64093`, resultado global `failure`. Artefacto de GitHub ID `12944887907`, SHA-256 del ZIP `d5a2b7d624526306ee045f15683a3d76684a89e665fe0224b41548367583f0bd`.

- La preparación del padre D y las tres fuentes nativas tuvo éxito.
- **D1 sí ejecutó OMC**: `D_G2_1.attempt=INVOCATION_STARTED`, `D_G2_1.exit_code=0`; el log nativo confirma que terminó la simulación. CSV nativo `D_G2_1_res.csv` SHA-256 `85e19d1523d841f370d92dbea9b48bc06e63ad6d4d7d3a8d30b913c4fa001ca3`.
- El modelo generó `D_G2_1.log` con permisos de root. El paso posterior `tee -a D_G2_1.log` devolvió `Permission denied`; `set -euo pipefail` detuvo el bucle.
- **D2 y D3 nunca fueron invocados**: no hay `*.attempt`, `*.exit_code` ni CSV nativo para ellos.
- El verificador original guardó `NO_NATIVE_G2_PASSES` (0/3), que es correcto como **resultado del runner fallido**, pero no evalúa la conservación/paridad de D1 porque un problema operativo le impidió procesar correctamente su log. El registro original se mantiene histórico e inalterado.
- Inspección independiente del CSV D1: 84 filas; residual físico máximo **1.4807710613240488e-11** pedidos frente al umbral `0.008`; paridad con RK4 máximo **5.432762932855439e-07** frente a `0.012`. Estos cálculos manuales no sustituyen un recibo suplementario verificable.

## Reparación y presupuestos

**Paso A (post-only, cero solvers):** `caf01_d_g2_postonly_recovery.py` lee exclusivamente el artefacto fallido, valida los SHA de los bytes originales y la identidad del padre, comprueba D1 invocado correctamente y ausencia de D2/D3. Copia y preserva las declaraciones de fallos históricos en `historical_receipts_do_not_overwrite/`. Llama a la función de verificación física nativa **sin solver** sobre los CSV existentes. Publica un expediente suplementario `D_G2_POSTONLY_RECOVERY.json` con D1 PASS, D2/D3 no ejecutados. Workflow PR `caf01-d-g2-postonly.yml` automáticamente verifica el artefacto real desde GitHub; no consume presupuesto científico.

**Paso B (manual, sometido a dictamen Astra):** `caf01-d-g2-remainder.yml` descarga el padre D original y el artefacto fallido, verifica todos los SHA conocidos, reproduce los tres modelos nativos sin solver, incorpora D1 CSV/log/marcador/código de salida del run anterior y ejecuta **solo D2 y D3** (dos invocaciones nuevas como máximo). Para cada uno conserva marca previa, código de salida y logs de consola en `D_G2_N.console.txt` (NO coincide con el `D_G2_N.log` que escribe OMC). Evita el conflicto de permisos. Tras la ejecución verifica los tres representantes por separado, conserva recibos PASS/FAIL y ledger entre runs, incluso ante fallo parcial. No existe automatismo de reintento ni sustitución.

| Recurso | Ya consumido | Recuperación máxima | Total máximo |
|---|---:|---:|---:|
| D RK4 CAF01+CAFN | 36 | 0 | 36 |
| D OpenModelica construcción | **1 (D1)** | **2 (D2,D3)** | **3** |
| DES evaluación | 0 | 0 | 0 |
| Buffalo / M | 0 | 0 | 0 |

El workflow original `caf01-d-g2-native.yml` **NO DEBE** reintentarse ni habilitarse con modificación de su contador para repetir D1. La nueva recuperación debe tener primer dispatch e intento propios, tras dictamen. Se solicita revisión focalizada de Astra de la recuperación histórica de D1 y la frontera de los dos intentos restantes.

No equivale a abrir el holdout ni convierte esta incidencia de permisos en fallo científico del candidato D1.