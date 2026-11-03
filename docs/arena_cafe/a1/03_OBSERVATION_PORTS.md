# A1 · Tercer incremento: operadores de observación de D y puertos tipados de E1

**Fecha:** 2026-11-02  
**PR:** #135 (Draft, apilado sobre #134 F0-HIST).  
**Código de este incremento:** `b57da4bf0fab9613b13361d8a74b23728c9563f2` (fuente y pruebas), más actualización CI `d5f3643` anterior.  
**Alcance:** contratos de entrada verificables que no sustituyen los generadores originales, no simulan el conocimiento que el sensor no posee y no seleccionan modelos. `INTERFACE-01=PARTIAL`, `CONDITION-01=PARTIAL`, `MODEL-01=NOT_RUN`.

## 1. Brazo D · observación de llegadas por intervalo, no pulso conocido

Fuente: O0/O1 POS, conteos acumulados `orders_created_cumulative` y `delivered_cumulative`, muestreados a `t=0,2,4,6,8,10` minutos. La ventana sigue siendo **[0,10)**. Para un par contiguo de muestras `t_i, t_j`, `C(t_j)-C(t_i)` mide el número de pedidos observados en **[t_i,t_j)**. No determina los tiempos individuales de los pedidos dentro del bin ni la tasa instantánea. El adapter entrega:

- Restricción observacional `orders_created_cumulative → integral(inputRate, 0, t)` (contraste de acumulado, **no** una señal conocida impuesta al modelo).
- Restricción observacional `delivered_cumulative → delivered(t)`, el stock terminal que representa la gramática D.
- Bins exactos, conteos enteros y tiempo racional, sin derivación numérica de tasas, sin construcción de `pulseRate` y sin estimación de `capacity`, `responseTime` o `lossTime`.
- O1 no permite suponer que la etapa `preparacion` observada corresponde a un stock particular de la gramática D genérica; esos agregados quedan `NOT_MAPPED_TO_GENERIC_D_STOCKS`.

**Veredicto D:** el contrato de observación es reproducible, pero `scripts.arena_d_v01.validate_case` **continúa rechazando** este input porque exige `pulse` y `nominal_parameters`. La CI ejecuta ese rechazo de la **implementación original**, no un reemplazo. Un futuro puerto para señales exógenas observadas/censuradas requerirá extensión explícita y revisión, no convertir intervalos en un pulso ficticio.

## 2. Brazo M · mapeo tipado contra el registro E1 original

`scripts/arena_cafe/observation_ports.py` llama `get_composer().load_registry` de Short E1 y exige uno de los registros autorizados `registry.base.json` o `registry.extended.json`. Comprueba clases, nombres reales de puerto, dirección, tipo y unidad contra el catálogo E0 asociado. Los tipos genéricos **no se adivinan**: el puerto `bounded-queue.completed` declara `FLOW<U>`; el `role_bindings.preparation.U=ReadyOrder` lo resuelve como `FLOW<ReadyOrder>`. La prueba rechaza una sustitución deliberada por `Shipment`.

| Medida del sensor | Rol y puerto nativos comprobados | Operador de observación propuesto | Condición |
|---|---|---|---|
| Pedidos POS creados acumulados | `source.outflow: FLOW<Order>` (`units/hour`) | Integral del flujo desde 0 hasta la muestra t, con conversión explícita de minutos a horas en futura evaluación | O0 y O1 |
| Pedidos POS entregados acumulados | `receipt.total: STATE<Delivered>` (`units`) | Valor del stock acumulado a t | O0 y O1 |
| Servicios instrumentados de preparación completos antes del corte | `preparation.completed: FLOW<U>` resuelto a `FLOW<ReadyOrder>` (`units/hour`) | Integral en [0,cutoff); asociación de rol autorizada por el nombre de etapa observado, **no identificación del mecanismo E1** | O1 |
| Espera media observada y servicio medio observado de preparación | **SIN puerto compatible establecido** | Ninguno. `waiting` del catálogo es un stock de pedidos, no minutos de espera; `responseTime` es parámetro del modelo, no medición directa de un servicio | Solo O1 |

**Advertencia de correspondencia:** identificar un pedido físico con una unidad material del modelo E1 es una hipótesis de mapeo `ONE_ORDER_EQUALS_ONE_E1_MATERIAL_UNIT_NOT_ESTABLISHED_EMPIRICALLY`. La salida guarda el tipo original, los vínculos T/U, la unidad del puerto y el operador, sin convertir la medición en parámetros o tasas inventadas. Como la hora del catálogo y el minuto del dato difieren, **una futura evaluación de integrales debe usar `dt_h = dt_min / 60`**; este incremento no integra series de modelos ni interpola señales.

**Veredicto M:** mapeo tipado válido y verificable en el catálogo original; el compositor E1 todavía enumera por registro fijo, con `candidate_selection=UNRESOLVED`, `parameter_fitting=NOT_RUN`. No afirma usar la evidencia para seleccionar una estructura.

## 3. Ensayo y custodia

- Nuevos archivos: `scripts/arena_cafe/observation_ports.py` y `tests/test_arena_cafe_a1_observation_ports.py`.
- La CI A1 ejecuta pruebas negativas de temporización, cambio de SHA, cruces O0/O1, catálogo no autorizado, tipo de puerto incorrecto y binding U corrupto. El productor `D` y el productor `M` generan solo su **sidecar tipado** desde la vista de su condición. No se añade a la entrada original de Buffalo.
- El *sidecar* se valida localmente, pero **no es consumido todavía** por la gramática D ni por el selector nativo M; la evidencia técnica no se promociona a `SUPPORTED_AND_CONSUMED`.
- Los seis trabajadores siguen separados mediante matrix CI con un archivo de entrada por condición, sin generador EV-01 ni DES en su checkout. El adjudicador recibe solo recibos mínimos. Esto no demuestra ACL formal, control de API de artifacts, ni separación de ledger/ATMS.

## 4. Lo que sigue realmente pendiente

`BASELINE-01`: registrado. `EVIDENCE-01`: PASS para mundo conocido sintético. `INTERFACE-01`: **PARTIAL**, aunque las restricciones y el mapeo de tipos estén construidos. `CONDITION-01`: **PARTIAL** (separación de trabajos, no custodia formal). `MODEL-01` / `MEMORY-01`: **NOT_RUN**. A2/F2 y A3/F3 no iniciados.

Antes de dar por concluido A1 hará falta decidir el **puerto observacional ejecutable nativo de D** (sin inventar estímulo), la evaluación de `H_j` en Short E1 más un procedimiento independiente y justificable de calibración/selección, y una prueba real y autorizada de uso por Buffalo. La existencia de un `H_j` documentado no asegura identificabilidad. Ninguna llamada Buffalo live se realizó ni se autorizó.
