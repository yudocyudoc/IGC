# FM-B2 — ATMS sobre candidatos moleculares

**Estado:** `B2_ATMS_MOLECULAR_SUPPORT_PASS_SYNTHETIC` en Actions #1, commit `93b72fb0d2de8e5c558b6556b924ac2c9ac1b07a`.

## Pregunta de integración

¿El probe ATMS existente conserva candidatos moleculares estructuralmente distintos cuando cada uno tiene soportes alternativos, y elimina solo la justificación cuyo entorno contiene un `nogood`?

## Flujo

1. B1 compone las estructuras seriales y las valida con LinkML.
2. Este corte vincula cada candidato y su hash estructural a supuestos y justificaciones sintéticos.
3. El probe ATMS calcula entornos mínimos consistentes. Se conservan todas las alternativas con al menos un entorno; no hay selección `top-1`.
4. Un verificador independiente reconstruye los entornos desde el plan de soportes y `nogoods`, y contrasta los hashes y referencias de estructura.

La fixture define dos justificaciones para cada candidato. Un `nogood` invalida una de CS-01; su segunda justificación permanece, al igual que las dos justificaciones de CS-02. Las estructuras y sus hashes no se modifican por el razonamiento.

Actions #1 conservó ambos candidatos: CS-01 con un entorno mínimo de soporte y CS-02 con dos. El verificador reconstruyó independientemente las etiquetas y confirmó la relación de cada candidato con su estructura y hash. [Ejecución y artefacto](https://github.com/yudocyudoc/IGC/actions/runs/39463491064).

## Límites

- Los supuestos y relaciones de soporte son sintéticos y explícitos; no vienen de RDF/CRMinf/SPARQL ni de evidencia real.
- `f0-atms-feasibility/0.1` es un probe de factibilidad, no una implementación retractable/versionada ni un motor seleccionado para producción.
- B2 demuestra mantenimiento de soportes sobre candidatos moleculares; no demuestra que ATMS descubra topologías o mecanismos.
- La simulación sigue siendo la evidencia B1; ejecutar únicamente candidatos seleccionados y contrastar observaciones se deja para el gate siguiente.
- No se modifica el catálogo molecular ni se evalúan licencias o fidelidad empírica.
