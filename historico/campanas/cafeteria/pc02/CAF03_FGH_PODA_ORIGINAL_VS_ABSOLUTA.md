# CAF-03 — F/G/H · Experimento exploratorio comparativo de poda K0

**Estado:** protocolo de laboratorio público, no validación independiente ni G5. **Motivación:** PR #111 documentó que la poda relativa descarta candidatos M-C01 en A que satisfacen los límites absolutos K0 y K1; no resuelve B/C/D y ensanchar el conjunto puede empeorar L_set. Esta prueba pone ambas reglas sobre **mundos DES nuevos**, fijados explícitamente antes de su ejecución.

## Diseño cerrado antes de observar F/G/H

| Mundo | Preparación | Despacho | Entrega | Cuello nominal |
|---|---|---|---|---:|
| F | 2 servidores × 1 min | 1 servidor × 6/7 min | 2 servidores × 1 min | 70 pedidos/h |
| G | 2 servidores × 1 min | 1 servidor × 2/3 min | 2 servidores × 1 min | 90 pedidos/h |
| H | 2 servidores × 1 min | 1 servidor × 6/11 min | 2 servidores × 1 min | 110 pedidos/h |

El único recurso cuya velocidad cambia es despacho; los otros dos tienen techo nominal 120/h. No se debe cambiar el diseño una vez observado ningún K0, K1 o K2. Los tiempos son racionales exactos en DES, en vez de interpolaciones aproximadas. Cero pérdidas, cancelaciones y stocks iniciales; cada corte arranca vacío.

La entrada K0 permanece 1.2 pedidos/min durante 20 min, se observan entregas en t5 y t10. **K1 es FIJO e igual para las cuatro variantes**: 1.5 pedidos/min, observación t20; a diferencia de PR #109/#110 no se ejecuta el selector conjunto para este experimento. Es una diferencia **de diseño explícita**, no una política CAF-02 modificada. K2 permanece en 1.35 pedidos/min, entregas acumuladas en t5,10,15,20,30,40.

## Variantes y métricas

En paralelo, sobre los mismos K0 y K1 de cada mundo:

- **M original:** MAE K0≤1 y MAE K0≤mejor de familia+0.4.
- **M absoluta:** MAE K0≤1, sin poda relativa.
- **D original:** mismas reglas de M original, sobre su propia rejilla D1/D2/D3.
- **D absoluta:** MAE K0≤1, sin poda relativa sobre la misma rejilla D.

Todas conservan tolerancia K1 de 0.77; no hay estimación de parámetros nuevos ni ajuste de gramáticas. Cada variante genera envolventes K2 antes de K1, las filtra con K1 y registra nuevas envolventes K2 antes de conocer K2. Se puntúan los mismos seis tiempos usando la función oficial `L_set = media(anchura/2 + distancia_fuera)`, cobertura de la envolvente, abstención de punto y conteo de candidatos por familia. No se pone cero a abstenciones. `REF_SCALE` y `REF_CAF` reciben solo K0; no ofrecen referencia de igualdad informativa frente a K1.

## Comando y registros

```bash
python experiments/cafeteria/pc02/caf03_laboratorio_politicas.py \
  --out artifacts/caf03-fgh-poda
```

Una ejecución por mundo de K0, K1 y K2: **nueve llamadas DES exploratorias** en total. Se usan los módulos originales de DES, curvas M, RK4 D, envolventes K2 y referencias. Los nuevos archivos de CAF-03 viven únicamente en `experiments/cafeteria/pc02`: no se sobrescriben resultados de PR #109/#110/#111 ni se modifica la política oficial CAF-02.

El directorio de salida es exclusivo/no reutilizable. `00_PLAN_PREDECLARADO.json` existe antes de la primera simulación. Cada `mundo_F/G/H` conserva `02_CANDIDATOS_Y_PREDICCIONES_ANTES_DE_K1.json`, `02B_CHECKPOINT_PRE_K1.json`, `05_CUATRO_PRONOSTICOS_K2_PREVIOS_A_DES.json`, `05B_CHECKPOINT_PRE_K2.json`, resultados K2, puntuaciones y hashes. El directorio raíz guarda `01_RESULTADOS.json`, `02_COMPARACION.csv`, `03_INFORME.md` y `04_HASHES.json`.

Las marcas de integridad locales solo demuestran el orden del programa **bajo el modelo de ejecución y las pruebas de software**; no prueban independencia externa. Las ejecuciones de mundos públicos son casos diseñados, no muestra aleatoria. Cualquier elección de política tras ver F/G/H vuelve a ser post hoc, y requiere casos futuros para validación prospectiva.

## Qué decidir con el resultado

Comparar por mundo si la política absoluta conserva familias que original descarta, si gana o pierde cobertura, cuánto varía amplitud/2 y distancia fuera, y cuántas veces deja de abstenerse. No elegir la regla solo por la menor pérdida retrospectiva. No introducir estados intermedios, nuevos sensores de colas, gramáticas nuevas o una fase burocrática adicional durante CAF-03.
