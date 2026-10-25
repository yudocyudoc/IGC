# Arena V0.0 — contrato mínimo, no implementación de generadores

**Fuente rectora:** [`ARENA_IGC_ATMS_PLAN_IMPLEMENTACION_V1_3_2026-10-25.md`](ARENA_IGC_ATMS_PLAN_IMPLEMENTACION_V1_3_2026-10-25.md).

El contrato vive en [`scripts/arena_v0_contract.py`](../scripts/arena_v0_contract.py) y cubre **solo** el límite de intercambio de las tres técnicas independientes (`D` determinista, `B` SD-AI Buffalo, `M` molecular). Los brazos reciben los mismos datos de construcción visibles por copia profunda, vinculados con `source_snapshot_hash` y `input_hash`. La fuente primaria y el diseño de las pruebas son comunes; la metodología de construir hipótesis **no** lo es.

- Una entrega **nativa** es `PROPOSED`, `PARTIAL`, `BLOCKED` o `ABSTAINED`: **no** recibe `SIMULATES` simplemente por existir JSON. Cada brazo conserva sus propios IDs, revision links y huellas del artefacto.
- La formalización y los diagnósticos físicos G0–G3 están pendientes; el contrato **acepta después** sus reportes únicamente como feedback a la entrega que los originó. La lista de campos es cerrada para rechazar accidentalmente salidas explícitas de otros brazos o material reservado.
- Las revisiones no sustituyen registros antiguos: el sobre de eventos incluye hashes, brazo, iteración y vínculo al evento previo. Este sobre **no es** un ledger persistente ni un ATMS productivo; la integración real será posterior.
- `C` (Clef) es **brazo cuarto reservado**; V0 rechaza cualquier intento de ejecutarlo. Para integrarlo más tarde, definir qué tarea nativa realiza y qué evaluación comparable se justifica; no fingir que una elección categórica genera ecuaciones Modelica.

**Advertencia de seguridad:** una inspección de claves JSON no ofrece aislamiento fuerte entre procesos, repositorios o identidades y no detecta valores sensibles ocultos dentro de texto libre. La custodia real necesita permisos separados y pruebas adversativas. Este incremento no proporciona esa custodia ni valida causalidad o predicción.
