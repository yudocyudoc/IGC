# Decisiones de arquitectura IGC

**Estado:** decisiones iniciales copiadas de la especificación v0.2; pendientes de implementación y verificación.  
**Fecha:** 2026-10-19

## ADR-0001 — Dinámica de Sistemas y OpenModelica son rectores

- **Decisión:** toda investigación IGC usa Dinámica de Sistemas como lente; OpenModelica es el destino de formalización y motor obligatorio de simulación.
- **Motivo:** decisión explícita del investigador registrada en la especificación v0.2.
- **Consecuencia:** un análisis de datos, tabla o modelo local no reemplaza el modelo dinámico de sistema. Las estructuras parciales pueden quedar no ejecutables sin inventar mecanismos, ecuaciones o parámetros.
- **Verificación:** OpenModelica 1.27.1 compiló y simuló el toy en GitHub Actions, con imagen fijada por digest. Esto verifica integración técnica sintética, no un modelo de sistema real.

## ADR-0002 — Separar conocimiento, sistema y formalización

- **Decisión:** mantener separados (E) afirmaciones/evidencia/procedencia, (S) hipótesis sobre el sistema y (M) modelos formales/simulaciones/pruebas.
- **Motivo:** evita tratar fuente como realidad, relación vectorial como causalidad o compilación como validación empírica.
- **Consecuencia:** los contratos, estados, procedencia y gates se representan por plano y se conectan mediante referencias explícitas.
- **Verificación parcial F0:** JSON-LD/RDF, PROV-O mínimo, perfil CRMinf I1/I2/I4/J2/J4, SHACL positivo/negativo y SPARQL pasan para la fixture sintética. LinkML, API, persistencia y conformidad OWL completa siguen pendientes.

## ADR-0003 — Investigación como espacio versionado de candidatos

- **Decisión:** `SystemInvestigation` contiene varios `SystemModelCandidate`; `ClaimOccurrence` permanece como unidad de atribución documental.
- **Motivo:** evidencia documental y candidato explicativo resuelven preguntas diferentes.
- **Consecuencia:** conservar alternativas compatibles/rivales, versiones, supuestos, fronteras, observaciones, predicciones, ejecuciones y desacuerdos.
- **Verificación pendiente:** esquema, ledger, ATMS y operaciones de comparación.

## ADR-0004 — Adaptadores y operación mediante GitHub Actions

- **Decisión:** integrar bibliotecas mediante adaptadores y contratos versionados; editar, instalar y verificar el proyecto a través de GitHub y GitHub Actions.
- **Motivo:** decisión explícita del investigador para hacer el desarrollo y las ejecuciones en GitHub Actions, con evidencia adjunta al run.
- **Consecuencia:** no se requiere checkout ni instalación local para la validación. D1/R2/Vectorize se diseñan de forma incremental; no se accede a recursos Cloudflare ni se crean recursos reales sin una decisión específica.
- **Verificación:** el workflow F0 instala dependencias fijadas y ejecuta pruebas, RDF/SHACL/SPARQL y OpenModelica en Ubuntu 24.04; el artefacto conserva reportes y resultados.

## ADR-0005 — Repositorio nuevo IGC

- **Decisión:** `yudocyudoc/IGC` es el repositorio destino de esta iniciativa. `yudocyudoc/short` se consulta sólo como antecedente hasta decidir una migración explícita.
- **Motivo:** la instrucción del investigador especifica `IGC`; la referencia a `short` en la especificación v0.2 corresponde al contexto previo.
- **Consecuencia:** no copiar ni declarar integradas las ramas/PR históricos; reutilización exige auditar fuente, dependencias, licencias y contratos.
- **Estado:** línea base documental inicializada; rama remota F0 creada.


## ADR-0006 — F0 se valida en CI, con límites de alcance explícitos

- **Decisión:** la CI ejecuta únicamente fixtures sintéticas y herramientas declaradas en `.github/workflows/f0-ci.yml`; no ejecuta experimentos con datos reales ni crea infraestructura cloud.
- **Motivo:** conservar reproducibilidad y evitar tratar una prueba de integración como evidencia empírica o como autorización de recursos.
- **Consecuencia:** las etapas no implementadas permanecen `PENDING`, `STUB` o `NOT_RUN`; el estado agregado puede ser `BLOCKED` aun cuando todos los gates técnicos F0 pasen.
- **Verificación:** ejecución #78 de `F0 synthetic spike` con diez pruebas, prototipo ATMS y OpenModelica sintético; [run](https://github.com/yudocyudoc/IGC/actions/runs/39339123071).

## ADR-0007 — Mapeo semántico sintético no inventa observación ni inferencia

- **Decisión:** representar el fixture de evaluación mediante CRMinf I1/I2/I4/J2/J4; no tiparlo como CRMsci Observation ni CRMinf I5 Inference Making.
- **Motivo:** la propia fuente de prueba declara que no contiene medición ni evidencia causal.
- **Consecuencia:** se mantiene explícita la frontera entre evaluación de una afirmación y observación o inferencia científica. El grafo oficial completo y entailment siguen pendientes.
- **Verificación:** gate de CRMinf pasa en la corrida F0 #78; CRMsci se reporta como no aplicable a esta fixture.

## ADR-0008 — El prototipo ATMS no es selección de motor

- **Decisión:** permitir en F0 una prueba acotada de etiquetas mínimas, coexistencia de candidatos y poda por nogood, sin declararla motor de producción.
- **Motivo:** demostrar el contrato vertical F0 antes de seleccionar e integrar una implementación completa en F3.
- **Consecuencia:** no se atribuye al prototipo soporte para retraction/versionado, ciclo completo, escalabilidad ni suite de conformidad.
- **Verificación:** diez pruebas y etapa `atms_reasoning` pasan en GitHub Actions; [run #78](https://github.com/yudocyudoc/IGC/actions/runs/39339123071).

## ADR-0009 — Arena con tres brazos autónomos, Clef después; consolidación sin destruir historia (2026-10-25)

- **Decisión del investigador:** primero tres métodos independientes de generación de hipótesis: **D** determinista sin composición molecular, **B** metodología original SD-AI Buffalo sin moléculas y **M** molecular con su catálogo/compositor. Cada uno aporta su modelo nativo y un adaptador **propio** a OpenModelica; se comparan sus consecuencias y pueden iterar solo con retroalimentación propia.
- **Cuarto brazo pospuesto:** **Clef (C)** se añade únicamente después del corte experimental de D/B/M para medir qué cambia. No asumir que Clef genera topologías/ecuaciones por haber demostrado capacidad de clasificación; distinguir tareas y límites al definir su experimento posterior. **Clairic** permanece como recurso/antecedente numérico separado.
- **Memoria:** ATMS es la proyección razonada de soportes, supuestos y dependencias de **hipótesis, simulaciones, contradicciones e iteraciones**. Un ledger bitemporal conserva los eventos y artefactos originales; ATMS no sustituye almacenamiento ni prueba verdad causal. La memoria visible para revisar un brazo excluye productos de los rivales.
- **Repositorio:** `IGC/main` es base integrada; no borrar ramas, PRs, commits o artefactos experimentales de `IGC`/`short`, no fusionar automáticamente PRs apilados; promover solo módulos auditados desde PRs pequeños con pruebas.
- **Alcance de verificación inicial:** `scripts/arena_v0_contract.py` y CI de V0.0 verifican **solo contratos de entrada, aislamiento lógico de paquetes, feedback y trazas**. No demuestran generadores D/B/M, OpenModelica común, custodia blind, memoria ATMS de producción ni cuarto brazo Clef.
- **Documento rector:** `docs/ARENA_IGC_ATMS_PLAN_IMPLEMENTACION_V1_3_2026-10-25.md`, con las fases posteriores mencionadas sin diseñarlas.
