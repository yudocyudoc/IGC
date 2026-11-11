# Arena IGC · Revisión 4 — P031, registro visual de otro tramo

**Fecha:** 2026-11-04. **Estado:** exploratorio, retrospectivo, mismo asistente y **NO ciego ni independiente**. Esta revisión se hizo a partir de imágenes nuevas del video original antes de leer `tiempos_pedidos.csv` y `operaciones.csv` para la comparación; el asistente ya había visto en conversaciones anteriores los nombres de productos y los intervalos aproximados de P031. No es una prueba de acuerdo interevaluador ni un etiquetado sin conocimiento previo.

## 1. Fuente y muestreo

- MP4 original con SHA-256 **`cd37c9d3f231f4d307c4f3353ce1dc096fad4185bbdf6ffab06266b9d41290c5`**, comprobado contra el archivo de Drive. Video declarado a 30 fps y 640×360 px.
- Se examina el intervalo **2748–2902 s** (45:48–48:22; extensión 154 s). Vista principal recortada a **x=0..389, y=0..359**; no se usa la vista secundaria.
- **78 fotogramas distintos cada dos segundos**, con cinco mosaicos de contacto completos. **45 fotogramas adicionales a un segundo** alrededor de los extremos del tramo y del ensamblado/retiro. Tres mosaicos de refinamiento.
- Anotaciones: **19 observaciones cualitativas**, no mutuamente excluyentes, y **15 instantáneas seleccionadas de estados de recipientes**. Un evento aquí puede ser la presencia de un objeto; no significa una operación finalizada. Las imágenes son muestras discretas: no prueban continuidad de una acción en el intervalo entre dos fotografías.
- **No verificado:** reloj físico de la cafetería, continuidad/cortes del video, trazabilidad por objeto o POS, identidad del trabajador, funcionamiento de bomba, dosis ni tiempos reales de extracción.

## 2. Qué se observa sin inferir productos o ventas

| Segundos video | Evidencia desde fotogramas nuevos | Frontera de interpretación |
|---|---|---|
| **2748–2753** | Termina un vertido y se retira un vaso. | Probable resto del tramo anterior, no atribuir a P031. |
| **2754–2778** | Manipulaciones repetidas de grupo, portafiltro y utensilios. Un recipiente metálico queda bajo la zona del grupo. | No identificar molienda, extracción o ciclo autónomo ni medir uso de máquina. |
| **2780–2784** | Se inclina un envase sobre recipiente transparente que queda en la barra. | Se observa vertido; ingrediente y cantidad no medidos. |
| **2784–2810** | Recipiente con contenido permanece en barra mientras el barista manipula herramientas de máquina. | Superposición **estado de objeto + intervención en otro recurso**; no clasificar como ocio. |
| **2812–2818** | Preparación de vaso alto con hielo. Alrededor de 2816 aparece un vaso oscuro a la derecha. | No afirmar correspondencia de objetos con productos de la pantalla. |
| **2824–2842** | Se añade una rodaja amarilla al vaso con hielo y se manipula o mezcla; vaso oscuro sigue visible a la derecha. | Rodaja aparentemente cítrica, sin ingrediente exacto certificado. |
| **2850–2862** | Más vertidos, remoción y cambio de apariencia del líquido en el vaso con rodaja; vaso oscuro continúa estacionado. | No medir dosis, trabajo continuo ni composición. |
| **2868–2882** | Se manipula recipiente metálico y se vierte su contenido en un vaso corto. | Es una tercera línea de manipulación visible; no receta inferida. |
| **2874–2888** | Hay **tres recipientes con contenido visibles a la vez**: alto oscuro, alto claro y corto. El barista sigue trabajando sobre el corto. | Mínimo observado en la región, NO tres bebidas terminadas ni capacidad máxima de barra. |
| **2889–2893** | Se ajustan accesorios y se desplazan vasos; en la imagen de 2893 aún están visibles en manos. | No está definido inequívocamente el fin de montaje. |
| **2894** | La región frontal antes ocupada está despejada. | Fin de **visibilidad local**, no entrega al cliente ni inventario global cero. |
| **2896–2902** | El barista vuelve a manipular la zona de máquina. | Puede corresponder a la siguiente tanda. |

## 3. Resultado del contraste con la anotación histórica P031

La anotación histórica describe P031 como una tanda de **1 Iced Americano, 1 Black Sesame Cream Latte y 1 Green Tangerine Ade**. Esa lista procede del panel revisado, no se usa para asignar de forma automática nombres a los recipientes del video.

| Hito | Previo | Esta segunda revisión | Veredicto |
|---|---|---|---|
| Inicio contextual de la tanda | 2750–2760 s | tras retirar el vaso anterior en ~2753, manipulación nueva en 2754–2760 | **Compatible**, no identidad de pedido certificada |
| Fin de montaje | 2880–2890 s | último vertido al vaso corto ~2877–2881; ajustes y accesorios hasta ~2892 | **Ambiguo por definición**; no validar ni sustituir automáticamente |
| Salida del último conjunto visible | 2890–2900 s | (2893,2894] s con muestreo refinado a 1 s | **Compatible, más estrecho**; no entrega al cliente |
| Clases de operaciones | 0 episodios registrados en `operaciones.csv` para P031 | 19 observaciones de tipos distintos (incluyen estados, no solo acciones) | **No hay comparación par a par posible** |

**No puede calcularse acuerdo interevaluador, sensibilidad, precisión o exhaustividad de acciones**. El registro original de operaciones no tenía una clasificación de P031, y ambas revisiones usan el mismo asistente.

## 4. Implicación para stocks y recursos (no calibración)

- **Stock mínimo localizado observado**: en el fotograma de **2874 s** y otros cercanos hay al menos **tres recipientes con contenido en la superficie frontal**. Son conteos instantáneos; no se pueden integrar como inventario continuo ni afirmar que hay tres bebidas concluidas.
- **Intercalación de actividades**: un recipiente se mantiene en la barra mientras el barista manipula la máquina o monta otros vasos. Así, `producto_en_estación` y `barista_interactuando_con_otra_estación` **pueden coexistir**. No implica que dos máquinas estén activas o que exista multitarea humana continua.
- **Límite físico inferior, no superior**: el video prueba que caben simultáneamente esos tres recipientes visibles en esa zona; **no** muestra cuál es la capacidad máxima ni el espacio total disponible.
- **Fronteras observadas**: `retirado_de_esta_región` no equivale a `entregado_al_cliente`, `cobrado` o `stock_global=0`.
- Las observaciones no bastan para estimar tiempos de servicio, utilización del barista, rendimiento o causalidad de un cuello de botella. Para eso necesitamos etapas con cobertura completa y calibración del reloj físico.

## 5. Problema abierto: definición del fin de montaje

El análisis previo acotó fin de montaje a **2880–2890 s**, pero se observan manipulaciones de accesorios sobre los vasos después del vertido final, próximas a **2889–2892 s**. Si `montaje_fin` incluye tapa, popote u otros accesorios, el marcador previo puede ser prematuro; si solo significa último vertido, quizá sea compatible. **No hay decisión de definición implementada**, por lo que se marca **REVISAR DEFINICIÓN**, no error probado de la revisión anterior.

## 6. Calidad y próximos pasos

**OBSERVADO:** objetos y su presencia, contacto manual en equipo, vertidos, tres recipientes coexistiendo, retirada local acotada por fotogramas.

**INFERIDO:** asociación contextual de parte de esos objetos con el lote P031. No atribuir tipos concretos de bebidas, insumos o dosis exclusivamente por color o apariencia.

**DESCONOCIDO:** continuidad de grabación a tiempo real, activación de bomba/vapor, ingredientes, tiempos autónomos, actividad oculta y entrega efectiva.

**Recomendación:** fijar un vocabulario operacional común antes de otro segmento: `objeto_aparece`, `objeto_estacionado`, `barista_manipula_objeto`, `barista_interactua_con_equipo`, `liquido_vertido_visible`, `objeto_sale_de_region`, `recurso_activo_verificado` (solo con evidencia propia). Separar `ultimo_vertido` de `montaje_completo` y `fuera_de_campo` de `inactivo`. Un revisor distinto, sin etiquetas anteriores, debe revisar una sección reservada antes de hablar de validación.

## 7. Procedencia de archivos

- `observaciones_p031.csv`: 19 observaciones mixtas con respaldo de segundos fotográficos; no duraciones laborales certificadas.
- `estados_visuales_p031.csv`: 15 muestras seleccionadas de mínimos de recipientes con contenido, incluye refinamiento t=2893 y 2894; sin trazabilidad individual completa.
- `manifiesto_78_fotogramas.csv`: tiempos, rutas locales y SHA-256 individual de cada imagen de 2s.
- `comparacion_con_registro_previo.csv`: alineación posterior con la anotación P031 original.
- `contacto_01.jpg` ... `contacto_05.jpg`: cobertura de todas las muestras de 2 s.
- `refinamiento_01.jpg` ... `refinamiento_03.jpg`: 45 muestras de 1 s de transiciones seleccionadas.
- `transiciones_clave.jpg`: ejemplos de coexistencia e intervenciones.
- `extract_frames.py`, `refine_transitions.py`, `build_review.py`, `compare_and_package.py`: reconstrucción reproducible de fotogramas y ensamblaje de la revisión.

**No se han modificado archivos originales del Drive o modelo de Arena; D/B/M intactos, G4/G5 no ejecutados.** Este informe es una lectura observacional del video, no la calibración del simulador.