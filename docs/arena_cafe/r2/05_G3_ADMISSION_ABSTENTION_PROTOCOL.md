# RF-02P · Política ejecutable de admisión y abstención para G3

**Fecha:** 2026-11-03. **Base:** RF-02H / PR #143, informe de H_j derivado de doce trazas nativas. **Estado:** protocolo prospectivo **propuesto**, auditoría determinista de ingeniería; G3/G4/G5 NOT_RUN, A3 PARTIAL y R2 científico PARTIAL.  
**Código:** `scripts/arena_cafe/r2_g3_admission_policy.py` · **Pruebas:** `tests/test_arena_cafe_rf02_g3_admission_policy.py` · **CI:** `.github/workflows/arena-cafe-rf02-g3-admission.yml`.

## 1. Qué cambia respecto de RF-02H

Hasta ahora la Arena tenía una compuerta general: **G3 bloqueado** por parámetros, equivalencia semántica y ausencia de evaluación. Eso era correcto, pero demasiado agregado. Esta entrega implementa un **árbitro de admisión separado para cada método**, que toma el resultado RF-02H, vuelve a vincularlo a las doce trazas congeladas y emite recibos de **capacidad nativa / cumplimiento de ingeniería / abstención científica** sin fabricar ganadores.

No modifica los motores D, Short E1 o Buffalo; no hace nueva simulación, no ejecuta provider, no puntúa ni estima parámetros. El algoritmo **nunca devuelve G3=PASS** a partir de un manifiesto, ni siquiera si ese manifiesto afirma haber sido aprobado o que su holdout está sellado. Las supuestas aprobaciones externas siguen necesitando verificación por un proceso separado. La barrera del código es de aplicación: no sustituye el aislamiento del sistema operativo, R6 o un sistema de permisos remoto.

## 2. Resultado individual exigido

| Brazo | Hecho que sí se conserva | Lo que **NO** atribuimos al motor | Acción admisible hoy |
|---|---|---|---|
| **D** | Seis estructuras originales, ejecutadas bajo input causal, G2 ingeniería PASS | D **no** aprendió nominales ni su gramática seleccionó ganadora: los únicos nominales fueron un fixture artificial | **ABSTAIN** G3; obtener parámetros externos prospectivamente atribuibles o abstenerse en la evaluación |
| **M / Short E1** | **6/6 AST nativos**, priors originales y G2 ingeniería PASS | Los parámetros no fueron inferidos de POS; no se obliga a E1 a tener un estimador inexistente. Tres proyecciones materiales no hacen tres mecanismos certificados | Enumerador **COMPLETE**, metodología científica G3 **ABSTAIN** hasta validar rol/observación y un ensayo independiente; no imponer calibración como requisito nativo |
| **B / Buffalo** | Preparación y replay históricos, sin solicitud LLM EV-01 nativa auténtica | Una llamada Cloudflare anterior o un mock no acredita generación B nueva ni uso de POS | **ABSTAIN** hasta autorización separada de llamada nativa y recibo verificable |

En todos los casos, la ausencia de observables que un método legítimamente no represente se registra como **NO COMPARABLE**, jamás como puntuación cero.

## 3. Qué datos del ejercicio actual NO pueden funcionar como holdout

El mundo sintético O0 ya fue inspeccionado en RF-01/RF-02, el sistema ya usó su secuencia completa de creaciones de pedidos para la entrada y ejecutó ingeniería sobre esa secuencia. Aunque no hayamos calculado un RMSE en la presente compuerta, **no puede rebautizarse retrospectivamente O0 como evaluación prospectiva ciega**. El mismo razonamiento vale para cualquier utilización previa de O1/EV-01 que hubiera expuesto respuestas del mundo.

Para una comparación futura se propone **otro mundo independiente**, con ID, fuente y digest diferentes de construcción, y con **resultados de evaluación aislados** de los brazos/calibradores hasta congelar candidatos, semántica, operadores y parámetros. Un simple SHA o texto `SEALED` en un JSON **no demuestra** aislamiento OS/ACL, independencia real ni prueba prospectiva. La interfaz de metadatos solo valida su *forma* y niega promoción científica.

No se crea ahora ningún mundo nuevo, ni se abre evidencia reservada.

## 4. Propuesta de G3 y el límite predictivo

**Tipo de tarea propuesto:** `OFFLINE_CONDITIONAL_REPLAY_WITH_EXOGENOUS_ARRIVALS_KNOWN`. Si la Arena entrega al motor todos los timestamps de creación de pedidos de una ventana, la corrida reconstruye respuestas a una **entrada exógena conocida**. No es predicción prospectiva en tiempo real: un pronosticador en t=4 no habría conocido pedidos futuros de t=8. **No se afirmará** capacidad de forecasting online por aprobar ese replay.

**Observable primario propuesto:** entregas acumuladas, mismas unidades y frontera por operador científico H_j. **Métrica candidata, aún sin aprobación científica:** MAE de entregas acumuladas a t=2,4,6,8,10 min en el **mundo independiente nuevo**, comparando con sus salidas reservadas solo después de congelación. Los cinco tiempos son observaciones temporalmente dependientes de un mismo mundo, **no cinco réplicas independientes**. No se generan bandas, p-valores ni rankings ahora. Los pedidos de entrada no son scoring.

**Política causal:** la aproximación rectangular posterior al evento (`w=0.5min`) conserva masa pre-corte y cola diferida. Es una opción de ingeniería **no científicamente certificada**; su anchura no se optimiza utilizando resultados del futuro holdout. Se conserva el aviso de censura en t=10.

**Manejo de parámetros:** D debe declarar mediciones operacionales externas a otros brazos, una política de estimación prospectiva con datos de construcción admitidos **o abstenerse**; no se puede heredar el fixture. M puede legítimamente mantener sus priors fijos del registro original y no necesita imitar un estimador D. B debe ejecutar su método nativo EV-01 solo tras una autorización explícita de coste, fuente, cuota y procedimiento. Cualquier comparación de rendimiento sería condicionada por estas asimetrías y no una prueba automática de superioridad de métodos.

## 5. Compuertas automáticas y compuertas científicas

### Automático y verificable aquí

La CI descarga evidencia pública y los CSV congelados de D/M; usa `hj.build(...)` para **repetir las comprobaciones nativas de G2** y confirmar que el reporte RF-02H conservado coincide, y comprueba:
- 6 D + 6 M, cero modelos B nuevos, hashes de estructura y CSV, misma señal de entrada; ninguna selección ya registrada.
- Ausencia de parámetros D EV-01 estimados, conservación de priors M, ausencia de llamada B; `G3/G4/G5=NOT_RUN`.
- O0 original nunca etiquetado como holdout independiente, tiempos de scoring prospectivos documentados pero sin aplicación, ninguna curva de predicción exportada ni ranking.
- Metadatos de posible futuro mundo: rechazo de ID/sha de mundo compartido, mundo actual reciclado, test no sellado, resultado test consultado antes del registro, cambio de parámetro tras ver resultado, registro incompleto, o pretender forecast.
- Incluso un **manifiesto futuro sintácticamente válido** recibe `PASS_ONLY_UNVERIFIED_SELF_ATTESTATION` y `execution_authorized=false`, nunca G3=PASS.
- La función `deny_privileged_action` rechaza en aplicación `SCORE_G3`, `SELECT_WINNER`, `UNSEAL_EVALUATION_OUTCOMES`, `CALIBRATE_FROM_RESERVED_DATA`, `RUN_NATIVE_B_PROVIDER`, `PROMOTE_TO_G4` y `PROMOTE_TO_G5`.

### Pendiente de autoridad independiente y diseño

1. Aprobar la semántica operacional H_j, con sus fronteras de procesos y unidades; no imponer preparación a quien no la represente.
2. Definir si la comparación es de **replay condicional** (entrada futura conocida offline) o de **pronóstico online** (solo entradas hasta t); estos resultados no son intercambiables.
3. Definir origen y procedimiento independiente para nominales D, o su abstención; reconocer M como método de priors fijos.
4. Obtener generación B real con presupuesto/autorización separados, no reutilizar mocks ni historiales de otra ronda.
5. Crear y aislar nuevas observaciones reservadas con auditoría de accesos **R6** y congelación anterior a cualquier unsealing. Un digest, por sí solo, no protege contra un mismo proceso que tenga acceso a todos los datos.
6. Sólo entonces solicitar **una revisión del hito científico G3** (por ejemplo a Astra), no un veto a cada commit.

## 6. Estado que debe aparecer en todos los recibos

`R2=PARTIAL_CONTRACTS_ENGINEERING_ONLY`; `A3=PARTIAL`; `G3/G4/G5=NOT_RUN`; `result=ABSTAIN_G3_WITH_ARM_SPECIFIC_REASONS`; `scientific_measurement_equivalence=NOT_ESTABLISHED`; `scientific_parameter_admission=NOT_ESTABLISHED`; `no_scores=true`; `provider_calls=0`; `omc_invocations=0`.

**Aclaración:** G2 = PASS de ingeniería permanece verdadero para 6 D y 6 M en sus corridas históricas. La abstención presente **no invalida G2 ni la finalización del enumerador M**; impide únicamente afirmaciones científicas no sustentadas.

**Política de avance:** PR en Draft, pruebas automáticas y documentación de procedencia; no merge a `main` por inercia ni pedidos de aprobación a Astra para compuertas administrativas. La revisión independiente se reserva para levantar una afirmación científica real.
