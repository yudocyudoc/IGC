# Arena R2 — PT-03: decisiones propias D/M con memoria F1a/ATMS

**Fecha:** 2026-10-27. **Origen:** R1 auténtico del PR #54, expediente PT-01 del PR #55 y memoria PT-04 del PR #57. **Estado:** segunda disposición *conservadora* D/M comprobada en CI; Buffalo R2 todavía pendiente.

## Dos decisiones, no dos simulaciones nuevas

- **D:** `RATIFY_SIX_ALTERNATIVES`. Las seis estructuras siguen como posibilidades de la gramática propia. Todas produjeron trazas reales G2, pero la elección de una como mecanismo verdadero no está justificada por cuatro observaciones de construcción, parámetros nominales y ausencia de cota instrumental común. **No se aplicó D2**: esa política requiere otra observación de ensayo que R1 no contiene. D no inventa una séptima propuesta ni declara ganadora la de RMSE 0.150205.
- **M:** `RATIFY_ABSTENTION`. Se reejecutó la decisión original `arena_m3_select.decide` sobre los tres RMSE verificables de las propias trazas R1, con límites anteriores `max_best=0.020` y `min_gap=0.035`. El mejor RMSE es `0.3165595861909595`, por lo que la razón sigue `ALL_FIXED_E1_STRUCTURES_MISS_CONSTRUCTION_TOLERANCE`. **No hay padre M seleccionado**, ajuste paramétrico ni ejecución de M2.
- **B:** permanece `PENDING`; su revisión auténtica en el motor Buffalo original exige un nuevo presupuesto/autorización distinto del experimento R1.

## Alcance epistemológico

Estas decisiones están generadas por políticas conservadoras explícitas y deterministas sobre datos propios, no por una nueva inferencia autónoma de D ni M. Son ratificaciones y no mejoras de ajuste. `scripts/arena_r2_dm_decisions.py` registra el método, entrada, hashes propios, evidencia, justificación, los límites y la ausencia de nuevas observaciones, simulaciones y llamadas.

El ledger F1a almacena la decisión de cada brazo como revisión append-only, enlaza una justificación ATMS a su propio feedback y política, y reconstruye el antes/después con `as_known_at`. Las vistas D/M excluyen el material privado del otro brazo y el estado Buffalo permanece idéntico. ATMS prueba dependencia lógica y continuidad, no la verdad estructural ni adecuación empírica.

**Prueba de aceptación:** [Actions PT-03](https://github.com/yudocyudoc/IGC/actions/runs/40483997449), cuatro pruebas de archivos reales, continuidad temporal, separación entre brazos, rechazo de decisiones alteradas y retirada hipotética de soporte. El resultado positivo de CI certifica esta integración, no que todos los productores hayan aprendido.

**Siguiente etapa:** una revisión Buffalo R2 desde el padre R1 y su propio log, con autorización acotada. Después PT-05 integra las tres segundas decisiones y memoria temporal sin fabricar el RMSE B de R1. R2 completo todavía no se declara.
