# Arena IGC · G3 de construcción con EV-01 conocido

**Fecha:** 2026-11-03. **Base:** PR #144 `069d2ad00ba646131ca969fa9aca55c5d5b38e23`.  
**Código:** `scripts/arena_cafe/g3_construction.py`. **CI:** `arena-cafe-g3-construction.yml`.

## Decisión ejecutada

Este incremento distingue tres cosas que antes se mezclaban:

- **G2, ingeniería:** los seis D y seis AST M ya simularon y conservaron materia; esos recibos permanecen intactos.
- **G3, construcción:** el EV-01 público O0 **ya conocido** puede servir para diagnóstico descriptivo contra las entregas acumuladas, pero nunca para una prueba ciega o un ranking de descubrimiento causal.
- **G4/G5:** pronósticos y contrastes posteriores. Ambos permanecen `NOT_RUN`. Ningún mundo nuevo ni reserva es requisito para calcular un diagnóstico de construcción.

Se omite R6 como trabajo en este incremento. No se ejecuta provider, DES ni OpenModelica nuevo, no se altera ningún motor original ni se fusiona con `main`.

## H_j operativo: correspondencia condicional, no causalidad

Se contrastan entregas acumuladas por pedido `pedido_entregado`, observadas estrictamente antes de `t={2,4,6,8,10}` minutos:

- **D:** stock `delivered`, tiempo en minutos, unidad de cantidad pedidos.
- **M:** `DeliveryCounter.total` que el backend expone como `deliveredTotal`, tiempo original en horas, convertido a minutos; la equivalencia `Order → ReadyOrder → Shipment → entrega` es **uno a uno condicional**.
- **B:** sin H_j operativo hasta generación EV-01 original real; ningún proveedor se invoca aquí.

Un conteo POS discreto contra una trayectoria continua mide **desajuste de acumulados**, no que los modelos originen los mismos eventos o mecanismos. Las llegadas son entrada conocida de reproducción condicional offline; no son pronóstico. `orders_created - delivered`, `inTransit` y `reportedDeliveryRate` no son puntuados como WIP o entrega física. Preparación O1, tiempos medios y `responseTime` no se identifican mediante una equivalencia asumida.

## M · imposibilidad analítica de los priors fijos

Se lee el `registry.base.json` original y se enumeran los **seis** AST. Se comprueba la ley original `maxFlow=maxThroughput`, los stocks iniciales cero y el contador inicial cero; se determina la capacidad mínima de la cadena material de cada AST. Preparación y despacho tienen `maxThroughput=20 pedidos/h`.

Por ello, para los seis grafos:

`entregas(10 min) <= 20 × 10/60 = 10/3 pedidos`.

Las observaciones O0 reportan 8 entregas a 10 min. La salida `M_FIXED_PRIOR_INCOMPATIBLE_WITH_O0_DELIVERIES` por cada AST es un **resultado analítico negativo de adecuación del prior a ese objetivo**, no refuta al compositor ni exige alterar el registro. Para llegar a ocho se necesita al menos 48 pedidos/h de capacidad terminal, **y normalmente más** por retardos y condiciones iniciales. No se calcula RMSE M ni se convierte la cota en selección.

## D · calibración externa exploratoria, no D nativo

El usuario puede activar `--d-external-grid` para una evaluación de **representabilidad**, no de inferencia autónoma. Se conserva la gramática original 1/2/3 stocks × con/sin pérdida; las seis alternativas participan y ninguna se descarta antes del ensayo.

- Se usa el input causal de RF-02T `w=0.5 min` con masa posterior al corte diferida.
- Para cada candidato se integra **fuera de D** la misma forma de las ecuaciones de su renderer original (flujo `min(capacity, max(0, stock / response_time))`, pérdidas desde primer stock si aplica) mediante RK4, separando pasos en discontinuidades del input.
- Malla declarada (unidades en min y pedidos/min): `capacity={0.8,1.2,1.8,2.7,4.0}`, `response_time={0.15,0.35,0.7,1.4,2.7}`, `loss_time={0.5,1.5,4.0,8.1,20.0}` para modelos con pérdida. En modelos sin pérdida `loss_time` no interviene y se etiqueta `INACTIVE`.
- Salida: MAE de cinco observaciones, residuos en cada tiempo, parámetros del mínimo **dentro de la malla** y rangos descriptivos de los puntos con `MAE <= mejor + 0.25 pedidos`. Este conjunto cercano al mínimo **no es intervalo de confianza ni conjunto de parámetros identificados**; la malla es deliberadamente pequeña y los resultados pueden depender de sus límites.
- El uso de O0 y la propuesta de métrica son retrospectivos y declarados `POST_HOC_EXPLORATORY`. No hay umbral de `G3 PASS`, ranking científico entre métodos ni supuesta selección D nativa.
- El integrador es **espejo numérico externo**, no OpenModelica ni el estimador original D (que no existe). El test de CI contrasta sus seis salidas bajo el fixture anterior con los seis CSV OpenModelica congelados; conformidad en esos puntos no equivale a validación universal del integrador ni del ajuste de nuevos parámetros.

**Importante:** la política genérica `SCORE_G3` del PR #144 sigue denegada para evaluaciones privilegiadas. Este incremento solo produce el informe especializado, explícitamente descriptivo y acotado al O0 público; **no desbloquea** una adjudicación general ni un `G3=PASS` científico.

## Uso reproducible

```bash
python -m scripts.arena_cafe.g3_construction \
  --visible artifacts/public/O0_VISIBLE.json \
  --out artifacts/G3_CONSTRUCTION_ANALYTICAL.json

python -m scripts.arena_cafe.g3_construction \
  --visible artifacts/public/O0_VISIBLE.json \
  --d-external-grid \
  --out artifacts/G3_CONSTRUCTION_D_EXTERNAL_GRID.json
```

La CI lee el artefacto público A1 y las seis trazas OMC G2 D existentes, sin generar un nuevo DES ni realizar llamadas a modelos. Los tests comprueban conservación, no negatividad, convergencia de paso, las seis estructuras, incoherencia del prior M y deriva respecto del solver anterior. Los resultados se publican como artefacto de ingeniería/metodología, **no como certificado de adecuación científica**.

## Límites y pendientes

- M mantiene priors originales; no calibrar M oportunistamente ni compararlo con D ajustado como si fueran métodos simétricos.
- La integral del input rectangular es una aproximación exógena no medida; ensayos de sensibilidad de anchura requieren reportes separados, nunca escoger ancho por mejor puntuación post hoc.
- La aproximación RK4 externa no sustituye ejecuciones nativas OpenModelica nuevas si se exige confirmación de parámetros hallados.
- Buffalo no tiene nueva inferencia EV-01.
- La pregunta que ahora se puede explorar: **¿qué estructuras D logran aproximar las salidas conocidas bajo ajustes externos, con qué sensibilidad y con cuánta no-identificabilidad?** No es «¿cuál descubrió la verdad?».

**Estado:** A3 `PARTIAL`; diagnóstico G3 de construcción acotado, sin `PASS` de método; G4/G5 `NOT_RUN`; no ranking científico ni invocación de proveedor.
