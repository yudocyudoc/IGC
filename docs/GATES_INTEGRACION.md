# Gates de integración IGC

Este documento separa la salud del laboratorio de la integración del candidato y de la evaluación científica. Un workflow verde solo acredita las aserciones que ejecuta.

| Gate | Estado de partida | Evidencia requerida | Qué no demuestra |
|---|---|---|---|
| **F0-ENG** — laboratorio y componentes | `PASS_PROVISIONAL` para las comprobaciones implementadas en Actions | Lock reproducible, pruebas y checks semánticos/OpenModelica publicados como artefactos | Cobertura integral T01–T30 o integración candidato→simulador |
| **F0-VERTICAL** — conocimiento a simulación | `BLOCKED` hasta que el PR de handoff pase en Actions y se revise | Claim anclado en fuente; candidato estructurado con mecanismo y supuestos; transformación reproducible a Modelica; compilación/simulación; manifiesto con hashes y procedencia; resultado sensible a un parámetro; rechazos negativos para unidad y referencias inválidas | Validez empírica, calibración, explicación causal o mejora de fidelidad |
| **H-IGC** — utilidad/fidelidad científica | `NOT_EVALUATED` | Protocolo y gates de evaluación posteriores con evidencia independiente | No se aprueba con fixtures sintéticos ni con una compilación |

## Alcance de F0-VERTICAL

El candidato de este gate es una instancia sintética ejecutable de SystemModelCandidate, separada del toy Modelica fijo existente. Su supuesto de promoción solo cambia un parámetro de llegadas inventado. El workflow debe generar dos modelos desde los datos del candidato, simular ambos con la misma versión fijada de OpenModelica y confirmar que la salida del stock cambia de acuerdo con la ecuación declarada.

Las pruebas negativas deben fallar antes de generar el modelo cuando falta una unidad compatible o una referencia a claim/supuesto no se resuelve. La evidencia enlaza el texto fuente, ClaimOccurrence, hipótesis, supuestos, Modelica generado, CSV de ambas simulaciones y hashes.

## Lectura del estado global

El reporte global F0 permanece `BLOCKED` mientras queden etapas F0 obligatorias como persistencia cloud sin ejecutar. Esto no cambia el estado de H-IGC. El estado de cada gate se comunica por separado; la ejecución sintética no aprueba datos, hipótesis ni mecanismos del mundo real.

## Criterio de salida del PR de handoff

Se puede proponer `F0-VERTICAL = PASS_SYNTHETIC` después de Actions verde en la cabeza del PR, revisión del manifiesto y confirmación de los negativos. La matriz T01–T30 conserva 0 PASS integral hasta que cada criterio tenga su propia prueba de requisito.
