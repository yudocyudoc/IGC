# Arena M2 — una revisión paramétrica por diagnóstico propio (Short E1)

**Fecha de integración:** 2026-10-25/26. **Rama:** `feature/arena-m2-own-feedback-revision-v01`, base PR #28. **Estado:** incremento experimental, resultados numéricos únicamente tras CI.

## Por qué esta iteración

M1 / PR #28 produjo una única hipótesis molecular propia (`M-f250c7b99b2c`), con las moléculas originales E1 de `short` y un pulso común de 1.7 items/h durante 2h. Su simulación real de [GitHub Actions #40271768284](https://github.com/yudocyudoc/IGC/actions/runs/40271768284) conserva materia (residuo <7e-12) pero sobreestima las entregas de construcción en t=2 y t=4. El modelo inicial tenía dos colas serie, cada una con `responseTime=0.5 hour` y `maxThroughput=20 items/hour`, declarados por el registro histórico E1 y nunca estimados empíricamente.

M2 investiga si el **mismo brazo molecular**, usando exclusivamente sus propios residuos de M1, puede producir una revisión de parámetros acotada que corra de nuevo en OpenModelica sin introducir mecanismos ajenos.

## Procedimiento fijado ANTES de examinar M2

1. Reproducir el artefacto M1 de [Actions #40271768284](https://github.com/yudocyudoc/IGC/actions/runs/40271768284), descargado mediante `actions/download-artifact@v4`. Verificar el SHA-256 **de bytes** de los cinco ficheros: `native-graph.json`, `submission.json`, `memory-event.json`, `g2-construction-report.json` y `m-visible_res.csv`; además reconstruir nativo/entrega/evento mediante el generador M1 original y verificar el informe con un lector CSV independiente.
2. La política de revisión pertenece solamente a M. Si hay residuo `simulado-observado > 0.1 items` tanto en **t=2** como en **t=4**, una sola vez: `responseTime := 2 × responseTime` para ambas colas originales `preparation` y `dispatch`. Si los residuos no cumplen el patrón, los datos son insuficientes, los rangos del registro lo impiden, o hay asimetría de parámetros iniciales, **abstenerse** sin fabricar un modelo.
3. Los límites `responseTime ∈ [0.1,5]` proceden del catálogo Short E1; para este caso se propone `0.5→1.0 hour` en cada cola. Se mantiene `maxThroughput=20 items/h`, la estructura de cuatro componentes, los siete puertos conectados y el pulso común.
4. Emitir una única `ArmSubmission` con `iteration=1`, revisión padre `M-f250c7b99b2c:r0`, hash nativo nuevo, detalle de los dos cambios paramétricos y los eventos encadenados `FEEDBACK_DELIVERED` y `HYPOTHESIS_REVISED` referenciados al evento M1. Estos **son trazas append-only**, **no** un ATMS de producción ni retractación/restauración plena.
5. Generar Modelica usando `backend.render_model` **sin editar** del Short E1, sustituyendo sólo el estímulo público externo mediante el adaptador ya auditado. Comparar el hash topológico canónico para bloquear cualquier cambio de estructura.
6. Ejecutar **una única simulación nueva OpenModelica** con el mismo OMC 1.26.5 / MSL 4.0.0 / SystemDynamics 2.1.2. Verificar balances dinámicos independientes desde los puertos `STATE` tipados y no desde el contador informativo `inTransit`.
7. Comparar los residuos observados t=0,1,2,4 y los RMSE M1/M2, informar el signo del cambio **sin asumir que necesariamente mejora**.

No se realiza una rejilla de parámetros, ajuste Bayesiano, selección post hoc entre estructuras, segundo LLM ni repetición oportunista. No hay nuevas inferencias Cloudflare. El presupuesto del paquete original `max_model_proposals=1`, `max_simulations=2`, `iteration_limit=2` se valida explícitamente: **una propuesta inicial y una revisión de la misma hipótesis; una simulación G2 por versión**.

## Integridad y fronteras

La fuente válida de M2 es únicamente `ArenaVisibleInput` y los cinco artefactos **M1** anteriores. Ningún modelador M consume salida nativa, modelo, residuo, AST ni diagnóstico de los brazos D/B; ninguna muestra es reservada. El diagnóstico G3 indica `PARTIAL` porque compara datos de *construcción*; no se presenta como `G3_HELDOUT_PASS`.

**No se demuestra identificabilidad de parámetros.** Al duplicar los dos tiempos de respuesta en una estructura con colas serie simétricas, estamos moviendo un grado de libertad compartido por una política heurística, no identificando por separado ambas dinámicas. Una mejora de RMSE implicaría mejor reproducción de los mismos datos que guiaron el cambio, no mayor poder predictivo independiente.

### Estados y límites a adjudicar con CI

| Aspecto | Veredicto posible |
|---|---|
| Fidelidad a Short E1 | Fuentes y composición original intactas, estructura canónica igual |
| Recepción M1 y feedback propio | PASS solo si los cinco SHA, la salida CSV y el linaje coinciden |
| G0 | Correspondencia semántica Order→Work provisional, no certificada |
| G1 | Contratos tipados + conservación independientes; dimensionalidad general no certificada |
| G2 | Real OpenModelica PASS/FAIL según ejecución |
| Comparación de construcción | MEJORA o NO_MEJORA; ambas respuestas se conservan |
| G3 de reserva, causalidad y ATMS pleno | NOT_RUN / NOT_DEMONSTRATED |

**Siguiente frontera tras un M2 exitoso:** adjudicar si vale la pena una futura observación discriminante y congelar un nuevo horizonte antes de ver sus datos. No volver a usar los cuatro puntos de construcción para reclamar validación fuera de muestra.
