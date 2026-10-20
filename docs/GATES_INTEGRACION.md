# Gates de integración IGC

Este documento separa la salud del laboratorio de la integración del candidato y de la evaluación científica. Un workflow verde solo acredita las aserciones que ejecuta.

| Gate | Estado de partida | Evidencia requerida | Qué no demuestra |
|---|---|---|---|
| **F0-ENG** — laboratorio y componentes | `PASS_PROVISIONAL` para las comprobaciones implementadas en Actions | Lock reproducible, pruebas y checks semánticos/OpenModelica publicados como artefactos | Cobertura integral T01–T30 o integración candidato→simulador |
| **F0-VERTICAL** — conocimiento a simulación | `PASS_SYNTHETIC` en Actions #235; PR #3 sigue sujeto a revisión del diff | Claim anclado en fuente; candidato estructurado con mecanismo y supuestos; transformación reproducible a Modelica; compilación/simulación; manifiesto con hashes y procedencia; resultado sensible a un parámetro; rechazos negativos para unidad y referencias inválidas | Validez empírica, calibración, explicación causal o mejora de fidelidad |
| **H-IGC** — utilidad/fidelidad científica | `NOT_EVALUATED` | Protocolo y gates de evaluación posteriores con evidencia independiente | No se aprueba con fixtures sintéticos ni con una compilación |

## Alcance de F0-VERTICAL

El corte actual de este gate es una instancia sintética ejecutable de SystemModelCandidate, separada del toy Modelica fijo existente. Actions #235 pasó sobre el commit `6f2bddf0c25d6e000d78fa42e2cbcde19c93849e`: 20 pruebas pasaron; las salidas finales fueron 20 y 30 orders al elevar llegadas de 3 a 4 orders/hour. El [artefacto F0](https://github.com/yudocyudoc/IGC/actions/runs/39354352547/artifacts/12234631998) conserva handoff.json, fuentes Modelica, logs y CSV. El workflow exige la carga de Modelica 4.0.0 y rechaza mensajes de error en `checkModel`. Su supuesto de promoción solo cambia un parámetro de llegadas inventado. El workflow debe generar dos modelos desde los datos del candidato, simular ambos con la misma versión fijada de OpenModelica y confirmar que la salida del stock cambia de acuerdo con la ecuación declarada.

Las pruebas negativas deben fallar antes de generar el modelo cuando falta una unidad compatible o una referencia a claim/supuesto no se resuelve. La evidencia enlaza el texto fuente, ClaimOccurrence, hipótesis, supuestos, Modelica generado, CSV de ambas simulaciones y hashes.

## Lectura del estado global

El reporte global F0 permanece `BLOCKED` mientras queden etapas F0 obligatorias como persistencia cloud sin ejecutar. Esto no cambia el estado de H-IGC. El estado de cada gate se comunica por separado; la ejecución sintética no aprueba datos, hipótesis ni mecanismos del mundo real.

## Criterio de salida del PR de handoff

El gate técnico sintético tiene estado `PASS_SYNTHETIC` por Actions #235 y sus negativos confirmados en 20 pruebas. El PR #3 sigue en borrador para revisión del diff/artefacto; este estado no promueve F0 ni aprueba H-IGC. La matriz T01–T30 conserva 0 PASS integral hasta que cada criterio tenga su propia prueba de requisito.
