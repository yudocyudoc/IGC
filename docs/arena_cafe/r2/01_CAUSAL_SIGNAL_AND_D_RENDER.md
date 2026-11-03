# RF-02T · Estímulo causal POS y renderizado de seis alternativas D-B

**Vínculo:** continuación operativa de [RF-02 / PR #139](https://github.com/yudocyudoc/IGC/pull/139).  
**Decisión de trabajo:** usar una política temporal de **referencia de ingeniería** sin anticipación, con anchura declarada antes de evaluar curvas, sin solicitar revisión de Astra por cada entrega.  
**Motor original D y registro E1:** sin cambios. **No es estimación de la tasa instantánea real, aprendizaje de parámetros, validación G2/G3 ni autorización de una predicción de EV-01.**

## 1. Política temporal causal, exacta a nivel racional

Para cada evento observado de creación de pedido `(pedido_i, t_i)`, el controlador define una señal externa

\[
u_i(t)=\begin{cases}
\dfrac{1}{w} & t_i\leq t < t_i+w,\\
0 & \text{de otro modo}.
\end{cases}
\qquad
u(t)=\sum_i u_i(t)
\]

La anchura **de referencia** es `w=1/2` minuto (30 segundos); no ha sido inferida de los datos ni optimizada por RMSE. Los anchos `1/4, 1/2, 1` minuto quedan **predeclarados solo para sensibilidad posterior**, no seleccionables tras ver quién gana. Para un pedido ocurrido a los 0.30 min, toda su masa empieza a t=0.30 y nada aparece antes: se corrige el efecto de anticipación de la reconstrucción histórica que llenaba el bin [0,0.5).

La integral en la ventana observada no siempre contiene la masa completa: si un pedido llega en t=9.9 y w=0.5, en t=10 solo han ingresado `1/5` de la unidad a la señal continua y `4/5` **quedan diferidos después del corte**. El sistema registra exactamente `mass_before_cutoff_orders_exact` y `mass_deferred_after_cutoff_orders_exact`. No infla la masa precorte para imponer 15 unidades, no descarta la fracción diferida y no introduce pedidos futuros.

**Distinción indispensable:** los 15 pedidos POS de la muestra original son 15 eventos observados antes del corte. En el modelo continuo con entrada rectangular y cola diferida, el volumen ya inyectado en la ODE a los 10 minutos **puede ser menor que 15**. No se comparará el balance D-B en t=10 contra 15 como si toda esa masa ya estuviera en el modelo. El evento de pedido (dato discreto) y la tasa aproximada por difusión causal (supuesto) tienen operadores diferentes.

La política se implementa en `scripts/arena_cafe/r2_causal_pos_signal.py`. Para todos los eventos, produce intervalos de tasa exactos mediante `fractions.Fraction`, segmenta también en el cutoff, genera hash de señal independiente de las entregas y registra `scientific_policy_approval=NOT_GRANTED`.

## 2. Renderizado Modelica de las alternativas D originales

Una función opcional `render_six_with_declared_nominals(...)` acepta **únicamente** nominales explícitos y atribuidos según el esquema de RF-02. Construye **todas** las estructuras permitidas con `r2_observational_contracts._grammar` y genera `.mo` de ingeniería mediante el **renderer original** `scripts.arena_d_v01.modelica`. No llama `D.generate(POS)`. Sustituye la ecuación de entrada por la señal causal, elimina las dos declaraciones `pulseRate/pulseDuration` ahora sin uso y verifica que las ecuaciones de capacidades, stocks, flujos, pérdidas y acumulados quedan byte-idénticas.

El renderizado usa tiempo en minutos y entrada en pedidos/minuto; toda candidata lleva el mismo estímulo y los mismos parámetros externos, con origen registrado; **ninguna candidata se escoge**. Se emiten **seis textos sin simulación** en pruebas con los nominales ficticios `capacity=1.23 orders/minute`, `response_time=2.7 minute`, `loss_time=8.1 minute`, escogidos solo para verificar renderizado y deliberadamente distintos de los valores E1. Estos números no se promueven como estimaciones operacionales EV-01 ni se usan para scoring.

Por defecto la CLI **no genera `.mo`**. Únicamente emitirá textos si se pasan a la vez `--nominal-provenance ... --render-engineering-modelica`. No produce `.mos`, no ejecuta OpenModelica y no marca G2/G3.

## 3. Invariantes adversariales

- No hay tasa antes del timestamp individual ni antes de 0; cada pedido aporta masa total 1 y no cambia el número de pedidos observados.
- La integral exacta del estímulo debe separar masa precorte y diferida, sumando exactamente `N_eventos`.
- O0/O1 comparten los mismos eventos y por tanto la misma señal; cualquier diferencia de entregas observadas no modifica el estímulo.
- Los tres anchos de sensibilidad son explícitos; se rechazan valores no declarados, tiempos posteriores al corte o negativos y lista desordenada.
- Para los seis D, la modificación sobre el output del generador original solo afecta a la función `inputRate` y declaraciones de pulso inoperantes; el resto de ecuaciones no se reescribe. La emisión sigue siendo **ingeniería**, no demostración de trayectoria válida.
- Se rechaza parametrización ausente, valor no positivo, unidad no declarada y fuente reconocida como E1, DES privado o brazo rival.
- El estado de esta entrega sigue siendo `R2=PARTIAL`, `R3=NOT_RUN`, `A3=PARTIAL`, `G2/G3=NOT_RUN`, `G4/G5=NOT_RUN`.

## 4. Flujo de trabajo ágil y siguiente hito

**En cada PR:** CI automática, tests negativos y fuente nativa protegida; los resultados son pruebas de ingeniería, no una aprobación del método científico. **Astra solo interviene ante cambio de contrato metodológico sustancial o antes de adjudicar G3/G4/G5**. Esto evita que cada test requiera consulta separada, preservando independencia en los verdaderos puntos de decisión.

Siguiente incremento sin aprobación externa: validar la compilación/solución **de ingeniería** de las seis propuestas con parámetros explícitamente ficticios y evento causal, con balance de masa usando **la integral de la señal realmente inyectada**, y verificar semántica de observables. Se mantendrá `G3=NOT_RUN`, sin selección de ganador, y no se hará inferencia pagada de Buffalo. Los parámetros EV-01 de producción o calibración externa requieren un contrato científico diferente.

**Código:** `r2_causal_pos_signal.py`. **Pruebas:** `test_arena_cafe_rf02_causal_pos_signal.py`. **CI:** workflow RF-02 de contratos (lectura del único artefacto público A1 congelado). No contiene scripts de generación DES ni llamadas a proveedor.
