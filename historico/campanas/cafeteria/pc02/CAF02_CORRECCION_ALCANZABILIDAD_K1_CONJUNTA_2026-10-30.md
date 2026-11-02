# CAF-02 · Corrección de la adquisición K1 conjunta M+D

**Fecha:** 2026-10-30. **Estado:** estudio interno de alcance del dominio + corrección propuesta de política. **NO** es un preregistro con testigo externo; no habilita DES, OMC, Buffalo, ni lectura de K2.

## Problema comprobado

En el protocolo del PR #102, cada envolvente K1 se ampliaba ±(0.75+0.02) = **±0.77 pedidos**. Para garantizar que los intervalos familiares completos no se superpusieran y superar la brecha requerida de 0.05, la distancia inicial debía ser al menos **1.59 pedidos**. El selector M exigía esa garantía *antes* de autorizar K1.

Astra examinó las **70** combinaciones K0 enteras y materialmente posibles, dadas las entradas designadas: 0≤D5≤6, D5≤D10≤12. Identificó 49 sin ambas familias M, 21 con ambas pero sin separación robusta, y **0 ejecuciones K1 habilitadas**. Esta condición de activación impedía prácticamente la pregunta central: **observar si M y D actualizan sus hipótesis con evidencia pertinente**. Que un test verifique las dos ramas de un `if` no demuestra que la rama deseada sea alcanzable dentro de la entrada admisible.

La corrección **NO altera** las tolerancias: K1 residual ±0.75, guardia numérica 0.02, total ±0.77; el umbral de separación robusta 0.05 queda como diagnóstico de identificación, no como permiso para recolectar evidencia.

## Nueva pregunta experimental y regla de diseño

**Pregunta de adquisición:** ¿qué medición K1, dentro del mismo menú, ofrece mayor **potencial de reducir alternativas compatibles**, aun cuando no garantice identificar una estructura única?

M mantiene C00/C01 y D mantiene D1/D2/D3 y sus rejillas originales del PR #103. Ambos reciben **exactamente dos conteos K0 públicos**, sin futuros valores de construcción ni información del generador. Para cada una de las tres opciones existentes (1.0,t10), (1.5,t20), (1.8,t30), el software calcula las entregas previstas de **cada miembro K0 compatible de ambos brazos**. No inventa una distribución poblacional. Se asignan pesos convencionales de diseño:

1. Cada brazo activo (M/D) recibe el mismo peso al agregarse el índice común.
2. Dentro de cada brazo, cada **familia estructural** adecuada recibe el mismo peso.
3. Dentro de esa familia, sus configuraciones conservadas reciben el mismo peso.
4. Para cada candidato, el número hipotético de entregas se obtiene redondeando su pronóstico a entero, con mitades hacia arriba; no se consulta el mundo.
5. Con ese valor hipotético, se calcula el peso de los candidatos de su brazo que **serían descartados** por un residual superior a 0.77. Se promedia sobre los resultados hipotéticos ponderados y luego sobre brazos activos. Gana la opción del menú con mayor índice; empate por orden A→B→C.

**Esta media no es una probabilidad real de identificar la estructura**: es un criterio reproducible de preferencia entre tres preguntas, condicionado a una mezcla hipotética de candidatos. Se informarán tanto el score M como el score D; una mayor dispersión de la rejilla o la duplicación de alias no se interpreta como confirmación científica.

**Activación predeclarada:** si al menos uno de los brazos conserva **un candidato** adecuado en K0, se autoriza *en el protocolo propuesto* escoger **una** K1 común. Si el índice de reducción potencial es cero, elegir la primera opción A y registrar `K1_PRECOMMITTED_NO_MODELLED_REDUCTION_ADEQUACY_TEST`: puede refutar modelos, pero no se pronostica reducción. Si **ningún** método conserva candidatos, no se consume K1: `K1_NO_ADEQUATE_HYPOTHESIS_NO_TRIAL`. Independientemente del resultado, solo se permite un pulso K1 precomprometido en G4a.

**Revisión posterior idéntica por brazo:** cada uno filtra **sus propios supervivientes K0** con `abs(predicción_K1-observación_entera)≤0.77`, sin añadir rejilla, sin cambiar el pulso y sin reconstruir hipótesis. El selector conjunto vincula un hash de la política y sendos hashes de los conjuntos calibrados K0; un revisor no puede presentar como precomprometida una decisión tomada sobre otro K0.

## Recuento exhaustivo de entrada admisible (software, NO mundos)

`caf02_joint_md_k1_design.py` enumera los 70 pares D5/D10 y ejecuta **los calibradores existentes** de M y D y **los selectores antiguo y corregido**. El cálculo usa únicamente las ecuaciones de los candidatos, no datos reservados.

| Categoría | Pares K0 |
|---|---:|
| Total físicamente admisibles | **70** |
| K0 con ambas familias M | **21** |
| **Viejo selector** M con garantía de separación: K1 elegida | **0** |
| **Nuevo selector** M+D con K1 precomprometible | **44** |
| De esos 44, reducción hipotética positiva | **43** |
| De esos 44, K1 solo para comprobar adecuación | **1** |
| Ningún modelo adecuado en M ni D; sin K1 | **26** |

**Interpretación:** se corrigió un fallo de **alcanzabilidad del ensayo**, no se ha demostrado que el mundo futuro vaya a favorecer a un modelo, identificar familias o mejorar K2. La diferencia entre 0/70 y 44/70 corresponde a **reglas experimentales distintas**, no es mejora empírica de predicción. Estos son 70 estados de entrada posibles, no réplicas independientes ni un resultado de poder estadístico. No se alteró el generador del mundo para seleccionar un caso favorable.

## Comparabilidad convencional y desenlaces negativos

REF-CAF y REF-SCALE se mantienen en su versión **K0-only** y nunca ven K1, mientras M/D recibirían información posterior. Se declaran como referencias **sin actualización**. Si M o D supera una referencia en K2, no se puede adjudicar esa diferencia específicamente al método; parte o toda podría explicarse por haber recibido información adicional. La comparación informativa primaria es **K0 vs K1 dentro de cada brazo**, con la misma regla de pérdida predeclarada y evaluada sobre el mismo K2, más una comparación descriptiva M vs D tras recibir idéntica K1. Una comparación metodológica contra referencias que también se actualizan requeriría otro protocolo; no se introduce ahora.

Se publicarán los casos negativos: K0 sin representación; K1 sin reducción real pese a tener un score positivo; K1 conserva dos o más familias; K1 elimina todas; falso descarte del generador fuera de rejilla o dentro de ella; K2 sin mejora, o peor; discrepancias de modelo agregado versus conteos discretos; fallos G2/ATMS/custodia. **Una medición permite aprender incluso cuando no identifica la estructura completa.**

## Archivos y frontera

- `caf02_joint_md_k1_design.py`: regla compartida, hashes y barrido de las 70 entradas admitidas.
- `test_caf02_joint_md_k1_design.py`: pruebas del selector, revisión M+D con el mismo K1 y rechazo de entradas incompatibles.
- `caf02_structural_k0k1k2.py` y `caf02_d_k0k1k2_adapter.py`: aceptación del nuevo compromiso y validación de su linaje antes de revisar.
- `CAF02_INDEPENDENT_K0K1K2_POLICY_PROPOSAL_2026-10-30.json`: mismo dominio, menú y tolerancia; cambia **solo la política de adquisición** y el papel de D.
- `CAF02_PROTOCOLO_INDEPENDIENTE_K0_K1_K2_PROPUESTA_2026-10-30.md`: pregunta y criterio de evaluación K2 corregidos.

**La comprobación offline y la integración matemática no equivalen a G5/G4, G2 nativo, persistencia real ATMS ni un experimento DES independiente.** CAF-01 no se reabre, E1 y la gramática histórica de D no cambian.
