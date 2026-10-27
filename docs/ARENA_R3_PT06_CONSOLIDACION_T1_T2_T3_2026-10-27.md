# IGC · Arena — Consolidación de R3 / PT-06 (T1, T2 y T3)

**Fecha:** 2026-10-27. **Estado:** cierre del corte experimental de tres casos y reconstrucción offline en la memoria F1a/ATMS. **Alcance:** PT-06/R3 de hoja de ruta v2.0; no se activa PT-07/R4.

## Resumen ejecutivo

**R3 sí produjo tres resultados empíricos distinguibles dentro del repertorio E1 declarado, pero no identificó una estructura causal única ni mejoró generalmente M3.**

- **T1 — parámetros generadores fuera de la grilla:** mundo C00, con respuesta de preparación 0.75 h y despacho 0.30 h; **M3 original ABSTAIN** y **R3 ABSTAIN**, pese a que la fuente material C00 pertenece al catálogo. El mejor modelo fue **C00P04 (RMSE 0.035408529)**, precisamente el representante nominal congelado, por encima del umbral 0.020.
- **T2 — observación demasiado temprana:** mundo C01 nominal, solo 0–0.15 h; **M3 original ABSTAIN**, mientras **R3 devuelve un conjunto ambiguo {C00,C01,C02}**, todas compatibles bajo la tolerancia 0.020. La verdad C01 se revela después de seleccionar, nunca se entrega al selector. No es equivalencia global.
- **T3 — dinámica demasiado lenta para la grilla:** mundo C02 con responseTime 4 h en preparación, despacho y tránsito, fuera de las 27 configuraciones pero dentro del catálogo molecular; **ambos métodos ABSTAIN**. R3 señala incompatibilidad de **la grilla particular**, sin afirmar imposibilidad de C02 o del repertorio E1 completo.

El resultado distintivo es que el selector R3 puede **preservar incertidumbre estructural** como conjunto compatible o declarar **incompatibilidad con la búsqueda finita**, en lugar de elegir ciegamente el menor RMSE. Esta capacidad es operacional y está condicionada al umbral/ventana, **no** constituye identificación causal, generalización ni predicción independiente.

## 1. Condiciones que no cambiaron

Los tres ensayos utilizaron C00, C01 y C02 (materiales del compositor/backend Short E1 original); 9 configuraciones por topología para tiempos de preparación y despacho `{0.25,0.5,1.0} h`; parámetros de tránsito candidatos congelados en el valor nominal; estímulo de entrada rectangular **1.7 items/h en t=0–2 h**.

La política M3 original quedó intacta, con máximo RMSE de construcción **0.020 items** y margen **0.035 items**. La política nueva de R3 toma el menor RMSE por estructura y devuelve todas las estructuras con mínimo ≤ **0.020**. Este umbral es **operacional**; ninguna fuente del experimento lo estableció como límite metrológico.

Los datos proceden de las simulaciones físicas reales: los **27 modelos candidatos + mundo T1** de [Actions #40578550337](https://github.com/yudocyudoc/IGC/actions/runs/40578550337), y solo **dos mundos generadores adicionales** de [Actions #40582633807](https://github.com/yudocyudoc/IGC/actions/runs/40582633807), T2/T3. Los 27 CSV se reutilizaron sin reejecutarlos. No hubo inferencias de IA. Los parámetros de origen sintético se revelaron **después** de almacenar las decisiones.

## 2. Matriz conjunta de evidencia

| Criterio | T1 — respuesta desplazada | T2 — ventana temprana | T3 — fuera de grilla |
|---|---|---|---|
| Fuente sintética | C00 | C01 | C02 |
| Intervalo observable h | 0,1,2,3 | 0,0.05,0.1,0.15 | 0,1,2,3 |
| Mejor C00 (RMSE items) | 0.035409 | 0.000424 | 1.074799 |
| Mejor C01 (RMSE items) | 0.647637 | 0.000000 | 0.433917 |
| Mejor C02 (RMSE items) | 1.290101 | 0.000037 | 0.143834 |
| M3 original | ABSTAIN | ABSTAIN | ABSTAIN |
| R3 paramétrico | ABSTAIN (ninguna) | AMBIGUO (tres) | ABSTAIN (ninguna) |
| Ajuste ≤ 0.020 | 0 estructuras | 3 estructuras | 0 estructuras |
| G2 mundo | Conservación verificada | Conservación verificada | Conservación verificada |

La grilla R3 **no mejoró el resultado de M3 en T1 ni T3**. En T2 aporta una salida descriptiva más rica: muestra las tres alternativas que comparten compatibilidad bajo información extremadamente débil. No se deduce una superioridad generalizable de un único caso.

## 3. Interpretación de estructura, parámetros y observabilidad

**T1:** estructura verdadera representable, parámetros generadores válidos en el catálogo pero no en la grilla; no se debe concluir que C00 sea falsa ni alterar a posteriori la grilla para conseguir éxito. El mejor candidato cae por encima del umbral, por lo que abstenerse es consistente con el protocolo.

**T2:** las señales de entregas son casi nulas durante los primeros 0.15 h; incluso estructuras diferentes pueden satisfacer el umbral 0.020. El experimento muestra el límite de una ventana no informativa, pero **no** demuestra equivalencia de las trayectorias para otros tiempos o intervenciones. Ni siquiera el RMSE cero de C01 justifica declarar a C01 identificada cuando C00 y C02 siguen siendo compatibles.

**T3:** las tres estructuras candidatas se alejan de la dinámica generadora lenta. El menor error pertenece a C02, la estructura fuente, pero sigue excediendo el umbral. El rechazo significa **incompatibilidad de las 27 parametrizaciones concretas**, no negación de la familia C02 ni del lenguaje molecular.

**Frontera general:** una única trayectoria de cuatro observaciones, con generador y biblioteca parcialmente compartidos, no basta para inferencia estructural/causal externa. El mundo sintético no crea validación independiente, aunque la separación de etiquetas de verdad del evaluador evita una selección directamente circular.

## 4. Consolidación en memoria existente: F1a/ATMS

El módulo `scripts/arena_r3_pt06_consolidate.py` lee y vuelve a comprobar las **fuentes originales** (CSV, decisiones, reportes de adjudicación) con los mismos evaluadores que aprobaron las pruebas anteriores. No confía exclusivamente en documentos narrativos.

Se añaden al **ledger F1a existente**, sin tablas ni motor nuevos, tres casos independientes (`R3-T1`, `R3-T2`, `R3-T3`) con:
- procedencia/hash de las cuatro observaciones y de los 27 CSV candidatos originales;
- política histórica M3 congelada y política R3 acotada como **premisas distintas**;
- el resultado original de ambos selectores y la constancia de trayectoria física G2;
- dos justificaciones separadas (soporte de decisión M3 y soporte de decisión R3), con consultas `as_known_at` previas y posteriores;
- etiqueta de verdad del mundo sintético **`case-private`**; no ingresa al contexto de selección M y mucho menos a D/B.

Pruebas: los soportes para ambas políticas **aparecen después** de incorporar las evidencias; al desactivar hipotéticamente la premisa de R3, desaparece **solo** la justificación de R3, mientras permanece el soporte de la política M3. Cada caso conserva sus propios IDs y no introduce evidencia en las vistas D/B. El informe conjunto de tres casos queda también con acceso **`case-private`**, sin convertirse en un nuevo canal de feedback a productores.

**Importante:** las marcas de tiempo del replay son **cortes administrativos explícitos**, no las horas históricas de los experimentos. ATMS mantiene relaciones de procedencia y soporte lógico, **no determina verdad empírica**. El JSON y SQLite producidos en CI son una reconstrucción reproducible; no se anuncia que esa base sea una memoria de producción ya desplegada.

## 5. Dictamen de la etapa y límites de cierre

Se considera **consolidada la evidencia experimental T1–T3 de PT-06**: parámetros desplazados, observabilidad insuficiente y repertorio paramétrico incompatible. El cierre no implica que toda incertidumbre estructural haya sido resuelta, ni que R3 haya validado causalidad.

Permanece vigente:
- M3 original como referencia congelada;
- 27 candidatas y condiciones predeclaradas, sin optimizar T1/T2/T3 después de observar resultados;
- histórico R1/R2 (incluido Buffalo con estímulo divergente) intacto y no comparable por RMSE a estos ensayos;
- **R4/PT-07 y REF no ejecutados** en esta consolidación; Clef/Clairic no se activan;
- ninguna llamada adicional de IA y ninguna simulación nueva de OpenModelica.

**Procedencia:** diseño [PT-06 preregistrado](https://github.com/yudocyudoc/IGC/blob/main/docs/ARENA_R3_PT06_PREDECLARACION_PRIMER_CASO_2026-10-27.md); resultado [T1](https://github.com/yudocyudoc/IGC/blob/main/docs/ARENA_R3_PT06_T1_RESULTADO_NEGATIVO_2026-10-27.md); predeclaración [T2/T3](https://github.com/yudocyudoc/IGC/blob/main/docs/ARENA_R3_PT06_T2_T3_PREDECLARACION_2026-10-27.md); resultado [T2/T3](https://github.com/yudocyudoc/IGC/blob/main/docs/ARENA_R3_PT06_T2_T3_RESULTADOS_REALES_2026-10-27.md). La salida técnica consolidada (JSON + SQLite) se genera en CI y se archiva como evidencia no derivada de simulaciones nuevas.
