# F0-HIST · Decisión de promoción por copia y archivo de CAF-01/02

**Fecha:** 2026-11-02. **Estado:** PR Draft de reorganización; no evaluación física, no inferencia y no modificación de modelos. **Base:** `5e2b5505a9224effe1b5242a3af61663b53aaa5d`.

## Motivación

Una dependencia vigente no debe quedar alojada varios experimentos atrás. Al mismo tiempo, mover o reescribir un motor histórico para dejar «limpio» el árbol rompería procedencia o modificaría resultados. Por ello se separan **procedencia archivada** y **código operativo clonado**.

## Decisiones ejecutadas en este corte

1. Archivar los 137 archivos de `experiments/cafeteria/pc01/` y `pc02/`, y las 42 definiciones CAF-01/02, conservando **los SHA de blob originales** y un mapa máquina a máquina.
2. Promover el DES original, **sin editar un solo byte**, a `scripts/arena_physical/des_engine.py`; conservar su SHA de blob `8cadbc1f9489c3e1cd7eecd020009978873822ba`.
3. Comprobar identidad de archivo en una prueba de regresión y ejecutar un fixture mínimo de conservación en la copia promovida. Ni el fixture ni un CI verde validan nuevas inferencias científicas.
4. Reproducciones históricas: `git checkout 5e2b5505a9224effe1b5242a3af61663b53aaa5d` y artefactos/CI originales; **no** ejecutar automáticamente workflows archivados ni exigir que sus imports resuelvan bajo la ruta `historico/`.
5. No modificar D/B/M, OpenModelica, ledger ni ATMS; no fusionar los Draft y no introducir un nuevo motor de simulación.

## Restricciones para el siguiente corte F0–F3

- Las rutas CAF-01/02 antiguas dejan de ser dependencias permitidas para **nuevas** integraciones. La ruta física vigente será `scripts.arena_physical.des_engine`.
- EV-01/02 (Draft) importan módulos antiguos: **al recuperarlos después**, adaptar sus imports a la copia activa y medir paridad antes de usarlos; no se presupone que hoy ejecutan sobre este PR.
- No confundir `scripts/arena_physical/des_engine.py` (motor DES auxiliar/evaluador) con un cuarto brazo de Arena. D/B/M permanecen independientes y OpenModelica sigue siendo su solucionador.
- Los resultados cerrados CAF-01/02 y sus números históricos no se recalculan ni reescriben.
- Este es **el primer tramo del archivo**, no una declaración de que todo el repositorio histórico ya fue retirado.

## Puertas de aceptación

- `HIST-01`: 179 rutas copiadas con el mismo blob SHA y 179 rutas originales retiradas; manifiesto completo.
- `HIST-02`: fuente clonada con SHA de blob idéntico a la original y fixture de conservación pasa.
- `HIST-03`: ningún cambio a `scripts/arena_v0_*`, D/B/M, Modelica, ledger, ATMS ni resultados de campañas.
- `HIST-04`: workflows CAF archivados fuera de `.github/workflows/`; las ejecuciones históricas siguen enlazadas por SHA de commit y run.
- `HIST-05`: CI existente sobre los componentes activos se verifica antes de fusionar; cualquier import roto bloquea el merge. Un PR Draft puede permanecer incompleto.

## Relación con plan v3.2

Esta decisión constituye `F0-HIST` **dentro de F0**, no añade una fase científica. No habilita G4/G5 ni futuras inferencias Buffalo. La primera entrega de ciencia sigue siendo F0–F3 con D/B/M reales, sin reusar holdouts históricos.
