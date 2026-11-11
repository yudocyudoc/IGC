# CAF-08 — Prueba de consistencia numérica entre fluido y DES de CAF-01

**Estado:** consistencia técnica reproducida en GitHub Actions; inferencia causal y selector NO validados. **Base:** PR #118, commit `5e2b5505a9224effe1b5242a3af61663b53aaa5d`. Este PR no toca ni fusiona #116–#118, D/M/Buffalo ni ATMS.

## Pregunta

¿La aproximación de cola fluida explica la equivalencia observacional de un cuello único y dos cuellos nominales, y permite formular una intervención discriminante sin migrar del motor DES?

## Artefactos para revisión de otras IA

- `caf08_fluid_des_pilot.py`: generador de **11 mundos**, cuatro lecturas por mundo (44 comparaciones), fluido ideal, fluido retardado y ejecución del **motor original** `experiments.cafeteria.pc01.caf01_des_engine`. No hay copia local del DES en el PR.
- `test_caf08_fluid_des_pilot.py`: seis pruebas que incluyen control de importación nativa, equivalencia pasiva, intervención, conservación, refinamiento temporal y comparación con referencia local congelada.
- `CAF08_BASELINE_LOCAL.json`: resumen de la ejecución local anterior, marcado como no verificado en el checkout GitHub.
- `.github/workflows/caf08-fluid-des-review.yml`: reproduce las pruebas en GitHub Actions y publica `caf08_full_results.json` como artefacto descargable para auditoría externa.

**Reproducción desde la raíz del repositorio:**

```bash
python -m unittest discover -s experiments/cafeteria/pc02 -p 'test_caf08_fluid_des_pilot.py' -v
python -m experiments.cafeteria.pc02.caf08_fluid_des_pilot --out artifacts/caf08_full_results.json
```

Solo Python estándar; requiere el DES versionado por el propio repositorio.

## Fundamento matemático y límite

Si los buffers parten vacíos, la entrada es constante `lambda`, las capacidades constantes `mu_i` y se omiten tiempos de residencia, la entrada efectiva a la etapa i es `min(lambda, mu_1, ..., mu_(i-1))` y la cola inicialmente crece a `max(0, entrada_i - mu_i)`. La salida ideal es `min(lambda, mu_1, ..., mu_n)`.

**No es la ecuación general de drenaje.** Con cola previa o cuando acaba el pulso, es necesario conservar los estados. El segundo fluido incorpora retrasos de servicio mediante integración numérica `dt=0.005` min; tampoco es un modelo analítico cerrado, ni tiene pedidos discretos o servidores individuales como el DES.

En este experimento se entrega deliberadamente la configuración real a **ambos simuladores** para compararlos, incluidos los **mismos tiempos de servicio** proporcionados por `des.validate_private_config(config)`. El fluido retardado es otra **implementación numérica de la misma especificación física**, no un modelo de mecanismo independiente. No es prueba ciega de recuperación de mecanismos, ni prueba de que un selector descubra una cuarta etapa.

## Resultados nativos reproducidos en GitHub Actions (no validación física)

| Cohorte | Comparaciones dentro del pulso | MAE entregas fluido ideal | MAE fluido retardado |
|---|---:|---:|---:|
| Cuello único | 9 | 3.5185 | 0.316 aproximado |
| Doble cuello nominal | 18 | 2.8056 | 0.436 aproximado |
| Etapa extra | 6 | 4.7778 | 0.259 aproximado |
| **Total** | **33** | **3.3586** | **0.3711** |

Para **44 observaciones**, incluida la medición tras el pulso a t=40, el MAE retardado fue **0.2783 pedidos**. Las **11 mediciones de entregas acumuladas en t=40 tienen error exactamente 0**, lo que reduce artificialmente el MAE global respecto del período informativo. El MAE principal es **0.3711** dentro del pulso (33 lecturas; máximo absoluto 0.5833 pedidos). Nunca mezclar denominadores.

**Convención del error firmado:** siempre `DES - FLUIDO`; el sesgo -3.3586 del fluido sin retardo significa que el fluido sobreestima entregas. El MAE nunca tiene signo.

**Procedencia nativa verificada:** [workflow GitHub Actions #41244317160](https://github.com/yudocyudoc/IGC/actions/runs/41244317160), SHA evaluado `265b5c1cbb7606e1ebf8364af8c7625d1e6b1b61`; seis pruebas completadas satisfactoriamente, incluyendo el test que contrasta MAE con la referencia local congelada. [Artifact completo de las 44 observaciones](https://github.com/yudocyudoc/IGC/actions/runs/41244317160/artifacts/13058324246), SHA256 interno `caec69fa701133434e005299dde465611103b93404e90f711242736fa96d2791`. El artefacto caduca; el código y tests permanecen versionados. **Esta CI es anterior a las aclaraciones de revisión metodológica posteriores: revisar el nuevo run para confirmar las pruebas añadidas.**

### Par indistinguible bajo el repertorio pasivo

- Mundo A: preparación 75/h; despacho y entrega 120/h.
- Mundo B: preparación y despacho 75/h; entrega 120/h.
- A 90 pedidos/h durante 20 minutos: **22 entregas** y cola `[5,0,0]` en ambos DES; fluido sin retardo, **25 entregas** y cola equivalente.

Estas observaciones **no** identifican las capacidades distintas de despacho, pero no prueban equivalencia universal.

### Intervención discriminante

Cambiar **solo preparación** de 75 a 105 pedidos/h, manteniendo iguales las otras capacidades:

| Lectura DES | A | B |
|---|---:|---:|
| Antes, minuto 20 | 22 | 22 |
| Después, minuto 20 | 26 | 22 |
| Después, cola despacho minuto 20 | 0 | 5 |
| Después, minuto 40 | 30 | 30 |

La intervención genera una diferencia en los 20 minutos, pero las entregas acumuladas coinciden una vez drenados todos los pedidos en el minuto 40. El momento y el tipo de observación son parte del experimento.

## Riesgos y falsadores

1. La ejecución nativa reproducida coincide con la línea base local congelada en los dos MAE principales. La prueba posterior a la revisión agrega el MAE intra-pulso y la comprobación del signo. No reajustar valores para hacer pasar CI.
2. Las aproximaciones pueden coincidir por construcción en el régimen macroscópico sin coincidir en transitorios, ocupación o colas discretas.
3. Las capacidades efectivas iguales no necesariamente producen colas crecientes en todas las etapas: una etapa anterior puede dejar a otra sin presión suficiente.
4. Se comparan mundos construidos por nosotros y conocidos por ambos modelos; cero evidencia sobre causalidad de una cafetería real.
5. Los costos y factibilidad de aumentar capacidad **no fueron evaluados**; una modificación de servidor en la simulación no es una autorización operativa.

## Instrucción específica a revisores IA

Auditar el resultado sin asumirlo correcto. Revisar el contrato de `half_open_arrivals`, prioridades de eventos, tiempos de servicio, interpretación de colas vs en-servicio, conservación, discretización temporal y la alteración aislada de preparación. Proponer un par rival donde falle la regla fluida o una medición no discriminante; distinguir la **prueba de equivalencia del fluido ideal** de una declaración injustificada de identificabilidad global.

La CI verifica reproducción e integridad de la ejecución, no éxito científico. **No fusionar por el mero hecho de que los tests pasen.**

## Revisión adversativa del 31 de octubre: observables, identificabilidad y límites

**Crítica recibida de Claude.** Esta prueba es de **consistencia de implementación**, no evidencia externa ni resolución del selector de CAF-07B (#118). En particular:

- La equivalencia de los mundos A/B solo vale para **lecturas de entregas acumuladas y colas** en los instantes y presiones establecidos. Con otro canal o frecuencia puede desaparecer.
- **Marcas de tiempo por etapa** son un candidato prioritario de observación menos invasiva. Según la regla física de CAF-07B, el tiempo mínimo de servicio sin espera de un pedido es A: `0.8 + 1 + 1 = 2.8 min`; B: `0.8 + 0.8 + 1 = 2.6 min`. Esa diferencia de 0.2 min (12 segundos) podría identificarse en trazas por pedido si hay suficiente resolución, eventos atribuibles y acceso legítimo. **No está medida** en CAF-08 ni expuesta por la API pública de observación de CAF-01: requiere una instrumentación verificable y pruebas con timestamps, además de manejar tiempos de espera.
- Las entregas acumuladas en t=40 pierden la distinción **de la intervención examinada** porque se terminó de drenar el pulso; no implica que todas las observaciones tardías sean inútiles.
- Aumentar preparación de 75 a 105/h sirve como **contrafactual DES**, no recomendación de inversión ni costo/beneficio de una pyme.
- El selector de #118 no se ejecutó con banco fluido: esta prueba **no resuelve** `BLOCKED_NO_DIAGNOSTIC_COVERAGE`. Tampoco calibra una tolerancia estadística. El error de aproximación numérica DES–fluido no puede sustituir por sí solo la resolución del sensor ni la incertidumbre de datos reales.

### Secuencia propuesta, con pruebas separadas

1. **Selector + banco fluido retardado:** conservar la política, presupuesto y 11 mundos DES de #118; reemplazar solamente las curvas predictivas candidatas. Reportar veredictos por estructura, abstenciones, brechas, falsos cuellos únicos y cobertura, sin retocar tolerancia usando los mundos evaluados. Separar resultados de comparación estructural y de política de selección.
2. **Observación por timestamps:** primero introducir de forma auditable lecturas de inicio/fin por etapa o duración por pedido sin pasar configuraciones privadas al selector. Comprobar que cada observación realmente diferencia mundos A/B y medir la separación en minutos, con precisión/resolución explícitas.
3. **Tolerancia:** comparar discrepancia determinista de modelo contra **resolución instrumental** y variabilidad experimental cuando existan; evitar deducir una tolerancia universal solo a partir del MAE o fijarla tras ver el gold.

**No autoriza fusionar ni promocionar.** Mantener CAF-08 como referencia auditable hasta que una revisión independiente adjudique el nuevo objetivo experimental.
