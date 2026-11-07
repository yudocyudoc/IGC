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

## 5. Pendientes reales antes de un único lote CT-03

1. Custodio con cuenta/credenciales distintas, mundo único fijado, ejecución privada y liberación t0,t1,t2,t4 sin filtrar t6/t8.
2. Workflow autorizado único que integre el ejecutor D/M de diez, el B original y su observable G1/G2, las revisiones M y B cuando procedan y los límites globales; el script de diez todavía **no es el job completo**.
3. Ensamblado de la fila B con evidencia auténtica, integración con las doce D/M, sellado de las trece plazas en GitHub **antes de abrir la reserva**, evaluación MAE y baselines únicamente por el custodio.
4. Fallos por ruta conservados; ningún retry, selección posterior de mundo, intercambio de feedback o reparación Arena.

**Costo:** CT-02 gastó 2 OMC. CT-03: **0 OMC, 0 POST Buffalo, 0 DES hasta ahora** y aún sin autorización. Techo CT-03 inalterado: **21 OMC / 2 POST**; con D0/M0 válidamente reutilizados, gasto nuevo máximo para el mismo caso: **19 OMC**. Estos topes no son un permiso ni un compromiso de gastar todas las llamadas.

**Siguiente hito:** completar la conexión B + revisión física + ensamblado 13 filas y desplegar la custodia efectiva. Después habilitar **una sola vez** el lote CT-03, sin pedir permiso por cada archivo y sin otra capa criptográfica.
