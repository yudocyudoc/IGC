# WEBA · Primer operador físico elemental: intervalos T110 de apertura/cierre

**Fecha:** 2026-11-04. **Estado:** auditoría retrospectiva sobre los mismos tres turnos reales previamente inspeccionados (#160–#164). **No es** una reserva ciega, prueba de actividad laboral por pedido, validación de operabilidad F5 de despacho ni identificación de un cuello causal.

## Pregunta y dictamen de evidencia

El problema no es si el archivo contiene un timestamp, sino **qué fenómeno físico representa**. Los autores de [WEBA, Scientific Data (2025)](https://doi.org/10.1038/s41597-024-04348-z) describen sensores **Tapo T110** adheridos a puertas de refrigeradores, congelador, vitrina de pasteles y puerta principal; los sensores **Tapo T100** registran movimiento. La tabla 3 propone usar la apertura de refrigeradores como indicio de que el barista accede a materias primas, pero eso **no establece la relación uno a uno con un pedido**, ni prueba que una apertura sea la extracción de un ingrediente.

**Decisión de modelado — jerarquía de afirmaciones:**

1. **OBSERVADO:** mensajes físicos T110 con `Open`, `Close` y `KeepOpen`, asociados a un sensor de contacto fijo y timestamp Unix.
2. **DERIVACIÓN CONDICIONAL DEFENDIBLE:** un `Open` seguido por `Close`, en el **mismo sensor** y sin contradicción intermedia, constituye un **intervalo de contacto registrado como abierto**. Su duración es la diferencia de esos dos timestamps; no es duración de trabajo humano.
3. **NO IDENTIFICABLE A PARTIR DE ESTE PAR:** quién abrió la puerta, qué ingrediente se retiró, si había una orden relacionada, si terminó de producir una bebida o si se entregó un pedido.
4. **NO PROBADO:** completitud y disponibilidad continua del sensor, precisión de reloj, detección de todas las aperturas, enlace del reloj POS a Tapo y estimación de capacidad de servicio.

Esta separación evita declarar `servicio_inicio`, `servicio_fin` o `preparación terminada` por una mera transición de contacto.

## Selección de dispositivos observados

**Cinco sensores de almacenamiento**: `r_wing_fridge`, `l_wing_fridge`, `freezer`, `r_door_cake_display`, `l_door_cake_display`.

**Un control contextual separado**: `front_door` (puerta de entrada). Un par apertura/cierre de la entrada **no** equivale a un cliente o pedido; no se suma a episodios de almacenamiento.

Los cuatro sensores T100 de movimiento `stair`, `front_door_m`, `zone_1` y `zone_2` quedan excluidos: no tienen semántica de contacto abierto/cerrado. El operador solo utiliza `3.logs.txt`, el libro POS y `shift_summary.xlsx` previamente fijados; el POS se usa exclusivamente para verificar **procedencia del conjunto de cinco archivos**, no para atribuir eventos a una orden.

## Reglas de reconstrucción conservadora

Los históricos Tapo vienen en orden cronológico descendente. Se reconstruyen en el orden inverso por sensor, sin emparejar dispositivos. `Open→Close` forma un par **solo** si no aparece otra `Open` antes del cierre y el cierre es posterior al inicio. `KeepOpen` se conserva pero **no** es otro inicio ni un cierre. Un cierre inicial sin apertura conocida no recibe un inicio inventado; una apertura final sin cierre permanece **censurada por la derecha**, sin duración imputada. Una contradicción (reapertura sin cierre) hace **fallar** el operador en vez de reparar datos.

El par se clasifica por `[inicio, fin)` documentado en `shift_summary.xlsx`, **bajo el supuesto horario no calibrado Europe/Budapest**: antes, íntegramente dentro, después, cruzando inicio, cruzando final o ambos. Solo un par cuyos extremos están dentro del turno se incorpora al conteo de **intervalos completos interiores**; jamás se interpreta la ausencia de par como inactividad o falta de acceso.

Se prohíbe dividir el número de pares o la suma de sus duraciones entre el turno como indicador de intensidad humana/ocupación. Dos puertas pueden estar abiertas al mismo tiempo; su tiempo abierto se superpone y **no es el tiempo trabajado por un único barista**.

## Primer resultado empírico verificado en las fuentes conocidas

En los registros ya revelados aparecen:

| Turno | Pares T110 almacenamiento en todo el snapshot | Pares íntegros dentro del turno | Pares anteriores | Pares posteriores | Aperturas sin cierre posterior |
|---|---:|---:|---:|---:|---:|
| 23-feb-2024 tarde | **79** | **76** | 2 | 1 | 0 |
| 4-mar-2024 tarde | **94** | **59** | 35 | 0 | 0 |
| 8-mar-2024 tarde | **67** | **44** | 23 | 0 | **1** |

Los valores pertenecen exclusivamente a cinco sensores de almacenamiento. No se han certificado sensores siempre encendidos ni eventos completos. El 8-mar, el sensor `r_wing_fridge` contiene una **`Open` final sin `Close`** en el historial disponible; se registra como censura, **no se completa usando el final del turno o la exportación**. Ese mismo día `l_door_cake_display` no devuelve registros: **cero en el snapshot no equivale a cero aperturas reales**.

`KeepOpen` de almacenamiento: **0 / 2 / 1** mensajes para las tres fechas; permanecen separados de las cuentas de apertura. Como control físico externo a almacenamiento, `front_door` tiene **74 / 27 / 49** pares completos dentro del turno, que **no representan número de clientes**.

**Censura instrumental adicional:** 8-mar último volcado a ~17:37:02 UTC frente a fin declarado 17:41 UTC (con huso supuesto). Un estado no registrado después del volcado es **desconocido**, no `Close`, `Open` o `IDLE`.

## Sobre los archivos de vibración de la cafetera

El artículo menciona muestras de vibración etiquetadas por tipo de bebida, pero el árbol público de este commit contiene **archivos de aceleración por turno y subarchivos identificados principalmente por tiempo**, no una tabla publicada de emparejamiento `order_ID → inicio/fin de vibración → bebida terminada` que haya sido acreditada aquí. Por ejemplo, una muestra original corta de `5.coffee_machine_acc/20240104_141839` contiene columnas de **hora de pared y tres componentes numéricas de aceleración**, no una etiqueta de pedido por línea. **No se afirma que no exista ninguna anotación en todo Figshare**; para utilizar ese canal habría que localizar y validar anotaciones originales y origen de los tiempos. Este PR **no descarga ni procesa** aceleración personal, fisiología ni vibración de máquina.

## Implementación, controles y custodia

- `scripts/arena_cafe/weba_contact_episode_audit.py`: reutiliza exactamente el control de hashes, formato Tapo y límites del PR #163, y publica **solo agregados por sensor funcional**, nunca IDs de eventos/dispositivos ni timestamps de aperturas particulares.
- `tests/test_arena_cafe_weba_contact_episode_audit.py`: prueba secuencias `Open/Close/KeepOpen`, apertura censurada, cierre huérfano, reapertura contradictoria, intervalos que cruzan límites, control de puerta principal y prohibición de atribuir tareas o pedidos. Fixtures del parser, **no mundos de cafetería simulados**.
- El workflow existente WEBA de cinco archivos se amplía para ejecutar esta auditoría sin otra descarga, con el **mismo commit fijo y blobs SHA-1**. Publica solo el JSON agregado y elimina las fuentes temporales.

## Veredicto

WEBA **sí aporta un operador de eventos físicos elementales observados:** apertura/cierre de contacto de puertas, con pares localmente consistentes y duración **de estado de contacto**, no de trabajo humano. **No identifica tareas concretas de atención/preparación ni su fin por pedido**, y no valida el operator F5 `despacho.servicio_fin([0,6))`. G4/G5 continúan `NOT_RUN`, la reserva independiente F5 sigue `NOT_CREATED`, O2 no autorizado y D/B/M intactos.

**Siguiente compuerta científica:** si se necesita inferir extracción de materiales o ciclo de bebida, se requiere una etiqueta de tarea externa al pulso T110 o anotaciones validadas sobre señales de máquina. No volver a medir más turnos de la misma fuente como sustituto de esa correspondencia.
