# RF-02H · Admisibilidad H_j y procedencia de parámetros sin evaluación G3

**Fecha:** 2026-11-03. **Base:** RF-02M / PR #142; evidencia fija A1 #41575917332, D G2 #41589895721 y M G2 #41591727790.  
**Ámbito:** auditoría **solo lectura**, O0, datos POS sintéticos publicados, 12 CSV históricos. Sin nuevos DES, OpenModelica, servicios externos, gasto, puntuación, comparación de rendimiento ni consulta de FULL/holdout.

**Decisión operativa:** continuar implementando sin pedir aprobación a Astra por cada PR. Los tests automáticos certifican solo los **invariantes comprobables de ingeniería**. La admisibilidad científica y cualquier G3 permanecen bloqueadas, a resolver en una revisión de hito que incluya contrato semántico y parámetros.

## 1. Por qué el hito es necesario

La Arena ya puede ejecutar **6 estructuras D** y **6 composiciones Short E1** con una misma señal causal de llegadas. Pero esto NO significa que ambas hayan inferido por separado la explicación de la cafetería. D usa parámetros de fixture no empírico; M utiliza parámetros fijos y roles obligatorios del registro original. D admite pérdida; M del registro base no modela la misma pérdida sin una justificación adicional.

Por tanto, la prueba de conservación material **G2 de ingeniería** no autoriza puntuación G3 ni que un RMSE menor implique un método mejor. El objetivo de RF-02H es evitar esa promoción indebida de una evidencia de ingeniería a una afirmación científica.

## 2. H_j: qué sí acredita la auditoría

La herramienta `scripts/arena_cafe/r2_hj_parameter_gate.py` descarga y **vuelve a verificar** los manifiestos y los doce CSV originales mediante los verificadores de D y M ya ejercitados. También comprueba el reporte de cada G2 contra su recomputación, la identidad de las seis candidatas por brazo, los hashes de los CSV y el **hash idéntico de la señal causal** con entrada de 15 creaciones POS. Ninguna simulación se repite.

Para la magnitud *entregas acumuladas*, comprueba por cada candidato:

| Elemento | D original | M original |
|---|---|---|
| Columna nativa | `delivered` | `deliveredTotal` |
| Significado de implementación | Stock acumulado de entregas | Estado acumulado del `DeliveryCounter` |
| Unidad nativa de tiempo | Minutos | Horas |
| Unidad común después del operador | Minutos | Minutos (conversión ×60) |
| Unidad de cantidad | Pedidos | Pedidos (interpretación del flujo `Shipment` propuesta) |
| Verificación | Monótono, no negativo, valor inicial 0, ventana [0,10], CSV autenticado | Igual |
| Aptitud científica de la medición | **NO ESTABLECIDA** | **NO ESTABLECIDA** |

Lo validado es un **operador tipado de ingeniería** de salida acumulada, no correspondencia real de mecanismos ni precisión de predicción. El expediente no extrae valores previstos, residuales, rankings ni puntuaciones de las curvas; solo sus hashes, forma, unidades y procedencia.

Se excluyen explícitamente: creaciones POS como puntuación (son entrada); `orders-created − delivered` como WIP (D puede perder material y la entrada causal puede estar diferida); `inTransit` de M como WIP total (incluye solo `STATE<Shipment>`, no preparación/despacho); y `reportedDeliveryRate` como entregas materiales (es una señal de información).

Los observables O1 de preparación, espera y servicio **NO** se incorporan en esta corrida O0, ni se convierten por decreto en el parámetro `responseTime`. El uso de O1 requerirá operador propio, correspondencia semántica y ausencia de fuga por condición.

## 3. Parámetros: tres estados y ninguna importación clandestina

**D-B:** el ensayo G2 usa `capacity=1.23 pedidos/minuto, response_time=2.7 minutos, loss_time=8.1 minutos`, atribuidos al **fixture no empírico de conformidad**. El nuevo auditor exige el hash exacto de ese fixture y los valores/procedencia del manifiesto verificado. No se trata de estimaciones del POS, y **no son admisibles como calibración EV-01**. El generador original D no los infirió.

**M/Short E1:** la auditoría verifica el registro `registry.base.json` fuente y sus valores por rol, incluidas preparación/despacho/tránsito y reporte, sin cambiar los seis AST ni seleccionar el más simple. Es un prior preexistente con uso válido de ingeniería, **no una estimación observacional**. Se preserva la diferencia entre un prior original legítimo y un parámetro aprendido de la evidencia.

**B/Buffalo:** el método nativo EV-01 todavía no ha realizado una inferencia real ni tiene candidato y parámetros verificables. Los runs Cloudflare anteriores de otros experimentos no pueden heredar evidencia EV-01.

Ningún parámetro se copia entre métodos. No se realiza estimación, inferencia por curva observada o optimización numérica en esta entrega.

## 4. Nueva compuerta: ingeniería aprobada, ciencia bloqueada

El archivo `HJ_PARAMETER_GATE.json` incluye doce candidatas con sus operadores tipados, los hashes de origen de los dos reportes G2 y cinco bloqueantes:

1. Falta aprobar la equivalencia semántica científica de la magnitud y de los operadores H_j.
2. Falta política prospectiva de parámetros **independientes** para D-B, o abstención explícita de simulación científica cuando no existan.
3. M solo tiene priors fijos originales, no parámetros calibrados para EV-01; el alcance debe declararse sin obligar al método a tener un estimador que no posee.
4. Falta la generación nativa real de Buffalo para EV-01, con autorización de coste separada.
5. Falta un protocolo prospectivo de G3 que separe datos de construcción de evaluación y no seleccione oportunistamente candidatos ni anchuras temporales.

**Resultado esperado correcto:** `Hj_D_M_engineering_operator=PASS` y `Hj_scientific_semantic_equivalence=NOT_ESTABLISHED`, `G3/G4/G5=NOT_RUN`, `A3=PARTIAL`, `decision=BLOCKED_G3_NEEDS_SCIENTIFIC_ADMISSION`.

Si un control de hash, origen, unidad, tiempo, csv, cantidad de candidatas, parámetro o condición falla, la CI termina FAIL. No se promueve la evaluación con un default tolerante.

## 5. Régimen de revisión más ágil

- Cada avance de código se revisa por CI y tests negativos; evidencia preservada en artefactos.
- No se solicita dictamen independiente por micro-PR, ni se cambia G3 como efecto de una CI verde.
- La revisión externa se concentra cuando exista una propuesta suficientemente madura de **operador semántico, política de parámetros y diseño prospectivo de G3**. Ese hito es el que puede modificar una conclusión científica.
- No se fusionan los PR apilados en `main` mientras el circuito de despliegue/revisión de integración permanezca sin aprobar; sí se pueden seguir desarrollando capas aditivas por CI.

**Limitación de procedencia:** hashes de archivo y marcadores del job acreditan continuidad dentro del sistema de artefactos de GitHub y fuentes fijadas, **no equivalen a firmas criptográficas independientes ni prueban OS/ACL**. La separación fuerte de condiciones y de acceso a evidencia reservada sigue pendiente de R6.
