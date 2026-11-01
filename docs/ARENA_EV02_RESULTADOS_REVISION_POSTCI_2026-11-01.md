# ARENA EV-02 — Informe post-CI de ingestión con semántica, procedencia y abstención

**Fecha:** 2026-11-01. **POST-EJECUCIÓN**, no parte del protocolo previo. [PR #132 Draft](https://github.com/yudocyudoc/IGC/pull/132), apilado sobre EV-01 PR #131, sin merge. El protocolo previo fue el PRIMER commit `b836e46138aad231a5595a1b429ea69407e786f8`, anterior al código y a la evaluación.

## Custodia y resultados auditados

- **CI canónica [#41357791833](https://github.com/yudocyudoc/IGC/actions/runs/41357791833): 11/11 pruebas PASS, regresión integral PASS.** Cabeza evaluada `19ef4c089a4cd6e7258a085e5b415dfaae64aacb`; checkout sintético de PR merge `e9e133bfc67817af423a69d941d2817d30c3161f`. Estos hashes son distintos y aparecen ambos en el artefacto.
- **[Artefacto canónico](https://github.com/yudocyudoc/IGC/actions/runs/41357791833/artifacts/13103866693)**: `00_PLAN_BEFORE_EVAL.json`, `01_RESULTS.json`, `02_REPORT.md`, `03_MANIFEST.json`. Descargado, **3/3 SHA256 del manifiesto coinciden** con los archivos originales. No contiene CSV raw, emails, nombres ni fuente empresarial real.
- Primera corrida [#41357661441](https://github.com/yudocyudoc/IGC/actions/runs/41357661441) completó 9/10 tests; fallo **solo de clasificación de motivo de cuarentena**: un timestamp ISO sin desplazamiento UTC fue rechazado como formato general inválido. Commit `d648802` distingue `EV02_TIMESTAMP_HAS_NO_UTC_OFFSET` sin modificar las entradas aceptadas, el contrato semántico ni el método. Posteriormente se añadió prueba de namespace de leads vs pedidos para prevenir joins interdominio. La CI final es la canónica.
- Núcleo general **`scripts/arena_operational_ingestion.py`** sin imports CAF, EV-01 o librerías de process mining; perfiles externos ilustrativos POS/KDS/CRM y normalización ISO 8601 con offset explícito. Adaptador de prueba **`experiments/cafeteria/pc02/arena_ev02_ingestion_probe.py`**, que transforma únicamente proyecciones EV-01 en exportaciones CSV con forma de fuente externa; **no hay proveedor externo conectado**.

## Resultado completo y estatus epistémico

| Condición | Registros válidos | Casos | Resultado sustentado |
|---|---:|---:|---|
| POS y KDS, relojes declarados sincronizados con precisión 1ms | 45 POS + 30 KDS = **75** | **15 pedidos** | 15 ciclos administrativos POS, 15 intervalos administrativos KDS y 15 lapsos cruzados entre clicks bajo declaración de relojes, **NUNCA servicio físico** |
| Idénticos registros con KDS `unverified` | **75** | **15 pedidos** | **15/15 intervalos entre fuentes bloqueados**; diferencia dentro de KDS sigue etiquetada como intervalo administrativo registrado |
| POS con cuatro registros adulterados añadidos | 45 aceptados y **4 en cuarentena** | 15 pedidos aceptados | Faltante de offset, ID duplicado, acción sin traducción, ID de pedido vacío: **una cuarentena de cada tipo** |
| POS con columna inesperada `email` | No se procesa el archivo | N/A | **`EV02_FILE_SCHEMA_REJECTED`**; prohibido trasladar datos extra |
| CRM sintético y separado | **4** | **2 leads** | Solo hitos administrativos; **0** atribuciones de duración de servicio, de espera o de cuello |

### Qué fue validado

1. **El significado no se adivina:** las acciones de POS/KDS/CRM solo se traducen con `ACTION_MAP` explícito, y todo lo observado se etiqueta `administrative_milestone`. Una pareja `prep_started`/`prep_done` es duración entre registros, no el tiempo físico del barista.
2. **El tiempo UTC no garantiza sincronización real:** UTC se deriva de marcas ISO con offset explícito; `verified_utc_sync` sigue siendo una **declaración del origen no verificada por instrumentos independientes**. Si un origen es `unverified`, la comparación entre fuentes se bloquea aunque los instantes parezcan compatibles.
3. **No se infiere la cola ni la topología oculta:** los 15 casos normales se conservan como ciclos administrativos observados; `n_unknown_topologies_detected=0`. El método no prueba que haya o no haya recursos o etapas ocultas.
4. **La identidad no se deduce por proximidad:** POS/KDS se enlazan solo si comparten namespace de pedidos declarado, ID de caso y secreto de seudonimización suministrado externamente. CRM utiliza namespace `crm:`, que no se puede declarar como `orders:` ni al revés. No se unen leads a órdenes por semejanza del texto.
5. **Calidad y minimización:** cabecera de CSV exacta, hasta 10,000 filas por fuente, campos obligatorios, eventos duplicados, fechas y clocks no declarados. Cuarentena devuelve únicamente perfil, número de fila y código. Los registros aceptados contienen hash de evidencia y referencias seudónimas, **no los identificadores de negocio en claro**; la cadena raw completa y el secreto no se exportan en el paquete.
6. **No se estiman tasas de servicio ni capacidades**. No hay banco discreto, grid, modelos de colas, detector OOD, aprendizaje de topología, acciones de negocio o inferencia con LLM.

## Revisión adversativa y límites

- Una exportación con tres timestamps POS (pedido, pago, entrega) puede contener clicks administrativos con diferencias respecto al trabajo real. EV-02 **no mide el desvío entre click y evento físico**, no identifica tiempos de espera y no permite comparar procesos reales.
- El tipo de reloj y su exactitud son **metadatos declarados por el usuario**, no una certificación del hardware. Se necesita un ensayo de sincronización, documentación de semántica del proveedor, latencia y resolución reales antes de autorizar métricas cruzadas.
- La seudonimización por secreto privado reduce exposición accidental, **no equivale a anonimización legal**: un entorno real requiere seguridad de acceso, retención, consentimientos/bases jurídicas y separación de custodias. Un SHA de CSV no prueba integridad de origen, solo fija los bytes recibidos.
- `row quarantine` demuestra validación estructural, no conocimiento del mecanismo de datos faltantes; no imputar automáticamente etapas o servicios.
- Los CSV son producidos a partir del simulador EV-01. **No se validó ningún conector POS, KDS o CRM externo** ni se obtuvo muestra independiente. Ningún resultado es sensibilidad/especificidad de un clasificador empresarial.
- El código usa librerías estándar de Python, sin necesidad de PM4Py para ingestión. EV-01 usa PM4Py OSS bajo AGPL-3.0 para DFG experimental; sigue requiriendo revisión de licencia antes de uso comercial.
- D/B/M y ATMS no están conectados, ni deberían consumir métricas que no alcancen un estado de observabilidad apto. El registro de evidencia puede incorporarse a su contrato en fase posterior.

## Siguiente compuerta de producto

Antes de construir un estimador de colas o pipeline de decisión:
- conseguir **un CSV real autorizado** sin datos personales innecesarios, con diccionario del proveedor y referencia temporal del reloj;
- comprobar la semántica `evento administrativo` vs `acción física` a partir del proceso de operación y medir sesgo click→acción cuando exista;
- declarar qué unidades de identidad y qué enlaces POS/KDS son efectivamente legítimos, y qué información queda fuera de observación.

No puede prometerse descubrimiento de una estación latente a partir de un residual positivo, ni capacidad de la cafetería, ni un diagnóstico válido de una PYME.

**Gate permanente:** `BLOCKED_SYNTHETIC_EXTERNAL_FORMAT_NO_REAL_POS_KDS_CRM_DATA_OR_CLOCK_VALIDATION`. PR Draft sin merge.
