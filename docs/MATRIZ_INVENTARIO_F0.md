# Matriz de inventario F0

**Corte:** 2026-10-19. Clasifica lo que existe en el checkout nuevo frente a propuestas y brechas. “Documentado” no significa implementado.

| Capacidad/artefacto | Existe en IGC | Documentado/propuesto | Faltante / evidencia necesaria |
|---|---|---|---|
| Especificación IGC v0.2 | Sí, `docs/` | Normativa de arquitectura y experimentación | Revisión/adjudicación de decisiones reservadas. |
| Plan F0–F9 | Sí, `docs/PLAN_IMPLEMENTACION_IGC_v0_2.md` | Oleadas y gates | Revisión al cerrar F0. |
| Ledger/temporalidad bitemporal | No | Contratos en especificación | LinkML, esquema, migraciones, eventos y consulta as-of reproducible. |
| Web Annotation | Spike sintético | Requerido por CQ/GATE | JSON-LD fixture se parsea a RDF/Turtle y verifica isomorfismo; falta suite completa de conformidad W3C. |
| PROV-O | Parcial, fixture sintético | Ontología objetivo | Relación mínima de actividad/uso/generación pasa y se consulta; falta procedencia completa/versionada. |
| CRMinf/CRMsci | Perfil mínimo sintético + grafos oficiales importados temporalmente en Actions | Manifiesto data/ontologies/manifest.json fija CIDOC CRM 7.1.3, CRMinf 1.2.1, CRMsci 3.2, PROV-O; hashes pinned y términos requeridos | Los cuatro grafos parsean, 6,974 triples fuente; closure OWL-RL tiene 18,847 triples e infiere CRM E16→CRMsci S4. No se expande owl:imports ni es conformidad ontológica completa. Fixtures sobre observaciones/inferencias siguen pendientes. |
| RDF/JSON-LD/SPARQL/SHACL | Parcial, fixture sintético | Estándares objetivo | RDFLib 7.6.0 y pySHACL 0.40.1 pasan en Actions; shapes y consulta cubren solo este fixture. OWL/entailment y suites generales pendientes. |
| LinkML | No | Fuente de esquemas prevista | Dependencia fijada, generación y validación. |
| ATMS | Prototipo sintético F0 | Contrato funcional en §10; motor de producción para F3 | Verifica etiquetas mínimas para alternativas compatibles y poda de un nogood; faltan selección/admisión de motor, retractación/versionado, ciclos y suite de conformidad. |
| Búsqueda semántica/FTS | No | Texto, KGE y firmas dinámicas previstas | Motores, manifests, evaluación temporal, negativos y ablaciones. |
| Candidatos de modelo rivales | No | `SystemInvestigation` / `SystemModelCandidate` | Persistencia, diff estructural, relaciones y evidencia trazable. |
| IGC-SL / linter L0–L6 | No | Contrato y gate definidos | AST, tipos, adapters, diagnósticos y tests negativos. |
| OpenModelica | Sí, en GitHub Actions | Destino y simulador obligatorio | Imagen oficial 1.27.1 fijada por digest; el toy Modelica compila/simula y genera CSV. No demuestra integración de un candidato de sistema. |
| Librerías Modelica | SystemDynamics carga en prueba aislada de Actions; no integrada al candidato IGC | SystemDynamics v2.1.2 commit b986a2e + MSL 4.0.0 commit 6626538, ambas fuentes con SHA de archivo en SBOM; BSL v2.2.0 sigue sin probar | SystemDynamics.Levels.Level pasa checkModel con OMC 1.27.1 fijado. No se simula un ejemplo ni se afirma compatibilidad de BSL. El artefacto retiene logs/hashes, no el código upstream. |
| D1 / R2 / Vectorize | No hay bindings ni recursos | Persistencia/cloud previstos | Adapters locales, pruebas y posterior decisión de recursos reales/costos. |
| Docker | Sí, en runner Actions | Laboratorio reproducible propuesto | Docker 28.0.4 observado y contenedor OpenModelica fijado por digest; no existe aún Compose de servicios IGC. |
| Spike vertical | Parcial y sintético | Recorrido detallado en Apéndice A | Source→Annotation→RDF/PROV/CRMinf/SPARQL/SHACL/ATMS-prototype→OpenModelica ejecutado; CRMsci no aplica a este fixture y el candidato sigue como stub. Estado global BLOCKED. |
| Suite de aceptación | Parcial | T01–T30 / suite adversativa en especificación | Catorce pruebas contractuales/de integración versionadas; matriz específica docs/MATRIZ_PRUEBAS_T01_T30.md marca 0 PASS integrales, 7 parciales y 23 pendientes. |
| Datos sintéticos | Sí, fixtures de F0 | Permitidos y requeridos para spikes | Ampliar fixtures con escenarios orientados a T01–T30 y mantener hashes/procedencia. |
| CI / PR | Sí, PR draft #1 en IGC | PRs antecedentes consultados en `yudocyudoc/short`: #20 cerrado sin merge; #39/#40 abiertos en draft | Sus estados y claims están anotados en `THIRD_PARTY.md`; no son código integrado ni revisión independiente de IGC. Workflow de Actions con artefactos; no sustituye revisión independiente. |

## Estado de los entornos

- El entorno local consultado conserva su inventario histórico: Python 3.13.1, Node.js 22.13.1, Git 2.51.0.windows.1; no detectó `omc`, Docker, RDFLib, pySHACL ni LinkML.
- GitHub Actions: Ubuntu 24.04, Python 3.13.16 y Docker 28.0.4; catorce pruebas pasan y el lock Python de ocho paquetes con SHA-256 se instala con `--require-hashes`; Actions adjunta SBOM SPDX 2.3 de 1,451 registros (Python, dpkg del runner/contenedor, acciones, Modelica y ontologías). Hash `60bef95ddb7e3c1811b2af9201ef73240bfe183ac206038e1846dee35e0c98dd`; licencias `NOASSERTION` pendientes para el último paso. No incluye herramientas fuera de dpkg ni dependencias internas de Actions. Las etapas JSON-LD/RDF/PROV/CRMinf/SHACL/SPARQL/ATMS-prototype/OpenModelica pasan.
- La validación del proyecto se hace en Actions por decisión vigente; los entornos son distintos.
