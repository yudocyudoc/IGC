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


## Primer resultado empírico de la corrección (mismos datos, nuevo recorte)

Se ejecutó el nuevo operador sobre los cinco archivos originales, con identidad de bytes confirmada mediante hashes y con la rejilla anterior intacta. **Estos resultados no proceden de turnos nuevos ni deben evaluarse como experimento ciego.**

| Turno | Pulsos en los archivos de los 4 sensores seleccionados | Pulsos ANTES del turno | Pulsos DENTRO del turno | Pulsos DESPUÉS del turno |
|---|---:|---:|---:|---:|
| 23 febrero | **667** | 12 | **638** | 17 |
| 4 marzo | **660** | 353 | **307** | 0 |
| 8 marzo | **704** | 226 | **478** | 0 |

Esta tabla **solo** cubre los cuatro canales `front_door`, `front_door_m`, `zone_1` y `zone_2`. El universo completo de diez sensores sigue registrando 911, 888 y 889 disparos por turno, respectivamente. Los conteos se conservan; las porciones fuera de turno no se borran del origen, pero ya no se suman como actividad del turno para la comparación.

**En el 4 de marzo, 353/660 disparos de los cuatro canales seleccionados están fuera del turno declarado.** El análisis original de ventanas sin recortar confundía una parte importante del historial de dispositivo con actividad de la sesión vespertina.

| Turno | Pedidos POS recibidos dentro del turno, hipótesis Budapest | Pedidos dentro del turno si la hora POS se interpretara como UTC | Ventanas con pulsos y cero nuevos pedidos POS después del recorte |
|---|---:|---:|---:|
| 23 febrero | 33 | 25 | 2 |
| 4 marzo | 7 | 6 | 2 |
| 8 marzo | 15 | 13 | 3 |

**Sensibilidad horaria más notable:** los 33 pedidos de febrero permanecen dentro del turno bajo el supuesto Budapest, pero **solo 25** caerían dentro si el número Excel fuese una hora UTC. Esto es una advertencia sobre la identificación de reloj, **no evidencia de que un supuesto sea el correcto**.

### Ventana crítica del 8 de marzo, 17:30–18:00 UTC

El intervalo declarado del turno termina a las **17:41 UTC** y la última respuesta Tapo fue exportada a las **17:37:02.167 UTC**. Por tanto, los treinta minutos de esta ventana se dividen en:

- **19 minutos fuera del turno**, sin intentar medir actividad de ese turno.
- **~7.036 minutos anteriores a la exportación dentro del turno**, pero **sin continuidad de Tapo demostrada**.
- **~3.964 minutos posteriores a la exportación y anteriores al final declarado**, **imposibles de observar** con ese snapshot.

No hay inferencia de estado `IDLE` en ninguno de estos tramos. En el archivo de POS seleccionado, los quince pedidos del 8 de marzo quedan anteriores al final de la exportación bajo la hipótesis Budapest, pero eso **no informa** de la actividad física faltante en los últimos cuatro minutos.

### Qué cambia en nuestra interpretación previa

Las ventanas con pulsos y cero pedidos POS dejan de ser **2 / 3 / 4** (23-feb / 4-mar / 8-mar, cálculo sin recortar de #161–#162) y pasan a ser **2 / 2 / 3** tras recortar a los turnos. Esto confirma que la actividad ambiental del archivo no se reduce a las ventas registradas, pero **no** demuestra servicios activos, pedidos acumulados ni falsos positivos de ningún sensor.

La auditoría demuestra que un **conteo físicamente registrado** puede ser válido como registro de pulsos y, al mismo tiempo, **ser inadmisible para medir carga de una operación en un intervalo específico**. La validez de la observación exige tanto su procedencia como una delimitación temporal apropiada y un operador físicamente justificado.

**Ejecución:** CI reproducible sobre el mismo commit externo WEBA fijado en #160, sin alterar D/B/M, sin sensores personales ni etiquetas físicas artificiales, con resultados JSON agregados y pruebas sobre cortes, censura y relojes.

## Decisión metodológica siguiente

La regla de observación ya respeta las fronteras documentadas; persisten dos incógnitas que el dataset abierto no resuelve automáticamente: **(1)** continuidad y sensibilidad del sensor durante el turno; **(2)** offset/error efectivo entre POS y Tapo. Si una de ellas es crucial para el siguiente modelo, necesitaremos nueva documentación instrumental, sincronización auditada u observación independiente. **No** aumentar el número de turnos antes de aclarar el operador físico que realmente queremos estimar.
