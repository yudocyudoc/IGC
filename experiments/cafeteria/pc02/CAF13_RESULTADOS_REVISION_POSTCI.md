# CAF-13 — Resultado canónico y revisión adversativa: cuándo son distinguibles dos estructuras

**Estado:** revisión POSTERIOR a la CI, no nuevo precompromiso. PR #125 Draft sobre #124 Draft; sin fusionar. **Fecha de protocolo:** 2026-10-31, primer commit `1267f8ffc3583b04619ceb8607a189c78c12a643`. No hay reoptimización de programas tras observar los mundos.

## Procedencia verificada

- CI canónica **[GitHub Actions #41257110496](https://github.com/yudocyudoc/IGC/actions/runs/41257110496)**: siete tests aprobados; ejecución del programa y guardas de ingeniería PASS. Head probado `22d071e98ced4757f8672ad823b3cc993e3be0c6` y **checkout SHA del merge sintético** `ec034a8159c60ee6044aa68b26bee67af86b4c39`, ambos registrados por separado en resultados.
- [Artefacto completo de 6 archivos](https://github.com/yudocyudoc/IGC/actions/runs/41257110496/artifacts/13063317188): `00B_CATALOGO_FIRMAS_ANTES_MUNDOS.json`, `00_PLAN_ANTES_MUNDOS.json`, `00C_GRAFO_GLOBAL_PRE_EVALUACION.json`, `01_RESULTADOS.json`, `02_INFORME.md`, `03_MANIFIESTO.json`. Plan, 48 conjuntos de firmas y 120 comparaciones del grafo **calculados antes de consultar DES sobre los mundos**. Manifiesto con SHA256.
- Corrida anterior [#41257075120](https://github.com/yudocyudoc/IGC/actions/runs/41257075120) también pasó 7/7 y produjo la misma tabla sustantiva, pero **NO se considera canónica** tras una modificación de ingeniería que reutiliza relojes de pruebas y el catálogo previo para verificar la contención del parámetro, en vez de recomputarlo durante la evaluación. La regla de decisión, familias, programas, mundos y tolerancia **no cambiaron**.
- Total: **6 familias** × 8 programas = 48 conjuntos exhaustivos de firmas racionales; **15 pares** × 8 programas = 120 comparaciones de confundibilidad; **32 mundos** × 8 programas × 6 familias = 1536 filtrados nominales. 27 mundos in-family y 5 out-of-family (cuarta etapa oculta), todos sintéticos compartiendo DES.

## Resultado global: TODOS los pares tienen al menos un testigo de confusión

| Programa fijo K0/K1 + T | Confundibles existencialmente /15 | Robustamente separables para TODAS las capacidades /15 | Únicos correctos exactos /27 | Únicos robustos ante ±1 /27 | Dobles únicos /18 | Unknowns falsos únicos /5 | Unknowns sin familia compatible /5 |
|---|---:|---:|---:|---:|---:|---:|---:|
| BASE (entregas únicamente) | **15** | 0 | 0 | 0 | 0 | 0 | 0 |
| Q20_15 (tres colas en t20, tasa 1.5/min) | **15** | 0 | 2 | 1 | 0 | 0 | 4 |
| STOCK20_15 (tres stocks en t20, tasa 1.5/min) | **15** | 0 | 1 | 1 | 0 | **1** | 3 |
| FULL20_15 (colas+stocks, t20, tasa 1.5/min) | **15** | 0 | 2 | 1 | 0 | 0 | 4 |
| Q40_15 (tres colas en t40, tasa 1.5/min) | **15** | 0 | 0 | 0 | 0 | 0 | 0 |
| FULL40_15 (colas+stocks, t40, tasa 1.5/min) | **15** | 0 | 0 | 0 | 0 | 0 | 0 |
| Q20_18 (tres colas en t20, tasa 1.8/min) | **15** | 0 | **3** | **3** | 0 | 0 | 4 |
| FULL40_18 (colas+stocks, t40, tasa 1.8/min) | **15** | 0 | 0 | 0 | 0 | 0 | 0 |

**Interpretación formal:** `CONFUSABLE_EXISTENTIAL` significa que existe al menos un par de capacidades (posiblemente distintas) para dos estructuras que generan firmas de conteos cuya diferencia es ≤2 en cada canal. Bajo ±1, las cajas de observación se intersectan y existe una lectura común. La ausencia de `ROBUSTLY_SEPARABLE_GLOBAL` **NO demuestra** que cada par sea indistinguible para todos los parámetros, inputs u horizontes.

**Todos los 9 pares single-vs-double y los 3 pares double-vs-double conservan testigos de confusión en CADA programa.** Los tres pares single-vs-single también. Todos los 27 mundos in-family mantienen su clase correcta compatible, control de autoconsistencia que era obligatorio y esperado. No hay ningún doble cuello como clase única, aun cuando una lectura pueda eliminar varias alternativas.

## Testigos exactos: el régimen sin excitación produce confusión real

En `Q20_18` (K0 y K1 entregas + tres colas a minuto 20 con demanda 9/5 por minuto), las familias:
- `preparacion+despacho`, capacidad **110 pedidos/hora**, y
- `preparacion+entrega`, capacidad **110 pedidos/hora**,

tienen la **misma firma entera exacta `[9,27,0,0,0]`**. Es un testigo directo de que ambas estructuras son observacionalmente confundibles bajo ese programa, incluso **sin error de sensor**. Esto no implica que sus dinámicas sean idénticas en otros regímenes: en este caso finito, observar colas cero no revela cuáles de las etapas de un servidor serían limitantes al aumentar la demanda o cambiar de horizonte.

En `BASE`, para estas mismas dos familias, el grafo da testigos con capacidades **110** y **`31590/371` ≈ 85.15 pedidos/hora**, firmas `[9,27]` y `[9,25]`; existe lectura común entera `[8,26]` bajo ±1. Nótese que no se requiere igual capacidad para obtener confusión de familias; es el problema de identificar simultáneamente estructura y parámetros.

**Importante:** estas dos instancias son testigos de confundibilidad, no una demostración de equivalencia de comportamiento para todos los parámetros.

## Efecto del tiempo: el horizonte de lectura puede borrar información

En los **32 mundos concretos** de este protocolo:
- `Q40_15`: el vector de las tres colas en minuto 40 es **[0,0,0] en 32/32**.
- `FULL40_15` y `FULL40_18`: el vector de las seis variables cola+stock de tres etapas es **[0,0,0,0,0,0] en 32/32**.

Todos los mundos han drenado el trabajo pendiente al minuto 40 en los canales observados. Por eso, esos programas regresan a las seis clases compatibles con BASE en los 27 mundos in-family y no ayudan a identificar los dobles en estos casos. **No concluir** que todo horizonte posterior sea peor: otras cargas, capacidades, duración de pulso o timestamps podrían cambiar esa conclusión.

## Distinción entre singleton observado y resolución robusta

Los únicos casos con clase única correcta en cualquiera de los ocho programas son:
- `SINGLE_68_2` (cuello único en entrega): robustamente único con Q20_15, STOCK20_15, FULL20_15 y Q20_18;
- `SINGLE_83_2`: única con Q20_15/FULL20_15, pero **NO robusta** ante todos los errores ±1; sí robusta con Q20_18;
- `SINGLE_97_2`: única y robusta **solo** con Q20_18.

La discrepancia en `SINGLE_83_2` es esencial: una única clase superviviente después de filtrar la lectura EXACTA con ±1 no garantiza que TODAS las lecturas alternativas ±1 alrededor del estado verdadero produzcan la misma clase. Por eso necesitamos distinguir etiqueta observada y criterio de separación robusta.

**Controles de topología desconocida:** `STOCK20_15` produce una **falsa clase única `despacho`** para `EXTRA_86` (cuarta etapa fuera de modelo). Q20_15, FULL20_15 y Q20_18 excluyen todas las seis familias en cuatro controles, pero ninguno demuestra la identidad de la cuarta etapa. El quinto permanece compatible. No derivar una garantía de detección de «unknown».

## Implicaciones metodológicas y siguiente hipótesis

1. **CAPACIDAD DE EXCITACIÓN.** Los testigos a `c=110` con colas cero sugieren que algunos programas nunca fuerzan simultáneamente suficientes restricciones como para identificar qué etapa concreta produciría un cuello si el campo cambiase. La indistinguibilidad es relativa a intervención, horizonte, sensor y dominio paramétrico.
2. **DOBLES CUELLOS.** Con igual duración nominal `d` en dos etapas de un tándem FIFO, el flujo aguas arriba puede regular la llegada a la segunda etapa e impedir que una segunda restricción aparezca como una cola adicional. Esto es una **hipótesis mecanística razonable**, no una demostración completa de equivalencia estructural.
3. **NUEVA PREGUNTA.** Antes de optimizar un selector, caracterizar qué entradas de demanda, duración de pulso, observables temporales por pedido y capacidad de sensor son *necesarios/suficientes* para distinguir familias en regiones del espacio paramétrico. Una prueba de excitación con tasa máxima cuidadosamente predeclarada debe respetar límites físicos y no crear sensores mágicos.
4. **PROTECCIÓN CONTRA FALSA CERTEZA.** Separar compatibilidad de clase, singleton en una lectura exacta, robustez ante todas las lecturas admitidas y validez frente a estructuras fuera del catálogo. Exigir evidencia independiente de la familia para promover una certificación real.

No se implementó un nuevo selector, política, modelo probabilístico, reentrenamiento, ni operaciones fuera del catálogo. No hay intervención económica recomendada ni validación externa.

**Gate científico permanente:** `BLOCKED_SAME_DES_PHYSICS_UNCALIBRATED_TOLERANCE_NO_EXTERNAL_VALIDATION`; conservar los resultados adversos y mantener PR Draft, sin fusionar.
