# WEBA F5 · Auditoría de anotaciones de vibración de cafetera y vínculo con pedidos

**Fecha:** 2026-11-04. **Estado:** inspección retrospectiva de metadatos y muestras originales; **no** operador nuevo, **no** ground truth de tareas, **no** nueva reserva ciega. Continúa #165 y mantiene intactos D/B/M, O2, G4/G5 y la reserva F5.

## Pregunta falsable

¿Los canales `5.coffee_machine_acc` y `5.kave` publican una anotación verificable que permita distinguir **(a)** una señal física de aceleración, **(b)** un ciclo real de operación de la cafetera, **(c)** la clase de bebida producida, y **(d)** el pedido POS `order_ID` al que corresponde, sin asumir coincidencia temporal como equivalencia causal?

**Respuesta acotada:** el canal de señal existe y ofrece medidas crudas. En los **metadatos de árbol versionado** y en las **muestras de contenido examinadas** no encontramos anotaciones utilizables para (b)–(d). **No se inspeccionó el contenido de todos los blobs ni se cotejó íntegramente Figshare v3**, por lo que no se declara ausencia global de etiquetas. La documentación publicada **tampoco acredita un enlace por pedido** entre el registro de la cafetera y POS. Por tanto, no se autoriza convertir la aceleración o una detección algorítmica en `servicio_fin`.

## Fuentes y procedencia

- Artículo científico: Tran et al., *Scientific Data* (2025), DOI [10.1038/s41597-024-04348-z](https://doi.org/10.1038/s41597-024-04348-z). La **tabla 3** afirma expresamente que «several vibration samples labeled with drink type are included»; esto es una afirmación de los autores, **no prueba de una tabla por pedido**. La **tabla 8** describe `5.coffee_machine_acc` como aceleración XYZ cruda y sin calibrar. En la **figura 10**, *Order* y *Coffee machine log* apuntan por separado a *Work shift* (`fromWorkshift`); para el log se documentan `Timestamp` y `Acceleration`, sin `order_ID` en sus propiedades.
- Repositorio público de los autores: [Department-of-System-Engineering/datasets_WEBA](https://github.com/Department-of-System-Engineering/datasets_WEBA), commit fijo **`d6841669e544579547c94b7ce1e8613bbd6b3a39`**, que ya estaba pinneado en los operadores previos. Se consultó el árbol recursivo de ese commit, sin mover la referencia a `main`.
- Archivo de descripción [`Description.txt`](https://github.com/Department-of-System-Engineering/datasets_WEBA/blob/d6841669e544579547c94b7ce1e8613bbd6b3a39/Description.txt) y código original [`code_for_public/preprocessing.py`](https://github.com/Department-of-System-Engineering/datasets_WEBA/blob/d6841669e544579547c94b7ce1e8613bbd6b3a39/code_for_public/preprocessing.py): el código consultado importa `orders_summary` y declara el nombre del canal, pero no implementa un mapeo verificable `order_ID → señal de máquina → bebida completada`.
- Fuente declarada adicional: [Figshare v3](https://figshare.com/articles/dataset/WEBA_dataset/27186516), versión 3 de **2024-12-07**. La página presenta un único archivo descargable, **`WEBA_dataset.rar` (877.5 MB, ID Figshare `51041552`)**. El depósito no proporciona en la página pública un índice interno de archivos/etiquetas. **No fue posible descargar o inspeccionar el archivo RAR desde este entorno**; ni se verificó que la copia de GitHub (subida en diciembre 2025) sea byte a byte idéntica a su contenido. Por ello, **no se pueden descartar anotaciones que solo estén dentro del RAR**.

## Inventario verificable del árbol original (metadatos, no interpretación de ciclo)

La ruta `B.shift_data` contiene **55 carpetas de turno**. El árbol `/git/trees/d6841669e544579547c94b7ce1e8613bbd6b3a39?recursive=1` devuelve `truncated=false`; en este árbol:

| Forma publicada de `5.coffee_machine_acc` | Número | Alcance verificable |
|---|---:|---|
| Un archivo plano por turno | **12 turnos; 12 blobs** | Hay datos de señal (168,167,524 bytes en conjunto); no se inspeccionó el contenido completo de estos blobs grandes |
| Carpeta por turno con subarchivos temporales | **39 turnos; 185 blobs** | Hay fragmentos de aceleración (501,132,969 bytes en conjunto); sus nombres son horarios, no tipos de bebida ni `order_ID` |
| Directorio alternativo `5.kave` (húngaro: *café*) | **2 turnos; 12 blobs** | `20240307_morning` y `20240308_morning`; subarchivos con nombres horarios (no se estimó cobertura de adquisición), **no son ausencia de cafetera** |
| Turnos sin ningún canal de máquina `5.coffee_machine_acc` ni `5.kave` | **2** | `20240122_evening`, `20240202_evening`; ausencia en el árbol **no** prueba que la máquina no funcionara |

**Inventario corregido tras buscar toda la ruta `B.shift_data`, no solo el nombre estandarizado:** **53/55 turnos con alguna entrada de datos de máquina**, **12 archivos planos + 185 fragmentos `5.coffee_machine_acc` + 12 fragmentos `5.kave` = 209 blobs**. Ninguno de los **197 nombres de fragmentos** contiene identificador `order_ID` o clase de bebida. La afirmación se refiere **solo a nombres/metadatos**; no prueba ausencia de anotaciones internas. **Enmienda explícita:** la versión previa de esta acta reportó incorrectamente 51/55 y 197 blobs por buscar solamente `5.coffee_machine_acc`. La carpeta `5.kave` es evidencia de que una búsqueda léxica restringida puede crear falsos negativos.

**Muestras de contenido leídas en el commit fijado:**

- [2024-01-04](https://github.com/Department-of-System-Engineering/datasets_WEBA/blob/d6841669e544579547c94b7ce1e8613bbd6b3a39/B.shift_data/20240104_evening/5.coffee_machine_acc/20240104_141839), blob `781bf79efef7c0f2f5a00851237d8e894eaefe71`.
- [2024-02-23](https://github.com/Department-of-System-Engineering/datasets_WEBA/blob/d6841669e544579547c94b7ce1e8613bbd6b3a39/B.shift_data/20240223_evening/5.coffee_machine_acc/20240223_143153), blob `ed6e907db552a95a286c20bf0ed08a214945995f`.
- [2024-03-08 (tarde)](https://github.com/Department-of-System-Engineering/datasets_WEBA/blob/d6841669e544579547c94b7ce1e8613bbd6b3a39/B.shift_data/20240308_evening/5.coffee_machine_acc/20240308_142322), blob `aa886fe8e110ad507084ba53089741a1e8e79973`.
- [2024-03-07 (mañana, carpeta alternativa)](https://github.com/Department-of-System-Engineering/datasets_WEBA/blob/d6841669e544579547c94b7ce1e8613bbd6b3a39/B.shift_data/20240307_morning/5.kave/20240307_134204), blob `f5946c73e538c376f6e547ad22fe3102939eee99`.
- [2024-03-08 (mañana, carpeta alternativa)](https://github.com/Department-of-System-Engineering/datasets_WEBA/blob/d6841669e544579547c94b7ce1e8613bbd6b3a39/B.shift_data/20240308_morning/5.kave/20240308_114003), blob `1989150a3b2ce23b71a4b9734bf3aaebfeb8d4e5`.

Las líneas muestreadas, incluidas las de `5.kave`, presentan **cuatro columnas por fila: hora de pared + tres aceleraciones numéricas**; no incluyen nombre de bebida, `order_ID`, operador de máquina encendida ni marcador de preparación terminada. No se examinó ni publicó aceleración corporal, HR, cuestionarios o identificadores personales.

## Hallazgo de localización (búsqueda 2026-11-04)

La búsqueda examinó (a) tabla 3/tabla 8/figura 10 del paper, (b) `Description.txt` y `code_for_public/preprocessing.py`, (c) árbol GitHub recursivo completo `truncated=false`, y (d) la página de Figshare v3 (identificación de archivo RAR, **sin inspección del interior del archivo**). **Etiqueta de bebida concreta: NO LOCALIZADA; inicio/fin de ciclo externo: NO LOCALIZADO; vínculo a `order_ID`: NO LOCALIZADO.** Lo encontrado son rutas verificables de señales crudas. No elevar la afirmación de la tabla 3 a una etiqueta recuperada.

## Escalera de identificabilidad y límites

| Nivel | Proposición | Dictamen en esta inspección |
|---|---|---|
| 0 | El repositorio contiene aceleración de máquina con hora | **OBSERVADO** en archivos muestreados; unidades crudas según autores |
| 1 | Un segmento contiene vibración por encima del reposo instrumental | **CANDIDATO MEDIBLE**, requeriría método de fondo, QC y cobertura; no equivale a `máquina operando` |
| 2 | Un intervalo corresponde a operación física de la cafetera | **NO VALIDADO**: se necesitan etiquetas externas de encendido/ciclo y controles negativos |
| 3 | Un ciclo corresponde a bebida de cierta clase | **NO IDENTIFICADO** con las muestras y metadatos inspeccionados; tabla 3 afirma que existen *algunas* muestras etiquetadas, pendientes de localizar y verificar |
| 4 | Una bebida se asocia inequívocamente a `order_ID` | **NO VALIDADO**: la figura 10 relaciona ambos con `shift_ID`, no entre sí |
| 5 | El pedido finalizó su servicio o entrega | **NO IDENTIFICABLE con el material comprobado**: preparar espresso no equivale a emplatar, atender o entregar |

**Prohibiciones:** no emparejar pedidos por cercanía temporal, ni elegir un desfase POS↔máquina que maximice correlación retrospectiva; no inferir cobertura de sensores de períodos sin registros; no tratar longitud de archivo como duración de extracción; no asumir que el inicio de un fragmento es inicio de máquina o que su fin es fin de bebida. El límite de único barista por turno no elimina estas ambigüedades.

## Siguiente compuerta (antes de cualquier detector)

1. **Localizar las muestras etiquetadas por bebida que afirma la tabla 3:** **pendiente real** inspeccionar *el interior* de `WEBA_dataset.rar` (Figshare v3, file ID `51041552`), y comparar su manifiesto de rutas contra el árbol GitHub en commit fijo; revisar, con búsqueda sensible a nombres alternativos/húngaros, archivos de anotaciones, encabezados y columnas no puramente numéricas. Si se encuentran, registrar versión/hash, definición de anotación, quién y cómo anotó, clase, instante y vínculo al orden. Si no aparecen tras inspección del archivo completo, pedir a autores el inventario exacto de los ejemplos citados. No llamar «inexistentes» a etiquetas no halladas.
2. **Separar dos pruebas distintas:** validación de *ciclo de máquina* contra anotación física independiente; y vinculación de ese ciclo a `order_ID` mediante clave explícita, captura manual validada o registro original común. Una no resuelve automáticamente la otra.
3. **Si hay ciclos etiquetados pero no vínculo POS:** admitir solo un futuro operador *actividad física de máquina*, sujeto a evaluación de sensibilidad/especificidad, duraciones y condiciones instrumentales; conservar `orden_desconocida` y `servicio_fin_desconocido`.
4. **Si no hay etiquetas suficientes:** **cerrar la ruta de preparación por pedido WEBA** y conservar el conjunto para los fenómenos realmente observados (llegadas de pedidos, indicadores de turno, pulsos/contactos físicos), evitando escalar algoritmos no identificables. Otra fuente etiquetada puede servir para validar un mecanismo distinto, **sin concatenarla ni equipararla a WEBA**.

### Criterio de parada

No construir nuevo detector ni consumir más turnos para «obtener» una etiqueta que no está en los datos conocidos. Reabrir únicamente con una anotación independiente y reproducible que cambie el peldaño de identificabilidad o habilite una nueva pregunta decisional.

## Estado de Arena

**No se modificaron scripts, modelos, simuladores ni tests** en este paso documental. PR #165 queda como primer operador de contacto T110. Este dictamen **no añade** `service_start`, `service_finish`, botella de recursos, cola, throughput causal ni validez predictiva de Arena. **D/B/M intactos; O2 no autorizado; G4=NOT_RUN; G5=NOT_RUN; reserva F5 independiente=NOT_CREATED.** Esta inspección es retrospectiva, sobre fuente pública accesible y **no** una prueba ciega.
