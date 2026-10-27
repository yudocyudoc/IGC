# IGC · Arena R3 / PT-06 · Resultado real STR-02, caso R3-T1

**Fecha:** 2026-10-27. **Estado:** PR #63; 28 simulaciones OpenModelica reales ejecutadas y auditadas. **Ejecución irrepetible autorizada:** [#40578550337](https://github.com/yudocyudoc/IGC/actions/runs/40578550337), primer intento, `SUCCESS`. **Auditoría offline posterior:** [#40578937420](https://github.com/yudocyudoc/IGC/actions/runs/40578937420).

**Marco operativo:** PT-06 / R3 del plan y hoja de ruta v2.0. Este documento consigna resultados del diseño previo congelado en PR #62, no modifica los criterios tras haber conocido el resultado.

## 1. Qué se ejecutó

Se usaron las clases generadas por el **compositor y backend originales Short E1**, y las bibliotecas Modelica MSL 4.0.0, SystemDynamics 2.1.2 y OpenModelica 1.26.5. Exactamente **27 modelos candidatos distintos** (3 topologías C00/C01/C02 × 9 parejas de parámetros `responseTime`) y **un mundo generador separado**.

- Candidatos: DASSL, t=0–6 h, 120 intervalos cada uno. No se ajustaron parámetros fuera de la grilla `{0.25,0.50,1.00}` h para preparación y despacho. El tránsito quedó en 1.6 h y el resto de parámetros, en los valores originales.
- Mundo fuente sintético: topología C00, preparación 0.75 h, despacho 0.30 h; DASSL t=0–3 h, 120 intervalos. **No se generó su serie de tiempos reservados 4,5,6 h**.
- Estímulo común: pulso rectangular 1.7 items/h, durante las primeras dos horas.
- Observables entregados al selector: **solo `deliveredTotal` en t={0,1,2,3}** más ruido sintético determinista `[0,+0.002,-0.003,+0.004]`. El selector recibe un archivo sin grafo generador, parámetros verdaderos ni puntos futuros.
- Cada uno de los 27 CSV reales pasó el verificador molecular original G2 (balances materiales), antes de calcular RMSE. No se hicieron inferencias IA, nuevas gramáticas, cambios de física o llamadas de simulación extra.

## 2. Observaciones del generador y decisión propia

Las mediciones de construcción extraídas de la simulación real, con ruido declarado, fueron:

| Tiempo (h) | `deliveredTotal` (items) |
|---:|---:|
| 0 | 0.000000 |
| 1 | 0.465015 |
| 2 | 1.759220 |
| 3 | 2.894891 |

El mundo simulado cumplió G2 con **residuo máximo de balance material 6.84297×10⁻¹² items**.

Resultados por estructura de la nueva política (mejor de las nueve parejas de cada topología):

| Estructura material | Mejor candidato | RMSE de construcción (items) | ¿Cumple límite 0.020? |
|---|---|---:|---|
| C00 (dos colas) | **C00P04** | **0.035408529** | **No** |
| C01 (tres colas) | C01P00 | 0.647636771 | No |
| C02 (cuatro colas) | C02P00 | 1.290101455 | No |

**M3 original, congelado:** `ABSTAIN`, sin padre seleccionado, razón `ALL_FIXED_E1_STRUCTURES_MISS_CONSTRUCTION_TOLERANCE`.  
**Nueva variante R3 3×9:** `ABSTAIN_ADMISSIBLE_GRID_HAS_NO_COMPATIBLE_STRUCTURE`, conjunto compatible **vacío**.

El mejor candidato C00P04 usa `responseTime=0.5 h` en preparación y despacho, es decir, **el representante nominal original M3**. En este primer caso, ampliar la búsqueda a las otras ocho parejas **no redujo el RMSE mínimo por debajo del original**, y tampoco evitó la abstención. Los cambios paramétricos propuestos no mostraron una mejora útil bajo el criterio predeclarado.

## 3. Lectura estructural / paramétrica correcta

El generador **sí pertenece a C00** pero su pareja verdadera (0.75,0.30 h) queda **fuera de la grilla discreta**, aunque dentro de los límites generales del catálogo E1. Por tanto:

- Se observó un **resultado negativo** de recuperación de la topología **dentro de la grilla y con el umbral 0.020**, no la imposibilidad de que C00 describa la dinámica con otros parámetros.
- Las tres estructuras no resultaron *igualmente ambiguas*: C00 obtuvo mucho menor RMSE que C01 y C02. Pero un ranking de error no justifica **selección estructural** cuando ninguna propuesta pasa la regla declarada.
- Este caso no demuestra que la grilla se pueda mejorar a posteriori: **no se amplía, no se densifica ni se adapta** después de conocer estos resultados. No se cambia el umbral ni se hace otra simulación para fabricar un PASS.
- No hay todavía evidencia sobre ambigüedad entre **múltiples estructuras compatibles**; ese ensayo separado de R3/STR-03 debe diseñarse y congelarse antes de ejecutarlo.
- Una simulación del mismo repertorio molecular con ruido definido no es validación causal externa ni predicción independiente de R4.

## 4. Memoria y procedencia

La autorización se consumió mediante `data/diagnostics/ARENA_R3_T1_28_SOLVER_AUTH_20261027.json` añadido a la rama de trabajo una sola vez; el workflow se activa exclusivamente en la adición original y en `GITHUB_RUN_ATTEMPT=1`.

El [artefacto físico completo](https://github.com/yudocyudoc/IGC/actions/runs/40578550337) incluye el manifest de 27 candidatos, programa `.mos` con exactamente 28 instrucciones de simulación, modelos E1, 27 CSV candidatos, CSV del mundo, log `omc`, caso de cuatro observaciones, resultado original del selector, provenance sellada y veredicto posterior. La auditoría [postonly #40578937420](https://github.com/yudocyudoc/IGC/actions/runs/40578937420) volvió a comprobar sus hashes, los mínimos RMSE y la decisión, **sin solver ni proveedor**.

- SHA256 del manifiesto de búsqueda: `d33cc4ca8c253226ff50efa6c47e40b9b8c32d0436f370907db2579c9dc0fde5`.
- SHA256 del conjunto público de cuatro observaciones (case): `e94432392e760109007aed3e3839d62f5e937014508b06ddeb50cf26f6530c4a`.
- Los seis mundos anteriores M3-P siguen siendo antecedentes de desarrollo, no nuevos casos de validación de R3.

**ATMS y R4:** esta ejecución no crea una nueva arquitectura de memoria ni adelanta pruebas predictivas. Se preserva la frontera de tiempos y la posibilidad de registrar posteriormente esta decisión negativa en la memoria existente, cuando PT-06 requiera una integración explícita.

## 5. Paso siguiente, estrictamente PT-06

Cerrar STR-02 como prueba **ejecutada y negativa**, conservarla como evidencia adversativa de la búsqueda finita y continuar el diseño de **ambigüedad estructural e incompatibilidad** previsto por PT-06/STR-03. Los casos y sus presupuestos deben quedar predeclarados antes de simularlos. **No iniciar PT-07/R4, REF, Clef, Clairic ni optimización posterior sobre R3-T1.**
