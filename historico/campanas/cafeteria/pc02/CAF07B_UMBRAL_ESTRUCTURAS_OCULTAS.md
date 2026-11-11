# CAF-07B — Umbral de decisión, presupuesto acumulado y estructura desconocida

**Fecha:** 2026-10-31. **Clasificación:** estudio DES público exploratorio. PR #116 (CAF-07) y PR #117 (CAF-07A) quedan intactos. Esta revisión se construye explícitamente **conociendo** los resultados anteriores y no es validación prospectiva independiente.

## Preguntas

1. ¿Puede una regla operativa elegir sin inventar un tipo de cambio entre dinero y número de pares separados?
2. ¿Cómo cambia un diagnóstico cuando el banco ya contempla **dos cuellos nominales simultáneos**?
3. ¿Qué ocurre si existe una **cuarta etapa no revelada al selector**, en lugar de rechazarla leyendo la configuración verdadera?
4. ¿Se puede ejecutar realmente una segunda observación condicional respetando el presupuesto **acumulado**?

## Contratos y decisión

**Banco A:** 12 hipótesis físicas DES existentes (cuello único en preparación, despacho o entrega; capacidades 60/75/90/105 pedidos/h).

**Banco B:** las mismas 12 más otras 12 hipótesis físicas con dos etapas de igual capacidad nominal, en las tres combinaciones preparación–despacho, preparación–entrega y despacho–entrega para cada capacidad 60/75/90/105/h. Un cuello nominal doble **no significa** dos colas creciendo a la vez; una etapa aguas arriba puede privar de trabajo a la siguiente.

Los dos bancos son **hipótesis auxiliares DES**, no familias M/D. Sus operadores físicos son explícitos; M/D continúan sin estar autorizados a asimilar stocks DES por igualdad de nombres. La clase de decisión es una etapa o, en B, un par de etapas.

**Umbral normativo de laboratorio:** mínimo **una hipótesis garantizadamente resuelta de cada clase superviviente**. Para cada hipótesis, una decisión está garantizada solo si **toda** observación entera posible dentro de ±1 pedido queda incompatible con cualquier hipótesis de clase distinta. Equivalente exacto para bandas rectangulares: para todo rival de otra clase debe haber algún canal con diferencia mayor que 2 pedidos. Este requisito es deliberadamente un **mínimo experimental, no un umbral de seguridad de negocio validado**. Un catálogo más fino cambia su significado; no se interpretará como probabilidad.

**Selección corregida:** si hay varias clases, elegir la medición **de menor costo ilustrativo** que alcance el umbral en todas, sin restar costo de ganancia informativa. Si ninguna satisface el requisito dentro del saldo, devolver `REQUIREMENT_NOT_MET`. Si no hay hipótesis compatibles, `MODEL_GAP`. Si ya hay una clase única, detenerse, rotulando el resultado **solo dentro del banco**; nunca declarar validación de la realidad.

## Dos mediciones verdaderamente condicionadas

- **Observación inicial K0:** entregas a 1.2/min, minuto 10 (sin costo presupuestado, como en CAF-07).
- **Primera acción fija:** entregas acumuladas a 1.5/min, minuto 20, costo ilustrativo 1. No la llamamos elección óptima; es un sondeo económico predefinido.
- **Segunda acción adaptativa:** después de conocer la primera lectura, actualizar candidatos y seleccionar una medida de menor costo que satisfaga el umbral, **saldo total ≤7**. Si no existe, no se simula. Se guarda la selección en disco **antes** del segundo DES.
- Cada prueba es una corrida DES independiente que reinicia pedidos y recibe una presión de entrada predeclara. No implica mover la demanda en una empresa real sin validar sus efectos y riesgos.

## Evaluación: once escenarios físicos, dos bancos

| Tipo físico | Configuraciones | Conocimiento del evaluador |
|---|---|---|
| Un cuello | Preparación 72/h, despacho 88/h, entrega 102/h | Clase real conocida solo para evaluar |
| Dos cuellos nominales | 55/h y 90/h × las tres combinaciones de etapas | **Seis controles negativos** de diagnóstico único |
| Cuatro etapas | Dos mundos, con cuello extra oculto aguas abajo a 70/h y 100/h | **No** se entrega al selector que hay cuatro etapas |

La observación de cuatro etapas sigue siendo físicamente consistente: se conserva masa entre aceptaciones, entregas finales y **stocks de las cuatro etapas** en el evaluador. El selector solo ve entrega final y, si procede, sensores etiquetados de las tres primeras etapas. Su algoritmo NO recibe la configuración ni comprueba `len(stages)`: no puede reclamar detectar lo desconocido por lectura de parámetros privilegiados.

Se compara el banco A contra el banco B bajo la misma política: **22 evaluaciones de dos o tres corridas DES cada una**. No hay una tasa de error independiente ni generalizable. Se cuentan por separado aciertos, errores, falsas declaraciones de cuello único, abstenciones y brechas de modelo. Una doble restricción adjudicada a una única etapa es un **falso diagnóstico único**, aunque el filtro sea internamente puro. Si resulta falso en controles, queda como una **falla experimental**, no se corrige ni se oculta ajustando hipótesis.

## Integridad y condiciones de no promoción

La CI suministra el SHA exacto de **su propio checkout** mediante `--source-commit "$GITHUB_SHA"`, que el proceso inscribe en el plan antes de las evaluaciones. El SHA de Git identifica una revisión del código; **no proporciona por sí solo custodia externa, pre-registro independiente ni cegamiento real**.

Antes del primer DES de evaluación se registran y escriben exclusivamente con `fsync` ambos bancos físicos, sus predicciones, los once escenarios, el umbral y el presupuesto. El segundo paso se escribe individualmente tras observar la primera respuesta y antes de ejecutar la segunda. Fallos del motor quedan visibles, sin reintentos y sin sobrescritura de resultados.

**La CI verifica ejecución e integridad, no suficiencia científica. **Se exige además cobertura diagnóstica mínima separada de la tasa de error: al menos un diagnóstico correcto por cada tipo de estructura (único y doble) para que la evaluación sea informativa. Si no hay cobertura, `promotion_gate=BLOCKED_NO_DIAGNOSTIC_COVERAGE` aunque los falsos positivos sean cero.**** El reporte incorpora `negative_controls_zero_false_single_expanded`, pero **nunca** marca `deployment_validated=true` por pasar tests o por superar estos controles.

Este estudio no incluye incertidumbre estocástica calibrada, selección óptima de primera prueba, utilidades empresariales reales, validación independiente, topologías arbitrarias, mecanismos de feedback SD o el enlace con ATMS. No extrapolar su cobertura limitada a operaciones reales.

## Ejecución

```bash
python -m unittest discover -s experiments/cafeteria/pc02 -p 'test_caf07b_umbral_secuencial.py' -v
python experiments/cafeteria/pc02/caf07b_umbral_secuencial.py \
  --out artifacts/caf07b-evidencia --source-commit "$(git rev-parse HEAD)"
```

**Próximo paso condicionado por hallazgos:** no ajustar CAF-07B a sus propios controles. Cualquier nueva tolerancia, requisito de calidad o catálogo estructural deberá evaluarse con nuevos escenarios y un plan registrado fuera de la misma ejecución.
