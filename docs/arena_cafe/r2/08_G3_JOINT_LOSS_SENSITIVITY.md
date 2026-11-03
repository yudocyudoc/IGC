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

## 5. Resultados ejecutados (CI RF-03D+03E)

**Fuente:** run `41718520386`, tres jobs PASS, 21 pruebas (10 RF-03D y 11 RF-03E). Artefacto `rf03e-joint-measurement-and-loss-domain-diagnostics` ID `13270443638`, SHA del código `4f8543ec`. Son diagnósticos **sobre la malla** y el escenario de parada, no validación independiente.

| Plan de mediciones conjuntas | Parejas con distancia > 0 en la malla | Parejas con distancia > 0.15 pedidos (margen numérico ilustrativo, ε=0) |
|---|---:|---:|
| Entregas t=3,5 | 15/15 | 0/15 |
| Entregas t=3,5,7,9 | 15/15 | 0/15 |
| Entregas hasta t=15 | 15/15 | 0/15 |
| Entregas hasta t=20 con pausa | 15/15 | 9/15 |
| WIP total t=10,12,15,20 | 15/15 | 9/15 |
| Pérdidas t=10,12,15,20 | 9/15 | 9/15 |
| Entregas + WIP | 15/15 | 9/15 |

**Lectura correcta:** los 15 pares pueden tener una distancia conjunta estrictamente positiva por la discretización del catálogo, pero ninguna secuencia de entregas hasta el minuto 15 alcanza 0.15 pedidos de separación mínima en esta malla. El hallazgo no autoriza decir que más mediciones siempre sean inútiles: demuestra que **el resultado depende de secuencia, resolución numérica y margen físico considerado**.

### Compatibilidad absoluta hipotética común

Con un error máximo por cada una de las cinco lecturas O0 de **0.25 o 0.5 pedidos**, ninguna de las seis familias conserva puntos de la malla que satisfagan simultáneamente el criterio. Con **1 pedido**, 5/6 familias conservan al menos un punto; con **2 pedidos**, 6/6. Estas cifras **no determinan precisión real de POS**; evidencian lo engañoso de comparar solo conjuntos relativos cercanos al mejor de cada familia.

### Pérdida débil: misma capacidad y mismo tiempo de respuesta

| lossTime (min) | Máx. distancia conjunta de entregas en 25 parejas idénticas de parámetros, 1 stock | Máx. pérdida acumulada modelada t=20 |
|---|---:|---:|
| 20 (límite del dominio anterior) | 3.1893 | 3.4949 |
| 80 (extensión) | 1.0575 | 1.1564 |
| 320 (extensión) | 0.2887 | 0.3151 |
| 1,280 (extensión) | 0.0739 | 0.0806 |

Con 2 y 3 stocks se observa la misma tendencia bajo pares del mismo `capacity`/`response_time`. Estos números prueban **sensibilidad del diagnóstico al dominio de pérdida**; no prueban si la cafetería pierde pedidos realmente. Sin una cota operacional superior para `lossTime`, las ramas con pérdida pueden aproximar las sin pérdida durante una ventana finita. Por tanto, el antiguo 9/15 permanece un resultado de la malla original, no una conclusión robusta.

**Advertencia matemática:** una distancia positiva en una malla finita no establece un límite inferior positivo sobre el espacio continuo de parámetros. Los márgenes usados no son tolerancias instrumentales estimadas. La extensión de pérdidas no modifica ni reemplaza los parámetros del ensayo G3 original.

## 6. Límites de alcance y reproducibilidad

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
