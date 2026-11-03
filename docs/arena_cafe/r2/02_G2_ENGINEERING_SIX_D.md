# RF-02G — Seis D-B en OpenModelica: G2 de ingeniería

**Continuación del RFC R2 y PR #140.** Esta entrega prueba el ejecutor y la conservación de masa de la gramática D original bajo la señal POS causal. No permite seleccionar parámetros de cafetería, elegir topología, recuperar mecanismos ocultos ni reclamar G3.

## Alcance y material

- Motor original: scripts/arena_d_v01.py, no modificado.
- Fuente pública: quince creaciones de pedidos POS observadas antes del cutoff de 10 minutos, artefacto congelado de A1 run 41575917332.
- Orquestador nuevo: scripts/arena_cafe/r2_causal_g2.py.
- Seis modelos: 1, 2 y 3 stocks, cada uno con/sin pérdida; ninguna estructura se descarta.
- Se usa solo O0 para no repetir simulaciones con la misma señal de llegadas O1; la evidencia física adicional de O1 no se emplea aquí.
- Se ejecuta una sola instancia de OpenModelica v1.26.5-minimal, con seis solicitudes internas y seis archivos CSV separados.

## Fixture numérico — jamás estimación de EV-01

Archivo de prueba: tests/fixtures/rf02_g2_fixture_nominals.json.

| Parámetro original D | Valor | Unidad |
|---|---:|---|
| capacity | 1.23 | pedidos/minuto |
| response_time | 2.7 | minutos |
| loss_time | 8.1 | minutos |

Los tres son **supuestos no empíricos, elegidos únicamente para validar compilación y conservación**. No están inferidos de POS, DES ni E1. Las seis estructuras comparten el mismo vector de fixture; ni el RMSE frente a entregas reales ni el ranking se calculan.

## Invariante formal de G2

Para cada muestra t de cada CSV original del solver:

    suma_stocks(t) + delivered(t) + lost(t) = integral_0^t(u_causal(s) ds)

La integral es de la **señal efectivamente suministrada**: calcula con fracciones racionales la fracción real inyectada hasta t y mantiene **masa diferida después del cutoff**. Nunca fuerza que todo el total de pedidos POS haya ingresado a la ODE antes de t=10. Para estructuras sin pérdida, lost(t) permanece cero; para las que la permiten, cuenta como sumidero material y no como WIP.

Antes de ejecutar se fija la tolerancia de ingeniería **0.08 pedidos** (la ya utilizada en A1). Si la conservación, continuidad, no negatividad, monotonicidad de entregas/pérdidas o completitud 0–10 min no se cumple, G2 técnico = FAIL; no se ajusta el umbral retrospectivamente.

El auditor exige: existencia y hashes de todos los modelos, script de simulación, marcador de llamada auténtica al solver, exit code 0, seis CSV con volumen mínimo y muestras válidas. Esta no es una prueba contra la respuesta física del DES.

## Límites del veredicto

Solo puede decirse **G2=PASS_REAL_OMC_ENGINEERING_ONLY** cuando se verifican los seis archivos reales. En cualquier caso se conservan G3/G4/G5=NOT_RUN, A3=PARTIAL, scientific_adequacy=NOT_ESTABLISHED, selection_actor=NONE y provider_calls=0. Una eventual falla se conserva como hallazgo; no se arregla con nuevas hipótesis construidas desde el resultado.

**Ninguna revisión de Astra es requisito para cada incremento de implementación.** Se reserva la revisión independiente para cerrar un hito científico posterior: parámetros defendibles, operador observacional y G3. El motor original, los métodos hermanos, el holdout y Cloudflare permanecen intactos.
