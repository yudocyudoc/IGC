# Arena M3-P — Variación paramétrica con el compositor Short E1 y selector M3 originales

**Fecha:** 2026-10-26. **Estado:** SEIS mundos sintéticos realmente simulados en OpenModelica, ejecución [#40419482374](https://github.com/yudocyudoc/IGC/actions/runs/40419482374) **SUCCESS**, artefacto original [#12697511713](https://github.com/yudocyudoc/IGC/actions/runs/40419482374/artifacts/12697511713) (modelos, seis CSV reales, observaciones ciegas, parámetros sellados, originales y evaluación). PR #41 draft.

## Pregunta y diseño

Astra R3 constató que M3 recuperaba estructura en dos mundos generados dentro de la misma familia **con exactamente los parámetros del candidato**. Debíamos probar si M3 podía distinguir estructura cuando el mecanismo molecular era el mismo pero los parámetros de tiempos de respuesta cambiaban.

Se reutilizan **sin editar** el original `experiments/e1/composer.py`, `backend.py`, `registry.base.json`, las moléculas originales y el selector `scripts/arena_m3_select.py`. Sus tres candidatos fijos C00 (dos colas), C01 (tres) y C02 (cuatro) proceden de los **CSV reales originales** de M3 [#40298421985](https://github.com/yudocyudoc/IGC/actions/runs/40298421985).

Se generaron seis mundos sintéticos **con el mismo compositor/backend E1 y las mismas topologías**, cambiando únicamente el parámetro `responseTime` en instancias del mundo generador. La gramática de moléculas admite esos valores (rango del catálogo 0.1..5 horas). No se asignan estos parámetros al selector. Cada mundo se simuló aparte con OpenModelica 1.26.5, MSL 4.0.0 y SystemDynamics 2.1.2; 240 intervalos, DASSL, 0..6 horas.

Se entrega a M3 solamente `deliveredTotal` en t=0,1,2,3 con ruido determinista preestablecido `[0,+0.002,-0.003,+0.004]`; t=4,5,6, el grafo generador, los parámetros cambiados y la clase de origen están fuera de su entrada. La política original exige RMSE máximo **0.020** y margen al segundo mínimo **0.035**; no se retocaron.

## Resultados originales de la inferencia M3

| Caso | Estructura generadora | Cambio solo en tiempos del mundo | RMSE mejor candidato fijo | Candidato menor RMSE (sin umbral) | Respuesta oficial M3 |
|---|---|---|---:|---|---|
| P01 | C00 | preparación .65 / despacho .45 h | 0.082695 | C00 | **ABSTAIN** |
| P02 | C01 | tránsito 1.10 h | 0.193385 | C01 | **ABSTAIN** |
| P03 | C02 | ambos tránsitos 1.10 h | 0.182299 | C02 | **ABSTAIN** |
| P04 | C01 | tránsito 0.12 h | 0.114778 | **C00 erróneo** | **ABSTAIN** |
| P05 | C00 | preparación .90 / despacho .90 h | 0.403941 | **C01 erróneo** | **ABSTAIN** |
| P06 | C02 | ambos tránsitos 0.12 h | 0.227056 | **C00 erróneo** | **ABSTAIN** |

**Seis abstenciones; cero estructuras correctamente seleccionadas, cero estructuras incorrectamente seleccionadas.** No se manipuló ningún umbral después de ver datos.

**Segundo hallazgo:** si M3 estuviera forzado a seleccionar siempre el mínimo RMSE ignorando el umbral de adecuación, elegiría **la topología equivocada en tres de los seis casos** (P04, P05, P06). No es un método de inferencia genuino, sino una comparación hipotética post hoc que muestra la importancia de su política de abstención.

Esta prueba evidencia que valores de parámetros fuera de las plantillas pueden hacer que una estructura material conocida parezca incompatible con su respuesta dinámica fija. Además, bajo ciertos parámetros, otras topologías del catálogo pueden producir trayectorias más cercanas. **No podemos separar inferencia estructural de incertidumbre de parámetros seleccionando únicamente las tres curvas nominales.**

## Consecuencia metodológica

Esto no demuestra que M3 «no puede modelar» el sistema: los seis mundos fueron construidos y simulados con las moléculas originales. Demuestra que **M3 actualmente no busca, ajusta ni marginaliza parámetros**; elige entre tres **parametrizaciones congeladas**. Cuando cambian los parámetros, sus reglas pueden abstenerse correctamente, pero no aprovechan las posibilidades de la familia.

Siguiente experimento delimitado: **estimación acotada de parámetros por topología** usando solo t=0–3, seguida de evaluación en los tiempos reservados y comparación de alternativas con penalización por complejidad. Evitar declarar «estructura encontrada» cuando varias topologías con parámetros ajustados reproducen lo mismo. También conservar la abstención como decisión legítima, así como los seis resultados negativos históricos.

**Límites:** los seis generadores usan el mismo backend/compositor que los candidatos; no hay validación independiente de un mecanismo causal de cafetería. El ruido es determinista, no instrumental. El tamaño de muestra, cuatro tiempos de construcción y tres de reserva dentro del mismo experimento sintético, puede ser insuficiente para identificar tantos parámetros conjuntamente. El filtro informativo de M sigue siendo invisible a este observable.

No ampliar ATMS ni reemplazar las moléculas. PR abierto como draft, sin merge a main.
