# CAF-02 — Matriz exploratoria de cinco mundos DES

**Fecha:** 2026-10-30. **Acción:** obtener resultados, no construir otra cadena de permisos. Esta matriz es experimental **exploratoria** y pública; no está protegida por G5 ni aporta evidencia confirmatoria independiente.

## Cinco configuraciones predefinidas

| Mundo | Preparación (servidores×min) | Despacho | Entrega | Capacidad mínima | Propósito |
|---|---|---|---|---:|---|
| A | 2×1.5 | 1×0.75 | 2×1.5 | 80 pedidos/h | Caso previo, control de regresión |
| B | 1×1 | 2×1 | 2×1 | 60 pedidos/h | Cuello en preparación |
| C | 2×1 | 1×1 | 2×1 | 60 pedidos/h | Cuello en despacho |
| D | 2×1 | 2×1 | 1×1 | 60 pedidos/h | Cuello en entrega |
| E | 2×1 | 2×1 | 2×1 | 120 pedidos/h | Capacidad sin saturación en todos los pulsos públicos |

En B/C/D solo se mueve la posición del recurso que limita el flujo. Todas las etapas sirven un pedido por servidor en un minuto. E supera tanto K0=72/h como K1-C=108/h. A reproduce el mundo publicado en el PR #109: **no se cuenta como réplica independiente nueva**.

El DES mantiene el mismo motor genérico de servidores y colas con pedidos individuales. Cero cancelaciones, pérdidas o stocks iniciales, entrada en instantes exactos medios hasta t20, lecturas hasta t40. El mundo se define en `caf02_lab_matriz_cinco_mundos.STAGES` **antes de producir cualquier salida de esta matriz**.

## Un comando, cinco resultados reales

```bash
python experiments/cafeteria/pc02/caf02_lab_matriz_cinco_mundos.py \
  --out artifacts/mi-caf02-cinco-mundos
```

No añade nuevas moléculas, heurísticas, rondas de optimización ni ajustes pos-K2. Reutiliza, **sin cambiar sus implementaciones**, K0, el selector conjunto M+D, K1 una sola vez si hay hipótesis, G4a/G4b y la función K2 de ambos brazos. Cada mundo tiene su propio directorio, sus hashes, pronósticos K2 guardados/sincronizados a disco antes de K2 y salidas DES posteriores; si falla, permanece incompleto y no se reintenta automáticamente.

Archivos principales: `00_PLAN_FIJO.json`, `mundo_A/` ... `mundo_E/`, `01_RESULTADOS.json`, `02_COMPARACION.csv`, `03_INFORME.md`, `04_ARCHIVOS_SHA256.json`. Los subdirectorios incluyen los mismos archivos numerados 00–11 del laboratorio original. La CI ejecuta casos DES reales y publica todo el directorio.

## Qué se examina

- Si K1 reduce candidatos y si esa reducción mejora **o empeora** la pérdida respecto del mismo brazo antes de K1.
- Si la reestructuración de la restricción física —cambiar solo el lugar del cuello de botella— modifica la opción K1, la clase superviviente o el resultado predictivo.
- Cuántos casos M y D pasan el umbral de mejora 0.25, cuántos se abstienen y cuántos sufren daño de predicción; sin convertir abstención en error cero.
- Cuánto se separan M/D de `REF_SCALE` y `REF_CAF`, aclarando siempre que las referencias usan solo K0.
- Cuándo M-C01 o D-D3 sobreviven a K1 pese a que el DES genera pedidos a través de tres etapas en los cinco mundos.

La inferencia principal posible será **de sensibilidad al mecanismo de este conjunto fijo de cinco configuraciones DES**, no una tasa de éxito poblacional, identificación causal o precisión sobre empresas reales. Los resultados del primer mundo ya eran conocidos al diseñar B–E; los resultados nuevos son útiles para ingeniería, no cegamiento prospectivo.

No reabrir CAF-01, E1, M, D, native G2 (15/15 previamente obtenido), Buffalo o ATMS. Política confirmatoria permanece sin autorización. El objetivo siguiente será discutir **los números** y modificar el método solamente si un fallo generalizable queda identificado, siempre separando el experimento que lo motivó de la nueva prueba.
