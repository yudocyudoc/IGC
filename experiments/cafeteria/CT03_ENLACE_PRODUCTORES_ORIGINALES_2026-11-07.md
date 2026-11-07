# CT-03 · Enlace de productores originales

**Corte 2026-11-07:** trabajo técnico preparado y probado sin costo de física nueva. **NO AUTORIZADO NI EJECUTADO CT-03.** No hay mundo seleccionado, reserva abierta ni nuevas llamadas Buffalo. CT-02 técnico quedó cerrado: OMC real D0/M0, run 42409210062, 2/2 intentos gastados. El PR #172 permanece Draft, sin merge.

Este documento complementa la hoja de ruta v4 y el protocolo CT-03; no modifica generadores, motores, ecuaciones, políticas, parámetros, Euler, horizonte, métricas o denominadores. Custodia procedimental, RSA externa opcional, sin otra auditoría general.

## Fronteras entre roles

El custodio guarda el modelo verdadero, parámetros, CSV íntegro y t6/t8 en credenciales y almacenamiento no disponibles para productores. Publica únicamente el pulso y las observaciones t0,t1,t2,t4. D/M/B reciben exactamente esos cuatro cortes, sus propios originales, sus propios modelos y su lane de ledger/ATMS. El evaluador lee la reserva **solo después** de verificar el lock archivado. Carpetas separadas dentro de la misma cuenta no cumplen la frontera.

## 1. Dos iniciales reutilizables: D0 y M0

El job de [E01, run 42411052819](https://github.com/yudocyudoc/IGC/actions/runs/42411052819) descargó el artefacto físico CT-02 13588621967, validó fuente en GitHub, modelo nativo, comandos, entorno y hashes. Sólo se reutilizan las consecuencias deterministas de D0/M0. No se reutilizan diagnósticos, feedback, decisiones ni resultados verdaderos de otro mundo. Si esa identidad falla, parar: no repetir en silencio.

## 2. Diez iniciales D1–D5 y M1–M5

El preparador de producción crea, sin OMC, diez scripts separados, cada uno con una simulación del modelo original íntegro:

```bash
python -m scripts.arena_cafe.ct03_dm_initial_batch prepare \
  --out artifacts/ct03-producer/dm-ten \
  --reuse-report artifacts/ct03-reuse/reused-original-two.json
```

El ejecutor futuro es scripts/arena_cafe/ct03_dm_execute_ten_once.sh. **No invocarlo aún**. Deniega por defecto y exige workflow_dispatch, SHA congelado, primer intento, autorización explícita CT-03 y cuota total del lote. Conserva intento, stdout/stderr, Modelica, CSV y resultado de cada candidato, sin reintentos. Una ruta fallida produce un recibo G2_FAILED y no un pronóstico cero. Las otras rutas pueden continuar.

Las pruebas CI ejecutan **el Bash real con un Docker simulado** y fuerzan el fallo de M3: diez intentos, nueve resultados válidos, un fallo G2 registrado, sin física auténtica. El gate verifica D mediante la conservación original D y M sumando las colas materiales E1 de su AST más entregas acumuladas; ambos se contrastan con el pulso de 3.4 unidades. La fórmula de M fue contrastada también con el verdadero CSV de CT-02.

## 3. Diagnóstico propio, ledger, ATMS y decisiones D/M

Después de ejecutar el lote **real autorizado**, con resultados verdaderos propios y sólo construcción pública:

```bash
python -m scripts.arena_cafe.ct03_dm_feedback_round \
  --ct02-root artifacts/ct03-reuse/original \
  --reuse-report artifacts/ct03-reuse/reused-original-two.json \
  --ten-root artifacts/ct03-producer/dm-ten \
  --construction public-release/construction.json \
  --recorded-at <UTC_REAL_POSTERIOR_A_LOS_RESULTADOS> \
  --out artifacts/ct03-producer/dm-feedback
```

Exige los doce padres originales y exactamente diez intentos físicos nuevos, no duplicados. Una ruta fallida conserva su plaza sin ejecutar una política falsa. Para cada ruta exitosa compara sólo t0,t1,t2,t4, registra el diagnóstico en ledger, recupera su propia evidencia mediante ATMS **antes** de la política, D ratifica su conjunto fijo y M usa la política M2 original sobre su AST completo. Persiste la decisión con soporte. Si M decide revisar, produce el nuevo Modelica con el renderer original; **la revisión exige su OMC separado antes del lock**.

La proyección al formato del cierre prospectivo genera sólo **12 filas D/M** y requiere resultados físicos para las revisiones elegidas:

```bash
python -m scripts.arena_cafe.ct03_dm_lock_projection \
  --dm-feedback artifacts/ct03-producer/dm-feedback/producer-12/dm-feedback-report.json \
  --d-manifest artifacts/ct03-producer/dm-ten/D/manifest.json \
  --m-manifest artifacts/ct03-producer/dm-ten/M/manifest.json \
  --revision-outcomes artifacts/ct03-producer/m-revision-outcomes.json \
  --out artifacts/ct03-producer/dm-twelve-lock-rows.json
```

No puede suplir un B faltante ni sustituir una revisión por su trayectoria inicial; los fallos G2 permanecen en el denominador.

## 4. Buffalo original → G1 → feedback propio

La preparación pública existente scripts/arena_cafe/ct03_b_visible.py alimenta el original scripts/arena_b_ct03_native_runner.mjs, que **no ha sido llamado live para CT-03**. Después de un resultado live genuino con recibo del propio B:

```bash
python -m scripts.arena_cafe.ct03_b_own_feedback \
  --construction public-release/construction.json \
  --native producer-B/initial/native-engine-result.json \
  --receipt producer-B/initial/receipt.json \
  --recorded-at <UTC_REAL_POSTERIOR_A_RESPUESTA> \
  --out artifacts/ct03-producer/B-own-feedback
```

Valida el padre/recibo B original, intenta traducir con el traductor G1 existente sin reparar ecuaciones, registra su diagnóstico G1, recupera su propio feedback por ATMS y prepara el paquete para la revisión con Engine.generate(currentModel) original. Si el modelo usa semántica no soportada, queda G1_TRANSLATION_BLOCKED, no G2 artificial. Una traducción válida **todavía no prueba un observable inequívoco de entregas acumuladas**; el enlace físico y la salida observable B permanecen pendientes.

### Extensión: observable físico B inicial, sin ejecutar

La retro del corte `06347b6` concluyó **sin defectos nuevos reproducidos** y pidió conectar el nativo B original con una observación inequívoca y OMC. Se añadieron dos módulos, sin cambiar el motor, el traductor, las ecuaciones o el protocolo:

- `scripts/arena_cafe/ct03_b_physical_prepare.py`: a partir del original `Engine.generate`, recibo live inicial y G1 del ledger B, invoca el **traductor original** y exige una salida semántica conservadora: exactamente un stock terminal de entregas explícitas, con valor inicial cero, una entrada material y sin salida, denominado en unidades de trabajo. Rechaza otros sumideros materiales ambiguos. Si no encuentra una designación inequívoca, registra **`B_OBSERVABLE_UNRESOLVED_NO_OMC`**, *no* un fallo G1 del modelo; la regla automática no agota todos los nombres o semánticas posibles. Si el traductor falla, registra separadamente `B_NATIVE_G1_TRANSLATION_BLOCKED_NO_OMC`. Si la salida es identificable, prepara **un solo** `initial.mos` con Modelica original sin agregar un contador ni ajustar por observaciones. Cero OMC en este paso.
- `scripts/arena_cafe/ct03_b_physical_result.py`: **después de que exista** una ejecución física B inicial autorizada, comprueba que modelo y comando coincidan, solver/log real 1.26.5, CSV íntegro t0–8, las predicciones propias t6/t8 de la columna nativa y la conservación de masa de los stocks materiales originales frente a las 3.4 unidades de entrada. No corre OMC ni consulta la reserva. El test de este módulo utiliza únicamente CSV y log **sintéticos**, no acredita que Buffalo ya haya sido simulado.

El preparador en una futura corrida productor usaría (nunca antes del B real y de la aprobación CT-03):

```bash
python -m scripts.arena_cafe.ct03_b_physical_prepare \
  --native producer-B/initial/native-engine-result.json \
  --receipt producer-B/initial/receipt.json \
  --construction public-release/construction.json \
  --b-feedback artifacts/ct03-producer/B-own-feedback/status.json \
  --out artifacts/ct03-producer/B-physical
```

Solo si el resultado es `B_NATIVE_PHYSICAL_PLANNED_NO_OMC`, el ejecutor autorizado puede efectuar el OMC de `initial.mos` (un intento, sin retry), conservar `b-original-omc.log` y `b-original_res.csv` y luego verificar con:

```bash
python -m scripts.arena_cafe.ct03_b_physical_result \
  --native producer-B/initial/native-engine-result.json \
  --receipt producer-B/initial/receipt.json \
  --plan artifacts/ct03-producer/B-physical/plan.json \
  --root artifacts/ct03-producer/B-physical \
  --git-sha <SHA_CONGELADO> --run-id <ID_RUN_REAL> \
  --out artifacts/ct03-producer/B-physical/physical-result.json
```

**Corrección F172-08 · P2 (retro del corte `9c3a8ec`):** la validación física B ya no confía únicamente en el orden de las predicciones t6 y t8. `ct03_b_physical_result.check` recorre **cada fila** de `cumulative_delivered` y rechaza cualquier disminución superior a `1e-8` unidades (tolerancia absoluta y fija, diferente de los `0.008` ítems del balance de masa). En marcas de tiempo duplicadas por eventos, exige valores iguales dentro de `1e-8`; admite redondeo pequeño, no un incremento inconsistente en el mismo instante. La retro reprodujo una caída artificial en t=3 que mantenía conservación y t6/t8 intactos; la nueva prueba verifica que falla. No suaviza el CSV, no obliga a `uniflow=true` ni repara ecuaciones Buffalo. **Esta es conformidad de interfaz, no un solver B real.** CI: [regresiones 42416877943](https://github.com/yudocyudoc/IGC/actions/runs/42416877943), [integración E01 42416877780](https://github.com/yudocyudoc/IGC/actions/runs/42416877780), ambas exitosas, sin nuevo consumo.

El flujo B **revisión → posible nuevo nativo → segunda física → decisión final** y el ensamblado de 13 filas continúan pendientes. No afirmar B G2, pronóstico real ni disponibilidad del piloto antes de ejecutar esas etapas y comprobar su evidencia.

### Extensión: cierre M revisado, Buffalo currentModel y trece entradas (sin activación)

Tras la retro del corte `978ef05` se conectaron los tres pasos que antes eran manuales:

**Revisiones M seleccionadas.** `scripts/arena_cafe/ct03_m_revision_physical.py` comprueba cada Modelica de la política M2 original, el padre/AST, el script, las bibliotecas, la prueba material, el CSV y el log contra **un intento físico diferente**. Entrega `m-revision-outcomes.json`, con `PREDICTED` o `G2_FAILED` por revisión; los fallos no se convierten en ceros. `scripts/arena_cafe/ct03_m_revision_execute_once.sh` es el ejecutor reservado a un eventual **único lote CT-03 autorizado**: requiere `workflow_dispatch`, SHA congelado, intentos iniciales contabilizados y tope global 19 OMC si siguen reutilizados D0/M0. Revisa todos los padres antes del primer OMC, ejecutaría cada seleccionado una sola vez, conservando salida y recibo. **No está conectado aún a un workflow autorizado ni se ha ejecutado.**

**Revisión B real.** La preparación física original `ct03_b_physical_prepare.py` admite ahora una *revisión explícita* solo si existe la respuesta native original del segundo `Engine.generate(currentModel)` y su recibo con enlace al padre inicial y al paquete de feedback ATMS propio. Vuelve a traducir el modelo revisado mediante el traductor original, comprueba el observable y prepara un `initial.mos` propio **en otro directorio**; el comprobador físico B existente puede validar después su CSV de esa revisión. Una respuesta idéntica ratifica y reutiliza la consecuencia original, **sin un OMC adicional**. Un cambio requiere nuevo resultado físico o bloqueo nativo documentado; jamás se copia como revisión la traza inicial.

**Trece plazas.** `ct03_b_lock_projection.py` compone la plaza B a partir de las respuestas originales de Buffalo, su propia recuperación de feedback, los reportes de G1/observable y la consecuencia física (o fallo). Distingue segunda respuesta idéntica `RATIFIED`, segunda respuesta cambiada `REVISED`, parada explícita `NOT_EXECUTED` y **ausencia auténtica de nativo B** como `NO_NATIVE`, manteniendo el candidato en el denominador. `ct03_assemble_entries.py` reúne esa plaza con las doce D/M de `ct03_dm_lock_projection.py` y valida las trece con el registro y esquema del **lock original**, sin consultar parámetros privados. Su salida es solo `entries.json`, **no un lock archivado**.

Comandos de preparación posterior a los resultados físicos **del lote autorizado**, nunca con fixtures sintéticos:

```bash
# Después de una corrida original de M/revisiones bajo el mismo run:
python -m scripts.arena_cafe.ct03_m_revision_physical \
  --dm-feedback artifacts/ct03-producer/dm-feedback/producer-12/dm-feedback-report.json \
  --dm-root artifacts/ct03-producer/dm-feedback \
  --m-manifest artifacts/ct03-producer/dm-ten/M/manifest.json \
  --run-id <RUN_REAL> --git-sha <SHA_CONGELADO> \
  --out artifacts/ct03-producer/dm-feedback/producer-12/m-revision-outcomes.json

# Consumir directamente el reporte completo de revisiones M; se
# comprueban identidad del caso, conteos y hashes de recibos por padre:
python -m scripts.arena_cafe.ct03_dm_lock_projection \
  --dm-feedback artifacts/ct03-producer/dm-feedback/producer-12/dm-feedback-report.json \
  --d-manifest artifacts/ct03-producer/dm-ten/D/manifest.json \
  --m-manifest artifacts/ct03-producer/dm-ten/M/manifest.json \
  --revision-outcomes artifacts/ct03-producer/dm-feedback/producer-12/m-revision-outcomes.json \
  --out artifacts/ct03-producer/dm-twelve-lock-rows.json

# Solo después del B original y revisión verdaderos o parada documentada:
python -m scripts.arena_cafe.ct03_assemble_entries \
  --dm-projection artifacts/ct03-producer/dm-twelve-lock-rows.json \
  --b-projection artifacts/ct03-producer/B-thirteenth-row.json \
  --construction public-release/construction.json \
  --d-manifest artifacts/ct03-producer/dm-ten/D/manifest.json \
  --m-manifest artifacts/ct03-producer/dm-ten/M/manifest.json \
  --out artifacts/ct03-producer/entries.json
```

La compilación JSON, por sí sola, **no habilita abrir t6/t8**. El flujo de archivo de predicciones en GitHub debe recibir `entries.json` y producir el lock en un run aparte ANTES de que el custodio acceda a la reserva. Faltan la orquestación global, el ejecutor B completo y el despliegue con cuenta/credenciales realmente separadas. Ninguna de estas funciones nuevas ejecuta al proveedor ni al solver por sí misma; las pruebas son **fixtures sintéticos**.

## 5. Pendientes reales antes de un único lote CT-03

1. Custodio con cuenta/credenciales distintas, mundo único fijado, ejecución privada y liberación t0,t1,t2,t4 sin filtrar t6/t8.
2. Workflow autorizado único que integre el ejecutor D/M de diez, el B original y su observable G1/G2, las revisiones M y B cuando procedan y los límites globales; el script de diez todavía **no es el job completo**.
3. Ensamblado de la fila B con evidencia auténtica, integración con las doce D/M, sellado de las trece plazas en GitHub **antes de abrir la reserva**, evaluación MAE y baselines únicamente por el custodio.
4. Fallos por ruta conservados; ningún retry, selección posterior de mundo, intercambio de feedback o reparación Arena.

**Costo:** CT-02 gastó 2 OMC. CT-03: **0 OMC, 0 POST Buffalo, 0 DES hasta ahora** y aún sin autorización. Techo CT-03 inalterado: **21 OMC / 2 POST**; con D0/M0 válidamente reutilizados, gasto nuevo máximo para el mismo caso: **19 OMC**. Estos topes no son un permiso ni un compromiso de gastar todas las llamadas.

**Siguiente hito:** completar la conexión B + revisión física + ensamblado 13 filas y desplegar la custodia efectiva. Después habilitar **una sola vez** el lote CT-03, sin pedir permiso por cada archivo y sin otra capa criptográfica.
