# CAF-02 — Protocolo propuesto de prueba independiente K0→K1→K2

**30 de octubre de 2026. ESTADO: BORRADOR DE POLÍTICA, NO PREREGISTRO EXTERNO NI AUTORIZACIÓN PARA EJECUTAR DES, OMC O PROVEEDORES.**

**Base:** sección 7 del plan ARENA v3.0, PR #100 (pregunta estructural) y PR #101 (estudio interno cerrado). El mundo de CAF-01 no puede reutilizarse como evaluación nueva.

## 1. Pregunta y límites de afirmación

Hipótesis A, **revisión de mecanismos**: con datos de K0, el brazo M conserva hipótesis C00 (dos etapas materiales) y C01 (tercera etapa material de tránsito) cuando ambas son compatibles. Elige antes de observar K1 una medición de un menú predeclarado, utilizando **todos** los parámetros compatibles por familia, y revisa sin descartar indebidamente la explicación generadora.

Hipótesis B, **valor predictivo**: las predicciones de K2 emitidas antes de K1 y después de K1 se comparan contra **la misma evaluación nueva** y contra REF-CAF/REF-SCALE. Mejorar únicamente el ajuste K1 no es éxito predictivo.

La primaria estudia M/C00/C01 porque esa ruta tiene implementado el contraste. D y Buffalo recibirán la misma evidencia cuando sean ejecutables bajo presupuestos y contratos nativos, pero **no** debe afirmarse éxito D/B/M desde un ensayo solo de M. La revisión de hipótesis entre dos grafos existentes no equivale a modificar arquitectura; cambiar solamente tiempos/capacidades es revisión paramétrica. No hay ninguna justificación para editar E1.

Una corrida de simulación independiente sigue sin acreditar utilidad operativa sobre cafeterías reales ni generalización estadística.

## 2. Mundo independiente, tres cortes y custodia

Fuente a construir **después** de aprobación: simulador privado por eventos discretos, independiente del integrador y compositor de moléculas E1. Antes de K0 se fijarán código, mecanismo de servicio, orden de eventos simultáneos, parámetros, semillas, horarios, política de reinicio, contrato de conteos enteros y observaciones. Cambiar de lenguaje sin cambiar conceptualización no basta como independencia. Se informará qué supuestos comparte con E1.

Frontera: una clase de pedido equivalente; desde aceptación hasta entrega; no pérdidas/cancelaciones; stocks iniciales vacíos; aceptación = entregas + pendientes; tiempo en minutos, tasas en pedidos/minuto. **K0, K1, K2 reinician desde vacío**; no mezclar con continuación de estados. La reserva K2 nunca se usa para elección de K1 ni calibración.

| Momento | Acción | Custodia |
|---|---|---|
| Antes de K0 | Fijar fuente privada y política completa. Testigo externo del hash, parámetros y calendario de mundo. | G5 previo a construcción, verificable |
| K0 | Ejecutar como máximo una construcción y entregar solo datos autorizados. Conservar candidaturas, elegir/abstener K1 y preparar propuesta anterior K2. | G4a externo **antes de K1** |
| K1 (condicional) | Una sola opción elegida antes de observarla; revisar por regla inmutable. | G4b externo **antes de K2** |
| K2 | Una sola evaluación independiente, después de dos versiones selladas. | Puntuar sin reajustes; publicar resultados adversos |

El G5 histórico de CAF-01 fue NOT_VERIFIED; **no** heredar aquella excepción ni usar un hash local como sustituto de testigo externo. No correr nuevos mundos sin autorización específica.

## 3. Dominio y reglas concretas **propuestas**, pendientes de aprobación previa a G5

Los valores proceden como propuesta del dominio sintético explorado en PR #101; **no** representan minutos reales de servicio de una cafetería. La política JSON es la fuente exacta de parámetros: CAF02_INDEPENDENT_K0K1K2_POLICY_PROPOSAL_2026-10-30.json.

| Dimensión | Propuesta |
|---|---|
| Estructuras | C00 preparación→despacho; C01 preparación→despacho→tránsito |
| Tiempos respuesta preparación/despacho (min) | 1, 1.5, 2, 3 por etapa |
| Capacidad preparación/despacho | 72, 100 pedidos/h, común a ambas etapas |
| Tránsito C01 | tiempos 0.25, 1, 6 min; capacidad 100 pedidos/h |
| Rejilla | 32 configuraciones C00, 96 C01; **128 en total** |
| K0 entrada | pulso 1.2 pedidos/min, 20 min; reinicio vacío |
| K0 información de ajuste | solo entregados acumulados t=5 y t=10 |
| K0 adecuación absoluta | MAE ≤1.0 pedido (ambas observaciones) |
| K0 cercanía al mejor ajuste por familia | MAE ≤ mejor familiar +0.4 |
| K1 tolerancia residual | ±0.75 pedidos |
| K1 margen numérico **provisional** | 0.02 pedidos; total ±0.77 |
| K1 separación exigida | distancia positiva entre intervalos ampliados ≥0.05 pedidos |
| K2 entrada | pulso 1.35 pedidos/min, 20 min; reinicio vacío |
| K2 puntuación | entregados acumulados t=5,10,15,20,30,40 |

**Cambio explícito respecto al estudio interno:** allí K0 absoluto=0.8 y residual K1=0.2. Aquí se **proponen** 1.0 y 0.75 para no exigir concordancia irreal con un conteo discreto y modelos agregados. No se presentan como umbrales validados; tampoco se elegirán retrospectivamente buscando éxito. Una política revisada necesitaría nueva versión fechada **antes de G5**, no después de ver K0/K1/K2.

Los tiempos son escalas agregadas stock/salida, no servicios por pedido. Se exigen tiempos positivos, unidades y conservación; no investigación operativa de cafeterías concretas como barrera adicional para esta prueba sintética.

## 4. Menú fijo K1 y regla de decisión

| Opción | Pulso conocido desde vacío | Única observación |
|---|---|---|
| A | 1.0 pedidos/min durante 20 min | entregados acumulados t=10 |
| B | 1.5 pedidos/min durante 20 min | entregados acumulados t=20 |
| C | 1.8 pedidos/min durante 20 min | entregados acumulados t=30 |

K0 calibra **ambas familias**; conserva todos los parámetros que cumplen las dos compuertas de adecuación. Para cada opción K1, calcula el intervalo de entregas de TODOS los supervivientes por familia. Amplía **cada** intervalo por ±(0.75+0.02)=±0.77. La separación robusta es la distancia positiva entre intervalos ampliados, cero si se solapan. Elegir mayor distancia ≥0.05; empate A→B→C. Sellar decisión y predicción K0 para K2 **antes de recibir K1**.

Si una familia o ninguna pasa K0, no existe problema de discriminar dos estructuras: **no ejecutar K1**. Si ambas pasan pero las tres opciones se solapan tras tolerancias, declarar K1_MENU_NO_GUARANTEED_SEPARATION y **no ejecutar K1**; conservar ambigüedad, sin sustituir la medición por un vector. No significa que ninguna medición imaginable sirva.

Si existe opción elegida, ejecutarla una vez y exponer únicamente el dato permitido. Mantener un candidato si |predicción - K1| ≤0.77; filtrar el resto sin nueva calibración. Si no sobreviven candidatos, declarar K1_CONTRADICTS_ALL; si sobrevive una familia, reducción de hipótesis estructurales compatible, **no** identificación causal garantizada.

El menú lo elige M como instrumento experimental: la misma observación se ofrece a D/B cuando participen, pero **no** se atribuye a esos brazos haber elegido óptimamente esa medición.

## 5. K2: pérdidas de conjuntos y comparadores

Comprometer dos versiones independientes de la misma predicción K2: **K0 antes de K1** y **K1 después de K1 y antes de K2**. Conservar las curvas por familia y la envolvente de unión de todas las familias y parámetros compatibles; no elegir a posteriori la curva que más se aproxima a la verdad.

Para un intervalo compatible [l,u] y observación y, definir pérdida por tiempo: **L = (u-l)/2 + max(0,l-y,y-u)**. Promediar L en los seis tiempos. Penaliza anchura y valores observados fuera del conjunto; **no es una puntuación probabilística propia**. Para el caso puntual l=u=m, L=|m-y| y coincide con MAE. Las referencias REF-CAF y REF-SCALE se puntúan como conjuntos degenerados, **solo si su regla adaptada a K0 permite emitir pronóstico**. No ven K1, K2 reservado ni llegadas privadas.

**Precisión de comparabilidad indispensable:** las versiones originales de CAF-01 **no pueden usarse sin cambios** con K0 limitado a t=5 y t=10. REF-CAF requería al menos dos intervalos elegibles de construcción para su mediana, y aquí como máximo aparece el intervalo 5–10; REF-SCALE original requería la curva de entregas de construcción en cada t de K2, que aquí no se revela. Por tanto se definen **dos versiones NUEVAS congelables** con exactamente la misma información inicial que M y nombres de versión propios:

- **REF-CAF-K0-1WINDOW:** tasa empírica mu=(D10-D5)/5 pedidos/min. Solo estima cuando el atraso ideal A_design−D es mayor a un pedido en **ambos** t=5 y t=10; sin esa evidencia, se abstiene. Pronostica min(A_K2(t), mu·t). No afirma que mu sea la capacidad física ni que esta nueva regla sea equivalente a la mediana original.
- **REF-SCALE-K0-EXTRAP:** reconstruye la curva K0 a partir de los tres puntos conocidos (t0=0, t5=D5, t10=D10), con interpolación lineal a t5/t10 y extrapolación posterior por la pendiente (D10−D5)/5, limitada por las aceptaciones de diseño A_K0(t). Luego multiplica por la razón de tasas 1.35/1.2 y limita por A_K2(t). Es control convencional de escalamiento **con extrapolación explícita**, no la regla REF-SCALE de CAF-01.

Estas referencias se calculan mediante caf02_k0_limited_references.py y se sellan **junto con K0**, sin retocarlas después de conocer K1. La abstención REF-CAF se reporta como ausencia de comparador, no victoria de M. Un triunfo contra estas versiones nuevas **no se compara directamente con los MAE de CAF-01**.

**Ganancia descriptiva:** L(K0)-L(K1) ≥ **0.25 pedidos** con **ambas versiones no vacías**. Informar L absolutos de K0, K1, REF-CAF y REF-SCALE. Mejorar K0, pero perder frente a REF-CAF, no es ventaja contra la referencia convencional. No tratar seis conteos acumulados correlacionados como seis réplicas.

**Puntos secundarios:** si ancho máximo de conjunto ≤2 pedidos, admitir el punto central y puntuar MAE/RMSE; en otro caso abstención puntual. Reportar simultáneamente ancho medio/máximo, cobertura observacional y distancia fuera del conjunto. Si no existe ningún candidato, **abstención completa**, no error cero ni victoria; si falta K0 o K1, no declarar mejora emparejada.

Si no hubo evidencia K1, la versión K1 es **idéntica a K0** (ganancia cero) y se registra que el caso no activó revisión. Si K1 eliminó todo, abstenerse sin rescate. La posibilidad de que la revisión estructural empeore K2 es un resultado publicable.

La pérdida propuesta se implementa en caf02_k2_set_scoring.py, función pura sin lectura de verdad reservada. Su coeficiente de penalización por anchura (0.5) es una elección explícita pragmática, no un teorema estadístico.

## 6. Presupuesto y realidad de ejecución

**Fuente DES:** K0 máximo 1; K1 máximo 1 solo si se elige, K2 máximo 1 tras autorización, total máximo **3 corridas**, sin reintentos. Un intento que falla consume presupuesto y se registra.

**Cálculos de candidatos (cota nominal sin deduplicación):** 128 curvas matemáticas K0 (32+96); hasta 384 proyecciones K1 para cubrir **las tres opciones del menú** con todos los supervivientes; y hasta 256 pronósticos K2 (128 para K0 más 128 para K1), total máximo **768 trayectorias calculadas** antes de reutilización de caché, excluyendo el preflight numérico independiente. Registrar denominadores y CPU. **NO** describirlas como 128 ejecuciones Modelica. Propuesta de máximo 12 verificaciones nativas G2 elegidas mediante regla anterior, sin extrapolar validez nativa de los modelos no examinados. Una divergencia nativa relevante limita la afirmación del brazo M. D y Buffalo solo podrán entrar con contratos nativos y costes independientes previamente autorizados; Buffalo máximo 1 inferencia propuesta, **cero invocaciones aquí**. Un fallo nativo es un resultado explícito, no habilita reparaciones retrospectivas.

Un DES de eventos discretos entrega conteos enteros; el modelo continuo no tiene por qué reproducirlos dentro de ±0.77 solo por compartir el mecanismo. Ese riesgo debe figurar en resultados y NO resolverse reparametrizando después de la verdad.

## 7. Verificación numérica puntual y criterio de cierre

Solo queda permitida **una comprobación de paso numérico** sobre las moléculas existentes, el dominio propuesto y los cinco pulsos públicos K0/K1/K2, para respaldar provisionalmente el margen 0.02 pedidos. Comparar integraciones Heun 0.05, 0.025 y 0.0125 min; esto mide convergencia en una rejilla **finita**, no un error global certificado ni equivalencia nativa/modelo-DES. Si incumple el umbral, no activar G5 con este margen. No hacer otra búsqueda de mundos para “optimizar” el resultado.

Publicar **todos** los desenlaces, incluso: K0 sin dos familias compatibles; K1 sin separación; K1 conserva ambas o elimina ambas; K2 no mejora o empeora; REF-CAF gana; D/B no ejecutables; G5 no verificado; y cualquier desviación de presupuesto.

**Éxito descriptivo acotado:** ambas familias sobreviven K0, opción K1 válida y seleccionada antes de respuesta, revisión fiel sin falso descarte de la familia real (adjudicado después), y mejora L de K2 ≥0.25 frente a versión K0. Solo si también supera REF-CAF/REF-SCALE se afirma ventaja descriptiva sobre la referencia en ese mundo. En cualquier otro desenlace se cierra con su diagnóstico; no se cambia el generador para fabricar éxito.

**Estado de esta entrega: no se ejecuta ni autoriza mundo DES nuevo, ningún K2 observado, ninguna modificación de E1.** La política debe aprobarse y obtener testigo externo ANTES de G5/K0. El informe interno PR #101 no es evaluación prospectiva.
