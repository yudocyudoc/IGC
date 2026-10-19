# Registro de terceros y estándares

**Estado:** inventario de candidatos, todavía no aprobación de dependencias. La revisión de licencias, versiones, hashes, mantenimiento y compatibilidad es pendiente de F0.

| Componente | Uso propuesto | Referencia disponible | Estado en IGC |
|---|---|---|---|
| CIDOC CRM / CRMinf / CRMsci | Interoperabilidad semántica y epistemológica | https://cidoc-crm.org/ ; https://cidoc-crm.org/crminf/ModelVersion/crminf-1.2.1 | Referenciado en v0.2; versión compatible, licencia/artefactos y perfil LinkML pendientes de verificación. |
| PROV-O | Procedencia de entidades, actividades y agentes | https://www.w3.org/TR/prov-o/ | Estándar objetivo; mapeo y pruebas pendientes. |
| W3C Web Annotation | Anclaje a fragmentos de fuentes | https://www.w3.org/TR/annotation-model/ | Estándar objetivo; round-trip pendiente. |
| RDF / JSON-LD / SPARQL / OWL | Grafo semántico, serialización, consultas y vocabularios | https://www.w3.org/TR/rdf11-concepts/ ; https://www.w3.org/TR/json-ld11/ ; https://www.w3.org/TR/sparql11-query/ | Motores, versiones y licencias no seleccionados. |
| SHACL | Validación de grafos | https://www.w3.org/TR/shacl/ | Recomendación objetivo; versión de motor y suite de conformidad pendientes. SHACL 1.2 aparece como borrador en la especificación y no se adopta por defecto. |
| LinkML | Esquema fuente y generación de modelos | https://linkml.io/linkml/ | Candidato; no instalado en el entorno consultado. |
| ATMS | Justificación por conjuntos de supuestos y nogoods | Candidatos de implementación por evaluar según la especificación §10 | Sin biblioteca seleccionada; conformance, licencia y límites pendientes. |
| OpenModelica | Formalización y simulación obligatoria | https://openmodelica.org/download/docker/ | `omc` y Docker no detectados en PATH del entorno; versión, licencia/distribución y ejecución pendientes. |
| SystemDynamics / Modelica Standard Library | Componentes Modelica candidatos | https://github.com/modelica-3rdparty/SystemDynamics ; https://doc.modelica.org/ | Referencias históricas en PR #20 de `short`; no instaladas/admitidas en IGC. Revisar versiones y compatibilidad exacta con OMC. |
| BusinessSimulation / BSL | Posibles moléculas e interfaces | https://github.com/bslMS/BusinessSimulation | PR #20 la describe como v2.2.0/EUPL-1.2 o posterior. Dato aún no verificado aquí; no copiar ni integrar antes de revisar fuente, licencia y puertos. |
| Hines, *Molecules of Structure* | Referencia para mecanismos dinámicos | https://www.vensim.com/documentation/Models/Molecules/molecule.pdf | Material de referencia; derechos y condiciones de reutilización deben revisarse antes de redistribuir contenido o modelos. |
| SQLite / Cloudflare D1 | Ledger y metadatos bitemporales | https://developers.cloudflare.com/d1/ | Diseñar adapter local; API, límites y comportamiento transaccional por verificar antes de integración. |
| Cloudflare R2 | Artefactos grandes y snapshots | https://developers.cloudflare.com/r2/ | Diseñar adapter; no hay binding ni bucket configurado. |
| Cloudflare Vectorize | Recuperación vectorial | https://developers.cloudflare.com/vectorize/ | Diseñar adapter; no hay índice configurado. Versiones/límites vigentes por verificar. |
| PyKEEN u otro KGE | Embeddings de grafos | https://pykeen.readthedocs.io/ | Candidato no seleccionado; no instalado; evaluación y licencia pendientes. |

## Reglas de admisión

1. Registrar URL oficial, versión/tag/commit, fecha de consulta y SHA-256 del artefacto usado.
2. Registrar licencia y obligación de redistribución/modificación antes de copiar código o modelos.
3. Separar “documentado”, “instalado”, “compilado”, “integrado” y “aprobado”; un estado no implica el siguiente.
4. No inferir compatibilidad semántica o de conectores Modelica por similitud de nombres.
5. No ejecutar instalaciones ni acceder a cuentas cloud reales hasta tener los manifiestos y límites aprobados.

Este archivo no es un lockfile ni un dictamen legal.
