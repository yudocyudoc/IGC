# Buffalo native: primera auditoría G1 sobre respuesta REAL (sin reparaciones)

**Fuente inmutable:** GitHub Actions [40255975864](https://github.com/yudocyudoc/IGC/actions/runs/40255975864), artifact `12622810831`, ruta `buffalo-cf-virtual-live/native-output.json`. SHA256 de bytes ZIP extraídos: `76391313d0fa96ec4704d44c2e5e3973e4c0ea21f6491bfd428c7171ec8c1864`. Upstream Buffalo `5199f7b`; Cloudflare `@cf/zai-org/glm-5.3-flash`. Única llamada real en ese ensayo; este diagnóstico **no** repite inferencia.

## Estructura recibida

`native-output.json` tiene `supportingInfo` y `model`. El objeto `model` tiene `relationships`, `variables`, `modules`, `specs`; son **15 variables** (2 stocks, 2 flows, 11 auxiliares), **18 relaciones** y specs `startTime=0`, `stopTime=8`, `dt=0.125`, `timeUnits=hour`, `integrationMethod=Euler`.

- `pending work`: stock inicial 0 items; inflow `arrivals`, outflow `completions`.
- `delivered work`: stock inicial 0 items; inflow `completions`.
- `arrivals = input_pulse`, `completions = completion_capacity * processing_signal`.

## Hallazgos bloqueantes o por resolver

1. **`pulse shape = PULSE profile over time`**: es prosa, no expresión cuantitativa. No sustituir por una función PULSE arbitraria: la forma, ventanas y semántica no están definidas por la salida. `NON_EXECUTABLE_EQUATION`.
2. **`normalized backlog = pending_work // processing_signal`**: CORRECCIÓN DE AUDITORÍA: Buffalo **sí define `//` como división segura que devuelve cero si el denominador es cero** (QuantitativeEngineBrain.js, apartado STEP 4). No es un defecto del modelo por sí mismo. El adaptador Modelica debe preservar exactamente esa semántica en vez de interpretarlo como comentario o división entera. Estado `ZERO_SAFE_DIVISION_REQUIRES_ADAPTER`, exclusivamente limitación de traducción.
3. **`completions`: unidades declaradas `items per hour` y fórmula `completion_capacity * processing_signal`. `completion_capacity` también está en `items per hour`, `processing_signal` en `items`; su producto produce `items²/hour`, incompatible con lo declarado. `DIMENSIONAL_MISMATCH`.
4. **`backlog pressure = normalized_backlog`** y dependencia `nominal capacity → backlog pressure` en la lista de relaciones aunque la ecuación no utiliza `nominal_capacity`: la relación es una afirmación causal gráfica no representada directamente por esa ecuación. `RELATIONSHIP_EQUATION_MISMATCH_CANDIDATE`; no prueba automáticamente falsedad causal.
5. **Fidelidad de formato:** nombres nativos con espacios (por ejemplo `pending work`) y referencias en fórmulas con underscores (`pending_work`). Un traductor puede mapearlos conservando identidad y dejando huella explícita; no confundir el problema de identificadores con modificación de estructura.
6. **Alcance de traductor del PR #24:** su `validate_model` actual exige exactamente `variables, relationships, specs` y solo admite ciertos campos nativos; no admite directamente `modules` ni todos los metadatos de variables, ni `integrationMethod`. El modelo real necesita un adaptador de *sobre* y cobertura del formato nativo comprobada, **no** un recorte silencioso de propiedades.

## Veredicto provisional

- Transporte OpenRouter virtual + inferencia real + procesamiento NodeJS original: **PASS** según recibo y workflow previo.
- `G0` fidelidad de Buffalo→Modelica: **PENDIENTE** (no hay traducción de este modelo).
- `G1` ecuaciones/unidades: **FAIL/PARTIAL** para el artefacto tal como llegó, por #1 y #3 (más revisión de consistencia); #2 es una limitación de nuestro adaptador, no un fallo Buffalo.
- `G2` OpenModelica de esta hipótesis: **NOT_RUN**.
- `G3` adecuación empírica: **NOT_RUN**.

**Corrección explícita:** La clasificación anterior de `//` como operador ambiguo fue incorrecta para el lenguaje documentado de Buffalo. Se conserva el hallazgo original en la historia del PR, pero se sustituye su interpretación.\n\n**Ruta correcta:** conservar este modelo inalterado y entregar al propio motor Buffalo un diagnóstico delimitado, verificando cómo usa `currentModel`. Nunca corregir ecuaciones con D ni con el catálogo molecular, y no presentar una revisión orientada por diagnóstico como predicción ciega nueva.

**Diferencia entre informe y automatización:** este examen del artefacto es manual; el preflight Node incluido en este PR aún es léxico, no prueba dimensional formal ni auditoría completa de coherencia causal. No atribuirle automáticamente todos los hallazgos anteriores.
