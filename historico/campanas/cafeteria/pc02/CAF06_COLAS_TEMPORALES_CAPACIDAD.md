# CAF-06 · Observaciones combinadas: cola, presión y capacidad

**2026-10-31. Estado: experimento DES público exploratorio.** Este protocolo sigue al resultado negativo de CAF-05, donde un sensor aislado de stock en despacho seleccionado con cafeterías de 60/h no pudo separar nuevos cuellos de 75/h (1/3 aciertos, 1 error y 1 abstención).

## Pregunta

¿Mejora la capacidad de localizar **dónde se acumula el trabajo** una regla física que observe conjuntamente las tres colas y su crecimiento temporal, frente al sensor único congelado de CAF-05, cuando la infraestructura y la presión de demanda cambian?

No es un contraste a igualdad de información: la nueva regla utiliza **tres canales**, medidos en dos instantes (seis lecturas), y el comparador CAF-05 utiliza **un canal** en un instante. Aquí comparamos el **beneficio de ampliar la observación**, no cuál algoritmo es superior con datos equivalentes. Tampoco demostramos que M/D puedan observar sus stocks internos; la prohibición de CAF-05 sigue vigente.

## Mundo físico y condiciones predeclaradas

Nueve mundos DES nuevos, con 3 estaciones preparación→despacho→entrega. Un solo cuello en una de las tres, con servicio determinista y **1 servidor**, y las otras dos estaciones **2 servidores × 1 minuto** (120/h). Los tiempos exactos de servicio del cuello son:

| Capacidad del cuello | Tiempo de servicio | Mundos (prep/despacho/entrega) |
|---|---|---|
| 65 pedidos/h | 12/13 minuto | W65P, W65D, W65E |
| 85 pedidos/h | 12/17 minuto | W85P, W85D, W85E |
| 95 pedidos/h | 12/19 minuto | W95P, W95D, W95E |

Entradas durante 20 minutos, sin abandonos, cancelaciones o stocks iniciales, con reinicio por corrida. Tres niveles:

| Condición | Llegadas/min | Qué examina |
|---|---:|---|
| LOW | 0.8 | Baja presión; sin congestión sostenida prevista |
| MATCHED | 1.5 | Presión original del sensor de CAF-05 |
| HIGH | 1.8 | Aumento de presión; aún por debajo de 120/h de estaciones no limitantes |

Se ejecuta una corrida única por mundo/nivel, total **9 × 3 = 27** corridas DES. Se observa exactamente a t10 y t20 (además de t0 y t40 para límites del motor). Se guardan entregas, pedidos aceptados y pendientes, colas en espera, pedidos en servicio y stocks por etapa. Conservación obligatoria: `aceptados = entregados + Σ(esperando + en_servicio)`.

## Dos reglas de diagnóstico congeladas ANTES de la primera observación

### Regla A — Tres colas, crecimiento entre dos instantes

Medir `waiting_preparacion`, `waiting_despacho` y `waiting_entrega` tanto en t10 como en t20. Para cada etapa:

```text
crecimiento(etapa) = cola_esperando(etapa, t20)
                    - cola_esperando(etapa, t10)
```

- Si **una sola etapa** tiene el crecimiento positivo **estrictamente máximo**, se propone como cuello.
- Si todos los crecimientos son cero/negativos, **ABSTAIN_NO_POSITIVE_GROWTH**.
- Si empatan dos o tres etapas con el máximo positivo, **ABSTAIN_TIED_GROWTH**.

No se utilizan prototipos, etiquetas verdaderas, tiempos de servicio ni umbrales aprendidos de los nuevos mundos para emitir el diagnóstico. La regla solo recibe las seis lecturas de cola. La literatura de colas y la conservación física motivan la hipótesis de que las colas crecen junto a restricciones saturadas, pero la regla **no es un teorema de identificación general**.

### Regla B — CAF-05, sensor único heredado

Mismo sensor `stage_stock:despacho` de CAF-05 al minuto 10; prototipos **congelados**: preparación=1, despacho=6, entrega=2. Clasificación por mínima distancia absoluta y abstención por empate. Esta regla se evalúa **solo en MATCHED (1.5/min)** para respetar su contrato anterior; no forzar diagnósticos fuera del dominio para LOW o HIGH.

## Orden temporal y auditoría

El código escribe, con creación exclusiva y `fsync`, `00_PLAN_PRE_DES.json` y `00B_CHECKPOINT_PRE_DES.json` antes de la primera ejecución DES. Ambos registran mundos, tasas, sensores, reglas, prototipos originales y hashes de la política CAF-02. Las pruebas interceptan cada llamada DES para comprobar que el plan ya existía, que no se habían observado resultados nuevos y que no hubo reintentos encubiertos.

Tras las 27 ejecuciones se generan `01_RESULTADOS.json`, `02_COMPARACION.csv`, `03_INFORME.md` y `04_MANIFIESTO.json`.

## Criterios de interpretación

En cada celda capacidad×demanda informar: correctos, erróneos, abstenciones de la regla temporal; resultados del clasificador CAF-05 donde corresponda; diversidad de entregas acumuladas y diversidad de vectores de colas.

**No considerar abstención como error numérico cero, ni automáticamente como éxito.** Cuando la demanda esté por debajo de la capacidad del cuello, la falta de congestión puede dejar al sistema sin señal diagnóstica. Cuando la demanda suba, observar diferencias puede tener costes reales no representados por DES: presión laboral, abandonos y ventas perdidas.

Las configuraciones son públicas y deliberadas, no una muestra aleatoria. No hay testigo externo, ni estimación poblacional, ni recuperación de estructura mediante M/D. Aun si la regla de colas localiza correctamente varios cuellos, no hay evidencia automática de que el diagnóstico se generalice a empresas reales.

## Ejecución

```bash
python -m unittest discover -s experiments/cafeteria/pc02 \
  -p 'test_caf06_colas_temporales_robustez.py' -v

python experiments/cafeteria/pc02/caf06_colas_temporales_robustez.py \
  --out artifacts/caf06-colas-temporales
```

**Regla de no adaptación:** los errores que se observen no se usan para modificar esta ejecución. Cualquier nueva regla o sensor será explícitamente un diseño diferente y deberá probarse en mundos adicionales.
