# Corrección Astra — fidelidad del traductor B y G3 de construcción (2026-10-26)

## Dictamen que motivó el cambio

Astra señaló un contraejemplo **reproducible**: el traductor del brazo B admitía una variable Buffalo de tipo `stock` con `subType=conveyor` y podía emitir exactamente la misma ecuación que para un stock ordinario. Eso viola G0 si el subtipo introduce una semántica dinámica que no fue trasladada. Astra también corrigió la lectura de G3: **G3 es adecuación respecto a construcción** según el plan rector 1.3; reserva/holdout es una etapa independiente.

## Correcciones implementadas y verificadas

**G0 fail-closed.** El traductor `scripts/arena_b_native_to_modelica.py` admite solo las claves del contrato nativo scalar Buffalo **observadas** en el modelo real original. Campos extra de variable como `subType`, `processingTime`, `delayLength`, dimensiones no modeladas, módulos distintos de vacíos o campos de modelo no conocidos ahora producen un error localizado `UNSUPPORTED_...`, no una traducción por defecto. Se rechazan funciones gráficas sobre stocks y conexiones de material sobre auxiliares/flujos. Esta frontera es deliberadamente restrictiva; **no prueba** que el brazo Buffalo sea incapaz de proponer esos mecanismos, solo que el adaptador G0 aún no los sabe representar.

**Solver scope.** Solo se aceptan `specs = {startTime:0,stopTime:8,dt:0.125,timeUnits:hour,integrationMethod:Euler}`, exactamente la configuración de la prueba original ejecutada. Otra configuración se bloquea en vez de ser ignorada. Generalizar G0 requerirá una nueva implementación y pruebas de semántica nativa Buffalo, sin variar silenciosamente `omc`.

**G3 de construcción descriptivo.** Nuevo verificador `scripts/arena_b_construction_check.py`, que vuelve a evaluar el CSV **real** de OpenModelica y comprueba conservación entre el incremento del stock total `pending_work + delivered_work` y el flujo `arrivals` por Euler. Informa los **dos** convenciones de RMSE:

| Métrica B revisado | Valor |
|---|---:|
| RMSE con t = 0,1,2,4 (4 observaciones) | `0.1670603872459463 items` |
| RMSE con t = 1,2,4 (3 observaciones) | `0.19290471909474044 items` |
| G2 y balance Euler | PASS bajo la trayectoria actual |
| G3 adecuación con cota instrumental | **No adjudicable**: no existe cota declarada |
| Evaluación reservada fuera de construcción | **NOT_RUN** |

**Corrida de regresión real:** [GitHub Actions #40283017108](https://github.com/yudocyudoc/IGC/actions/runs/40283017108) — SUCCESS. Descargó la revisión Buffalo ya generada y autenticada, sin otra llamada Cloudflare. Superó los tests negativos y tradujo/compiló/simuló el mismo modelo nativo original, respetando los dos lookups y la división segura `//`; obtuvo el mismo hash nativo de la fuente semántica (`3aa200a87a3f...` es la huella del JSON canonizado, **no** la huella de bytes del artefacto).

## Qué NO cambia

No hay un motor Buffalo nuevo, ni intento de reparar la ecuación de utilización al cuadrado desde el adaptador. No se ha demostrado paridad Buffalo/Modelica para todas las tablas y subtipos, ni adecuación causal. Tampoco se ha normalizado todavía el protocolo experimental común D/B/M; si se comparan curvas, deberá fijarse conjuntamente ventana, solver, error instrumental, grados de libertad y denominador RMSE. Una diferencia de RMSE causada por agregar el dato t0=0 no es ganancia de método.

**Fronteras pendientes que corresponden a pruebas separadas:** feedback dinámico a Buffalo, simulación de salida revisada de D2, selección estructural molecular desde evidencia y experimento discriminante entre D y M. Conservar las ramas previas como historia; no reasignar nuevos veredictos retroactivos.
