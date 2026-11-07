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


## Continuación posterior a F172-09 · feedback físico B y entrega al lock (7 nov.)

**Implementado y probado offline, no ejecutado CT-03.** La rama F172-09
conserva el intento físico B fallido con su nativo como `G2_FAILED`, recibo
de OMC y ausencia explícita de traza/pronóstico. No sustituye `NO_NATIVE` ni
autoriza retry. Las pruebas cubren fallo inicial, fallo revisado y los
trece denominadores.

### B: el resultado físico ya puede llegar a la segunda decisión

Antes, `ct03_b_own_feedback` preparaba el feedback G1 aun sin resultado
numérico: útil ante fallos de traducción, pero insuficiente cuando el propio
modelo **sí** había sido simulado. El nuevo
`ct03_b_physical_feedback.py` consume el reporte G1 anterior, el nativo
y recibo originales, el plan físico y **reproduce con los bytes de entrada**
el verificador del resultado físico. Sólo entonces:

- Si la corrida B es admisible, añade G3 con sus **cuatro residuos propios**
  de t0,t1,t2,t4, la conservación y la identidad de su CSV; **jamás** añade
  predicciones reservadas t6/t8 al paquete transmitido a Buffalo.
- Si la corrida B fue efectivamente intentada pero falló, añade un G2 con
  clase/motivo, recibo, código de ejecución y **sin** trayectoria inventada.
- Continúa mediante un backup del **mismo ledger F1a/ATMS**; agrega revisiones
  append-only del diagnóstico y conocimiento, conservando la consulta
  temporal G1 anterior. No crea un segundo motor de memoria.
- Recupera el feedback actualizado por ATMS **antes** de construir el paquete
  para `Engine.generate(currentModel)`; el contrato JavaScript permite un G2
  sin CSV solamente con recibo y causa tipados.

El reporte B inicial de G1 sigue siendo la justificación del **plan inicial**;
el feedback G2/G3 posterior es la justificación de la **segunda llamada**.
`ct03_b_lock_projection` exige ambos reportes explícitos cuando corresponde,
sin reemplazar uno por el otro. Los tests conservan ratificación real de nativo
idéntico y el bloqueo de una revisión sin padre o feedback acreditados.

La ejecución física futura, **sólo tras autorización específica del lote**,
dispone de `ct03_b_physical_execute_once.sh`: por defecto se niega a
ejecutar, comprueba SHA, `workflow_dispatch`, primer intento, plan y fuente
nativa antes de OMC, considera el límite de diecinueve intentos nuevos
(incluidos mundo, diez D/M, revisiones M y físicos B) y registra una sola
invocación por nativo original/revisado. El resultado es un reporte de éxito
o G2 fallido, nunca un reintento oculto. **Esta comprobación local de
contabilidad no autentica por sí misma las ejecuciones del custodio ni
reemplaza el workflow global pendiente.**

### Entrega exacta a la reserva

`ct03_producer_freeze_handoff.py` reutiliza
`ct03_assemble_entries.assemble` y el registro de trece plazas. Acepta
las doce filas D/M, la plaza B, la construcción pública, el compromiso de
custodia y los manifiestos originales. Produce exclusivamente:

`construction.json`, `world-commitment.json`,
`D/manifest.json`, `M/manifest.json`, `entries.json`.

Es exactamente el conjunto permitido por
`arena-ct03-freeze-predictions.yml`; un error de fuente, mundo,
protocolo, identidad o número de plazas detiene el empaquetado. **El
empaquetado NO crea el lock ni lo archiva.** La ejecución del workflow
de archivo sigue siendo un acto posterior en Actions, y la apertura
del evaluador sigue condicionada a verificar ese archivo anterior.

### Comandos de conexión preparados, no órdenes de ejecución live

```bash
# Después de G1 original y resultado B físico del lote autorizado.
python -m scripts.arena_cafe.ct03_b_physical_feedback \
  --native producer-B/initial/native-engine-result.json \
  --receipt producer-B/initial/receipt.json \
  --construction public-release/construction.json \
  --g1-dir artifacts/ct03-producer/B-own-feedback \
  --initial-plan artifacts/ct03-producer/B-physical/plan.json \
  --physical artifacts/ct03-producer/B-physical/physical-result.json \
  --physical-root artifacts/ct03-producer/B-physical \
  --recorded-at <UTC_POSTERIOR_A_G1_Y_AL_INTENTO> \
  --out artifacts/ct03-producer/B-physical-feedback

# La respuesta B revisión, si llega realmente, usa:
# --review-feedback .../B-physical-feedback/status.json
# --review-packet .../B-physical-feedback/own-revision-packet.json
# en ct03_b_lock_projection. El plan revisado recibe ese paquete
# y el recibo del mismo currentModel, nunca la respuesta de otro B.

# Una vez existan las doce y una filas legítimas:
python -m scripts.arena_cafe.ct03_producer_freeze_handoff \
  --dm-projection artifacts/ct03-producer/dm-twelve-lock-rows.json \
  --b-projection artifacts/ct03-producer/B-thirteenth-row.json \
  --construction public-release/construction.json \
  --commitment public-release/world-commitment.json \
  --d-manifest artifacts/ct03-producer/dm-ten/D/manifest.json \
  --m-manifest artifacts/ct03-producer/dm-ten/M/manifest.json \
  --out artifacts/ct03-producer/public-freeze-handoff
```

**CI comprobada para esta entrega:** regresiones
[42422819276](https://github.com/yudocyudoc/IGC/actions/runs/42422819276)
e integración
[42422819259](https://github.com/yudocyudoc/IGC/actions/runs/42422819259),
ambas exitosas, sin `physical-m3`, proveedor ni física nuevos.
La prueba del bundle ejecuta un sellado **en memoria con fixture**,
no un lock prospectivo real.

**Pendiente operativo real:** desplegar custodio externo y su corrida
de mundo único, workflow global CT-03 que encadene los ejecutores originales
D/M/B con controles y presupuesto comunes, publicar sólo el paquete público,
archivar el lock en Actions y luego permitir que el custodio lea t6/t8.
CT-03 sigue en **0 OMC nuevos, 0 POST Buffalo, 0 DES**;
CT-02 conserva sus dos simulaciones históricas consumidas.
No se habilita este piloto por un push, CI verde o el presente documento.


## CT-03 · Productor único preparado por workflow manual (continuidad posterior a Astra d3cc94a)

**Alcance:** se cerró F172-09 offline, sin un defecto nuevo reproducido en la revisión independiente. Esta continuación prepara el productor global **sin dispararlo**. Continúa vigente la hoja v4.0 y el protocolo CT-03: no se amplían motores, métodos, mundo, parámetros, presupuesto ni métrica.

### Dos fronteras y una contabilidad compartida

- `.github/workflows/arena-ct03-public-intake.yml` es una **recepción manual** de los únicos tres JSON ya liberados por el custodio externo: `construction.json`, `world-commitment.json`, `release-status.json`. Recibe únicamente sus bytes base64 públicos, exige SHA40 de código congelado, rechaza la reserva y coteja los cuatro cortes, hashes y protocolo mediante `ct03_public_intake.py`. **No selecciona, ejecuta ni acredita por sí mismo la independencia del custodio.** Este último tiene que elegir y simular su único mundo bajo cuenta/credenciales privadas **antes** del intake; no debe aportar modelo, semilla ni CSV íntegro.
- `.github/workflows/arena-ct03-producer.yml` define un **lote único manual**, con aprobación de SHA, run anterior de intake, `authorized=yes`, máximos `max_new_omc=19` y `max_provider_posts=2`, primer intento, rama congelada y aprobación adicional en variables `CT03_APPROVED_FREEZE_SHA`, `CT03_APPROVED_RELEASE_RUN_ID`, `CT03_EXTERNAL_CUSTODIAN_ACK=external_private_world_attempted_once`. El nombre de un environment **no garantiza** required reviewers: se deben configurar efectivamente. Una segunda ejecución manual se rechaza conservadoramente hasta adjudicación de incidentes, pues la primera podría haber consumido presupuesto.
- El job D/M reutiliza D0/M0 del run físico CT-02 **sin nuevas simulaciones**; ejecutaría únicamente D1–D5, M1–M5, feedback propio y revisiones M2 seleccionadas. El job B recibe sólo el paquete público y `dm-budget.json` de `ct03_lot_budget.py`: **no monta modelos, CSV ni ledger D/M**. El recibo cuenta mundo 1 + originales 10 + revisiones M 0–6; B puede gastar 0–2 OMC, sin rebasar 19. Exige mismo GitHub run, SHA, mundo y hash de fuente pública, incluso antes del primer POST.
- B original ejecutaría la ruta existente `arena_b_ct03_native_runner.mjs` máximo una vez; conservaría `NO_NATIVE`, G1 bloqueado, G2 fallido o G3, con feedback propio F1a/ATMS y una revisión real `Engine.generate(currentModel)` máximo una vez. `ct03_b_producer_rounds_once.sh` orquesta ambas fases y el ejecutor B físico existente. Un error irreversible detiene el lote; no hay retries, reparación automática ni proveedor de respaldo.
- El job de cierre une las doce plazas D/M con la única B y emite **sólo** los cinco archivos autorizados `arena-ct03-producer-public-and-forecasts`. No dispone de parámetros/CSV del mundo verdadero. El workflow separado `arena-ct03-freeze-predictions.yml` ahora exige origen exacto: productor manual exitoso, mismo SHA, primer intento, rama y ruta de workflow, y genera el archivo prospectivo **en otro run**. Antes de ese archivo no se abre la reserva del evaluador.

### Rectificación de interoperabilidad B

En el runner original CT-03, `own_feedback_sha256` del recibo se calculaba con `JSON.stringify` de JavaScript; la proyección Python exigía `digest(packet)` de bytes canónicos ordenados. No son hashes equivalentes en general. El runner de caso ahora registra SHA-256 de los **bytes canónicos UTF-8 del paquete exportado por Python**, quitando exactamente el LF final exigido, sin resintetizar el contenido JS ni alterar el motor original. La integración mock real del runner verifica igualdad exacta con `digest(packet)`. Es un arreglo de procedencia de la segunda llamada, no otro método predictivo.

### Cuándo puede intentarse un lote real

Esta preparación **no autoriza** lanzar intake, productor, Buffalo, OMC ni un lock. Antes de hacerlo faltan: custodio externo separado realmente desplegado con su único intento privado; revisión humana del congelado, aprobación efectiva de environments/variables y credenciales por rol; registro de los workflows manuales en la rama por defecto para permitir `workflow_dispatch` **sin fusionar automáticamente PR #171/#172**; evidencia pública válida; y una autorización explícita del lote completo. Ni el intake ni el productor deben obtener claves del custodio. Cualquier fallo o ejecución parcial queda para adjudicación, no se despacha un nuevo run automáticamente.

**Costos a la fecha de esta preparación:** CT-02 = 2/2 OMC históricos técnicos; CT-03 = **0 OMC, 0 POST Buffalo, 0 DES**. Mundo no seleccionado, verdad reservada no abierta, trece predicciones reales no selladas. CI y fixtures no son un resultado G3 ni prueba de acceso aislado. Ningún evaluador ni scoring se ejecuta en los nuevos workflows.
