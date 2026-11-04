# WEBA F5 · Auditoría de anotaciones de vibración de cafetera y vínculo con pedidos

**Fecha:** 2026-11-04. **Estado:** inspección retrospectiva de metadatos y muestras originales; **no** operador nuevo, **no** ground truth de tareas, **no** nueva reserva ciega. Continúa #165 y mantiene intactos D/B/M, O2, G4/G5 y la reserva F5.

## Pregunta falsable

¿El canal `5.coffee_machine_acc` publica una anotación verificable que permita distinguir **(a)** una señal física de aceleración, **(b)** un ciclo real de operación de la cafetera, **(c)** la clase de bebida producida, y **(d)** el pedido POS `order_ID` al que corresponde, sin asumir coincidencia temporal como equivalencia causal?

**Respuesta acotada:** el canal de señal existe y ofrece medidas crudas. En los **metadatos de árbol versionado** y en las **muestras de contenido examinadas** no encontramos anotaciones utilizables para (b)–(d). **No se inspeccionó el contenido de todos los blobs ni se cotejó íntegramente Figshare v3**, por lo que no se declara ausencia global de etiquetas. La documentación publicada **tampoco acredita un enlace por pedido** entre el registro de la cafetera y POS. Por tanto, no se autoriza convertir la aceleración o una detección algorítmica en `servicio_fin`.

## Fuentes y procedencia

- Artículo científico: Tran et al., *Scientific Data* (2025), DOI [10.1038/s41597-024-04348-z](https://doi.org/10.1038/s41597-024-04348-z). La **tabla 3** afirma expresamente que «several vibration samples labeled with drink type are included»; esto es una afirmación de los autores, **no prueba de una tabla por pedido**. La **tabla 8** describe `5.coffee_machine_acc` como aceleración XYZ cruda y sin calibrar. En la **figura 10**, *Order* y *Coffee machine log* apuntan por separado a *Work shift* (`fromWorkshift`); para el log se documentan `Timestamp` y `Acceleration`, sin `order_ID` en sus propiedades.
- Repositorio público de los autores: [Department-of-System-Engineering/datasets_WEBA](https://github.com/Department-of-System-Engineering/datasets_WEBA), commit fijo **`d6841669e544579547c94b7ce1e8613bbd6b3a39`**, que ya estaba pinneado en los operadores previos. Se consultó el árbol recursivo de ese commit, sin mover la referencia a `main`.
- Archivo de descripción [`Description.txt`](https://github.com/Department-of-System-Engineering/datasets_WEBA/blob/d6841669e544579547c94b7ce1e8613bbd6b3a39/Description.txt) y código original [`code_for_public/preprocessing.py`](https://github.com/Department-of-System-Engineering/datasets_WEBA/blob/d6841669e544579547c94b7ce1e8613bbd6b3a39/code_for_public/preprocessing.py): el código consultado importa `orders_summary` y declara el nombre del canal, pero no implementa un mapeo verificable `order_ID → señal de máquina → bebida completada`.
- Fuente declarada adicional: [Figshare v3](https://doi.org/10.6084/m9.figshare.27186516.v3). **La colección en Figshare no se cotejó exhaustivamente en esta inspección**: no asumir que el espejo GitHub agota los recursos o anotaciones de Figshare.

## Inventario verificable del árbol original (metadatos, no interpretación de ciclo)

La ruta `B.shift_data` contiene **55 carpetas de turno**. El árbol `/git/trees/d6841669e544579547c94b7ce1e8613bbd6b3a39?recursive=1` devuelve `truncated=false`; en este árbol:

| Forma publicada de `5.coffee_machine_acc` | Número | Alcance verificable |
|---|---:|---|
| Un archivo plano por turno | **12 turnos; 12 blobs** | Hay datos de señal (168,167,524 bytes en conjunto); no se inspeccionó el contenido completo de estos blobs grandes |
| Carpeta por turno con subarchivos temporales | **39 turnos; 185 blobs** | Hay fragmentos de aceleración (501,132,969 bytes en conjunto); sus nombres son horarios, no tipos de bebida ni `order_ID` |
| Turnos sin entrada `5.coffee_machine_acc` en el árbol | **4** | `20240122_evening`, `20240202_evening`, `20240307_morning`, `20240308_morning`; ausencia en el árbol **no** significa que la máquina no funcionara |

Total: **51/55 turnos con alguna entrada de datos de máquina y 197 blobs**. Ninguno de los 185 nombres de subarchivos examinados incluye un identificador de pedido ni clase de bebida. Esta afirmación se refiere **solo a nombres y metadatos**; no se infiere ausencia de anotaciones internas en archivos no abiertos.

**Muestras de contenido leídas en el commit fijado:**

- [2024-01-04](https://github.com/Department-of-System-Engineering/datasets_WEBA/blob/d6841669e544579547c94b7ce1e8613bbd6b3a39/B.shift_data/20240104_evening/5.coffee_machine_acc/20240104_141839), blob `781bf79efef7c0f2f5a00851237d8e894eaefe71`.
- [2024-02-23](https://github.com/Department-of-System-Engineering/datasets_WEBA/blob/d6841669e544579547c94b7ce1e8613bbd6b3a39/B.shift_data/20240223_evening/5.coffee_machine_acc/20240223_143153), blob `ed6e907db552a95a286c20bf0ed08a214945995f`.
- [2024-03-08](https://github.com/Department-of-System-Engineering/datasets_WEBA/blob/d6841669e544579547c94b7ce1e8613bbd6b3a39/B.shift_data/20240308_evening/5.coffee_machine_acc/20240308_142322), blob `aa886fe8e110ad507084ba53089741a1e8e79973`.

Las líneas muestreadas presentan **cuatro columnas por fila: hora de pared + tres aceleraciones numéricas**; no incluyen nombre de bebida, `order_ID`, operador de máquina encendida ni marcador de preparación terminada. No se examinó ni publicó aceleración corporal, HR, cuestionarios o identificadores personales.

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

1. **Localizar las muestras etiquetadas por bebida que afirma la tabla 3:** inspeccionar fuente Figshare v3 y, si es necesario, consultar a autores. Guardar rutas, versión, hash, etiqueta, quién anotó, protocolo y definición física del inicio/fin. Si no aparecen, registrarlo como «no localizadas tras búsqueda especificada», nunca como inexistentes.
2. **Separar dos pruebas distintas:** validación de *ciclo de máquina* contra anotación física independiente; y vinculación de ese ciclo a `order_ID` mediante clave explícita, captura manual validada o registro original común. Una no resuelve automáticamente la otra.
3. **Si hay ciclos etiquetados pero no vínculo POS:** admitir solo un futuro operador *actividad física de máquina*, sujeto a evaluación de sensibilidad/especificidad, duraciones y condiciones instrumentales; conservar `orden_desconocida` y `servicio_fin_desconocido`.
4. **Si no hay etiquetas suficientes:** **cerrar la ruta de preparación por pedido WEBA** y conservar el conjunto para los fenómenos realmente observados (llegadas de pedidos, indicadores de turno, pulsos/contactos físicos), evitando escalar algoritmos no identificables. Otra fuente etiquetada puede servir para validar un mecanismo distinto, **sin concatenarla ni equipararla a WEBA**.

### Criterio de parada

No construir nuevo detector ni consumir más turnos para «obtener» una etiqueta que no está en los datos conocidos. Reabrir únicamente con una anotación independiente y reproducible que cambie el peldaño de identificabilidad o habilite una nueva pregunta decisional.

## Estado de Arena

**No se modificaron scripts, modelos, simuladores ni tests** en este paso documental. PR #165 queda como primer operador de contacto T110. Este dictamen **no añade** `service_start`, `service_finish`, botella de recursos, cola, throughput causal ni validez predictiva de Arena. **D/B/M intactos; O2 no autorizado; G4=NOT_RUN; G5=NOT_RUN; reserva F5 independiente=NOT_CREATED.** Esta inspección es retrospectiva, sobre fuente pública accesible y **no** una prueba ciega.
