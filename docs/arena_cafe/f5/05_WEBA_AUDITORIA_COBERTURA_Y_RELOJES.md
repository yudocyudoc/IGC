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


## Resultados observados en los cinco archivos originales

**Auditoría ejecutada con fuentes auténticas, antes de cualquier intento de inferencia de eventos de servicio.** El libro `shift_summary.xlsx` contiene **56 filas de metadatos de turno**; el repositorio WEBA enumera **55 carpetas de turnos**. Esta diferencia requiere cotejo de cobertura y no autoriza afirmar por sí sola que falta un archivo específico.

El formato **real** de `start_time` y `end_time` en los tres turnos es `HHhMM` (ejemplo `14h36`), no la hora de 12 horas presentada en la Tabla 9. La conversión de hora local a UTC de esta tabla asume, sin calibración, `Europe/Budapest` (UTC+01 en febrero/marzo 2024).

| Turno | Intervalo declarado del registro, hora local | Tapo total | Antes del inicio | Dentro de intervalo | Después del final |
|---|---|---:|---:|---:|---:|
| 20240223_evening | 14:36–18:31 | **911** | **16** | **873** | **22** |
| 20240304_evening | 14:54–18:50 | **888** | **436** | **452** | **0** |
| 20240308_evening | 14:33–18:41 | **889** | **287** | **602** | **0** |

**Estos son conteos de disparos ambientales registrados dentro/fuera del intervalo nominal, NO pruebas de presencia de clientes, trabajo en curso o pérdida de eventos.** Los valores resultan de comparar segundos Unix de sensores con límites de turno convertidos desde horas de pared. Sin confirmar la referencia horaria original, la clasificación sigue siendo *condicional*.

### Exportación de snapshots frente al fin declarado

| Turno | Última hora del volcado Tapo (UTC) | Fin del turno bajo hipótesis Budapest (UTC) | Advertencia |
|---|---|---|---|
| 23 feb. | 17:35:41 | 17:31:00 | Exportación posterior al fin; **no acredita cobertura retrospectiva** |
| 4 mar. | 17:50:03 | 17:50:00 | Exportación apenas posterior al fin; **no acredita cobertura retrospectiva** |
| **8 mar.** | **17:37:02** | **17:41:00** | **Volcado unos 3 min 58 s ANTES de terminar el turno declarado**: su tramo final ni siquiera estaba disponible en ese momento |

Los snapshots de los tres turnos comprenden **10 respuestas (una por sensor)** con `sum` igual a la longitud de los registros devueltos. Se verificaron IDs sin duplicación dentro de cada respuesta y marcas ordenadas en sentido descendente. **Seis sensores** devuelven más de 50 registros en febrero, **seis** en marzo 4 y **cinco** en marzo 8: el texto `last 50 trigger logs` no restringe realmente la respuesta a 50.

Pero faltan pruebas de continuidad y calidad del instrumento: no hay secuencias de *heartbeats* ni control de desconexiones; los saltos de IDs no prueban pérdidas y un período sin disparos no significa ausencia de movimiento. Los sensores no necesariamente comparten inicio de historial, incluso dentro del mismo archivo.

### Hora POS: fuente distinta de un reloj sincronizado

El archivo `orders_summary.xlsx` contiene **588 filas de transacciones**. Todas tienen una hora legible como reloj de pared, almacenada en **588 celdas numéricas de Excel** (`t` OOXML por defecto), no en 588 cadenas con zona horaria. En las horas de pedido inspeccionadas se encontraron:

- **588/588** fechas codificadas como `YYYYMMDD`, en contraste con `dd/mm/yyyy` descrito en la Tabla 9.
- **0/588** valores con sufijo de zona horaria (`Z` o `±HH:MM`); tampoco hay marcas literales AM/PM en los valores numéricos.
- **0** horas vacías en este libro concreto; esto no invalida lo dicho por los autores sobre falta de timestamps en otros turnos o etapas de recopilación.

**Un número fraccionario de Excel da hora del día, NO fecha/huso calibrados por sí mismos.** El artículo identifica `order_time` como hora de recepción en el POS, no llegada física a la cafetería; no documenta aquí un procedimiento que certifique sincronía, error u offset entre el POS y los Tapo. La hipótesis `Europe/Budapest` es plausible, pero permanece **sin verificación instrumental independiente**.

### Corrección metodológica a la lectura de PR #161 y #162

La rejilla común `[13:00,18:00)` UTC utilizada antes era útil para comparar **conteos de los archivos**, pero **no equivale a una rejilla enteramente dentro de cada turno real**:

- El turno del 23-feb empieza a **13:36 UTC** y termina a **17:31 UTC** bajo la hipótesis horaria; algunos minutos de las ventanas extremas quedan fuera del registro declarado.
- El 4-mar empieza a **13:54 UTC** y termina a **17:50 UTC**. Además, **436/888 disparos** de su archivo preceden al inicio del turno.
- El 8-mar empieza a **13:33 UTC**, termina a **17:41 UTC**, pero el snapshot se guardó cerca de **17:37 UTC**, por lo que el final del registro está **censurado por el momento de exportación**.

Por ello, el hallazgo de pulsos Tapo en «ventanas sin pedidos POS» de #161/#162 **no puede interpretarse uniformemente como actividad dentro del turno** sin recortar ambas fuentes a los límites originales y validar la referencia horaria. Tampoco la coincidencia entre canales por ventana valida identificación de tareas. Esta auditoría **corrige la lectura**, no recalibra retrospectivamente un reloj ni reoptimiza las ventanas.

**Decisión técnica:** para una nueva comparación descriptiva, separar `[inicio declarado, fin declarado)` de *cobertura efectivamente verificable*, y reportar explícitamente lo anterior/al posterior al turno y los snapshots tomados antes de su fin. No fingir cobertura continua ni tratar tiempo sin eventos como estado `IDLE`. Cualquier adjudicación causal F5 necesitará un vínculo de tarea/servicio y un control real de relojes, además de estas comprobaciones.

## Código y trazabilidad

- `scripts/arena_cafe/weba_instrument_integrity.py` — auditoría desde bytes externos fijados.
- `tests/test_arena_cafe_weba_instrument_integrity.py` — pruebas estructurales de los parsers, derivación condicionada de límites y ausencia de datos individuales.
- `.github/workflows/arena-cafe-f5-weba-instrument-integrity.yml` — descarga, validación, ejecución y publicación exclusiva del JSON agregado.

**Estado no negociable:** D/B/M no modificados; reloj POS–Tapo no calibrado; cobertura continua no certificada; G4 y G5 `NOT_RUN`; F5 reserva `NOT_CREATED`.
