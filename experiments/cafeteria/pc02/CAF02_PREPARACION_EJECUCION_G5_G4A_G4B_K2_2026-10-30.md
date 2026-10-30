# CAF-02 — Conexión preparatoria con fuente privada, G2 nativo y secuencia G5→G4a→G4b→K2

**Fecha:** 2026-10-30. **Estado: ADAPTADORES DE CORTES Y COMPROMISOS LOCALES, SIN MUNDO EJECUTADO, SIN SELLO EXTERNO. NO AUTORIZADO.**  
**Alcance:** únicamente conectar el ensayo definido en el PR #104; no buscar parámetros, no cambiar el menú ni las moléculas, no reabrir CAF-01.

## 1. Qué se ha conectado realmente

La validación de K2 reservado se ubica en un **módulo de adjudicación posterior a la revelación** (`caf02_k2_adjudicator_boundary.py`), que no debe instalarse ni invocarse en los procesos G4a/G4b. Valida solo formato/contabilidad de un K2 **ya liberado por un custodio independiente**, y su función de autorización permanece bloqueada. **La separación de archivos no sustituye aislamiento de procesos ni permisos del sistema operativo.**

El código fuente de CAF-02 dispone de un **adaptador del lado del evaluador** (`caf02_private_source_boundary.py`) que acepta instantáneas del motor de eventos discretos y devuelve paquetes mínimos. **No ejecuta DES** y debe operar en un proceso separado del productor de hipótesis, que **no importa ni lee** ese módulo ni el archivo privado del mundo.

| Corte | Interno al evaluador (NO se revela) | Paquete permitido fuera del evaluador |
|---|---|---|
| K0, pulso público 1.2 pedidos/min ×20 | Colas, servidores, servicios, aceptaciones efectivas, configuración, semillas, eventos y el resto de la curva | **Solo** entregados enteros acumulados a t5 y t10 + referencia opaca al compromiso G5 |
| K1, una opción conjunta A/B/C | Todas las demás observaciones de la corrida y la configuración privada | **Solo** opción ya elegida (tasa, tiempo), **un** conteo entero de entregados + misma referencia G5 |
| K2, pulso público 1.35 pedidos/min ×20 | **Seis valores reservados**, estados y parámetros privados | **Nada al productor hasta después de una acreditación G4b independiente y autorización específica**; el contrato define el formato de revelación separado |

Todas las corridas futuras tendrán stocks iniciales vacíos y tratarán las llegadas según el calendario medio intervalo (t_j=(j+1/2)/lambda), anterior a t20, con instantáneas después de procesar los eventos del instante. No se mezclan estados de las tres corridas. El evaluador deberá verificar conservación: aceptados = entregados + pedidos pendientes. **Las observaciones del mismo mecanismo privado** son la prueba; el motor no se selecciona con base en qué candidatos M/D funcionan mejor.

**Precisión de conteos enteros descubierta al preparar el puente:** a K2=1.35 pedidos/min, las aceptaciones máximas a t5 y t10 son **7 y 14**, no `floor(1.35×t)` = 6 y 13. Los eventos de llegada se programan en instantes medios y el límite exacto es inclusivo en la observación. El validador K2 reservado usa ahora la secuencia **[7,14,20,27,27,27]**. Es una corrección de frontera física de lectura, no información privada ni ajuste de modelos. El pulso de K0 conserva 6 y 12 aceptaciones para t5/t10.

### Motor DES y significado de independencia

El repositorio ya contiene `pc01/caf01_des_engine.py`, un motor **genérico de eventos discretos** separado del integrador E1 y del RK4 de D. Su gramática de servidores, colas, tiempos de servicio y calendario de eventos podría reutilizarse en un **nuevo** evaluador CAF-02, pero **el código actual no lo ejecuta ni elige sus parámetros**. Si se reutiliza, el G5 de CAF-02 debe fijar sus bytes exactos y toda diferencia de ecuaciones/conceptos frente a M y D. Reutilizar el motor no equivale a reutilizar las observaciones, mundo ni excepción G5 de CAF-01: quedan prohibidos.

La separación efectiva requiere **procesos distintos**: el operador del evaluador mantiene la configuración, el nonce, la fuente y K2 inaccesibles al productor; publica solo el objeto mascarado para cada corte. Una función que recibe instantáneas privadas pero se llama dentro del mismo proceso del productor **no es ceguera independiente**. No se ha implementado un entorno de aislamiento ni existe aquí testigo externo.

## 2. Paquetes G4a y G4b reproducibles, todavía sin custodia

`caf02_public_cut_bridge.py` consume solamente el JSON público del corte, la política actual de borrador y los modelos ya existentes. Rechaza campos adicionales (semillas, colas, aceptaciones reales, curvas K0 completas, estado interno, K2 o supuestos parámetros de la fuente).

**G4a (pre-K1)** calcula ambos calibradores **M y D** para los mismos D5/D10, preserva **todos** los candidatos K0, el índice y la opción K1 conjuntos, las proyecciones K2 de K0 de ambas familias de cada brazo y las referencias convencionales **solo-K0**. Incluye hash de política, hashes de K0 por brazo y un hash del propio paquete. Se computa **antes** de recibir el conteo K1.

**G4b (pre-K2)** requiere el paquete G4a intacto y, cuando existe opción seleccionada, **exactamente** el conteo K1 para ese estímulo, con la referencia G5 sin cambios. Aplica `m.k1_revise` y `d.revise_k1` a los supervivientes K0, conserva el hash de las proyecciones previas, y produce los conjuntos K2 posteriores sin evaluar ningún K2. Si no se eligió K1, exige ausencia de observación nueva y K2 posterior **idéntico** al previo. Declara por separado el tipo de revisión y las abstenciones.

**No confundir el hash de contenido con un sello externo.** Ambos paquetes se emiten con `external_custody_verified=false`, `state=NOT_CUSTODIED...`, `native_OpenModelica_parity_verified=false` y `ATMS_persistence_verified=false`. La función `authorize_world_execution` está deliberadamente bloqueada. El identificador G5 provisto en paquetes no se autentica por sí mismo.

**CLI local solo preparatoria** (los archivos de ejemplo no existen en el repositorio y no contienen verdad reservada):

```bash
python experiments/cafeteria/pc02/caf02_public_cut_bridge.py \
  --stage G4a --public-evidence /ruta/solo_K0_publico.json \
  --out /ruta/nuevo_G4a_candidato.json

python experiments/cafeteria/pc02/caf02_public_cut_bridge.py \
  --stage G4b --g4a-candidate /ruta/nuevo_G4a_candidato.json \
  --public-evidence /ruta/solo_K1_publico.json \
  --out /ruta/nuevo_G4b_candidato.json
```

La herramienta **rechaza sobrescritura**. El resultado es un **candidato de paquete**; estos comandos no invocan mundos, no obtienen firmas, no generan un recibo de custodia independiente y no autorizan liberar K2. Cuando no se seleccionó K1, `--public-evidence` se omite en G4b.

## 3. Qué se exige en G5 / G4a / G4b (todavía no realizado)

| Puerta | Condición previa verificable | Estado hoy |
|---|---|---|
| **G5 antes de K0** | Política finalmente aprobada, DES seleccionado independientemente del ajuste de M/D, parámetros y nonce privados, semillas/calendario, **hash de bytes exactos del motor**, presupuesto y testigo externo con fecha y autenticación comprobable | **NO** |
| **K0** | Autorización independiente posterior a G5; una ejecución privada, sin reintentos; salida exacta de dos enteros y referencia G5 | **NO** |
| **G4a antes de K1** | Paquete G4a completo, comparación de casos G2 nativos según alcance predeclarado, testigo externo que firma bytes y orden temporal, validación externa por actor separado | **NO** |
| **K1** | Una opción conjunta ya comprometida; una ejecución privada con reset y solo un entero revelado; cero ensayos alternativos | **NO** |
| **G4b antes de K2** | Paquete G4b, ambas versiones de pronóstico M/D, referencias, abstenciones, consumos y recibo externo **verificado antes de liberar K2** | **NO** |
| **K2 / evaluación** | Autorización separada, única ejecución reservada, evaluación imparcial de la pérdida `L_set` de M/D versus sus propias versiones K0 y referencias K0-only; resultados adversos publicados | **NO** |

Los tres recibos externos deben vincular el **mismo compromiso G5** y cadenas de hashes G4a→G4b. No basta un booleano `verified` escrito en un JSON propio, ni un commit GitHub, ni un hash que el productor pueda cambiar. La política sigue declarada `DRAFT_FOR_REVIEW_NOT_FROZEN_NOT_AUTHORIZED`; **el adaptador matemático de D también exige ese estado**. No convertir el texto de la política a `AUTHORIZED` sin separar esa validación de la autorización real: en su forma actual se bloquearía el cálculo. Es una dependencia de activación conocida, no una nueva objeción metodológica.

La persistencia `ATMS_persisted=false` es **real**. Se podrán publicar resultados de revisión matemática y sus hashes, **no** afirmar memoria ATMS persistida, ejecución completa D+ATMS o aprendizaje del sistema entre experimentos. Su integración es un trabajo adicional con límites de presupuesto y de acceso.

## 4. Comprobación de OpenModelica (G2): una compuerta pendiente, no un resultado

`caf02_g2_native_correspondence_plan.py` produce un manifiesto determinista de **12 casos M (seis C00, seis C01) y 3 D (D1, D2, D3)** elegidos **antes de K0**, sin utilizar información del mundo. Usa solo el pulso público K0 1.2 pedidos/min×20 y seis instantes 5,10,15,20,30,40 para obtener curvas continuas de referencia del propio integrador. La tolerancia **propuesta** del contraste es máximo desvío absoluto ≤**0.05 pedidos** en los seis valores, con unidades min→h explícitas, conservación, parámetros y estructura exactamente coincidentes y fuente Modelica identificada por hash. No se confunde con el residuo K1 ±0.77 ni con el margen de convergencia Heun 0.02.

El manifiesto **no** genera modelos Modelica listos para correr, ni ejecuta OMC, ni valida el compilador, ni certifica 182 candidatos. Un CSV que copie exactamente el integrador no constituye paridad nativa: se requiere el modelo compilado, el solver real, la referencia de origen y recibo del intento, con testigo independiente si lo exige el protocolo. Hay que implementar el generador de modelos nativos **con la misma gramática y unidades** y comprobar los casos bajo los presupuestos propuestos, **antes de ver K0 del nuevo mundo**. Una verificación en un único pulso tampoco prueba equivalencia bajo K1/K2; cualquier conclusión debe restringirse al pulso ensayado.

## 5. Pruebas y límites de entrega

GitHub Actions ejecuta solamente **tests locales con objetos de evidencia pública sintéticos y estructuras de instantánea construidas a mano**, sin importar datos del mundo privado, ni correr DES, ni utilizar OpenModelica, Buffalo o un K2 real. Se comprueban rechazos por datos ocultos, máscaras erróneas, pulso K1 distinto, linaje de G4a/G4b alterado, intento de reutilizar un K2 como K0/K1, ausencia de K1 y corrección del calendario exacto en K2.

**Veredicto:** el cableado y la secuencia documental están listos para revisión, **no** para activar el ensayo independiente. Faltan autorización, productor/operador aislados, world source independiente seleccionado, custodio G5/G4a/G4b y simulaciones G2 nativas. No se modifica D, E1, CAF-01, ni la política de K1.
