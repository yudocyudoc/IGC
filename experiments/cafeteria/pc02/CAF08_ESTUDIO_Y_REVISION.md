# CAF-08 — Contraste entre aproximación fluida y DES de CAF-01

**Estado:** exploratorio y no validado. **Base:** PR #118, commit `5e2b5505a9224effe1b5242a3af61663b53aaa5d`. Este PR no toca ni fusiona #116–#118, D/M/Buffalo ni ATMS.

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

En este experimento se entrega deliberadamente la configuración real a **ambos simuladores** para compararlos. No es prueba ciega de recuperación de mecanismos, ni prueba de que un selector descubra una cuarta etapa.

## Resultados de referencia LOCALES, pendientes de ejecución nativa

| Cohorte | Comparaciones dentro del pulso | MAE entregas fluido ideal | MAE fluido retardado |
|---|---:|---:|---:|
| Cuello único | 9 | 3.5185 | 0.316 aproximado |
| Doble cuello nominal | 18 | 2.8056 | 0.436 aproximado |
| Etapa extra | 6 | 4.7778 | 0.259 aproximado |
| **Total** | **33** | **3.3586** | **0.371 aproximado** |

Para **44 observaciones**, incluida la medición tras el pulso a t=40, el MAE retardado fue **0.2783 pedidos**. El campo `lagged.mae` de la línea base contiene esa métrica, y `zero_lag.mae` únicamente las 33 observaciones durante el pulso. No confundir denominadores.

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

1. El DES original podría discrepar de la transcripción local usada para producir `CAF08_BASELINE_LOCAL.json`. La CI debe **fallar visiblemente** si ocurre; no recalibrar los valores para hacerla verde.
2. Las aproximaciones pueden coincidir por construcción en el régimen macroscópico sin coincidir en transitorios, ocupación o colas discretas.
3. Las capacidades efectivas iguales no necesariamente producen colas crecientes en todas las etapas: una etapa anterior puede dejar a otra sin presión suficiente.
4. Se comparan mundos construidos por nosotros y conocidos por ambos modelos; cero evidencia sobre causalidad de una cafetería real.
5. Los costos y factibilidad de aumentar capacidad **no fueron evaluados**; una modificación de servidor en la simulación no es una autorización operativa.

## Instrucción específica a revisores IA

Auditar el resultado sin asumirlo correcto. Revisar el contrato de `half_open_arrivals`, prioridades de eventos, tiempos de servicio, interpretación de colas vs en-servicio, conservación, discretización temporal y la alteración aislada de preparación. Proponer un par rival donde falle la regla fluida o una medición no discriminante; distinguir la **prueba de equivalencia del fluido ideal** de una declaración injustificada de identificabilidad global.

La CI verifica reproducción e integridad de la ejecución, no éxito científico. **No fusionar por el mero hecho de que los tests pasen.**
