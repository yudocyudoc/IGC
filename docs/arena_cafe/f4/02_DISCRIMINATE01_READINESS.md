# ARENA IGC · DISCRIMINATE-01 · Requisitos de evidencia y frontera hacia F5

**Fecha:** 2026-11-03 · **Corte:** F4, continuación de PR #149 y del plan de cafetería v3.2 de 2026-11-02 · **Estado:** diseño de evaluación **NO LISTO**, no prerregistro, no G4 ni G5.

## 1. Pregunta que mantenemos

**Identificabilidad causal de un cuello de botella:** ¿pueden dos mecanismos diferentes explicar S0 (observación operativa básica), producir respuestas distintas ante **la misma intervención físicamente viable**, y puede S1 (instrumentación legítima adicional del *mismo mundo*) reducir las explicaciones compatibles **sin inventar una clase única**?

Esta es una pregunta de **predicción y discriminación**; no se exige que las acciones óptimas sean distintas, puesto que no se ha definido utilidad ni costos. Tampoco hay valor predictivo de minería P demostrado.

## 2. Hechos ya comprobados, no otro ajuste de modelos

- **PR #148:** dos mecanismos auxiliares de tres estaciones, escogidos constructivamente después de consultar O0, tienen idénticas entregas acumuladas **[0,0,2,4,6,8]**; al añadir un servidor de preparación desde t=0, producen respectivamente **14 y 8** entregas al minuto 10, usando el motor DES original.
- **PR #149:** sobre O1 del *mismo* EV-01, **9 preparaciones** completadas antes del minuto 10 y servicio medio **15/17 minutos**. A predice **9** y **1 minuto**, B predice **15** y **3/5 minutos**. **Ambas hipótesis fallan la coincidencia O1 exacta**. Es un vacío de estas **dos hipótesis deterministas**, no un fallo de toda la familia SD ni una identificación del mecanismo verdadero.
- **PR #147:** la minería PM4Py original sobre FULL de EV-01 no añadió variantes de ruta frente a la instrumentación B1; no se justifica atribuirle este hallazgo O1. B1/B2 sí son referencias físicas, no un brazo competidor ni una autorización para introducir FULL en O0.

**Resultado:** no conservamos artificialmente la pareja cambiando sus parámetros a posteriori; tampoco saltamos a la optimización continua ni a una malla nueva. Conservamos las dos hipótesis como testigos de **ambigüedad O0** y **refutación O1**, y registramos por qué faltan datos antes de F5.

## 3. Qué diferencia tendría que admitir un criterio con error acotado

El cálculo usa **solo los resultados O1 ya ejecutados** y no corre otro DES. Para cada hipótesis fija calcula dos diferencias absolutas independientes (conteo de servicios completados y media de duración de preparación):

| Hipótesis | `|n_modelo − n_O1|` (servicios) | `|media_modelo − 15/17|` (min) |
|---|---:|---:|
| A · cuello en preparación | **0** | **2/17** ≈ 0.11765 |
| B · cuello en despacho | **6** | **24/85** ≈ 0.28235 |

Si **algún día** un protocolo piloto validara bandas absolutas separadas `ε_n` (conteo) y `ε_t` (media), estas condiciones serían **necesarias para no excluir** las hipótesis fijas por esas dos observaciones:

- Para A: `ε_n ≥ 0` y `ε_t ≥ 2/17` minutos.
- Para B: `ε_n ≥ 6` servicios y `ε_t ≥ 24/85` minutos.
- Para evitar excluir **ambas** en el mismo criterio de dos coordenadas: `ε_n ≥ 6` y `ε_t ≥ 24/85`.

**No hemos demostrado que tales tolerancias existan.** No son «errores instrumentales medidos», intervalos de confianza, márgenes estadísticos ni requisitos para elegir sensores. Son desigualdades exactas derivadas de **residuales de hipótesis diseñadas**. Una discrepancia puede deberse a error de medición, variación real del servicio, censura, falta de correspondencia de la etapa, parámetros incorrectos o estructura errónea. **No la atribuimos automáticamente a ruido de sensor.**

Un modelo que satisficiera esas desigualdades tampoco quedaría identificado: el criterio solo evitaría su exclusión según dos variables, **dentro de esta pareja**.

## 4. Paquete mínimo de evidencia antes de diseñar una reserva

**Medición física:** el piloto fuera de la reserva deberá documentar resolución y sincronización de relojes, latencia y pérdida de eventos POS/KDS, vínculos por `case_id` y marcas físicas de entrada/inicio/fin, cobertura por recurso, ventana exacta `[0,cutoff)`, y política de simultaneidad. La media O1 procede únicamente de servicios **terminados antes del corte**, y sus sesgos de selección y heterogeneidad se examinan en réplicas piloto genuinas, no con números arbitrarios.

**Hipótesis y predicción:** registrar la distinción entre compatibilidad de S0, compatibilidad adicional S1, falta de cobertura `MODEL_GAP`, falsa exclusividad `FALSE_UNIQUE` y abstención. La hipótesis rivales F4 ya fue diseñada a la vista de O0 y O1; no puede contarse como predicción prospectiva en esos datos. La evaluación de una acción de +1 preparación solo adquiere significado empresarial cuando se comprueban espacio, personal, equipo, inventario, costos y la factibilidad de ejecutar esa acción.

**Tres métodos originales:** F3 sigue **A3 parcial** hasta una ejecución auténtica o fallo/abstención propio de Buffalo en EV-01, y hasta satisfacer el aislamiento de condiciones. No reemplazar B por un stub, ni D/M por un selector externo de ajustes. OpenModelica continúa como solucionador, no método competidor.

**Reserva independiente:** solo después de un piloto de ruido/variabilidad, especificación `H_j`, acciones factibles y separación de sesgos, se podrá considerar un diseño nuevo con mundos y réplicas **no consultados** en desarrollo. Para cada `mundo × réplica × brazo × condición`, aislar procesos, cachés, eventos y lecturas de ATMS/ledger. El evaluador conserva la correspondencia entre condiciones del mismo mundo, pero los productores no ven la vista hermana ni la verdad privada. Las predicciones y abstenciones deben quedar congeladas en G4 antes de leer G5. Este documento no crea esa reserva ni autoriza su apertura.

## 5. Minería de procesos, con una condición concreta

La investigación de minería P sigue motivada por la **identificabilidad insuficiente de cuellos de botella**. No se añade P por estética del DFG: únicamente se estudia si existe una regularidad **procesual observada** (retrabajo, prioridades, recursos compartidos, lotes, rutas alternativas) que B1/B2 no recuperen suficientemente con los **mismos logs y sensores**. Se evalúa *con/sin P* **dentro** de cada D/B/M, con sesiones y memorias aisladas, y una reserva adicional si P fue seleccionada gracias a F5. EV-01 de ruta fija no activa esa justificación.

## 6. Estado ejecutable y falsadores

`scripts/arena_cafe/f4_discriminate_readiness.py` registra exactamente las diferencias de las **dos hipótesis F4 originales**, leyendo O0, O1, el testigo F4 y el informe O1 precedentes. Rechaza artefactos de otro mundo, lecturas O1 alteradas o hipótesis cambiadas. No ejecuta modelos, proveedores, DES, PM4Py ni OpenModelica. La CI reproduce estos requisitos desde las **fuentes congeladas** y emite `DISCRIMINATE01_READINESS.json` con:

- Condiciones **necesarias** para la no exclusión en una comparación con tolerancias futuras aún desconocidas.
- Separación explícita de incertidumbre de medición, variación y error de mecanismo.
- Bloqueos con causas verificables: A3 parcial, precisión no calibrada, piloto no ejecutado, factibilidad no comprobada, aislamiento y reserva no creados, G4 no emitido.
- Resultado `F5_readiness=NOT_READY`; `A3=PARTIAL`; `G4=G5=NOT_RUN`; `PM_attribution_or_ablation=NOT_RUN`.

**Criterio de parada del incremento:** no convertir diferencias numéricas de modelos en una «tolerancia defendible»; la prueba correcta puede descubrir que aún no disponemos de ella. Ese estado deja una tarea empírica concreta, sin inventar otra metodología de identificación.
