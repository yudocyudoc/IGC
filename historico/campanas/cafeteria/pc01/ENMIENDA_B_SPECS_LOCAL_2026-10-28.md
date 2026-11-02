# CAF-01 · Enmienda local B-SPECS-01 — Solo preparación

**Estado:** propuesta para Astra, no fusionada; no preinscripción congelada.

El adaptador de CAF-01 permite traducir una propuesta nativa Buffalo cuyo objeto `model.specs` declare exactamente `startTime=0`, `stopTime=2/3 h`, `dt=1/120 h`, `timeUnits=hour`, `integrationMethod=Euler`. Ningún otro horizonte ni integrador está autorizado. El traductor histórico **no se modifica** y todavía rechaza correctamente esos specs si se le llama directamente.

## Mecanismo y procedencia

El puente realiza una copia profunda del documento recibido, cambia **solo** `model.specs` en esa copia a los valores históricos (0–8 h, dt=0.125, Euler), y delega toda la traducción de fórmulas, stock-flow, uniflow y funciones gráficas al traductor original. Se verifica que, al retirar `specs`, original y copia coincidan exactamente. El informe conserva hashes del original, del cuerpo sin specs y de la copia de traducción, además de **ambas** configuraciones temporales con etiquetas inequívocas. La salida Modelica es traducción de ecuaciones; no ejecuta el solver ni prueba paridad de integración.

Este procedimiento depende de que los specs no sean reescritos dentro de las ecuaciones por el traductor heredado, propiedad inspeccionada en la implementación actual. **No** equivale a afirmar que el simulador Buffalo interpola `TIME`, búsquedas o Euler igual que OpenModelica: G0/G1 y paridad siguen condicionales. Antes de autorizar ejecuciones de CAF-01 habrá que reconciliar las diferencias en el límite de pulso y las salidas por tiempos exactos.

## Separación de errores de adaptación

El puente intenta usar `arena_b_native_series.resolve_roles` solo sobre la estructura de puertos material. Para el caso histórico dos stocks/dos flujos puede señalar `SHAPE_MAPPED_CSV_AND_DYNAMICS_UNVERIFIED`; **faltan aún las columnas reales CSV y la verificación física**. Si el grafo no tiene esa forma o es ambiguo devuelve `BLOCKED_SERIES_VIEW_NOT_PROVIDER_MODEL_FAILURE` con razón, sin convertirlo en fallo de traducción ni fracaso científico del modelo propuesto por Buffalo. No se extiende silenciosamente el mapper.

## Alcance del test

El fixture `fixtures/b_caf_local_synthetic_native.json` es **fabricado para probar ingeniería**, no generado por Buffalo, no es un mundo sintético DES y no aporta evidencia predictiva. El workflow reproduce pruebas negativas, genera un único modelo y ejecuta a lo sumo `checkModel` sin `simulate`. El número de llamadas al proveedor y de simulaciones de candidatos CAF-01 es **cero**.

Pendientes: comprobar paridad temporal y semántica del modelo real cuando exista una respuesta autorizada, ampliar visor solo con justificación local, selección G3, DES sellado y aprobación de presupuesto. No fusionar esto con PC-02.
