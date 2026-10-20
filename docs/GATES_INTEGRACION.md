# Gates de integración IGC

Este documento separa la salud del laboratorio, el handoff sintético, el cierre de la fase y la evaluación científica. Un workflow verde acredita solo las aserciones que ejecuta.

| Gate | Estado | Evidencia / criterio | Límite |
|---|---|---|---|
| F0-ENG — laboratorio y componentes | PASS_PROVISIONAL | Locks, pruebas, validaciones RDF acotadas y Modelica verificados por Actions #450 | No cubre T01–T30 integralmente |
| F0-VERTICAL — candidato a simulación | PASS_SYNTHETIC | Actions #250: 27 pruebas; candidato tipado, handoff reproducible, sensibilidad y verificador independiente | No demuestra fidelidad empírica, calibración ni causalidad |
| ATMS → selección → handoff | PASS_SYNTHETIC (PR #5; Actions #2) | Actions #2 (run 39365713141): 5 pruebas; el nogood poda el baseline y OpenModelica obtiene 30/40 pedidos para el candidato seleccionado y su perturbación; artefacto 12238439065 | El probe ATMS sigue siendo prototipo; no consume conclusiones RDF/CRMinf/SPARQL ni demuestra semántica empírica |
| F2b/F3 — RDF/CRMinf → SPARQL → ATMS | PENDING_ACTIONS (PR #6 propuesto) | Formalización sintética con claim, PROV-O y CRMinf; consulta SPARQL debe alimentar propuestas y selección | No afirma inferencia empírica ni causalidad; nogoods siguen declarados en fixture |
| F0 — fase | ACCEPTED_WITH_LIMITATIONS | Investigador autorizó e integró PR #1 y #3 en `main` el 2026-10-20 | No completa la plataforma ni evalúa H-IGC |
| H-IGC — utilidad/fidelidad científica | NOT_EVALUATED | Requiere protocolo experimental y evidencia posterior | Fixtures sintéticos no evalúan hipótesis científicas |
| Plataforma completa | INCOMPLETE | F1–F9 siguen su secuencia; la persistencia cloud está planificada en F8 | No es una dependencia para aceptar los gates técnicos de F0 |

## Alcance demostrado por F0-VERTICAL

El recorrido implementado es:
ClaimOccurrence anclado en fuente → SystemModelCandidate estructurado → hipótesis de mecanismo y supuestos sintéticos → generación de dos modelos Modelica → simulación → manifiesto con hashes → verificación independiente.

El generador acepta deliberadamente solo la estructura single_stock y usa una ecuación stock-flow predeterminada. La etapa semántica F0 aún corre por separado. El incremento F3 (PR #5) conecta la sonda ATMS al selector: justificaciones derivan etiquetas de soporte, nogoods podan alternativas y solo candidatos soportados se entregan al handoff. El fixture tiene dos variantes sintéticas de una misma estructura single_stock; el gate demuestra que la decisión ATMS cambia candidato y tasa de llegada, no composición estructural abierta. El probe sigue sin retractación/versionado ni selección de motor de producción. La salida no es evidencia de causalidad o fidelidad.

La perturbación cambia llegadas de 3 a 4 pedidos/hora. OpenModelica debe producir toda la trayectoria esperada desde el valor inicial hasta el resultado final: 20 y 30 pedidos, respectivamente, tras 10 horas. Se verifica cada muestra y su tiempo, no solo el último valor. Los negativos rechazan unidades/parámetros/referencias inválidas.

## Integridad del handoff

La operación verify-handoff relee el manifiesto y verifica las rutas y hashes de fuente, claim, candidato, generador, ambos modelos y ambos CSV. También valida las referencias de entidad y vuelve a calcular toda la trayectoria de cada CSV contra los parámetros y duración declarados.

La suite modifica un archivo Modelica y una muestra interior del CSV; el verificador debe detectar ambos cambios, incluso si el hash del manifiesto se actualiza para la muestra alterada. Actions guarda handoff.json, verification.json, fuentes Modelica, logs y CSV en el artefacto F0.

## F0 y la integración cloud de F8

D1/R2 son integración cloud planificada en F8, no requisito de aceptación de F0. La corrida F0 marca esa etapa OUT_OF_SCOPE; si los gates técnicos requeridos pasan, el resultado de la spike es PASS_WITH_LIMITATIONS y la plataforma queda INCOMPLETE. El dictamen técnico del 2026-10-20 acepta el alcance de F0-VERTICAL y cierra su discusión técnica. La autorización formal fue otorgada y PR #1/#3 quedaron integrados. F0 se acepta con limitaciones.

La evidencia de F0-VERTICAL en Actions #250 corresponde al commit `19fb16723d02352b14e0d394573d57fcaa0e013d`; conserva `handoff.json`, `verification.json`, fuentes Modelica, logs y CSV. El resultado reportado fue 20 pedidos base y 29.99999999999999 perturbado al cabo de 10 horas. Actions #247 (#748880e) es la corrida previa; #239, #235 y #238 son antecedentes históricos.

## Revisión técnica y formal de F0

El dictamen del 2026-10-20 acepta técnicamente F0-VERTICAL como PASS_SYNTHETIC. PR #1 y PR #3 se integraron en main con autorización del investigador; F0 queda ACCEPTED_WITH_LIMITATIONS. F0-ENG permanece PASS_PROVISIONAL.

La aceptación técnica de F0 no evalúa H-IGC ni completa la plataforma. PR #2 y el seguimiento PR #4 integraron el corte inicial F1a. Continúan los contratos semánticos F2 y el razonamiento ATMS F3. El objetivo posterior es experimentar con configuraciones de conocimiento estructurado, ATMS, embeddings y modelos SD; no ampliar artificialmente la ecuación sintética de F0. La persistencia cloud corresponde a F8.


## F1a temporal

PR #2 implementó el contrato LinkML y ledger SQLite local; PR #4 añadió `recorded_at` monotónico por entidad. Actions #253 validó 40 pruebas combinadas F0/F1a. El corte sigue siendo sintético y no productivo.


## Incremento F3: selección ATMS conectada al handoff

El workflow `F3 ATMS candidate handoff` (run #4) pasó y generó `selection.json`, el candidato seleccionado, el manifiesto del handoff y la verificación de OpenModelica. La suite comprueba que el nogood elimina el candidato baseline, que sin nogood coexisten las dos alternativas, y que referencias o valores inválidos fallan cerrados. La selección se conserva dentro del candidato hasheado y el manifiesto enlaza esa evidencia.

Este incremento no cierra F3a/F3b: usa el probe F0 explícitamente no productivo, no procesa salidas semánticas RDF/CRMinf/SPARQL, y no compone estructuras SD distintas. La integración semántica, retractación/versionado, conformance del ATMS y modelos estructuralmente rivales quedan pendientes.


## Puente semántico F2b/F3 — PR #6 propuesto

El siguiente corte construye una formalización RDF sintética del ClaimOccurrence anclado, registra la actividad de formalización como PROV-O/CRMinf y usa SPARQL para recuperar solo las propuestas ligadas a esa afirmación. Las propuestas recuperadas, su procedencia y el resultado de la consulta pasan al selector ATMS y de ahí a OpenModelica. Sigue siendo una traducción explícita de fixture: no prueba una inferencia empírica, deja nogoods declarados y no convierte el resultado en verdad causal.