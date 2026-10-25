# ARENA — System Dynamics System Prompt v2 (propuesta pre-experimental)

**Estado:** `DRAFT_NOT_ACTIVE`. Texto íntegro ejecutable: [`data/prompts/arena_sd_system_v2.txt`](../data/prompts/arena_sd_system_v2.txt). El prompt fue añadido de forma independiente: **no modifica** `data/diagnostics/glm53_nw2_config_probe_request.json`, las llamadas V4 ya efectuadas, los reportes NW1/NW2, la reserva o PredictionLock.

## Propósito

El `system` anterior era una instrucción de rol y esquema JSON con escasa disciplina dinámica. V2 demanda una evaluación causal de fronteras, stocks/flows, conservación, retardos, estados iniciales, dimensiones, observabilidad y falsación de estructuras rivales; no exige inventar feedback no sustentado. Mantiene los mismos cinco campos JSON y restricciones de catálogo, fuente y ceguera.

### Soporte conceptual

- Naugle, Langarudi y Clancy (2024), *System Dynamics Review*, DOI [10.1002/sdr.1762](https://doi.org/10.1002/sdr.1762): dinámica de sistemas cuantitativa se caracteriza por estructuras causales de feedback, acumulaciones/demoras, modelos en ecuaciones, tiempo continuo y análisis de dinámicas de realimentación.
- MIT System Dynamics (Sterman), [material didáctico](https://live.ocw.mit.edu/courses/res-15-004-system-dynamics-systems-thinking-and-modeling-for-a-complex-world-january-iap-2020/65a2dc7433fcb6cce64b55da0342f0c0_MITRES15_004IAP20_slides.pdf): separación de eventos, patrones y estructura; stocks-flows, retrasos, información y límites.
- System Dynamics Learning Guide, [validación](https://pressbooks.lib.jmu.edu/sdlearningguide/chapter/chapter-5/): una buena réplica de la conducta no establece la estructura verdadera; pruebas dimensionales y estructurales son necesarias.

## Qué NO promete

1. El prompt no cambia el catálogo fijo `CS-01`/`CS-02`: **no demuestra descubrimiento de mecanismos nuevos**. Los mecanismos fuera del catálogo sólo pueden expresarse como incertidumbre.
2. No sustituye las ecuaciones, pruebas físicas de OpenModelica ni el filtro G3. Exigir razonamiento de stocks-flows no significa que el texto del modelo sea una deducción válida.
3. La elección de ambos modelos sigue siendo científicamente admisible cuando los datos no identifican la estructura. No puntuar indebidamente a V2 por podar más modelos.
4. No usar NW2 ya conocido para optimizar el prompt hasta obtener la selección deseada. Las pruebas NW2 de conectividad no cuentan como evidencia comparativa de calidad.

## Diseño del próximo contraste (pendiente de autorización)

Comparar `S_baseline` (system previamente congelado) vs `S_SD_v2` en **mundos nuevos**, con la misma vista pública, catálogo, temperatura, `reasoning_effort`, límite de salida y sin revelar la reserva. Congelar la asignación, todos los prompts, versiones y criterios de puntuación **antes** de inferir. Medir por separado:
- JSON válido, cumplimiento de IDs y prohibiciones, tokens/costo.
- Calidad de la explicación dinámica mediante un criterio preregistrado que no premie vaguedad o verbosidad.
- Poder de discriminación real: falsaciones justificadas, rendimiento predictivo tras la misma calibración y el mismo G3, comparado también con `D` (enumeración).
- Falsos descartes, sobreconfianza causal y abstenciones, no sólo aciertos.

La configuración de V2 todavía NO se ha ejecutado contra Cloudflare. La próxima solicitud será nueva y precongelada; nunca una reescritura del recibo NW2.
