# Decisión de inventario ATMS — F0

**Fecha de evaluación:** 2026-10-19  
**Decisión:** no seleccionar un motor de producción durante F0. Mantener el probe propio como evidencia de viabilidad, sin promoverlo a motor de IGC. Llevar la selección y prueba de conformidad a F3.

## Requisito del sistema

El motor debe mantener, por nodo, etiquetas de entornos mínimos de supuestos; combinar justificaciones; mantener conjuntos nogood y eliminar sus superconjuntos; propagar retractaciones/versiones de justificaciones; detectar ciclos o convergencia; permitir explicaciones; preservar la coexistencia de candidatos compatibles; y ofrecer límites explícitos de memoria/tiempo. Debe tener pruebas de conformance contra los contratos IGC y ser invocable desde el ledger de justificaciones versionadas.

## Candidatos revisados por capacidad

| Candidato | Evidencia primaria | Ajuste al requisito | Resultado |
|---|---|---|---|
| Probe F0 de IGC | scripts/f0_atms_probe.py y tests/test_f0_spike_contract.py | Etiquetas mínimas, propagación Horn y poda de nogood; no conserva retractación/versionado ni ofrece semántica completa | Sólo prueba de viabilidad; no producción |
| ATMS-in-Python (FellnerDotDev) | https://github.com/FellnerDotDev/ATMS-in-Python — README y atms_algo.py | El propio README declara que el algoritmo no está completo; código de demostración sobre reglas Horn, sin interfaz mantenida de retractación/explicación/conformance para IGC | Rechazado para integración de producción |
| pisanuw/ltms | https://github.com/pisanuw/ltms — README y PLAN.md | Declara como no objetivo portar ATMS; implementa LTMS/BCP y JTMS/LTRE, que no sustituyen semánticamente el contrato ATMS | No candidato ATMS; excluir de comparativa |

## Resultado y trabajo F3

La implementación propia F0 confirma sólo dos comportamientos acotados: alternativas no declaradas incompatibles pueden coexistir, y un nogood explícito elimina una etiqueta inconsistente. No acredita retractación, ciclo de vida de justificaciones, concurrencia, persistencia, escalabilidad ni completitud del ATMS.

F3 debe comparar:
1. Una implementación ATMS fiel con soporte verificable para los contratos anteriores, si aparece una mantenida y compatible.
2. Una implementación del núcleo ATMS del proyecto con semántica/documentación de referencia y suite de conformidad propia.

El equipo debe elegir por resultados reproducibles de conformance, retractación, explicación, convergencia y límites medidos; registrar por separado la decisión de licencia en la revisión final de terceros. No seleccionar LTMS por compartir el nombre genérico TMS ni copiar un algoritmo de juguete sin ampliar sus pruebas.

## Fuentes consultadas

- https://github.com/FellnerDotDev/ATMS-in-Python
- https://github.com/pisanuw/ltms
- de Kleer, “Problem solving with the ATMS”, Artificial Intelligence 28(2), 1986, https://doi.org/10.1016/0004-3702(86)90082-2
