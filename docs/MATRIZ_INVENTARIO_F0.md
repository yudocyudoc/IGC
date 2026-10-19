# Matriz de inventario F0

**Corte:** 2026-10-19. Clasifica lo que existe en el checkout nuevo frente a propuestas y brechas. “Documentado” no significa implementado.

| Capacidad/artefacto | Existe en IGC | Documentado/propuesto | Faltante / evidencia necesaria |
|---|---|---|---|
| Especificación IGC v0.2 | Sí, `docs/` | Normativa de arquitectura y experimentación | Revisión/adjudicación de decisiones reservadas. |
| Plan F0–F9 | Sí, `docs/PLAN_IMPLEMENTACION_IGC_v0_2.md` | Oleadas y gates | Revisión al cerrar F0. |
| Ledger/temporalidad bitemporal | No | Contratos en especificación | LinkML, esquema, migraciones, eventos y consulta as-of reproducible. |
| Web Annotation | Spike sintético | Requerido por CQ/GATE | JSON-LD fixture se parsea a RDF/Turtle y verifica isomorfismo; falta suite completa de conformidad W3C. |
| PROV-O | Parcial, fixture sintético | Ontología objetivo | Relación mínima de actividad/uso/generación pasa y se consulta; falta procedencia completa/versionada. |
| CRMinf/CRMsci | No | Ontologías objetivo | Fijar artefactos/versiones oficiales y ejecutar mapeos/fixtures. |
| RDF/JSON-LD/SPARQL/SHACL | Parcial, fixture sintético | Estándares objetivo | RDFLib 7.6.0 y pySHACL 0.40.1 pasan en Actions; shapes y consulta cubren solo este fixture. OWL/entailment y suites generales pendientes. |
| LinkML | No | Fuente de esquemas prevista | Dependencia fijada, generación y validación. |
| ATMS | No | Contrato funcional en §10 | Biblioteca o implementación seleccionada, nogoods, retractación y conformance. |
| Búsqueda semántica/FTS | No | Texto, KGE y firmas dinámicas previstas | Motores, manifests, evaluación temporal, negativos y ablaciones. |
| Candidatos de modelo rivales | No | `SystemInvestigation` / `SystemModelCandidate` | Persistencia, diff estructural, relaciones y evidencia trazable. |
| IGC-SL / linter L0–L6 | No | Contrato y gate definidos | AST, tipos, adapters, diagnósticos y tests negativos. |
| OpenModelica | Sí, en GitHub Actions | Destino y simulador obligatorio | Imagen oficial 1.27.1 fijada por digest; el toy Modelica compila/simula y genera CSV. No demuestra integración de un candidato de sistema. |
| Librerías Modelica | No inventariadas localmente | PR #20 las cita como antecedentes | Fuente/versión/licencia/adaptadores y ejecución exacta en OMC. |
| D1 / R2 / Vectorize | No hay bindings ni recursos | Persistencia/cloud previstos | Adapters locales, pruebas y posterior decisión de recursos reales/costos. |
| Docker | Sí, en runner Actions | Laboratorio reproducible propuesto | Docker 28.0.4 observado y contenedor OpenModelica fijado por digest; no existe aún Compose de servicios IGC. |
| Spike vertical | Parcial y sintético | Recorrido detallado en Apéndice A | Source→Annotation→RDF/PROV/SPARQL/SHACL→OpenModelica ejecutado; ATMS y candidato siguen pendientes/stub. Estado global BLOCKED. |
| Suite de aceptación | Parcial | T01–T30 / suite adversativa en especificación | Seis pruebas contractuales/de integración versionadas; falta incorporar suite integral T01–T30. |
| Datos sintéticos | No incorporados | Permitidos y requeridos para spikes | Fixtures versionados, hashes y procedencia sintética declarada. |
| CI / PR | Sí, PR draft #1 | PR draft previsto por mandato F0 | Workflow de Actions con artefactos; no sustituye revisión independiente. |

## Estado de los entornos

- El entorno local consultado conserva su inventario histórico: Python 3.13.1, Node.js 22.13.1, Git 2.51.0.windows.1; no detectó `omc`, Docker, RDFLib, pySHACL ni LinkML.
- GitHub Actions: Ubuntu 24.04, Python 3.13.16 y Docker 28.0.4; seis pruebas y las etapas sintéticas mínimas de JSON-LD/RDF/PROV/SHACL/SPARQL/OpenModelica pasan.
- La validación del proyecto se hace en Actions por decisión vigente; los entornos son distintos.
