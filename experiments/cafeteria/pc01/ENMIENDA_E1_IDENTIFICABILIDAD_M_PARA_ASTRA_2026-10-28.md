# PC-01 / CAF-01 — Enmienda propuesta E1: identificabilidad de la grilla M

**Estado:** PROPUESTA PARA REVISIÓN DE ASTRA; no modifica ni congela contrato v0.3. **Rama:** `fix/caf01-m-capacity-identifiability-20261028`.

## Hallazgo y certificado

Para `BoundedQueue`, según `src/modelica/IGCMolecules.mo`, `release = min(maxThroughput, stock/responseTime)`. Con frontera sin pérdidas, estado vacío y 24/30 órdenes totales de construcción/evaluación, cada stock individual es no negativo y no supera 30. Preparación y despacho tienen `responseTime=0.5 h`; por tanto su liberación proporcional está acotada por 60 pedidos/h. En las tres estructuras C00/C01/C02, valores de capacidad 72 y 100 jamás restringen esas liberaciones. Son indistinguibles **dentro de cada estructura y bajo estas condiciones**, incluso con observación continua perfecta. La capacidad 20 puede llegar a restringir flujo, pero el certificado no demuestra que cada comportamiento singleton sea distinto de los demás.

**Resultado:** nueve configuraciones nominales; como máximo seis clases de comportamiento intraclase. Puede haber menos. No agrupar C00/C01/C02 entre sí por esta prueba. El certificado `caf01_m_equivalence.py` verifica supuestos del JSON v0.3 y se niega a certificar si éstos cambian. Su derivación también depende de que las conexiones nativas conserven material y de la fórmula exacta de la molécula; esto debe verificarse en preflight, y el certificado **no examina ni ejecuta Modelica**.

## Política propuesta de selección, agregación y abstención (G3; pendiente de aprobación)

1. **Antes de leer el holdout**: construir un manifiesto de equivalencia a partir de entradas públicas, contrato y código; archivar versión/SHA, prueba y membresía. Ninguna agrupación se decide usando D de evaluación. El grupo intraclase `[72,100]` representa **una sola conducta** por estructura; `[20]` permanece candidato distinto, sin presunción de identificabilidad.
2. **Selección por brazo**: M debe elegir usando **solo construcción**, con MAE de entregados como métrica primaria. Cada clase exacta tiene un representante canónico (menor capacidad: 72) para ejecutar y reportar; el empate entre clases no autorizadamente equivalentes se registra como conjunto de candidatos, no se resuelve mirando evaluación. D aplica sus tres topologías sin pérdidas y su búsqueda RK4 de construcción, con regla de desempate predeclarada; B propone a lo sumo un modelo, sujeto a paridad/adaptación. El comparador REF se calibra únicamente con construcción bajo sus reglas ya publicadas.
3. **Agregación**: No hay autorización para promediar predicciones nominales con pesos uniformes. Por defecto reportar **mejor clase por brazo** y conjunto de empates. Si se decide producir un agregado, sus pesos deben fijarse prospectivamente **por clase de comportamiento**, no por número de configuraciones, y registrarse con el pronóstico bloqueado. No inferir probabilidades bayesianas de una grilla arbitraria. No mezclar candidatos de diferentes estructuras solo por empate numérico.
4. **Abstención**: Si ningún candidato pasa puertas físicas/semánticas, devolver `NO_VALID_CANDIDATE`. Si dos o más clases compatibles son indistinguibles en observación de construcción, devolver `STRUCTURE_OR_PARAMETER_NOT_IDENTIFIABLE` respecto de esa distinción y conservar pronósticos alternativos. Si estos pronósticos difieren en evaluación y no existe regla congelada para seleccionar, **abstenerse de pronóstico puntual único**. Si son idénticos, puede publicarse la predicción compartida **sin** afirmar estructura única. CAF-N debe declarar explícitamente las propiedades no identificables bajo el enmascaramiento.
5. **Evaluación**: bloquear pronósticos por brazo, reglas de selección, series y presupuesto **antes** de liberar evaluación. Reportar MAE primario (seis tiempos), comparadores REF-CAF/REF-SCALE y métricas derivadas sin doble evidencia; reportar clases indistinguibles y costo efectivo por separado. No confundir empate de MAE con equivalencia de trayectoria, ni buena predicción con recuperación estructural.

**Precaución:** la regla de D y B arriba es un marco, no la especificación exhaustiva de sus desempates ni del umbral de empate. G3 no está cerrado; cerrar esos detalles usando solo datos públicos de construcción y sin resultados ocultos, con aprobación científica.

## Efecto sobre presupuesto y ejecución

El límite vigente sigue siendo **26 OM, 36 RK4, 2 DES, hasta 2 Buffalo** hasta que se apruebe una nueva contabilidad. Deduplicar `[72,100]` permitiría potencialmente ahorrar 3 corridas M en construcción y 3 en evaluación (M 18→12, total OM 26→20), pero **solo** tras preflight de igualdad entre la formulación analítica y los grafos nativos, y sin usar resultados ocultos para decidir. No ajustar cifras retrospectivamente ni afirmar ahorro realizado.

## Pendientes independientes no resueltos

- D: compilación/ejecución nativa de las tres topologías sin pérdidas, RK4↔OM y balance de stocks; respetar las 36 integraciones RK4 máximas.
- M: linter y horizonte nativo para C00/C01/C02 y verificación de conexiones/capacidades.
- B: traductor fuera de alcance G2; adaptación local G0/G1 sin alterar ecuaciones nativas; manejo tipado de grafos no exactamente 2 stocks/2 flows.
- DES: generador privado, orden de eventos, parámetros/topología sellados antes de construir, límite 2 mundos.
- G3: fijar desempates, equivalencia numérica, agregación y abstención de **todos** los brazos; después congelar con autorización explícita.

## Verificaciones locales reproducibles

```bash
python experiments/cafeteria/pc01/caf01_m_equivalence.py
python -m unittest discover -s experiments/cafeteria/pc01 -p 'test_caf01_m_equivalence.py' -v
python experiments/cafeteria/pc01/validar_pc01_v0_3_offline.py --tests
```

Estas pruebas son estáticas: no certifican ejecución CAF ni sustituyen revisión independiente de Astra.
