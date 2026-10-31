# CAF-09: auditoría estática de clases supervivientes y confusibilidad

**Fuente:** GitHub Actions canónica [#41246972768](https://github.com/yudocyudoc/IGC/actions/runs/41246972768). **No se ejecutó DES:** solo se leyeron plan y 66 resultados.

**Alcance:** un paso condicional K2, presupuesto 8, tolerancia ±1; 11 mundos retrospectivos conocidos. No es validación externa.

## Cobertura de clase verdadera (solo mundos representados en catálogo)

| Banco | Política | Cubierta tras K1 | Cubierta al final | Clases únicas correctas | Fuera de taxonomía (excluidos) |
|---|---|---:|---:|---:|---:|
| single_only | STRICT_ORIGINAL | 3/3 | 3/3 | 1/3 | 8 |
| single_only | ANY_GUARANTEED | 3/3 | 3/3 | 2/3 | 8 |
| single_only | PAIRWISE_ANY | 3/3 | 3/3 | 2/3 | 8 |
| single_plus_dual | STRICT_ORIGINAL | 9/9 | 9/9 | 0/9 | 2 |
| single_plus_dual | ANY_GUARANTEED | 9/9 | 9/9 | 1/9 | 2 |
| single_plus_dual | PAIRWISE_ANY | 9/9 | 9/9 | 1/9 | 2 |

**9/9 con el banco ampliado no equivale a 9/9 diagnósticos**: contener una clase correcta entre seis rivales es cobertura, no identificación. No incluir mundos de cuarta etapa en denominador de cobertura de clase; su clase no existe en el catálogo.

## Supervivencia por mundo: banco ampliado (24)

Clases enumeradas con la nomenclatura original; el orden no indica prioridad.

| Mundo | Política | K1: n clases | K2: clases restantes | ¿Contiene clase verdadera? | Acción |
|---|---|---:|---|---|---|
| SINGLE_72_0 | STRICT_ORIGINAL | 6 | despacho, despacho+entrega, entrega, preparacion, preparacion+despacho, preparacion+entrega | sí | ninguna |
| SINGLE_88_1 | STRICT_ORIGINAL | 3 | despacho, entrega, preparacion | sí | ninguna |
| SINGLE_102_2 | STRICT_ORIGINAL | 6 | despacho, despacho+entrega, entrega, preparacion, preparacion+despacho, preparacion+entrega | sí | ninguna |
| DUAL_55_01 | STRICT_ORIGINAL | 6 | despacho, despacho+entrega, entrega, preparacion, preparacion+despacho, preparacion+entrega | sí | ninguna |
| DUAL_55_02 | STRICT_ORIGINAL | 6 | despacho, despacho+entrega, entrega, preparacion, preparacion+despacho, preparacion+entrega | sí | ninguna |
| DUAL_55_12 | STRICT_ORIGINAL | 6 | despacho, despacho+entrega, entrega, preparacion, preparacion+despacho, preparacion+entrega | sí | ninguna |
| DUAL_90_01 | STRICT_ORIGINAL | 6 | despacho, despacho+entrega, entrega, preparacion, preparacion+despacho, preparacion+entrega | sí | ninguna |
| DUAL_90_02 | STRICT_ORIGINAL | 6 | despacho, despacho+entrega, entrega, preparacion, preparacion+despacho, preparacion+entrega | sí | ninguna |
| DUAL_90_12 | STRICT_ORIGINAL | 6 | despacho, despacho+entrega, entrega, preparacion, preparacion+despacho, preparacion+entrega | sí | ninguna |
| UNKNOWN_EXTRA_70 | STRICT_ORIGINAL | 0 | ∅ | N/A: fuera de taxonomía | ninguna |
| UNKNOWN_EXTRA_100 | STRICT_ORIGINAL | 3 | despacho, entrega, preparacion | N/A: fuera de taxonomía | ninguna |
| SINGLE_72_0 | ANY_GUARANTEED | 6 | preparacion, preparacion+despacho, preparacion+entrega | sí | prep_dispatch_15_t20 |
| SINGLE_88_1 | ANY_GUARANTEED | 3 | despacho | sí | prep_dispatch_18_t20 |
| SINGLE_102_2 | ANY_GUARANTEED | 6 | despacho, despacho+entrega, entrega, preparacion, preparacion+despacho, preparacion+entrega | sí | ninguna |
| DUAL_55_01 | ANY_GUARANTEED | 6 | preparacion, preparacion+despacho, preparacion+entrega | sí | prep_dispatch_15_t20 |
| DUAL_55_02 | ANY_GUARANTEED | 6 | preparacion, preparacion+despacho, preparacion+entrega | sí | prep_dispatch_15_t20 |
| DUAL_55_12 | ANY_GUARANTEED | 6 | despacho, despacho+entrega | sí | prep_dispatch_15_t20 |
| DUAL_90_01 | ANY_GUARANTEED | 6 | despacho, despacho+entrega, entrega, preparacion, preparacion+despacho, preparacion+entrega | sí | ninguna |
| DUAL_90_02 | ANY_GUARANTEED | 6 | despacho, despacho+entrega, entrega, preparacion, preparacion+despacho, preparacion+entrega | sí | ninguna |
| DUAL_90_12 | ANY_GUARANTEED | 6 | despacho, despacho+entrega, entrega, preparacion, preparacion+despacho, preparacion+entrega | sí | ninguna |
| UNKNOWN_EXTRA_70 | ANY_GUARANTEED | 0 | ∅ | N/A: fuera de taxonomía | ninguna |
| UNKNOWN_EXTRA_100 | ANY_GUARANTEED | 3 | despacho, entrega, preparacion | N/A: fuera de taxonomía | prep_dispatch_18_t20 |
| SINGLE_72_0 | PAIRWISE_ANY | 6 | preparacion, preparacion+despacho, preparacion+entrega | sí | prep_dispatch_15_t20 |
| SINGLE_88_1 | PAIRWISE_ANY | 3 | despacho | sí | prep_dispatch_18_t20 |
| SINGLE_102_2 | PAIRWISE_ANY | 6 | despacho, despacho+entrega, entrega, preparacion, preparacion+despacho, preparacion+entrega | sí | prep_dispatch_18_t20 |
| DUAL_55_01 | PAIRWISE_ANY | 6 | preparacion, preparacion+despacho, preparacion+entrega | sí | prep_dispatch_15_t20 |
| DUAL_55_02 | PAIRWISE_ANY | 6 | preparacion, preparacion+despacho, preparacion+entrega | sí | prep_dispatch_15_t20 |
| DUAL_55_12 | PAIRWISE_ANY | 6 | despacho, despacho+entrega | sí | prep_dispatch_15_t20 |
| DUAL_90_01 | PAIRWISE_ANY | 6 | preparacion, preparacion+despacho, preparacion+entrega | sí | prep_dispatch_18_t20 |
| DUAL_90_02 | PAIRWISE_ANY | 6 | preparacion, preparacion+despacho, preparacion+entrega | sí | prep_dispatch_18_t20 |
| DUAL_90_12 | PAIRWISE_ANY | 6 | despacho, despacho+entrega | sí | prep_dispatch_18_t20 |
| UNKNOWN_EXTRA_70 | PAIRWISE_ANY | 0 | ∅ | N/A: fuera de taxonomía | ninguna |
| UNKNOWN_EXTRA_100 | PAIRWISE_ANY | 3 | despacho, entrega, preparacion | N/A: fuera de taxonomía | prep_dispatch_18_t20 |

## Confusibilidad robusta en todo el menú asequible

No existen **bloques de equivalencia bajo ±1** en general: la relación «los intervalos se superponen» no es transitiva. Para un solo canal, 0~2 y 2~4, pero 0 no~4. Se reporta un **grafo de pares incompatibles con garantía de separación**, no una partición.

| Mundo | Pares entre clases | Pares inseparables bajo todas las acciones |
|---|---:|---:|
| SINGLE_72_0 | 15 | 4 |
| SINGLE_88_1 | 12 | 5 |
| SINGLE_102_2 | 60 | 24 |
| DUAL_55_01 | 15 | 4 |
| DUAL_55_02 | 15 | 4 |
| DUAL_55_12 | 15 | 4 |
| DUAL_90_01 | 60 | 24 |
| DUAL_90_02 | 60 | 24 |
| DUAL_90_12 | 60 | 24 |
| UNKNOWN_EXTRA_70 | 0 | 0 |
| UNKNOWN_EXTRA_100 | 12 | 5 |

Un par de clases distintas con diferencias ≤2 en **todos** los canales y acciones asequibles impide garantizar que ese par sea distinguible **para todas** las observaciones posibles con errores ±1; una observación realizada puede sin embargo eliminar una de las hipótesis. Esto es un límite robusto local del menú, no equivalencia física general. Evaluar *todas* las acciones por separado no implica que puedan ejecutarse todas dentro del presupuesto total.

## Menú efectivo y diferencias entre compuertas

**single_only**
- STRICT_ORIGINAL: NO_MEASUREMENT=7, prep_dispatch_15_t20=4
- ANY_GUARANTEED: NO_MEASUREMENT=1, prep_dispatch_15_t20=4, prep_dispatch_18_t20=6
- PAIRWISE_ANY: NO_MEASUREMENT=1, prep_dispatch_15_t20=4, prep_dispatch_18_t20=6

**single_plus_dual**
- STRICT_ORIGINAL: NO_MEASUREMENT=11
- ANY_GUARANTEED: NO_MEASUREMENT=5, prep_dispatch_15_t20=4, prep_dispatch_18_t20=2
- PAIRWISE_ANY: NO_MEASUREMENT=1, prep_dispatch_15_t20=4, prep_dispatch_18_t20=6

## Lemas y cautelas

1. **Elegibilidad de una acción para ≥2 clases:** estricta ⇒ alguna hipótesis totalmente aislable ⇒ algún par de clases con bandas disjuntas. Se verificaron todas las opciones asequibles en el catálogo sin contraejemplo. **No implica** que la abstención final sea monótona si dos reglas eligen acciones distintas.
2. **Compuerta versus resultado:** distinguir pares en la tabla de predicciones no garantiza reducción de clases con la observación real. Una compuerta es posibilidad estructural; el veredicto depende del valor observado.
3. **Criterio de certificación** no cambia; cuando el banco omite cuellos dobles, una clase única de un catálogo incompleto puede ser falsa.
4. **Cobertura 9/9** se mide solo sobre clases estructurales representadas. No está garantizada con capacidades continuas o error de modelo. Las capacidades verdaderas de evaluación pueden no existir como puntos exactos en la cuadrícula de entrenamiento.
5. **Sin simulaciones nuevas ni ajuste de políticas**: la tabla se extrajo del JSON previo al recibir las revisiones, con resultados retrospectivos. No usarla como confirmación de una regla elegida después.

**Promotion gate:** BLOCKED_RETROSPECTIVE_NOT_STOCHASTIC.
