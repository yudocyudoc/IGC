# IGC · Arena R3 / PT-06 — predeclaración del primer caso de estructura frente a parámetros

**Fecha:** 2026-10-27. **Estado:** PREFLIGHT / PR #62. **Fuente operativa:** `ARENA_IGC_ATMS_PLAN_IMPLEMENTACION_V2_0_2026-10-27.md`, PT-06 y STR-01/02/03; `ARENA_IGC_HOJA_DE_RUTA_V2_0_2026-10-27.md`, R3.

## 1. Pregunta que prueba R3 (no R4)

**¿Cuándo el fracaso del selector M3 fijo refleja parámetros nominales insuficientes en una estructura representable, y cuándo persiste ambigüedad estructural o incompatibilidad del repertorio ensayado?**

R2 quedó cerrado en PT-05: D conservó seis alternativas, M3 mantuvo ABSTAIN y Buffalo generó una segunda estructura ejecutable condicionalmente, con un estímulo diferente al solicitado. **No se reutiliza su RMSE para ordenar métodos ni se corrige el pulso Buffalo.** Este paquete aborda la siguiente limitación identificada por **M3-P**; no modifica el compositor, las moléculas, D, Buffalo, ATMS, ni la política histórica M3.

## 2. Métodos: referencia y variante distinguibles

- **M3 fijo:** código original `scripts/arena_m3_select.py`; solo C00/C01/C02 con parámetros E1 nominales, RMSE de los 4 tiempos, umbral `0.020 items` y margen `0.035 items`. Su política no se modifica, incluso si vuelve a abstenerse.
- **Nueva variante R3:** `scripts/arena_r3_pt06_parametric.py`; mismo repertorio **material** C00 (2 colas), C01 (3), C02 (4), sin el filtro informativo no identificable desde `deliveredTotal`. Usa el compositor original E1 para construir una **grilla finita** sin introducir una nueva gramática ni derivadas manuales.
- **Parámetros libres del primer caso:** `responseTime` de **preparación** y **despacho**. Cada uno toma `{0.25, 0.50, 1.00}` horas. Nueve parejas por topología: 3 × 9 = **27 candidatas**. Son valores de diseño definidos por adelantado, dentro de los límites del catálogo molecular original (0.1–5 h), **no extraídos de la verdad de M3-P**.
- **Congelado en R3-01:** `responseTime` de tránsito `1.6 h` cuando haya tránsito, `maxThroughput`, conexiones, unidades y la fuente rectangular `1.7 items/h` durante `0–2 h`. El espacio de búsqueda no cubre toda la familia de tiempos posibles: un fallo de esta grilla no demuestra una limitación absoluta del compositor.
- **Simulador futuro:** mismo backend E1 original, referencia M3 con OpenModelica DASSL, 0–6 h, 120 intervalos para las candidatas. No se cambia la física molecular.
- **Política nueva:** agrupar por topología, minimizar RMSE de construcción dentro de cada grilla y declarar **el conjunto** de estructuras cuya mejor configuración tenga RMSE ≤ `0.020`. Si está vacío, abstenerse; si incluye varias, conservarlas como conjunto ambiguo; si incluye una, marcarla **única condicional dentro de la grilla**, nunca estructura causal identificada. El umbral se conserva solo como política operativa, **no es una cota instrumental**.

El código separado `scripts/arena_r3_pt06_evaluate.py` acepta solo observaciones de construcción y CSV efectivamente verificados por el comprobador molecular G2 original. Se rechazan rutas/campos de verdad, observaciones temporales reservadas, discrepancias de Modelica, CSV faltantes y balances materiales inválidos. Los tres representantes nominales ya forman parte de las 27 candidatas, por lo que no se oculta una nueva ejecución de referencia.

## 3. Primer caso prospectivo R3-T1 (STR-02)

Caso sintético representable por **C00**, dentro del repertorio E1 original, con tiempos de respuesta de preparación `0.75 h` y despacho `0.30 h`; ambos difieren de los `0.50 h` del M3 fijo. Son valores válidos del catálogo, **distintos de los seis mundos históricos P01–P06** y no coinciden exactamente con la grilla. Esto prueba la capacidad *acotada* de aproximación frente a parámetros no nominales; no obliga a que pase el umbral.

El estímulo será el pulso rectangular E1 ya conocido. `deliveredTotal` en t=`0,1,2,3`; ruido sintético determinista declarado `[0,+0.002,-0.003,+0.004]` items, como en M3, sin fingir error instrumental medido. El archivo de blueprint de investigación se guarda separado de los datos que recibiría el selector. Como el generador es sintético y su código será accesible, **no se declarará un holdout independiente ni ceguera técnica absoluta**.

**Se generó offline el código Modelica del mundo R3-T1** a partir del compositor E1 original, pero **no se ha ejecutado ninguna simulación de ese mundo**, ni se han obtenido sus observaciones. No existe una conclusión empírica STR-02.

## 4. Casos siguientes previstos, no fabricados

- **STR-01:** sensibilidad de decisión ante observaciones diferentes con identidad de caso estable, usando los resultados históricos M3 únicamente como antecedentes, no sustituyendo el ensayo nuevo.
- **STR-03 / ambigüedad:** diseñar antes de generar el mundo un escenario en que varias configuraciones y topologías puedan ser compatibles dentro de un criterio de error declarado; salida válida conjunto, nunca ganador forzado.
- **Incompatibilidad:** generar una condición que ninguna configuración **admitida por la grilla** explique. Concluir `incompatible con las 27 configuraciones probadas`, no fuera de todo modelo físicamente posible.

No se ha predeclarado aún el estímulo/ruido del caso ambiguo ni del incompatible; quedan como tareas específicas que se deben congelar **antes de ejecutarlos**, no como resultados inventados. Los mundos M3-P constituyen antecedentes de desarrollo y no medirán la generalización de R3.

## 5. Presupuesto y compuerta

| Operación | Presupuesto de diseño | ¿Ejecutada en este PR? |
|---|---:|---|
| Generar fórmulas desde E1, sin OpenModelica | 27 candidatas + 1 fuente sintética | Sí (offline) |
| Simular las 27 configuraciones candidatas | Máximo 27 llamadas OpenModelica para **un** caso | **No** |
| Simular un mundo R3-T1 separado | 1 simulación adicional, si se autoriza | **No** |
| Leer y evaluar los 27 CSV G2 | 27 análisis sin solver | **No; faltan CSV** |
| Generar casos adicionales | Requiere presupuestos separados | **No** |
| Inferencias de IA/proveedor | 0 | **0** |
| Predicción R4, holdout nuevo | Fuera de PT-06 | **No** |

**27 es la cota orientativa del plan, no autorización para gastar 27 evaluaciones.** El costo físico del primer caso completo sería al menos 28 simulaciones distintas (27 propuestas + 1 generador), más cualquier comprobación técnica expresamente contabilizada. No se hará una corrida hasta fijar esa autorización y el protocolo final de generación, con presupuesto total visible.

## 6. Prueba de aceptación de este avance

[Workflow R3 PT-06](https://github.com/yudocyudoc/IGC/actions/runs/40573560841) (ejecución inicial): construyó manifest y Modelica desde el repositorio sin modificar archivos upstream, verificó unicidad, límites y clases, ejecutó casos **unitarios sintéticos** de conjunto compatible/abstención, rechazó información de verdad en el contrato y devolvió `PREFLIGHT_ONLY_NOT_SIMULATED`. **Es una prueba de diseño e integración, no un STR-02 empírico.**

## 7. Próximo avance exacto en PT-06

Después de comprobar el preflight en CI, congelar el productor sintético R3-T1 en un módulo evaluador separado y establecer un único presupuesto autorizado para su simulación y las 27 candidatas. Ejecutar la comparación de M3 fijo contra la variante sobre **observaciones reales del modelo simulado**, registrar casos correctos, conjuntos y abstenciones, y preservar resultados negativos. No iniciar PT-07/R4, REF, Clef o Clairic.
