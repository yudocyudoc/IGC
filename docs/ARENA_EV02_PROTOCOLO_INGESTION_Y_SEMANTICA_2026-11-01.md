# ARENA EV-02 — Protocolo previo: ingestión de registros operativos y contrato de observabilidad

**Fecha local:** 2026-11-01. **Este documento es el PRIMER commit de EV-02 antes de programar, ejecutar o inspeccionar resultados del nuevo ensayo.** Rama Draft apilada sobre [EV-01 #131](https://github.com/yudocyudoc/IGC/pull/131), cabeza base `21cc0b0630b405e1b8749390ff317c702e3448b7`. No fusionar, reescribir ni modificar CAF-01..16, MC-01, EV-01, D/B/M, ledger ni ATMS.

## Pregunta y criterio de éxito

EV-01 demuestra que los mismos 15 pedidos producen distintos grados de observabilidad (POS, POS+KDS idealizado, FULL). EV-02 no repite simulaciones ni descubre otra topología. Construye **un adaptador de ingestión de registros exportados** con contratos de semántica y calidad que **NO confunda acciones administrativas (click KDS) con inicios/finales de trabajo físico**. En ausencia de exportaciones reales autorizadas, solo emplear **CSV de muestra sintéticos** que imiten POS/KDS y un perfil CRM ilustrativo, nunca reclamar conexión con proveedor o negocio.

Resultados obligatorios: filas normalizadas con UTC, identificadores de caso vinculados explícitamente, evidencia/semántica por fuente y reportes de calidad; casos inválidos en cuarentena, sin falsos diagnósticos. Un par de eventos `preparacion_iniciada, preparacion_terminada` solo prueba tiempo de servicio físico SI el perfil declara **`physical_service_verified`** con soporte documentado. Sin ello, la diferencia se reporta como intervalo de marcas administrativas, nunca servicio ni espera.

## Contrato de fuente fijo (sin inferencia de significado por nombres)

Dos perfiles de ejemplo (configuraciones solo de prueba):
- `pos_export_v1`: columnas exactamente `order_id,event_id,action,occurred_at,clock_id`. Acciones explícitas `created -> order_created`, `paid -> payment_recorded`, `handed_off -> delivery_recorded`. **Semántica `administrative_milestone`**, incluso delivery: se desconoce el retardo entre click y entrega real.
- `kds_export_v1`: columnas exactamente `order_id,event_id,action,occurred_at,clock_id`. Acciones `prep_started -> preparation_started` y `prep_done -> preparation_completed`. **Semántica `administrative_milestone`** por defecto; NO physical service. Nada de etapa adicional.
- `crm_export_v1`: columnas exactamente `lead_id,event_id,action,occurred_at,clock_id`, `created -> lead_created`, `qualified -> lead_qualified`, `demo_requested -> demo_requested`, `demo_booked -> demo_booked`, `lost -> lead_lost`. Semántica administrativa y **ninguna interpretación de duración de servicio o colas de baristas**.
- Los alias externos de `order_id` deben coincidir **solo** si existe un `namespace` de identificación de casos previamente acordado y declarado. No vincular por nombre, teléfono, proximidad horaria ni semejanza textual. Para CRM, namespace distinto. Los eventos conservan `source_system`, `source_profile`, `source_record_id`, `case_namespace`, `case_id`, `observed_at_utc`, `raw_timestamp`, `clock_id`, `timestamp_semantics`, `source_digest`, `evidence_ref` y `quality`; **no guardar PII ni columnas desconocidas**.
- No aceptar timestamps naive: **ISO 8601 con desplazamiento explícito** `Z` o `±HH:MM`. Convertir a UTC con `datetime.fromisoformat`; preservar precisión declarada en microsegundos de Python, y registrar resolución. Parseo fallido, no sincronía, duplicados y marcas negativas no deben producir mediciones legítimas.
- Documento de fuente obligatorio para cada profile: `clock_status` en `verified_utc_sync` o `unverified`; `timestamp_accuracy_ms` número entero no negativo o `null`; `timestamp_semantics` administrativo por defecto. El perfil `physical_service_verified` se reservará a futura instrumentación y requerirá prueba de reloj y documentación de que cada timestamp corresponda al evento físico. EV-02 no lo utiliza para afirmar duración física.
- Ingestión con **fail closed** por esquema en perfiles; filas con acciones no mapeadas, faltas, `event_id` duplicado, hora malformada o case_id ausente se ponen en **cuarentena** con códigos de causa, nunca se desvían silenciosamente a `unknown stage`. Fuente privada identificable no se copia al informe/artifact. Tests detectan credenciales o columna `email` y rechazan el esquema.
- En unión POS+KDS, si el `clock_status` de alguna fuente no está verificado o hay precisión insuficiente, **NO comparar intervalos cross-source como si fueran tiempos físicos**. Registrar `CROSS_SOURCE_TEMPORAL_COMPARISON_BLOCKED` incluso si los timestamps parecen ordenados. Si un perfil no aporta exactamente una creación y entrega por caso, el ciclo se marca `UNRESOLVED_INCOMPLETE_LIFECYCLE` y jamás se interpola. Si los eventos de ambos sistemas se contradicen cronológicamente, anotar inconsistencia y bloquear el cálculo intersistemas.

## Ensayo sintético congelado

Reutilizar `arena_ev01_event_views.trace_generator` SOLO COMO generador evaluador, sin reescribir su código. Tomar sus proyecciones `POS` y `POS_KDS` para producir dos CSV que parecen exportaciones reales, con 15 pedidos y todos los hitos correspondientes (POS 45 filas, KDS 30 filas), adaptados a `origin_utc=2026-01-01T00:00Z`, sin columnas internas. El CSV es sintético y los timestamps originales son fracciones de minuto convertidas a microsegundos de forma **redondeada y declarada**, no exactos. Comparar eventos compartidos de forma estable. NUNCA pasar truth FULL a la inferencia.
- **Caso S1** POS y KDS con `verified_utc_sync` y exactitud documental ±1ms: 75 eventos aceptados, 0 cuarentena, 15 ciclos administrativos y 15 intervalos administrativos KDS (NO tiempo físico). Reportar que sigue SIN medirse la espera de preparación y SIN explicarse el residuo.
- **Caso S2** mismísimos archivos, KDS `unverified`: mismos 75 eventos normalizados y métricas dentro de cada reloj que cumplan contrato, pero BLOQUEO explícito de comparaciones POS↔KDS. Un timestamp con zona explícita **no implica** reloj sincronizado.
- **Caso S3** introducir (a) timestamp sin zona, (b) duplicado de event_id, (c) acción desconocida, (d) fila sin case_id, (e) cabecera extra `email`: cuarentena de filas para (a–d), rechazo de archivo completo para (e). No aprender de anomalías después del ensayo.
- **Caso S4** CRM con 2 leads fabricados, eventos y namespaces separados; aceptar hitos, NO atribuir servicio/cola, NO unir leads con pedidos.

## API y artefactos

Implementar núcleo general `scripts/arena_operational_ingestion.py` sin imports CAF/EV01/PM4Py, y adaptador de experimento `experiments/cafeteria/pc02/arena_ev02_ingestion_probe.py` que reutiliza únicamente fixture EV01 para construir CSV de pruebas en memoria. Archivos fuera del módulo núcleo:
- `00_PLAN_BEFORE_EVAL.json` con SHA head/checkout, perfiles semánticos, gates y criterios.
- `01_RESULTS.json` conteos, calidad y métricas permitidas; solo IDs sintéticos en artifacts.
- `02_REPORT.md` de resultados y abstenciones.
- `03_MANIFEST.json` de hashes SHA256.
- No escribir CSV con nombres/emails o datos empresariales reales; CI usa exclusivamente fixtures fabricados. Restringir llamadas a adaptadores externos de proveedor, credenciales, red, cuentas privadas o PRs en otras ramas.
- CI verifica 15/15 casos con igual timestamp normalizado POS; duplicados, cross-clock unverified, tiempos faltantes, ISO sin offset, PII, y **que el analista no etiquete una etapa oculta ni llame duración física al par de clicks del KDS**. Los controles son fail-closed; integridad con SHA, no tests que exijan una «mejora de detección».

## Alcance, límites, gate

**GATE** `BLOCKED_SYNTHETIC_EXTERNAL_FORMAT_NO_REAL_POS_KDS_CRM_DATA_OR_CLOCK_VALIDATION`. Implementar solamente infraestructura de ingestión y contrato de evidencia, NO inferencia causal, modelos de colas, decisión de sobrecarga ni integración activa con D/B/M o ATMS. Se requiere ejemplo de exportación real autorizado, documentación del proveedor, relojes, latencia de logging y calidad de datos antes de sostener métricas empresariales. PR Draft sin merge; mantener MC-01 como backend matemático opcional.
