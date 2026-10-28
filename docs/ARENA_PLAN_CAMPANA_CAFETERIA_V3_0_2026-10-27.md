# ARENA · Plan de campaña de diagnóstico de cafetería

**Versión documental:** 3.0. **Fecha local:** 27 de octubre de 2026, America/Mexico_City.  
**Corte consultado:** 28 de octubre de 2026 UTC; `main` en `6f0ba57d175c10d31f762237287cb1e79cdaea41`, posterior al PR #70.  
**Estado:** plan de una campaña nueva; experimentos, resultados e implementación pendientes.  
**Objeto:** transferencia a un caso nuevo, discriminación y revisión de mecanismos, y utilidad de la memoria existente.  
**Destino de producto:** diagnóstico comprensible de pequeñas empresas, comenzando por una cafetería.  
**Documento relacionado:** [Brief de opciones de implementación](ARENA_BRIEF_ASTRA_OPCIONES_IMPLEMENTACION.md).

Este documento ordena el trabajo científico siguiente. La campaña v2.0 queda cerrada en el alcance de sus primeros cortes. Sus protocolos y resultados permanecen vigentes para sus respectivos experimentos; no se reabren R1–R5. La numeración 3.0 es documental, no una versión de software.

La autorización actual comprende redactar este plan. No comprende implementar el producto, ejecutar simulaciones, realizar inferencias, crear workflows de ejecución o publicar cambios. La selección entre las alternativas de implementación del brief se resolverá después con los resultados pertinentes.

## 1. Decisión y pregunta principal

El siguiente experimento debe responder:

> Ante una cafetería que acumula pedidos, ¿ARENA puede conservar explicaciones rivales, anticipar el efecto de una intervención y producir un diagnóstico que aporte algo frente a un análisis convencional con la misma información?

La unidad inicial será un proceso operativo de preparación y entrega de pedidos. Se estudiará una congestión delimitada, con unidades y fronteras explícitas. La primera entrega no abarcará el diagnóstico financiero integral, todas las recetas, el aforo y la reposición simultáneamente.

El trabajo comienza por **un caso de transferencia**. Después se estudia una revisión ante evidencia nueva y, en un caso distinto, el aporte de la memoria. Los resultados negativos cierran cada experimento si son interpretables; no se encadenan ajustes hasta obtener éxito.

### Regla para cualquier cambio

No se recomendará un cambio arquitectónico sin una prueba concreta que la arquitectura actual sea incapaz de superar. La prueba debe identificar entrada, operación requerida, comportamiento observado y criterio de aceptación. Antes de atribuir el fallo a la arquitectura se distinguirán datos, parámetros, búsqueda, hipótesis, adaptación, simulador y representación.

Las nuevas piezas del experimento se limitarán a lo necesario para formular esa prueba: contrato del caso, fuente evaluadora, comparación y lectura de resultados. Se reutilizarán controles y memoria existentes. Un generador independiente de datos es un instrumento experimental, no un cuarto brazo ni un sustituto de OpenModelica.

## 2. Punto de partida comprobado

| Corte | Resultado heredado | Consecuencia para esta campaña |
|---|---|---|
| R2 / PT-05 | D conservó seis alternativas; M mantuvo abstención; Buffalo produjo una revisión ejecutable con estímulo divergente. Memoria temporal reconstruida con ledger/ATMS. | Hay rutas y resultados propios por brazo. Debe comprobarse la fidelidad al estímulo del nuevo caso antes de comparar errores. |
| R3 / PT-06 | T1 y T3: abstención; T2: tres estructuras compatibles. La grilla finita no resolvió todos los desplazamientos paramétricos. | Conjunto vacío no identifica por sí solo la causa del fallo; conservar límites de búsqueda y alternativas. |
| R4 / PT-07 | En T2, una observación posterior redujo tres estructuras a C01, con tres configuraciones supervivientes. Error agregado 0.007952 frente a 0.074986 de REF. | Existe evidencia positiva de discriminación prospectiva en un caso sintético intrafamilia. Falta medir transferencia a otra fuente y utilidad frente a una referencia operativa pertinente. |
| R5 / PT-08 | Clef no superó el filtrado conservador en tres tratamientos del mismo caso. El cierre declara reconstrucción posterior de respuestas, no captura cruda independiente previa a calificar. | El piloto queda cerrado. Clef no se incorpora como filtro irreversible; Clairic no es requisito de esta campaña. |

La documentación y los scripts experimentales existen. Su disponibilidad no demuestra que sean interfaces generales para cualquier cafetería. La preparación comprobará únicamente las rutas necesarias para el caso elegido.

Fuentes fijadas al corte: [R2](https://github.com/yudocyudoc/IGC/blob/6f0ba57d175c10d31f762237287cb1e79cdaea41/docs/ARENA_R2_PT05_CIERRE_TRES_BRAZOS_2026-10-27.md), [R3](https://github.com/yudocyudoc/IGC/blob/6f0ba57d175c10d31f762237287cb1e79cdaea41/docs/ARENA_R3_PT06_CONSOLIDACION_T1_T2_T3_2026-10-27.md), [R4](https://github.com/yudocyudoc/IGC/blob/6f0ba57d175c10d31f762237287cb1e79cdaea41/docs/ARENA_R4_PT07_T2_REAL_PROSPECTIVE_RESULT_2026-10-28.md), [R5](https://github.com/yudocyudoc/IGC/blob/6f0ba57d175c10d31f762237287cb1e79cdaea41/docs/ARENA_PT08_CLEF_SEIS_PARES_REALES_RESULTADO_2026-10-28.md).

## 3. Capacidades que se medirán por separado

| Capacidad | Evidencia requerida | Conclusión que debe evitarse |
|---|---|---|
| Cálculo operativo correcto | Conteos, unidades, balances y métricas reproducibles. | Presentarlo como descubrimiento de un mecanismo. |
| Transferencia predictiva | Predicción congelada de una condición nueva, contrastada con una fuente independiente de la construcción de candidatos. | Llamar validación de campo a otro experimento sintético. |
| Discriminación de mecanismos | Evidencia adicional que reduzca alternativas sin excluir injustificadamente las compatibles. | Confundir menor error con estructura causal única. |
| Revisión estructural | Cambio explícito de estados, conexiones o ley de flujo, motivado por evidencia propia y evaluado después. | Llamar revisión estructural a cambiar únicamente capacidades o tiempos. |
| Utilidad de memoria | Comparación del mismo método con y sin acceso a conocimiento previo permitido, en un caso nuevo. | Inferir aprendizaje porque el ledger guarda correctamente una decisión. |

**Precisión de dominio:** preparación lenta y despacho lento pueden pertenecer al mismo grafo y diferir solo en parámetros. La localización de ese cuello de botella es útil, pero no basta para demostrar inferencia estructural. Un contraste estructural debe explicitar, por ejemplo, la presencia de una etapa adicional de espera o una dependencia de flujo diferente. El nombre comercial de la etapa no define su identidad científica.

## 4. Contrato mínimo de la cafetería

### 4.1 Frontera inicial

Se propone comenzar con una sola clase de pedido equivalente, desde aceptación hasta entrega. La agregación debe declararse: este primer caso no representa automáticamente una mezcla de bebidas con recetas y recursos distintos. Tiempo en minutos; cantidades en pedidos; tasas en pedidos/minuto. Cualquier conversión de los experimentos históricos se hará explícita.

Datos de construcción mínimos:

- Perfil temporal de pedidos aceptados y conteos de entregas.
- Pendientes al inicio y al final del periodo, cuando estén disponibles.
- Horarios y cambios operativos que el dueño realmente conocería.
- Resolución de muestreo, unidades, faltantes y condiciones de medición.
- Restricciones conocidas de equipos o personal, separadas de capacidades inferidas.

Con esos datos se pueden calcular balances y tasas agregadas. Los tiempos individuales de espera requieren marcas de tiempo por pedido u otra medición adecuada: no se inventarán a partir de dos conteos. Si hay cancelaciones o pérdidas, deberán representarse como salidas explícitas; de otro modo el balance queda incompleto.

Los tiempos internos, capacidades desconocidas y existencia de etapas no observadas forman parte de las hipótesis. No se entregarán al productor bajo etiquetas que revelen la solución.

### 4.2 Fuente evaluadora

La opción inicial propuesta es una cafetería sintética con implementación independiente del compositor, plantillas y bibliotecas E1 usadas por los candidatos. Podrá conservar el mismo contrato físico de conteos y flujos. El protocolo describirá qué ecuaciones, supuestos o datos siguen compartidos; cambiar el lenguaje de programación no basta para acreditar independencia conceptual.

Para el primer caso conviene mantener una semántica de agregación compatible con los observables de los brazos. Si se elige una simulación de eventos discretos o se introduce variabilidad aleatoria, se fijarán agregación, semillas y error de muestreo antes de evaluar. No se atribuirá automáticamente al mecanismo un desajuste causado por otra escala temporal o por discreción.

Una fuente real puede sustituir esta opción si ya existe un conjunto utilizable con condiciones bien documentadas. No se inicia una integración POS ni captura masiva para obtenerlo. La investigación de campo y cualquier intervención sobre una operación real requieren su propio diseño posterior.

### 4.3 Separación de información

El expediente distinguirá construcción, observación adicional, evaluación posterior y datos del generador. Los brazos recibirán la misma información pública permitida y su propio feedback. Las etiquetas de verdad se usarán únicamente para adjudicación posterior.

Si el investigador o el agente puede reconstruir el generador, se declarará separación procedimental y posible conocimiento previo. Un hash o una carpeta no convierten ese caso en una reserva ciega. Los ejemplos usados para desarrollar el protocolo no se presentarán después como validación nueva.

## 5. Métodos y comparación convencional

Se conservan D, B y M con sus salidas nativas y sus adaptadores. El propósito es medir qué puede hacer cada uno ante la misma pregunta. Ningún brazo deberá producir a la fuerza un candidato; una limitación de representación o una abstención son resultados explícitos.

| Método | Papel en el ensayo | Condición de comparación |
|---|---|---|
| D | Hipótesis y predicciones desde sus reglas y modelos propios. | Repertorio, parámetros y política declarados. |
| B / Buffalo | Propuesta nativa y, cuando corresponda, una revisión con evidencia propia. | Estímulo, unidades y ecuaciones fieles al contrato; sin reparación del evaluador. |
| M | Composición y búsqueda dentro del repertorio molecular declarado. | Separar estructura, parámetros probados y configuraciones no exploradas. |
| REF-CAF | Análisis convencional reproducible: balance de pedidos, tasas, restricciones conocidas y una regla sencilla de pronóstico. | Misma información, calibración solo en construcción y regla congelada antes de evaluar. |

REF-CAF debe ser una alternativa razonable para el problema, no únicamente persistencia si los datos permiten estimar algo mejor. En preparación se elegirá y documentará una sola referencia principal, con sus supuestos y tratamiento de faltantes. Puede implementarse como hoja de cálculo o código equivalente. Si coincide con una subfamilia de D, se declarará esa coincidencia.

Todos los métodos entregarán, en un formato breve: observaciones que utilizan, hipótesis compatibles, incertidumbres, predicción, siguiente medición sugerida y límites del diagnóstico. La comparación no premiará extensión narrativa ni cantidad de diagramas.

## 6. CAF-01 · Primer caso de transferencia

**Pregunta:** ¿los modelos construidos con la operación inicial anticipan una condición distinta de demanda?

1. Congelar el contrato del caso, fuente independiente, información publicada, límites paramétricos y presupuesto. Preparar un periodo de demanda variable que pueda producir acumulación de pedidos, sin publicar el mecanismo generador.
2. Entregar únicamente construcción. D/B/M y REF-CAF producen sus diagnósticos y predicciones según sus políticas. Los parámetros inferidos se identifican como estimaciones; los supuestos no se presentan como mediciones.
3. Comprobar unidades, balance, fidelidad del estímulo y posibilidad de simular. Un candidato que modela otra entrada no participa en el ranking predictivo común; su fallo queda registrado.
4. Congelar modelos y una intervención común predeclarada sobre la entrada: por ejemplo, un cambio de ritmo de llegadas. Precisar inicio, duración, perfil y condiciones iniciales. No cambiar al mismo tiempo capacidad, estructura y demanda.
5. Obtener la respuesta evaluativa y comparar, sin reajuste, trayectoria de entregas y pendientes. Comparar también con REF-CAF.
6. Emitir un diagnóstico comprensible: qué se sostiene, qué sigue ambiguo y qué dato faltaría. Publicar el resultado incluso si la referencia convencional iguala o supera a los brazos.

El protocolo deberá decidir si se evalúa un nuevo tramo que continúa el estado anterior o un escenario que reinicia desde un estado conocido. Esas dos operaciones no se mezclarán. No se rellenarán estados internos desconocidos con los del generador reservado.

**Salida mínima:** un caso nuevo evaluado, con denominadores completos de intentos y límites de interpretación. Un resultado favorable solo acredita transferencia para ese caso y esa intervención. Cambiar las llegadas prueba respuesta predictiva a esa perturbación; no valida automáticamente decisiones sobre contratación, equipos o inversión.

## 7. CAF-02 · Discriminación y revisión ante evidencia nueva

**Pregunta:** cuando la información inicial admite mecanismos distintos, ¿el sistema pide evidencia pertinente y revisa su explicación de manera comprobable?

Este caso se diseña después de cerrar CAF-01, con parámetros o configuración diferentes. Antes de ejecutarlo se precisarán las clases materiales comparables entre brazos. No se juzgará a Buffalo por tener distinto número de variables si sus mecanismos observables son equivalentes.

La secuencia tiene tres cortes:

| Corte | Información disponible | Trabajo permitido |
|---|---|---|
| K0 · Construcción | Señales iniciales limitadas. | Proponer, ajustar en construcción, conservar alternativas y justificar una medición. |
| K1 · Evidencia adicional | Una medición o intervención elegida mediante una regla publicada antes de conocer su resultado. | Revisar parámetros, estructura o confianza, o abstenerse. Registrar el cambio y su soporte. |
| K2 · Evaluación nueva | Respuesta no usada en K0/K1, obtenida después de congelar la revisión. | Puntuar las predicciones anteriores y revisadas; no volver a ajustar. |

Se declarará un menú pequeño de mediciones factibles, por ejemplo acumulación en un punto intermedio o tiempos de paso medidos. Los métodos podrán justificar una elección. El experimento ejecutará una sola opción común seleccionada con una regla predeclarada; los brazos reciben el mismo resultado, sin recibir las propuestas privadas de sus rivales. Si solo se ejecuta una opción, no se proclamará que es mejor que todas las alternativas no medidas.

La ambigüedad inicial y la contradicción posterior son condiciones de diseño deseadas, no resultados garantizados. Si no aparecen, se registra que el caso no activó la pregunta prevista. No se modifica el mundo después para fabricar una revisión exitosa.

El informe distinguirá:

- **Revisión paramétrica:** cambia un tiempo, tasa o capacidad dentro del mismo mecanismo.
- **Revisión estructural:** cambia un estado relevante, una conexión o una dependencia funcional.
- **Revisión epistémica:** mantiene varios mecanismos, reduce confianza o se abstiene.
- **Corrección técnica:** resuelve traducción o formato; no cuenta por sí sola como revisión científica.

**Salida mínima:** linaje K0→K1→K2 y evaluación posterior de la revisión. Mejorar el ajuste a K1 no basta para declarar mejora predictiva. Para comparar la versión anterior y la revisada se usarán el mismo escenario K2 y condiciones iniciales permitidas, con ambas predicciones registradas antes de recibir la respuesta K2. No se exige que todos los brazos revisen ni que la revisión resulte favorable.

## 8. CAF-N · Control negativo de diagnóstico

Se preparará una copia identificada de un caso, retirando una medición necesaria para una conclusión concreta. Por ejemplo, conservar ventas por periodo pero omitir los tiempos individuales requeridos para estimar esperas. La salida admisible mantiene los cálculos identificables y declara qué no puede concluirse.

Este control prueba ausencia de afirmaciones injustificadas; no se contabiliza como un mundo independiente ni como evidencia de transferencia. Puede reutilizar la fuente ya generada y no requiere por sí mismo otro solver. Su orden de presentación y aislamiento deben evitar que el método recupere de memoria el campo retirado.

Si se incluye además un dato físicamente inconsistente, se calificará por separado como detección de inconsistencia. No confundir información insuficiente con evidencia contradictoria. Se aprovecharán validaciones existentes; este paquete no abre una campaña de auditoría general.

## 9. MEM-CAF · Utilidad experimental de la memoria

**Pregunta:** ¿el acceso al conocimiento previo permitido mejora la investigación de otro caso de cafetería?

Se ejecutará después de disponer de al menos un expediente anterior pertinente. El caso objetivo será nuevo: no una repetición con otro nombre del caso cuya respuesta ya figura en memoria. No se presupone una mejora.

Primer contraste propuesto: un único método consumidor, preferentemente M si puede utilizar la memoria existente sin reorganizar la arquitectura. Antes de activarlo se deberá señalar la decisión concreta que la memoria puede afectar: orden de exploración, propuesta de medición o revisión de una hipótesis. Si el método solo escribe al ledger y nunca consume su contenido, el contraste aún no está conectado.

| Condición | Información del caso objetivo | Acceso histórico |
|---|---|---|
| C0 | Construcción y nuevas observaciones comunes; feedback propio bajo reglas fijadas. | Sin recuperación de casos anteriores. |
| C1 | La misma construcción, observaciones y reglas de feedback. | Un conjunto previo, congelado y autorizado para ese brazo. |

Ambas condiciones tendrán la misma versión, repertorio, límites paramétricos, presupuesto total y criterio de parada. Si producen modelos distintos, sus residuos y errores propios pueden diferir; se conserva la misma regla para producir feedback, sin trasladar el diagnóstico privado de una condición a la otra. La recuperación consume parte del presupuesto de C1. Se cambiará solo el acceso a la memoria; una mejora que también cambie motor, prompt general o espacio de búsqueda requeriría otra comparación.

El histórico podrá incluir resultados negativos y revisiones previas con su alcance. Una hipótesis rechazada en otro caso no se convierte en una prohibición universal. No se transferirán etiquetas `case-private`, verdad del nuevo generador ni propuestas privadas de otro brazo. Una experiencia anterior tampoco se incorporará como observación de la cafetería objetivo.

Se medirá: calidad de predicción nueva, exclusiones injustificadas, repetición de errores conocidos, número de propuestas y simulaciones realmente ejecutadas, y costo de recuperación. La búsqueda incompleta se declarará: no explorar una configuración no equivale a refutarla.

Si se emplean CSV ya calculados, la diferencia de orden o evaluaciones será un ahorro potencial de búsqueda, no ahorro físico realizado. Si el consumidor es estocástico, un par será exploratorio; cualquier repetición se fijará por adelantado y no se elegirá la mejor muestra.

**Salida mínima:** efecto observado o ausencia de efecto atribuible al acceso histórico bajo esas condiciones. Un resultado nulo no implica que ATMS falle como sistema de soporte lógico. Si el acceso correcto perjudica el diagnóstico, se conserva ese resultado y se examina la política de uso antes de ampliar almacenamiento o recuperación.

## 10. Evaluación y criterios de aceptación

Los umbrales se fijarán antes de observar evaluación, a partir del contrato de medición y del objetivo del diagnóstico. No se heredará automáticamente el límite histórico de 0.020 items para pedidos medidos en otra escala. Si la tolerancia es operacional, se identificará así; una banda de candidatos no es un intervalo probabilístico.

| Dimensión | Medida principal | Criterio de interpretación |
|---|---|---|
| Fidelidad | Entrada aplicada, unidades, frontera y condiciones iniciales. | Comparar bajo el mismo experimento; declarar desviaciones. |
| Ejecución | Propuestas recibidas, traducidas, simuladas y abstenciones. | Publicar todos los intentos; no puntuar únicamente supervivientes como si fueran el total. |
| Predicción | Error en entregas/pendientes por ventana; error de efecto de la intervención cuando esté definido. | Puntuar después del congelamiento y con la misma agregación para REF-CAF. |
| Incertidumbre | Alternativas conservadas, exclusiones incorrectas y observaciones no explicadas. | Un conjunto pequeño no es mejor si elimina mecanismos compatibles. |
| Estructura | Cambios de mecanismo frente a cambios de parámetros. | Identificación acotada al repertorio y a lo observable. |
| Diagnóstico | Cada afirmación vinculada a dato, cálculo, hipótesis o resultado evaluativo. | Se reconoce qué falta medir; no se confunde relato con evidencia. |
| Memoria | Diferencia C1−C0 en calidad y costo. | Mismo caso objetivo y condiciones; acceso histórico como factor estudiado. |
| Utilidad práctica | Claridad, viabilidad de la medición y utilidad percibida por un usuario objetivo, si participa. | Sin usuario objetivo, informar revisión técnica de comprensibilidad, no usabilidad validada. |

Una reducción del error de construcción no demuestra transferencia. Una etiqueta sintética acertada no demuestra causalidad externa. Si varias formulaciones producen las mismas consecuencias observables, se conservará la clase de equivalencia pertinente.

## 11. Secuencia de trabajo y presupuestos

| Paquete | Entrega | Condición de cierre |
|---|---|---|
| PC-01 · Preparación | Contrato de cafetería, fuente propuesta, referencia convencional, disponibilidad de D/B/M y protocolo CAF-01. | Entrada, salida exigida, métricas y costo se pueden revisar antes de ejecutar. |
| PC-02 · Transferencia | CAF-01 y control CAF-N con sus resultados. | Contraste nuevo interpretable, favorable o adverso. |
| PC-03 · Revisión | CAF-02 con K0/K1/K2. | Se distingue lo revisado y se mide su consecuencia posterior, o se documenta por qué no hubo revisión. |
| PC-04 · Memoria | MEM-CAF sobre un caso diferente. | Comparación C0/C1 válida, o limitación concreta que impide atribuir utilidad. |
| PC-05 · Decisión de producto | Informe breve que conecta resultados con las opciones del brief. | Se identifica una primera utilidad demostrada, límites y una decisión de implementación o de no ampliación. |

PC-01 no debe convertirse en un inventario de todo el repositorio. Se examina la ruta del caso y se prepara el primer contraste. PC-03 y PC-04 se ajustarán a la evidencia anterior sin modificar sus resultados históricos ni presentar los casos de desarrollo como validación nueva.

### Contabilidad previa a ejecución

El protocolo de cada paquete tendrá un cuadro con cantidades máximas explícitas para:

- Mundos generadores, escenarios y realizaciones aleatorias.
- Candidatos D/M, propuestas B y revisiones permitidas.
- Ejecuciones de cada candidato por escenario, incluidas las usadas para escoger una medición.
- Simulaciones de REF si las requiere, llamadas a proveedor, entrada/salida máxima y tiempo límite.
- Condiciones de memoria, pruebas técnicas que consuman solver y regla de parada.

Para una lista de modelos y escenarios, el presupuesto físico se calculará como la suma de las ejecuciones necesarias por modelo, más generador, referencia y comprobaciones técnicas. «27 candidatos» no significa «27 ejecuciones» si cada uno se simula en varias condiciones. Se registrarán por separado propuestas inválidas, ejecuciones fallidas y reutilización de artefactos.

Este plan no fija una cifra ficticia antes de elegir el contrato y las políticas. Tampoco otorga presupuesto abierto: **ningún paquete queda listo para ejecución sin cantidades, versión y protocolo concretos**. Se comienza por CAF-01; los casos restantes no se lanzan en lote por aprobar este documento. La redacción y revisión actual consumen cero inferencias experimentales y cero simulaciones.

## 12. Reutilización técnica delimitada

Las rutas siguientes están presentes en el árbol del corte consultado. Son puntos de inspección y reutilización, no una certificación de adaptación a cafetería.

| Necesidad | Rutas existentes en `yudocyudoc/IGC` | Verificación puntual pendiente |
|---|---|---|
| Fuente y contrato | `scripts/arena_v0_contract.py`, `scripts/arena_v0_common_evidence.py` | Expresar nuevos observables sin cambiar su significado. |
| D | `scripts/arena_d_v01.py`, `scripts/arena_d_v1_screen.py`, `scripts/arena_d_v2_revision.py` | Política y modelos aplicables al contrato elegido. |
| B | `scripts/arena_b_openrouter_cloudflare.mjs`, `scripts/arena_b_native_to_modelica.py`, `scripts/arena_b_native_series.py` | Nuevo caso y revisión propios; alcance real del mapeo de series, sin forzar topologías nuevas. |
| M | `scripts/arena_m_short_e1.py`, `scripts/arena_r3_pt06_parametric.py`, `scripts/arena_m_visible_verify.py` | Repertorio, límites de búsqueda y adaptación de observables. |
| Pronóstico y evaluación | `scripts/arena_r4_pt07_t2_forecast.py`, `scripts/arena_r4_pt07_t2_score.py` | Reutilizar cálculo pertinente; separar dependencias fijas de T2. |
| Memoria | `scripts/ledger.py`, `scripts/arena_atms.py`, `scripts/arena_memory.py`, `scripts/arena_r2_memory_first_cut.py` | Consulta pertinente y consumidor efectivo; no confundir replay con servicio desplegado. |

Los scripts históricos conservarán sus protocolos. Si hay identificadores o supuestos fijos que impiden el nuevo caso, se documentará el fallo de contrato y se resolverá con una adaptación localizada cuando baste. Un fallo de traducción tampoco deberá contabilizarse como incapacidad científica del modelo nativo.

La persistencia guardará lo necesario para reconstruir decisiones y soportes, usando F1a/ATMS. No se abren ontologías, recuperación vectorial, concurrencia, nuevas bases ni interfaces generales sin una necesidad demostrada por la prueba.

## 13. Cómo se resolverá después el brief de producto

El brief conserva el destino: restricciones físicas, referencia operativa de cafetería y salud financiera integrada. Este plan produce evidencia para decidir el primer corte de ese producto.

| Resultado de la campaña | Decisión que habilita discutir |
|---|---|
| El análisis convencional ofrece el mismo diagnóstico útil con menos costo. | Empezar por cálculos y restricciones verificables; justificar cualquier simulación adicional por una pregunta específica. |
| Una plantilla dinámica acotada mejora predicción o elección de mediciones. | Examinar una plantilla modular para ese problema y delimitar su dominio. |
| Composición o revisión de mecanismos aporta una ventaja observable. | Examinar composición incremental donde esa ventaja exista, sin convertirla en requisito de todo cálculo. |
| La memoria aporta calidad o costo favorable sin descartes injustificados. | Incorporar ese uso concreto de memoria al flujo del producto. |
| El resultado es insuficiente o negativo. | Mantener la utilidad convencional comprobada y acotar la afirmación de producto; no ampliar componentes por inercia. |

La tabla no selecciona todavía A, B o C ni supone que sean excluyentes. Una mejora operativa no valida automáticamente un módulo financiero. Recetas, inventario, conciliación contable y escenarios de caja tendrán contratos y pruebas propios cuando se retome su implementación. Los antecedentes bibliográficos del brief se examinarán en esa etapa; este plan no afirma haber validado sus ecuaciones, licencias o interoperabilidad.

## 14. Decisiones de preparación pendientes

Estas decisiones corresponden a PC-01 y no requieren interrumpir la redacción del plan:

1. **Fuente del primer caso:** generador independiente propuesto o datos reales ya disponibles; precisar supuestos compartidos y separación efectiva.
2. **Contrato observable y mecanismos:** elegir resolución, duración, variables, clases de hipótesis y límites paramétricos justificables sin usar la verdad reservada.
3. **Referencia y perturbación:** fijar REF-CAF y una intervención común que permita evaluar una pregunta concreta con métricas predeclaradas.
4. **Presupuesto por fase:** completar cantidades y versiones, incluida cualquier revisión y simulación para seleccionar mediciones.
5. **Consumidor de memoria:** identificar en PC-04 qué método usa qué conocimiento previo y qué decisión puede cambiar, manteniendo igual el resto.

## 15. Entrega final y criterio de término

La campaña entregará un expediente por caso, una comparación con REF-CAF, el linaje de una revisión cuando ocurra, un contraste de memoria cuando sea ejecutable y una recomendación breve para retomar el brief. Los resultados se presentarán como demostrados, negativos o pendientes, con su alcance.

El cierre admite que ARENA conserve varias explicaciones, que un brazo falle, que la memoria no mejore el resultado o que el análisis convencional sea suficiente. No exige un ganador D/B/M ni una recuperación estructural forzada. Un paquete no ejecutado se marcará como pendiente o excluido con motivo; no se declarará probado.

La entrega inmediata siguiente a este documento es **PC-01: protocolo concreto del primer caso y comparación convencional**, cuando se retome el trabajo. La implementación del diagnóstico integral del brief se decidirá con evidencia sobre qué capacidad merece convertirse en producto.

## Referencias locales de continuidad

- [Hoja de ruta v2.0, conservada como antecedente](ARENA_IGC_HOJA_DE_RUTA_V2_0_2026-10-27.md).
- [Plan de implementación v2.0, conservado como antecedente](ARENA_IGC_ATMS_PLAN_IMPLEMENTACION_V2_0_2026-10-27.md).
- [Brief de opciones de implementación, pendiente de decisión posterior](ARENA_BRIEF_ASTRA_OPCIONES_IMPLEMENTACION.md).

Para el estado de lo ya ejecutado prevalecen los cierres R2–R5 enlazados en la sección 2 sobre los apartados de v2.0 escritos antes de esos resultados. Este documento organiza una campaña nueva y mantiene los históricos intactos.
