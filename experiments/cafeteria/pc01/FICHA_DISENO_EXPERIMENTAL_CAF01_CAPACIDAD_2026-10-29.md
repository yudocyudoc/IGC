# CAF-01 · Ficha de diseño experimental 0.1 — Capacidad que se desea probar

**Fecha:** 2026-10-29 · **Ámbito:** PC-01, cafetería sintética · **Estado:** decisión de diseño propuesta, pendiente de revisión científica y de selección privada de la verdad. **No es una configuración DES**, ni una autorización para ejecutar construcción o evaluación.

## Pregunta precisa

**¿Puede D, B o M transferir una dinámica de servicio que ya dejó señales observables durante construcción a una demanda mayor, con el mismo mecanismo físico, sin reajustar el modelo después del bloqueo?**

Esta primera CAF-01 **no** busca revelar por primera vez un cuello de botella que fue completamente invisible durante construcción. Esa situación queda reservada para una prueba posterior de revisión y abstención. Tampoco busca demostrar recuperación causal de la topología interna: distintas colas, etapas y recursos pueden dar la misma serie agregada de entregas.

El mundo se tratará como **cafetería sintética con justificación operativa**, no como cafetería real validada.

## Ficha de decisiones

| Elemento | Decisión de diseño pública | Qué debe fijarse y custodiarse privadamente antes de construir |
|---|---|---|
| Frontera | Un pedido equivalente: desde aceptación hasta entrega. Estado inicial vacío, sin cancelaciones ni pérdidas | Operaciones materiales específicas y razón de cada separación en etapas |
| Etapas | Crear una etapa distinta solo si representa una operación y un recurso dedicado distintos; FIFO, servicio determinista y servidores finitos | **Número y orden** de etapas, sin revelar su topología a D/B/M |
| Servidores | Cada servidor procesa a lo sumo un pedido por vez; la capacidad concurrente se justifica físicamente | **Servidores por etapa**, con racional operativo, no seleccionados por RMSE |
| Servicio | Los tiempos son supuestos sintéticos explícitos, expresados en minutos racionales; no se presentan como mediciones reales | **Duración de cada operación** y fuente del supuesto |
| Fenómeno objetivo | **Congestión moderada con entregas observables en construcción**, que pueda intensificarse al aumentar la tasa; no bloqueo total ni servicio instantáneo | Comprobación analítica de carga, latencia mínima y límites de capacidad; los valores numéricos y la decisión de aceptación quedan sellados |
| Calendario | Construcción 1.2 pedidos/min × 20 min = 24 llegadas; evaluación 1.5 pedidos/min × 20 min = 30; lecturas 0,5,10,15,20,30,40; reinicio completo y horizonte 40 min | Misma configuración en ambos escenarios, sin parámetros alternativos ni reinicio parcial |
| Desempate | Primero terminaciones, después aceptaciones, después nuevos inicios aguas abajo; lectura tras eventos simultáneos | Regla idéntica en los dos escenarios; ningún ajuste posterior |
| Evidencia | Todos los brazos usan solo pulso prescrito y entregas D(t) de construcción; A/P sidecar común y no privilegiado | Topología, tiempos individuales, servicio y estados internos DES nunca entran en los modelos |

## Comprobación de informatividad **antes de observar datos**

La selección de un escenario no debe descansar exclusivamente en una descripción narrativa de cafetería. En la ficha **privada** se documentarán, calculadas solo a partir de servidores y tiempos propuestos:

- **Capacidad teórica de cada etapa**: \(\mu_i=s_i/\tau_i\) pedidos/min; \(s_i\) es el número de servidores dedicados y \(\tau_i\) la duración determinista del servicio.
- **Cuello de botella teórico**: \(\mu_*=\min_i\mu_i\). Para esta cadena FIFO sin pérdidas, es una cota nominal de rendimiento sostenido, **no** una predicción exacta de D(t) en 40 minutos.
- **Carga de construcción y evaluación**: \(\rho_c=1.2/\mu_*\), \(\rho_e=1.5/\mu_*\). El escenario buscado debe permitir congestión en construcción sin llevar el sistema a una situación absurda de bloqueo o casi ninguna entrega; la evaluación aumenta presión sobre **el mismo** sistema.
- **Latencia mínima sin cola**: \(L_0=\sum_i\tau_i\). Contrastar con los siete momentos de lectura y los 40 minutos de horizonte; tiempos excesivos podrían hacer trivial el resultado sin revelar dinámica útil.
- **Coherencia de recursos**: etapa, servidor y tiempo deben poder explicarse como operación plausible; si falta justificación física, se rechaza **antes** de usar el DES.

### Criterios cuantitativos propuestos para el primer mundo (públicos antes del sello)

Para evitar seleccionar libremente el escenario después de conocer sus resultados, propongo registrar **ahora**, sujetos al dictamen de Astra y antes de escoger la configuración privada, las siguientes restricciones de diseño:

| Comprobación analítica | Regla propuesta | Justificación y límite |
|---|---|---|
| Congestión de construcción | **\(1.05 \le \rho_c \le 1.25\)** | La entrada prescrita supera moderadamente la capacidad nominal del cuello de botella; no implica que cada lectura revele cola ni que REF-CAF sea identificable |
| Presión de evaluación | **\(1.3125 \le \rho_e \le 1.5625\)**, consecuencia de \(\rho_e=1.25\rho_c\) | La misma capacidad se somete a un aumento de entrada del 25%; no se ajusta según el resultado |
| Capacidad nominal implícita | **\(0.96 \le \mu_* \le 1.2/1.05\approx1.142857\)** pedidos/min | Se deduce algebraicamente de \(\rho_c\); **no** es una capacidad DES medida |
| Latencia sin espera | **\(0<L_0\le4\)** minutos | El primer pedido aceptado durante construcción ocurre a \(5/12\) min y, con las reglas FIFO y recursos inicialmente libres, debería poder terminar antes de la primera lectura a 5 min; no garantiza entregas posteriores ni identifica etapas |

Estos rangos son **hipótesis operativas sintéticas explícitas**, no distribuciones empíricas de cafeterías reales, ni restricciones extraídas de las rejillas D/M/B. La cota de 4 minutos es intencionalmente una condición de observabilidad temprana; la banda de carga es una regla de diseño, no una garantía de saturación estimable por REF-CAF. **Astra puede rechazarlas o corregirlas antes del primer sello**, dejando el cambio registrado en la propia ficha; no se deben mover tras observar una curva.

**Paridad de información (pendiente de Astra):** incluso una banda *pública* para \(\mu_*\) puede dar a los brazos información indirecta sobre una capacidad que supuestamente está reservada. Estos rangos son **propuestas del diseñador, no entradas para D/B/M/REF**. Antes de fijarlos como regla experimental, el responsable debe decidir y verificar que esa información no llegue a los productores, o declarar expresamente su entrega simétrica a todos y revisar la política «pulso + D(t)». Si el repositorio es accesible a los brazos, publicar aquí el rango equivale a revelar una restricción sobre la verdad, aunque no se haya escogido su valor exacto. **No asumir cegamiento por el mero hecho de llamar privado al parámetro.** Ninguna verdad se ha elegido ni se ha compartido con los brazos.

**Procedimiento privado de una sola selección:** primero justificar operaciones, recursos y tiempos plausibles; calcular \(\mu_i,\mu_*,\rho_c,\rho_e,L_0\) sin invocar el motor DES; comprobar las cuatro reglas; si el primer diseño incumple alguna, documentar el motivo físico del ajuste **antes del sello y sin obtener salidas DES**. Una vez fijado y sellado, no hacer barridos, reintentos, reemplazos o previsualizaciones del mundo para maximizar ajuste, congestión, identificabilidad o ventaja predictiva. La existencia de una elección ex ante no prueba que se observe el fenómeno deseado.

La ficha privada debe conservar la **configuración escogida**, sus justificaciones y valores analíticos; la política de aceptación es pública, pero **no** los parámetros particulares ni sus evaluaciones. No incluir estos datos privados en el paquete que reciben D/B/M. **Estos cálculos no son una simulación DES, no prueban congestión observada ni identificabilidad.** Tras la primera construcción autorizada, si el supuesto de congestión visible resulta incorrecto, se reporta como resultado o límite del diseño: **no se sustituye el mundo**.

La condición de primera prueba será, por tanto, **transferencia de dinámica con señales ya disponibles**, no inferencia de una limitación completamente latente. Esta es una elección de alcance científico, no una promesa de que los tres brazos alcanzarán identificabilidad.

## Qué resultados interpretar, sin reabrir reglas

| Observación posterior | Interpretación permitida |
|---|---|
| D/B/M predice la evaluación con G2 válido y mejora ≥1 pedido MAE frente a REF-CAF, con contraste separado frente a REF-SCALE | Evidencia **descriptiva** de transferencia predictiva en este caso sintético; no identifica por sí sola el mecanismo |
| Varias estructuras o capacidades tienen ajuste similar en construcción y pronósticos divergentes | **Abstención o envolvente**, conforme G3; no declarar ganador estructural por un desempate numérico |
| REF-SCALE explica igual de bien la evaluación | No atribuir recuperación de una estructura por una mejora meramente proporcional |
| No emerge señal suficiente durante construcción o REF-CAF no alcanza sus intervalos elegibles | Documentar limitación de informatividad o abstención, **sin cambiar parámetros ni repetir el DES** |
| Se falla conservación, validación nativa o paridad numérica de un brazo | Bloquear o abstener **ese brazo** donde proceda; conservar resultados válidos de los demás |
| La evaluación revela un cuello de botella no inferible desde construcción | Señal legítima de límite predictivo/identificabilidad, no motivo para reajustar retrospectivamente |

La variable primaria sigue siendo **MAE de entregas acumuladas en seis tiempos de evaluación**; RMSE es secundario y pendientes son derivados. No introducir un segundo holdout aparente.

## Secuencia operativa — sin trabajos adicionales de arquitectura

1. **Revisión de Astra e investigador:** aprobar esta pregunta y el régimen objetivo, el mecanismo de desempates y el carácter sintético del mundo.
2. **Decisión privada offline:** completar la hoja física con operaciones, \(s_i\), \(\tau_i\), \(\mu_i\), \(\mu_*\), \(\rho_c\), \(\rho_e\), \(L_0\), justificación y criterios numéricos de aceptación **antes de ver cualquier curva**. No guardar estos datos en GitHub ni enviarlos a los brazos.
3. **Precompromiso y custodia externa:** usar G5 solo en el equipo local del investigador, resguardar configuración y nonce y obtener el primer acuse independiente. La coincidencia local del hash no es custodia.
4. **Construcción autorizada y única:** producir las siete lecturas públicas con el presupuesto existente; de forma separada conservar la traza material privada. No generar evaluación.
5. **D/B/M y controles:** usar construcción para ajuste, G0–G3, CAF-N enmascarado y REF-CAF/REF-SCALE; registrar fallos, abstenciones y presupuesto.
6. **Segundo acuse externo:** G4 contiene los pronósticos y referencias, con SHA de bytes exactos; custodiarlo antes de cualquier acceso a resultados de evaluación.
7. **Evaluación única, previamente autorizada:** mismo mundo privado reiniciado, 30 entradas públicas y seis observaciones para MAE/RMSE. No retocar estructura ni parámetros.

**Presupuesto duro sin ampliar:** 2 DES, 36 RK4, 26 OpenModelica, 2 consultas Buffalo y cero reintentos automáticos. Reducción OM a 20 **condicional**. **CAF-01 aún no se congela y PC-02 no está autorizado.**

**Nota crítica:** esta ficha no contiene la topología ni los números reales del mundo; completar y sellar la ficha privada requiere una decisión del investigador en un entorno externo. No confundir el ejemplo ilustrativo de Astra (45 s/45 s) con parámetros aceptados.
