# WEBA · F5 · Auditoría de integridad instrumental: Tapo y reloj POS

**2026-11-04. Naturaleza:** auditoría de procedencia/cobertura sobre tres turnos REALES previamente inspeccionados en PR #160, #161 y #162. **No** es preregistro ciego, evaluación G5, atribución de tareas, medición física por pedido, ni experimento nuevo de cafetería.

## Fuentes fijas y regla de custodia

Origen académico: [Tran et al., *Scientific Data* (2025)](https://www.nature.com/articles/s41597-024-04348-z), [WEBA Figshare v3](https://doi.org/10.6084/m9.figshare.27186516.v3); copia GitHub en commit fijo `d6841669e544579547c94b7ce1e8613bbd6b3a39`.

Se inspeccionan exactamente **cinco fuentes originales**, y sus hashes Git blob/tamaños se comprueban antes de analizar:

| Archivo | Propósito, sin información individual en la salida |
|---|---|
| `B.shift_data/orders_summary.xlsx` | Tipo de celda de `order_time`, disponibilidad de horas, formato efectivo de fechas, presencia o ausencia de zona horaria explícita |
| `B.shift_data/shift_summary.xlsx` | Solo `shift_date`, `time_of_day`, `start_time`, `end_time`; se **ignora** `par_ID` y toda información de ingresos/participantes |
| `B.shift_data/20240223_evening/3.logs.txt` | Primer turno de desarrollo |
| `B.shift_data/20240304_evening/3.logs.txt` | Primer turno replicado, ya divulgado |
| `B.shift_data/20240308_evening/3.logs.txt` | Segundo turno replicado, ya divulgado |

**Ningún registro de salud, acelerómetro personal, cuestionario, identidad de participante, ingresos, ítem comprado, ID de pedido o dispositivo se publica.** Los cinco originales se eliminan antes del artefacto agregado de CI.

## Pregunta 1: qué *no* demuestra un snapshot Tapo

Los `3.logs.txt` contienen respuestas `TriggerLogsResult` con un bloque por sensor. Un mensaje del código dice **`last 50 trigger logs`**, pero la cantidad efectivamente devuelta puede ser mayor de 50 por sensor. Se verifican, por los diez sensores de cada turno, el número de registros, `sum`, unicidad de los IDs dentro de la misma respuesta, orden descendente de timestamps, y el rango de tiempos registrado.

**Se distingue estrictamente:**
- `sum == longitud de la lista devuelta` indica **consistencia interna de una respuesta**, NO captura completa durante el turno.
- La etiqueta `last 50` no es evidencia de paginación ni de un máximo real de 50 eventos: verificar directamente el número devuelto. El archivo puede ser un **snapshot único de historial** capturado al final, no un flujo en tiempo real con continuidad demostrada.
- Los saltos en los IDs del proveedor **no equivalen a eventos perdidos** sin especificación de su numeración. Del mismo modo, un intervalo sin movimientos no demuestra dispositivo encendido y ambiente inactivo: faltan *heartbeats*, auditoría de caídas y prueba independiente de sensibilidad.
- La primera/última fecha de disparo no es por sí misma el inicio/fin de cobertura. Se presenta la fecha de exportación del log por separado.
- Es posible que el historial de una carpeta `evening` contenga eventos anteriores a esa jornada. Debemos distinguirlos usando únicamente los límites de captura **declarados en `shift_summary.xlsx`**.

El tratamiento de fechas utiliza una hipótesis de hora local `Europe/Budapest` para `start_time` y `end_time`, cuya zona y offset **no están verificados instrumentalmente**. Se cuentan disparos anteriores, interiores y posteriores al intervalo *supuesto*, sin imputar períodos de actividad.

## Pregunta 2: cuál es la procedencia del reloj POS

La tabla de variables del artículo (Tabla 9) describe `order_time` como una **hora de recepción de pedido en formato de 12 horas, sin especificar una zona horaria ni la calibración del dispositivo**. Describe `order_date` como `dd/mm/yyyy`, mientras que el archivo previamente auditado almacena valores de fecha `YYYYMMDD`; por tanto, **la especificación del artículo no reemplaza una inspección del archivo**.

El nuevo auditor:
1. Lee el tipo de almacenamiento OOXML de celdas `order_time` sin publicar su valor individual.
2. Cuenta entradas interpretables como reloj de pared, entradas sin hora, valores con sufijo `Z` o `±HH:MM`, y codificación real de fechas.
3. Contrasta la existencia de `start_time` y `end_time` del `shift_summary`; **tener esos metadatos no calibra el POS frente a Tapo** ni confirma su precisión de segundos.
4. **No** escoge un offset mediante correlación POS–Tapo, no rellena horas, no transforma aperturas de puerta en clientes, no atribuye señales a órdenes.

## Umbral de aprobación

La CI debe autenticar cinco fuentes fijas, reconocer exactamente **10 respuestas de sensor por cada uno de los tres turnos**, conservar las **911, 888 y 889** entradas Tapo ya documentadas, e informar sus rangos y su distribución dentro/fuera de los intervalos de turno declarados. Si no es posible leer las horas de turno de la fuente original, **bloquear** la comparación, sin inventar horarios. Si la integridad original no se prueba, marcarlo explícitamente como **NO ESTABLECIDA**, aunque pase la CI.

**La conclusión permitida es descriptiva:** cuánta evidencia temporal aparece en los archivos, de dónde proviene, qué limitaciones tienen sus relojes e historial. Esta auditoría no establece `servicio_fin`, duración de proceso físico, causalidad, sincronización de relojes, independencia F5 ni G4/G5.

## Código y trazabilidad

- `scripts/arena_cafe/weba_instrument_integrity.py` — auditoría desde bytes externos fijados.
- `tests/test_arena_cafe_weba_instrument_integrity.py` — pruebas estructurales de los parsers, derivación condicionada de límites y ausencia de datos individuales.
- `.github/workflows/arena-cafe-f5-weba-instrument-integrity.yml` — descarga, validación, ejecución y publicación exclusiva del JSON agregado.

**Estado no negociable:** D/B/M no modificados; reloj POS–Tapo no calibrado; cobertura continua no certificada; G4 y G5 `NOT_RUN`; F5 reserva `NOT_CREATED`.
