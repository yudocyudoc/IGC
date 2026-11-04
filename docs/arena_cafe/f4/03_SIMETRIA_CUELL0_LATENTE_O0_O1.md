# Arena IGC · F4 · Simetría estructural que oculta una restricción secundaria

**Fecha:** 2026-11-03 · **Plan rector:** cafetería v3.2, hipótesis rivales F4 y frontera hacia F5. **Estado:** testigo de **desarrollo con verdad sintética conocida**, no G4/G5, no análisis causal identificado por los productores. No reutiliza como «reserva independiente» la fuente histórica EV-01.

## Hallazgo: O0 + O1 tampoco garantizan identificación de toda la física

La pareja anterior de los PR #148–149 mostró que dos mecanismos construidos para O0 podían ser rechazados por el O1 de preparación. Eso no significa que O1 identifique todas las demás estaciones. En esta entrega se usa una **invariancia matemática del tándem FIFO**, sin otra malla de parámetros, para mostrar una clase de mecanismos que **sí preserva simultáneamente O0 y O1 del mundo sintético EV-01 original**, pero cambia la respuesta ante una perturbación física específica.

Se parte de la configuración **privada del evaluador EV-01** (`ev01.config()`), no de una estructura deducida por los brazos. Esto es una construcción consciente después de conocer la verdad sintética, y por eso **carece totalmente de independencia prospectiva**. El código de evaluación se ejecuta con acceso privado; el artefacto público solo contiene estadísticas y no divulga eventos completos por pedido ni el archivo de configuración a D/B/M.

| Estación | Mundo A (original EV-01) | Mundo B (mecanismo rival) |
|---|---|---|
| Caja | Dos servidores, 1 min/pedido | **Igual** |
| Preparación | Un servidor, **15/17 min/pedido** | **Igual** |
| Despacho | Un servidor, **30/43 min/pedido** | Un servidor, **3/11 min/pedido** |
| Transferencia final | Un servidor, **3/11 min/pedido** | Un servidor, **30/43 min/pedido** |

En ambos casos: las **15 entradas POS originales**, FIFO, capacidad física por estación, colas sin límite, sin abandonos ni bloqueo y estado inicial vacío. **No se busca ni optimiza ningún parámetro**: solo se **permutan dos servicios existentes** a partir de una simetría exacta. Son dos estructuras paramétricas distintas del evaluador, no dos hipótesis generadas de forma nativa por D, Buffalo o Moléculas.

### Por qué el resultado es exacto (no una coincidencia de seis números)

Sea una secuencia de arribos a una estación `A_1,…,A_n` y el operador FIFO de servidor único y servicio determinista constante `s>0`. Las salidas obedecen

\[
F_s(A)_i=\max_{1\le k\le i}\{A_k+(i-k+1)s\}.
\]

Para **dos estaciones consecutivas** de servidores únicos y tiempos `a,b>0`:

\[
F_b(F_a(A))_i
=\max_{k\le i}\left[
 A_k+\max\big\{(i-k+1)a+b,\ a+(i-k+1)b\big\}
\right].
\]

La expresión es simétrica en `a` y `b`; por tanto, **\(F_b\circ F_a=F_a\circ F_b\)**. La igualdad vale para cualquier calendario de entradas en este régimen físico, no solo para el pulso de quince pedidos. Los dos mecanismos tienen **todos los instantes terminales de entrega idénticos**; dos, cien o mil muestreos del mismo contador terminal no resuelven esta simetría.

La prueba depende de **servidor único, tiempos constantes, FIFO, colas ilimitadas y ausencia de bloqueo**. Si hay servidores múltiples, recursos compartidos, prioridades, retrabajos o bloqueo, **no** se puede extrapolar la identidad sin demostrarla de nuevo. No se afirma que esa simplificación describa un negocio real.

### Por qué O1 también es idéntico

Caja y preparación —las **dos primeras etapas del mundo EV-01**— son exactamente iguales en ambos mecanismos, y en este DES no existe bloqueo ni feedback aguas arriba. Por tanto, la secuencia de entrada a preparación, sus inicios y finales de servicio son iguales. El operador de observación O1 ya autorizado, sobre servicios de preparación **terminados antes de t=10**, arroja en ambos:

- **9 servicios completos**;
- duración media de servicio **15/17 minutos**;
- espera media de esos nueve servicios **1204/765 minutos**.

Esto coincide con el **O1 original**, no solo con un O1 inventado para cada mundo. Las seis entregas O0 coinciden también: **[0,0,2,4,6,8]** a t={0,2,4,6,8,10}. La conclusión para **este par conocido del evaluador** es: observaciones de terminales y preparación no bastan para determinar **cuál es la capacidad de despacho y cuál la de transferencia**.

No se debe confundir el resultado con **dos cuellos activos iniciales**: ambos tienen la misma restricción nominal de **preparación, 68 pedidos/h**; despacho y transferencia son más rápidos. Lo que permanece oculto es **la localización de una restricción secundaria potencial**, que puede activarse si cambia la operación.

## Una perturbación rompe la simetría

Experimento de desarrollo: **añadir treinta segundos de trabajo físico por pedido en despacho desde t=0** en ambos mecanismos, con el mismo calendario de llegadas y nuevos estados iniciales vacíos. Es un estrés selectivo para observar respuesta, por ejemplo una inspección manual adicional de tiempo constante; **no una recomendación comercial**. No se modifican las otras estaciones.

| Indicador al minuto 10 | Mundo A original | Mundo B permutado |
|---|---:|---:|
| Entregas sin intervención | 8 | 8 |
| Entregas con +30 s/pedido en despacho | **6** | **8** |
| Efecto respecto a línea base | **−2** | **0** |

El mismo estrés reduce la capacidad nominal de despacho A a aproximadamente **50 pedidos/h**, por debajo de la preparación (68/h); en B deja despacho alrededor de **78 pedidos/h**, todavía superior a la preparación. El cuello secundario **se activa solo en A**. La intervención no intenta mejorar ventas ni descubre por sí sola cuál mecanismo rige una cafetería desconocida; presenta una **predicción falsable distinta si se consiguiera una prueba independiente y segura**.

### Implicaciones para la minería de procesos

Los dos mundos siguen exactamente la misma **ruta estructural** caja→preparación→despacho→transferencia; un DFG de actividades sin información temporal adicional no distingue su física. Si una instrumentación FULL registra los servicios reales de despacho/transferencia, **B1 ya posee las duraciones necesarias para distinguirlos**, sin atribuir esa información nueva a P. La pregunta de valor incremental de minería sigue **condicional**: ¿puede P encontrar una regularidad procesual no recuperada suficientemente por B1/B2 bajo los **mismos registros y sensores**? Aquí no hemos demostrado que sí.

## Ejecución reproducible, custodia y límite

```bash
python -m scripts.arena_cafe.f4_latent_downstream_symmetry \
  --o0 artifacts/public/O0_VISIBLE.json \
  --o1 artifacts/public/O1_VISIBLE.json \
  --out artifacts/F4_LATENT_SYMMETRY_DEVELOPMENT.json
```

El módulo es **evaluador-only** e importa `ev01.config()` directamente; jamás se distribuye la configuración o los eventos individuales por pedido a un brazo. El **motor DES es exactamente el existente**, y el verificador adicional es la recurrencia algebraica de servicio, no otro motor de búsqueda. La CI reutiliza las copias públicas congeladas O0/O1; las pruebas comprueban la paridad de las **15 salidas terminales exactas**, la coincidencia de medias y conteos O1, conservación y respuesta a estrés, más entradas adulteradas y prohibición de promesas de G4/G5.

Este testigo sirve para fundamentar una mejor pregunta de identificabilidad: **no solo si un cuello es visible hoy, sino qué restricción latente podría aparecer ante un cambio de campo**. No permite recomendar agregar/quitar estaciones, ni elegir sensores óptimos, ni afirmar que un algoritmo de los tres brazos reconstruya esa distinción.

**Estado:** `A3=PARTIAL` (método Buffalo aún sin inferencia auténtica autorizada en EV-01); `F5_independent_reserve=NOT_CREATED`; `G4/G5=NOT_RUN`; valor incremental de PM **no demostrado**. La clase de ambigüedad fue construida **con la verdad EV-01 conocida**, por lo que toda evaluación futura deberá usar mundos nuevos y condiciones aisladas. No se ejecutó PM4Py, un proveedor ni OpenModelica y no se introdujo malla.
