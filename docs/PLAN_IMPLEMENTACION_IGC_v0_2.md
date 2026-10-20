# Plan de implementación IGC v0.2

**Estado:** plan de trabajo derivado de la especificación integral v0.2; no constituye aprobación científica ni certifica implementación.  
**Fecha:** 2026-10-19  
**Especificación normativa:** [`IGC_CONOCIMIENTO_SISTEMICO_ESPECIFICACION_v0_2_2026-10-19.md`](IGC_CONOCIMIENTO_SISTEMICO_ESPECIFICACION_v0_2_2026-10-19.md)  
**Repositorio:** `https://github.com/yudocyudoc/IGC.git`

## 1. Propósito

Convertir la especificación IGC v0.2 en entregas verificables, preservando todo el alcance F0–F9. Cada fase debe dejar artefactos reproducibles, declarar limitaciones y enlazar sus resultados con contratos y criterios de aceptación. La secuencia permite trabajo incremental; no elimina capacidades ni convierte una integración técnica en evidencia científica.

La primera autorización de implementación se limita a **F0 y a una spike vertical sintética**, según el Apéndice A de la especificación. El resto de las fases se detalla aquí como hoja de ruta; iniciar trabajo que use recursos cloud reales, incorporar datos reales o publicar/mergear resultados requiere las decisiones y autorizaciones señaladas en la especificación.

## 2. Estado inicial verificado

- El checkout local contiene la especificación IGC v0.2 en `docs/`.
- El remoto `origin` apunta a `https://github.com/yudocyudoc/IGC.git`.
- GitHub informa que `yudocyudoc/IGC` existe, está vacío, usa `main` como rama predeterminada y la cuenta conectada cuenta con permisos de lectura y escritura.
- El árbol local aún no tiene commits de proyecto. La especificación local aparece sin seguimiento.
- No se ha auditado aquí ningún código, dependencia, PR, runtime de OpenModelica ni configuración de Cloudflare. Estos son elementos de F0, no hechos asumidos.

## 2.1 Decisión de entorno (actualización del investigador)

El desarrollo y las verificaciones se realizan en GitHub mediante commits al PR y GitHub Actions. La corrida de F0 instala y ejecuta sus dependencias únicamente en el runner Ubuntu; no depende del entorno local. Los recursos Cloudflare reales quedan fuera de las corridas sintéticas.

## 3. Secuencia de entregas

| Fase | Entrega verificable | Criterio de salida resumido |
|---|---|---|
| **F0 — Inventario y laboratorio** | Auditoría del repo y PR relevantes; inventario de librerías Modelica y dependencias; `STATUS.md`, `THIRD_PARTY.md`, `stack.lock.yaml`, decisiones de arquitectura y ERD conceptual; ejecución reproducible en GitHub Actions; spike vertical sintética. | Workflow de GitHub Actions reproducible; límites y contratos registrados. La spike informa qué componentes son reales, cuáles son prototipos/stubs y qué gates siguen pendientes. |
| **F1 — Esquema y ledger** | Esquema LinkML del dominio, artefactos derivados, migraciones D1, journal, temporalidad bitemporal, almacenamiento R2, API/CLI y seeds sintéticos. | T01–T08, T21, T22 y T27; consulta `as-of` reproducible. |
| **F2 — Semántica ejecutable** | Modelos y mappings auditados para CIDOC CRM, CRMinf, CRMsci, PROV-O y Web Annotation; RDF, SPARQL, SHACL y round-trip. | CQ-01, CQ-02, CQ-11, T24 y suite RDF. |
| **F3 — ATMS y modelos rivales** | Motor de etiquetas de supuestos/nogoods; investigaciones, fronteras, campos y candidatos versionados; diferencias estructurales y pruebas. | CQ-03, CQ-04, CQ-05, CQ-10, T11, T12 y T26. |
| **F4 — Vectores íntegros** | FTS y recuperación vectorial de texto, KGE, firmas dinámicas, manifests, cortes temporales y ablaciones. | T09, T13, T14 y T28; benchmarks que reportan falsos positivos y resultados negativos. |
| **F5 — Puente SD completo** | Adaptador P2, roles y moléculas, linter L0–L6, backend OpenModelica reproducible y dos modelos candidatos rivales. | T04, T05, T15–T19, T29 y T30; compilación y simulación real con trazabilidad. |
| **F6 — Ciclo investigador** | Diseño de pruebas, consultas discriminantes, observaciones, revisiones e informes; separación campo percibido/reconstruido. | CQ-06–CQ-10 y CQ-14; ciclo completo en B1/B2/B3. |
| **F7 — Matriz experimental** | Perfiles E0–E7, costos, cegamiento, ablaciones, replicaciones y auditoría independiente. | Reporte con métricas separadas, resultados negativos y sin declarar una victoria anticipada. |
| **F8 — Integración cloud y escala** | Workers/API, D1, R2, Vectorize, runner Linux, seguridad, privacidad, conciliación y costos. | Recuperación ante fallos, pruebas de carga/seguridad y operación dentro del presupuesto aprobado. |
| **F9 — Transferencia y caso real** | B4 con datos autorizados, extensión a otros dominios y revisión metodológica. | Evidencia independiente sobre utilidad y fidelidad; datos y permisos documentados. |

La spike vertical de F0 debe avanzar en paralelo con el diseño de F1/F2, sin reemplazarlos: `Source → Web Annotation → CRMinf/PROV → SPARQL → ATMS → SystemModelCandidate → handoff → OpenModelica → artefacto/evento`. Si un componente no puede ejecutarse todavía, el resultado debe etiquetarse como stub y su gate permanecer pendiente.


### 3.1 Gates independientes de integración

El estado de la plataforma no sustituye al estado de la integración vertical ni a la evaluación científica. Se reportan por separado:
- **F0-ENG:** laboratorio de Actions y componentes verificados; estado provisional según las aserciones efectivamente ejecutadas.
- **F0-VERTICAL:** Source/ClaimOccurrence → SystemModelCandidate → handoff Modelica → simulación trazable; permanece bloqueado hasta superar sus pruebas propias.
- **H-IGC:** fidelidad/utilidad científica; `NOT_EVALUATED` mientras no exista protocolo experimental y evidencia adecuada.

El criterio técnico de F0-VERTICAL para la spike es sintético y acotado: una instancia estructurada enlaza claim anclado, mecanismo hipotético y supuestos sintéticos; genera Modelica reproducible; compila y simula; conserva hashes/procedencia; una perturbación declarada cambia el resultado; unidades y referencias inválidas se rechazan. No exige modelos rivales, calibración ni datos reales. Tampoco demuestra fidelidad empírica o causalidad. Véase [GATES_INTEGRACION.md](GATES_INTEGRACION.md).

### 3.1 Secuencia propuesta de PRs F1–F9

La secuencia conserva todo el alcance y ejecuta validaciones e integraciones mediante GitHub Actions. Cada PR debe ser revisable por separado; una fase puede abrirse cuando sus contratos y artefactos de entrada estén versionados. Los recursos Cloudflare reales se ejercitan desde workflows únicamente después de configurar secretos, límites y autorización.

| PR / fase | Contenido aislado | Depende de | Gate de salida | Riesgo principal |
|---|---|---|---|---|
| PR F1a — contrato y ledger | LinkML, entidades/versiones, eventos, migraciones D1 local/SQLite y API de journal | F0 contratos y ERD | T01–T08 aplicables, T21/T22 en modo local, round-trip as-of | Diseñar esquema demasiado pronto o romper historia |
| PR F1b — objetos y temporalidad | R2 adapter, hashes, borrado, outbox/projection interfaces y consulta temporal | F1a | T06/T21/T22/T27 | Consistencia de proyecciones y borrado verificable |
| PR F2a — fuentes ontológicas | Manifiesto versionado, descarga verificable en CI y cierre de hashes de CRM/CRMinf/CRMsci/PROV-O | Inventario F0; revisión final de licencias antes de distribuir fuentes | Grafos parsean, clases/versiones esperadas y provenance de la descarga | Fuentes web cambiantes, imports incompletos, incompatibilidad de releases |
| PR F2b — perfiles semánticos | Importación/conjunto de ontologías, mappings, JSON-LD/RDF, SHACL y SPARQL | F2a | CQ-01/02/11, T08/T24/T27 positivos y negativos; entailment delimitado | Confundir entailment con validación empírica |
| PR F3a — motor ATMS | Selección tras benchmark o implementación fiel propia; labels, justificaciones, nogoods | F1a, DECISION_ATMS_F0 | T11/T12 y retractación/versionado/conformance | Explosión de entornos o semántica incompleta |
| PR F3b — investigación/candidatos | SystemInvestigation, frontera, revisión estructural, candidatos rivales y diffs | F1a + F3a | T11/T18/T26/T29 | Modelo de datos confundido con causalidad |
| PR F4a — recuperación textual | SQLite FTS5/adapters, manifests y búsqueda temporal | F1b + F2a | CQ-06, T09/T14 con holdout temporal | Fuga futura y falsos positivos de similitud |
| PR F4b — KGE y firmas | PyKEEN (o candidato medido), embeddings de texto/grafo/dinámica y ablaciones | F4a + snapshot semántico F2b | T13/T14/T28; reportar abstención y negativos | Grafo pequeño, sesgo de entrenamiento y espacios incompatibles |
| PR F5a — IGC-SL y linter | AST tipado, catálogo, reglas L0–L6, diagnósticos y adaptador de moléculas | F1a, F3b; inventario/licencias concluido antes de adoptar moléculas | T04/T05/T15/T16/T17 negativos y controles positivos | Ejecutabilidad aparente sin conservación ni fundamento |
| PR F5b — backend y modelos rivales | OpenModelica, dos candidatos, compile/simulate, sensibilidad y artefactos | F5a + librerías admitidas | T18/T19/T30, GATE-INT-5 | Compilación confundida con fidelidad del sistema |
| PR F6 — ciclo investigador | consultas, pruebas discriminantes, observaciones y revisiones | F2b + F3b + F5b | CQ-08–10/14, T19/T20/T25/T26 | Permisos o mediciones no justificadas |
| PR F7 — evaluación E0–E7 | Protocolo ciego, datasets separados, métricas, costos y replicación | F4b + F5b + F6 | T23/T30 y reporte reproducible | Filtración de gold o confusión de efectos |
| PR F8a — adapters cloud | Workers/API, D1/R2/Vectorize, configuración y observabilidad, desplegados desde Actions | F1b, F4b, decisión/secretos/límites aprobados | T21/T22 + pruebas de seguridad/carga y reconciliación | Costos, secretos y divergencia de datos |
| PR F8b — operación/escala | Jobs, reintentos, runner de cómputo y límites operacionales | F8a + F5b | Recuperación y presupuesto de operación verificados | Runtime pesado fuera de límites de Workers |
| PR F9 — caso y transferencia | B4 autorizado, replicación y revisión metodológica independiente | F7 + F8 + aprobación de datos | gates integrales §21 y auditoría independiente | Generalizar desde un dominio o fuente no autorizada |

La aceptación de cada PR requiere su propio workflow de Actions verde, artefactos descargables, revisión del diff y limitaciones registradas. El estado verde de una fase no promueve a `main`; la promoción sigue bajo revisión del investigador.

## 4. Orden de trabajo de F0

1. **Aislar el trabajo:** crear y usar una rama de desarrollo; mantener `main` intacta. Confirmar el estado real del repo antes de importar o modificar código.
2. **Auditar:** inventariar archivos, dependencias, librerías Modelica y los PR #20, #39 y #40 mencionados por la especificación. Registrar refs y hashes consultados; no inferir que un PR está fusionado o ejecutable.
3. **Fijar decisiones e interfaces:** producir ADR de responsabilidades, ERD conceptual, matriz existente/documentado/faltante y contratos mínimos de la spike.
4. **Verificar terceros:** identificar versiones, licencias, fuentes oficiales y compatibilidades de ontologías, RDF/SPARQL/SHACL, ATMS, OpenModelica y herramientas auxiliares. Fijar el resultado en `stack.lock.yaml`/manifiestos, con los límites conocidos.
5. **Laboratorio en GitHub Actions (decisión vigente):** automatizar dependencias fijadas, pruebas y componentes sintéticos dentro de workflows de GitHub Actions. No se requiere checkout, runtime ni Docker/Compose local como paso del procedimiento; Docker puede ejecutarse dentro del runner de Actions. Cloud real queda fuera de F0.
6. **Ejecutar spike sintética:** recorrer el flujo vertical, conservar entradas, salidas, logs, hashes y pasos de reproducción. Incluir fallos negativos y distinguir pruebas contractuales de capacidades integradas.
7. **Cerrar F0:** actualizar `STATUS.md`, proponer secuencia PR F1–F9 con dependencias/riesgos y preparar PR draft con resultados revisables. No hacer merge, despliegue, gasto cloud ni publicar afirmaciones de éxito sin autorización expresa.

### Paquete mínimo de F0

- `STATUS.md`
- `THIRD_PARTY.md`
- `stack.lock.yaml`
- `ARCHITECTURE_DECISIONS.md`
- ERD conceptual
- matriz existente/documentado/faltante
- manifiesto de ontologías y licencias
- workflows de GitHub Actions y configuración del laboratorio ejecutado en runner
- fixtures sintéticos, comandos de reproducción y salidas de la spike
- reporte de limitaciones, gates pendientes y pruebas negativas
- propuesta de pull requests para F1–F9

## 5. Reglas de avance y aceptación

- Cada fase se trabaja en rama aislada y entrega un diff revisable, workflow de GitHub Actions reproducible, pruebas ejecutables, resultados y limitaciones. La promoción a `main` se hace mediante revisión y autorización del investigador.
- Un gate solo se marca como aprobado si se ejecutó con el componente real requerido y se conservaron evidencias reproducibles. Stubs, mocks y contratos pendientes se identifican como tales.
- SD permanece como lente de investigación y OpenModelica como destino y motor de simulación obligatorio. Un resultado de simulación no identifica por sí mismo un mecanismo real.
- Se conservan modelos rivales, desacuerdos, fallos, resultados negativos, versiones y procedencia. No se promueven relaciones vectoriales a causalidad sin el proceso de evaluación definido.
- D1/R2/Vectorize se diseñan desde F0 y se integran incrementalmente; la plataforma debe tener modo local reproducible. Los recursos cloud reales, datos reales y gastos quedan sujetos a las decisiones reservadas al investigador.
- La integración técnica y la evidencia de H-IGC se reportan por separado.

## 6. Decisiones reservadas

Antes de usar datos reales, operar recursos cloud reales, incurrir en gasto, aprobar promoción causal automática, publicar resultados o fusionar cambios, registrar la decisión correspondiente del investigador conforme a §22 de la especificación. Estas decisiones no impiden inventariar ni construir el laboratorio local con datos sintéticos.

## 7. Próximo paso

Iniciar **F0 solamente** en una rama aislada. Confirmar refs y estado del repo desde GitHub; completar auditoría, contratos, laboratorio de Actions y spike sintética. No usar pasos locales de ejecución. Al cierre de F0, presentar resultados y una secuencia revisada de PRs F1–F9 antes de ampliar la implementación.
