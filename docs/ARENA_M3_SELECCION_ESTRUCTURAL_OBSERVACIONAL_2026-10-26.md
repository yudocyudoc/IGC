# Arena M3 — prueba de selección estructural por observaciones dentro de Short E1

**Fecha:** 2026-10-26. **Motivación:** hallazgos del revisor Astra (REVISION_CAMBIOS_BRAZOS_R2): el brazo M componía estructuras originales tipadas, pero `choose_one` elegía siempre la más simple sin consultar observaciones; M2 duplicaba dos tiempos de respuesta por una heurística definida por el adaptador. Ninguna operación seleccionaba la topología a partir de los datos.

## Alcance preciso

Este PR **no modifica** `experiments/e1/composer.py`, `experiments/e1/backend.py`, el catálogo, las moléculas Modelica ni el M1/M2 histórico. Introduce una prueba **M3 distinta y adicional**, con recursos propios, sin atribuirle retrospectivamente un logro a M1/M2.

La selección M3 es una **política nueva, implementada en el adaptador experimental**, sobre los candidatos del **compositor original**. Debemos atribuir por separado la *capacidad de representar estructuras* (Short E1) y la *capacidad de elegir usando evidencia* (nuevo M3). No afirmar que el algoritmo original Short E1 ya realizaba selección observacional.

## Los seis grafos y las tres clases materialmente observables

`registry.base.json` produce seis grafos. Son **tres caminos materiales** con y sin un filtro de señal de reporte que, por definición de los puertos del backend, no afecta `deliveredTotal`. La señal de reporte podría identificarse con **otro observable**, pero es invisible para esta prueba de entrega acumulada. Los tres alias se excluyen de la clasificación de estructura por no ser discriminables con los datos actuales; no se declaran refutados.

- `C00`: preparación y despacho, **dos colas**, sin tránsito.
- `C01`: preparación y despacho y una cola de tránsito, **tres colas**.
- `C02`: preparación y despacho y dos colas de tránsito, **cuatro colas**.

Los `responseTime` de preparación y despacho siguen en **0.5 h**, `maxThroughput` **20 items/h**; la cola de tránsito, cuando existe, conserva `responseTime=1.6 h` y `maxThroughput=100 items/h`. **No se calibra ningún parámetro**. El único reemplazo del backend original es la fuente externa pública `rate=1.7 items/h, duration=2 h`; se conservan los componentes.

## Diseño del ensayo, fijado antes de adjudicar

Un experimento separado del M2 original utiliza **cinco simulaciones reales** de OpenModelica, usando las bibliotecas Short E1 originales SystemDynamics 2.1.2 y MSL 4.0.0:
- Tres candidatos `C00/C01/C02`, simulados en 0–6 h con 120 intervalos, método DASSL.
- Dos mundos sintéticos ejecutados como clases diferentes por el backend E1 original, `M3W00` de dos colas y `M3W01` de tres colas, **240 intervalos** y mismo motor. Esto sirve para **probar recuperación de la propia familia de modelos**, no para validar ante mecanismos externos.

Los dos casos ciegos `case-alpha` y `case-beta` contienen únicamente `deliveredTotal` sintético de sus mundos fuente en `t={0,1,2,3}` más una perturbación fijada antes de evaluar: `[0,+0.002,-0.003,+0.004]` items. No contienen nombre de modelo generador, número de colas, puntajes previos ni salida de D/B. Solo después de congelar la selección se abren los puntos temporales reservados `t={4,5,6}` (perturbaciones `[-0.003,+0.002,-0.004]`) y la tabla sellada de origen.

La frontera selector/evaluador se asegura con procesos separados y contratos de entrada: `scripts/arena_m3_select.py` **no acepta ni abre** la tabla de verdad o los puntos reservados. El script de adjudicación final los abre después. Se conservan todos los CSV y las trazas.

La política de decisión (predeclarada):
1. Verifica el grafo nativo original, el repertorio fijo y la paridad de material/entregado de cada candidato mediante la sonda G2 original de M.
2. Calcula RMSE con **4** puntos de construcción para cada uno de los **3** candidatos fijos.
3. Si el mejor RMSE supera **0.020 items**, declara `ABSTAIN: ALL_FIXED_E1_STRUCTURES_MISS_CONSTRUCTION_TOLERANCE` — no inventa una nueva estructura.
4. Si la diferencia RMSE entre los dos mejores es menor a **0.035 items**, declara `ABSTAIN: OBSERVATIONS_DO_NOT_DISCRIMINATE_FIXED_E1_PATHS` — no confunde parámetros con estructura.
5. En otro caso selecciona la topología con menor RMSE, con desempate determinista por número de colas y hash/ID. No se ajustan parámetros.

El evaluador, no el selector, comprueba después si `case-alpha` seleccionó `C00` y `case-beta` seleccionó `C01`; si cambiaron de estructura al cambiar las observaciones y qué RMSE obtienen con los tres tiempos reservados. **La adjudicación reserva tiempos posteriores del mismo mundo sintético, no representa una población, mecanismo o cafetería independiente.**

## Resultados reales (primera corrida completa, anterior al negativo ampliado)

[GitHub Actions #40298010634](https://github.com/yudocyudoc/IGC/actions/runs/40298010634) **SUCCESS**, OpenModelica real, artefacto [#12639246621](https://github.com/yudocyudoc/IGC/actions/runs/40298010634/artifacts/12639246621), con cinco CSV (tres candidatos y dos mundos sintéticos separados), observaciones cegadas, puntuaciones y tabla de origen revelada **solo en la adjudicación**.

| Caso ciego | Origen sellado, revelado después | Elección desde construcción | RMSE C00 | RMSE C01 | RMSE C02 | Margen al siguiente | RMSE de t=4–6 |
|---|---|---|---:|---:|---:|---:|---:|
| alpha | C00 (2 colas) | **C00** | **0.002693** | 0.977483 | 1.466708 | 0.974791 | 0.003109 |
| beta | C01 (3 colas) | **C01** | 0.975931 | **0.002693** | 0.503199 | 0.500506 | 0.003109 |

Las tres trayectorias candidatas verificaron conservación material dentro de \(7\times10^{-12}\) elementos. La prueba contiene ruido sintético determinista fijado previamente y **no calibró** parámetros. Cada caso eligió la estructura generadora, y la elección cambió al cambiar los datos. No afirmar precisión causal externa: **el generador pertenece exactamente a la familia seleccionable**. Los datos de t=4–6 vienen de la **misma** simulación fuente y solo estaban temporalmente reservados; no equivalen a un holdout independiente de cafeterías.

Una primera ejecución M3 chocó con la duplicación de filas en t=2 (evento de cierre del pulso) y t=6 (fin del CSV). La corrección solo admite duplicados de tiempos cuando \(\text{deliveredTotal}\) coincide numéricamente (tolerancia 1e-5), preservando los eventos reales sin interpolar ni editar el modelo. Se añadió un control negativo que rechaza duplicados físicamente contradictorios.

Una prueba adversativa complementaria toma **el mismo identificador de caso alpha** y sustituye únicamente sus observaciones por las beta: debe pasar de C00 a C01. Otra usa entregas nulas ante el pulso inicial: el selector debe declararlas fuera de su familia con `ABSTAIN`, nunca presentar el modelo «menos malo» como identificado. Ambos controles usan los **CSV reales** de los candidatos y no nuevas simulaciones. La regresión ampliada terminó **SUCCESS** en [Actions #40298421985](https://github.com/yudocyudoc/IGC/actions/runs/40298421985) y dejó el artefacto completo [#12638758997](https://github.com/yudocyudoc/IGC/actions/runs/40298421985/artifacts/12638758997). El log confirmó ambos resultados con CSV reales:

- `M3_EMPIRICAL_EVIDENCE_SWAP_CHANGED_STRUCTURE_WITH_SAME_CASE_ID`: con la **misma etiqueta alpha** y las observaciones de beta, M3 cambió de `C00` a `C01`.
- `M3_OUT_OF_FAMILY_CONSTRUCTION_ABSTENTION ALL_FIXED_E1_STRUCTURES_MISS_CONSTRUCTION_TOLERANCE`: con un vector de entregas nulas, se abstuvo en lugar de seleccionar por defecto `C02` u otra ruta.

El artefacto contiene el modelo generado E1, tres CSV candidatos y dos CSV generadores independientes de compilación, observaciones publicadas, puntajes, contrafactuales, clave sellada, evaluación temporal reservada y log de OMC; todos los pasos de CI concluyeron SUCCESS. La revisión externa deberá distinguir esta **sensibilidad de la política adaptadora M3** de capacidades pertenecientes al compositor E1 original.

## Lectura correcta de un resultado

Un PASS demostraría únicamente que **la combinación E1 + nueva política M3** puede consultar datos de construcción, **seleccionar diferentes topologías materiales de un repertorio fijo** y expresar abstención frente a ambigüedad o fuera-de-familia. Las opciones de filtro informativo seguirían sin identificación con `deliveredTotal`.

No mostraría:
- Que el compositor original descubrió por sí solo qué estructura física correspondía a datos.
- Que M tiene capacidad de descubrir mecanismos ajenos al catálogo actual o calibrar parámetros no prefijados.
- Que existe superioridad estadística de M respecto de D/B.
- Que se ha identificado un mecanismo causal real a partir de cafeterías.
- Que los tiempos reservados de la **misma** simulación constituyen prueba predictiva externa.

Un FAIL documentaría exactamente qué se rompe: simulación/modelización G2, diferencia no observable, selección no sensible, abstención o fallo de la revisión posterior. Nunca reemplazar candidatos perdedores, ampliar umbrales ni modificar los mundos después de observarlos para fabricar un PASS.

## Archivos y auditoría

- `scripts/arena_m3_prepare.py`: genera E1 original y un manifiesto fijo, más dos clases generadoras separadas.
- `scripts/arena_m3_select.py`: selección **solo** con CSV de candidatos y observaciones de construcción, verificando conservación; incluye abstención.
- `scripts/arena_m3_adjudicate.py`: genera observaciones desde el mundo, guarda la clave sellada, **solo después** abre reserva y compara la selección contra origen.
- `tests/test_arena_m3_structure.py`: invariantes del catálogo, repetibilidad del emisor, cambio de elección por observaciones, abstenciones, inyección de contenido prohibido y manejo de filas duplicadas por eventos OMC.
- `.github/workflows/arena-m3-evidence-structure.yml`: cinco ejecuciones originales en OpenModelica; las series, modelos, observaciones, selecciones y clave sellada quedan juntos en un artefacto descargable tras la corrida.

**Dependencia antes del piloto cafetería:** a diferencia de este ensayo cerrado, los datos de una cafetería no provendrán de uno de los tres modelos candidatos. Deberá conservarse el estado `ABSTAIN` como resultado legítimo y formular nuevas preguntas de campo para distinguir mecanismos no observables.
