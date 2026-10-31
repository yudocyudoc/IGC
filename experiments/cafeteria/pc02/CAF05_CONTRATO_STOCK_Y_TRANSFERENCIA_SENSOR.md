# CAF-05 — Contrato de observabilidad física y transferencia de un sensor

**Fecha:** 2026-10-31. **Estado:** experimento exploratorio público. **No se modifica CAF-02, CAF-03 ni CAF-04; tampoco M, D, la gramática de moléculas, el motor DES o los filtros K0/K1.**

## Pregunta

CAF-04 encontró que B/C/D pueden tener exactamente las mismas entregas acumuladas bajo seis presiones, pero distintas colas y stocks por etapa. **¿Sirve un sensor escogido con B/C/D de 60/h para distinguir tres mundos nuevos de 75/h, sin volver a escogerlo?** Y, separadamente, **¿qué observables internos pueden atribuirse legítimamente a los candidatos M y D?**

Estos son dos componentes de un solo laboratorio. **La transferencia física del sensor no es un ensayo de identificación de topologías M/D.**

## 1. Contrato de observación de stocks

| Observable físico | M C00/C01 | D D1/D2/D3 | Uso permitido ahora |
|---|---|---|---|
| Entregas acumuladas | Salida del surrogate E1 | Salida de la cadena RK4 | **Compatible con puntuación existente** |
| Pendientes totales | Derivable por conservación si se conoce la entrada | Derivable por conservación si se conoce la entrada | Derivado de la salida; no localiza etapa |
| Esperando por etapa | No dispone de descomposición cola/servicio | No dispone de descomposición ni nombres físicos | **No admitido** |
| En servicio por etapa | No dispone de descomposición cola/servicio | No dispone de descomposición ni nombres físicos | **No admitido** |
| Stock total preparación/despacho | Tiene roles E1 nominales | Solo posiciones genéricas D1/D2/D3 | **M: coincidencia nominal condicional, no operador validado; D: no admitido** |
| Stock total entrega | C00 no tiene stock de entrega; C01 tiene *transit*, que no es automáticamente entrega | No tiene etapa física llamada entrega | **No admitido** |

Se documenta con estados de máquina `SUPPORTED_DIRECT_MODEL_OUTPUT`, `DERIVED_FROM_DELIVERED_NOT_INDEPENDENT`, `CONDITIONAL_ROLE_MATCH_NO_DES_OPERATOR` y `UNSUPPORTED_NO_VALID_OPERATOR`. La función `require_scoring_support` **rechaza explícitamente** cualquier sensor de etapa cuyo operador no esté justificado. No transformamos un stock matemático de D en un empleado/estación de preparación por el simple orden de la cadena.

En DES: `stage_stock = waiting + in_service`, y `aceptados = entregados + Σstage_stock`. Las mediciones están en pedidos; no representan inventario de ingredientes ni recursos humanos.

## 2. Selector cerrado antes de nuevos mundos

**Datos de entrenamiento:** archivo `02_DIAGNOSTICO_SENSORES.json` del <https://github.com/yudocyudoc/IGC/actions/runs/41162881478> (CAF-04), SHA-256 `d8a2cee6fbeb1e1a88cf4abe7a343a0b8a20ee8a38d89e4aa3e638384549902c`. La instantánea relevante quedó en `caf05_referencia_caf04_congelada.json`.

**Tasa y momento de entrenamiento fijos:** 1.5 pedidos/min, t10. Los tres mundos anteriores B/C/D tenían entregas 7/7/7, pero stock total de despacho B=1, C=6, D=2.

- Se compara un menú de 9 canales: waiting/in_service/stage_stock en cada una de tres etapas.
- Se selecciona el número **mínimo** de canales que separa B/C/D; empate de soluciones se resolvería lexicográficamente, **sin datos nuevos**.
- La elección reproducible es un único canal: `stage_stock:despacho`, observado en t10 a 1.5 pedidos/min.
- Prototipos de clasificación **congelados** por clase de cuello: preparación=1, despacho=6, entrega=2. La regla es distancia absoluta mínima; cualquier empate implica **ABSTAIN**. No se reajusta con I/J/K.
- Un segundo régimen de entrada 0.8 pedidos/min es **control fuera de dominio**; se registra la observación, pero no se ejecuta el clasificador condicionado en 1.5.

## 3. Tres mundos DES nuevos predeclarados

| Mundo | Cuello real | Preparación | Despacho | Entrega | Capacidad mínima |
|---|---|---|---|---|---|
| I | Preparación | 1 servidor × 4/5 min | 2 × 1 min | 2 × 1 min | 75/h |
| J | Despacho | 2 × 1 min | 1 × 4/5 min | 2 × 1 min | 75/h |
| K | Entrega | 2 × 1 min | 2 × 1 min | 1 × 4/5 min | 75/h |

Todos comparten pedidos homogéneos, stocks vacíos, servicio determinista, duración de llegada 20 min, sin abandonos ni cancelaciones. **Total: seis corridas DES nuevas** (tres mundos × dos presiones), con lecturas en t10. Una corrida por mundo/presión, sin búsqueda ni reintentos.

Los mundos I/J/K son **públicos, diseñados y no aleatorios**. El experimento aporta transferencia fuera de los casos B/C/D, pero no un testigo ciego ni una estimación poblacional de acierto.

## 4. Orden e indicadores de éxito/fallo

Antes del primer DES se guarda mediante escritura exclusiva y `fsync` el archivo `00_SENSOR_Y_MUNDOS_PREDECLARADOS.json`: sensor, prototipos, reglas, tres mundos, tasas y firma de la política original. A continuación se guardan el contrato `01_CONTRATO_OBSERVABILIDAD.json` y su checkpoint `01B_CHECKPOINT_ANTES_DE_DES.json`. Los tests interceptan las seis llamadas DES y verifican que esos archivos existan **antes** de observar las mediciones nuevas.

Después se informan:

- Número de valores distinguibles por el sensor, comparado con entregas totales bajo la presión emparejada.
- Resultado del clasificador congelado sobre I/J/K: correcto, erróneo o abstención, con todas las observaciones visibles.
- Bajo presión baja, número de valores físicos distintos del sensor, **sin extrapolar el clasificador**.
- Cumplimiento de conservación física y de correspondencia explícita de operadores M/D.
- Archivo de resultados y hashes locales: prueba de procedimiento de software, **no custodia externa**.

**No confundir:** distinguir tres clases conocidas por un solo sensor DES no implica inferir la arquitectura de cualquier empresa; para eso harían falta hipótesis, mecanismos de observación validados y un diseño de muestreo/perturbación distinto.

## Ejecución

```bash
python -m unittest discover -s experiments/cafeteria/pc02 \
  -p 'test_caf05_contrato_y_sensor.py' -v

python experiments/cafeteria/pc02/caf05_contrato_y_sensor.py \
  --out artifacts/caf05-contrato-y-transferencia
```

Los resultados de CI se publican como JSON, CSV, Markdown y ZIP. Una vez visto el resultado, **no se reescogen ni sensor ni prototipos en estos mundos**; cualquier cambio exigiría una prueba futura en mundos distintos, no reinterpretar esta corrida.
