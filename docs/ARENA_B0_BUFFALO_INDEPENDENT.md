# Arena B0 — SD-AI (Universidad de Buffalo) como segundo brazo independiente

**Fecha:** 2026-10-25 · **Estado:** fase de integración, PR aislado de `main`. El brazo D permanece en su propio [PR #23](https://github.com/yudocyudoc/IGC/pull/23), sin añadir más funciones.

## Propósito y frontera

No se pretende que ningún brazo explique por sí solo el sistema. **D, B y M deben generar explicaciones rivales o complementarias con metodologías independientes**, conservar sus incertidumbres y someter sus consecuencias a la misma verificación en OpenModelica. Una deliberación posterior **podrá confrontar** sus resultados, sin permitir que un brazo corrija otro antes de su entrega. Clef sigue reservado para una cuarta etapa.

**B usa la metodología cuantitativa de SD-AI de la Universidad de Buffalo**, documentada en [UB-IAD/sd-ai](https://github.com/UB-IAD/sd-ai), commit `5199f7b45f3a7ae4a773cb0dd8542940aabe9edc` (14 octubre de 2026). El upstream publica dos motores separados: `qualitative` (CLD) y `quantitative` (SFD). Este incremento integra el **proceso cuantitativo** (identificación de variables, relaciones causales, stocks/flows, ecuaciones, verificación y errores de formulación), sin afirmar que el motor cualitativo ya esté conectado.

### Qué se recuperó sin alterar

- `data/buffalo-sdai/quantitative_system_scalar.txt` contiene secciones **literales** de `QuantitativeEngineBrain.js` bajo licencia MIT, con aviso de procedencia en `data/buffalo-sdai/UPSTREAM.md` y licencia original en `data/buffalo-sdai/LICENSE`.
- Es equivalente al ensamblado `generateSystemPrompt(false, false, false, false)`: versión profesional sin arrays/módulos/subtipos. No es una copia íntegra del motor NodeJS ni una afirmación de paridad con todos los proveedores de LLM del upstream.
- La solicitud se produce con `make_request(visible)`, con pregunta y evidencia visibles idénticas en contenido al contrato de Arena; `currentModel` vacío para la iteración inicial; **sin** soluciones generadoras ocultas, propuestas D, moléculas ni información de otros brazos.

### Contrato de entrada y salida

`scripts/arena_b_sdai_v0.py` admite `sd-json` original de Buffalo `{variables,relationships,specs}`, con `stock`, `flow`, `variable`, sus ecuaciones y polaridades. El modelo se almacena **sin modificar** antes de traducirlo a Modelica, con hashes y un evento de hipótesis del brazo B.

El adaptador actual es deliberadamente parcial: acepta variables escalares, expresiones aritméticas, `MIN`, `MAX`, `ABS`, `TIME` y conexiones materiales tipadas. **Rechaza** arrays, módulos, lookups, subtipos, funciones desconocidas, fórmulas faltantes, variables implícitas, duplicaciones materiales y mezclas de unidades incompatibles. No completa ecuaciones omitidas ni adivina relaciones. Los modelos fuera del subconjunto son `UNSUPPORTED_BY_ADAPTER`, **no** «errores científicos de Buffalo».

### Pruebas y límites

- `data/synthetic/arena_b_v0_handwritten_sdjson.json` es explícitamente **un modelo SFD de prueba escrito por nosotros**, NO salida de SD-AI ni prueba de recuperación de estructuras.
- La CI valida preparación de solicitud, sintaxis, ausencia de contaminación cruzada, rechazo de semánticas peligrosas y fidelidad de la traducción; después compila/simula **ese ejemplo** en el mismo OpenModelica fijado utilizado para D. Compara balances de materia y no negatividad de stocks.
- La entrada sintética incluye un pulso que termina a las 2 horas; el ejemplo escrito a mano usa una **llegada constante** durante las dos horas del smoke test. Por tanto, su éxito de compilación/balance **no** demuestra ajuste a las observaciones completas de 4 horas ni validez de la estructura. **G3 no probado.**
- El campo `origin` solo documenta la procedencia declarada. Cambiarlo a `UPSTREAM_PROVIDER_OUTPUT` no autentica mágicamente un modelo. La conexión con el proveedor real debe preservar un registro verificable de la solicitud y respuesta, configuración, costos, y ausencia de `gold`.

## Siguiente incremento

**B1: una generación real con el proceso de Buffalo**, mediante un proveedor elegido, guardando la respuesta bruta, token usage e identidad de modelo. Ningún candidato será sustituido por la fixture si la respuesta real falla. Después, traducir los modelos que estén dentro del subconjunto soportado y simularlos. Más adelante adaptar el motor cualitativo original si la comparación indica que agrega una perspectiva distinta; no usar técnicas moleculares para mejorar B.

**La meta no es que B converja a D. La meta es contar con una explicación independiente, simulable o claramente declarada no simulable, para una deliberación posterior.**
