# Arena IGC — RF-03D, distinguir estructuras sin inventar evidencia

**Base:** PR #145, G3 de construcción ya ejecutado en O0; las seis estructuras D usaron una malla de parámetros **externa a D** y compartieron el input causal de los quince pedidos POS. Este incremento no toca el método original, no ejecuta DES, OpenModelica, Cloudflare ni Buffalo y no modifica los parámetros M.

## Pregunta

La diferencia mínima entre un candidato y otro en cinco conteos acumulados **no identifica** un mecanismo. ¿Qué mediciones podrían distinguir los seis modelos D cuando admitimos **todas las combinaciones próximas al mejor ajuste** de cada estructura, en vez de comparar solamente seis curvas óptimas?

## Lo implementado

`scripts/arena_cafe/g3_observability.py` recompone la **misma malla** del PR #145, sobre la misma evidencia O0 pública, y verifica para cada candidata que el mejor resultado de construcción, los parámetros y el número de combinaciones próximas coincidan con el artefacto anterior. No se selecciona una topología ni se obtiene una nueva conclusión de adecuación.

Cada combinación se prolonga hasta minuto 20 bajo un escenario expresamente hipotético: **solo las quince llegadas de O0, manteniendo la cola causal después del corte en el minuto 10, y cero llegadas nuevas**. Esto **no significa** que hayamos visto nuevos datos reales o pronosticado la actividad posterior de la cafetería.

Para cada una de las seis estructuras se registran tres salidas matemáticas:

1. `delivered_cumulative`: entregas acumuladas (la única salida con operador POS ya establecido) en minutos 3, 5, 7, 9, 12, 15 y 20.
2. `total_wip = sum(s_i)`: material en stocks de la estructura, en minutos 10, 12, 15 y 20. **No está medido en O0**, no equivale a `creados - entregados` cuando hay pérdidas o masa de entrada diferida.
3. `lost_cumulative`: masa que atraviesa el sumidero D `lost` en los mismos minutos. **No debe igualarse automáticamente al número entero de cancelaciones reales** sin una definición operacional adicional.

Se calculan envolventes `[mínimo,máximo]` entre combinaciones con MAE de construcción menor o igual a `MAE_mínimo + 0.25 pedidos`. Este umbral y las fronteras de la malla fueron definidos en RF-03C: **no constituyen intervalos de confianza, identificación ni garantías**.

Se calculan las 15 parejas entre las seis estructuras. Para cada tiempo/magnitud se indica cuántas parejas tienen envolventes que no se intersectan. Es una **evaluación de separabilidad bajo una malla hipotética**, no potencia estadística, ni evidencia observada, ni selección de un método ganador.

## Hallazgos del ensayo sobre la malla exploratoria O0

La CI RF-03D reconstituyó las 450 combinaciones previas para 6 estructuras y encontró:

| Magnitud / tiempo | Pares con envolventes que no se intersectan (de 15) | Interpretación limitada |
|---|---:|---|
| Entregas adicionales t=3,5,7,9,12,15 | **0/15** en cada tiempo | Solo densificar entregas hasta 15 min no distingue ninguna pareja bajo esta malla |
| Entregas en t=20 con pausa de nuevas llegadas | **9/15** | Distingue únicamente estructuras con pérdidas de aquellas sin pérdidas |
| Pérdidas acumuladas modeladas en t=10 | **9/15** | Separación algebraica de las 9 parejas con/sin sumidero, si realmente pudiera observarse la magnitud |
| Inventario total en proceso t=15 | **8/15** | Separa 8 de las 9 parejas con/sin sumidero, sin separar distinto número de stocks dentro de un mismo grupo |

Las 15 comparaciones consisten en **9 parejas entre estructuras con/sin pérdida** (tres por lado), y **6 parejas entre estructuras con igual condición de pérdida pero diferente número de stocks**. Bajo estas envolventes, **ninguna de las mediciones examinadas distingue esas seis parejas del segundo grupo**. Por tanto, no hemos identificado el número verdadero de stocks.

La evaluación es condicional al supuesto de interrupción de nuevas llegadas, al kernel medio minuto, a los parámetros de la malla y al criterio exploratorio de proximidad al mínimo. No equivale a una demostración general de no-identificabilidad estructural ni a potencia estadística.

## Qué aportaría cada nuevo registro

- **Entregas durante una pausa de llegadas:** permiten observar la cola de salida; distintas cadenas, tiempos de respuesta y pérdidas pueden mostrar trayectorias distintas. El ensayo requiere anotar también si entraron pedidos nuevos. Una pausa planificada no es lo mismo que un día ordinario.
- **Inventario realmente en proceso:** contar pedidos presentes dentro de la operación junto con las entregas y las entradas permite cerrar el balance y hacer visible material no explicado. La ecuación de conservación es `entrada_inyectada = WIP + entregas + pérdidas`; WIP y pérdida no son medidas independientes si se deriva una de las otras.
- **Cancelaciones, mermas o pérdidas con definición precisa:** son necesarias para evaluar físicamente la rama `lost`. El `lost` continuo de D puede ser fraccionario y no significa por sí mismo «cancelaciones»; se requiere una correspondencia de magnitud.
- **Colas por etapa:** solo tienen sentido si se demuestra qué representa un stock genérico D en la cafetería. No declarar que `s1` es preparación o `s2` es despacho sin evidencia de esa correspondencia.

El agregado O1 de preparación observado anteriormente **no es un segundo mundo independiente** y no descompone por sí mismo los estados D ni entrega un operador de medición válido para cada stock. No se lo puntúa en esta etapa.

## Criterios de esta entrega

El análisis usa los 450 puntos paramétricos del G3 anterior (25/125 alternativas para cada topología sin/con pérdida), conserva seis candidatas, produce 15 comparaciones estructurales y verifica la suma física de todos los stocks, entregas y pérdidas contra la masa de entrada realmente inyectada. Las trayectorias extendidas hasta 20 minutos son **resultados condicionales simulados**, no evidencia nueva.

La CI puede validar: conservación, no negatividad, origen de los artefactos congelados, reconstrucción de los mínimos y controles negativos de parámetros. **No certifica** que nuevas mediciones distingan realmente los modelos.

## Cómo ejecutar

```bash
python -m scripts.arena_cafe.g3_observability \
  --visible artifacts/public/O0_VISIBLE.json \
  --previous-g3 artifacts/previous-g3/G3_CONSTRUCTION_D_EXTERNAL_GRID.json \
  --out artifacts/G3_OBSERVABILITY_DESIGN.json
```

**Límites:** no se elige ganador D, M o B. No se inventan muestras nuevas. La evaluación de construcción G3 sigue exploratoria; G4 y G5 no se han ejecutado; A3 permanece parcial. Lo siguiente depende de resultados de esta evaluación: decidir **qué medición física mínima puede realmente reducir las alternativas**.
