# F5 · Captura instrumental para un piloto real (todavía SIN mediciones reales)

**Fecha:** 2026-11-03. **Plan:** revisión v3.2 (F3→F4→F5); continuación del PR #150. **Estado:** herramienta de adquisición/validación de evidencia instalada y probada con EV-01 sintético. **No es F5 prospectivo ni calibración de error.**

## Por qué esta entrega es distinta de los últimos expedientes de preparación

El testigo F4 produjo dos mecanismos con las mismas entregas O0 y consecuencias distintas bajo la misma intervención. O1 descartó ambos mecanismos al medir 9 preparaciones y un tiempo medio 15/17. Calcular la distancia de esos mecanismos a O1 **no mide el error de un sensor**: mezcla desacierto del mecanismo, heterogeneidad, efectos de censura y cualquier posible error del registro.

Esta entrega implementa un consumidor reutilizable de **eventos realmente instrumentados**, que será apto para recibir un piloto externo una vez exista una cafetería y fuentes autorizadas. No elige márgenes ni infiere la física de un modelo. Reusa el contrato de eventos físicos EV-01 y distingue censura, visitas repetidas y relojes. Un resultado limpio en datos sintéticos solo prueba que la herramienta respeta ese contrato.

## Contrato del archivo de eventos

El comando `scripts/arena_cafe/pilot_event_capture.py` acepta CSV en **minutos exactos racionales**, con las columnas en este orden:

```csv
event_id,case_id,visit_id,event_type,stage,resource_id,t_minutes_exact,source,clock_id,sensor_id
```

`case_id` seudonimizado identifica un pedido; `visit_id` identifica **cada visita concreta** a una etapa: si hay retrabajo o vuelve a preparación, ese nuevo paso tiene **otro** `visit_id`. `event_id` no se repite. No se aceptan nombres de clientes, campos extra o marcas de tiempo inventadas en lugar de las observadas.

- Eventos POS: `pedido_creado`, `pago_confirmado`, `pedido_entregado`; `source=pos` y los campos `visit_id,stage,resource_id` vacíos.
- Eventos instrumentados: `etapa_entrada`, `servicio_inicio`, `servicio_fin`; `source=instrumentacion_fisica`; nombre de etapa observado, recurso físico en inicio/fin. Un click KDS administrativo **no es una medición de servicio físico**.
- `clock_id` es el identificador declarado del reloj; no es certificado de sincronía. `sensor_id` es el instrumento declarado; dos nombres distintos tampoco certifican independencia.
- Todo registro tiene que estar en **[0,cutoff)**. No se incorporan eventos posteriores para completar trayectorias de servicio. A la izquierda y hasta el corte, entrada sin inicio indica espera censurada; inicio sin fin indica servicio censurado; fin sin inicio es inconsistente y se rechaza.
- La herramienta no impone cuatro estaciones, tasas, capacidades, servidores, rutas únicas ni tiempos de servicio fijos. Sí verifica recursos que no pueden atender dos servicios simultáneos bajo un reloj compartido, y que una visita completa tenga entrada→inicio→fin consistentes.
- Con **un único reloj declarado** calcula, por etapa observada, servicios completados antes del corte y medias de espera y servicio **solo de servicios completados**. No llama «tiempo medio de todos los pedidos» a esa media censurada.
- La enumeración de secuencias de entradas físicas **separa los casos con entrega terminal observada de los pedidos todavía pendientes al corte**: estos últimos tienen prefijos censurados que **no son variantes de proceso**. Incluso una secuencia de un pedido entregado prueba solo las actividades **registradas**, no cobertura completa de todas las etapas ocultas. Ninguna de estas cifras constituye por sí sola descubrimiento causal ni ganancia atribuible a PM.
- Con **múltiples relojes sin calibración externa**, retiene la señal de falta de sincronía y **no publica medias por etapa ni orden temporal entre etapas** que mezclen esos relojes. Las rutas observadas con un solo reloj siguen siendo sucesiones registradas, no topología causal demostrada.

## Contraste voluntario entre dos instrumentos

Opcionalmente puede recibirse un segundo archivo CSV con:

```csv
pair_id,primary_event_id,secondary_sensor_id,secondary_clock_id,secondary_t_minutes_exact
```

El `primary_event_id` debe corresponder exactamente a un evento del CSV primario y el segundo sensor declarado debe ser distinto. El reporte calcula solamente `max|t_primario−t_secundario|`, expresado como fracción racional exacta. **No lo convierte en margen de error de ninguno de los instrumentos.** Dos lecturas discrepantes no dicen cuál es correcta, y aunque coincidan no prueban ausencia de sesgo común. Hacen falta una referencia con incertidumbre trazable, calibración independiente, resolución verificable, sincronización/deriva de reloj y repetición suficiente.

## Ejecución

```bash
python -m scripts.arena_cafe.pilot_event_capture \
  --events /ruta/registro_instrumentado_pre_corte.csv \
  --pairs /ruta/pares_independientes.csv \
  --cutoff 10 \
  --source-context real_pilot_declared \
  --out /ruta/resultado_piloto.json
```

`--pairs` es opcional. `real_pilot_declared` es una **declaración del operador**, no una certificación automática de que la fuente es real ni de que obtuvo consentimiento. La CI nunca usa esta etiqueta: ejecuta solamente `synthetic_fixture`. El reporte contiene SHA-256 de los archivos leídos, totales, conteos censurados, rutas observadas y diagnósticos instrumentales; evita divulgar IDs de los pedidos o tiempos caso por caso.

El archivo `--out` debe ser nuevo; no se sobrescribe una ejecución anterior silenciosamente. El operador o custodio conserva por separado los registros originales, autorizaciones, identificación de instrumentos, muestras de reloj y procedimientos. Este script **no gestiona** por sí solo custodia independiente, consentimiento, una segunda condición S1 o reserva prospectiva.

## Prueba de ingeniería sobre el control histórico

La CI invoca el generador original de eventos EV-01 solo en el **job del evaluador**, transforma los registros FULL previos al minuto 10 a este contrato y comprueba que reproduzcan:
- 15 pedidos creados;
- 9 preparaciones completadas antes del corte;
- media exacta de duración `15/17` minutos;
- media exacta de espera (solo las nueve terminadas) `1204/765` minutos;
- una secuencia observada entre los **8 pedidos ya entregados** al corte, con los prefijos truncados de pedidos pendientes etiquetados como **censurados y no como variantes**;
- ausencia de dato suficiente para calibrar error físico, aunque los eventos sintéticos sean exactos.

Las pruebas adversariales cubren falta de un inicio físico, campos KDS disfrazados, eventos futuros, servicio solapado por un mismo recurso, visitas repetidas legítimas y mezcla de relojes. Los reportes sintéticos son **evaluador-only**; la CI publica solo el resumen agregado, no el log completo ni la física privada al productor.

## Estado de los métodos, PM y próxima decisión

**F3/A3 continúa parcial:** D y M tienen ejecuciones nativas registradas; Buffalo aún no generó una inferencia propia sobre O0/O1 en una ejecución live autorizada. El contrato de captura de datos no sustituye esa autorización ni acredita CONDITION-01.

**F5 permanece NO ABIERTO.** Aún faltan: un piloto verdaderamente instrumentado, sincronía y referencia de relojes con incertidumbre sustentada, replicación y heterogeneidad, estimación de fallos de captura sin confundirlos con censura, verificación de viabilidad física de la intervención, S0/S1 y `H_j` definidos prospectivamente, aislamiento de brazos/condiciones y nueva reserva G4→G5.

**Minería P:** este lector no ejecuta PM4Py ni interpreta un camino observado como causa del cuello. Su capacidad de capturar visitas repetidas permite **detectar** una regularidad procesual si una fuente física la registra. Solo después se preguntaría si aporta un requisito nuevo a B1/B2 y, de ser así, se harían ablaciones con/sin P por brazo con evidencia idéntica y reserva independiente.

**Límite no negociable:** reporte `instrumental_error_calibrated=false`, `empirical_compatibility_tolerance=null`, `G4=G5=NOT_RUN`. No hay malla, otro DES, estimación arbitraria de sensores, nuevos escenarios reservados ni ejecución de proveedores.
