# CAF-01 · D · G2 nativo — representantes fijados (2026-10-29)

**Estado:** PR #84, preparación y CI únicamente. **Cero simulaciones OpenModelica nuevas consumidas.** No ejecutar hasta revisión de Astra.

## Origen inmutable y alcance

- Mundo de construcción DES en GitHub Actions: **40915090599** (reproducción del mundo sellado; 1 local anterior conocida, por separado).
- Cribado D ya ejecutado: **40974820126**, 18 RK4 CAF01 + 18 RK4 CAFN, **36/36 gastadas**.
- Artefacto D-CAF01 permitido: `caf01-d-rk4-CAF01-run-40974820126`, ID `12941329156`.
- SHA-256 del archivo extraído `D_RK4_SCREEN.json`: `e77dbbabc18370104f74c1ee88b86ec3a29d91a2cb3ec30b546a882f4a3675b3`.
- Archivo de evidencia CAF01 de construcción: `727501a3b5b33a63ab5a5d5f0f907d5431d0ee4f0d8b24ffd6f97758d59386fb`.

El runner rechaza cualquier alteración de esos bytes, exige 18 candidatos D originales y **recalcula las puntuaciones con las curvas ya publicadas**, sin una sola integración adicional. Comprueba que los representantes coinciden con la selección previa, uno por cada estructura D1/D2/D3. Regenera únicamente esos tres modelos con el renderizador D original y exige que cada SHA de fuente nativa coincida con el que fue registrado antes en el cribado. No reasigna parámetros si un modelo no supera G2.

## Futuro workflow manual

`.github/workflows/caf01-d-g2-native.yml`: manual sobre `main`, confirmación `RUN_CAF01_D_G2_THREE_ONCE`, primer despacho y primer intento. Descarga directamente el artefacto D original con `actions: read` y prepara los tres fuentes. Marca `CAF01_D_G2_OMC_INVOCATION_STARTED=1/3` antes de cada llamada a OMC. Cada modelo usa el pulso de construcción 72 pedidos/h durante 1/3 h; horizonte 2/3 h, 80 intervalos y CSV nativo. **Máximo tres simulaciones** (0/3 consumidas mientras el workflow no sea despachado).

La comprobación posterior exige que los stocks nativos `s1..sN`, `delivered` y `lost` cumplan conservación y no negatividad en la curva CSV, con residual máximo **≤0.008 pedidos**; además, la diferencia absoluta máxima entre entregas nativas y la serie RK4 previamente seleccionada debe ser **≤0.012 pedidos**. Son tolerancias numéricas de ingeniería, no incertidumbre instrumental, prueba de identidad causal ni ajuste al mundo oculto.

El output `D_G2_VERIFIED.json` solo aparece si las tres comprobaciones pasan. Ante cualquier fallo se retienen código Modelica, CSVs disponibles y logs de intentos, pero no se reinicia nada automáticamente. El número real gastado se reconcilia con los marcadores `OMC_INVOCATION_STARTED`; no se inventa un pase G2 por el estado del job. El artefacto no debe compartirse con los productores M ni B antes de su propia selección independiente.

## Validación previa realizada

- CI de PR: seis pruebas sintéticas/mocks (verificación física y paridad sobre CSV de juguete, selección irrevocable, hashes, no evaluación, rechazo de ramas y reintentos).
- CI de PR: descarga el **artefacto real de GitHub** y verifica que su fuente original reproduce los tres modelos nativos y sus SHA sin solver. Esto encontró y corrigió una discrepancia semántica entre `source_GitHub_workflow_run` (construcción DES 40915090599) y el run que almacena el JSON de D (RK4 40974820126). Ambas procedencias quedan ahora separadas explícitamente.
- No se invocó el OMC real, no se generaron nuevos RK4 ni se abrió la evaluación.

## Próxima acción

Revisión de Astra de PR #84 y posterior integración. La activación manual necesitará una autorización específica del presupuesto G2 (3 OpenModelica). **La aprobación de CI no es aprobación científica G2**; solo acredita integridad de preparación y pruebas sintéticas. Después corresponden M y Buffalo con contextos aislados, selección G3 y custodia G4 antes de abrir el holdout.
