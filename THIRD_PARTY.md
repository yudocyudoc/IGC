# Registro de terceros y estándares

**Estado:** inventario de candidatos, todavía no aprobación de dependencias. La revisión de licencias, versiones, hashes, mantenimiento y compatibilidad es pendiente de F0.

| Componente | Uso propuesto | Referencia disponible | Estado en IGC |
|---|---|---|---|
| CIDOC CRM / CRMinf / CRMsci | Interoperabilidad semántica y epistemológica | https://cidoc-crm.org/ ; https://cidoc-crm.org/crminf/ModelVersion/crminf-1.2.1 | Referenciado en v0.2; versión compatible, licencia/artefactos y perfil LinkML pendientes de verificación. |
| PROV-O | Procedencia de entidades, actividades y agentes | https://www.w3.org/TR/prov-o/ | Estándar objetivo; mapeo y pruebas pendientes. |
| W3C Web Annotation | Anclaje a fragmentos de fuentes | https://www.w3.org/TR/annotation-model/ | Fixture sintético JSON-LD parseado a RDF y round-trip RDF/Turtle validado; SHACL cubre un perfil IGC mínimo, no es una suite completa de conformidad W3C. |
| RDF / JSON-LD / SPARQL / OWL | Grafo semántico, serialización y consultas | https://github.com/RDFLib/rdflib/releases/tag/7.6.0 ; https://www.w3.org/TR/rdf11-concepts/ ; https://www.w3.org/TR/json-ld11/ ; https://www.w3.org/TR/sparql11-query/ | RDFLib 7.6.0, BSD-3-Clause, fijada en `requirements-f0.txt`; parseo JSON-LD, round-trip e instancia de consulta SPARQL 1.1 pasan en Actions. OWL/entailment siguen pendientes. |
| SHACL | Validación de grafos | https://github.com/RDFLib/pySHACL/releases/tag/v0.40.1 ; https://www.w3.org/TR/shacl/ | pySHACL 0.40.1, Apache-2.0, fijado en `requirements-f0.txt`; Shape IGC sintético pasa el caso positivo y rechaza el negativo. Se usa SHACL 1.0 estable; el perfil no equivale a conformidad general. |
| LinkML | Esquema fuente y generación de modelos | https://linkml.io/linkml/ | Candidato; no instalado en el entorno consultado. |
| ATMS | Justificación por conjuntos de supuestos y nogoods | Candidatos de implementación por evaluar según la especificación §10 | Sin biblioteca seleccionada; conformance, licencia y límites pendientes. |
| OpenModelica | Formalización y simulación obligatoria | https://openmodelica.org/download/docker/ ; https://openmodelica.org/terms-of-service/ | OpenModelica 1.27.1 en imagen oficial `openmodelica/openmodelica:v1.27.1-minimal`, fijada por digest `sha256:ac9a0223e69b8055d444b42f58ccb9680342b56848c68b81385bf83d7c0ba824`; licencia indicada por distribución: OSMC-PL 1.8 o AGPLv3. Compilación/simulación del toy sintético pasa en Actions. |
| SystemDynamics / Modelica Standard Library | Componentes Modelica candidatos | https://github.com/modelica-3rdparty/SystemDynamics ; https://doc.modelica.org/ | Referencias históricas en PR #20 de `short`; no instaladas/admitidas en IGC. Revisar versiones y compatibilidad exacta con OMC. |
| BusinessSimulation / BSL | Posibles moléculas e interfaces | https://github.com/bslMS/BusinessSimulation | PR #20 la describe como v2.2.0/EUPL-1.2 o posterior. Dato aún no verificado aquí; no copiar ni integrar antes de revisar fuente, licencia y puertos. |
| Hines, *Molecules of Structure* | Referencia para mecanismos dinámicos | https://www.vensim.com/documentation/Models/Molecules/molecule.pdf | Material de referencia; derechos y condiciones de reutilización deben revisarse antes de redistribuir contenido o modelos. |
| SQLite / Cloudflare D1 | Ledger y metadatos bitemporales | https://developers.cloudflare.com/d1/ | Diseñar adapter local; API, límites y comportamiento transaccional por verificar antes de integración. |
| Cloudflare R2 | Artefactos grandes y snapshots | https://developers.cloudflare.com/r2/ | Diseñar adapter; no hay binding ni bucket configurado. |
| Cloudflare Vectorize | Recuperación vectorial | https://developers.cloudflare.com/vectorize/ | Diseñar adapter; no hay índice configurado. Versiones/límites vigentes por verificar. |
| PyKEEN u otro KGE | Embeddings de grafos | https://pykeen.readthedocs.io/ | Candidato no seleccionado; evaluación y licencia pendientes. |

| GitHub Actions | Instalación/ejecución reproducible de F0 | https://github.com/yudocyudoc/IGC/actions/runs/39337951127 | Runner Ubuntu 24.04, Python 3.13.16, seis pruebas pasan y artefacto `f0-spike-evidence` disponible. La resolución transitiva de pip se adjunta como reporte del run; no hay todavía un lock completo con hashes de todos los paquetes. |

## Reglas de admisión

1. Registrar URL oficial, versión/tag/commit, fecha de consulta y SHA-256 del artefacto usado.
2. Registrar licencia y obligación de redistribución/modificación antes de copiar código o modelos.
3. Separar “documentado”, “instalado”, “compilado”, “integrado” y “aprobado”; un estado no implica el siguiente.
4. No inferir compatibilidad semántica o de conectores Modelica por similitud de nombres.
5. No ejecutar instalaciones ni acceder a cuentas cloud reales hasta tener los manifiestos y límites aprobados.

Este archivo no es un lockfile ni un dictamen legal.
