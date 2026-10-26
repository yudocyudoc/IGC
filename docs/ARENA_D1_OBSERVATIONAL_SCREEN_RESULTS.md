# Arena D1 — cribado de compatibilidad observacional y diseño de nueva medición

**Fecha:** 2026-10-25 · **Estado:** verificado en CI, **todavía PR draft**. Parte de [PR #23](https://github.com/yudocyudoc/IGC/pull/23). No es identificación causal, no fusionado a `main`.

## Decisión metodológica

El brazo D es **puro como método generativo**: su espacio de estructuras lo produce una gramática determinista restringida de niveles/flujos conservativos, no SD-AI Buffalo, Clef, un catálogo de moléculas ni una consulta ATMS. El simulador, comprobación física y memoria de eventos son infraestructura externa compartible. Se permite aprender únicamente de observaciones y de resultados propios durante una iteración posterior; **todavía no se implementó una revisión estructural automática**.

## Implementado

- `scripts/arena_d_v1_screen.py` recibe exactamente el mismo `ArenaVisibleInput` de D0 y un protocolo explícito (`data/synthetic/arena_d_v1_screen_protocol.json`) con incertidumbre instrumental **declarada** en unidades del observable, rejillas, presupuesto y tiempos candidatos de una nueva prueba.
- Un integrador RK4 determinista (no reemplaza OpenModelica) respeta exactamente la frontera de un pulso rectangular de entrada y conserva masa con posibles salidas laterales. Ajusta por exploración de grilla `capacity`, `response_time` y, si procede, `loss_time`, sin inferir parámetros fuera de los rangos declarados.
- Cada estructura conserva la **mejor combinación en la rejilla** (máximo residuo absoluto, RMSE). Un candidato con residuo máximo dentro de la cota instrumental declarada tiene testigo `GRID_COMPATIBLE_NOT_IDENTIFIED`. La ausencia de testigo **no falsifica** la estructura: `UNRESOLVED_GRID_NOT_FALSIFIED`.
- Si no se conoce la cota instrumental, se devuelve `INSUFFICIENT_INSTRUMENT_INFORMATION`: **no** se finge aceptación/rechazo. La violación de no negatividad, monotonicidad intervalar o masa observable con cota explícita se marca como contradicción entre observación, supuesto instrumental y familia modelada; **no** como identificación de la estructura verdadera.
- Cuando sobreviven al menos dos alternativas, se propone un ensayo **nuevo, independiente, reiniciado**, que repite el pulso y mide en un instante permitido con gran separación nominal entre predicciones de los mejores ajustes. **Es una heurística exploratoria**, no maximización demostrada de información ni discriminación garantizada bajo incertidumbre paramétrica.
- Se crean modelos Modelica de las seis estructuras con los **parámetros exploratorios** encontrados, `screen.json`, y `memory-events.json`, donde el evento de cribado queda enlazado al evento **real** de D0 (hash, scope y round verificados). No se creó un ATMS persistente ni se reescribió la historia; la primera simulación del cribado es Python, la verificación cruzada es OpenModelica.

## Evidencia ejecutada

- [CI D1 #40246130127](https://github.com/yudocyudoc/IGC/actions/runs/40246130127): **SUCCESS**.
- **12/12** tests D1, **9/9** tests D0, incluyendo negativos de campos reservados, falsos descartes por rejilla, cotas instrumentales, memoria manipulada, masa y salida Modelica falsa.
- La fixture abierta D0 con incertidumbre instrumental **sintética asumida de ±0.20 unidades** evaluó **108 combinaciones** y obtuvo **2 de 6 estructuras compatibles en la rejilla**. Veredicto: `NON_DISCRIMINATING_MULTIPLE_GRID_COMPATIBLE`. No conocemos qué estructura la generó; los cuatro modelos restantes **no fueron falsados**.
- OpenModelica 1.27.1 imagen fijada ejecutó **6 de 6** modelos con los parámetros de mejor ajuste. Las seis series CSV fueron contrastadas con las trayectorias del integrador Python para los mismos tiempos de observación, tolerancia absoluta 0.012 unidades. **Paridad no valida causalidad.**
- [Evidencia cruda #12618981680](https://github.com/yudocyudoc/IGC/actions/runs/40246130127/artifacts/12618981680) conserva los Modelica, CSV, pantalla de ajuste, hashes, cadena de eventos y logs.
- [Regresión F0 #40246129975](https://github.com/yudocyudoc/IGC/actions/runs/40246129975) también **SUCCESS**. La base `main` permanece intacta.

## Interpretación y errores a evitar

1. **2/6 no significa probabilidad 2/6 ni certeza de que una de esas dos es correcta.** La gramática podría omitir el verdadero mecanismo. Los resultados dependen fuertemente de rejilla y de la cota instrumental supuesta.
2. La regla `GRID_NO_FIT` no es refutación estructural: una grilla finita puede saltar parámetros admisibles o una estructura puede estar fuera de la familia. Evitar el error de Short donde una tolerancia rígida produjo falsos descartes.
3. Una serie que ajuste bien no establece que el modelo describa la organización real. Las intervenciones fuera de la muestra y los modelos fuera de catálogo requieren pruebas nuevas.
4. El selector de siguiente medición compara trayectorias nominales de mejores ajustes, **no el solapamiento completo de incertidumbres**. No estimamos información esperada ni costo humano de nueva medición.
5. Aunque la gramática genera seis estructuras, todas son variantes de cadenas de tránsito con posible pérdida; no incluye bucles de retroalimentación, inventarios genéricos ni políticas. Es capacidad acotada, **no el brazo D completo**.

## Próxima frontera, no incluida aquí

Implementar memoria ATMS de **eventos verdaderos**: persistir soportes e hipótesis, contradicciones y revisiones sin pérdida de antecedentes, con acceso a feedback únicamente de la propia vía. Después introducir un **ciclo de revisión** del generador D y una prueba de perturbación con reserva realmente separada. No modificar las técnicas de Buffalo ni moléculas para ayudar a D.

**Conclusión:** tenemos un generador D0 que construye modelos físicos y un cribador D1 que puede reconocer **ambigüedad en evidencia visible** y proponer una nueva observación; todavía no recupera de forma confiable la estructura verdadera.
