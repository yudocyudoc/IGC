# Arena V0.1 · Integración D1/D2 y seis modelos revisados en OpenModelica

**Corte:** 2026-10-26. **Alcance:** importación por capacidad, no fusión indiscriminada de experimentos.  
**Base:** `main` después de PR #43 (D0 G0/G1 independiente).  
**Fuentes:** PR #23 (D1, puente D→ATMS, D2 de parámetros), PR #32 (corrección de G2 de los modelos revisados). Fuente de código exacta: branch `fix/arena-d2-revised-modelica-g2-20261026`, commit `cb0ad83534cdee74866c87b51318534a5b146024`.

## Qué se incorpora

Se traen **sin cambios algorítmicos** estos archivos desde los blobs originales:

| Archivo | Git blob SHA original |
|---|---|
| `scripts/arena_atms.py` | `fe649009e5b99243e07e987a97b903180a9058a1` |
| `scripts/arena_d_v1_screen.py` | `700ed6d10b3d094104ee5c74d1459736e1220f41` |
| `scripts/arena_d_atms_bridge.py` | `d2bc5eaacf4beee41cbe0707318b1c7bee47cf21` |
| `scripts/arena_d_v2_revision.py` | `ab3f98e87f49746371e7807a9d8e65bcc5089374` |
| `scripts/arena_d2_revised_g2.py` | `d9e83ba5170464b4a5b60ef73c388fdb8133a358` |
| `data/synthetic/arena_d_v1_screen_protocol.json` | `dcdcb660f2ec68ed2ca4b6109681e55cb120fe9e` |
| Cuatro pruebas D1/ATMS/D2/G2 | Ver blobs y CI de rama de integración; tres primeros originales `f6a721a7`, `38c49fd3`, `cba1dd3a`, G2 `4820e450` |

La memoria ATMS incluida es una **proyección local de la ruta D**, con pruebas sobre soportes y retractaciones. **No** demuestra aún el funcionamiento transversal de ATMS para D, B y M.

## Evidencia física y procedencia

La CI obtiene la entrega D2 original del run [#40248817463](https://github.com/yudocyudoc/IGC/actions/runs/40248817463), nombre `arena-d-v1-screen-modelica-evidence`. La función `read_parent` exige **cuatro hashes SHA-256 de archivos originales**, comprueba su cadena D0→D1→D2, identidad de la estructura, parámetros ajustados dentro del grid y **ningún mundo evaluador** en las propuestas del brazo.

El nuevo `arena_d2_revised_g2.py`:
1. Recupera los seis candidatos nativos D y sus parámetros revisados, sin sustituirlos por los del «mundo» de evaluación.
2. Emite seis `D2fit_*.mo` con ecuaciones D originales y parámetros ajustados por el brazo.
3. Ejecuta los seis realmente en **OpenModelica 1.27.1**, imagen fijada por SHA, solver DASSL.
4. Compara balances, no negatividad y paridad numérica con el integrador original RK4.
5. Contrasta las entregas con observaciones de **construcción** y la perturbación visible de D2; verifica una sola hipótesis soportada **condicionalmente** al error instrumental y la grilla de parámetros.

Evidencia original de origen físico histórico: [#40284851680](https://github.com/yudocyudoc/IGC/actions/runs/40284851680).

## Qué no se interpreta como prueba

- **G2 PASS** significa compilación/simulación y conservación en seis candidatos revisados, **no** que seis mecanismos se hayan validado causalmente.
- **G3 construcción** es descriptivo y sujeto a incertidumbre. D2 reusa una perturbación visible y **no posee holdout nuevo**.
- Un test local de ATMS no prueba memoria versionada de la Arena completa, ni aislamiento de otros brazos a nivel permisos.
- Los archivos de Actions tienen retención temporal. El pipeline reejecuta desde una fuente histórica en GitHub; **antes de un release estable debe depositarse el paquete original y sus hashes en un archivo duradero verificable**. Si el artefacto expira, el gate falla: no reconstruir una respuesta sintética a mano para hacerlo pasar.
- La fase V0.1 común requiere todavía M y B, una comparación común, ATMS transversal y gates de fidelidad/adecuación.

**Estado:** test físico de promoción pendiente de corrida en el HEAD de integración, no `v0.1.0` liberada. Clef no participa. Sin llamadas remotas de IA en la CI.
