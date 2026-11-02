# CAF-02 · G2 nativo: fuentes Modelica M/D y ejecución de 15 casos sin mundo DES

**Fecha:** 2026-10-30. **Ámbito:** comprobación nativa de los 15 casos de prueba **ya seleccionados en el PR #106**; no autoriza K0/K1/K2 independientes, no cambia los parámetros de la campaña ni habilita DES. No es un preregistro externo G5.

## Entregables y correspondencia

- Cada script `.mos` ejecuta explícitamente `cd(<carpeta de artefactos>)` antes de simular, para que **los CSV se escriban dentro del mismo lote auditable**, no en la raíz del repositorio.
- `caf02_g2_native_modelica_sources.py`: sintetiza de forma determinista **12 modelos M** (6 C00 de dos etapas, 6 C01 de tres etapas) y **3 modelos D** (D1/D2/D3 con 1/2/3 stocks), usando las filas exactas de `caf02_g2_native_correspondence_plan.plan(policy)`. Para cada caso genera `CAF02_<ID>.mo`, `CAF02_<ID>.mos` y un registro SHA-256 en `G2_SOURCE_MANIFEST.json`.
- `caf02_g2_native_executor.py`: **verificación posterior a la ejecución** que NO invoca OpenModelica; exige `.attempt` escrito antes de ejecutar, `.exit_code=0`, log real, CSV, hashes del modelo y script intactos, stocks y conservación de material. Compara la entrega nativa en t=[5,10,15,20,30,40] con la curva Heun de M o RK4 de D **para el mismo pulso y configuración**, máximo error absoluto ≤**0.05 pedidos**. Genera un recibo por modelo y resumen de quince aunque haya fallos.
- `test_caf02_g2_native_modelica_executor.py`: verifica unidades y topologías, rechazo de CSV sintético sin marcador/solver y falsos datos, controles de capacidad y manifest inalterado.
- `.github/workflows/caf02-g2-modelica-preflight.yml`: en PR prepara fuentes y ejecuta **`checkModel` real de OpenModelica** para los quince modelos, sin invocar `simulate`; guarda fuentes y log.
- `.github/workflows/caf02-g2-native-one-shot.yml`: el **primer y único push relevante a `main`** ejecuta el lote G2 bajo guardias `github.run_number==1`, `github.run_attempt==1`, `main` y concurrencia sin cancelación. Genera fuentes, comprueba los 15 modelos **antes de gastar llamadas**, y luego ejecuta cada `.mos` **una vez sin reintentos**. Conserva intento, código de salida, fuentes `.mo`, instrucciones `.mos`, CSV del solver, log, huellas y recibos tanto en PASS como en FAIL.

**No se adjuntan como resultados nativos curvas copiadas de Python.** Las trazas y diferencias solo serán reportadas como observadas cuando el workflow de ejecución haya consumido sus 15 llamadas y archivado CSV reales.

## Ecuaciones de los modelos nativos

Toda la simulación Modelica emplea tiempo **horas**, velocidades **pedidos/hora**, stocks y acumulados **pedidos**. Los `tau` de la gramática previa, declarados en **minutos**, se dividen entre 60. Los pulsos públicos de duración 20 minutos se traducen en `pulseDurationH = 1/3` y `pulseRateH = 60 × tasa_por_minuto`; fuente igual a cero desde el instante de corte.

Para cada etapa (i), flujo:

`fi = min(capacityiH, max(0, si/responseiH))`

Balance: `der(s1) = inputRate - f1`; para i>1, `der(si) = f(i-1) - fi`; salida `der(delivered) = fN`; entradas acumuladas `der(accepted) = inputRate`. Los estados `si`, `accepted`, `delivered` parten de **cero en cada caso**.

**M:** C00 tiene preparación y despacho con la misma capacidad y tiempos específicos por etapa; C01 añade tránsito con `tau_transit` propio y capacidad fija 100/h, como en su integrador Heun. **D:** 1/2/3 stocks seriales, mismo `responseTime` y capacidad en todas las etapas, pérdida prohibida, idénticos a su RK4. **No se añade ni altera la gramática E1 ni la de D.**

Los 15 inputs son exactamente K0 a 1.2/min y K1-B/C a 1.5 y 1.8/min del menú **existente**. Son condiciones **públicas de validación matemática**, NO observaciones ni ejecuciones K1 del mundo independiente. La muestra conserva dos controles sin saturación y trece casos estresados por capacidad, según la revisión Astra del PR #106.

## Contraste y límites de conclusión

El futuro CSV nativo se examinará al menos para: columnas de los stocks esperados, `accepted`, `delivered`, `time`; continuidad temporal, no-negatividad, entregas acumuladas monótonas; conservación `accepted = delivered + Σ stocks`; igualdad de `accepted` con el pulso público; seis tiempos exactos; y diferencia nativa-vs-surrogado ≤0.05 pedidos. Material se comprueba con tolerancia de validación **0.02 pedidos**, separada de la comparación de salida.

Un simple script que copia seis números del integrador puede pasar el **criterio aritmético**, pero **no** cuenta como una ejecución nativa: no tiene `.attempt`, solver, log, CSV ni hash del modelo OMC correspondiente. **Aun con esos artefactos**, un recibo local de CI prueba ejecución operativa verificable, **no** testimonio externo G5 ni equivalencia global sobre todos los 182 candidatos. El tag Docker `openmodelica/openmodelica:v1.26.5-minimal` y el ID de imagen resuelto se registran, pero el tag por sí solo no es un digest inmutable pre-registrado.

La pareja de integradores **no es un patrón de verdad empírica**. Un PASS nativo prueba correspondencia numérica para el subconjunto, parámetros, pulsos y muestras examinadas, incluyendo saturación; no identifica la verdadera estructura de una cafetería ni acredita una mejora K2 independiente. Un FAIL conserva todas las trazas, consume el intento declarado y **no autoriza ajustar tolerancia ni reintentar por conveniencia**.

## Ejecución: presupuestos y orden

La verificación `checkModel` **no consume** simulaciones. Después, el workflow de ejecución puede gastar como máximo **15 invocaciones de simulación**: 12 M y 3 D. Cada llamada escribe `INVOCATION_STARTED` **antes** de llamar a `omc`; fallos o salidas incompletas consumen el intento, y no se reparan con nuevas llamadas. **El workflow utiliza un segundo contenedor con red cerrada para ejecutar el solver**; el Docker tag se descarga antes.

Esto solo se aplica a la fase G2, que se realiza **antes de conocer el nuevo K0 privado**. La política CAF-02 continúa `DRAFT_FOR_REVIEW_NOT_FROZEN_NOT_AUTHORIZED`; la fuente DES no se crea ni se ejecuta, no hay firmas G5/G4a/G4b, K2 permanece reservado y D no puede declarar ATMS persistido. Quedan fuera del alcance las familias B y cualquier búsqueda general de topologías.
