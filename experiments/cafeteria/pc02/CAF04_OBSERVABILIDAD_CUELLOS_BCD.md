# CAF-04 — Qué observación permite localizar un cuello de botella

**2026-10-30. Laboratorio DES, exploración descriptiva.** A partir de PR #110, se sabía que tres cafeterías de 60 pedidos/h con un cuello en distinta etapa (B preparación, C despacho, D entrega) daban exactamente las mismas seis entregas K2. Este experimento contesta dos preguntas: ¿cambiar la presión de entrada revela la ubicación mirando solo las entregas?, ¿y qué información de colas/stock interno bastaría para distinguirlas?

**No es un nuevo experimento confirmatorio ni una ampliación de M/D.** Los mundos B/C/D son ya conocidos y públicos. Se reutiliza sin modificaciones el mismo motor DES discreto y las mismas configuraciones de PR #110, sin cambiar gramáticas, políticas K0/K1/K2, RK4, OpenModelica ni ATMS.

## Diseño fijado antes de ejecutar

Las tres estaciones tienen servicio de un pedido/min por servidor. En cada mundo solo una etapa tiene **1 servidor**, las otras dos tienen **2**. Capacidad mínima 60 pedidos/h en B/C/D. Todos los stocks se reinician vacíos.

| Entrada en 0–20 min | Tasa (pedidos/min) | Razón para incluir |
|---|---:|---|
| LOW | 0.8 | Menor que capacidad del cuello (sin saturación nominal) |
| K0 | 1.2 | Reproducir entrada conocida |
| K2 | 1.35 | Reproducir entrada conocida |
| K1 | 1.5 | Reproducir entrada conocida |
| HIGH | 1.8 | Demanda mayor que capacidad del cuello |
| VERY_HIGH | 2.4 | Demanda superior también a los 120/h de estaciones no limitantes |

Por mundo/tasa se realiza **un único DES**, para un total de 18 simulaciones exploratorias. Se registran estados a los minutos 5,10,15,20,30,40: entregas acumuladas, pedidos aceptados, pendientes, esperando por etapa, en servicio por etapa y stock por etapa (= esperando + en servicio). Balance exigido en cada lectura:

`aceptados = entregados + Σ(esperando + en_servicio)`.

Los resultados K0/K1/K2 históricos ya conocidos se comprueban como regresión. No se usa K2 para seleccionar modelos ni inferir topologías. El directorio `00_PLAN_INSTRUMENTACION.json` se escribe con fsync antes de la primera corrida y declara tasas, mundos y sensores.

## Preguntas de observabilidad

1. **Equivalencia de salidas:** para cada tasa y tiempo, comprobar si B/C/D tienen el mismo número de entregas y pendientes totales. Si coinciden, ese par de observables no localiza la posición del cuello.
2. **Observación interna:** para cada tasa e instante, buscar el número mínimo de canales de *cola esperando por etapa*, *pedidos en servicio por etapa* o *stock total por etapa*, cuya combinación produce tres firmas distintas para B, C y D.
3. **Sensibilidad a presión:** no dar por hecho que esas firmas distintivas existan para todas las tasas; distinguir el campo operativo donde la diferencia estructural se hace observable.

La búsqueda exhaustiva de subconjuntos de hasta 3 sensores para cada modalidad es **posterior a observar** el mundo DES; proporciona mínimos descriptivos *para estos tres mundos específicos*, no un método optimizado validado en mundos futuros. Tampoco afirma costes físicos, de personal o instrumentación para los sensores; se cuenta únicamente el número de canales medidos.

## Ejecución reproducible

```bash
python experiments/cafeteria/pc02/caf04_observabilidad_bcd.py \
  --out artifacts/caf04-observabilidad-bcd
```

Los archivos incluyen la configuración exacta del mundo `00_PLAN_INSTRUMENTACION.json`, registros `01_DES_MUNDO_B/C/D.json`, comparaciones `02_DIAGNOSTICO_SENSORES.json`, inventario `03_OBSERVACIONES_ETAPAS.csv`, resumen `04_COMPARACION_SENSORES.csv`, informe `05_INFORME.md` y hashes locales `06_HASHES.json`.

No reutilizar el directorio: las salidas son exclusivas y no se sobreescriben. Integridad reproducible local, nunca custodia G5 independiente.

**Interpretación:** si solo medir entregas no distingue B/C/D bajo estas tasas y tiempos, eso no implica que nunca pueda distinguirse mediante otra entrada, servicio aleatorio, sensores o perturbaciones directas. Si medir colas o stocks internos distingue B/C/D, esto tampoco acredita que las gramáticas M/D puedan digerir esos observables; eso exigiría un experimento separado con definición de operadores de observación y sus costos.

El resultado buscado no es que «gane» una modalidad de sensor, sino delimitar qué información física necesita el sistema para pasar de predicción de salidas a localización de restricciones.
