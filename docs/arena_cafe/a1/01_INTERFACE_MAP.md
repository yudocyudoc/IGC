# A1 · F1: proyección O0/O1, `H_j` y matriz de consumo

**Estado de este incremento: `A1=PARTIAL`.** No hay todavía transporte hasta el *puerto nativo* con lectura y uso probados para los tres brazos. Los sobre V0 validados **no** equivalen a modelos ejecutados ni a consumo. Este documento no autoriza Buffalo live ni afirma G3/G5.

## Frontera física y temporal

**Fuente primaria de control:** EV-01 sintético. `ev01.trace_generator` y `SPEC` pertenecen al **evaluador**; el productor A1 `scripts/arena_cafe/evidence.py` solo recibe las proyecciones públicas POS/FULL ya exportadas. La cuarta etapa `transferencia_final` **no** sale al productor, ni por alias/contador/número de eventos, ni `resource_id` individuales. FULL se usa solo como *fuente de medición autorizada de preparación*, no como licencia para entregar al brazo todo lo que conoce el evaluador.

En el control actual: `cutoff=10 min`, intervalo físico **[0,10)**, muestras `t = 0,2,4,6,8,10`; la cuenta publicada en `t` usa únicamente eventos cuyo timestamp es **estrictamente menor que t**, incluidos los contadores en 10. Se conocen eventos del mismo mundo, no dos mundos independientes. No se usa observación posterior al corte para llenar un servicio inacabado.

| Campo | Fuente | Semántica de medición | Ventana/unidad | Proyección | Consumidor y operador `H_j` | Estado |
|---|---|---|---|---|---|---|
| `orders_created_cumulative` | POS, `pedido_creado` | Número acumulado de **pedidos**, no personas | [0,t), pedidos | O0 y O1 `observation_series` | Para flujo modelado `order_arrival_rate`: integrar en [0,t). No aplicar automáticamente a D/B/M | Proyección válida; `H_j` nativo aún no conectado |
| `delivered_cumulative` | POS, `pedido_entregado` | Pedidos terminales entregados, sin doble descuento | [0,t), pedidos | O0 y O1 `observation_series` | `H_j` teórico del stock entregado, **no** la derivada `delivery_rate` (pedidos/min) | Proyección válida; D solo admite esquema legado `{t,delivered}` con pulso |
| `n_completed_stage_services` | FULL autorizado, `preparacion` | Intervalos físicamente completados y observados en etapa autorizada | [0,cutoff), servicios completos | O1 `physical_observation` | Comparación de distribuciones/intervalos si un modelo expone servicio de preparación comparable | Agregado visible; sin mapeo D/B/M |
| `mean_wait_minutes_exact` | FULL: `etapa_entrada` → `servicio_inicio` de preparación | Espera física **observada**, no residual administrativo KDS | [0,cutoff), minutos, solo servicios completos | O1, promedio exacto racional | `H_j` por espera de preparación solo si el modelo la representa | No comparabilidad demostrada |
| `mean_service_minutes_exact` | FULL: `servicio_inicio` → `servicio_fin` de preparación | Duración física de preparación, no clic KDS | [0,cutoff), minutos, solo servicios completos | O1, promedio exacto racional | `H_j` por tiempo de servicio, si existe | No comparabilidad demostrada |
| `cutoff_minutes_exact` | Protocolo evaluador | Tiempo de censura, no variable física inferida | minutos desde origen sintético | Metadatos O0/O1 | Filtro anterior a todo `H_j` | Validado |

**Censura y selección:** los promedios O1 solo utilizan intervalos **completados** antes del corte; no son duración media de todos los pedidos ni muestra libre de sesgo. Con cero intervalos, `n=0` y los promedios quedan `null`, nunca cero fingido. Las vistas POS y FULL deben coincidir en todos sus eventos POS previos al corte; el proyector rechaza discrepancias.

## `INTERFACE-01`: fuente → sobre → consumidor nativo

| Brazo / condición | Transporte hasta sobre | Lectura/uso nativos | Estado `INTERFACE-01` | Motivo sustentado en fuente |
|---|---|---|---|---|
| D · O0 | `arm_view` acepta sobre | **No ejecutado** | `UNSUPPORTED_DOCUMENTED` | `arena_d_v01.validate_case` exige `input_profile.kind=pulse`, parámetros nominales y observaciones `{t,delivered}`; O0 no los inventa |
| D · O1 | `arm_view` acepta sobre | **No ejecutado** | `UNSUPPORTED_DOCUMENTED` | Además, ninguna interfaz D lee agregados de preparación O1 |
| B · O0 | `arm_view` acepta sobre; la ruta fuente Buffalo dispone de `backgroundKnowledge` | **No ejecutado; sin traza del consumo** | `NOT_VERIFIED` | Ver código `arena_b_native_runner.mjs`; no hubo petición LLM autorizada |
| B · O1 | Igual, datos O1 en `construction` si se enviaran | **No ejecutado; sin traza del consumo** | `NOT_VERIFIED` | El modelo puede ignorar el campo; cambio de salida tampoco probaría consumo |
| M · O0 | `arm_view` acepta sobre | **No ejecutado** | `UNSUPPORTED_DOCUMENTED` | `arena_m_short_e1.prepare` enumera E1 por roles ya configurados, sin proyección observación→molécula |
| M · O1 | Igual | **No ejecutado** | `UNSUPPORTED_DOCUMENTED` | O1 no crea automáticamente parámetros, topología ni calibración |

**Importante:** `UNSUPPORTED_DOCUMENTED` es un diagnóstico de interfaz **en esta revisión**, no una conclusión general sobre la capacidad científica del método. `NOT_VERIFIED` de B tampoco demuestra capacidad ni incapacidad.

Cada tupla `arm_id × condition_id` recibe `context_id`, `input_hash` y `source_snapshot_hash` propios. Los tres brazos dentro de **una** condición tienen el mismo `input_hash`; O0 y O1 tienen evidencia y hashes diferentes. **No existe aún** proceso, sesión, caché, ACL ni vista de ledger/ATMS aislados: `conditions_are_isolated_by_id_only=true` y `actual_process_cache_ledger_acl=NOT_IMPLEMENTED`. `CONDITION-01` queda pendiente y es requisito de A3.

## Reproducción offline (sin generador privado en el proyector)

A partir de los CSV públicos EV-01 que el **evaluador** haya exportado:

```bash
python -m scripts.arena_cafe.evidence \
  --pos ruta/01_POS_PUBLIC_EVENTS.csv \
  --full ruta/01_FULL_PUBLIC_EVENTS.csv \
  --cutoff 10 \
  --out artifacts/a1_public_001
```

Se generan exclusivamente `O0_VISIBLE.json`, `O1_VISIBLE.json`, `EVIDENCE01.json` e `INTERFACE01.json`. Ni la traza privada ni el DES forman parte de las entradas al productor. Los archivos de salida no se sobreescriben silenciosamente.

## Gates de este incremento

- `BASELINE-01`: dependencias y CI del corte F0-HIST registradas con campos faltantes `NOT_VERIFIED`.
- `EVIDENCE-01`: cutoff, semántica, unidades, paridad de fuente y ausencia de futuro/verdad privada comprobadas **sobre control sintético**.
- `INTERFACE-01`: seis estados conservadores reportados, **ninguno `SUPPORTED_AND_CONSUMED` todavía**. Por tanto, **A1 parcial**.
- `MEMORY-01` y `CONDITION-01`: **no realizados**. El ledger/ATMS original no debe aceptar eventos cruzados solo porque compartan un `round_id`.

**Próximo incremento concreto:** puente nativo tipado por brazo y trazas de lectura y uso real, incluyendo una política explícita para entradas POS que **no** son un pulso; aislamiento verificable de condición antes de habilitar iteraciones o memoria. No abrir G4/G5.
