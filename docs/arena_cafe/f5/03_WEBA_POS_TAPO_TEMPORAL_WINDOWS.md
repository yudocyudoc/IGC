# F5 / WEBA · Ventanas POS frente a pulsos Tapo: comparación temporal descriptiva

**Fecha:** 2026-11-04 · **PR anterior:** #160, inventario de fuente real para un turno. **Estado:** desarrollo con señales externas auténticas; **NO** inferencia de servicios, identidad de clientes ni F5 independiente.

## Objetivo y protocolo antes de ejecutar el cruce

Se examina el turno de WEBA **20240223_evening**, ya usado para desarrollo, con los dos archivos originales fijados en #160:

- Libro POS: \`B.shift_data/orders_summary.xlsx\`, 588 filas, de las cuales 33 tienen \`order_time\` en el turno vespertino de 23-feb-2024.
- Snapshot Tapo: \`B.shift_data/20240223_evening/3.logs.txt\`, 10 sensores con 911 disparos devueltos y registros de tipo \`Open\`, \`Close\`, \`KeepOpen\`, \`Motion\`.

Ambos archivos se descargan desde el **commit externo fijo** \`d6841669e544579547c94b7ce1e8613bbd6b3a39\`, con tamaño y Git blob hash verificados por el mismo módulo de #160. No se ingestan HR, participantes, cuestionarios ni aceleración corporal.

El nuevo comparador solo emplea cuatro sensores: \`front_door\` (contacto), \`front_door_m\` (movimiento), \`zone_1\` y \`zone_2\`. No combina los demás dispositivos como si fueran órdenes físicas.

**Ventanas de análisis fijadas antes del cruce (pero con conocimiento previo del rango temporal Tapo de #160; no constituyen una preinscripción independiente):** intervalos **[13:00,18:00) UTC del 23-feb-2024**, con paso de **30 minutos**, diez ventanas exactas **[a,b)**. El evento exactamente en una frontera pertenece a la ventana que empieza allí. La primera y la última ventana pueden estar truncadas por el historial Tapo: no se declara una jornada íntegra ni se infiere silencio como inactividad.

## Hipótesis explícita de reloj, no calibración

Los timestamps del Tapo son segundos Unix de disparos físicos, interpretados como UTC. Los valores POS \`order_time\` se interpretan **condicionalmente** como hora local de **Europe/Budapest**, que el 23-feb-2024 tiene UTC+01, y se convierten a UTC antes de contarse. La documentación consultada **no demuestra** que los relojes POS y Tapo estuvieran sincronizados ni que \`order_time\` declarara formalmente esa zona.

Como sensibilidad **no optimizada**, se computa además cuántas marcas POS caerían dentro de la misma rejilla si \`order_time\` se interpretase literalmente como UTC. Ninguna interpretación se escoge a partir de una correlación o coincidencia; los resultados bajo ambas son **descriptivos**, no un cálculo de offset o deriva. No hay enlaces evento↔pedido.

## Lo que publica el algoritmo

Por cada ventana de 30 minutos únicamente:

- Conteo de pedidos POS con marca temporal bajo la hipótesis \`Europe/Budapest\`.
- Conteos independientes de disparos de contacto de puerta, movimiento de puerta y zonas 1/2.
- Totales dentro y fuera de la rejilla, estadísticas de ventanas que contienen **al menos una marca POS y una marca de sensor**, y estado de sensibilidad horaria.

El resultado no publica identificadores, horas individuales de pedido, timestamps físicos individuales, POS monetario, SSID/MAC/IP, IDs de Tapo ni registros de participantes. Los archivos originales se eliminan de CI antes de publicar el JSON agregado.

**La co-presencia en una ventana no demuestra co-causalidad ni que el pulso Tapo pertenezca al pedido POS.** No hay prueba de acceso a \`despacho.servicio_fin\` por pedido, de presencia de varios empleados o de equivalencia con el escenario sintético EV-01.

## Primer resultado empírico: comparación de canales, sin enlace a pedidos

Tras ejecutar el comparador sobre los archivos originales (hashes iguales a PR #160), la **hipótesis de reloj POS local Budapest** coloca los **33 pedidos** en la rejilla fija [13:00,18:00) UTC. Si, **solo para sensibilidad**, interpretáramos los mismos valores POS como UTC directamente, **32** quedarían dentro y **uno fuera**. Esta diferencia **no valida** que el reloj POS sea efectivamente Budapest ni permite estimar un offset a posteriori.

| Ventana UTC, 23-feb-2024 | POS (reloj local supuesto) | Puerta contacto Tapo | Puerta movimiento Tapo | Zona 1 Tapo | Zona 2 Tapo |
|---|---:|---:|---:|---:|---:|
| 13:00–13:30 | 0 | 0 | 0 | 0 | 0 |
| 13:30–14:00 | 6 | 32 | 18 | 25 | 36 |
| 14:00–14:30 | 4 | 16 | 13 | 18 | 38 |
| 14:30–15:00 | **0** | **22** | **12** | **9** | **14** |
| 15:00–15:30 | 9 | 22 | 11 | 15 | 40 |
| 15:30–16:00 | 2 | 24 | 15 | 21 | 31 |
| 16:00–16:30 | 4 | 13 | 12 | 18 | 20 |
| 16:30–17:00 | 7 | 18 | 22 | 24 | 23 |
| 17:00–17:30 | 1 | 9 | 10 | 14 | 33 |
| 17:30–18:00 | **0** | **5** | **2** | **3** | **9** |
| **Total** | **33** | **161** | **115** | **147** | **244** |

**Control negativo no trivial:** hay **dos ventanas** con POS=0 pero con actividad en los cuatro sensores. Esos intervalos reúnen, respectivamente, **27 disparos de contacto**, **14 de movimiento de puerta**, **12 en zona 1** y **23 en zona 2**. Eso **no** significa que los sensores sean erróneos; podrían registrar limpieza, movimiento, uso de zona sin venta, entradas/salidas u otros fenómenos, o reflejar carencias de los registros POS. Tampoco permite inferir servicios pendientes. Lo único demostrado es que **un disparo no representa necesariamente un pedido POS en su misma ventana**.

En **siete de las diez ventanas** hay al menos un pedido POS y pulsos de los cuatro sensores, pero los sensores emiten pulsos en nueve de las diez ventanas: **la co-presencia es poco discriminante y no acredita vinculación por pedido**. Es un resultado descriptivo de una jornada y una hipótesis horaria, no correlación calibrada ni ventaja de un método.

La primera ventana termina antes del primer disparo observado del snapshot Tapo y la última continúa más allá del último disparo registrado. Los ceros de esos extremos **no deben interpretarse como ausencia física de actividad**: el snapshot no acredita cobertura continua.

## Implementación y límites

- \`scripts/arena_cafe/weba_temporal_windows.py\`: extrae **en memoria** las horas de los 33 pedidos seleccionados y los eventos de los cuatro sensores. Reutiliza \`weba_source_readiness\` para validar el formato y los hashes. Aplica la rejilla fija, la conversión horaria explícita y control de conservación de conteos; no selecciona rezagos ni calcula un índice de éxito.
- \`tests/test_arena_cafe_weba_temporal_windows.py\`: pruebas de reloj Excel/12h/24h, valores ambiguos rechazados, frontera exacta [a,b), hora local frente a UTC, contaminación por ID, fuente Tapo validada y ausencia de ajuste retrospectivo. Son fixtures de parser, no cafeterías sintéticas adicionales.
- CI A1/F5 WEBA del PR #160 extendido: analiza **exactamente los mismos bytes externos**, ejecuta ambos lectores y publica dos JSON agregados, sin nuevo permiso al método D/B/M.

El alcance de la investigación queda delimitado: **observabilidad temporal agregada de canales externos**, no reconstrucción de actividades específicas del barista, reloj físico calibrado, medición de cuellos causales, validación de fluido E1 o G4/G5.

**Próxima compuerta científicamente defendible:** un diseño previamente declarado para validar qué señales corresponden a tareas (si los metadatos y etiquetados originales lo admiten) en turnos distintos, sin optimizar umbral/ventana sobre el conjunto usado para declarar éxito. Si la vinculación por pedido continúa ausente, abstenerse de inferir \`servicio_inicio\`/\`servicio_fin\` a nivel caso.
