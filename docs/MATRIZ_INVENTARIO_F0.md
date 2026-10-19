# Matriz de inventario F0

**Corte:** 2026-10-19. Clasifica lo que existe en el checkout nuevo frente a propuestas y brechas. “Documentado” no significa implementado.

| Capacidad/artefacto | Existe en IGC | Documentado/propuesto | Faltante / evidencia necesaria |
|---|---|---|---|
| Especificación IGC v0.2 | Sí, `docs/` | Normativa de arquitectura y experimentación | Revisión/adjudicación de decisiones reservadas. |
| Plan F0–F9 | Sí, `docs/PLAN_IMPLEMENTACION_IGC_v0_2.md` | Oleadas y gates | Revisión al cerrar F0. |
| Ledger/temporalidad bitemporal | No | Contratos en especificación | LinkML, esquema, migraciones, eventos y consulta as-of reproducible. |
| Web Annotation | No | Requerido por CQ/GATE | Instancias válidas y round-trip. |
| CRMinf/CRMsci/PROV-O | No | Ontologías objetivo | Versiones, mappings, datos RDF, motor, SPARQL y SHACL ejecutados. |
| LinkML | No | Fuente de esquemas prevista | Dependencia fijada, generación y validación. |
| ATMS | No | Contrato funcional en §10 | Biblioteca o implementación seleccionada, nogoods, retractación y conformance. |
| Búsqueda semántica/FTS | No | Texto, KGE y firmas dinámicas previstas | Motores, manifests, evaluación temporal, negativos y ablaciones. |
| Candidatos de modelo rivales | No | `SystemInvestigation` / `SystemModelCandidate` | Persistencia, diff estructural, relaciones y evidencia trazable. |
| IGC-SL / linter L0–L6 | No | Contrato y gate definidos | AST, tipos, adapters, diagnósticos y tests negativos. |
| OpenModelica | No detectado en PATH | Destino y simulador obligatorio | Instalar/verificar versión en entorno autorizado; compilar y simular modelo nativo. |
| Librerías Modelica | No inventariadas localmente | PR #20 las cita como antecedentes | Fuente/versión/licencia/adaptadores y ejecución exacta en OMC. |
| D1 / R2 / Vectorize | No hay bindings ni recursos | Persistencia/cloud previstos | Adapters locales, pruebas y posterior decisión de recursos reales/costos. |
| Docker/Compose | No detectado en PATH | Laboratorio reproducible propuesto | Runtime disponible y configuración reproducible. |
| Spike vertical | No | Recorrido detallado en Apéndice A | Source→Annotation→RDF/SPARQL→ATMS→candidato→OM→artefacto, ejecutado con piezas reales o stubs explícitos. |
| Suite de aceptación | No | T01–T30 / suite adversativa en especificación | Tests versionados, fixtures y trazas ejecutables. |
| Datos sintéticos | No incorporados | Permitidos y requeridos para spikes | Fixtures versionados, hashes y procedencia sintética declarada. |
| CI / PR | No workflows en IGC | PR draft previsto por mandato F0 | Flujo local/CI, artefactos y revisión independiente. |

## Estado de las herramientas del entorno consultado

- Encontrados: Python 3.13.1, Node.js 22.13.1, Git 2.51.0.windows.1, `jsonschema`, `pytest`, `networkx`.
- No encontrados: `omc`, Docker, `rdflib`, `pyshacl`, `linkml`, `pykeen`, `owlrl`.
- Wrangler está localizado, pero su versión no se confirmó.
- Esto describe el PATH/entorno consultado, no todas las máquinas o runners potenciales.
