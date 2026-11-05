# Arena IGC — Vocabulario canónico de eventos de video v0.1

**Fecha:** 2026-11-04  
**Estado:** propuesta de contrato observacional para revisión; **NO** criterio de calibración de SD, ni compuerta F5, G4 o G5.  
**Video fuente:** SHA-256 `cd37c9d3f231f4d307c4f3353ce1dc096fad4185bbdf6ffab06266b9d41290c5`; 640 × 360 px, 30 fps nominales y ~5024.87 s de tiempo de video.  
**Base:** `eventos.csv`, `operaciones.csv`, `tiempos_pedidos.csv` y revisiones cualitativas R3-P045 y R4-P031. Los originales son inmutables; no se ha validado independientemente el reloj físico ni la continuidad del video.  
**Objetivo:** que anotaciones futuras sean comparables, auditables, reproducibles y eventualmente transformables a observables de la Arena; **no** construir automáticamente una ontología universal ni una simulación de cafetería a partir de esta cámara.

## 1. Regla epistemológica principal

Separar **imagen → afirmación observacional → posible inferencia → variable del modelo**. Ninguna etiqueta puede saltar etapas sin un adaptador explícito y evidencia adicional.

- **OBSERVADO:** algo visible en uno o varios fotogramas; se especifican los segundos y región visual.
- **INFERIDO:** interpretación basada en observaciones, con regla explícita, alternativas y límites. No se registra como hecho visual.
- **HIPÓTESIS:** mecanismo candidato, no identificación de un evento.
- **DESCONOCIDO:** sin observación suficiente; no sustituir por 0, inactividad, no uso o entrega.

Un grado cualitativo `alta/media/baja` informa legibilidad de la evidencia, **no** una probabilidad estadística. La ausencia de evento anotado no demuestra ausencia de actividad. Las filas de estado y acción **no son automáticamente tareas con duración**.

## 2. Capas mutuamente distinguibles (pero coexistentes)

| `kind` | Unidad | Reloj | Consecuencia admitida |
|---|---|---|---|
| `estado` | Fotograma(s) discreto(s) | `samples_video_s` | Presencia/conteo mínimo **en esas muestras**; no integral temporal |
| `accion` | Manipulación visible | `samples_video_s` | Acción observada; no duración continua por defecto |
| `transicion` | Cambio entre estados visibles | `(t_último_estado,t_primer_estado_nuevo]` | Un cambio visual acotado, no flujo de la empresa |
| `episodio` | Operación con inicio y fin acotados | Ventanas `[lo,hi]` para inicio y fin | Duración compatible **en tiempo de video**, no trabajo físico certificado |

Una acción puede suceder durante un episodio y mientras otro objeto se encuentra estacionado. No imponer exclusividad de categorías. Dos registros que comparten recursos tampoco pueden sumarse indiscriminadamente como «tiempo total del barista».

## 3. Catálogo operacional

La tabla completa y legible por máquina está en `catalogo_eventos_v0_1.json`. `base` es anotable ahora con esta fuente; `condicional` exige mayor seguimiento; `reservado` requiere evidencia distinta o inequívoca.

| Código | Clase | Alcance | Criterio mínimo / límite clave |
|---|---|---|---|
| `objeto_visible_en_region` | `estado` | base | Silueta distinguible y región documentada; **no inferir** inventario total, propiedad o identidad de pedido |
| `recipiente_con_contenido_visible` | `estado` | base | Contorno del recipiente y contenido visualmente apreciable; **no inferir** ingrediente, volumen, receta o bebida finalizada |
| `recipiente_estacionado_muestra` | `estado` | base | Posición sobre barra sin sujeción aparente en la muestra; **no inferir** inactividad entre fotogramas o permanencia continua |
| `superficie_montada_visible` | `estado` | base | Forma/acabado observable desde la vista analizada; **no inferir** último vertido registrado, montaje completo o entrega |
| `recipiente_bajo_grupo_visible` | `estado` | base | Ubicación espacial visible; **no inferir** extracción automática, bomba activa, cantidad espresso |
| `jarra_proxima_a_lanza_visible` | `estado` | base | Posición visible respecto a lanza; **no inferir** vapor activo, temperatura, válvula abierta |
| `barista_visibilidad_parcial` | `estado` | base | Frontera/oclusión visible; **no inferir** ocio, tarea específica, ausencia laboral |
| `minimo_recipientes_con_contenido` | `estado` | base | Contar solo los inequívocamente visibles y declarar región; **no inferir** capacidad máxima, stock continuo, productos acabados |
| `barista_manipula_objeto_visible` | `accion` | base | Mano y objeto coinciden en muestras/movimiento discernible; **no inferir** actividad continua o identidad del producto |
| `barista_interactua_con_equipo_visible` | `accion` | base | Contacto o manipulación distinguible; **no inferir** activación de bomba, vapor, extracción efectiva |
| `liquido_vertido_visible` | `accion` | base | Trayectoria líquida o cambio consistente visual comprobable; **no inferir** ingrediente, g/ml, merma, salida de stock de insumos |
| `mezcla_manual_visible` | `accion` | base | Movimiento observable del útil dentro del recipiente; **no inferir** disolución completada, dosis, tiempo continuo |
| `accesorio_colocado_visible` | `accion` | base | Antes/después o movimiento de accesorio identificado; **no inferir** montaje de todos los productos de un lote |
| `objeto_desplazado_visible` | `accion` | base | Seguimiento local observable o fotogramas inequívocos; **no inferir** salida de región si no se observa frontera |
| `objeto_aparece_en_region` | `transicion` | base | Misma región, muestras ordenadas, criterio de visibilidad; **no inferir** objeto creado, inicio de producción, pedido nuevo |
| `objeto_deja_de_verse_en_region` | `transicion` | base | Misma región; describir oclusión posible; **no inferir** objeto cruzó frontera, producto entregado, inventario cero |
| `objeto_cruza_frontera_region` | `transicion` | ampliado | Trayectoria visual cruzando frontera identificada; **no inferir** entrega a cliente u operación pos |
| `ultimo_vertido_visible` | `transicion` | condicional | Seguimiento de objeto suficiente para determinar último vertido dentro de cobertura declarada; **no inferir** montaje completo, último vertido global sin cobertura |
| `montaje_completo_verificado` | `transicion` | condicional | Checklist de acabado fijada antes de revisar, cada requisito observable; **no inferir** final de pedido, entrega, preparación exhaustiva |
| `jarra_sostenida_junto_a_lanza` | `episodio` | base | Inicio y fin acotados con imágenes de transición, más muestras de presencia; **no inferir** vapor activo, tiempo físico de vaporización o utilización total de lanza |
| `manipulacion_equipo_delimitada` | `episodio` | condicional | Inicio y fin acotados; describir subacciones y oclusiones; **no inferir** funcionamiento autónomo continuo del equipo |
| `vapor_activo_verificado` | `transicion` | reservado | Registro de mando/vapor inequívoco o señal instrumental validada; **no inferir** derivarlo de jarra sostenida, inferir caudal/energía |
| `extraccion_activa_verificada` | `transicion` | reservado | Flujo observable inequívoco de grupo o medición validada; **no inferir** derivarla de taza bajo grupo o manos en portafiltro |

### Distinciones obligatorias

**`ultimo_vertido_visible` / `montaje_completo_verificado`:** el primero es el último vertido *identificable en la cobertura observada*; no asegura que sea el último del proceso real. El segundo exige un checklist **definido antes** de revisar cada producto (p. ej. accesorios requeridos), seguimiento de identidad y visualización suficiente de todos sus requisitos. En P031 se ajustan accesorios tras el vertido; por eso **no se migrará** `assembly_end` o `montaje_fin` sin adjudicación semántica.

**`objeto_deja_de_verse_en_region` / `objeto_cruza_frontera_region`:** pasar de presente en 2893 a ausente en 2894 en la barra de P031 **solo certifica pérdida de visibilidad local**. Cruzar una frontera requiere trayectoria o cruce identificable. Ninguno acredita `entrega_al_cliente`.

**`jarra_sostenida_junto_a_lanza` / `vapor_activo_verificado`:** proximidad y sujeción (P045 4068–4086, 4112–4128) no acreditan vapor, temperatura, caudal ni encendido automático. No se debe renombrar el episodio visual como `vapor_activo` solo porque en el CSV heredado aparece `vaporizado_con_sujecion`.

**`recipiente_estacionado_muestra` / `barista_inactivo`:** recipiente inmóvil no implica que el barista no esté trabajando. Del mismo modo, `barista_visibilidad_parcial` denota **no evaluabilidad**, nunca descanso.

## 4. Recursos, regiones, objetos y asociaciones

- **Región (obligatoria):** identificador de frontera visual estable, por ejemplo `barra_frontal_vista_principal` o `lanza_vista_principal`. Documentar la región en un archivo de geometría si luego se usa para conteo o flujo; no combinar sin comprobar vista secundaria y principal.
- **Objeto:** `object_track_id` es **local y provisional**; si no hay seguimiento inequívoco usar `null` y un conjunto de objetos sin traza. Un `batch_context=P031` o `P045` indica **asociación contextual**, no identidad POS ni correspondencia 1:1 con bebida.
- **Recursos:** enumerar recursos **visualmente involucrados**; presencia en `resources` no implica funcionamiento activo o tiempo exclusivo. Vocabulario inicial: `barista_visible`, `lanza_visual`, `grupo_visual`, `barra_frontal`, `portafiltro_visible`, `jarra_visible`, `vaso_visible`. No confundir herramienta, persona, zona y producto.
- **Simultaneidad:** `parallel_group` enlaza observaciones coexistentes como la jarra de P045 y la taza que se mueve cerca de 4122 s. Esto no crea duraciones de multitarea ni demuestra atención paralela ilimitada.
- **Conteo de objetos:** `count_lower_bound=3` en el fotograma 2874 s de P031 significa **al menos 3 recipientes visibles** en esa región y ese instante. No es capacidad máxima del espacio, producción ni inventario empresarial.

## 5. Tiempo, incertidumbre y censura

1. Todo tiempo lleva `clock=video_presentation_time_s`. No se etiqueta como tiempo físico real sin verificar continuidad, cortes y velocidad; 30 fps nominales ≠ reloj de negocio verificado.
2. **Estado / acción:** conservar segundos exactos de los fotogramas de apoyo; varios segundos listados son observaciones discretas, **no intervalo continuo**.
3. **Transición:** a `t0` existe la condición anterior y a `t1` la nueva; el cambio se localiza en `(t0,t1]`. Escribir evidencia de ambos extremos; si hay oclusión, la transición es pérdida de visibilidad, no movimiento.
4. **Episodio:** si inicio `[a,b]`, fin `[c,d]`, duración compatible `[max(0,c-b), d-a]`; exigir coherencia `a≤b`, `c≤d`, `b≤d`. Si falta un límite, mantener `null` y `censoring`, sin imputar cero.
5. Si hay cortes, saltos o cambios de velocidad, **no** combinar extremos como duración física. Un tramo muestreado cada 1/2/10 s no es observación continua.
6. Dos acciones que se solapan visualmente no se deben sumar como dos turnos independientes de trabajo humano; el estado de un recurso y la manipulación de producto pueden coexistir.

## 6. Contrato mínimo de registro (v0.1)

El contrato detallado se encuentra en `schema_anotacion_v0_1.json` y se valida con `validar_anotaciones.py` (JSON Schema + invariantes adicionales). La unidad persistida es una **anotación** —no un pedido, ni una bebida, ni una transacción—. Campos principales:

| Campo | Sentido |
|---|---|
| `event_id`, `event_code`, `kind` | Identificador, término canónico y capa; deben concordar con catálogo |
| `claim_level`, `observation` | Estado epistemológico y descripción literal de lo visible |
| `time` | `sample` / `transition` / `episode` con intervalos y censura |
| `region_id`, `entities`, `resources` | Frontera visual, objetos y recursos con roles explícitos |
| `evidence` | Segundo de fotograma + ruta de evidencia verificable |
| `provenance` | SHA-256 MP4, vista, reloj y banderas de continuidad |
| `review` | Modalidad, independencia real, certeza cualitativa y adjudicación |
| `batch_context`, `batch_link`, `object_track_id` | Asociación contextual separada de trazabilidad certificada |
| `count_lower_bound`, `parallel_group`, `caveats` | Conteos inferiores, simultaneidad y límites |
| `source_annotation_ids` | Referencias R3/R4 o ID original para no borrar procedencia |

**Importante:** `kind=episodio` no garantiza continuidad; `continuity_status=episode_bounded_not_continuous` es la opción normal con estos fotogramas. Sólo pasar a `continuous_video_manually_verified` tras inspección continua documentada y control del reloj.

## 7. Ejemplos reproducibles (no inventados)

El archivo `ejemplos_p031_p045_v0_1.jsonl` contiene siete anotaciones y rutas relativas dentro de los paquetes de evidencia **ya generados** de las revisiones 3 y 4.

| Caso | Lo codificado | Lo que NO se afirma |
|---|---|---|
| P031 @ 2874 s | Al menos 3 recipientes con contenido visibles | Tres productos terminados, capacidad máxima |
| P031 @ 2782 s | Vertido visible (descripción de revisión R4-05) | Ingrediente, volumen, duración de servicio |
| P045 @ 4068–4086 s | Sujeción de jarra, episodio 1 | Vapor activo instrumental |
| P045 @ 4112–4128 s | Sujeción de jarra, episodio 2 | Exclusividad total del barista |
| P045 @ 4122 s | Desplazamiento de taza compatible con sujeción simultánea | Dos operaciones complejas completas |
| P045 @ 4144 s | Dos superficies montadas visibles | Montaje completo según receta, entregas |
| P031 `(2893,2894]` s | Conjunto de recipientes deja de verse en región frontal | Entrega o cruce certificado por una frontera |

Todas las etiquetas de ejemplo se basan en la revisión visual previa y usan el mismo asistente: **no constituyen validación independiente**. No se genera ejemplo positivo de `vapor_activo_verificado`, `extraccion_activa_verificada`, `montaje_completo_verificado` o `objeto_cruza_frontera_region` porque falta apoyo suficientemente específico.

## 8. Traducción hacia stocks/flujos de dinámica de sistemas: contrato de NO-promoción

| Evidencia de video | Observable eventual | NO promover automáticamente a |
|---|---|---|
| Recipientes visibles en un fotograma | `conteo_minimo_visible(region,t)` | Inventario total `S(t)` o capacidad máxima |
| Presente→ausente en región | `cambio_de_visibilidad(region,t)` | `entregas/min`, salidas reales de inventario |
| Sujeción jarra junto a lanza | `episodios_interaccion_lanza` | Utilización de lanza, caudal de vapor, productividad |
| Manipulación de barista y equipo | `interacciones_manual_visibles` | Tiempo laboral total, velocidad o costo marginal |
| Panel ORDER | `lotes_panel_visibles` | Llegadas POS, pagos, demanda real |
| Último vertido acotado | `ultimo_vertido_visible` | `montaje_completo`, pedido despachado |

Para derivar una trayectoria de stock requiere: (a) frontera definida; (b) stock inicial o cota; (c) entradas/salidas exhaustivas con unidades; (d) continuidad observacional o mecanismo explícito de datos faltantes; (e) identidad si hay retrabajo y cruces; (f) calibración de reloj si se estiman tasas físicas. **P031/P045 no satisfacen todas estas condiciones**. No se ejecuta D/B/M ni se modifican G4/G5.

## 9. Procedimiento recomendado para nuevas anotaciones

1. Seleccionar un tramo **nuevo, previamente no codificado** y declarar región, visibilidad, objetivo y frecuencia de fotogramas. Conservar SHA del MP4.
2. Un codificador que no haya leído las anotaciones existentes etiqueta **estados / acciones / transiciones / episodios separadamente**, sin consultar pedidos mientras asigna acciones físicas; después se podrán añadir vínculos contextuales.
3. Para cada anotación guardar evidencia antes/después (cuando corresponda), certeza cualitativa, ausencia de trazabilidad y límites. Admitir `DESCONOCIDO` sin penalización.
4. Pasar el validador automático. Revisión metodológica de ambigüedades; no corregir a posteriori ocultando el primer registro.
5. Comparar solo categorías y límites realmente equivalentes, con denominador, unidad temporal y cobertura iguales. La ausencia de clases históricas no es desacuerdo cuantificable.
6. Mantener el catálogo versionado y ampliar **solo** cuando surja una observación sin representación válida. Pasar al modelo físico únicamente con puente semántico y compuerta explícitos.

## 10. Compromisos / límites de esta entrega

- **Producción:** catálogo v0.1, esquema JSON, ejemplos, validador y pruebas de negativos. La estructura se incorpora en un directorio separado: no reescribe los CSV antiguos.
- **No hecho:** nuevos eventos del video, validación doble ciega, estimación de utilización de recursos, asignación de las 105 unidades a vasos físicos, tiempo físico calibrado, recetas, mínimos de inventario empresarial, capacidad máxima, causalidad o simulación.
- **Decisión pendiente:** checklist operativo para `montaje_completo_verificado`, definición geométrica fija de cada región y diseño de un segundo anotador independiente.