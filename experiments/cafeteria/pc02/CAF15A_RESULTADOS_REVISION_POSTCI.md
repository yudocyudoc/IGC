# CAF-15A — Resultados post-CI y revisión adversativa

**2026-10-31 local (ejecución CI registrada en UTC el 2026-11-01). Estado: POST HOC respecto al primer protocolo, NO preregistro adicional. PR #127 Draft apilado sobre #126 Draft; #125–#123 Draft y sin merges.**

## Procedencia auditable

- Protocolo: primer commit `af837c9d2e716ffc5a2b7e3f99c579e46be0e301` ANTES del código. Enmienda de constructor rápida de cuarta etapa `7f66df735e0909433542a6d2e9cc21d8f232c932`, también ANTES de código, sin cambiar los cinco controles ni la familia de hipótesis.
- **[GitHub Actions #41263963016](https://github.com/yudocyudoc/IGC/actions/runs/41263963016)**: siete pruebas PASS y programa auditado PASS. Head probado `8a7176165b25d0f68b1af2a5e41a6f0e5a748abd`, checkout de merge sintético `6069e0efda6521d2aec4bb99d8c55a9cf85f2ab2` (registrados por separado).
- **[ZIP de 6 artefactos originales](https://github.com/yudocyudoc/IGC/actions/runs/41263963016/artifacts/13066047047)**: `00B_CATALOGO_TESTIGOS_PRE_MUNDOS.json` (720 configuraciones y firmas de cuatro programas), `00_PLAN_PRE_MUNDOS.json`, `00C_GRAFO_TESTIGOS_PRE_MUNDOS.json`, `01_RESULTADOS.json`, `02_INFORME.md`, `03_MANIFIESTO.json`. Hash de catálogo registrado en plan: `sha256:f634193b6a236f4fa048114f94ebd0f3c856868b1b2bf8a0707bbf78acdbe412`. Plan/catálogo/grafo guardados antes de evaluar mundos.
- **Método de archivo:** aritmética exacta `Fraction(60,c_s)` y motor DES-CAF01 en las **720 configuraciones**: tres familias simples con un c, y tres dobles con dos c independientes. 90 configuraciones diagonales y 630 fuera de diagonal. No se infieren resultados para capacidades omitidas de la malla.
- **La búsqueda de contraejemplos es una falsación asimétrica:** si se halla una firma común bajo ±1 para dos clases, el par es globalmente CONFUSABLE en el continuo físico porque los dos parámetros exactos son posibles. **No encontrar testigo NO certifica separabilidad global bidimensional.**

## Resultado principal: ninguna arista nueva apareció en la malla

| Programa fijo | Pares con testigo c1=c2 /15 | Pares con testigo c1,c2 libres en malla /15 | Pares añadidos |
|---|---:|---:|---:|
| BASE (K0/K1) | 15 | 15 | 0 |
| F_R18_T20 (108/h, waiting+stocks t20) | 15 | 15 | 0 |
| F_R25_T20 (150/h, waiting+stocks t20) | **4** | **4** | **0** |
| F_R25_T25 (150/h, waiting+stocks t25) | **4** | **4** | **0** |

**No se encontró contraejemplo nuevo a las 11 separaciones globales de CAF-14 en este retículo.** Eso NO significa que sean separables para todo `[55,110]^2`. La afirmación de CAF-14 solo estaba certificada (condicionalmente al submodelo exacto) en la **diagonal c1=c2**, cuyo conjunto está contenido en el plano bidimensional.

Los cuatro testigos históricos persisten con fuerza: a **c=55/h** las parejas:
- `preparacion` vs `preparacion+despacho`,
- `preparacion` vs `preparacion+entrega`,
- `despacho` vs `despacho+entrega`,
- `preparacion+despacho` vs `preparacion+entrega`

tienen **firmas enteras exactamente iguales** con programas R25_t20 y R25_t25, sin requerir error de medición. Los casos con parámetros desiguales incluyen esas soluciones diagonales por contención. Esta coincidencia confirma confusión existencial, NO igualdad de dinámicas para todas las capacidades.

## Evaluación de mundos con capacidades desiguales

Se fijaron **24 mundos dobles off-diagonal** en la propia malla (por tanto 24/24 coverage es un **control casi tautológico**) y **5 controles de cuarta etapa** (64,86,106,160,220/h).

| Programa | Clase real conservada, diagonal /24 | Clase real conservada, 2 capacidades /24 | Clases únicas correctas en malla 2D /24 | Media de clases diagonal | Media de clases 2D |
|---|---:|---:|---:|---:|---:|
| BASE | 24 | 24 | 0 | 6.0000 | 6.0000 |
| F_R18_T20 | 19 | 24 | 5 | 2.1250 | 2.5833 |
| F_R25_T20 | 18 | 24 | 6 | 2.0000 | 2.2500 |
| F_R25_T25 | 16 | 24 | 8 | 1.7917 | 2.1250 |

- **6/24 mundos a t20 y 8/24 a t25** resultan `NO_MATCH_ON_DIAGONAL_LATTICE` (sin clase compatible en esa malla): se debe a la hipótesis demasiado restrictiva c1=c2. En la malla 2D siempre hay una configuración verdadera exacta, que recupera la clase real y su par de capacidades. Nunca interpretar conjunto vacío del modelo diagonal como descubrimiento de topología nueva.
- En esos mismos casos, el modelo ampliado devuelve una **única clase en la malla**, siempre correcta. A t20 son los tres pares nominales de etapa con capacidades `(100,95)` o `(100,60)`; a t25 se agregan `(86,83)` para dobles `preparacion+entrega` y `despacho+entrega`.
- **Advertencia decisiva:** 6/24 y 8/24 NO son diagnósticos unívocos **en el continuo**. Cualquier capacidad fuera de los 15 puntos puede restaurar una clase rival. No comparar directamente con los 0/18 dobles únicos del CAF-14 como si fuera el mismo conjunto de mundos: cambiaron los 24 mundos y se usó una malla. Ambos factores alteran la interpretación.
- Aunque en la malla la familia bidimensional retiene 24/24 verdades, no hay prueba independiente: la propia malla fue usada para elegir todas las capacidades de evaluación. Es una comprobación de código.

## Controles de cuarta etapa rápida

- El constructor de `CAF07B.make_physical_config` imponía `cap<120` como regla del ejercicio histórico. Un constructor local con `des.validate_private_config` habilitó controles de cuarta etapa a **160 y 220/h**, junto a 64,86,106/h, sin ampliar el dominio del catálogo conocido.
- Con BASE, los cinco controles siguen siendo compatibles con familias de tres etapas. Bajo 108/h y t20, dos de cinco carecen de coincidencia de malla. Bajo **150/h t20 y t25**, **5/5** controles tienen `NO_MATCH_ON_LATTICE` tanto en diagonal como en 2D.
- **No afirmar detector universal de topología ausente:** `NO_MATCH_ON_LATTICE` no significa `MODEL_INCONSISTENT_IN_CONTINUUM`. Además, una cuarta etapa rápida puede no saturarse pero sigue agregando duración física y latencia que afectan entregas/stock. El resultado sintético no determina sensibilidad en el mundo real.

## Reglas metodológicas reforzadas

1. **Incluir un submodelo conserva sus testigos de confusión.** Liberar `c1,c2` no puede hacer desaparecer las cuatro confusiones CAF-14. Las once separaciones globales previas NO se heredan de forma automática; en esta malla no aparecieron testigos contrarios, resultado NEGATIVO NO CERTIFICADO.
2. **Una prueba sobre malla no es inversión bidimensional.** La exhaustividad racional de eventos de CAF-11/12 solo certifica cortes de un único parámetro. CAF-15A prueba valores individuales 2D con DES exacto, pero no particiona `[55,110]^2`.
3. **Separar lectura fija vs dos modelos inciertos.** Un modelo se ajusta a una lectura física `y` si `|x−y|≤1`; dos modelos pueden compartir ALGUNA lectura en sus cajas ±1 si `|x−z|≤2`. El código prueba ambas operaciones.
4. **Desigualdad de capacidades puede crear evidencia nueva** en algunos regímenes, pero la unicidad dentro del catálogo de malla aún puede ser espuria por capacidades intermedias u otras topologías.
5. **Sin probabilidades ni extrapolación:** los 24 casos y cinco controles NO estiman prevalencias, no calibran ±1, no prueban diagnósticos reales ni desempeño bajo aleatoriedad.
6. **No otro selector ni optimización de política**, ya que el problema sigue siendo representar familias y medir información.

## Siguiente decisión científica

Es prioritario dejar de intentar demostrar una negación global mediante rejillas. Dos opciones:
- **CAF-15B matemático:** partición certificada del espacio 2D de tiempos de servicio en regiones de firmas constantes, o solver verificable de intersección de firmas por par. Solo así se podría afirmar separabilidad global bajo ese modelo.
- **CAF-16 de robustez física/estocástica:** nueva predeclaración, tiempos de servicio variables y sensor temporal con error medido/justificado, mundo evaluador independiente, contraejemplos OOD, modelos con c1≠c2; no confundir simulación con prueba real.

Se recomienda revisión adversativa de los supuestos `FIFO`, `servers=2`, ausencia de inventario o bloqueo, y pruebas de que las firmas del DES reflejan estados observables por una PYME sin información privilegiada.

**Gate:** `BLOCKED_LATTICE_WITNESSES_ONLY_NO_2D_GLOBAL_CERTIFICATION_NO_EXTERNAL_VALIDATION`. PR #127 permanece Draft; sin merge o validación externa.
