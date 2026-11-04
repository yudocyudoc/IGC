# F5 · WEBA: auditoría inicial de POS y Tapo reales

**4 de noviembre de 2026. Estado: verificación de observabilidad de fuente; no G5.**

## Material y corte exacto

- Estudio: Tran et al., Scientific Data (2025), DOI https://doi.org/10.1038/s41597-024-04348-z.
- Datos: Figshare https://doi.org/10.6084/m9.figshare.27186516.v3 y GitHub https://github.com/Department-of-System-Engineering/datasets_WEBA.
- Commit externo fijo: d6841669e544579547c94b7ce1e8613bbd6b3a39.
- Muestra de desarrollo ya conocida: turno 20240223_evening; **no es una reserva ciega**.
- ÚNICOS archivos descargados durante CI: B.shift_data/orders_summary.xlsx (58,322 bytes, git blob a7f10b818402884255a3f6390da59b34a4ccdec2); B.shift_data/20240223_evening/3.logs.txt (45,209 bytes, blob dc98f6b68eeebf7544d1981e825e3fb26129face).

No se descargan datos de participantes, frecuencia cardiaca, cuestionarios, registros de aceleración personal ni otras fuentes de salud. El reporte publicado contiene solo agregados, nombres funcionales de sensores y hashes de las dos fuentes; no se publican registros de eventos, identificadores de dispositivos ni pedidos.

## Primer hallazgo verificable: el log Tapo no es un log por pedido

El texto Tapo comprende diez sensores y mensajes retrospectivos llamados **last 50 trigger logs**, con tipos de registro Open, Close, KeepOpen y Motion. Los conteos preliminares sobre el archivo real son: front_door **161**, front_door_m **115**, zone_1 **147**, zone_2 **244**, y **911 registros devueltos** sumando los diez sensores.

El sensor front_door incluye **siete registros KeepOpen**, que perderíamos al filtrar solamente Open/Close. Incluso cuando la cantidad declarada por Tapo coincide con el número de registros visibles, eso **no prueba** cobertura de todas las actividades de la cafetería. Un pulso de puerta no es un cliente, un pulso de zona no es una tarea ni un evento de máquina es la terminación de una bebida vinculada a un pedido.

Los timestamps Tapo corresponden a registros epoch Unix del sensor. Las horas POS son campos del sistema de pedidos; **no se ha demostrado el offset, la deriva ni la identificación uno-a-uno de ambos canales**. Este primer pase no alinea físicamente dichos relojes.

## Resultado real del primer pase con fecha normalizada

El archivo original de pedidos conserva las fechas como **YYYYMMDD** (por ejemplo, el día del turno se representa como 20240223), no como una fecha ya normalizada ISO o DMY. El primer extractor no reconoció ese formato y reportó incorrectamente cero coincidencias. **Se corrigió el parseo y se añadió una prueba adversarial específica**; los archivos originales y sus hashes permanecen idénticos.

Tras normalizar este encoding, el informe agregado de la ejecución real produce:

| Auditoría POS | Conteo |
|---|---:|
| Filas no vacías de pedidos | **588** |
| Filas con hora de pedido no vacía | **588** |
| Filas con fecha original normalizable | **588** |
| Fechas distintas representadas en el libro | **28** |
| Pedidos del día 2024-02-23 | **48** |
| Pedidos del turno 20240223_evening | **33** |
| Pedidos de ese turno con hora disponible | **33** |

En paralelo, el log Tapo del mismo turno presenta **911 registros IoT devueltos por 10 sensores** y siete eventos **KeepOpen**. Los tiempos de sensor van aproximadamente de **13:34 a 17:35 UTC**, pero esos extremos son de un historial de disparos, no de la apertura y cierre operacional certificada de la cafetería.

**La coincidencia del identificador de fecha/turno NO valida correspondencia pedido↔sensor**, integridad del historial ni sincronización de relojes. En particular, **911/33 no es una medida de tareas por pedido**. No se extrajeron servicios individuales, llegadas físicas por puerta ni una tasa de atención.

La prueba final debe fallar si un cambio de fuente vuelve a dejar sin marcas POS el turno seleccionado; no basta detectar que el archivo global contiene filas.

## Libro de pedidos POS

Se inspecciona orders_summary.xlsx con un lector mínimo de solo lectura para OOXML, usando la biblioteca estándar de Python. El informe resume encabezados y cobertura de order_ID, order_date, order_time y time_of_day; cuenta filas con horas y filas asociables por fecha/etiqueta al turno elegido. No se emiten horas individuales, IDs, productos ni montos. Ninguna hora faltante se reconstruye desde aperturas de puerta.

## Implementación y controles

- scripts/arena_cafe/weba_source_readiness.py: descarga externa separada, verificación de tamaño y Git blob SHA-1, SHA-256, auditoría de conteos Tapo y campos POS. La ejecución no utiliza un nuevo modelo DES ni genera pedidos artificiales.
- tests/test_arena_cafe_weba_source_readiness.py: pruebas del parser, KeepOpen, eventos desconocidos, IDs duplicados, hojas con horas faltantes y verificación de fuentes. Son fixtures estructurales, no mundos simulados.
- .github/workflows/arena-cafe-f5-weba-real-source.yml: descarga únicamente ambos archivos originales desde el commit fijo, los elimina antes de publicar artefactos y publica exclusivamente un JSON agregado. Si el archivo o su estructura difiere, el job falla; no se imputan terminaciones físicas.

## Decisiones de admisibilidad

- Fuente externa real y cruda **SÍ**.
- Señales temporales ambientales y pedidos POS **SÍ**.
- Llegada física independiente y vinculada al pedido **NO DEMOSTRADO**.
- Inicio/fin de caja, preparación o despacho por pedido **NO DEMOSTRADO**.
- Servidores humanos independientes de caja y barra como en EV-01 **NO**: el caso WEBA tiene un solo barista realizando varias funciones.
- Reglas históricas A=4 y B=5 de despacho t6 aplicables al nuevo negocio **NO**.
- Operador WEBA apto para la reserva F5 de despacho por pedido **NO**.
- Conjunto ciego G5 de evaluación de D/B/M **NO CREADO**.

**Siguiente decisión:** si hay disponibilidad POS efectiva y señales Tapo interpretables, diseñar una pregunta limitada a observabilidad de actividad de un trabajador único; especificar una política de eventos y validarla en otra muestra independiente antes de inferir colas. No fabricar eventos de despacho ni mezclar los relojes para conseguir una simulación exitosa.
