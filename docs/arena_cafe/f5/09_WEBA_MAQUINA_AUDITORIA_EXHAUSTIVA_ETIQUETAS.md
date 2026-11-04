# WEBA F5 · Auditoría integral de formato del canal de cafetera, 209 blobs

**Fecha:** 2026-11-04. **Estado:** COMPLETADA sobre el espejo GitHub público en commit inmutable; retrospectiva y no ciega. **No** equivale a validar ciclo de máquina, bebida producida, vínculo a pedido POS ni servicio terminado.

## Pregunta y principio de evidencia

Después del PR #166 (inspección del árbol y la copia descomprimida aportada por el investigador a Drive, cuatro archivos leídos íntegramente), quedaban **205 archivos de señal de máquina sin inspección de contenido completo**. Pregunta: ¿hay etiquetas de tipo de bebida, pedidos o marcadores de operación incrustados como filas/columnas distintas del formato \`hora, aceleración_X, aceleración_Y, aceleración_Z\`?

Se revisó el contenido completo del **espejo GitHub** sobre los **209 archivos**, incluidos los cuatro muestreados previamente. No se afirma que los **205 archivos privados de Drive restantes** hayan sido leídos byte a byte, ni que el RAR completo de Figshare haya sido autenticado. Los cuatro archivos previamente comparados entre Drive y GitHub tenían hashes coincidentes, por lo que el espejo ofrece evidencia real verificable, pero la equivalencia universal de copias permanece **NO PROBADA**.

**Método:** árbol git recursivo \`truncated=false\`, commit upstream fijado **\`d6841669e544579547c94b7ce1e8613bbd6b3a39\`**; solo carpetas \`B.shift_data/<turno>/5.coffee_machine_acc\` y \`5.kave\`. Descarga cada blob por ruta exacta bajo ese commit, comprueba **longitud y Git blob SHA-1** con metadatos del árbol, analiza **todas las líneas**, cuenta cuatro campos con hora de pared y tres floats finitos frente a filas irregulares. Los datos de personas, wearables, HR, cuestionarios, POS, vídeo y otras categorías se excluyen por diseño.

El analizador es \`scripts/arena_cafe/weba_machine_label_exhaustive_audit.py\`. Pruebas de parser \`tests/test_arena_cafe_weba_machine_label_exhaustive_audit.py\`. CI con descargas públicas temporales y **salida solo agregada**, sin filas, identificadores de personas/pedidos ni timestamps de caso:
[GitHub Actions #41910562764](https://github.com/yudocyudoc/IGC/actions/runs/41910562764) — **PASS** (10 tests, integridad de 209 blobs y controles de privacidad).
[Artefacto agregado #13362083597](https://github.com/yudocyudoc/IGC/actions/runs/41910562764/artifacts/13362083597).

## Resultado exhaustivo verificado

| Tipo de archivo de máquina | Blobs con SHA comprobado | Bytes comprobados | Filas de datos numéricos | Filas no estándar | Líneas vacías |
|---|---:|---:|---:|---:|---:|
| Registro continuo \`5.coffee_machine_acc\` | **12** | 168,167,524 | **4,503,292** | **0** | 4 |
| Fragmentos horarios \`5.coffee_machine_acc\` | **185** | 501,132,969 | **13,197,288** | **1** | 0 |
| Fragmentos \`5.kave\` | **12** | 26,604,798 | **695,015** | **0** | 0 |
| **Total** | **209** | **695,905,291** | **18,395,595** | **1** | **4** |

**Total no vacío: 18,395,596 filas**. Se recorrieron 55 carpetas de turno; 53 contienen archivos de máquina y dos carecen de series (las carpetas vacías se conservaron en la extracción de Drive). Todos los 209 blobs publicados en el árbol fijado pasaron el chequeo Git SHA-1 y tamaño. No se empleó muestreo de filas.

### Única anomalía

La segunda pasada de clasificación (misma fuente y código actualizado, CI PASS) mostró:
- **Una fila con exactamente un campo** en un fragmento estándar \`5.coffee_machine_acc\`, en vez de cuatro.
- El campo no tiene formato horario válido ni caracteres alfabéticos ASCII.
- No contiene palabras de anotación explícita entre \`espresso\`, \`latte\`, \`cappuccino\`, \`drink\`, \`beverage\`, \`coffee\`, \`label\`, \`order\`, \`chocolate\`, \`americano\`.
- El contenido exacto de la fila **no se publicó**; tampoco se presenta como etiqueta o intervalo de máquina. Podría ser un marcador/corrupción/valor aislado y **su semántica sigue desconocida**. Un código numérico desconocido tampoco puede interpretarse como tipo de bebida sin diccionario externo.

### Dictamen respecto de la tabla 3 del artículo

La afirmación de Tran et al. (*Scientific Data* 2025, tabla 3) de que se incluyen **algunas muestras etiquetadas por tipo de bebida** continúa sin correspondencia identificada en los datos públicos examinados. **Lo que se verificó** es el contenido de **los 209 blobs de señal del espejo GitHub**, no la inexistencia universal de posibles anotaciones en un archivo auxiliar, en metadatos del RAR, en materiales no publicados o en la documentación de los autores.

La ausencia de campos textuales de bebida entre 18.4 millones de filas de aceleración **no prueba que la máquina estuviera inactiva ni que los segmentos representen operaciones únicas**; muestra que **no existe una etiqueta física explícita legible en el formato examinado**, salvo una fila anómala sin interpretación certificada.

El libro \`orders_summary.xlsx\` tiene hora de recepción y cantidades \`coffee_cup\`, \`choco_cup\`, \`cake\`, no pares \`order_ID → ciclo de cafetera\`. No se hizo matching temporal por cercanía, ni calibración POS–sensor por máxima correlación. El vínculo con \`order_ID\` y \`servicio_fin\` **permanece NO VALIDADO**.

## Consecuencia de decisión

**Cerrar la búsqueda de etiquetas por muestreo o escaneo adicional de los mismos blobs GitHub**: el canal ya fue exhaustivamente leído con evidencia reproducible. Reabrir solo si se obtiene:
1. Un **manifiesto externo verificable de etiquetas** (ruta/archivo, clase, protocolo, autor de anotación, límites del ciclo, enlace de captura), o
2. Una **diferencia concreta** al cotejar Figshare v3 o el conjunto íntegro de Drive frente a los 209 hashes GitHub, o
3. Una respuesta de los autores con ubicación precisa de las muestras de bebida referidas en la tabla 3.

En la Arena se conserva únicamente lo identificado: pedidos POS recibidos, señales ambientales, T110 apertura/cierre y aceleración XYZ **como observación física sin atribución de tarea**. Ningún ciclo completo, tipo de bebida ni finalización de pedido ha sido validado por este escaneo.

## Invariantes

**D/B/M no modificados; O2 no autorizado; G4=NOT_RUN; G5=NOT_RUN; F5 independent reserve=NOT_CREATED.** CI y acta documentan validez del instrumento de lectura, no validez de los operadores de despacho. El PR permanece **Draft**, apilado sobre #166.
