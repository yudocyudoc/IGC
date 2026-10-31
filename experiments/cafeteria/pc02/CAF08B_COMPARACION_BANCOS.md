# CAF-08B — Selector de CAF-07B con banco fluido retardado (comparación controlada)

**Estado:** protocolo exploratorio retrospectivo; sin validación física, diagnóstica ni comercial.
**Dependencia:** PR #119 (fluido y motor DES nativo); este PR se apila sobre esa rama en lugar de copiar el archivo. **Antecedente:** PR #118 (CAF-07B, fusionado). No modifica sus archivos.

## Pregunta

Bajo **los mismos 11 mundos DES**, mismo menú de mediciones, primera prueba, presupuesto acumulado, umbral por clase, tolerancia ±1 y funciones de selección de CAF-07B, ¿cambian los diagnósticos cuando el banco predictivo del selector procede del fluido retardado en lugar del DES?

No pretende determinar la estructura física real ni el mejor algoritmo de identificación. Los once mundos ya se han visto en #118 y en #119: no son mundos reservados nuevos.

## Dos brazos con política idéntica

| Dimensión | Referencia | Comparador |
|---|---|---|
| Mundo de evaluación | DES de CAF-01 | **El mismo DES** |
| Bancos de hipótesis | CAF-07B (12 / 24) | **Las mismas configuraciones** |
| Predicciones del banco | CAF-07B `precompute()` → DES | `delayed_fluid()` de #119 |
| Operadores de observación | entregas, colas, stock de etapa | **Los mismos operadores y canales** |
| Interfaz del selector | conteos enteros | masa fluida cuantizada a enteros |
| Primera medición | fija, entregas 1.5/min t=20 | Igual |
| Segunda medición | `choose_second()` original | **La misma función original** |
| Tolerancia y presupuesto | ±1, presupuesto 8 | **Sin cambios** |
| Veredictos | `evaluate_case()` de CAF-07B | **La misma función original** |

**Adaptador obligatorio:** el fluido devuelve números reales. Antes de entrar al selector se aplica **redondeo al entero más cercano, con 0.5 hacia arriba** (`floor(max(0,x)+0.5)`). No se calibró ni seleccionó con nuevos mundos y **no** equivale a medir el error instrumental. Su efecto es una limitación explícita: una comparación adicional con truncamiento o intervalos podría producir resultados distintos, pero no se mezcla ahora.

**Advertencia sobre las clases:** “cuello nominal doble” significa capacidad nominal mínima compartida; no dos colas necesariamente creciendo.

## Reproducibilidad auditable

Desde la raíz del checkout de este PR y con Python 3.12, sin paquetes nuevos:

```bash
python -m unittest discover -s experiments/cafeteria/pc02 -p 'test_caf08b_selector_fluid_bank.py' -v
python experiments/cafeteria/pc02/caf08b_selector_fluid_bank.py \
  --out artifacts/caf08b-comparison --source-commit "$(git rev-parse HEAD)"
```

CI adjunta captura checkout SHA, plan con predicciones DES y fluidas **antes de simular mundos de evaluación**, todas las selecciones de segunda prueba **antes del DES de esa segunda prueba**, resultados por mundo y por tipo, informe legible, y manifiesto SHA256. No implica custodia externa o cegamiento verdadero. Las llamadas DES de precomputación del banco son previas al plan; los escenarios de evaluación, no.

**Artifacts de salida:**
- `00_PLAN_ANTES_DE_EVALUAR.json`: configuraciones, catálogo, predicciones, política y plan.
- `01_CHOICE_...json`: selección por mundo/brazo, antes de segunda observación.
- `01_RESULTADOS.json`: 44 evaluaciones emparejadas (11 mundos × 2 bancos × 2 motores), 22 comparaciones, contadores por clase, discrepancias de predicción.
- `02_INFORME.md`: veredictos por clase y discrepancias.
- `03_MANIFIESTO.json`: SHA256 de archivos, SHA de checkout.

## Gates de evaluación

**Engineering:** el módulo original de selección es importado sin cambios; operadores/canales equivalentes; mismo dato inicial y primera observación por pareja; presupuesto ≤8; los artefactos se escriben sin sobrescribir; todas las predicciones fluidas son enteros no negativos tras adaptador.

**Ciencia (por separado):** correctos, falsos únicos, brechas `MODEL_GAP`, abstenciones, segundas pruebas, diferencias de política, y distancia entre predicciones. **No hay gate de promoción positiva**: `BLOCKED_RETROSPECTIVE_NOT_BLINDED` y `deployment_validated=false` incondicional.

**Interpretación de MODEL_GAP:** con banco fluido puede significar que la verdad quedó fuera de la tolerancia debido a **error de aproximación del modelo**, incluso cuando la estructura verdadera está en el banco. No atribuir automáticamente a cuarta etapa.

## Objeciones que pedimos investigar a otra IA

1. ¿Redondear una masa continua a conteos causa falsos `MODEL_GAP` bajo ±1? ¿El signo cambia la conclusión?
2. ¿Hay clases que desaparecen de supervivientes desde la primera lectura por discrepancia entre implementación DES y fluido?
3. ¿Se heredan configuraciones físicas de DES de modo que la aparente confirmación sea tautológica?
4. ¿La exigencia normativa de «una hipótesis garantizada por clase superviviente» impide mediciones útiles aunque exista separación parcial?
5. ¿Se confunde consistencia física con utilidad decisional o con validez fuera de banco?
6. ¿La alternativa de timestamps sería menos costosa que intervenir? **No probada aquí**: no hay timestamps como canal de CAF-07B.

**Regla:** resultado negativo se conserva sin ajustar a posteriori tolerancia, catálogo, cuantización o mundos. Si la nueva política falla, eso **es** el hallazgo. CAF-08B no cambia D/M/Buffalo ni ATMS; no añade sensores ni simula operación real.


## Resultado ejecutado: GitHub Actions (31-oct-2026)

**Ejecución reproducida con DES nativo:** [run 41245798310](https://github.com/yudocyudoc/IGC/actions/runs/41245798310), código evaluado `58ffd5b3870f46b03ff6f1490a1341b46606602c`. **5/5 pruebas PASS**; `CAF08B_TECHNICAL_PASS_SCIENTIFIC_NOT_PROMOTED`. [Artefacto con 48 archivos](https://github.com/yudocyudoc/IGC/actions/runs/41245798310/artifacts/13058732715) (44 decisiones escritas antes de segunda observación, plan, resultados, informe y manifiesto). Artifacts caducan; script y tests permiten regenerarlos.

### ¿Cuánto difieren las curvas predictivas?

| Banco | Canales predichos cotejados | Diferencias no nulas DES vs fluido cuantizado | Diferencia máxima | Exceden ±1 |
|---|---:|---:|---:|---:|
| 12 hipótesis (cuello único) | 156 | 3 | 1 pedido | 0 |
| 24 hipótesis (único + doble) | 312 | 6 | 1 pedido | 0 |

El **promedio absoluto** entre predicciones *enteras* es **0.01923 pedidos/canal** para ambos bancos. Esto NO es el MAE de los 44 mundos y tampoco mide precisión de sensores; es distancia entre bancos predictivos para las mismas hipótesis y pruebas. La pequeña diferencia **no prueba** equivalencia general entre simuladores.

### Veredictos: resultado del comparador

Los dos motores predictivos obtuvieron **exactamente los mismos veredictos, decisiones de segunda prueba, supervivientes y estados** en las 22 parejas mundo×banco.

| Banco evaluado | Correctos / 11 | Falsos cuellos únicos / 11 | Abstenciones / 11 | MODEL_GAP / 11 | Segundas mediciones / 11 |
|---|---:|---:|---:|---:|---:|
| DES, 12 hipótesis | 1 | 3 | 6 | 1 | 4 |
| Fluido retardado, 12 hipótesis | 1 | 3 | 6 | 1 | 4 |
| DES, 24 hipótesis | **0** | 0 | **10** | 1 | **0** |
| Fluido retardado, 24 hipótesis | **0** | 0 | **10** | 1 | **0** |

**Veredicto técnico/científico:** cambio de motor **sin beneficio diagnóstico demostrado**. En banco ampliado, cero falsos positivos se obtiene porque el sistema esencialmente no diagnostica: 10 abstenciones y una brecha. El programa permanece en `BLOCKED_RETROSPECTIVE_NOT_BLINDED`. No ajustar ±1 ni reescribir mundos para crear una mejora aparente.

### Implicación para la siguiente prueba

La hipótesis más útil pasa de “otro banco numérico arreglará al selector” a “**el espacio de observación es insuficiente para sus decisiones**”. Una siguiente prueba (no realizada en este PR) debe incorporar tiempos de inicio/fin de etapa, con trazas por pedido y resolución explícita, sin revelar la configuración privada por el sensor. El par A/B de #119 sugiere tránsito mínimo sin espera de 2.8 vs 2.6 min; queda pendiente comprobar que las trazas operativas realmente distingan modelos bajo las condiciones de llegada ensayadas.

**Límite:** no demostrar discriminabilidad mediante datos de configuración, no confundir resolución nominal con precisión instrumental ni inferir utilidad económica de una intervención simulada.
