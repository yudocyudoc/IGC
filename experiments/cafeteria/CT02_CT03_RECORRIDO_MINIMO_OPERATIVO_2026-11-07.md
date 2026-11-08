# Arena IGC · Recorrido operativo mínimo CT-02 → CT-03

**Estado (2026-11-07, posterior al run 42409210062):** **CT-02 aceptado como preparación y conformidad técnica acotada de D0/M0** (2 de 2 OMC consumidos, sin reintento). **CT-03 aún no autorizado ni ejecutado**; no hay mundo elegido, llamadas Buffalo, predicciones selladas, evaluación reservada ni resultado científico prospectivo. Basado en la hoja vigente `ARENA_IGC_HOJA_DE_RUTA_V4_0_2026-11-07.md`, sin cambiar métodos, métricas ni límites. El antiguo conjunto de firmas/atestaciones RSA es **opcional y no se invoca** en esta ruta piloto. Se conserva el PR #172 en Draft y el protocolo CT-03 actual.

> **Actualización operativa posterior a F172-10/11, 7-nov-2026:** el workflow productor global **ya existe** y pasó CI offline. Las frases históricas de este documento que decían «pendiente cableado live» se refieren al corte anterior y no deben usarse como estado actual. El estado vigente de habilitación, sin datos privados, es [CT03_HABILITACION_OPERATIVA_LOTE_2026-11-07.md](CT03_HABILITACION_OPERATIVA_LOTE_2026-11-07.md): registrar los tres workflows en `main` (no presentes aún), acreditar environments/custodio y autorizar un único lote. No fusionar automáticamente #171/#172 ni gastar CT-03 por el mero hecho de que CI sea verde. **El workflow de freeze debe despacharse en la misma rama y SHA del productor, NO en `main`, porque ambos verifican SHA exacto.**


## 1. Congelar una única versión y habilitar un lote, no cada archivo

La revisión se realiza **una vez por lote**, antes de seleccionar mundo o abrir resultados. Registrar el SHA completo del commit que contiene protocolo, D/B/M, adaptadores, fuente de mundo, métrica y workflow. El protocolo ya fija Euler 0–8 h, 64 intervalos (dt=0.125 h), OpenModelica 1.26.5, MSL 4.0.0 y SystemDynamics 2.1.2. No escoger otro solver según el resultado.

Los workflows manuales nuevos deberán estar incorporados a la **rama por defecto** para estar disponibles mediante `workflow_dispatch`. **No fusionar PR #172 automáticamente** ni inferir autorización a partir de un push. Configurar, si se desea, required reviewers del environment `arena-ct02-physical`; su sola denominación no concede protección.

### CT-02 · Lote técnico de conformidad: exactamente 2 simulaciones OMC

Candidatos fijados antes de ver datos: D inicial #0 de la gramática original y M inicial #0 del compositor Short E1. **No son candidatos seleccionados por error.** D produce `delivered`; M produce la variable raíz `deliveredTotal`. Los otros diez candidatos no se simulan en este lote. No hay mundo CT-03 ni datos reservados.

**Lote YA EJECUTADO; no volver a dispararlo.** El único comando autorizado que se usó, registrado históricamente para reproducibilidad (NO ejecutar nuevamente), es:

```bash
gh workflow run arena-ct02-minimal-physical.yml \
  --repo yudocyudoc/IGC \
  --ref experiment/arena-ct00-ct02-20261107 \
  -f authorized=yes -f budget=2 -f freeze_sha=<SHA40_DE_ESA_RAMA>
```

Este job se dispara **exclusivamente** por `workflow_dispatch`. GitHub exige que el archivo del workflow esté registrado en la rama por defecto, pero `--ref` puede seleccionar la rama experimental sin fusionar toda la cadena #171/#172. Si se usa `--ref main`, el SHA debe ser el de `main`, no el experimental. Confirma el SHA de checkout, la autorización y presupuesto 2 antes de preparar scripts. Descarga bibliotecas originales por tags fijados, anota sus commits e identidad de imagen, ejecuta:

```bash
docker run --rm --network none --user "$(id -u):$(id -g)" \
  -v "$PWD:/repo" -w /repo \
  -v "$RUNNER_TEMP/e1-home:/omhome" -e HOME=/omhome \
  -v "$RUNNER_TEMP/e1-libs:/thirdparty:ro" \
  -e OPENMODELICALIBRARY=/thirdparty/msl:/thirdparty/systemdynamics \
  openmodelica/openmodelica:v1.26.5-minimal \
  omc artifacts/ct02-exact-two/D-single.mos

# Solo si D completó y produjo su CSV:
# misma invocación Docker, usando M-single.mos
```

Los scripts tienen **un `simulate(...)` cada uno** y conservan los Modelica/AST completos. No hay retry. Antes de cada llamada se añade una línea a `attempts.log`. El artefacto `arena-ct02-technical-attempt-<run_id>` conserva siempre que existan: `D/M-single.mos`, `D/M-omc.log`, `d00_res.csv`, `m00_res.csv`, fuentes, manifiestos, `attempts.log`, `runtime-identity.txt` y `conformity.json` solo si ambas pruebas pasan.

**Parada:** inmediatamente después de ejecutar D, `verify-arm --arm D` comprueba versión, fuente, script, horizonte y **balance material** antes de consumir M; tras M aplica el mismo chequeo específico, y solo si ambos pasan produce el reporte agregado. Si la primera falla, la segunda no se ejecuta; un fallo cuenta como intento consumido. Si falta cualquier CSV o log, el solver/versión/columna difiere, no hay 0–8 h completos, el balance material D no cierra o falta un corte nativo M, no declarar aceptación técnica ni correr repeticiones para «arreglar» datos. El presupuesto **máximo 2**, no una obligación de gastarlo. Dejar `physical-m3` sin ejecutar. Ninguna llamada al proveedor.


### Reutilización sin repetir CT-02: D0 y M0 como consecuencias iniciales de CT-03

La implementación `scripts/arena_cafe/ct03_reuse_ct02.py` y el job **sin OMC** `ct03-reuse-authentic-ct02-originals` de `.github/workflows/arena-continuity-e01.yml` recuperan el archivo auténtico del [run 42409210062](https://github.com/yudocyudoc/IGC/actions/runs/42409210062), artefacto GitHub **13588621967**, y verifican en GitHub su procedencia (run/SHA/evento/intento/ID/digest), los dos manifiestos, fuente D/M original recién generada, modelo, script, runtime (OpenModelica 1.26.5, MSL/SystemDynamics, imagen Docker), logs y CSV. No inventan recibos de proveedor ni ejecutan otro solver.

**Resultado confirmado:** D inicial índice 0 y M inicial índice 0 son **elegibles para reutilizar su consecuencia numérica** con el mismo pulso, estado inicial, parámetros, horizonte, biblioteca, solver y operador. Sus pronósticos propios t6/t8 son D=(3.379100198824965, 3.39753242195592) y M=(3.398933866844736, 3.399984796863248). Estos números **no son y6/y8 reservados**, no se han puntuado contra el mundo ni prueban feedback. No se reutilizan observaciones del mundo, decisiones, diagnósticos, ledger o feedback: se calcularán para el caso CT-03 nuevo, después de liberar solamente t0/t1/t2/t4. Reutilizar consecuencia numérica no permite saltarse la decisión inicial/final ni el lock.

El plan CT-03 mantiene **techo 21 OMC y 2 POST B**, no ya gastados ni autorizados. Si se conservan las identidades comprobadas, las dos iniciales reutilizadas reducen el **máximo gasto OMC nuevo del mismo lote a 19**, sin alterar sus 13 slots (1 mundo + 5 D restantes + 5 M restantes + 1 B inicial + hasta 6 revisiones M + 1 B revisión). Si la identidad se pierde, la ruta se **detiene** y el coste adicional necesita su aprobación correspondiente; no repetir silenciosamente D0/M0.

**Hito siguiente real:** completar el job productor único que realiza el resto del recorrido: proponer D/M originales y B inicial con el adaptador Cloudflare, registrar fallos/consecuencias originales, construir *su* feedback con observaciones de CT-03, recuperarlo mediante ATMS antes de políticas M/D/B, ejecutar únicamente las revisiones disparadas por política, emitir predicciones iniciales/finales de los trece slots y cerrar lock de Actions antes del evaluador. Los adaptadores y tests aislados existen; **la conexión live integral aún no existe**. El custodio real debe demostrar inaccesibilidad de secretos/CSV privado al job productor, no solo rutas disjuntas. Este requisito de operación es una compuerta CT-03, no repetir el ciclo prospectivo como supuesto requisito CT-02.

La hoja vigente es el documento rector: no añadir otra auditoría general, RSA obligatoria, grilla, selección de mundo por acierto ni física extra para «probar» el primer piloto.

## 2. Custodio del mundo CT-03: entorno y cuenta separados

**Requisito real:** el custodio humano usa cuenta o entorno propio, con datos y permisos *no accesibles* a los jobs de productores, sus credenciales ni a los artefactos descargables por ellos. El código añade un rechazo de rutas que se solapan, **pero carpetas diferentes bajo la misma cuenta no certifican aislamiento**. Se declara `PROCEDURAL_HUMAN_NO_EXTERNAL_SIGNER`.

**Solo después de congelar método y autorizar el lote CT-03:** el custodio elige UNA configuración de dos o tres etapas y parámetros en los intervalos predefinidos, sin buscar el mejor escenario ni revelar valores. Conserva bajo su cuenta el archivo privado `world-config.json` con `world_public_id`, `stage_count`, `capacity`, `response_time`, `custody_nonce` de alta entropía y `protocol_sha256` igual al digest del protocolo congelado. El archivo **no entra al repositorio ni a Actions**.

Preparación, con `$PRIVATE_BASE` **fuera del checkout y no montado en ningún job de productores**:

```bash
IGC_CT03_CUSTODIAN_AUTH=CT03_POST_LOCK_CUSTODIAN_ONLY \
python -m scripts.arena_cafe.ct03_world_custody \
  --sealed-config "$PRIVATE_BASE/world-config.json" \
  --private-out "$PRIVATE_BASE/world-run" \
  --producer-root "$PRODUCER_CHECKOUT" \
  --public-commitment "$PRIVATE_BASE/world-commitment.json"
```

El custodio reproduce la instalación de librerías e imagen fijadas por el workflow técnico, y corre **una** simulación privada con esos mounts (el repositorio solo lectura):

```bash
docker run --rm --network none --user "$(id -u):$(id -g)" \
  -v "$PWD:/repo:ro" \
  -v "$PRIVATE_BASE/world-run:/private" -w /private \
  -v "$RUNNER_TEMP/e1-home:/omhome" -e HOME=/omhome \
  -v "$RUNNER_TEMP/e1-libs:/thirdparty:ro" \
  -e OPENMODELICALIBRARY=/thirdparty/msl:/thirdparty/systemdynamics \
  openmodelica/openmodelica:v1.26.5-minimal omc simulate.mos \
  2>&1 | tee "$PRIVATE_BASE/world-run/world-omc.log"
```

**Atención:** ejecutar bajo `set -o pipefail` para que el error de OMC no se esconda por `tee`. Si falta `sealed_world_res.csv` o falla el contrato, custodio detiene la entrega; no cambia mundo o parámetros para mejorar a un brazo.

Con el CSV completo aún privado, el custodio publica **solo cuatro observaciones**:

```bash
python -m scripts.arena_cafe.ct03_minimal_custody \
  --producer-root "$PRODUCER_CHECKOUT" \
  --private-dir "$PRIVATE_BASE/world-run" \
  --commitment "$PRIVATE_BASE/world-commitment.json" \
  --public-out "$PRIVATE_BASE/public-release"
```

Archivos públicos *únicos*: `construction.json` (t0,1,2,4), `world-commitment.json` y `release-status.json`. No se exportan `private_world.mo`, configuración, script privado, logs, CSV completo ni y6/y8. Solo se entregan esos tres archivos a los productores. El custodio conserva el original de la ejecución, su run/log, configuración y reserva.

## 3. Productores D/M/B: solo la construcción y sus propias rutas

Todos reciben el mismo `construction.json` y la definición pública de pulso. D prepara los seis candidatos fijos nominales; M prepara **seis AST completos** (tres proyecciones materiales), y cada padre consulta su feedback propio en ledger/ATMS. B usa su `Engine.generate()` original y como máximo una revisión `currentModel`, sin reparaciones por Arena. Los archivos de productor y su trabajo OMC deben estar en jobs **sin ninguna credencial o mount del custodio**.

Comandos de preparación, sin ninguna simulación:

```bash
python -m scripts.arena_cafe.ct03_d_prepare --out producer-artifacts/D
python -m scripts.arena_cafe.ct03_m_prepare --out producer-artifacts/M
```

Las simulaciones CT-03 requieren una **autorización de lote independiente**: máximo **21 OMC** (1 mundo + 6 D + 6 M + 1 B inicial + hasta 6 M revisiones + 1 B revisión), y máximo **2 POST** Buffalo (inicial + revisión). D2 no se aplica sin ensayo reiniciado. Fallos G1/G2/timeout/ausencia de padre permanecen en el denominador; no se llenan con ceros, no se repiten o sustituyen llamadas, ni se repara un motor por la puntuación.

**Estado actualizado tras el cierre independiente F172-10/11:** el job global CT-03 y sus rutas B/D/M/feedback/trece plazas están cableados y probados en CI con replays **offline**; CT-02 fue aceptado como preparación con las dos conformidades OMC originales. **Falta habilitación operativa real** (registro de workflow por defecto, custodia independiente, environments protegidos, autorización explícita y ejecución física auténtica). No crear un `entries.json` sintético para representar el piloto. Ver [hito operativo](CT03_HABILITACION_OPERATIVA_LOTE_2026-11-07.md).

## 4. Cierre prospectivo y puntuación (nunca en el mismo job)

Con propuestas, diagnósticos y decisiones reales, el productor registra los 13 slots inicial/final, incluyendo los fallidos, en `entries.json`. Antes de abrir t6/t8, se genera un lock de predicciones propias:

```bash
python -m scripts.arena_cafe.ct03_prospective_lock \
  --construction public-release/construction.json \
  --commitment public-release/world-commitment.json \
  --d-manifest producer-artifacts/D/manifest.json \
  --m-manifest producer-artifacts/M/manifest.json \
  --entries producer-artifacts/entries.json \
  --out producer-artifacts/lock.json
```

El paquete del productor para GitHub contiene **exactamente** `construction.json`, `world-commitment.json`, `D/manifest.json`, `M/manifest.json` y `entries.json`; no incluye datos del custodio. Tras subirlo como artefacto `arena-ct03-producer-public-and-forecasts`, cerrar mediante:

```bash
gh workflow run arena-ct03-freeze-predictions.yml --ref experiment/arena-ct00-ct02-20261107 \
  -f freeze_sha=<SHA40> -f producer_run_id=<PRODUCER_RUN_ID>
```

El workflow verifica que el productor corrió el mismo SHA y publica un artefacto de lock con ID de run independiente. **No ejecuta OMC ni proveedor.** Custodio humano comprueba en GitHub el SHA, la existencia e ID del artefacto y su orden temporal **antes de abrir la reserva**; registra ese hito en un pequeño `archive-record.json` con el esquema `igc-ct03-procedural-archive-ack/1.0`, IDs de run/artefacto, lock SHA, code SHA, responsable y `archived_before_reveal=true`, `producer_write_disabled=true`, `custody_scope="PROCEDURAL_HUMAN_NO_EXTERNAL_SIGNER"`.

**Solo después de esa comprobación humana**, el evaluador, desde el espacio del custodio y sin credenciales productoras, ejecuta:

```bash
python -m scripts.arena_cafe.ct03_minimal_score \
  --lock "$CUSTODIAN/verified-archived-lock.json" \
  --archive-record "$CUSTODIAN/archive-record.json" \
  --construction "$CUSTODIAN/public-release/construction.json" \
  --commitment "$CUSTODIAN/public-release/world-commitment.json" \
  --producer-root "$PRODUCER_CHECKOUT" \
  --private-dir "$CUSTODIAN/world-run" \
  --out "$CUSTODIAN/score-post-lock.json"
```

La evaluación abre **solo en ese paso** t6/t8 del mundo. Aplica MAE inicial/final, diferencia pareada, baselines de persistencia y tendencia limitada por masa, y mediana de medianas por seis grupos D y tres M. Conserva los **13 slots en el denominador** y registra fallos sin convertirlos en error cero. Con cero predicciones admisibles, **se detiene**. No recalibra, no escoge otro mundo y no llama a OMC o Buffalo.

## 5. Límite de gasto y criterio de parada por fase

| Fase | Máximo OMC nuevo | Máximo POST Buffalo | Se detiene cuando |
|---|---:|---:|---|
| Preparación de código + tests | 0 | 0 | Sin protocolo/commit congelable o contrato roto |
| CT-02 lote técnico manual **consumido** | **2/2 ejecutadas** | **0** | Completo; no repetir D0/M0 |
| CT-03 una instancia, **otro lote** | **21** | **2** | Filtración al productor, falta de evidencia propia, error G1/G2, fin de cuota; fallos por candidato bloquean su ruta, no todos los brazos necesariamente |
| Evaluación posterior al lock | **0** | **0** | No existe archivo de lock verificado, cambia el mundo/código/scope, cero predicciones admisibles o falta reserva |

Los techos son máximos acumulables con contabilidad, **no autorizaciones**. Esta implementación no gasta OMC, DES ni proveedor. No hay reintentos automáticos ni un sistema nuevo de presupuestos. La custodia es **procedimental y declarada**, no independencia de operador, pruebas OS ACL ni firma RSA. Tampoco equivale una compilación numérica a un resultado G3 o una mejora predictiva.

**Hito próximo:** aprobar el paquete CT-02 con su SHA y presupuesto de hasta dos simulaciones; revisar el artefacto real único. Después resolver aceptación técnica CT-02 + habilitación condicionada de CT-03 en un mismo hito, sin pedir autorizaciones por microcommit ni abrir una revisión general nueva.
