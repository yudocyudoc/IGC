# Matriz de inventario F0

**Corte:** 2026-10-19. Clasifica lo que existe en el checkout nuevo frente a propuestas y brechas. “Documentado” no significa implementado.

| Capacidad/artefacto | Existe en IGC | Documentado/propuesto | Faltante / evidencia necesaria |
|---|---|---|---|
| Especificación IGC v0.2 | Sí, `docs/` | Normativa de arquitectura y experimentación | Revisión/adjudicación de decisiones reservadas. |
| Plan F0–F9 | Sí, `docs/PLAN_IMPLEMENTACION_IGC_v0_2.md` | Oleadas y gates | Revisión al cerrar F0. |
| Ledger/temporalidad bitemporal | No | Contratos en especificación | LinkML, esquema, migraciones, eventos y consulta as-of reproducible. |
| Web Annotation | Spike sintético | Requerido por CQ/GATE | JSON-LD fixture se parsea a RDF/Turtle y verifica isomorfismo; falta suite completa de conformidad W3C. |
| PROV-O | Parcial, fixture sintético | Ontología objetivo | Relación mínima de actividad/uso/generación pasa y se consulta; falta procedencia completa/versionada. |
| CRMinf/CRMsci | Perfil mínimo en fixture sintético | CRMinf 1.2.1, CRMsci 3.2, compatibles con CIDOC CRM 7.1.3 según declaraciones oficiales | I1/I2/I4/J2/J4 se verifican en el grafo y son gate de CI; I5 y clases de observación CRMsci no se afirman para esta fixture. Falta importar los grafos oficiales, probar entailment y ampliar mapeos con fixtures de observación/inferencia apropiados. |
| RDF/JSON-LD/SPARQL/SHACL | Parcial, fixture sintético | Estándares objetivo | RDFLib 7.6.0 y pySHACL 0.40.1 pasan en Actions; shapes y consulta cubren solo este fixture. OWL/entailment y suites generales pendientes. |
| LinkML | No | Fuente de esquemas prevista | Dependencia fijada, generación y validación. |
| ATMS | Prototipo sintético F0 | Contrato funcional en §10; motor de producción para F3 | Verifica etiquetas mínimas para alternativas compatibles y poda de un nogood; faltan selección/admisión de motor, retractación/versionado, ciclos y suite de conformidad. |
| Búsqueda semántica/FTS | No | Texto, KGE y firmas dinámicas previstas | Motores, manifests, evaluación temporal, negativos y ablaciones. |
| Candidatos de modelo rivales | No | `SystemInvestigation` / `SystemModelCandidate` | Persistencia, diff estructural, relaciones y evidencia trazable. |
| IGC-SL / linter L0–L6 | No | Contrato y gate definidos | AST, tipos, adapters, diagnósticos y tests negativos. |
| OpenModelica | Sí, en GitHub Actions | Destino y simulador obligatorio | Imagen oficial 1.27.1 fijada por digest; el toy Modelica compila/simula y genera CSV. No demuestra integración de un candidato de sistema. |
| Librerías Modelica | No integradas en IGC; spike OMC sintética separada | Fuentes upstream verificadas: BSL v2.2.0 (commit `608cf499`) y SystemDynamics v2.1.2; PR #20 cerrado sin merge, #39/#40 en draft | BSL declara MSL 4.0.0/EUPL-1.2+ y prueba de release con OMEdit 1.23.0-dev; SystemDynamics declara MSL 4.0.0/BSD-3-Clause. Ninguna está fijada ni compilada por el workflow IGC actual; probar versión exacta en la imagen OMC fijada antes de admitirla. |
| D1 / R2 / Vectorize | No hay bindings ni recursos | Persistencia/cloud previstos | Adapters locales, pruebas y posterior decisión de recursos reales/costos. |
| Docker | Sí, en runner Actions | Laboratorio reproducible propuesto | Docker 28.0.4 observado y contenedor OpenModelica fijado por digest; no existe aún Compose de servicios IGC. |
| Spike vertical | Parcial y sintético | Recorrido detallado en Apéndice A | Source→Annotation→RDF/PROV/CRMinf/SPARQL/SHACL/ATMS-prototype→OpenModelica ejecutado; CRMsci no aplica a este fixture y el candidato sigue como stub. Estado global BLOCKED. |
| Suite de aceptación | Parcial | T01–T30 / suite adversativa en especificación | Trece pruebas contractuales/de integración versionadas; falta incorporar suite integral T01–T30. |
| Datos sintéticos | Sí, fixtures de F0 | Permitidos y requeridos para spikes | Ampliar fixtures con escenarios orientados a T01–T30 y mantener hashes/procedencia. |
| CI / PR | Sí, PR draft #1 en IGC | PRs antecedentes consultados en `yudocyudoc/short`: #20 cerrado sin merge; #39/#40 abiertos en draft | Sus estados y claims están anotados en `THIRD_PARTY.md`; no son código integrado ni revisión independiente de IGC. Workflow de Actions con artefactos; no sustituye revisión independiente. |

## Estado de los entornos

- El entorno local consultado conserva su inventario histórico: Python 3.13.1, Node.js 22.13.1, Git 2.51.0.windows.1; no detectó `omc`, Docker, RDFLib, pySHACL ni LinkML.
- GitHub Actions: Ubuntu 24.04, Python 3.13.16 y Docker 28.0.4; trece pruebas pasan y el lock Python de ocho paquetes con SHA-256 se instala con `--require-hashes`; Actions adjunta SBOM SPDX 2.3 de 1,445 registros (Python, dpkg del runner/contenedor y acciones fijadas). Las licencias quedan `NOASSERTION`; faltan herramientas no-dpkg y revisión de licencias. Las etapas JSON-LD/RDF/PROV/CRMinf/SHACL/SPARQL/ATMS-prototype/OpenModelica pasan.
- La validación del proyecto se hace en Actions por decisión vigente; los entornos son distintos.
