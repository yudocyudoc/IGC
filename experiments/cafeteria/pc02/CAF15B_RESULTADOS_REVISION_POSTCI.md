# CAF-15B — Resultado canónico, demostración de exclusión y revisión adversativa

**Documento POSTERIOR a CI**, no parte del primer precompromiso. **PR #128 Draft**, apilado sobre #127 CAF-15A Draft; #123–#126 continúan Draft, ninguno fusionado. Primer commit del protocolo CAF-15B `eb2d48d227c7c3dc20fca18fd6a0e320a7afbbb5`, anterior al código y a ambas corridas de CI.

## Cadena de custodia

- **[CI canónica #41264831277](https://github.com/yudocyudoc/IGC/actions/runs/41264831277)**: 8/8 tests PASS; solver y verificación de árboles PASS. **Head probado** `b88dd6462fe0a6c6ab14a14ea320a8bf994cacb8`; **checkout merge sintético** `da36317ee36a63b018aa99d4022c8afc49e8189c` (distintos, registrados en los archivos).
- Corrida anterior **[#41264793808](https://github.com/yudocyudoc/IGC/actions/runs/41264793808)** falló por **verificación física de K0** que pasaba al DES llegadas posteriores al instante observado (error `DES_ARRIVAL_AFTER_HORIZON`). Commit correctivo `b88dd64` restringe el prefijo de llegadas de la llamada de VERIFICACIÓN física en t<20. **No** modifica recurrencia racional, cotas, topologías, firmas, tolerancia, programas, presupuesto, criterio de exclusión o veredicto científico. El primer resultado válido es la corrida canónica.
- **[Cuatro archivos auditables originales](https://github.com/yudocyudoc/IGC/actions/runs/41264831277/artifacts/13067026769)**: `00_PLAN_BEFORE_SOLVER.json`, `01_RESULTADOS.json` (árboles y testigos), `02_INFORME.md`, `03_MANIFIESTO.json`. **3/3 hashes SHA256 coinciden** con el manifiesto.
- En el primer archivo se fijan los treinta contrastes `15 pares×2 programas`, 5000 nodos/contraste, profundidad máxima 32, tolerancia ±1, parámetros continuos de `55..110` pedidos/h por etapa, y tres posibles estados científicos. El plan se escribe antes de ejecutar el solver; no se generan ni evalúan nuevos mundos.

## Resultado: separación GLOBAL (condicional a la familia) de 11 pares sobre capacidades independientes

| Programa congelado | Testigos certificados de confusión | Separaciones globales certificadas | Indeterminados | Nodos usados |
|---|---:|---:|---:|---:|
| `F_R25_T20`: K0/K1 + tres colas/tres stocks bajo tasa 150/h, t20 | **4/15** | **11/15** | 0 | 15 |
| `F_R25_T25`: mismo pulso, t25 | **4/15** | **11/15** | 0 | 15 |

Cada certificado de separación es una hoja `X` sobre el **producto completo** `[6/11,12/11]^(kA+kB)`, con canal discriminante y cotas enteras racionales. El verificador reconstruye el dominio y recalcula la condición `L_A>U_B+2` o `L_B>U_A+2`. **No hubo subdivisiones**: una sola región completa por contraste ya bastaba para los once casos, por lo que no hay argumento de convergencia numérica escondido. Los cuatro testigos de confusión están en los vértices de duración mínima (c=110), pertenecen al dominio y fueron comparados contra DES nativo y recurrencia.

## Cotas independientes que explican los once certificados

Se realizó una comprobación adicional separada del buscador, implementando la recurrencia exacta FIFO con `Fraction` y contando eventos en `≤t` a las esquinas rápidas/lentas del dominio. Las siguientes cotas son **cotas garantizadas conservadoras** (NO intervalos estadísticos):

| Sonda a demanda 150/h | Cola de preparación si preparación limitada (1 servidor, c∈55..110) | Cola de preparación si NO limitada (2 servidores fijos, servicio 1 min) | Diferencia inferior |
|---|---|---|---:|
| t20 | **[13,31]** | **[10,10]** | 3 |
| t25 | **[4,27]** | **[0,0]** | 4 |

Esto separa cualquier pareja de estructuras donde solo una tiene preparación nominalmente limitada. En los otros pares sin cuello en preparación, la **cola de despacho** diferencia una etapa de un servidor de otra con dos servidores fijos:

| Sonda a demanda 150/h | Despacho limitado, preparación no limitada | Despacho no limitado, preparación no limitada | Diferencia inferior |
|---|---|---|---:|
| t20 | **[3,20]** | **[0,0]** | 3 |
| t25 | **[4,26]** | **[0,0]** | 4 |

Las dos diferencias superan `2×1=2`, así que **ninguna lectura entera compartida ±1 es posible** para esos pares de familias para NINGUNA capacidad independiente del dominio. Las otras etapas aguas abajo **no bloquean** las primeras etapas en este DES (buffers ilimitados), por lo que sus tiempos de servicio no alteran estas colas.

**Por qué son suficientes para todos los once:** nueve pares se distinguen por presencia/ausencia de preparación limitada y los otros dos, cuyas etapas de preparación no están limitadas, por presencia/ausencia de despacho limitado; las cuatro confusiones persistentes ocurren precisamente cuando compartir el perfil de colas observables de las etapas aguas arriba vuelve indistinguibles las restricciones posteriores con esta tolerancia. El mapa exacto de hoja del artefacto usa solo el índice 2 (`waiting_preparacion`) o 3 (`waiting_despacho`), nunca stocks, para las once separaciones.

**La independencia de capacidades no perjudica el certificado:** en vez de consultar un único c diagonal se comprueba de forma conservadora `c_preparacion∈[55,110]` y/o `c_despacho∈[55,110]` sin acoplarlos. El producto de cuatro dimensiones queda descartado por un solo canal.

## Las cuatro parejas confundibles, con testigo DES exacto

1. `preparacion` frente a `preparacion+despacho`;
2. `preparacion` frente a `preparacion+entrega`;
3. `despacho` frente a `despacho+entrega`;
4. `preparacion+despacho` frente a `preparacion+entrega`.

La existencia de capacidades y firmas compatibles en un punto del dominio demuestra `CONFUSABLE_WITNESS_CERTIFIED`, pero **no** que toda capacidad de esos pares sea confundible. En particular, varios testigos usan c=110/h, pero la revisión POST HOC de CAF-14 ya demostró que estas ambigüedades persisten en interior y no son únicamente artefacto del borde.

## Revisión adversativa de la palabra «certificado»

- **Sí está certificado matemáticamente CONDICIONAL a esta física** que los once pares de estructuras no pueden compartir observación con error de conteo ±1 en esos programas, incluso con capacidades dobles independientes. La prueba es una exclusión exacta de todo el producto, no una rejilla.
- El verificador implementado es **independiente del recorrido del árbol de búsqueda**, reconstruye cobertura y reevalúa cada hoja. Sin embargo **comparte la implementación de las cotas físicas y la recurrencia con el solver**; por tanto **no es una demostración formal mecanizada con núcleo de confianza independiente**. Una auditoría matemática externa sigue siendo necesaria. La tabla de cotas anterior proporciona una derivación/revisión adicional fácil de reproducir con `Fraction`, pero no reemplaza prueba formal de semántica DES.
- La monotonía usada es demostrable por inducción en la recurrencia FIFO: llegada a etapa, liberación de servidor, `max` y adición de duración son funciones no decrecientes de todos los tiempos de servicio. El conteo de eventos `≤t` invierte el orden. Las diferencias `arrived-started` y `arrived-completed` se acotan **conservadoramente**, sin suponer monotonía de las colas o stocks mismos.
- No se ha probado el sistema de una PYME ni su capacidad de ejecutar una demanda de 150/h, medir stocks en tiempo real, sostener una cola sin bloqueo físico o tener error ±1 calibrado.
- No hay estimación de c1,c2 a partir de datos estocásticos; la prueba es de **separabilidad de pares de familias**, que no equivale a identificar un mecanismo único de los seis si queda al menos un rival confundible con él. Tampoco afirma que se identifique un mecanismo ante estructura ajena al catálogo.
- El dominio y la carga máxima fueron elegidos en laboratorios sintéticos previos; esto **no** es validación empírica independiente ni inferencia de campo real. La literatura de excitación persistente no convierte esta prueba en un instrumento económicamente seguro.

## Implicación y siguiente decisión

Se cierra la laguna estrictamente matemática entre CAF-14 (un c diagonal) y CAF-15A (malla 2D): **los once pares de CAF-14 sobreviven como separables en el dominio 2D completo, dentro del DES especificado**. Esto no resuelve las cuatro confusiones ni justifica otro torneo de selectores. La prioridad científica pasa a **robustez ante servicio estocástico, sensores temporales con error explícito, observación de demanda natural, y un generador independiente**. Los sensores de colas definidos aquí presuponen que pueden instrumentarse por etapa y con suficiente exactitud.

**Gate:** `BLOCKED_DETERMINISTIC_SAME_DES_UNCALIBRATED_SENSOR_NO_EXTERNAL_VALIDATION`. PR #128 sigue Draft y sin merge. Revisión externa antes de utilizar cualquier afirmación como evidencia empresarial.
