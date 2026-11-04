# F5 / WEBA · Ventanas POS frente a pulsos Tapo: comparación temporal descriptiva

**Fecha:** 2026-11-04 · **PR anterior:** #160, inventario de fuente real para un turno. **Estado:** desarrollo con señales externas auténticas; **NO** inferencia de servicios, identidad de clientes ni F5 independiente.

## Objetivo y protocolo antes de ejecutar el cruce

Se examina el turno de WEBA **20240223_evening**, ya usado para desarrollo, con los dos archivos originales fijados en #160:

- Libro POS: \`B.shift_data/orders_summary.xlsx\`, 588 filas, de las cuales 33 tienen \`order_time\` en el turno vespertino de 23-feb-2024.
- Snapshot Tapo: \`B.shift_data/20240223_evening/3.logs.txt\`, 10 sensores con 911 disparos devueltos y registros de tipo \`Open\`, \`Close\`, \`KeepOpen\`, \`Motion\`.

Ambos archivos se descargan desde el **commit externo fijo** \`d6841669e544579547c94b7ce1e8613bbd6b3a39\`, con tamaño y Git blob hash verificados por el mismo módulo de #160. No se ingestan HR, participantes, cuestionarios ni aceleración corporal.

El nuevo comparador solo emplea cuatro sensores: \`front_door\` (contacto), \`front_door_m\` (movimiento), \`zone_1\` y \`zone_2\`. No combina los demás dispositivos como si fueran órdenes físicas.

**Ventanas de análisis fijadas antes del cruce:** intervalos **[13:00,18:00) UTC del 23-feb-2024**, con paso de **30 minutos**, diez ventanas exactas **[a,b)**. El evento exactamente en una frontera pertenece a la ventana que empieza allí. La primera y la última ventana pueden estar truncadas por el historial Tapo: no se declara una jornada íntegra ni se infiere silencio como inactividad.

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

## Implementación y límites

- \`scripts/arena_cafe/weba_temporal_windows.py\`: extrae **en memoria** las horas de los 33 pedidos seleccionados y los eventos de los cuatro sensores. Reutiliza \`weba_source_readiness\` para validar el formato y los hashes. Aplica la rejilla fija, la conversión horaria explícita y control de conservación de conteos; no selecciona rezagos ni calcula un índice de éxito.
- \`tests/test_arena_cafe_weba_temporal_windows.py\`: pruebas de reloj Excel/12h/24h, valores ambiguos rechazados, frontera exacta [a,b), hora local frente a UTC, contaminación por ID, fuente Tapo validada y ausencia de ajuste retrospectivo. Son fixtures de parser, no cafeterías sintéticas adicionales.
- CI A1/F5 WEBA del PR #160 extendido: analiza **exactamente los mismos bytes externos**, ejecuta ambos lectores y publica dos JSON agregados, sin nuevo permiso al método D/B/M.

El alcance de la investigación queda delimitado: **observabilidad temporal agregada de canales externos**, no reconstrucción de actividades específicas del barista, reloj físico calibrado, medición de cuellos causales, validación de fluido E1 o G4/G5.

**Próxima compuerta científicamente defendible:** un diseño previamente declarado para validar qué señales corresponden a tareas (si los metadatos y etiquetados originales lo admiten) en turnos distintos, sin optimizar umbral/ventana sobre el conjunto usado para declarar éxito. Si la vinculación por pedido continúa ausente, abstenerse de inferir \`servicio_inicio\`/\`servicio_fin\` a nivel caso.
