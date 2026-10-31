# CAF-07 — Selector de evidencia entre hipótesis y decisiones

**2026-10-31. Exploración DES pública, no validación confirmatoria.**

El resultado de CAF-06 demostró que, con demanda baja, varias localizaciones de cuello de botella son observacionalmente equivalentes, mientras que otras condiciones dejan crecer colas que permiten separarlas. En CAF-07 no solo preguntamos si un sensor es útil retrospectivamente: construimos un **selector explícito que compara mediciones futuras en función de hipótesis todavía compatibles, relevancia para la decisión y costos ilustrativos**, y admite detenerse o reconocer una brecha de modelo.

## Lo que CAF-07 NO afirma

- **No es un selector de stocks de M o D.** CAF-05 demostró que los operadores de estado interno DES→M/D no estaban justificados. Continúan bloqueados. El banco de hipótesis de este experimento está implementado directamente con configuraciones físicas DES cuya observación de colas y entregas tiene significado explícito.
- No es un POMDP, un estimador bayesiano ni un cálculo de valor esperado económico de información. No hay probabilidades de hipótesis ni costos observados de instrumentación.
- No es una inferencia de causalidad económica ni un plan de contratación.
- Los nuevos mundos y los candidatos son generados por la **misma familia de motor DES**, lo que simplifica el experimento pero **no permite afirmar independencia estructural** ni extrapolación a cafeterías reales.

## Banco de hipótesis físico, anterior a los mundos de evaluación

**12 candidatos**: cuello localizado en preparación, despacho o entrega; capacidades nominales alternativas 60, 75, 90 o 105 pedidos/h. Cada candidata tiene tres etapas en serie, 1 servidor en cuello con tiempo exacto `60/capacidad` minutos/pedido, y 2 servidores de un minuto en las otras etapas (capacidad 120/h). Stocks iniciales vacíos, pedidos homogéneos, aceptaciones durante 20 minutos.

**Tres mundos nuevos, físicamente distintos del banco:** preparación 72/h, despacho 88/h, entrega 102/h. Son configuraciones deliberadas para probar comportamiento *fuera de la rejilla de capacidades*, no muestra aleatoria ni caja negra. Sus etiquetas solo son accesibles al evaluador después de cada medición.

Toda candidata produce antes de observar cualquier mundo nuevo un vector de predicciones para una medición inicial `delivered @ 1.2 pedidos/min, t10` y para cada acción del menú posterior. Se ejecutan **12 × 10 = 120 simulaciones DES de hipótesis**. Se guardan todas las predicciones en `00_PLAN_Y_CANDIDATOS_ANTES_DE_EVALUAR.json` con escritura exclusiva y `fsync` **antes de iniciar la primera simulación DES de los nuevos mundos**.

## Mediciones candidatas y costos declarados

| Acción | Presión pedidos/min | t | Canales | Costo ilustrativo |
|---|---:|---:|---|---:|
| Entregas acumuladas | 1.5 | 20 | 1 | 1 |
| Cola esperando en preparación | 1.5 | 20 | 1 | 2 |
| Cola esperando en despacho | 1.5 | 20 | 1 | 2 |
| Cola esperando en entrega | 1.5 | 20 | 1 | 2 |
| Stock total en despacho | 1.5 | 20 | 1 | 2 |
| Colas preparación + despacho | 1.5 | 20 | 2 | 4 |
| Colas de las tres etapas | 1.5 | 20 | 3 | 6 |
| Colas preparación + despacho | 1.8 | 20 | 2 | 7 |
| Colas de las tres etapas | 1.8 | 20 | 3 | 9 |

Presupuesto máximo **8 unidades ilustrativas**: por tanto, medir las tres colas bajo 1.8/min está fuera de presupuesto. Es una prueba explícita de factibilidad, no una cifra en MXN ni una estimación de riesgos laborales. Cambiar demanda en una empresa real requeriría consentimiento, ética operacional y cálculo de riesgos que aquí NO están modelados.

## Selector determinista y abstención

1. Recibe solo la observación K0 visible (entregas acumuladas t10 a 1.2/min), nunca la estructura o los parámetros reales del nuevo mundo.
2. Conserva hipótesis cuya predicción difiera de la observación en **≤1 pedido**. Ese margen es de diseño del laboratorio, no calibración de un error estadístico.
3. Si no sobrevive ninguna, devuelve `MODEL_GAP_NO_COMPATIBLE_HYPOTHESIS`: **no fuerza una causa inexistente en su banco**. Si todas las supervivientes implican la misma etapa física, detiene la adquisición.
4. Entre medidas factibles, cuenta **pares de hipótesis supervivientes que proponen intervenciones distintas** (cuellos en distintas etapas) y cuyas predicciones están separadas en al menos un canal por más de **2 pedidos**; es una separación robusta frente a dos bandas ±1.
5. Calcula `separación de pares – costo ilustrativo`. Elige el mayor valor positivo (desempata por separación bruta, menor costo e identificador), sin utilizar probabilidades inventadas.
6. Si no existe una acción con valor discriminativo neto positivo, devuelve `STOP_NO_INFORMATION`. Este es un criterio **heurístico**, no una demostración de que el valor económico de seguir midiendo es negativo.
7. Escribe la elección y los candidatos por mundo en `01_PRE_PROBE_<mundo>.json` **antes de realizar cualquier medición posterior**.
8. Actualiza la lista con los valores nuevos, usando los mismos operadores físicos y tolerancia ±1. Emite diagnóstico solo si queda **una única clase de cuello**; si sobreviven varias, abstiene. Si ninguna sobrevive, declara brecha de modelo.

No se usa el mecanismo DES para hacer afirmaciones de identificación de M/D. **Reducir el conjunto de candidatos no equivale por sí mismo a demostrar que cambiar una estación aumentará las ventas.**

## Ejecución y pruebas

```bash
python -m unittest discover -s experiments/cafeteria/pc02 \
  -p 'test_caf07_selector_evidencia.py' -v

python experiments/cafeteria/pc02/caf07_selector_evidencia.py \
  --out artifacts/caf07-evidence-selector
```

La CI intercepta las ejecuciones DES para comprobar que las predicciones físicas de hipótesis se completen antes de empezar cualquier mundo nuevo; que cada elección individual esté en disco antes de su experimento siguiente; que un error en el motor no provoque reintentos silenciosos; y que M/D, sus políticas y la restricción del contrato CAF-05 permanezcan intactos.

Los resultados `01_RESULTADOS.json`, `02_COMPARACION.csv` y `03_INFORME.md` distinguen aciertos, errores, abstenciones, decisiones de detenerse y falta de hipótesis. No se trata abstención como un pronóstico acertado ni como pérdida cero. Los hashes son locales: no hay custodia independiente.

## Preguntas a resolver con los resultados

- ¿El selector elige una medición que distinga **decisiones relevantes** o solo discrimina diferencias de capacidad?
- ¿El límite de gasto elimina mediciones potencialmente muy discriminativas?
- ¿El presupuesto y la tolerancia hacen que deba detenerse o admitir que sus modelos son insuficientes?
- ¿Las hipótesis de capacidad discreta siguen siendo adecuadas en mundos intermedios?
- ¿Existe una señal que el selector no pueda interpretar porque su gramática física es demasiado estrecha?

Si hay errores, no se modifican la regla, los costos ni el banco para recuperar estos mundos como éxitos; cualquier corrección se evalúa en nuevas configuraciones.
