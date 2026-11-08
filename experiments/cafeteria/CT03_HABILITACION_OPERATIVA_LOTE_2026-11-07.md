# CT-03 · Habilitación operativa del lote único (sin gasto ni ejecución)

**Estado verificado el 2026-11-07:** preparación offline, **NO READY FOR LIVE**. Fuente rectora: `ARENA_IGC_HOJA_DE_RUTA_V4_0_2026-11-07.md`, §§6, 8 y reglas R06/R12/R18/R19/R24; cierre externo de F172-10/11 en `REVISION_PR172_CIERRE_F172_10_11_A2E190B_2026-11-07.md`. **No es nueva hoja de ruta, rediseño ni solicitud de repetir las dos corridas CT-02.** El protocolo actual mantiene `currently_authorized_new_omc=0` y `currently_authorized_new_provider_post=0`.

## Estado comprobado y condición de entrada

- Repositorio `yudocyudoc/IGC`: **público**; rama por defecto `main`.
- PR [#171](https://github.com/yudocyudoc/IGC/pull/171): Draft, cabeza `2d7678c985270eaaa9eb7ba8f6d63a80ddc43656`, base `main`. PR [#172](https://github.com/yudocyudoc/IGC/pull/172): Draft, base #171; al comprobar el hito operativo, cabeza `a2e190b84d42db5c9aab31116a39e2baa38477f3` (este documento crea un commit adicional: **leer nuevamente el HEAD antes de aprobar un SHA**). No hubo merge automático.
- Los archivos `.github/workflows/arena-ct03-public-intake.yml`, `arena-ct03-producer.yml` y `arena-ct03-freeze-predictions.yml` **no existen en `main` al comprobar este hito**. GitHub requiere registro en la rama por defecto para mostrar/despachar normalmente un `workflow_dispatch`. Se deberán incorporar *después de decidir explícitamente* la integración de los PR; el usuario no ha autorizado fusionarlos automáticamente (R24). Tras registrarlos, `--ref experiment/arena-ct00-ct02-20261107` puede seleccionar el commit experimental congelado, siempre que la rama siga existiendo exactamente en ese SHA.
- La presencia en YAML de `environment: ...` **no certifica** que existan required reviewers, protecciones de rama o secretos. La configuración real **no fue acreditada**. Los scripts que generan mundo y publican cuatro puntos existen, pero la cuenta, permisos y almacenamiento reales del custodio no se han seleccionado o verificado.
- Último corte con CI verde del incremento F172-10/11: [42427019959](https://github.com/yudocyudoc/IGC/actions/runs/42427019959) (integración B/D/M) y [42427019990](https://github.com/yudocyudoc/IGC/actions/runs/42427019990) (regresiones). Son **offline**, no prueba de environments, cuentas ni ejecución física CT-03.

## Secuencia operativa; cada compuerta debe registrarse como hecho, nunca inferirse de un nombre

| Orden | Responsable y acción concreta | Evidencia / condición para avanzar |
|---|---|---|
| 1 | Responsable GitHub: decidir conscientemente registro de los 3 workflows en `main` después de revisar las dependencias #171 y #172. **No fusionar automáticamente.** | Los 3 archivos realmente visibles en `main`; PR/base final documentados; revisión de workflows de mismo SHA en branch experimental. |
| 2 | Responsable GitHub: configurar `Settings → Environments` para `arena-ct03-public-intake`, `arena-ct03-producer` y `arena-ct03-producer-b-provider`. Establecer required reviewer humano, reglas de rama y, si hay un segundo actor con permisos, impedir aprobación propia. | Captura/registro **administrativo sin secretos** que acredite reglas reales. No confundir etiqueta `environment` con protección. Para este repositorio público hay soporte para reviewers, sujeto a la configuración efectiva. |
| 3 | Custodio: designar **cuenta/entorno distinto del productor**, almacenamiento privado y persona que lo controle; verificar por permisos efectivos que productor y sus jobs **no pueden leer** configuración, fuente Modelica privada, CSV completo, logs ni valores t6/t8. | Separación efectiva documentada; no basta carpeta distinta ni firma declarativa. No colocar mundo ni claves en el repo público, issues, comentarios, Actions, artefactos públicos ni entradas de workflow. |
| 4 | Congelar un **único SHA40 real** de protocolo + código y autorizar **explícitamente un lote CT-03**: un mundo nuevo (un intento OMC), diez D/M originales nuevos, hasta seis revisiones M, B inicial/revisión hasta dos OMC y hasta dos POST. Dos D0/M0 auténticos de CT-02 **se reutilizan** y nunca se repiten. | Acta o decisión de lote vinculada al SHA40, límites **máximo 19 OMC nuevos y 2 POST** y reglas de parada. Es presupuesto total del lote, no meta; no autoriza CT-04, DES ni otra selección de mundo. |
| 5 | Custodio **solo tras (3)-(4)**: seleccionar una configuración verdadera en rangos fijados (sin elegir por RMSE), preparar fuente privada, registrar el **único intento de mundo**, ejecutar un OMC y mantener el CSV completo fuera del alcance productor. | `private-manifest.json`, `private_world.mo`, `simulate.mos`, `world-omc.log` y `sealed_world_res.csv` solo en espacio privado. Si falla, se cuenta el intento y **se detiene**, no se elige otro mundo por conveniencia. |
| 6 | Custodio: `ct03_minimal_custody` libera **exactamente 3 JSON públicos**, con t0/t1/t2/t4 y ningún t6/t8. Operador GitHub: intake manual con SHA40 coincidente; conservar `public_release_run_id`. | Artefacto `arena-ct03-public-release-<run_id>`, schema/hashes aceptados y ausencia de privados. La etiqueta de custodia por sí sola NO acredita independencia. |
| 7 | Responsable GitHub: configurar **en environment `arena-ct03-producer`** las variables `CT03_APPROVED_FREEZE_SHA`, `CT03_APPROVED_RELEASE_RUN_ID`, `CT03_EXTERNAL_CUSTODIAN_ACK=external_private_world_attempted_once` (este valor es una declaración procedimental, no una prueba). En `arena-ct03-producer-b-provider` cargar `CLOUDFLARE_ACCOUNT_ID` y `CLOUDFLARE_API_TOKEN` como **secrets**, nunca variables de texto ni mensajes/artefactos. | Comparación exacta con SHA y run aceptados, protección efectiva y autorización del lote antes de disparar el productor. **No publicar los secretos**, tampoco en esta ficha. |
| 8 | Operador GitHub: `arena-ct03-producer.yml` **una vez** en `--ref` rama experimental SHA40 congelada, `authorized=yes`, `max_new_omc=19`, `max_provider_posts=2`, `public_release_run_id` exacto. | Jobs reales D/M/B, recibo conteos, 13 plazas (incluidos fallos), logs e intentos. **No re-dispatch ni re-run** por errores; una falla puede haber consumido el techo. |
| 9 | Operador GitHub: workflow **separado** `arena-ct03-freeze-predictions.yml` en **la misma rama y SHA40** del productor, con `producer_run_id` y `freeze_sha`. | Artefacto `arena-ct03-prospective-lock-<run_id>` inmutable por convención, ID/SHA/tiempo comprobados y archivo verificado **antes** de revelar reserva. El `--ref main` del documento operativo antiguo NO cumple identidad si el productor corrió sobre la rama experimental. |
| 10 | Custodio **después de (9)**: archivar el `lock.json` y su recibo `igc-ct03-procedural-archive-ack/1.0` con la evidencia GitHub; desactivar escritura productora, solo entonces ejecutar `ct03_minimal_score` en espacio evaluador. | Tabla de 13 denominadores, fallos, MAE(t6/t8), diferencias pareadas, baseline, contabilidad y limitación sintética. Sin reseleccionar mundo, cambiar políticas, llamar proveedor o OMC desde el evaluador. |

### Comandos del recorrido existente (NO EJECUTAR ANTES DE LAS COMPuERTAS)

El código de custodia ya existe; no inventar un servicio nuevo. **Privado:** directorio `$PRIVATE_BASE` fuera del checkout y no accesible al actor productor. `$PRODUCER_CHECKOUT` debe ser un directorio existente, distinto, sin permisos de lectura sobre `$PRIVATE_BASE`. Ejecutar los comandos con `set -euo pipefail` y contabilizar la única simulación del mundo antes de invocar OMC:

```bash
IGC_CT03_CUSTODIAN_AUTH=CT03_POST_LOCK_CUSTODIAN_ONLY \
python -m scripts.arena_cafe.ct03_world_custody \
  --sealed-config "$PRIVATE_BASE/world-config.json" \
  --private-out "$PRIVATE_BASE/world-run" \
  --producer-root "$PRODUCER_CHECKOUT" \
  --public-commitment "$PRIVATE_BASE/world-commitment.json"

# Ejecutar una sola vez /private/simulate.mos con las bibliotecas e
# imagen OpenModelica 1.26.5 fijadas en CT-02/03 y conservar world-omc.log.
# No montar /private en runners productores.

python -m scripts.arena_cafe.ct03_minimal_custody \
  --producer-root "$PRODUCER_CHECKOUT" \
  --private-dir "$PRIVATE_BASE/world-run" \
  --commitment "$PRIVATE_BASE/world-commitment.json" \
  --public-out "$PRIVATE_BASE/public-release"
```

El único paquete que cruza de custodio al productor es `construction.json`, `world-commitment.json`, `release-status.json`. Para subirlo, usar exclusivamente los **inputs públicos base64** de `arena-ct03-public-intake.yml` después de registrar el workflow; nunca pasar configuración/semilla/mundo/csv en un input.

Despacho del **productor**, solo una vez y con cuota autorizada (no sustituir `<...>` con datos ficticios):

```bash
gh workflow run arena-ct03-producer.yml -R yudocyudoc/IGC \
  --ref experiment/arena-ct00-ct02-20261107 \
  -f authorized=yes -f freeze_sha='<SHA40_CONGELADO>' \
  -f public_release_run_id='<RUN_ID_INTAKE>' \
  -f max_new_omc=19 -f max_provider_posts=2
```

Despacho posterior **sin solver/proveedor**, después de que las 13 plazas del productor existan:

```bash
gh workflow run arena-ct03-freeze-predictions.yml -R yudocyudoc/IGC \
  --ref experiment/arena-ct00-ct02-20261107 \
  -f freeze_sha='<MISMO_SHA40>' -f producer_run_id='<RUN_ID_PRODUCTOR>'
```

**Parada actual:** pendientes (1) registro en `main`, (2) protección efectiva de environments, (3) custodia independiente con acceso acreditado, (4) autorización del lote. No hay `world_public_id` elegido, `public_release_run_id`, gastos CT-03, lock real, score ni verdad reservada abierta. **No emitir `authorized=yes` hasta satisfacer lo anterior.**
