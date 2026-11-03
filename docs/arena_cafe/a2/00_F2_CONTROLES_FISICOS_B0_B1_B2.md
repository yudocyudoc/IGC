# A2/F2 — Controles físicos B0, B1 y B2 · Cafetería EV-01

**Fecha:** 2026-11-02. **Estado:** control de ingeniería realizado, no inferencia científica ni F3.  
**Base de implementación:** PR #135 (A1/F1), encadenado a PR #134 (F0-HIST); rama separada A2/F2.  
**Contrato rector:** `REVISION_Y_PLAN_IMPLEMENTACION_CAFETERIA_V3_2_2026-11-02`, §F2.  
**Reproducción:** [Actions 41552216315](https://github.com/yudocyudoc/IGC/actions/runs/41552216315), commit `b1b4a7172f8a1549d04c514ff8091e2536e06f8d`, **PASS**. [Artefacto JSON](https://github.com/yudocyudoc/IGC/actions/runs/41552216315/artifacts/13191977748).

## 1. Dos experimentos distintos

**EV-01 regresión:** 15 pedidos; el calendario EV-01 independiente y el CAF-01 DES original concuerdan en **9 checkpoints**. Hay exactamente **45 filas POS, 75 POS+KDS y 225 FULL**. Los registros `resource_id` proceden del **generador EV-01**, no se construyen retrospectivamente desde el motor genérico. No se altera ninguna fuente ni el comportamiento original de CAF-01, ni se produce una falsa evaluación independiente.

**Sostenido:** control físico NUEVO con 300 pedidos a **150/h durante [0,120)**, sistema vacío en t=0, políticas FIFO/ties originales y conteos de salida en **(30,90]**. Este ensayo **no** reutiliza como si fuese prolongación el lote original de 15 pedidos. Se preservan el WIP inicial en t=30, las llegadas entre t=30 y t=90, el WIP final y la diferencia finita contra el techo nominal. No se llama estacionario a un sistema cuya demanda supera su capacidad.

## 2. Tres controles que no deben confundirse

### B0 — Contabilidad observable desde POS

`b0_public()` recibe **solo** eventos POS autorizados y snapshots de paridad de la fuente evaluator; comprueba para cada checkpoint:
`accepted(t) = delivered(t) + WIP(t)`, con terminal entregado exclusivo en este mundo sin cancelaciones ni abandono. La salida contiene tiempo, entradas, entregas y WIP, **nunca** `resource_id` ni nombres de estaciones físicas. Se declaran NO identificables los tiempos por etapa desde POS.

### B1 — Medición física completa (FULL)

`b1_physical()` reutiliza **sin modificar** `scripts/arena_cafe/diagnosis.py` y `arena_event_observability.analyze_view`. Se validan 15 balances temporales de ciclo y, para **cada una de las cuatro etapas instrumentadas**, exactamente 15 entradas, 15 inicios de servicio y 15 finales. Se mide espera, servicio, ocupación y presión de cola observada. `preparacion` concentra la mayor espera acumulada en el control, pero no se identifica por ello automáticamente como el único cuello causal. POS y POS+KDS se rechazan explícitamente como fuentes insuficientes.

### B2 — Períodos por recurso real

`resource_periods()` reconstruye intervalos exactos por **ID físico** usando pares `servicio_inicio`/`servicio_fin`; verifica identidad de recurso, no solapamiento, balance de cola por etapa y continuidad de cobertura [0,30). La telemetría de servicio debe tener `source=instrumentacion_fisica`. La disponibilidad de servidores **no** se infiere de silencio: el caso de control declara explícitamente ventanas de disponibilidad [0,30) para los cinco recursos y esa suposición queda registrada; sin disponibilidad, el recurso sin actividad comprobada permanece `UNKNOWN`. Una actividad de servicio prueba disponibilidad **solo durante ese servicio**.

- `PROCESSING`: servicio físico instrumentado; es la **única** etiqueta `ACTIVE` de este ensayo.
- `STARVED`: servidor *declarado disponible*, sin servicio y sin cola habilitada en ese instante.
- `IDLE_AVAILABLE`: servidor disponible sin servicio con trabajo esperando; no se etiqueta automáticamente como espera de operador.
- `UNKNOWN`: no hay evidencia suficiente de disponibilidad/estado.
- `NOT_AVAILABLE`: no está en una ventana de disponibilidad declarada.
- `BLOCKED_AFTER_SERVICE` y `WAITING_FOR_OPERATOR`: **no observados ni fabricados**. El DES original no tiene buffer finito que permita inferir bloqueo posterior al servicio.
- `ANY_ACTIVE`/`ALL_ACTIVE`: agregaciones descriptivas; si no hay recursos disponibles, resultado `NO_AVAILABLE_RESOURCES` (nunca `ALL_ACTIVE=True` por vacuidad). Telemetría insuficiente produce `UNKNOWN`, salvo actividad físicamente constatada.

**Períodos medidos [0,30) para cinco recursos, en minutos exactos:**

| Recurso | PROCESSING | STARVED |
|---|---:|---:|
| caja-r1 | 8 | 22 |
| caja-r2 | 7 | 23 |
| preparacion-r1 | 225/17 ≈ 13.235 | 285/17 ≈ 16.765 |
| despacho-r1 | 450/43 ≈ 10.465 | 840/43 ≈ 19.535 |
| transferencia_final-r1 | 45/11 ≈ 4.091 | 285/11 ≈ 25.909 |

Estos porcentajes o rachas de actividad **no demuestran por sí solos** el cuello único ni un cuello doble.

## 3. Capacidad: techo nominal vs conteo finito real

Configuración original, según EV-01: dos cajas de 1 min/pedido; preparación de 60/68 min; despacho de 60/86 min; transferencia final de 60/220 min. Capacidades máximas **por etapa**: **120 / 68 / 86 / 220 pedidos/h**. El techo de la cadena es el mínimo.

| Intervención sintética, factibilidad NO evaluada | Techo analítico (pedidos/h) | Entregados **(30,90]** | WIP t=30 → t=90 |
|---|---:|---:|---:|
| Base | 68 | 68 | 44 → 126 |
| +1 servidor preparación | 86 | 86 | 36 → 100 |
| +1 servidor caja | 68 | 68 | 44 → 126 |
| +1 preparación **y** +1 despacho | 120 | 120 | 21 → 51 |

Son **300 entradas nuevas en dos horas**, de las cuales **150** ocurren dentro del intervalo de medición. El balance de cada celda es `WIP(30) + 150 − entregados(30,90] = WIP(90)`. En este ejemplo las entregas finitas coinciden numéricamente con el techo de 60 minutos, pero esa igualdad **no es general**: el reporte contiene explícitamente `finite_window_count_minus_nominal_ceiling` y reconoce fase, condiciones iniciales y transitorios. Un techo es una cota nominal, no garantía de entregar exactamente 68 pedidos en cada ventana.

**Interpretación local limitada:** para este DES y demanda sostenida de control, añadir caja **no cambia** el throughput; añadir preparación cambia el límite nominal de 68 a 86/h; añadir preparación y despacho cambia el límite nominal a 120/h. No se prueba que contratar o comprar equipos resulte factible, eficiente o rentable. Espacio, máquina, inventario, costos, turnos y mezcla de productos **no se han evaluado**. La comparación NO descubre un mecanismo causal nuevo: son parámetros conocidos del control del evaluador.

## 4. Pruebas y límites de divulgación

`tests/test_arena_cafe_f2_physical_controls.py` verifica paridad EV-01, B0 balances y rechazo de corrupción, B1 datos FULL y denegación POS/KDS, estados B2 por recurso, cobertura temporal, `ALL_ACTIVE` sin disponibles, telemetría ausente, timestamp administrativo inválido, servicio sin final, recurso solapado, sensibilidad y conservación de las cuatro intervenciones sostenidas. Se ejecuta además la suite original `experiments/arena_cafe/test_diagnosis.py`.

El producto del workflow se publica solo como **artefacto evaluador F2**, no se introduce en la entrada de los productores O0/O1 y no se consume por D/B/M durante este incremento. La etiqueta evaluator-only indica frontera *de proceso y contrato*, **no un ACL GitHub formal** frente a un token que pueda descargar artifacts. Mantener `CONDITION-01=PARTIAL`.

**Gates:** `EV01-REGRESSION=PASS` y `RESOURCE-01=ENGINEERING_CONTROL_PASS`, condicionados a las fuentes instrumentadas del mundo sintético. `F2` cumple el control físico de esta fase, no constituye descubrimiento de cuellos dobles, ni evidencia de PM, ni identifica la física de una cafetería real. A3/F3 y los tres motores nativos permanecen como siguiente integración sustancial.

### Fuente de código

- `scripts/arena_cafe/f2_physical_controls.py`: nueva capa de referencia. Importa el generador EV01, la diagnosis original y el DES original, **sin modificar sus métodos**.
- `scripts/arena_cafe/ev01.py`: generador independiente instrumentado, fuente de IDs físicos.
- `scripts/arena_physical/des_engine.py`: motor CAF01 DES existente, única fuente del ensayo sostenido.
- `.github/workflows/arena-cafe-a2-physical.yml`: pruebas aisladas de evaluator con reporte JSON, sin Blue/Buffalo/Molèculas, sin proveedores, sin OpenModelica adicional.
