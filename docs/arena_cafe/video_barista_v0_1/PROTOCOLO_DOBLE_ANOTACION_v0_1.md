# Arena Café · Protocolo prospectivo de doble anotación visual v0.1

**Fecha de declaración:** 2026-11-04 (Mexico City). **Estado:** protocolo propuesto, NO ejecutado. **Sin acceso a F5/G4/G5 ni cambios a D/B/M.**

## 1. Pregunta y objetivo limitado

¿Dos codificadores sin acceso a las etiquetas del otro identifican categorías, observaciones puntuales y ventanas temporales compatibles usando el contrato `data/arena/video_barista_v0_1/contrato/` sobre tramos de video previamente fijados?

**No medir ahora:** tiempo de servicio POS, productividad, utilización laboral o de máquinas, inventario inicial, capacidad máxima, causalidad de cuellos de botella ni mejor intervención.

## 2. Fuente, selección de ventanas y regla

Archivo de origen SHA-256 `cd37c9d3f231f4d307c4f3353ce1dc096fad4185bbdf6ffab06266b9d41290c5`, 5024.87 s de video de presentación (no tiempo físico validado). Solo vista principal; se excluye el recuadro secundario.

Seleccionar dos ventanas de 120 segundos sin consultar sus anotaciones:
- Conjunto A, inicios elegibles `[1200,1600,1900,2350]`
- Conjunto B, inicios elegibles `[3000,3300,3500,3750]`
- Índices = `int(video_sha256[0:8],16) % 4` e `int(video_sha256[8:16],16) % 4`, respectivamente.

Para este SHA, los índices son `3` y `3`; **ventanas seleccionadas: [2350,2470] y [3750,3870] s**. Los conjuntos excluyen los tramos previamente revisados a detalle P001, P004, P006, P031 y P045. El archivo, candidatos y regla se declaran antes de revisar visualmente estas ventanas para este experimento.

Este muestreo **no es aleatorio representativo** de la jornada; busca dos pruebas operativas sin selección posterior de escenas convenientes.

## 3. Anotadores y enmascaramiento

- Codificador A: una persona o modelo que no haya visto las anotaciones históricas, del video u otros revisores.
- Codificador B: otra persona o modelo, también sin ver A, y sin ver resultados o comentarios del codificador anterior.
- Ambos reciben **solo** las ventanas del MP4, vista principal, la definición de regiones y el vocabulario/JSON Schema v0.1. El administrador puede entregar instrucciones idénticas sin mostrar los archivos `barista/*.csv`, `revisiones/*.csv` o las respuestas anteriores de esta conversación.
- El asistente que ha realizado R2, R3 y R4 **no califica como revisor independiente** de aquellas escenas.
- Guardar A y B sin cambios en archivos separados, con identidad o pseudónimo de revisor y versión de protocolo, **antes** de ejecutar la comparación. Un eventual resultado posterior a discusión es adjudicación, no dato independiente.

## 4. Proceso de codificación

1. Cada codificador analiza muestras cada 2 segundos (`2350,2352,…,2470` y `3750,3752,…,3870`, incluidos extremos), conservando intervalo y referencia de fotograma. Puede añadir muestras a 1 segundo donde necesite delimitar una transición, documentando por qué.
2. Registrar estados positivos visibles, acciones visibles, transición si hay evidencia antes/después, y episodios solo con límites acotados. Usar los 23 códigos del catálogo, sin inventar códigos para POS/entrega/capacidad.
3. Registrar `DESCONOCIDO` o ausencia de evento, diferenciando entre **no observado** (mala visibilidad/oclusión) y **ausencia observada** cuando el campo sí es claramente visible. No asignar `0` a un stock por estar fuera de cuadro.
4. Para recipientes anotar **mínimo visible por muestra**, no stock absoluto ni cantidad de productos completos. Para uso de lanza distinguir `jarra_proxima_a_lanza_visible`, `jarra_sostenida_junto_a_lanza` y `vapor_activo_verificado`: este último no se declara sin criterio de evidencia adicional explícito.
5. Las referencias de evidencia siguen siendo rutas relativas hacia fotogramas preservados fuera del GitHub público. No colocar imágenes, audio ni enlace privado al repositorio.

## 5. Comparación previamente declarada

- **Integridad:** cada JSONL pasa JSON Schema y validador semántico v0.1; reportar violaciones por clase.
- **Cobertura:** proporción de muestras con región completamente visible, parcialmente visible y `DESCONOCIDO` por anotador. Mantener no emparejados y desconocidos explícitos.
- **Presencia y conteos mínimos:** tabla de desacuerdos por muestra y diferencia absoluta en conteos; no interpretar la coincidencia de conteos como capacidad de la superficie.
- **Acciones y transiciones:** compararlas por código y tiempo; se considera *coincidencia candidata* el mismo código con muestras a ≤2 s o ventanas temporales que se solapen, conservando falsos positivos y falsos negativos por ambas partes.
- **Episodios:** comparar clasificación, límites inicio/fin, solapamiento temporal e intervalos de duración compatibles; no deducir continuidad por acuerdo entre anotadores.
- **Métricas:** proporción de acuerdo, precisión/recobrado/F1 simétrico para eventos con reglas de emparejamiento explícitas y dispersión de diferencias temporales. Ningún número aislado será aprobación científica.

No hay umbral numérico de aprobación inventado de antemano: se publicará el desacuerdo íntegro y se identificará qué códigos necesitan definición adicional. No rediseñar categorías tras ver las etiquetas y después evaluar con esas mismas escenas sin declarar el cambio de versión.

## 6. Salidas obligatorias y puerta

Se esperan, después del ejercicio y **no incluidas en este PR**:
`anotador_A.jsonl`, `anotador_B.jsonl`, `reporte_acuerdo.json`, `adjudicacion_separada.json` y un informe con errores, resultados nulos, incertidumbre y decisiones.

El siguiente paso tras una concordancia suficientemente documentada sería un **adaptador observacional aislado**, que produjera restricciones como `recipientes_visibles_minimo(t)>=k`, no una simulación que complete automáticamente lo no observado.

**Puerta cerrada:** no alimentar D/B/M, no inferir parámetros físicos y no anunciar F5 validado, hasta contar con anotaciones independientes, cobertura y trazabilidad justificadas.
