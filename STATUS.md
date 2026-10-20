# IGC — Estado del laboratorio

**Corte:** 2026-10-19  
**Fase:** F0 — Inventario y laboratorio  
**Estado:** EN CURSO; spike sintético ejecutado en GitHub Actions, con integraciones parciales demostradas.

## Rama y alcance

- Repositorio: `yudocyudoc/IGC`.
- Rama: `f0-inventario-spike`; PR borrador #1 contra `main`.
- El código, cambios de documentación y verificaciones se gestionan en GitHub. Las ejecuciones usan GitHub Actions; esta fase no depende del checkout local.
- La corrida solo usa datos/modelos sintéticos y no afirma nada de un sistema real.

## Evidencia ejecutada

- Workflow `F0 synthetic spike`, ejecución #179: [resultado y artefactos](https://github.com/yudocyudoc/IGC/actions/runs/39344398983). Todos los pasos y 14 pruebas pasan; artefacto ID `12230756168`. El reporte funcional sigue `BLOCKED` deliberadamente por capacidades de fases futuras.
- Catorce pruebas contractuales/de integración cubren perfiles sintéticos, SBOM, lock de dependencias, etiquetas ATMS y estados bloqueados; no equivalen a la suite T01–T30 integral.
- Python 3.13.16; RDFLib 7.6.0 (BSD-3-Clause) y pySHACL 0.40.1 (Apache-2.0) se instalan desde `requirements-f0.lock.txt`, que fija los ocho paquetes de la resolución con SHA-256. Actions instala en un venv limpio con `--require-hashes`, compara la resolución resultante con el lock y conserva reportes y freeze en el artefacto.
- OpenModelica 1.27.1 corre desde la imagen oficial `openmodelica/openmodelica:v1.27.1-minimal`, fijada por digest. El modelo sintético compila y simula; SystemDynamics 2.1.2 más MSL 4.0.0 carga `SystemDynamics.Levels.Level` y pasa `checkModel`. No se simula un ejemplo de la librería ni se integra a un candidato IGC.
- El anclaje de fuente pasa con SHA-256 `d1f9ff1422b8283e6ada4bd8bbf28ef6582039a380b13435e9048df09cb7e25e`.
- El fixture Web Annotation se parsea como JSON-LD, se serializa a RDF/Turtle y se verifica por isomorfismo.
- El perfil SHACL IGC pasa el fixture positivo y rechaza el negativo.
- La traza PROV-O mínima, el perfil CRMinf I1/I2/I4/J2/J4, la consulta SPARQL y el prototipo ATMS pasan en Actions. El ATMS conserva etiquetas mínimas para alternativas compatibles y poda el nogood explícito; no es un motor de producción. CRMsci no aplica al fixture, que no contiene observaciones ni mediciones.
- Ontologías oficiales: CIDOC CRM 7.1.3, CRMinf 1.2.1, CRMsci 3.2 y PROV-O parsean y pasan términos requeridos. OWL-RL infiere E16 Measurement → S4 Single Observation sobre el set cargado. SHA-256 y reporte quedan en el artefacto; `owl:imports` closure completa no está expandida.
- Artefactos: `run.json`, grafo sintético y reportes SHACL, CSV, logs OpenModelica, chequeo SystemDynamics, hashes de librerías/ontologías, reporte de entailment, reportes de pip, locks, entorno y SBOMs SPDX 2.3.

## Límites y pendientes

- El resultado agregado del runner sigue `BLOCKED` deliberadamente: quedan pasos fuera de este corte.
- El perfil Web Annotation y shapes SHACL son mínimos y sintéticos; no son una certificación de conformidad completa W3C.
- PROV-O solo cubre el vínculo de generación/uso de la fixture.
- CRMinf 1.2.1 / CRMsci 3.2 / CIDOC CRM 7.1.3: perfil mínimo de argumentación I1/I2/I4/J2/J4 añadido al fixture sintético y puesto como gate de CI. El fixture declara explícitamente que no contiene medición; por eso no se tipa como S4/S27 y tampoco se afirma I5 (inferencia). El grafo completo de las ontologías no se importa ni se declara conformidad OWL.
- El lock hash cubre el cierre Python para Ubuntu 24.04/CPython 3.13.16 x86_64. El SBOM SPDX 2.3 de plataforma enumera 1,451 registros: 8 paquetes Python, 1,210 dpkg del runner, 222 dpkg del contenedor, 3 acciones, 2 fuentes Modelica y 4 grafos ontológicos, además de runner e imagen. Snapshot hash `60bef95ddb7e3c1811b2af9201ef73240bfe183ac206038e1846dee35e0c98dd`. La revisión documental acotada de licencias está completada en `docs/REVISION_LICENCIAS_F0.md`; el SBOM permanece `NOASSERTION` porque 1,210 paquetes dpkg del runner y 222 del contenedor no se auditaron individualmente. El inventario no desglosa herramientas del runner instaladas fuera de dpkg ni dependencias internas de las acciones. Las acciones están fijadas por commit SHA y la imagen OpenModelica por digest; la etiqueta `ubuntu-24.04` sigue siendo una imagen alojada administrada por GitHub, no una imagen inmutable del runner.
- El prototipo ATMS de `scripts/f0_atms_probe.py` cubre solo propagación Horn básica, minimalidad y poda por nogood. La selección de motor y la semántica completa quedan para F3. El candidato del sistema sigue como stub.
- LinkML, D1/R2/Vectorize, recuperación, motor ATMS de producción y BSL siguen pendientes. No se expande la closure `owl:imports`; SystemDynamics pasa un check básico, pero no hay modelo integrado ni simulación de su ejemplo.
- Cloudflare no fue accedido. No se creó ni modificó ningún recurso cloud.

## Veredicto de fase

`F0_PARTIAL — SOURCE/OA/RDF/PROV/CRMINF_PROFILE/CRMSCI_BOUNDED_ENTAILMENT/ATMS_PROTOTYPE/SHACL/SPARQL/OPENMODELICA_SYNTHETIC_PASS/SYSTEMDYNAMICS_CHECKMODEL_PASS — T01_T30_PARTIAL — ATMS_ENGINE/LINKML/CANDIDATE/CLOUD/LICENSE_REVIEW_SCOPED_COMPLETE_PLATFORM_CLOSURE_PENDING`.

La revisión documental acotada de licencias está completada, pero no hay cierre integral de la plataforma para redistribución. No se declara completado F0, gate científico ni hipótesis alguna.
