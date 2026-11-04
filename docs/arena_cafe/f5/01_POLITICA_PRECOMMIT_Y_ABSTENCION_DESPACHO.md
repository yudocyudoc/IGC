# Arena IGC · F5 · Política congelable de medición de despacho y compuerta de abstención

**Fecha de desarrollo:** 2026-11-03. **Antecedentes exactos:** PR #152 (dos mundos FIFO indistinguibles bajo O0/O1), PR #157 (B2 y advertencia de lookahead) y PR #158 (testigo retrospectivo: 4 frente a 5 terminaciones de despacho estrictamente antes de t6). Este archivo **no** registra una reserva F5 ni una prueba independiente; documenta el contrato de ingeniería previo a conseguir datos nuevos.

## Decisión y procedencia

La propuesta fija una sola variable de medición:

`#(despacho.servicio_fin con t < 6 minutos)`, sobre un **recorrido BASE previo a cualquier intervención**, con el mismo sentido temporal de O0/O1 (`[0,6)`, sin sumar eventos exactamente en t6). El corte t6 no fue elegido a ciegas: es consecuencia **post-hoc** del testigo F4 ya conocido. Congelarlo ahora evita retocarlo al ver **futuros** datos, pero **no convierte su elección pasada en una selección prospectiva de EV-01**.

La política de comparación queda limitada a **dos hipótesis previamente declaradas**:

| Conteo real de despacho antes de t6 | Interpretación condicional (si captura y reloj fueran correctos) |
|---|---|
| 4 | Compatible con A, no con B, **dentro del par declarado** |
| 5 | Compatible con B, no con A, **dentro del par declarado** |
| Otro valor | **Abstención**: ninguna de las dos hipótesis conocidas reproduce la medición |
| Sin registro, reloj no compartido o estación no observada | **Abstención** por observación inutilizable |

A y B **no son una enumeración exhaustiva de los mecanismos posibles**. Una coincidencia con 4 o 5 no demuestra cuál es la estructura física verdadera, ni se traduce por sí sola en una predicción de intervención o en un resultado de D/B/M.

## Dos pasos diferentes (la frontera que faltaba)

1. `freeze` emite el JSON íntegro de la política y su `policy_sha256` determinista. No recibe un log físico ni importa el DES o la verdad privada. El archivo no se sobreescribe. El SHA identifica **contenido**, no es firma digital, prueba de cronología ni sustituto de custodia externa. El commit del repositorio constituye el corte de versión que debe quedar **antes de cualquier nuevo dato usado en una evaluación**.
2. `probe` recibe **solo un CSV de eventos truncados a [0,6)** y el contrato `pilot_event_capture.py` del PR #151. Este valida nombres de eventos, visitas, secuencia física, recursos, censura, pseudónimos y relojes declarados. No rellena terminaciones ausentes. Si falta una medición de despacho o no hay reloj común declarado, devuelve abstención.

Los dos comandos son:

```bash
python -m scripts.arena_cafe.f5_sensor_precommit_gate freeze \
  --out artifacts/F5_SENSOR_POLICY.json

python -m scripts.arena_cafe.f5_sensor_precommit_gate probe \
  --policy artifacts/F5_SENSOR_POLICY.json \
  --events captura_hasta_t6.csv \
  --source-context real_pilot_declared \
  --out artifacts/F5_SENSOR_PROBE.json
```

La entrada CSV debe tener **exactamente** los diez encabezados de `pilot_event_capture.EVENT_FIELDS`. Debe contener eventos POS `pedido_creado` y las visitas físicas de despacho registradas antes de t6 con `visit_id` y recurso en `servicio_inicio/fin`. Los eventos posteriores a t6 están prohibidos. No se entregan a la salida IDs, instantes por caso o recursos individuales: solamente conteo agregado, hash del archivo de entrada y estados de validez.

**Advertencia:** `source-context=real_pilot_declared` es una **declaración del suministrador**, nunca prueba independiente de que ocurrió un piloto real. Tampoco un único `clock_id` acredita reloj calibrado, una serie aparentemente íntegra acredita ausencia de pérdidas, ni los dos mundos usados en las pruebas proporcionan un G5.

## Condiciones que siguen impidiendo un resultado científico

Para pasar de compatibilidad descriptiva a un resultado independiente hace falta contar con **una fuente nueva cuyo mecanismo no se revele durante selección e inferencia**, instrumentación verificable de servicios terminados, control de pérdidas/duplicados de eventos, resolución/alineación del reloj, condición base separada de la intervención y una evaluación prospectiva predeclarada con sus abstenciones. Si se pretende medir el beneficio de D/B/M, deben participar los tres métodos originales con la misma evidencia autorizada, presupuesto, aislamiento y predicciones congeladas antes del resultado.

El código **siempre** declara `source_origin_independently_attested=false`, `pilot_event_capture_completeness_verified=false`, `scientific_identification=NOT_ESTABLISHED`, `F5_independent_reserve=NOT_CREATED`, `A3=PARTIAL` y `G4/G5=NOT_RUN`. **Nunca interpreta una coincidencia con 4/5 como validación científica.** El operador físico de Moléculas no se recalibra y la minería de procesos permanece condicional.

## Pruebas de ingeniería, no un estudio independiente

Se usan **solo como fixtures históricos conocidos** los mundos A/B de F4. La CI debe reproducir conteos 4 y 5, pero comprobar también que la política no cambia según el archivo, que un registro tardío o en t6 no entra, que sin estación o reloj común se abstiene, que un `servicio_fin` faltante no se inventa, y que el score no contiene eventos, casos ni recursos privados. Un experimento con datos reales todavía necesita implementación y custodia por separado.

**Decisión:** el trabajo habilita una frontera de obtención de evidencia mejor definida. **No abre G4, G5, ni un nuevo mundo simulado para producir un triunfo retrospectivo.**
