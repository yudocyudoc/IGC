# CAF-01 / M-C00 — representabilidad exploratoria con construcción únicamente

**Fecha: 2026-10-30. Estado: estudio matemático-exploratorio posterior a la evaluación cerrada, no pre-registrado.** PR de implementación [#97](https://github.com/yudocyudoc/IGC/pull/97); ejecución GitHub [#41017881129](https://github.com/yudocyudoc/IGC/actions/runs/41017881129), exit=0. El resultado CAF-01 original, incluyendo el fracaso predictivo de M, no se modificó ni recalibró.

## Pregunta y frontera

La primera evaluación reservada midió MAE de REF-CAF=1.6667, REF-SCALE=2.0833 y M=14.1717. El M seleccionado `M_C00_C72` es una cadena de dos moléculas **BoundedQueue**, de preparación a despacho, con `responseTime` de 0.5 h cada una y `release=min(capacity,stock/responseTime)`. La pregunta nueva es: ¿esas mismas dos moléculas, **con otra parametrización**, pueden aproximar la **construcción** al menos tan bien como un estimador sencillo?

Único insumo empírico leído por el análisis: `public_inputs/run_40915090599/CAF01.json`, SHA-256 `727501a3b5b33a63ab5a5d5f0f907d5431d0ee4f0d8b24ffd6f97758d59386fb`. Se observan entregas acumuladas 3/8/13/18/24/24 en minutos 5/10/15/20/30/40 con entrada pública 1.2 pedidos/min. **No** se leen los valores posteriores de evaluación, fuentes privadas DES, ni los pronósticos futuros G4.

## Método acotado

- Estructura única C00: dos stocks de las moléculas E1 existentes, salida de cada una acotada por capacidad. **No** se añaden componentes o conexiones.
- Capacidades conjuntas originales: 20, 72 y 100 pedidos/h. No se introduce ninguna capacidad nueva.
- Tiempos de respuesta de preparación/despacho **variados independientemente** (la campaña original no lo hizo): primero los valores históricos 15, 30 y 60 minutos; después hipótesis exploratorias 1, 2, 3, 5, 7.5 y 10 minutos, **sin validación operativa**.
- 9×9×3=243 combinaciones nominales. Se computan con Heun 0.05 min y 0.025 min, sin OpenModelica, RK4, Buffalo ni DES; se exige conservación y concordancia numérica <0.005 pedidos. El caso original de 30/30 min se contrasta adicionalmente con solución analítica de dos compartimentos sin saturación.
- Como comparador **dentro de construcción**, se estima REF-CAF usando exclusivamente los mismos puntos de construcción. Obtiene tasa efectiva 1 pedido/min y MAE **1.333333 pedidos** (no confundir con el MAE **1.666667** de REF-CAF en evaluación G4).
- Criterio descriptivo de comparabilidad exploratoria: MAE de construcción de C00 ≤ 1.333333+0.25 pedidos. La banda 0.25 es una regla exploratoria de proximidad, **no** incertidumbre instrumental ni nueva regla G4.

## Resultado computado en GitHub

| Configuración | MAE construcción (pedidos) | Alcance |
|---|---:|---|
| M original C00, 30/30 minutos y 72/h | 13.0040 | Parametrización histórica ensayada |
| Mejor del subconjunto 15/30/60 minutos, 15/15 minutos y 72/h | 10.0766 | Sin comparabilidad con REF-CAF |
| REF-CAF, ajustada con construcción | 1.3333 | Diagnóstico convencional *in-sample* |
| Mejor C00 de todo el barrido, 1/3 minutos y 72/h | **0.5057** | Hipótesis matemática, sin justificación operacional |

La mejor alternativa C00 hipotética presenta esta curva en construcción:

| Minuto | Entregas observadas | C00 hipotética | Residuo pronóstico menos observado |
|---:|---:|---:|---:|
| 5 | 3 | 2.2159 | −0.7841 |
| 10 | 8 | 7.3926 | −0.6074 |
| 15 | 13 | 13.2364 | +0.2364 |
| 20 | 18 | 19.2069 | +1.2069 |
| 30 | 24 | 23.8076 | −0.1924 |
| 40 | 24 | 23.9931 | −0.0069 |

**0** combinaciones del subconjunto histórico alcanzaron la banda de comparabilidad. **22** combinaciones nominales del barrido completo sí la alcanzaron, pero corresponden a **11 clases diferentes**: a una entrada máxima de 72 pedidos/h con estados iniciales vacíos, las capacidades 72/100 pedidos/h nunca restringen el flujo de las dos etapas y resultan equivalentes. No se contaron estas duplicaciones como 22 soluciones comportamentales independientes.

Diferencia numérica máxima entre Heun grueso/fino: **0.000188 pedidos**. Son resultados de una aproximación numérica auditada y un rango discreto, **no** una prueba matemática de óptimo global.

## Qué sí y qué no concluimos

1. **Sí hay representabilidad matemática de construcción con dos moléculas C00 ya existentes** para tiempos cortos hipotéticos. Por tanto, no se puede declarar incapaz a toda la familia C00 de producir esa forma temporal.
2. La parametrización original 30/30 minutos generaba una respuesta demasiado lenta y la búsqueda original **solo variaba capacidades, con los tiempos fijados**. No podía seleccionar tiempos 1/3 minutos que nunca le fueron ofrecidos.
3. Ni la fidelidad operacional de tiempos 1/3 minutos, ni la identificabilidad de esos tiempos, ni la transferencia de esa parametrización a nuevos pulsos han sido demostradas.
4. La incapacidad de igualar REF-CAF **en el subconjunto histórico inspeccionado** no demuestra imposibilidad para todos los tiempos mayores o para otras topologías C01/C02. Tampoco demuestra que SD sea inferior a una cola empírica simple.
5. La evaluación reservada original permanece **cerrada**; ninguna predicción anterior fue corregida, sustituida o puntuada otra vez. La nueva parametrización **no** adquiere derecho a una puntuación competitiva en ese mundo ya revelado.

**Decisión técnica sugerida:** antes de evaluar otra vez, obtener rangos de servicio sustentados operativamente y estudiar si el modelo puede identificar parámetros de forma estable a partir de construcción. Es un nuevo protocolo, no una enmienda retrospectiva de CAF-01.
