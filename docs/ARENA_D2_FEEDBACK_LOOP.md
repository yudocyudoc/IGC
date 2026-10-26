# Arena D2 — primera revisión con nueva evidencia y memoria ATMS (2026-10-25)

**Estado:** implementado y probado **en PR #23 (draft)**, todavía no en `main`. **Método:** determinista puro en generación, ATMS como memoria externa; no se incorporan moléculas, SD-AI Buffalo ni Clef.

## Resultado observado, no extrapolación

[GitHub Actions D2 #40248817463](https://github.com/yudocyudoc/IGC/actions/runs/40248817463) **SUCCESS**: nueve tests D0, doce D1, cinco D-ATMS, siete D2 (**33/33**); seis modelos D1 contra OpenModelica, además de una **nueva simulación Modelica** usada solo por el evaluador; persistencia de la segunda iteración en ledger F1a/ATMS. [Regresión D0 #40248817278](https://github.com/yudocyudoc/IGC/actions/runs/40248817278) y [F0 #40248817504](https://github.com/yudocyudoc/IGC/actions/runs/40248817504): **SUCCESS**.

- D0 generó **6** estructuras en una gramática restringida de cadenas de stocks con salida lateral opcional.
- D1 evaluó **108** conjuntos de parámetros, y halló **2** estructuras compatibles bajo el supuesto instrumental sintético ±0.20 unidades.
- Antes de generar la segunda observación, D1 fijó medir entrega acumulada a las **8 horas** en un **nuevo ensayo con reinicio** y el mismo pulso.
- Un modelo físico sintético nuevo, creado con ecuaciones Modelica del **evaluador** y simulado en el contenedor OpenModelica fijado, entregó la medición. D2 **solo recibió** el objeto `d2-trial-visible.json` (pulso, tiempo, valor, hashes de procedencia), no la estructura del modelo evaluador.
- D2 volvió a ajustar **sobre evidencia de ambos ensayos** dentro de la misma rejilla y su misma cota instrumental. Una estructura mantiene testigo de compatibilidad; la otra queda `REVISION_UNRESOLVED_GRID_NOT_FALSIFIED`. La conclusión: `ONE_REMAINS_OTHER_MODELS_UNRESOLVED`. **No** se declara que el modelo superviviente sea el verdadero.
- ATMS preservó los soportes D1 originales (2) y construyó soporte lógico adicional `D2CURRENT:` para **1**, a partir del soporte anterior y la nueva observación. El ledger guarda de forma append-only la observación, reporte D2 y un evento `HYPOTHESIS_REVISED` de iteración 1, enlazado al evento real `SIMULATION_REPORTED` D1. La historia D1 no se sobrescribe.

## Interfaces concretas

- `scripts/arena_d_v2_revision.py` implementa `extract` (operación solo del evaluador) y `revise` (método D). Su revisión combina los residuos de la primera construcción y el nuevo ensayo desde condiciones iniciales cero.
- `scripts/arena_d_atms_bridge.py` y `scripts/arena_atms.py` se mantienen externos al generador determinista; leen y proyectan `lane:D` bajo investigación+ronda.
- `.github/workflows/arena-d-v1-screen.yml` congela la hora de medición antes de producir el mundo evaluador, ejecuta OpenModelica, comprueba la huella CSV, entrega un **paquete limitado** a D2 y ejecuta la revisión contra el ledger que ya contenía D0/D1.
- `tests/test_arena_d_v2_revision.py` cubre soporte selectivo, caso sin testigo, selección temporal no autorizada, contaminación entre brazos, paquete `gold`, historia previa manipulada, falta de historial y replay de D2.

## Lo que ATMS sabe en las dos fechas

- **Antes de D2:** `DCOMPATIBLE:<candidate>` para dos candidatos bajo soporte `DSTRUCT ∧ DOBS ∧ DINSTR ∧ DGRID`, entendido solo como testigo de **ajuste en rejilla**.
- **Después de D2:** esos dos nodos originales siguen siendo reconstruibles y una nueva justificación `D2RULE:` sostiene `D2CURRENT:<candidate>` para uno, condicionada además a `DTRIAL:<hash>`.
- Ni `ATMS.project` ni `what_if` certifican verdad empírica. La revisión actualiza parámetros propuestos y estatus, **no la topología**. Los candidatos sin testigo de rejilla no se borran ni se declaran causalmente imposibles.

## Restricciones de validez y siguientes fronteras

**Esto es una prueba de ingeniería sintética, no una evaluación científica ciega.** Las ecuaciones del mundo evaluador constan en el workflow del repositorio y son conocidas para quien inspecciona el protocolo. Solo el **paquete de ejecución entregado a D2** carece del mundo generador; no hay separación fuerte de procesos/permisos ni una reserva externa independiente. La segunda medición usa el mismo perfil exógeno y la incertidumbre instrumental se impone como supuesto, no está estimada experimentalmente.

La gramática D sigue siendo acotada. La reducción de dos soportes a uno puede depender de la cota elegida y de la rejilla, sin excluir modelos fuera del repertorio. La selección temporal maximizó una **separación nominal** entre mejores ajustes; todavía no hubo cálculo de valor de información robusto sobre todos los parámetros.

**Siguiente incremento, no realizado aquí:** permitir que D reestructure topologías ante evidencia que no admite ningún candidato, ampliando la gramática determinista y probando que no se adoptan mecanismos de los otros brazos. Para una Arena comparativa formal se necesita un procedimiento de evaluación/custodia independiente y un conjunto de mundos sintéticos inéditos. Buffalo y moléculas siguen aislados, y Clef queda como cuarto brazo futuro.

## Evidencia trazable

- [CI D2 completa](https://github.com/yudocyudoc/IGC/actions/runs/40248817463)
- [Artefacto D visible: CSV, SQLite, reporte D2 y soporte ATMS](https://github.com/yudocyudoc/IGC/actions/runs/40248817463/artifacts/12619352557)
- [Artefacto separado del evaluador: ecuaciones del mundo y CSV](https://github.com/yudocyudoc/IGC/actions/runs/40248817463/artifacts/12619202899)
- [PR de implementación #23](https://github.com/yudocyudoc/IGC/pull/23)

**Conclusión:** D + OpenModelica + ATMS completaron **una revisión de soporte y parámetros** a partir de una nueva observación, sin mezcla metodológica, sin sobrescribir historia y sin declarar recuperación causal.
