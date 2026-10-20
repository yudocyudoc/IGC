# FM-B2 — ATMS sobre candidatos moleculares

**Estado:** PoC sintética en revisión; no es un motor ATMS de producción.

## Pregunta de integración

¿El probe ATMS existente conserva candidatos moleculares estructuralmente distintos cuando cada uno tiene soportes alternativos, y elimina solo la justificación cuyo entorno contiene un `nogood`?

## Flujo

1. B1 compone las estructuras seriales y las valida con LinkML.
2. Este corte vincula cada candidato y su hash estructural a supuestos y justificaciones sintéticos.
3. El probe ATMS calcula entornos mínimos consistentes. Se conservan todas las alternativas con al menos un entorno; no hay selección `top-1`.
4. Un verificador independiente reconstruye los entornos desde el plan de soportes y `nogoods`, y contrasta los hashes y referencias de estructura.

La fixture define dos justificaciones para cada candidato. Un `nogood` invalida una de CS-01; su segunda justificación permanece, al igual que las dos justificaciones de CS-02. Las estructuras y sus hashes no se modifican por el razonamiento.

## Límites

- Los supuestos y relaciones de soporte son sintéticos y explícitos; no vienen de RDF/CRMinf/SPARQL ni de evidencia real.
- `f0-atms-feasibility/0.1` es un probe de factibilidad, no una implementación retractable/versionada ni un motor seleccionado para producción.
- B2 demuestra mantenimiento de soportes sobre candidatos moleculares; no demuestra que ATMS descubra topologías o mecanismos.
- La simulación sigue siendo la evidencia B1; ejecutar únicamente candidatos seleccionados y contrastar observaciones se deja para el gate siguiente.
- No se modifica el catálogo molecular ni se evalúan licencias o fidelidad empírica.
