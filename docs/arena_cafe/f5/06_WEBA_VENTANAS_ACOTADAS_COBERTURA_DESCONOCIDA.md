# WEBA · F5 · Ventanas acotadas al turno y censura instrumental explícita

**Fecha:** 2026-11-04. **Estado:** corrección metodológica de PR #161–#163; desarrollo retrospectivo sobre los **mismos tres turnos** ya publicados. **No** crea una nueva muestra independiente, no calibra relojes y no identifica servicios físicos.

## Problema corregido

Las comparaciones originales de WEBA usaron **diez ventanas de 30 minutos**, `[13:00,18:00)` UTC. La auditoría posterior (#163) confirmó que esa rejilla **no coincide** con los horarios reales declarados en `shift_summary.xlsx`. Además, los `3.logs.txt` son snapshots históricos Tapo: `sum == longitud` confirma integridad de respuesta, **no continuidad de medición**. Un evento ausente no demuestra inactividad, y un pulso presente no identifica ni cliente ni servicio.

En el nuevo operador, cada ventana se cruza contra `[inicio_declarado, fin_declarado)`. Los relojes de esos límites están en formato `HHhMM` y se convierten **solo condicionalmente** usando `Europe/Budapest`; no hay una calibración POS↔Tapo.

| Turno ya auditado | Límite declarado local | Límite UTC condicional | Tiempo de turno declarado |
|---|---|---|---:|
| `20240223_evening` | 14:36–18:31 | 13:36–17:31 | 235 min |
| `20240304_evening` | 14:54–18:50 | 13:54–17:50 | 236 min |
| `20240308_evening` | 14:33–18:41 | 13:33–17:41 | 248 min |

Para cada ventana original se informan *minutos dentro del turno*, *minutos fuera del turno*, *minutos dentro del turno anteriores a la última exportación Tapo* y *minutos posteriores a esa exportación*. Esta última categoría es **imposibilidad lógica de observación con el snapshot existente**; el intervalo anterior a la exportación es solo **potencialmente observable**, con continuidad **NO DEMOSTRADA**. Ni siquiera una ventana completa dentro del turno significa que los sensores funcionaran de manera ininterrumpida.

### Caso crítico: 8 de marzo

El último timestamp de exportación del snapshot es `17:37:02.167 UTC`, mientras que el final declarado del turno es `17:41 UTC`, suponiendo Budapest. El tiempo entre ambos, aproximadamente **3 minutos 57.833 segundos**, no pudo formar parte de esa exportación. Cualquier cero Tapo en ese tramo **es ausencia de evidencia por falta de captura**, no evidencia de ausencia de actividad. La comparación de POS conserva por separado cualquier pedido en dicho intervalo.

No se recalibra la hora POS para hacerla coincidir con Tapo. La lectura principal la interpreta como hora de pared Budapest y la alternativa conserva la lectura UTC literal, sin escoger la que produzca mejores resultados. Las dos son análisis de sensibilidad condicionados, **no sincronización comprobada**.

## Contadores permitidos, sin cambiar el fenómeno observado

- **POS:** cantidad de **pedidos recibidos** en la fecha/turno correspondientes, anterior, dentro y posterior a los límites declarados; además se distingue si el timestamp suponiendo Budapest cae después de la exportación Tapo. **No** significa llegada física por la puerta.
- **Tapo:** cantidades de disparos **ya retornados** por `front_door`, `front_door_m`, `zone_1`, `zone_2`, antes/dentro/después del turno. Se conserva la misma fuente y la comprobación de todos los diez sensores realizada en #163; no se equipara movimiento a trabajo.
- **Ventanas mixtas:** se informa que contienen pulsos con cero pedidos POS solo como **coincidencia descriptiva de registros acotados al turno**. Esos pulsos no son falsos positivos, clientes no registrados ni necesariamente tareas sin pedido.
- **Sin continuidad demostrada:** todo intervalo anterior a la exportación que pertenece al turno lleva etiqueta `UNKNOWN_SENSOR_CONTINUITY`; los minutos posteriores al último volcado Tapo son `CANNOT_OBSERVE_POST_EXPORT`. Nunca se etiqueta `IDLE`, `ACTIVE` o `COMPLETE_COVERAGE` basándose en la presencia/ausencia de eventos.

El algoritmo **no estima tasas de servicio, correlaciones, desfasajes óptimos, cuellos de botella o probabilidades de actividad**. La nueva tabla evita dividir eventos entre minutos supuestamente observados y no convierte salidas parciales en métricas normalizadas de capacidad.

## Código y custodia

- `scripts/arena_cafe/weba_shift_bounded_windows.py`: se apoya en el auditor `weba_instrument_integrity.py` del PR #163, validando los mismos **cinco originales con hashes fijos** antes del conteo. Reutiliza el esquema de ventanas del PR #161 y los nombres de canales originales.
- `tests/test_arena_cafe_weba_shift_bounded_windows.py`: casos de límites semiabiertos, inicios/finales parciales, tiempo posterior a exportación, tiempo sin pulsos no identificado como inactividad, POS posterior al snapshot y ausencia de identificadores.
- CI añade la ejecución al flujo WEBA real de #163. Publica **solo un informe agregado nuevo** junto al informe original; los bytes POS, metadatos y Tapo se eliminan antes del artefacto.

La selección de turnos es **retrospectiva y ya revelada**. No se admite una nueva condición O2 para D/B/M, no se deducen eventos `servicio_fin`, y **G4/G5 siguen NOT_RUN; F5 independiente NOT_CREATED**.

## Decisión metodológica siguiente

La regla de observación ya respeta las fronteras documentadas; persisten dos incógnitas que el dataset abierto no resuelve automáticamente: **(1)** continuidad y sensibilidad del sensor durante el turno; **(2)** offset/error efectivo entre POS y Tapo. Si una de ellas es crucial para el siguiente modelo, necesitaremos nueva documentación instrumental, sincronización auditada u observación independiente. **No** aumentar el número de turnos antes de aclarar el operador físico que realmente queremos estimar.
