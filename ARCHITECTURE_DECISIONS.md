# Decisiones de arquitectura IGC

**Estado:** decisiones iniciales copiadas de la especificación v0.2; pendientes de implementación y verificación.  
**Fecha:** 2026-10-19

## ADR-0001 — Dinámica de Sistemas y OpenModelica son rectores

- **Decisión:** toda investigación IGC usa Dinámica de Sistemas como lente; OpenModelica es el destino de formalización y motor obligatorio de simulación.
- **Motivo:** decisión explícita del investigador registrada en la especificación v0.2.
- **Consecuencia:** un análisis de datos, tabla o modelo local no reemplaza el modelo dinámico de sistema. Las estructuras parciales pueden quedar no ejecutables sin inventar mecanismos, ecuaciones o parámetros.
- **Verificación pendiente:** compilación y simulación reales con `omc`; no disponibles en el entorno inventariado.

## ADR-0002 — Separar conocimiento, sistema y formalización

- **Decisión:** mantener separados (E) afirmaciones/evidencia/procedencia, (S) hipótesis sobre el sistema y (M) modelos formales/simulaciones/pruebas.
- **Motivo:** evita tratar fuente como realidad, relación vectorial como causalidad o compilación como validación empírica.
- **Consecuencia:** los contratos, estados, procedencia y gates se representan por plano y se conectan mediante referencias explícitas.
- **Verificación pendiente:** LinkML, RDF/SHACL, API y persistencia implementados.

## ADR-0003 — Investigación como espacio versionado de candidatos

- **Decisión:** `SystemInvestigation` contiene varios `SystemModelCandidate`; `ClaimOccurrence` permanece como unidad de atribución documental.
- **Motivo:** evidencia documental y candidato explicativo resuelven preguntas diferentes.
- **Consecuencia:** conservar alternativas compatibles/rivales, versiones, supuestos, fronteras, observaciones, predicciones, ejecuciones y desacuerdos.
- **Verificación pendiente:** esquema, ledger, ATMS y operaciones de comparación.

## ADR-0004 — Adaptadores y operación local primero

- **Decisión:** integrar bibliotecas mediante adaptadores y contratos versionados; poder operar localmente sin Cloudflare.
- **Motivo:** evitar asumir compatibilidades entre ontologías, conectores Modelica o servicios cloud y desacoplar validez científica del hosting.
- **Consecuencia:** D1/R2/Vectorize se diseñan desde F0 y se integran incrementalmente; recursos cloud reales permanecen fuera hasta aprobación de límites/costos.
- **Verificación pendiente:** entorno local y pruebas de adapters/fallos.

## ADR-0005 — Repositorio nuevo IGC

- **Decisión:** `yudocyudoc/IGC` es el repositorio destino de esta iniciativa. `yudocyudoc/short` se consulta sólo como antecedente hasta decidir una migración explícita.
- **Motivo:** la instrucción del investigador especifica `IGC`; la referencia a `short` en la especificación v0.2 corresponde al contexto previo.
- **Consecuencia:** no copiar ni declarar integradas las ramas/PR históricos; reutilización exige auditar fuente, dependencias, licencias y contratos.
- **Estado:** línea base documental inicializada; rama remota F0 creada.
