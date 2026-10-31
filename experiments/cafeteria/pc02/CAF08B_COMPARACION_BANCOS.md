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
