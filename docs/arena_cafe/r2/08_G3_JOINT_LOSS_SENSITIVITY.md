# Arena IGC · RF-03E — Separabilidad conjunta y sensibilidad a la pérdida

**Fecha:** 2026-11-03. **Sobre:** PR #146, conservando resultados RF-03C/RF-03D y corrigiendo RF146-01/02/03 de Astra. **Alcance:** cálculo exploratorio sobre EV-01 público O0; no nueva evidencia, no nueva ejecución OpenModelica, DES, Cloudflare o Buffalo.

## 1. Corrección: un intervalo no es una trayectoria

RF-03D solo midió solapamiento de intervalos marginales. La ausencia de brecha por instante no prueba que un vector conjunto de entregas no discrimine. Astra aportó el contraejemplo A={(1,2),(2,3)}, B={(1,3),(2,2)}: en los dos instantes las envolventes son iguales, pero la distancia conjunta mínima en norma máxima vale 1 pedido. Una prueba automatizada exige ese resultado.

En `g3_joint_identification.py` se preservan los vectores completos para cada **misma parametrización** en todas las coordenadas de cada plan, sin hacer combinaciones imposibles de mínimos marginales. Para cada pareja de estructuras D y plan T:

\[d_{A,B}(T)=\min_{\theta_A\in\Theta_A,\theta_B\in\Theta_B}\max_{t\in T}\left|y_A(t;\theta_A)-y_B(t;\theta_B)\right|.\]

Los siete planes comprenden entregas a (3,5); (3,5,7,9); (3,5,7,9,12,15); (3,5,7,9,12,15,20); WIP total a (10,12,15,20); pérdida acumulada a esos tiempos; y un vector conjunto entregas + WIP.

**Condición importante:** el mínimo recorre únicamente puntos de la malla y conjuntos de `MAE <= mejor de la propia estructura + 0.25` ya publicados. Por ello una distancia positiva **no es un límite inferior garantizado** frente a todos los parámetros continuos posibles. No seleccionamos sensores por el máximo de esos números.

## 2. Márgenes ilustrativos ≠ precisión del sensor

Se reporta sensibilidad para valores hipotéticos de error absoluto por medición `ε={0,0.25,0.5,1}` pedidos, comparando `d > 2ε + 0.15` pedidos. El sumando `0.15` es una **margen numérico ilustrativo**, no una cota validada de error del integrador RK4 para todas estas parametrizaciones. No hay error de POS instrumental estimado; todo veredicto se etiqueta como separación *únicamente en la malla y bajo ese margen supuesto*, sin certificar discriminación física.

## 3. Dependencia del dominio de `lossTime`

El dominio previo de construcción tiene `lossTime={0.5,1.5,4,8.1,20}` minutos. Se preserva íntegro como base histórica. RF-03E estudia **sin reajustar los parámetros originales** `lossTime={20,40,80,160,320,640,1280}` minutos, emparejando cada estructura con pérdida con la estructura sin pérdida del mismo número de stocks, y manteniendo **idénticos** `capacity` y `response_time` (25 parejas por topología y por tiempo de pérdida). No se declara ese rango ampliado como prior original ni como parámetro real de cafetería.

Se comprueban diferencias de trayectoria completa de entrega y WIP hasta el minuto 20. La pérdida acumulada satisface la cota conservadora para entrada total 15, inventario inicial 0 y estado no negativo:

\[L(T)=\int_0^T\frac{s_1(t)}{\tau_L}\,dt\le\frac{15T}{\tau_L}.\]

Para T=20 minutos, esa cota es `300/lossTime` pedidos. Si `lossTime` no está operacionalmente acotado, el mecanismo con pérdida puede volverse arbitrariamente débil en este horizonte. Por eso el antiguo 9/15 **no debe convertirse en una conclusión estructural robusta**.

## 4. Un criterio común distinto al «cerca del mínimo propio»

Como exploración de sensibilidad, se examinan los **450 puntos originales** frente a un mismo umbral hipotético de error máximo `max |D_pred(t)-D_POS(t)|`, con t={2,4,6,8,10} y umbrales `{0.25,0.5,1,2}` pedidos, reportando cuántas parametrizaciones de cada estructura cumplen cada umbral.

Esto **no equivale a admisión estadística**: son supuestos de tolerancia ilustrativos, no una estimación de error instrumental ni una región continua de parámetros factibles. Se separa explícitamente este cribado absoluto común de los conjuntos relativos de RF-03C.

## 5. Límites de alcance y reproducibilidad

- Las salidas después de t=10 son **escenarios condicionales con cero pedidos nuevos**, no observaciones futuras ni forecast online.
- Un inventario `total_wip` genérico o `lost` continuo solo puede tratarse como variable medible cuando exista una correspondencia operacional con el sistema físico; hoy son sondas de diseño.
- No se altera D nativo, los seis AST M, sus parámetros, ni Buffalo. El integrador es un espejo externo de Arena ya contrastado previamente en G2 con fixture, no un estimador D.
- El resultado final conserva `A3=PARTIAL`, `G3=EXPLORATORY_CONSTRUCTION_ONLY`, `G4=G5=NOT_RUN`. No existe ganador ni recomendación de instalación de sensor certificada.

## Ejecutar

```bash
python -m scripts.arena_cafe.g3_joint_identification \
  --visible artifacts/public/O0_VISIBLE.json \
  --previous-g3 artifacts/previous-g3/G3_CONSTRUCTION_D_EXTERNAL_GRID.json \
  --out artifacts/G3_JOINT_LOSS_SENSITIVITY.json
```

CI usa exclusivamente artefactos A1 y RF-03C existentes y deja el reporte íntegro disponible para revisión. Las pruebas incluyen el contraejemplo de Astra, conservación de masa, comparación conjunta de los seis D, y el límite de pérdida débil.
