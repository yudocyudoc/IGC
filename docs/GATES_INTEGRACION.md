# Gates de integración IGC

Este documento separa la salud del laboratorio, el handoff sintético, el cierre de la fase y la evaluación científica. Un workflow verde acredita solo las aserciones que ejecuta.

| Gate | Estado | Evidencia / criterio | Límite |
|---|---|---|---|
| F0-ENG — laboratorio y componentes | PASS_PROVISIONAL | Locks, pruebas, validaciones RDF acotadas y Modelica verificados por Actions #248 | No cubre T01–T30 integralmente |
| F0-VERTICAL — candidato a simulación | PASS_SYNTHETIC | Actions #248: 27 pruebas; candidato tipado, handoff reproducible, sensibilidad y verificador independiente | No demuestra fidelidad empírica, calibración ni causalidad |
| Integración semántica/ATMS → modelador | NOT_YET_INTEGRATED | Los checks semánticos y la sonda ATMS corren en el mismo workflow | El generador no consume una conclusión CRMinf/PROV/SPARQL ni la selección de supuestos del ATMS |
| F0 — cierre de fase | TECHNICAL_REVIEW_ACCEPTED; FORMAL_AUTHORIZATION_PENDING | Dictamen del 2026-10-20 acepta F0-VERTICAL en su alcance sintético; PR #1 y PR #3 son las evidencias principales para revisión formal | La aceptación técnica no fusiona PRs ni completa la plataforma |
| H-IGC — utilidad/fidelidad científica | NOT_EVALUATED | Requiere protocolo experimental y evidencia posterior | Fixtures sintéticos no evalúan hipótesis científicas |
| Plataforma completa | INCOMPLETE | F1–F9 siguen su secuencia; la persistencia cloud está planificada en F8 | No es una dependencia para aceptar los gates técnicos de F0 |

## Alcance demostrado por F0-VERTICAL

El recorrido implementado es:
ClaimOccurrence anclado en fuente → SystemModelCandidate estructurado → hipótesis de mecanismo y supuestos sintéticos → generación de dos modelos Modelica → simulación → manifiesto con hashes → verificación independiente.

El generador acepta deliberadamente solo la estructura single_stock y usa una ecuación stock-flow predeterminada. La etapa semántica y la sonda ATMS se ejecutan antes en el mismo workflow, pero no gobiernan ni alimentan la construcción del candidato. La integración de esa decisión corresponde a F2/F3; esta limitación no invalida el gate F0-VERTICAL acotado.

La perturbación cambia llegadas de 3 a 4 pedidos/hora. OpenModelica debe producir toda la trayectoria esperada desde el valor inicial hasta el resultado final: 20 y 30 pedidos, respectivamente, tras 10 horas. Se verifica cada muestra y su tiempo, no solo el último valor. Los negativos rechazan unidades/parámetros/referencias inválidas.

## Integridad del handoff

La operación verify-handoff relee el manifiesto y verifica las rutas y hashes de fuente, claim, candidato, generador, ambos modelos y ambos CSV. También valida las referencias de entidad y vuelve a calcular toda la trayectoria de cada CSV contra los parámetros y duración declarados.

La suite modifica un archivo Modelica y una muestra interior del CSV; el verificador debe detectar ambos cambios, incluso si el hash del manifiesto se actualiza para la muestra alterada. Actions guarda handoff.json, verification.json, fuentes Modelica, logs y CSV en el artefacto F0.

## F0 y la integración cloud de F8

D1/R2 son integración cloud planificada en F8, no requisito de aceptación de F0. La corrida F0 marca esa etapa OUT_OF_SCOPE; si los gates técnicos requeridos pasan, el resultado de la spike es PASS_WITH_LIMITATIONS y la plataforma queda INCOMPLETE. El dictamen técnico del 2026-10-20 acepta el alcance de F0-VERTICAL y cierra su discusión técnica. La revisión formal de F0 y la autorización del investigador siguen pendientes; PR #1 y PR #3 son las evidencias principales. Los PR permanecen sin fusionar.

El artefacto verificado en Actions #248 corresponde al commit `b669a3015375db805d28733177c7c5805ebcfe8e`; conserva `handoff.json`, `verification.json`, fuentes Modelica, logs y CSV. El resultado reportado fue 20 pedidos base y 29.99999999999999 perturbado al cabo de 10 horas. Actions #247 (#748880e) es la corrida previa; #239, #235 y #238 son antecedentes históricos.

## Revisión técnica y formal de F0

El dictamen del 2026-10-20 acepta técnicamente F0-VERTICAL como PASS_SYNTHETIC y recomienda cerrar su discusión técnica. La evidencia principal para la revisión formal de fase es PR #1 (inventario, laboratorio y componentes) junto con PR #3 (candidato, handoff y simulación). F0-ENG permanece PASS_PROVISIONAL; la aceptación formal y la autorización del investigador aún están pendientes. Los PR #1, #2 y #3 no se fusionan hasta esa autorización.

La aceptación técnica de F0 no evalúa H-IGC ni completa la plataforma. Tras la autorización formal, la secuencia prevista continúa con F1a (#2) y luego F2/F3, donde se conectarán los contratos semánticos y el razonamiento ATMS. El objetivo posterior es experimentar con configuraciones de conocimiento estructurado, ATMS, embeddings y modelos SD; no ampliar artificialmente la ecuación sintética de F0. La persistencia cloud corresponde a F8.
