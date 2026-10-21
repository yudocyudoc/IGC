# FM-12/13 — Ablación ATMS e interfaz para LLM

**Estado previsto:** evaluación sintética de reglas de soporte; utilidad de respuestas LLM aún no evaluada.

## Pregunta

¿Qué añade el ATMS frente a un filtro de `nogoods` y un cierre explícito OR/AND, al mantener soportes alternativos para candidatos? Como pregunta separada, ¿la representación de etiquetas y justificaciones del ATMS permite a un LLM explicar mejor por qué un candidato sobrevive o pierde soporte?

## Diseño de la ablación

Las tres condiciones reciben los mismos supuestos, reglas y restricciones sintéticas.

| Escenario | Comparación | Resultado correcto esperado |
| --- | --- | --- |
| S0 | Filtro directo por subconjunto de `nogood`, cierre OR/AND y probe ATMS | Mismas etiquetas; `ATMS_VALUE_ADDED=NOT_DEMONSTRATED` |
| S1 | Dos justificaciones independientes para una conclusión; un `nogood` elimina solo una ruta | La conclusión conserva la etiqueta mínima de la ruta alternativa |

El cálculo OR/AND es una implementación transparente de punto fijo y el ATMS usa el probe `f0-atms-feasibility/0.1`. Las salidas se comparan como conjuntos de entornos mínimos. Esto mide corrección funcional en estas fixtures, no superioridad general, escalabilidad ni retractación/versionado.

S0 usa filtro directo porque cada candidato tiene una justificación conjuntiva explícita. S1 introduce conclusiones intermedias, dos rutas independientes y una incompatibilidad parcial. Allí se compara ATMS con el cierre OR/AND; el filtro booleano simple solo informa estado del candidato y pierde la explicación de la ruta que queda.

## Interfaz para el LLM: condición separada

El workflow prepara tres paquetes comparables: etiquetas y reglas de soporte ATMS; estado booleano del filtro sencillo; y conclusiones con traza OR/AND. Las preguntas son idénticas para cada condición e incluyen criterios de contenido requerido y afirmaciones prohibidas. Los paquetes conservan la condición sintética, un hash del plan y límites epistemológicos.

No hay un proveedor ni credenciales de inferencia LLM configurados para este workflow. Por ello, genera la interfaz y el protocolo de evaluación, pero informa `NOT_EVALUATED_NO_MODEL_PROVIDER_CONFIGURED` para calidad de respuestas. No atribuye utilidad al LLM a partir de la mera serialización de contexto.

Para evaluar respuestas en una iteración posterior, usar el mismo modelo y versión, las mismas preguntas y presupuesto, registrar prompt/entrada/salida/latencia/tokens, aleatorizar y ocultar los nombres de condición a quienes puntúan, y medir exactitud factual, cobertura de soporte, referencias, abstenciones y afirmaciones causales indebidas. El evaluador no debe revelar la respuesta esperada al modelo.

## Resultado y límites

El veredicto de ingeniería se limita a que el probe ATMS y el cierre de reglas producen etiquetas correctas en S0/S1. Si coinciden, el valor añadido lógico de ATMS permanece `NOT_DEMONSTRATED`; la trazabilidad de rutas y actualización incremental pueden seguir siendo diferencias de interfaz a medir. No se concluye que ATMS razone mejor que reglas sencillas ni que un LLM responda mejor con su salida.

Todas las entradas son sintéticas y preparadas a mano. El experimento no conecta RDF/CRMinf/SPARQL, no aprende soportes desde evidencia, no selecciona mecanismos del mundo real y no evalúa la hipótesis científica H-IGC. La fidelidad causal y empírica no se evalúa.
