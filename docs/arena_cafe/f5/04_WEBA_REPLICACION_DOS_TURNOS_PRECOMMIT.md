# WEBA · Replicación descriptiva entre turnos (protocolo anterior a la lectura)

**Fecha:** 2026-11-04. **Clase:** control de transportabilidad temporal de operadores de lectura; NO reserva F5, NO G4/G5, NO operador de `servicio_fin`.

## Congelación de selección

El turno exploratorio anterior fue `20240223_evening` (PR #161). A partir **únicamente del inventario de carpetas y nombres de archivo** en el commit fijo del upstream WEBA `d6841669e544579547c94b7ce1e8613bbd6b3a39`, se eligieron los **dos primeros turnos con nombre `*_evening` posteriores a 20240223 que contienen `3.logs.txt`**:

- `20240304_evening`: `3.logs.txt`, 44,186 bytes, Git blob `e9059ae926717492a29dd8a4ac5743fcfc7f4f39`.
- `20240308_evening`: `3.logs.txt`, 44,237 bytes, Git blob `9b4eab54a3a31696970f7221aee42fc4448fb9a1`.

El POS es **el mismo archivo original** `B.shift_data/orders_summary.xlsx` ya validado en #160: 58,322 bytes, Git blob `a7f10b818402884255a3f6390da59b34a4ccdec2`. Las fechas/turnos pueden existir en el POS o no; **se debe informar toda falta**, sin cambiar selección ni fabricar transacciones.

Se prohíbe inspeccionar los eventos crudos de ambos turnos hasta que la selección, los parámetros de reloj y la lógica de análisis estén registrados en Git. Si faltan sensores, el resultado es **dato no apto** o error de esquema, nunca sustitución del turno por otro. El upstream público se congela por commit SHA y hashes de contenido; no se usan los participantes, HR o acelerómetros.

## Operador conservador de comparación

Se mantiene el protocolo descriptivo del PR #161, sin calibrar relojes con resultados:

- Rejilla de **10 ventanas fijas de 30 minutos** en `[13:00,18:00) UTC`, para cada día.
- **Interpretación principal, explícitamente no validada:** `order_time` del POS es hora local `Europe/Budapest`, que en ambos días seleccionados es **UTC+01**. Se convierte por calendario. **Sensibilidad fija:** misma hora escrita en POS interpretada como UTC, sin elegir un desfase óptimo.
- Tapo: **epoch Unix UTC de eventos ambientales**, no identificadores de visitas de pedido. Se cuentan por separado `front_door`, `front_door_m`, `zone_1` y `zone_2`; el operador original conserva `Open`, `Close`, `KeepOpen`, `Motion`.
- Reportar por turno conteos POS, conteos de Tapo por canal dentro y fuera de la rejilla, ventanas con ambos canales y ventanas **sin pedidos POS pero con disparos**. Reportar además disponibilidad de marcas POS; no inferir pérdida de clientes a partir de apertura de puerta.
- **NO** calcular coeficientes de correlación buscando una coincidencia, ni seleccionar lags, ni declarar a un sensor proxy causal del flujo de pedidos, ni interpretar `POS=0` como inactividad de un trabajador. El contenido histórico de un snapshot Tapo puede tener bordes truncados.

## Qué constituye una réplica exitosa

Una ejecución válida no depende de que aparezcan patrones similares: demuestra que **el mismo operador de extracción puede ejecutarse sin cambios** sobre los dos turnos y conservar todos los registros en las ventanas o fuera de ellas. Los resultados, incluidos ceros, cobertura parcial o diferencias grandes, son informativos y se reportarán tal cual. Los datos son reales y externos al generador de EV-01, pero **dos turnos del mismo establecimiento, seleccionados dentro del estudio ya conocido, no constituyen una validación prospectiva, causal ni un G5 independiente**.

## Trazabilidad de ejecución

El análisis se implementará en `scripts/arena_cafe/weba_two_shift_replication.py` con tests de relojes, límites de ventanas, ausencia de optimización, fuente fijada por hash y no publicación de registros individuales. Los originales solo existirán en el runner de CI y se eliminarán antes del artefacto; la única salida pública será JSON agregado con metadatos de procedencia.

**Regla de frontera:** la observación no autoriza inferir `etapa_entrada`, `servicio_inicio`, `servicio_fin`, KDS ni llegada física por cliente, y no altera D/B/M, O0/O1 ni la reserva F5.


## Resultado del primer análisis real (posterior al compromiso de selección)

Se ejecutó el protocolo anterior **sin cambiar el par de turnos ni la rejilla**, usando bytes del repositorio WEBA verificados por hash. Los números siguientes son **registros ambientales y ventas POS**, no servicios físicos.

| Indicador observado | 20240304_evening | 20240308_evening |
|---|---:|---:|
| Pedidos POS en el turno, con hora | **7** | **15** |
| Pedidos dentro de [13:00,18:00) UTC bajo hipótesis Budapest | 7 | 15 |
| Pedidos dentro de la misma ventana si POS fuera UTC | 6 | 13 |
| Pedidos fuera de ventana bajo interpretación UTC alternativa | 1 | 2 |
| Registros Tapo en los 10 sensores | **888** | **889** |
| Ventanas de 30 min con al menos un pedido POS | 6/10 | 6/10 |
| Ventanas con disparos Tapo pero ningún nuevo pedido POS | **3/10** | **4/10** |
| Disparos de los cuatro sensores seleccionados en ventanas sin POS | **115** | **136** |

**Control negativo reproducido:** en ambos turnos hay actividad ambiental en intervalos donde el POS no registró pedidos. El valor 115 del 4-mar proviene de puerta contacto **20**, puerta movimiento **11**, zona 1 **31**, zona 2 **53**; el 8-mar los correspondientes valores son **33**, **20**, **34** y **49** (suma 136). **No** implica que alguno sea un falso disparo ni un servicio pendiente; tampoco demuestra la existencia de clientes no registrados.

**Cobertura incompleta del intervalo fijo:** se contabilizan y publican por separado los registros Tapo fuera de la rejilla en los cuatro canales: para 4-mar, contacto 33, movimiento 19, zona 1 60 y zona 2 94; para 8-mar, contacto 34, movimiento 21, zona 1 37 y zona 2 78. **No se descartaron silenciosamente** para hacer coincidir canales. Las ventanas vacías no demuestran inactividad: el archivo es un snapshot histórico cuya cobertura del turno no está certificada.

**Limitación metodológica decisiva:** no se ha validado que el POS esté expresado en hora local de Budapest. El análisis UTC alternativo se informa simultáneamente y **no se selecciona el desfase que maximice concordancia**. Tampoco se ha demostrado una correspondencia entre pedido y pulso Tapo; que las seis ventanas con POS también tengan pulsos en los cuatro sensores es compatible con actividad general de una cafetería y no identifica servicios ni cuellos de botella.

El único avance acreditado es de **replicabilidad de extracción y comparación de observabilidad parcial en dos turnos reales**, frente a la única muestra exploratoria de febrero. No hay predicciones de intervención, ni E1 calibrado, ni identificación de tareas por caso, ni G4/G5 o reserva F5 independiente.

**Evidencia técnica:** workflow específico para dos turnos de WEBA, fuentes congeladas por commit y blobs, pruebas de extracción y límites, JSON agregado de GitHub Actions. Los datos crudos se eliminan antes de publicación.
