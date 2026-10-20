# Gates de integración IGC

Este documento separa la salud del laboratorio, el handoff sintético, el cierre de la fase y la evaluación científica. Un workflow verde acredita solo las aserciones que ejecuta.

| Gate | Estado | Evidencia / criterio | Límite |
|---|---|---|---|
| F0-ENG — laboratorio y componentes | PASS_PROVISIONAL | Locks, pruebas, validaciones RDF acotadas y Modelica verificados por Actions #239 | No cubre T01–T30 integralmente |
| F0-VERTICAL — candidato a simulación | PASS_SYNTHETIC | Actions #239: 21 pruebas; candidato tipado, handoff reproducible, sensibilidad y verificador independiente | No demuestra fidelidad empírica, calibración ni causalidad |
| Integración semántica/ATMS → modelador | NOT_YET_INTEGRATED | Los checks semánticos y la sonda ATMS corren en el mismo workflow | El generador no consume una conclusión CRMinf/PROV/SPARQL ni la selección de supuestos del ATMS |
| F0 — cierre de fase | PENDING_FORMAL_REVIEW | Revisar PR #1 y PR #3, evidencias, inventario y límites declarados | La revisión de fase es independiente de H-IGC |
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

D1/R2 son integración cloud planificada en F8, no requisito de aceptación de F0. La corrida F0 marca esa etapa OUT_OF_SCOPE; si los gates técnicos requeridos pasan, el resultado de la spike es PASS_WITH_LIMITATIONS y la plataforma queda INCOMPLETE. F0 aún requiere revisión formal de fase; no se declara completa solo por Actions verde.

El artefacto verificado en Actions #239 corresponde al commit 66953076bed8d9767f81ef3cd48c81fbc2310373. Actions #235 y #238 son corridas históricas anteriores; la referencia vigente debe actualizarse al cerrar las mejoras de este PR.

## Criterio para el cierre de fase

F0 puede proponerse para cierre técnico con F0-ENG PASS_PROVISIONAL y F0-VERTICAL PASS_SYNTHETIC, inventario y límites documentados y revisión del investigador. Esto no promueve a main ni evalúa H-IGC. No se requiere configurar servicios cloud reales; estos pertenecen a F8.
