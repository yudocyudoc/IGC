# Matriz de cobertura de aceptación T01–T30

**Corte:** 2026-10-19. Esta matriz diferencia pruebas F0 ejecutadas de criterios todavía no implementados. Una prueba cercana al requisito se marca **Parcial**, nunca como PASS completo. La suite integral de aceptación sigue pendiente.

| Test | Requisito resumido | Evidencia actual en IGC | Estado |
|---|---|---|---|
| T01 | Modalidad de habla no se convierte en causa cierta | El fixture contiene una afirmación sintética anclada, pero no prueba preservación modal ni atribución de causa | Pendiente |
| T02 | Resúmenes dependientes no cuentan como fuentes independientes | No hay grafo de dependencias entre fuentes | Pendiente |
| T03 | Valores de periodos distintos no se contradicen automáticamente | Sin ledger temporal ni prueba as-of | Pendiente |
| T04 | Rechazar rol/dimensión stock–flujo inválida | Sin IGC-SL/linter dimensional | Pendiente |
| T05 | Aceptar split conservativo y rechazar duplicación | Sin chequeo topológico/conservativo | Pendiente |
| T06 | Corrección posterior preserva historial y responde as-of | Sin journal bitemporal | Pendiente |
| T07 | Eliminación de modalidad por LLM activa gate | No existe pipeline de extracción LLM ni gate de fidelidad | Pendiente |
| T08 | Cita inventada o selector/digest alterado no se ingesta | test_synthetic_claim_has_an_exact_source_anchor prueba un anclaje válido; no hay caso negativo de manipulación | Parcial |
| T09 | Similitud semántica no crea soporte causal | Sin índice vectorial ni regla de promoción | Pendiente |
| T10 | Homónimos se distinguen por roles/contexto | Sin resolución de entidades | Pendiente |
| T11 | Modelos compatibles coexisten en ATMS | test_atms_alternatives_can_coexist verifica dos nodos asumidos del prototipo, sin modelos versionados ni relación de compatibilidad | Parcial |
| T12 | Supuestos incompatibles producen nogood y podan entornos | test_atms_nogood_prunes_inconsistent_environment y test_atms_f0_probe_is_explicitly_prototype cubren un nogood sintético de la sonda | Parcial |
| T13 | KGE abstiene con grafo pequeño | Sin KGE | Pendiente |
| T14 | Recuperación histórica excluye futuro | Sin índices temporales | Pendiente |
| T15 | Parámetro sin fundamento mantiene candidato parcial | El candidato actual es stub; no hay handoff ni validador de parámetros | Pendiente |
| T16 | Rechazar molécula de nombre parecido pero semántica errónea | Sin catálogo/linter de moléculas IGC-SL integrado | Pendiente |
| T17 | Compilar no basta si falla conservación | No hay validación de conservación; el toy stock no prueba bifurcación | Pendiente |
| T18 | Trayectoria histórica común no identifica mecanismo | Sin conjunto de candidatos rivales y contrastación | Pendiente |
| T19 | Diferencia bajo perturbación genera prueba trazable | Sin motor de pruebas discriminantes | Pendiente |
| T20 | Intervención alucinada queda no autorizada | No hay autorización de intervenciones ni flujo LLM | Pendiente |
| T21 | Fallo entre D1 y Vectorize se recupera con outbox | Sin D1/Vectorize ni outbox | Pendiente |
| T22 | Borrado privado limpia proyecciones/embeddings con auditoría | Sin controles de privacidad ni proyecciones | Pendiente |
| T23 | Reuso de dataset test invalida evaluación | Sin banco experimental ni gold separado | Pendiente |
| T24 | Mapping CRMinf/CRMsci inválido da diagnóstico | test_semantic_spike_roundtrip_provenance_shacl_and_sparql verifica un perfil sintético positivo; el negativo SHACL genérico no acredita mapping inválido | Parcial |
| T25 | Simulación no se presenta como observación | El reporte F0 etiqueta sus etapas/candidato, pero no prueba un intento adversativo de promoción | Parcial |
| T26 | Cambio de frontera requiere nueva revisión | Sin registro versionado de frontera | Pendiente |
| T27 | Fuente cambia/se desplaza y selector detecta divergencia | El anclaje exacto válido se prueba; no se cambia el documento ni se verifica el fallo | Parcial |
| T28 | Dimensionalidad vectorial incompatible se rechaza | Sin espacios vectoriales ni índices | Pendiente |
| T29 | Sin candidatos ejecutables se informa parcialidad | test_pending_component_cannot_be_reported_as_pass y test_stub_cannot_be_reported_as_pass aseguran resultado BLOCKED para etapas PENDING/STUB | Parcial |
| T30 | Inestabilidad numérica queda localizada y reproducible | El toy OpenModelica compila/simula, pero no inyecta inestabilidad ni verifica recuperación | Pendiente |

## Resumen

- **PASS integral:** 0 de 30.
- **Parcial con prueba F0 relacionada:** T08, T11, T12, T24, T25, T27, T29.
- **Pendiente:** 23 de 30.
- La suite existente tiene 14 pruebas contractuales/de integración, pero ese conteo no equivale a 14 criterios T aprobados. F0 no incluye todavía fixtures adversativos vecinos positivos/negativos para cada requisito.
- Para F1–F5 se deben convertir los estados parciales en pruebas de requisito con entradas adversativas, resultado esperado localizado y control vecino aceptado. La cobertura debe conservar links a nombres de test y artefactos de Actions.
