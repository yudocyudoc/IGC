# ARENA EV-01 — Cierre post-CI: eventos, minería de procesos y fronteras de observabilidad

**2026-11-01, POST-EVALUACIÓN.** PR #131 Draft apilado sobre MC-01 PR #130 Draft; sin fusiones, sin cambios a CAF-01..16, D/B/M o ATMS. Primer commit de protocolo **ANTES DEL CÓDIGO** `6bd6c224578fa90af6e9a2ce348981839bfd7f5e`. Este informe registra resultados, no modifica el plan previo ni atribuye causalidad a un DFG.

## Estado canónico y evidencia

- **[GitHub Actions #41356387093](https://github.com/yudocyudoc/IGC/actions/runs/41356387093): 8/8 pruebas unitarias PASS y evaluación CLI PASS**. Head probado `668a9aadc9ed6b543048c8d1c6daa90d936c1470`; checkout de merge sintético `b6be17084e793cb3c1e07765b71bfb146f9bac57` (dos identificadores distintos, no confundir).
- **[Artefacto original de ocho archivos](https://github.com/yudocyudoc/IGC/actions/runs/41356387093/artifacts/13102494734)**: `00_PLAN_BEFORE_TRACE.json`; `00B_EVALUATOR_ONLY_PHYSICAL_TRACE.json` (truth separada); `01_POS_PUBLIC_EVENTS.csv`, `01_POS_KDS_PUBLIC_EVENTS.csv`, `01_FULL_PUBLIC_EVENTS.csv`; `02_RESULTS.json` (todos los casos y DFG); `03_REPORT.md`; `04_MANIFEST.json`. **7/7 hashes SHA256 validados** en el ZIP descargado, contra los archivos que declara el manifiesto. SHA256 del ZIP publicado por Actions `3723958351d9d6519b2826db3652621cfc3712ef2c55a141b84ed67285812d9d`.
- Fuente física única: 15 pedidos `des.half_open_arrivals("5/2",6)`, 4 estaciones FIFO deterministas caja (2×1min), preparación (1×15/17min), despacho (1×30/43min), transferencia final (1×3/11min). Simulador local nuevo de eventos con **Fraction**; **paridad exacta CAF-01 en nueve checkpoints** de pedidos aceptados, entregados, colas y servidores; conservación y recursos auditados en cada timestamp.
- Método real de minería: **PM4Py 2.7.23.11**, versión pinned, `pm4py.discover_dfg` sobre pandas con caso, evento y timestamp. Tiempos científicos conservados como fracciones exactas del evento; el timestamp pandas derivado usa microsegundos para PM4Py solamente.

## Resultado principal: MISMA operación, diferente observabilidad

| Vista | Eventos del mismo mundo | Actividades del DFG | Aristas DFG | Observables válidos | No inferibles |
|---|---:|---:|---:|---|---|
| A — POS | **45** | **3** | **2** | ID pedido, creación, pago, entrega, tiempo ciclo | Espera/servicio, colas internas, servidores, número de etapas |
| B — POS+KDS IDEALIZADO | **75** | **5** | **4** | Lo de POS + duración entre inicio/fin de preparación y lapso preparación-fin→entrega | Espera antes de preparación, recursos de otras etapas, explicación causal del lapso final |
| C — FULL | **225** | **15** | **14** | ID+entrada/inicio/fin de cada etapa, recurso, espera, servicio, 4 etapas registradas, balance de tiempo | Causas externas ausentes de la instrumentación |

Todos los 15 pedidos tienen **tiempo de ciclo IDÉNTICO** a través de A/B/C, porque son tres proyecciones de los MISMOS eventos, y los balances temporales exactos `ciclo=Σwaiting+Σservice` se cumplen **15/15** solo en C, donde todos los extremos fueron observados. El CSV POS no contiene columna `stage` ni `resource_id`; KDS solo puede incluir `stage=preparacion` y carece de recursos. Los event_seq se vuelven a numerar de forma contigua en cada vista para impedir que saltos del ordinal revelen eventos no autorizados. Ninguna vista A/B contiene `transferencia_final` ni su existencia presupuesta.

### Contraejemplo concreto al «residuo positivo = nueva etapa demostrada»

En la vista B, el tiempo desde `servicio_fin::preparacion` hasta `pedido_entregado` es el mismo en los quince pedidos: **459/473 min ≈0.9704 min**. En la vista B es un intervalo SIN DESGLOSE, compatible temporalmente con diversas asignaciones de trabajo y espera.

La vista C del MISMO mundo conoce los eventos de otras estaciones y explica el lapso concreto como **despacho 30/43 min ≈0.6977 + transferencia final 3/11 min ≈0.2727**, sin espera intermedia. **La cuarta etapa no fue «detectada» por residuos: C la observó directamente**, y B no la recibe. Con solo dos endpoints de tiempo no existe evidencia suficiente para certificar de qué actividades procede un lapso residual. Los dos ejemplos de reparto de tiempo en el informe son **contraejemplos aritméticos**, no prueba de realizabilidad de dos redes FIFO completas bajo exactamente los mismos recursos.

### Estadísticas del mundo (solo auditoría EVALUATOR_ONLY)

- Duración de ciclo promedio **250446/40205 min ≈6.229 min**, rango **22939/8041 ≈2.852 min** a **386197/40205 ≈9.606 min**. Son 15 pedidos correlacionados en UNA operación, no 15 negocios ni muestra poblacional.
- Tiempo de espera promedio en caja **49/75 min ≈0.6533** y en preparación **3472/1275 min ≈2.7231**. Despacho y transferencia tienen espera cero en este ensayo determinista (buffers ilimitados).
- Esas esperas internas NO son salidas legítimas de A/B. Solo C puede sostenerlas porque registra cada entrada, inicio, final y recurso.

## Qué prueba y qué NO

1. **Prueba positiva de integración:** un modelo de flujo físicamente conservador puede emitir eventos con procedencia, proyectarse sin fuga a POS/KDS/FULL, procesarse con una librería de Process Mining existente y calcular solo duraciones cuyo par de timestamps es OBSERVABLE. Las 8 pruebas incluyen manipulación de timestamps/recursos y solapamientos fraudulentos que se rechazan.
2. **Prueba de frontera de observación:** POS solo permite tiempo de ciclo; POS+KDS idealizado añade duración de preparación, pero no espera en esa etapa (falta su llegada física), ni el mecanismo responsable de tiempo final. C ve cuatro etapas porque las instrumentamos.
3. **NO valida un detector de etapa oculta, OOD, causalidad ni predicción de intervención.** Un DFG muestra sucesión de actividades OBSERVADAS, no identificabilidad causal ni número de etapas no observadas. Los datos físicos y la proyección obedecen el mismo mundo sintético, sin validación externa.
4. **La marca KDS puede ser administrativa, no de servicio efectivo** en una cafetería. Sin semántica de cada evento y sincronización de relojes no se obtiene `wait/service` real; el laboratorio anota B como IDEALIZADO.
5. **PM4Py open-source es AGPL-3.0**, se emplea en CI para investigación solamente; su distribución/uso como componente de software comercial requiere evaluación jurídica o licenciamiento apropiado. Las vistas y el código de contratos propios no dependen del funcionamiento interno de PM4Py para preservar tiempo de ciclo.
6. No se han conectado D/B/M, ATMS, un POS real, un CRM, inventario finito ni forks/joins. La fuente primaria de eventos puede posteriormente ser un backend real, pero deberá pasar un contrato de calidad de datos, unidades, ausencias y procedencia.

## Próxima tarea de integración de menor riesgo

Un **adaptador de ingestión de logs reales** con contrato de semántica de timestamps, metadatos de reloj/zonas, versiones de actividad, correlación de ID, calidad de registro y limitaciones por origen POS/KDS/CRM. Solo entonces autorizar diagnóstico de colas; las actividades internas que un sistema no registra se conservarán como `NO_OBSERVADO` y no como estimaciones certeras.

**Gate científico permanente:** `BLOCKED_SYNTHETIC_EVENT_LOG_NO_EMPIRICAL_SENSOR_SEMANTICS_OR_EXTERNAL_VALIDATION`. Mantener PR #131 Draft y sin merge; no inducir sobrecarga en negocios ni promover afirmaciones de identificación de mecanismos ocultos.
