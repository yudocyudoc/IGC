# IGC · Hoja de ruta de la Arena y del laboratorio sistémico

**Versión documental:** 2.0 · **Fecha:** 27 de octubre de 2026, America/Mexico_City.  
**Corte verificado:** `IGC/main@f07d94c9109bbbb77264509bf7ed04d6aead9cba`, posterior a los PR #52, #53 y #54. Recuperación y primera ronda de intentos D/B/M cerradas; R2 pendiente.  
**Estado:** hoja de ruta para ejecutar desde el corte actual. Los hitos futuros son trabajo propuesto; no capacidades certificadas ni autorización de gasto. La versión 2.0 pertenece a estos documentos, no a una versión publicada del software.  
**Documento operativo compañero:** [Plan de implementación v2.0](ARENA_IGC_ATMS_PLAN_IMPLEMENTACION_V2_0_2026-10-27.md).

## 1. Decisión principal

La prioridad es completar y someter a prueba el ciclo **evidencia → hipótesis independiente → simulación propia → contraste → revisión**, usando D/B/M y la memoria ATMS que ya existen. No corresponde volver al inicio del plan v1.1 ni abrir una nueva fase extensa de controles, índices o auditorías.

La primera ronda común ya se intentó: D y M produjeron trayectorias; Buffalo produjo un modelo que OpenModelica no pudo construir. El siguiente paso es **R2: revisión de ese modelo con su propio feedback y persistencia de las decisiones D/B/M**, conservando el resultado negativo inicial. No repetir R1 para obtener una propuesta favorable.

El objetivo científico es averiguar si IGC ayuda a identificar, conservar, cuestionar y revisar mecanismos que explican comportamiento dinámico. Compilar Modelica, conservar hashes o resolver dependencias lógicas son capacidades necesarias, pero no contestan por sí solas esa pregunta.

**Regla rectora del investigador:** no recomendar un cambio arquitectónico sin identificar primero una prueba concreta que la arquitectura actual sea incapaz de superar. Un resultado adverso de un modelo, una mala estimación o una abstención no demuestran automáticamente esa incapacidad.

## 2. Por qué v1.1 ya no puede dirigir el trabajo inmediato

| Aspecto | Lectura de v1.1 que quedó superada | Dirección actual |
|---|---|---|
| Productores | Vías D/S/P; D combina determinismo y moléculas | Tres métodos separados: D determinista, B Buffalo, M molecular |
| Traducción | Tendencia a converger en el compositor molecular | Cada método conserva su salida nativa y su propio adaptador a OpenModelica |
| Plataforma | Implementación amplia de ATMS, semántica e índices como prioridades centrales | Conectar la memoria mínima al experimento; ampliar servicios solo ante una necesidad demostrada |
| Estado inicial | Prototipos y piezas pendientes de recuperación | Rutas avanzadas recuperadas y R1 intentado; faltan revisión y memoria conjunta |
| Evidencia científica | Inferencia estructural todavía prácticamente sin ensayar | M3, B4/B5, M3-P y R1 aportan resultados acotados; no prueban identificación general |
| Clef/Clairic | P como vía de la arquitectura inicial | Clef experimental después del contraste D/B/M; Clairic con evaluación específica de extracción |
| Siguiente entrega | Más infraestructura integral | Revisión Buffalo desde R1 y segunda decisión trazable de cada brazo |

Se conservan de v1.1 el ledger bitemporal, ATMS como memoria constitutiva, la procedencia, la distinción entre soporte y verdad, la independencia y la separación entre construcción y evaluación. Las versiones v1.1–v1.3 permanecen como historia; el [plan v2.0](ARENA_IGC_ATMS_PLAN_IMPLEMENTACION_V2_0_2026-10-27.md) reemplaza sus instrucciones operativas incompatibles y establece qué decisiones siguen y qué tareas cambian de prioridad.

## 3. Punto de partida: qué está disponible y qué falta

| Capacidad al corte | Evidencia disponible | Trabajo pendiente |
|---|---|---|
| D autónomo | Generación stock-flow y política D2; seis candidatos propios simulados en R1, mínimo RMSE 0.150205 items | Segunda decisión ante sus trazas y eventual ensayo adicional declarado |
| Buffalo original | Ensayos B2–B5; en R1, una llamada real y un modelo de 17 variables con G1 negativo | Revisar el padre R1 con su propio fallo; no reutilizar padres históricos ni repetir la inferencia inicial |
| Molecular | Short E1, M1/M2, selector M3, M3-P y tres candidatos comunes simulados | Registrar segunda decisión y evaluar separación estructura/parámetros |
| Evaluación común M3 | Mejor RMSE 0.316560 items, superior al umbral nativo 0.020; abstención | Conservar abstención; investigar la política paramétrica en una condición nueva |
| Memoria | Ledger, ATMS, soporte alternativo, recuperación léxica/FTS5 y vistas D/B/M | Persistir y consultar el ciclo real de los tres brazos; el puente D no equivale a un puente conjunto ya terminado |
| Discriminación | Pulsos separan D2/M2 y B2/B3 congelados | Obtener una observación evaluativa que permita contrastar las predicciones |
| Clef | Piloto numérico y semántico ejecutado | Prueba de utilidad incremental, si se alcanza el hito correspondiente |
| Clairic | Aritmética y pronósticos pequeños, con resultados mixtos | Evaluación de extracción sobre fuentes que el proyecto necesite realmente leer |

El [workflow de recuperación](https://github.com/yudocyudoc/IGC/actions/runs/40443107291), la [ronda física D/M](https://github.com/yudocyudoc/IGC/actions/runs/40450646600) y la [adjudicación Buffalo](https://github.com/yudocyudoc/IGC/actions/runs/40453262004) terminaron correctamente. Una CI correcta puede registrar un resultado científico negativo. Estos cortes no certifican una segunda iteración conjunta ni una evaluación externa ciega.

Las pruebas anteriores ya permiten estas conclusiones limitadas:

- **M3:** recupera dos estructuras representadas por sus plantillas; responde a cambios de observaciones. No identifica universalmente estructura ni parámetros.
- **M3-P:** se abstiene en seis mundos con parámetros cambiados. La abstención evita tres identificaciones erróneas que produciría forzar el mínimo RMSE. La familia puede expresar esos mundos; la política de tres plantillas fijas no los recupera.
- **B4/B5:** Buffalo pudo proponer y revisar un mecanismo ejecutable. B5 redujo su error respecto de B4, pero no superó B2/B3; la explicación verbal siguió excediendo las entregas simuladas.
- **R1 común:** D/M tienen trayectorias; B tiene un fallo propio reproducible. Los RMSE D/M describen cuatro tiempos de construcción bajo distintos supuestos paramétricos, no identifican una estructura ganadora.
- **Pulsos:** demostraron separación predictiva, sin decidir cuál propuesta describe mejor un sistema.

## 4. Secuencia de hitos

| Hito | Pregunta que debe resolver | Entrega concreta | Criterio de cierre | Prioridad |
|---|---|---|---|---|
| **R0 · Recuperación** | ¿Está disponible el avance existente? | Main con fuentes avanzadas y regresiones | PR #52 integrado y CI correcta | Cerrado al corte |
| **R1 · Primera ronda común** | ¿Qué produce cada método ante la misma evidencia? | Seis D y tres M simulados; B nativo con G1 negativo y sin trayectoria | Tres métodos intentados y resultados propios adjudicados | Cerrado al corte, con resultado B negativo |
| **R2 · Revisión y memoria** | ¿Puede cada brazo revisar su decisión a partir de sus consecuencias? | Segundo estado de cada brazo y linaje consultable | Revisión, ratificación o abstención explícita; memoria antes/después verificable | Próximo hito inmediato |
| **R3 · Pruebas estructurales** | ¿Se distingue estructura, parámetro e insuficiencia de datos? | Casos nuevos y contrastes predeclarados, incluida variación paramétrica | Resultados explicables por caso, sin forzar identificación | Siguiente prioridad científica |
| **R4 · Evaluación nueva** | ¿Las predicciones sobreviven a datos no usados para construir o ajustar? | Predicciones congeladas y comparación posterior | Evaluación sin refit; alcance de la independencia explícito | Después de congelar el método |
| **R5 · Aporte Clef/Clairic** | ¿Añaden información o capacidad útil? | Piloto comparativo de selección semántica o extracción | Beneficio medible frente a una referencia adecuada, o descarte justificado | Condicionado al cierre D/B/M |
| **R6 · Expansión de IGC** | ¿Qué necesita el siguiente problema que el sistema actual no puede hacer? | Experimento de ampliación acotado | Prueba fallida previa y mejora comprobable | Horizonte condicionado |

```mermaid
flowchart LR
    R0["R0 Recuperación cerrada"] --> R1["R1 cerrado: D/M simulados, B G1 negativo"]
    R1 --> R2["R2 Revisión propia y memoria"]
    R2 --> R3["R3 Estructura, parámetros y ambigüedad"]
    R3 --> R4["R4 Predicción ante evidencia nueva"]
    R4 --> R5["R5 Clef o Clairic con comparación específica"]
    R5 --> R6["R6 Ampliación por necesidad demostrada"]
```

La preparación de pruebas posteriores puede avanzar mientras se ejecuta el hito actual. No debe cambiar las reglas de una campaña que ya empezó. Un fallo de infraestructura se corrige localmente; un resultado científico negativo se conserva y orienta la siguiente prueba.

## 5. R1: resultado ya obtenido y límites

La fuente común es pública: entrada rectangular de 1.7 items/h durante 2 h y entregas acumuladas 0, 0.35, 1.1 y 2.5 items en t=0,1,2,4 h. El caso comprueba el recorrido y permite comparar resultados de construcción; no es una reserva ciega.

El [informe final R1](https://github.com/yudocyudoc/IGC/blob/f07d94c9109bbbb77264509bf7ed04d6aead9cba/docs/ARENA_R1_PRIMER_CORTE_TRES_BRAZOS_RESULTADO_2026-10-26.md) establece:

1. D ejecutó seis candidatos propios y M tres. El menor RMSE D fue 0.150205; M conservó abstención pese a un mínimo de 0.316560. No se infiere superioridad metodológica de esos mínimos.
2. Buffalo recibió la misma fuente mediante su motor original y realizó una sola llamada. Su nativo contiene una dependencia circular sin anclaje entre `congestion_multiplier` y `product_of_capacity_effects`.
3. El conteo de 17 ecuaciones y 17 variables no evitó el fallo real de construcción en OpenModelica. B tiene G1 negativo, ninguna trayectoria y G3 no calculable. No existe un RMSE B que comparar con D/M.
4. El diagnóstico encontró además capacidad no efectiva en el flujo y un pulso que decae donde la entrada pedía un rectángulo. Son discrepancias de la hipótesis nativa, no razones para sustituir la arquitectura.

R1 queda cerrado **como primera ronda de intentos**, sin ganador y sin tres simulaciones exitosas. Los documentos intermedios que situaban B bloqueado describen una etapa anterior a su llamada, no el estado vigente.

La autorización inicial ya se consumió. La revisión R2 requiere su propio alcance y presupuesto; este plan no los concede. Conservar el modelo fallido y sus logs como padre de revisión permite probar una capacidad que repetir R1 ocultaría: responder a las consecuencias de una propuesta propia.

## 6. R2: probar revisión dinámica y memoria útil

Cada brazo recibe únicamente sus predicciones, observaciones de construcción y discrepancias, bajo una plantilla equivalente. El mensaje no debe sugerir la ecuación que corregir ni entregar modelos rivales.

Para B, que no tiene predicciones físicas R1, el feedback contiene su modelo nativo, la fuente y el log del intento fallido. La condición recomendada no le entrega una reparación redactada ni la localización detallada de errores por el evaluador. Si se da esa ayuda, debe identificarse como condición asistida. Su pregunta inmediata es si logra revisar la formulación o reconocer que no puede hacerlo.

Si B R2 llega a simular, será la primera trayectoria de este linaje. Se medirá ejecutabilidad y ajuste de R2, **sin inventar un porcentaje de mejora de RMSE respecto de R1**, que no tuvo ese valor.

La revisión puede cambiar estructura, parámetros, interpretación o grado de confianza. Debe indicar cuál cambió. Mantener una hipótesis o abstenerse también son respuestas válidas cuando no hay fundamento para revisarla.

Dos precauciones evitan fabricar una demostración:

- M3 absteniéndose no autoriza elegir C00 como su supuesto padre y aplicarle M2. Si no existe una hipótesis seleccionada, se conserva ese estado y se define explícitamente qué pregunta o variante se prueba después.
- D2 utiliza un protocolo de ensayo adicional. No se deben inventar nuevas observaciones para imitar su revisión histórica. Si se agrega evidencia, se entrega el mismo nuevo corte primario a los tres brazos, separado del feedback privado.

ATMS/ledger deben responder: qué sostuvo una propuesta, qué versión recibió feedback, por qué cambió y qué se conocía antes del cambio. Implementar esas consultas sobre el ciclo real tiene prioridad sobre ampliar motores de búsqueda o auditoría.

**R2 se cierra** cuando existe una segunda decisión documentada por brazo, incluso negativa, y el linaje puede reconstruirse. No exige que todos mejoren.

## 7. R3: separar las capacidades científicas

Las pruebas siguientes deben distinguir estas preguntas:

| Pregunta | Diseño mínimo | Interpretación correcta |
|---|---|---|
| ¿La selección depende de los datos? | Cambiar observaciones conservando la identidad administrativa del caso | La respuesta debe seguir la evidencia, como ya se comprobó en M3 |
| ¿Los parámetros fijos causan el fallo? | Estructura representable con parámetros distintos de las plantillas | Comparar M3 congelado con una variante explícita y acotada, si se implementa |
| ¿Hay información suficiente para distinguir estructuras? | Dos mecanismos compatibles dentro del error declarado | Conservar la clase compatible o abstenerse |
| ¿La familia no explica el comportamiento? | Caso que ninguna parametrización admitida logra explicar bajo la prueba | Registrar incompatibilidad del repertorio probado; no afirmar conocimiento de todo mecanismo posible |
| ¿La hipótesis anticipa sus consecuencias? | Confrontar la explicación del brazo con su simulación | Corregir mecanismo, expectativa o confianza; B4/B5 constituye un antecedente |
| ¿La perturbación adjudica o solo separa? | Simular rivales y después obtener una observación del sistema evaluador | Sin observación, solo se demuestra separación |

La primera extensión razonable a investigar es **calibración acotada por estructura**, porque M3-P ya mostró una limitación concreta de la política fija. No se recomienda modificar moléculas ni el compositor: los mundos de M3-P ya eran expresables por ellos.

La variante debe tener identificador propio, límites de parámetros, presupuesto y evaluación nuevos. Las seis respuestas históricas M3-P permanecen como evidencia de desarrollo y no se convierten retrospectivamente en una validación independiente del método ajustado.

## 8. R4: valor predictivo fuera de construcción

Una vez congelados método, parámetros y predicciones, confrontarlos con una nueva perturbación o un nuevo tramo de observaciones. Si los datos eran públicos o el constructor podía reconstruirlos, describirlos como comprobación temporal o sintética, no como reserva ciega.

La evaluación debe distinguir:

- error de predicción;
- cobertura de las alternativas o intervalos, si están definidos;
- número de identificaciones incorrectas y abstenciones;
- capacidad de distinguir mecanismos frente a simples diferencias paramétricas;
- costo de obtener cada resultado.

Añadir una referencia matemática sencilla reutilizando código existente, definida antes del resultado. Su nombre operativo será **REF**, para no confundirla con Buffalo B ni con las revisiones históricas B0–B5. Si D ya contiene exactamente esa referencia, reportar esa coincidencia; no fingir un método adicional.

Un único caso no demuestra superioridad general de una técnica. Primero se obtiene un resultado interpretable; después se amplía el conjunto si la pregunta lo necesita.

## 9. R5: cuándo usar Clef y Clairic

**Clef.** El piloto recuperado dio 4/8 conjuntos conservadores exactos en tareas numéricas y 9/9 en notas operativas sintéticas, con matices de confianza. Esto justifica estudiar selección o priorización semántica; no reemplazar el cálculo de errores ni activar automáticamente C.

La prueba útil comparará, sobre los mismos casos, información numérica y evidencia operativa adicional. Debe fijar el repertorio antes de que Clef vea las soluciones de D/B/M y usar una referencia determinista pertinente. Si clasifica las salidas ya emitidas por los rivales, será un selector posterior, no un cuarto productor independiente.

**Clairic.** Evaluarlo solo cuando haya una necesidad real de extraer datos de registros, tablas o imágenes. Medir campos, unidades, ausencias y errores de extracción; hacer las operaciones aritméticas con código. Las pruebas anteriores no demostraron calidad multimodal ni fiabilidad como calibrador físico.

No es necesario que ambos modelos participen en el mismo recorrido. Un resultado sin ventaja también cierra el piloto.

## 10. R6: horizonte de IGC sin adelantar su construcción

Se conserva la visión de un laboratorio que reutiliza conocimiento, mantiene controversias y explora consecuencias de políticas e intervenciones. Sus expansiones quedan ligadas a necesidades verificadas:

| Horizonte | Condición para abrirlo |
|---|---|
| Recuperación semántica, RDF o vectores adicionales | Un corpus y una consulta relevantes que la recuperación actual no resuelva adecuadamente |
| Más moléculas o clases de sistema | Un mecanismo requerido por una prueba concreta que el catálogo actual no pueda representar |
| ATMS de mayor escala o servicio persistente | Un volumen o patrón de uso real que exceda los límites medidos del motor y almacenamiento actuales |
| Estudio de políticas | Modelos suficientemente contrastados para la pregunta de decisión, con incertidumbre explícita |
| Investigación de campo | Caso delimitado, datos utilizables y permisos correspondientes |
| Despliegue e interfaz | Un flujo repetido cuya operación justifique producto y mantenimiento |

No se especifican ahora servicios, APIs cloud ni clases para esos horizontes.

## 11. Cómo decidir un cambio sin caer en perfeccionamiento indefinido

Antes de proponer una modificación, responder en una ficha breve:

1. ¿Qué tarea observable se quiere realizar?
2. ¿Qué entrada concreta hace fallar la versión actual y cuál sería el resultado aceptable?
3. ¿Es un fallo de integración, traducción, presupuesto, datos, parámetros, política o representación?
4. ¿Puede resolverlo una corrección localizada sobre los componentes existentes?
5. ¿Qué comparación demostraría que el cambio aportó algo?

Una limitación de representación u organización que impida una prueba necesaria puede justificar un rediseño después de comprobar que una corrección localizada no basta. B4 fue una hipótesis dinámica fallida; Buffalo R1 produjo ecuaciones indeterminadas; M3-P mostró una política paramétrica insuficiente; la falta de B/M en una enumeración fue un error de integración. Ninguno demuestra por sí mismo que deba sustituirse la arquitectura.

Los controles existentes se mantienen y se ejecutan cuando corresponda. Solo se añade un control si un fallo observado o una ambigüedad concreta impide interpretar la prueba actual.

## 12. Orden del trabajo y criterio de término

La siguiente secuencia es de entregas, no un calendario prometido:

1. Consumir el cierre R1 y preparar el feedback propio sin repetir sus llamadas ni cambiar sus resultados.
2. Conectar el padre Buffalo R1 a la revisión R2, verificar la entrada offline y fijar el presupuesto antes de una llamada nueva.
3. Ejecutar la revisión autorizada y persistir las segundas decisiones D/B/M, admitiendo conservación, fallo o abstención.
4. Ejecutar pruebas nuevas de estructura/parámetros/ambigüedad.
5. Evaluar predicciones congeladas ante evidencia nueva.
6. Decidir, con esos resultados, si merece abrirse Clef, extracción Clairic o una ampliación de representación.

La **Arena técnica** se considera cerrada para este corte cuando los tres métodos, sus rutas de simulación o bloqueos y una segunda decisión trazable funcionan en conjunto. La **evidencia científica** se expresa por prueba y alcance; no se resume en «arquitectura aprobada» ni en un ganador universal.

## 13. Fuentes del corte

- [Recuperación e integración, PR #52](https://github.com/yudocyudoc/IGC/pull/52) y [CI en main](https://github.com/yudocyudoc/IGC/actions/runs/40443107291).
- [PR #53: ronda física D/M](https://github.com/yudocyudoc/IGC/pull/53) y [PR #54: Buffalo y adjudicación final](https://github.com/yudocyudoc/IGC/pull/54).
- [Resultado R1 al corte vigente](https://github.com/yudocyudoc/IGC/blob/f07d94c9109bbbb77264509bf7ed04d6aead9cba/docs/ARENA_R1_PRIMER_CORTE_TRES_BRAZOS_RESULTADO_2026-10-26.md), [llamada Buffalo real](https://github.com/yudocyudoc/IGC/actions/runs/40452596916) y [diagnóstico sin nueva inferencia](https://github.com/yudocyudoc/IGC/actions/runs/40453262004).
- [Plan rector v1.3 conservado en el corte](https://github.com/yudocyudoc/IGC/blob/1ac282f7e6cafd2280c7e0ae69a0330d35d2b222/docs/ARENA_IGC_ATMS_PLAN_IMPLEMENTACION_V1_3_2026-10-25.md).
- [M3 y sus límites](https://github.com/yudocyudoc/IGC/blob/1ac282f7e6cafd2280c7e0ae69a0330d35d2b222/docs/ARENA_M3_SELECCION_ESTRUCTURAL_OBSERVACIONAL_2026-10-26.md) y [M3-P](https://github.com/yudocyudoc/IGC/blob/1ac282f7e6cafd2280c7e0ae69a0330d35d2b222/docs/ARENA_M3_P_VARIACION_PARAMETRICA_RESULTADOS_2026-10-26.md).
- [B5 y autocorrección parcial](https://github.com/yudocyudoc/IGC/blob/1ac282f7e6cafd2280c7e0ae69a0330d35d2b222/docs/ARENA_B5_AUTOCORRECCION_B4_REAL_2026-10-26.md).
- [Pilotos Clef](https://github.com/yudocyudoc/IGC/blob/1ac282f7e6cafd2280c7e0ae69a0330d35d2b222/docs/ARENA_CLEF_DOS_PILOTOS_REALES_RESULTADOS_2026-10-26.md).
- [Informe local de recuperación](RECUPERACION_MAIN_ARQUITECTURA_2026-10-26.md) y [revisión B4/M3/pulsos](REVISION_CORRECCIONES_B4_M3_DM_B2B3_2026-10-26.md).

Las fuentes fijadas al PR #52 conservan la procedencia de los antecedentes; el estado actual de R1 procede del PR #54. Se contrastaron informes y logs de ejecución; no se recalcularon todos los RMSE desde CSV durante esta revisión documental.

La hoja de ruta ordena el trabajo. Las tareas, archivos, pruebas, presupuestos y condiciones de entrega están en el [plan de implementación](ARENA_IGC_ATMS_PLAN_IMPLEMENTACION_V2_0_2026-10-27.md).
