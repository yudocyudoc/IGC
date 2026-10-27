# Arena B1 — promoción selectiva del adaptador Buffalo→Modelica

**Corte:** 2026-10-26. **Origen histórico:** PR #30, commit `2d06549bf8d1ab87e5d41c52a134e2cd11854126`. **Base:** IGC main posterior a PR #46.

## Implementación

Se portan sin alterar los bytes lógicos de los cuatro archivos Python del PR #30: traductor de modelo cuantitativo nativo Buffalo a Modelica, diagnóstico de construcción, y sus respectivas pruebas unitarias. Una CI nueva permite ejecutarlos sin credenciales ni proveedor LLM. No se cambia código upstream UB-IAD/sd-ai ni el generador del brazo D o el compositor M.

El traductor **falla cerrado** para subtipos (conveyor/delay/pipeline/smooth), módulos, variables o funciones no compatibles, topologías materiales ambiguas y especificaciones de solver fuera del escenario Euler acotado. Esto evita convertir silenciosamente semántica desconocida en un stock sencillo.

El diagnóstico de construcción verifica conservación de materia en una trayectoria Euler y presenta RMSE descriptivo **sin pasar G3**, porque no se dispone de una cota de error instrumental. Distingue explícitamente `heldout_evaluation_status=NOT_RUN`.

## Límites del gate

- Los tests offline no son ejecución física OpenModelica de una salida Buffalo viva.
- La traducción admite supuestos explícitos sobre interpolación de funciones gráficas; **G0 no es fidelidad universal**.
- El traductor tiene alcance de simulación fijado a t=0..8, dt=0.125, Euler, hora.
- G1 es parcial y no constituye comprobación general de unidades.
- No se establece adecuación G3 ni identificación causal ni ceguera de reserva.
- No se cuenta como revisión autónoma, ATMS integrado ni Arena V0 funcional.

## Siguiente prueba de aceptación

Sobre una respuesta Buffalo nativa autenticada y fechada, ejecutar el traductor, inspeccionar G0 por correspondencia de ecuaciones, correr el .mo en OpenModelica fijado, archivar CSV y diagnóstico, y mantener separados datos de construcción y reserva. Si no es traducible, emitir BLOCKED con causa; no sustituir el modelo.
