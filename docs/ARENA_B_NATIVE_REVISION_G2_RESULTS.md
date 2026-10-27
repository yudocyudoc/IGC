# Arena B — Primera revisión REAL Buffalo + G2 OpenModelica

**Fecha:** 2026-10-25/26 · **Estado:** resultados técnicos auditables en PR #26; no certificación científica.

## Cadena de evidencia

1. Buffalo original `UB-IAD/sd-ai` SHA `5199f7b45f3a7ae4a773cb0dd8542940aabe9edc`.
2. Primera salida real Workers AI: [Actions 40255975864](https://github.com/yudocyudoc/IGC/actions/runs/40255975864), bytes nativos SHA256 `76391313d0fa96ec4704d44c2e5e3973e4c0ea21f6491bfd428c7171ec8c1864`. 15 variables, 18 relaciones.
3. Segunda iteración usando el **mismo motor Node original** y su `currentModel`, con diagnóstico G1 de primera versión y sin salidas D/M: [Actions 40259178852](https://github.com/yudocyudoc/IGC/actions/runs/40259178852). El paso live recibió HTTP 200 de Cloudflare, exactamente una llamada, cero reintentos, 15 variables, 19 relaciones. Artifact `12624126056`, `revision-live/native-output.json` bytes SHA256 `d7630830b4812c8880dc88c5f93f821707a75d22e0ecdf2cc1e9b5d8ec0889b9`.
4. Consumo del proveedor en iteración 1: 4,069 tokens prompt, 3,199 completion, 7,268 total; uso reportado por Cloudflare en su respuesta cruda, no costo monetario certificado.
5. Traducción independiente `scripts/arena_b_native_to_modelica.py` y OpenModelica real fijado en contenedor: [Actions 40260181965](https://github.com/yudocyudoc/IGC/actions/runs/40260181965), artifact `12624606460`. Compilación y simulación **SUCCESS** con Euler, 64 intervalos, horizonte 0–8 h; 66 filas en CSV.

## Qué mejoró la revisión de Buffalo

- Antes: `pulse shape = PULSE profile over time`, prosa no ejecutable. Después: `pulse shape = TIME` **con función gráfica**, puntos `(0,0),(0.001,1),(2,1),(2.001,0),(8,0)`. No interpretar el `TIME` aislado: Buffalo representa una tabla de lookup con TIME como **entrada**, y su salida es adimensional.
- Antes: `completions = completion_capacity * processing_signal`, unidades `(items/hour)*(items)`. Después: `completions = completion_capacity * capacity_utilization`, unidades compatibles bajo lo declarado. Variable `processing_signal` eliminada.
- Después: `capacity utilization from pressure` es una función gráfica con puntos `(0,0),(0.25,0.5),(0.5,0.85),(1,1),(4,1)`.
- El operador `//` es la división segura documentada por **Buffalo**, no una expresión inválida. El traductor lo representa condicionalmente: si denominador = 0, resultado = 0.
- Preflight limitado: primera versión 4 hallazgos G1 (error dimensional, prosa, dos símbolos no resueltos) + 1 obligación ADAPTER; segunda versión 0 hallazgos G1, pero 1 división segura y 2 lookups requieren traducción y revisión semántica. **0 hallazgos léxicos no implica G1 universal.**

## G0 condicional y G2 ejecutado

El traductor no usa catálogo molecular ni composición D, ni añade stocks o relaciones causales; toma variables, ecuaciones, puertos y tablas Buffalo.

**Supuestos todavía no verificados con el simulador nativo Buffalo:** interpolación lineal entre puntos, extrapolación constante por extremos, semántica numérica exacta de `//` y del `uniflow`. Son decisiones declaradas de G0 condicional, no equivalencia certificada. El solver ejecutó con esos supuestos. CSV sin no-finitos ni stocks negativos bajo esta corrida; G2 técnico PASS.

## Comparación descriptiva con construcción — NO holdout, NO causalidad

Observable: stock `delivered_work`, unidades items. Fuente visible `data/synthetic/arena_b_native_visible.json`.

| Hora | Observación | OpenModelica | Simulado - observado |
|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 |
| 1 | 0.350 | 0.3876059 | +0.0376059 |
| 2 | 1.100 | 0.9876059 | -0.1123941 |
| 4 | 2.500 | 2.1876059 | -0.3123941 |

RMSE descriptivo horas 1,2,4: **0.1929047 items**. Resultado t=8: `pending_work=0.0494358`, `delivered_work=3.3505642`. Los valores reproducidos vienen de CSV **OpenModelica real**, no del LLM ni de una curva dibujada.

No hay error instrumental declarado, incertidumbre paramétrica ni evaluación ciega. **No** presentar RMSE como G3 favorable ni como evidencia de mecanismo correcto.

## Riesgo estructural restante

La versión revisada tiene:
- `completion_capacity = nominal_capacity * capacity_utilization`
- `completions = completion_capacity * capacity_utilization`

Por sustitución, `completions = nominal_capacity * capacity_utilization²`. Puede ser una doble atenuación no explicitada en la explicación de Buffalo, que habla de una tasa limitada por capacidad; **hay que contrastar intención causal y ecuaciones**, no corregirlas desde el adaptador. Otra posible fuente de discrepancia es la tabla de utilización y su base de evidencia.

El primer objetivo de la Arena se cumplió parcialmente: **hipótesis B real → diagnóstico → revisión B real → simulación OpenModelica**, sin mezclar el generador con D o moléculas. ATMS completo, G0 exacto, G3 y pruebas de intervención/no-vistas siguen fuera de este incremento.

## Veredictos

| Nivel | Veredicto |
|---|---|
| Inferencia real Cloudflare y original Buffalo | PASS |
| currentModel y feedback exclusivamente B | PASS |
| G1 preflight acotado | Ningún error detectado en versión revisada; no certificación general |
| G0 nativo→Modelica | CONDITIONAL: lookups y `//` requieren cotejo nativo |
| G2 OpenModelica | PASS (versión revisada con supuestos declarados) |
| G3 ajuste con construcción | Solo comparación descriptiva, no adjudicación |
| ATMS memoria y comparación tres brazos | Pendientes |

**Restricción:** no retocar el modelo B para reducir el RMSE desde el traductor; cualquier nueva estructura o ecuación debe provenir de iteración explícita del propio Buffalo y registrarse como nueva versión.
