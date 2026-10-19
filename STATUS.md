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

- Workflow `F0 synthetic spike`, ejecución #61: [resultado y artefactos](https://github.com/yudocyudoc/IGC/actions/runs/39338634022). Run exitoso sobre el commit `3538c8f7c339e5a869322cc62a37d917deb81324`; artefacto ID `12227452916`.
- Seis pruebas contractuales/de integración pasan, incluida la validación del perfil CRMinf mínimo.
- Python 3.13.16; RDFLib 7.6.0 (BSD-3-Clause) y pySHACL 0.40.1 (Apache-2.0) instalados desde los pins directos de `requirements-f0.txt`. El reporte de resolución de pip y `pip freeze` están en el artefacto.
- OpenModelica 1.27.1 corre desde la imagen oficial `openmodelica/openmodelica:v1.27.1-minimal`, fijada por digest en el workflow. El modelo sintético compila y simula; se genera CSV.
- El anclaje de fuente pasa con SHA-256 `d1f9ff1422b8283e6ada4bd8bbf28ef6582039a380b13435e9048df09cb7e25e`.
- El fixture Web Annotation se parsea como JSON-LD, se serializa a RDF/Turtle y se verifica por isomorfismo.
- El perfil SHACL IGC pasa el fixture positivo y rechaza el negativo.
- La traza PROV-O mínima, el perfil CRMinf I1/I2/I4/J2/J4 y la consulta SPARQL sintética pasan en Actions. CRMsci no aplica al fixture, según su declaración de que no contiene observaciones ni mediciones.
- Artefactos: `run.json`, `annotation-graph.ttl`, reportes SHACL, `omc.log`, CSV del modelo, reporte pip y entorno resuelto.

## Límites y pendientes

- El resultado agregado del runner sigue `BLOCKED` deliberadamente: quedan pasos fuera de este corte.
- El perfil Web Annotation y shapes SHACL son mínimos y sintéticos; no son una certificación de conformidad completa W3C.
- PROV-O solo cubre el vínculo de generación/uso de la fixture.
- CRMinf 1.2.1 / CRMsci 3.2 / CIDOC CRM 7.1.3: perfil mínimo de argumentación I1/I2/I4/J2/J4 añadido al fixture sintético y puesto como gate de CI. El fixture declara explícitamente que no contiene medición; por eso no se tipa como S4/S27 y tampoco se afirma I5 (inferencia). El grafo completo de las ontologías no se importa ni se declara conformidad OWL.
- RDFLib/pySHACL tienen pins directos; la resolución de dependencias transitivas está en el artefacto CI, pero aún falta consolidar un lock completo con hashes en el repositorio.
- ATMS sigue sin implementación seleccionada; candidato del sistema sigue como stub.
- LinkML, D1/R2/Vectorize, recuperación y librerías Modelica adicionales no están implementados ni integrados.
- Cloudflare no fue accedido. No se creó ni modificó ningún recurso cloud.

## Veredicto de fase

`F0_PARTIAL — SOURCE/OA/RDF/PROV/CRMINF/SHACL/SPARQL/OPENMODELICA_SYNTHETIC_PASS — CRMSCI_NOT_APPLICABLE_TO_FIXTURE — ATMS/LOCK/CANDIDATE/CLOUD_PENDING`.

No se declara completado F0, gate científico ni hipótesis alguna.
