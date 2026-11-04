# Arena IGC · F5 · Política congelable de medición de despacho y compuerta de abstención

**Fecha de desarrollo:** 2026-11-03. **Antecedentes exactos:** PR #152 (dos mundos FIFO indistinguibles bajo O0/O1), PR #157 (B2 y advertencia de lookahead) y PR #158 (testigo retrospectivo: 4 frente a 5 terminaciones de despacho estrictamente antes de t6). Este archivo **no** registra una reserva F5 ni una prueba independiente; documenta el contrato de ingeniería previo a conseguir datos nuevos.

## Decisión y procedencia

La propuesta fija una sola variable de medición:

`#(despacho.servicio_fin con t < 6 minutos)`, sobre un **recorrido BASE previo a cualquier intervención**, con el mismo sentido temporal de O0/O1 (`[0,6)`, sin sumar eventos exactamente en t6). El corte t6 no fue elegido a ciegas: es consecuencia **post-hoc** del testigo F4 ya conocido. Congelarlo ahora evita retocarlo al ver **futuros** datos, pero **no convierte su elección pasada en una selección prospectiva de EV-01**.

La política de comparación queda limitada a **dos hipótesis previamente declaradas**:

| Conteo real de despacho antes de t6 | Interpretación condicional (si captura y reloj fueran correctos) |
|---|---|
| 4 | Compatible con A, no con B, **dentro del par declarado** |
| 5 | Compatible con B, no con A, **dentro del par declarado** |
| Otro valor | **Abstención**: ninguna de las dos hipótesis conocidas reproduce la medición |
| Sin registro, reloj no compartido o estación no observada | **Abstención** por observación inutilizable |

A y B **no son una enumeración exhaustiva de los mecanismos posibles**. Una coincidencia con 4 o 5 no demuestra cuál es la estructura física verdadera, ni se traduce por sí sola en una predicción de intervención o en un resultado de D/B/M.

## Dos pasos diferentes (la frontera que faltaba)

1. `freeze` emite el JSON íntegro de la política y su `policy_sha256` determinista. No recibe un log físico ni importa el DES o la verdad privada. El archivo no se sobreescribe. El SHA identifica **contenido**, no es firma digital, prueba de cronología ni sustituto de custodia externa. El commit del repositorio constituye el corte de versión que debe quedar **antes de cualquier nuevo dato usado en una evaluación**.
2. `probe` recibe **solo un CSV de eventos truncados a [0,6)** y el contrato `pilot_event_capture.py` del PR #151. Este valida nombres de eventos, visitas, secuencia física, recursos, censura, pseudónimos y relojes declarados. No rellena terminaciones ausentes. Si falta una medición de despacho o no hay reloj común declarado, devuelve abstención.

Los dos comandos son:

```bash
python -m scripts.arena_cafe.f5_sensor_precommit_gate freeze \
  --out artifacts/F5_SENSOR_POLICY.json

python -m scripts.arena_cafe.f5_sensor_precommit_gate probe \
  --policy artifacts/F5_SENSOR_POLICY.json \
  --events captura_hasta_t6.csv \
  --source-context real_pilot_declared \
  --out artifacts/F5_SENSOR_PROBE.json
```

La entrada CSV debe tener **exactamente** los diez encabezados de `pilot_event_capture.EVENT_FIELDS`. Debe contener eventos POS `pedido_creado` y las visitas físicas de despacho registradas antes de t6 con `visit_id` y recurso en `servicio_inicio/fin`. Los eventos posteriores a t6 están prohibidos. No se entregan a la salida IDs, instantes por caso o recursos individuales: solamente conteo agregado, hash del archivo de entrada y estados de validez.

**Advertencia:** `source-context=real_pilot_declared` es una **declaración del suministrador**, nunca prueba independiente de que ocurrió un piloto real. Tampoco un único `clock_id` acredita reloj calibrado, una serie aparentemente íntegra acredita ausencia de pérdidas, ni los dos mundos usados en las pruebas proporcionan un G5.


## Auditoría de fuentes externas (2026-11-03): ninguna fuente pública acredita todavía F5

Esta auditoría distingue **que una fuente tenga columnas parecidas** de que los datos acrediten un evento físico, su reloj, sus vínculos por pedido y su independencia del desarrollo EV-01.

| Fuente examinada | Qué contiene verificablemente | Dictamen para F5 |
|---|---|---|
| [Toast Kitchen API](https://dev.toasttab.com/doc/devguide/apiKitchenGettingFulfillmentData.html) | `ticketFiredAt`, `itemStartedAt`, `itemFulfilledAt`, identificadores de pedido/ticket y estación de preparación; exportación por día para restaurantes con KDS y suscripción elegible | **CANDIDATO CON SOCIO**, no dataset público. `itemStartedAt` puede ser igual a `ticketFiredAt` si no se usa *start queue*: no se debe presentar como inicio físico sin verificarlo. La unidad es **ítem/estación/nivel de cumplimiento**, no necesariamente pedido completo o despacho. |
| [CAKE Kitchen Operations report](https://university.cake.net/articles/Knowledge/Dashboard-Kitchen-Operations-Report) | Hora de envío a cocina, cumplimentación, estación y tiempo de cocina por ítem/ticket | **CANDIDATO CON SOCIO**, pero hay que demostrar si el evento `fulfilled` significa terminación física, pulsación KDS o retiro. No prueba por sí mismo `servicio_inicio`. |
| [Ejercicio Deliveroo publicado en GitHub](https://github.com/soumyadg/food-prep-model) ([CSV](https://github.com/soumyadg/food-prep-model/blob/main/Data/orders.csv)) | Archivo de alrededor de 32 mil filas con `order_acknowledged_at`, `order_ready_at`, `restaurant_id`, `number_of_items`, `prep_time_seconds`; sin ID de pedido ni eventos de estación o recurso | **NO APTO para la compuerta despacho t6**: no permite vincular con seguridad una visita de despacho ni distinguir preparación de despacho; la procedencia como registro real independiente tampoco está documentada suficientemente para G5. No se reutiliza como si fuese FULL. |
| [Restaurant kitchen ticket timings](https://databasesample.com/datasets/restaurant-kitchen-ticket-timings-dataset) | Tickets, estaciones, tiempos de *fire*, cocina y espera | **RECHAZADO COMO EVIDENCIA INDEPENDIENTE**: su documentación declara que todo es sintético y que los tiempos no responden a la congestión. Puede servir de fixture, no de contraste empírico causal. |
| [IIT Delhi, estudio con Domino's India](https://www.cse.iitd.ac.in/~cs5180411/Prediction%20of%20Kitchen%20Preparation%20Time%20in%20Food%20Delivery.pdf) | La tesis describe registros de pedidos con marcas KDS y entrada a horno cedidos por la empresa | **NO DISPONIBLE COMO ARCHIVO AUDITABLE AQUÍ**: la tesis demuestra que ese tipo de medición existe, pero no concede acceso al dataset crudo, ni prueba que horno y despacho equivalgan al proceso F4. |

**Decisión de adquisición:** priorizar **una cafetería colaboradora con POS + KDS que exponga marcas originales a nivel de evento**, o bien observación directa de despacho corroborada por un POS real y por una segunda fuente de contraste. **Ninguna columna se mapeará automáticamente a `servicio_inicio` o `servicio_fin` sin verificar su semántica física.** No se requieren servicios específicos de estas marcas.

### Nuevo candidato documental: WEBA (Tran et al., Scientific Data, 2025)

**Estado tras inspección de artículo y archivos de GitHub: ACEPTADO COMO FUENTE REAL DE OBSERVABILIDAD PARCIAL / NO ELEGIBLE TODAVÍA COMO F5 DE TERMINACIONES POR PEDIDO.** Procedencia académica: [artículo](https://doi.org/10.1038/s41597-024-04348-z); [Figshare v3](https://doi.org/10.6084/m9.figshare.27186516.v3); [repositorio actual](https://github.com/Department-of-System-Engineering/datasets_WEBA), redirección del enlace original `operator40/datasets_WEBA`.

La cafetería observada estaba en **Budapest**. Los autores documentan cinco baristas y 55 turnos, con **un solo barista trabajando a la vez**, que se desplaza entre las zonas de caja/despacho y preparación. **No** modelar ambas zonas como servidores humanos independientes en paralelo: una misma persona comparte la capacidad física. El repositorio accesible presenta exactamente **55 carpetas** en `B.shift_data/`, más `orders_summary.xlsx`, `shift_summary.xlsx` y `workload_summary.xlsx`.

| Observación original WEBA | Archivo/canal auditado | Qué se puede decir ahora | Qué **no** se puede inferir directamente |
|---|---|---|---|
| Hora e ítems del pedido en POS | `B.shift_data/orders_summary.xlsx`, variables `order_ID`, `order_date`, `order_time`, `coffee_cup`, `choco_cup`, `cake` (Tabla 9 del artículo) | Identificador y **hora de recepción de pedido** en una fuente externa real | Entrada física por puerta, inicio de caja o correspondencia con fin de servicio individual |
| Apertura de puerta / movimiento delante de entrada | `yyyymmdd_shift/3.logs.txt`, eventos Tapo T110/T100 `front_door`, `front_door_m` | Señales ambientales con marca temporal, útiles como **proxies** de actividad de entrada | Un evento = un cliente nuevo. Aperturas también pueden obedecer a salidas, barista o visitantes, y varios clientes pueden compartir una apertura |
| Presencia/movimiento en Zona 1 o Zona 2 | Mismo `3.logs.txt`: T100 `zone_1`, `zone_2` | Señales de actividad espacial del barista/ocupación potencial de zonas, a validar por secuencia | Inicio/fin de caja, preparación, despacho o `servicio_fin` de un pedido; presencia no significa procesamiento efectivo |
| Funcionamiento de máquina | `5.coffee_machine_acc` o carpeta `5.coffee_machine_acc/` según turno; ADXL345 a 25 Hz, raw | Señal física de **vibración de máquina** con muestreo nominal de 40 ms | Que un segmento de vibración corresponda sin ambigüedad a una bebida, pedido, barista o al fin completo de preparación/entrega |
| Movimiento humano | `1.body_acc.csv` 25 Hz, `2.hand_acc.csv` 12.5 Hz | Señales temporales de actividad laboral | Terminación auditada de cada servicio o identificación inequívoca de pedido, sin validación y anotación |
| Percepción / condiciones de turno | `4.hr.csv`, cuestionarios, summaries | Contexto humano y de carga; **no necesario** para el primer pase operacional | No usar datos de salud/participantes como sustituto de eventos físicos ni publicar información de participantes |

**Restricción de cobertura que cambia el diseño:** los autores declaran que las marcas temporales POS de pedidos **faltan para los primeros 13 turnos y están disponibles para los últimos 42**. El análisis de llegada POS solo es posible donde ese campo existe. No completar horas faltantes con puertas Tapo.

**Comprobación directa limitada de un turno:** `B.shift_data/20240223_evening/` incluye `3.logs.txt`, señales de cuerpo/mano, HR y carpeta de aceleración de máquina; el log es un volcado de registros Tapo que puede incluir **listas de eventos históricos recientes** por dispositivo, no un CSV ya deduplicado de `servicio_fin`. No existe un `front_door_events.csv` en ese directorio. `B.shift_data/20231129_evening/` presenta una disposición distinta de archivos. Se inspeccionaron metadatos, nombres, documentación y encabezados de log, **NO** se descargó ni analizó íntegramente el paquete Figshare ni se validaron los enlaces pedido↔sensores.

**Puertas científicas que todavía NO pasan:**

- **T0 — Origen externo auténtico:** SÍ: artículo revisado por pares y datos crudos de campo documentados, independencia de la construcción sintética EV-01.
- **T1 — Señales ambientales crudas disponibles:** SÍ, en el repositorio GitHub, con diferencias de cobertura y formato por turno.
- **T2 — Eventos derivados físicos de tarea validados:** NO DEMOSTRADO: hace falta algoritmo/revisión manual, definiciones de zona y machine-on/off, calibración de reloj, tasa de omisiones y falsos positivos.
- **T3 — Enlace caso/pedido a evento de preparación y despacho:** NO DEMOSTRADO. El artículo ofrece `order_ID` en POS y `shift_ID`, no un identificador de pedido por evento de máquina o de zona.
- **T4 — `despacho.servicio_fin([0,6))` directamente medible para la regla PR #159:** NO, salvo nueva prueba de mapeo que todavía no existe. **Nunca** llamar `servicio_fin` a un retorno a Zona 1.
- **T5 — G5 independiente, ciego y predeclarado:** NO: la independencia del **origen de datos** no implica una evaluación prospectiva válida ni que los mundos A/B sintéticos representen esa cafetería.

**Decisión técnica:** no ingerir el archivo completo de ~centenas de MB indiscriminadamente, especialmente mediciones de HR/cuestionarios de participantes. Priorizar **un inventario de cobertura por turno**, usando SOLO `orders_summary.xlsx` y registros `3.logs.txt` de una muestra; confirmar offsets y reloj de ambos sensores/servidores. Definir después, antes de leer una muestra de evaluación separada, un operador observacional de **eventos de máquina/zonas** etiquetado como aproximación, con abstención cuando el vínculo a pedido no sea defendible. Conservar la procedencia, la licencia aplicable y los archivos originales; no publicarlos en la Arena. Si solo conseguimos proxies de actividad, **cambiar la pregunta medible** y no fingir que son el operador F5 de despacho original.

### Plan mínimo de una captura verificable, antes de ejecutar `probe`

1. **Permiso y unidad:** obtener autorización para un ensayo observacional sin clientes identificados; fijar si se cuenta *pedido*, *ítem* o *visita a estación*. No mezclar ítems KDS con pedidos para conseguir artificialmente 4 o 5.
2. **Definir el evento:** nombrar la estación física `despacho`, establecer qué acción observable señala el **fin real del servicio**, distinguirla de un *bump* KDS, un `ready` de cocina y la entrega final. Identificar y registrar los casos que siguen esperando o en servicio cuando termina la ventana.
3. **Vincular y fechar:** conservar el identificador seudónimo del pedido y, cuando corresponda, `visit_id` y recurso; conservar la exportación POS original por separado. **No inventar eventos `pedido_creado` con fuente `pos` a partir de clics de un observador**, ni registrar `etapa_entrada` / `servicio_inicio` si la fuente nunca los midió. Si los relojes son distintos, conservar sus identificadores reales y abstenerse de comparaciones hasta calibrar alineación y deriva.
4. **Control independiente:** contrastar manualmente una muestra de finales de despacho con los logs KDS, y cuantificar omisiones y duplicaciones antes de tratar los conteos como observaciones fieles. No inferir exactitud de reloj por el mero acuerdo de dos sistemas.
5. **Ventana y custodia:** guardar el evento original y documentación instrumental **antes** de inspeccionar resultados; registrar hash del archivo, día/corte, versión de política y responsable de custodia. A la compuerta solo entra `[0,6)`; los eventos posteriores nunca reconstruyen finales censurados. El conjunto original permanece fuera del repositorio público.
6. **Resultado:** ejecutar el lector genérico de PR #151 y, solo si cumple su esquema, el `probe` de PR #159. Un dato 4/5 prueba **compatibilidad con el par sintético histórico**, no identidad de una cafetería nueva. Cualquier otro valor obliga a abstenerse, no a reoptimizar el corte, elegir otra estación a posteriori ni ajustar las expectativas de A/B.

**Advertencia de transportabilidad:** las predicciones discretas A=4 y B=5 corresponden a **15 arribos, configuración vacía y tiempos de servicio específicos de EV-01**. Una cafetería nueva tendrá otra carga, mezcla de productos, estado inicial y capacidad; por ello incluso un log real impecable **no validaría automáticamente** la comparación de dos configuraciones de ese mundo sintético. Para adjudicar métodos en F5 hará falta un objetivo de predicción y un conjunto de hipótesis pertinentes a la nueva cafetería, fijados **antes de conocer los resultados**, además de evidencia de intervención factible y permiso operativo.

**Compuerta de avance:** actualmente **NO HAY una fuente externa aprobada ni un archivo del piloto real**. En tanto no exista, no ejecutar G4/G5, no reinterpretar tests sobre A/B como prueba ciega ni construir otro escenario ajustado a esta regla. Este anexo documenta posibles vías de adquisición, **no** una conexión API ni una solicitud a un establecimiento.

## Condiciones que siguen impidiendo un resultado científico

Para pasar de compatibilidad descriptiva a un resultado independiente hace falta contar con **una fuente nueva cuyo mecanismo no se revele durante selección e inferencia**, instrumentación verificable de servicios terminados, control de pérdidas/duplicados de eventos, resolución/alineación del reloj, condición base separada de la intervención y una evaluación prospectiva predeclarada con sus abstenciones. Si se pretende medir el beneficio de D/B/M, deben participar los tres métodos originales con la misma evidencia autorizada, presupuesto, aislamiento y predicciones congeladas antes del resultado.

El código **siempre** declara `source_origin_independently_attested=false`, `pilot_event_capture_completeness_verified=false`, `scientific_identification=NOT_ESTABLISHED`, `F5_independent_reserve=NOT_CREATED`, `A3=PARTIAL` y `G4/G5=NOT_RUN`. **Nunca interpreta una coincidencia con 4/5 como validación científica.** El operador físico de Moléculas no se recalibra y la minería de procesos permanece condicional.

## Pruebas de ingeniería, no un estudio independiente

Se usan **solo como fixtures históricos conocidos** los mundos A/B de F4. La CI debe reproducir conteos 4 y 5, pero comprobar también que la política no cambia según el archivo, que un registro tardío o en t6 no entra, que sin estación o reloj común se abstiene, que un `servicio_fin` faltante no se inventa, y que el score no contiene eventos, casos ni recursos privados. Un experimento con datos reales todavía necesita implementación y custodia por separado.

**Decisión:** el trabajo habilita una frontera de obtención de evidencia mejor definida. **No abre G4, G5, ni un nuevo mundo simulado para producir un triunfo retrospectivo.**
