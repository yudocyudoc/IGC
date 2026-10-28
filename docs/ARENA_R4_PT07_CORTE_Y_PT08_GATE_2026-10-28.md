# Arena IGC · Cierre acotado PT-07 / R4 y decisión de entrada PT-08

**Fecha:** 2026-10-28 UTC. **Fuente normativa:** `ARENA_IGC_HOJA_DE_RUTA_V2_0_2026-10-27.md`, §§8–9; `ARENA_IGC_ATMS_PLAN_IMPLEMENTACION_V2_0_2026-10-27.md`, PT-07 y PT-08. **Estado:** propuesta de cierre de **primer corte** sintético de R4; sin certificación de validez externa.

## 1. ¿Qué exigía PT-07?

- Pronosticar y congelar parámetros **antes** de obtener datos evaluativos nuevos.
- Contrastar después sin refit; declarar de forma verificable la custodia y el límite de independencia.
- Medir error predictivo, cobertura estructural, abstenciones, costo y una referencia **REF** sencilla; no otorgar causalidad a un RMSE.
- Una primera prueba interpretable precede a cualquier campaña ampliada; la hoja de ruta **no exige** más casos por simple calendario.

## 2. Primer contraste R4-A / T2: recibido y reproducido

Protocolo [PR #67](https://github.com/yudocyudoc/IGC/pull/67), precompromiso `sha256:94b1231c33f605cbca4efb81aa6a6f31883e628e4303eae9cbdbd53eb78811d8` creado en [Actions #40614473892](https://github.com/yudocyudoc/IGC/actions/runs/40614473892), antes de la nueva simulación.

Experimento prospectivo original [Actions #40618493022](https://github.com/yudocyudoc/IGC/actions/runs/40618493022), una sola ejecución autorizada OpenModelica t=1 h del mundo original T2; adjudicación y repetición offline [#40618879131](https://github.com/yudocyudoc/IGC/actions/runs/40618879131). Resultado y limitaciones íntegros en [informe PR #68](https://github.com/yudocyudoc/IGC/blob/main/docs/ARENA_R4_PT07_T2_REAL_PROSPECTIVE_RESULT_2026-10-28.md).

| Métrica | Resultado |
|---|---|
| Construcción previa | T2, t=0–0.15 h, 27/27 candidatos compatibles, clases C00/C01/C02 |
| Horizonte fijado **antes** | t=1.0 h |
| Pronóstico agregado R4 y REF | 0.06711172531961446 y 0.00007814994299197591 items |
| Nueva observación genuina del simulador | 0.07506397335646263 items |
| Error absoluto de pronóstico / REF | **0.0079522480 / 0.0749858234** items |
| Cobertura de la estructura generadora, revelada después | C01 retenida |
| Conjunto estructural posterior | **C01**; tres configuraciones paramétricas supervivientes |
| Simulaciones nuevas / inferencias IA en R4-A | **1 / 0** |
| Límite de independencia | Generador sintético público del mismo repertorio E1: **no ceguera externa** |

La amplitud de las bandas R4 estaba **congelada**, no era intervalo probabilístico. La mejor puntuación no demuestra mecanismo único ni exactitud en otras dinámicas o perturbaciones. La ventaja frente a REF fue observada **en un caso**, no como tasa de éxito general.

**Veredicto de planificación:** **PT-07 PRIMER CORTE CERRADO / EVALUACIÓN SINTÉTICA INTRAFAMILIA FAVORABLE**. No declarar PT-07 «validación general completada», no consumir nuevas simulaciones para seguir calificando T2, no retocar el método o el umbral. Un futuro estudio externo corresponde a una campaña nueva con reserva realmente independiente y presupuesto explícito.

## 3. ¿Por qué PT-08 y no otro ajuste R4?

El plan PT-08 está condicionado a una **utilidad marginal concreta**, no a instalar un cuarto brazo. Los dos pilotos anteriores de Clef mostraron:

- Numérico: **4/8** conjuntos conservadores correctos, **3 falsos descartes** y **2 apoyos firmes falsos**. Un comprobador determinista sobre las mismas curvas y cotas sigue siendo referencia fuerte: Clef no mostró ventaja numérica.
- Notas operativas redactadas para prueba: **9/9** conjuntos conservadores correctos, frente a **6/9** de una regla léxica deliberadamente estrecha. No son notas de una cafetería real, ni una comparación apareada: los ocho casos numéricos y los nueve semánticos difieren.

[Fuente: dos pilotos reales de Clef](https://github.com/yudocyudoc/IGC/blob/main/docs/ARENA_CLEF_DOS_PILOTOS_REALES_RESULTADOS_2026-10-26.md). Esto habilita una **pregunta más estricta, todavía no un beneficio demostrado**: con **la misma evidencia numérica**, ¿la nota semántica aporta exclusiones correctas sin crear falsos descartes, y puede priorizar evaluaciones físicas de las 27 configuraciones?

## 4. PT-08-A · Primer diseño apareado y controlado (solo preparación offline)

Se reutilizará T2, con **las mismas cuatro observaciones numéricas** y el catálogo C00/C01/C02 original, y se prepararán **tres cortes de información textual**, manuales y declaradamente sintéticos:

1. **Pantalla solamente:** no se observó tránsito ni almacenamiento físico después del despacho. Conjunto no descartable `{C00,C01,C02}`.
2. **Parada física observada, cobertura parcial:** hay al menos un almacén posterior al despacho, pero no se comprobó el resto de la ruta. No descartables `{C01,C02}`.
3. **Seguimiento físico exhaustivo de una ruta:** exactamente una parada física posterior al despacho y ninguna más antes de entrega. No descartable `{C01}`.

Estos **no son tres mundos independientes** y las notas fueron redactadas con conocimiento del generador C01. Son tres *tratamientos de información* sobre un mismo caso sintético. No permiten estimar generalización, ni puede presentarse el mero contenido añadido como «descubrimiento autónomo de C01».

Se producirán pares con y sin nota; mismo numérico, repertorio, formato de salida y criterio de interpretación Clef ya conocido (p≤0.30 excluye, 0.30–0.70 incertidumbre, p≥0.70 sostiene). **Seis solicitudes hipotéticas** (3×2), presupuestadas pero **no autorizadas ni ejecutadas**. Para evitar ventajas artificiales, habrá dos referencias deterministas:

- **Numérica fuerte**: compatibilidad real de las 27 curvas simuladas, RMSE de construcción ≤0.020, igual para ambos lados.
- **Nota estructurada**: aplicación de las reglas explícitas de exhaustividad/cobertura de la nota **sin IA**. Este «oráculo operacional» es una cota superior para estos textos artificiales, no una línea base de NLP con coste real equiparable.

**Métricas primarias:** falsos descartes de clases compatibles bajo la nota, conjunto conservador exacto por par, cambio entre numérico-solo y numérico+nota, y coste marginal medido de inferencia. **Métrica subordinada**: cantidad de configuraciones que un filtro semántico podría priorizar antes de un solver, **solo ahorro hipotético** porque los 27 CSV ya fueron simulados. Nunca presentar 18 simulaciones reutilizadas como ahorro efectivo.

## 5. Compuerta

El preparador `scripts/arena_pt08_clef_paired_preflight.py` producirá únicamente manifest y solicitudes candidatas para el futuro; no invoca ningún proveedor ni simulator. Debe pasar validación de hashes, casos y separación del oráculo. **No se autoriza Clef** mediante este documento o PR.

Si se aprueba el experimento futuro, archivar primero salidas crudas, calificar después bajo la política previa y conservar falsos descartes. Si no produce ventaja frente a las referencias pertinentes, la decisión válida de PT-08-A es **no incorporar Clef**. Clairic y una ampliación de la arquitectura permanecen fuera de esta prueba.
