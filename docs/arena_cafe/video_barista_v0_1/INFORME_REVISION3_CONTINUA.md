# Arena IGC — Revisión 3: tramo continuo de P045 y recursos compartidos

**Fecha:** 2026-11-04. **Estado:** EXPLORATORIO, RETROSPECTIVO, NO CIEGO, SIN VALIDACIÓN INDEPENDIENTE.  
**Objeto:** video de cafetería, secuencia de P045 (dos *Hot Latte* en panel revisado), incluidos los extremos contextuales de las tandas vecinas. **No se modificaron archivos originales ni modelos D/B/M.**

## 1. Alcance y controles

- Fuente: `/mnt/data/videoplayback.mp4`, **SHA-256 `cd37c9d3f231f4d307c4f3353ce1dc096fad4185bbdf6ffab06266b9d41290c5`**; 640×360 px, 30 fps declarado en archivo, duración de video aproximada 5024.87 s.
- Tramo revisado: **4018–4152 s**, es decir 66:58–69:12 del reloj del video (**134 s** de extensión entre fotogramas extremos).
- Evidencia nueva: **68 fotogramas**, uno cada **2 s**, recorte de la vista principal x=0..389. Se extrajeron también **seis mosaicos de refinamiento de 1 s** alrededor de transiciones seleccionadas. El recuadro secundario NO se usó.
- Registro: **68 lecturas por fotograma**, **20 anotaciones cualitativas** (incluyen estados, transiciones, actividad no identificable y una microacción superpuesta; **NO equivalen a 20 tareas completadas**) y **10 instantáneas seleccionadas de estado de productos**.
- Comparación puntual: dos episodios previamente anotados de sujeción de jarra en P045. El revisor es nuevamente el asistente y ya conocía parte de los registros: **NO es doble codificación ciega ni acuerdo interevaluador**.
- **Tiempo:** los segundos corresponden al tiempo de presentación del archivo; no se verificó la igualdad entre tiempo de video y tiempo físico real, ni ausencia de cortes. Dos fotogramas próximos **no garantizan** continuidad de actividad entre ellos.
- **Tanda:** la asociación de productos a P045 es contextual (panel visual), no trazabilidad POS. Los extremos 4018–4029 y 4147–4152 pueden contener acciones de P044/P046.

## 2. Cronología de evidencia, no cadena cerrada de proceso

| Instantes aproximados (s video) | Evidencia de vista principal | Qué NO permite afirmar |
|---|---|---|
| **4018–4039** | Manipulaciones de utensilios, estación de portafiltro y zona parcialmente fuera de encuadre | No se asignan todas a P045 ni se determina molienda, dosis o inicio de pedido |
| **4040–4049** | Contacto con el grupo; recipiente bajo la zona del grupo | No se certifica bomba activa, extracción ni tiempo automático de espresso |
| **4050–4068** | Se sitúan taza y jarra; barista manipula útiles y aproxima una jarra a la lanza | No se identifican ingredientes ni cantidades |
| **4068–4086** | Primer episodio delimitable de **jarra sostenida junto a lanza**, más aproximación y retirada | No se observa un estado instrumental `vapor_activo` |
| **4085–4102** | Retiro de jarra y acciones parciales fuera del área de observación | No se clasifican como espera ni inactividad |
| **4103–4106** | Una taza reaparece con **superficie montada visible** hacia 4105–4106 | El vertido completo y el instante de finalización real no se observan íntegramente |
| **4107–4110** | Barista inclina un envase sobre una jarra; acción compatible con trasvase de líquido | Ingrediente exacto, volumen y merma no identificados |
| **4112–4128** | Segundo episodio de **jarra sostenida junto a lanza**; la primera taza montada permanece visible en varios fotogramas | No se confirma que la lanza esté liberando vapor en cada instante |
| **4121–4123** | **Simultaneidad en fotogramas:** una mano mueve la taza mientras se mantiene la jarra junto a la lanza | No implica atención divisible ilimitadamente ni capacidad multitarea general |
| **4130–4142** | Primera taza visible; actividad del barista parcialmente fuera del encuadre | No reconstruimos el segundo montaje ni inferimos ocio |
| **4144–4145** | **Dos tazas con montaje visible simultáneamente** en el mostrador | No equivalen a dos entregas a clientes |
| **4145–4146** | Las dos tazas dejan de verse en esa región del encuadre | No acredita entrega, pago ni salida de la cafetería |
| **4147–4152** | Manipulaciones posteriores de útiles junto al grupo | No podemos adjudicarlas a P045; posible siguiente tanda |

La cronología tiene superposiciones intencionales entre eventos de distintos tipos: una operación de jarra, una manipulación de producto y un estado visible de taza pueden coexistir. Las categorías cualitativas de los 68 fotogramas se guardan en `lecturas_cada_2s_p045.csv` y las 20 observaciones en `eventos_cualitativos_p045.csv`.

## 3. Episodios delimitables: jarra próxima a lanza ≠ vapor certificado

| Episodio | Acercamiento/inicio `[lo,hi]` | Retirada/fin `[lo,hi]` | Duración compatible (segundos de video) | Anotación original |
|---|---|---|---:|---|
| P045-steam-09 | [4068,4070] | [4084,4086] | **14–18 s** | inicio [4066,4068], final [4082,4086] |
| P045-steam-10 | [4112,4114] | [4126,4128] | **12–16 s** | inicio [4110,4112], final [4124,4128] |
| **Suma de ambas** | — | — | **26–34 s** | Suma descriptiva de intervalos de sujeción visual; **no** utilización de toda la jornada |

Se mantuvo la definición de la revisión anterior (sujeción visual de jarra próxima a lanza) en lugar de inferir activación de vapor, energía, temperatura o ciclo físico certificado. Son episodios no solapados; el barista aparece realizando otras acciones entre ellos. Una única lanza visible no prueba la cantidad total de lanzas del establecimiento.

## 4. Hallazgo nuevo: superposición de subrecursos

En fotogramas **4121, 4122 y 4123** se observa una jarra mantenida junto a la lanza y la primera taza desplazándose en el mostrador. Es evidencia visual de dos **microacciones compatibles en un mismo intervalo**, probablemente ejecutadas por un mismo barista, pero sin identificación biométrica ni seguimiento continuo de manos.

**Implicación metodológica para Arena:** no imponer sin prueba la regla `barista_ocupado_en_lanza ⇒ barista_no_puede_realizar_ninguna_otra_accion`. Una regla más cauta considera recursos y requisitos diferentes para cada acción: **lanza**, **manos**, **atención**, **zona física**; algunos recursos pueden ser compartidos y ciertas actividades pueden ser incompatibles. Ni la capacidad de multitarea ni sus costos están calibrados aquí.

La propuesta operativa es distinguir (i) **estado visible de herramienta**, (ii) **interacción manual**, (iii) **estado visible de producto**, en tres capas que se solapan sin sumar la misma fracción de tiempo dos veces.

## 5. Stocks y transiciones, estrictamente observables

- **4105–4106 s:** primera taza con superficie montada aparece a la vista (mínimo 1 en el campo visible).
- **4114–4126 s:** la taza montada se ve en muestras del segundo episodio de jarra; se reubica cerca de **4122 s**.
- **4144–4145 s:** ambas tazas montadas se ven simultáneamente (mínimo 2 en esa zona).
- **4146 s:** ninguna de las dos tazas montadas se ve ya en esa región (0 **visibles**, no stock global 0).

Esto admite un **estado visual** `tazas_montadas_visibles_en_estacion` en instantes muestreados. No permite derivar una trayectoria continua de inventario ni una conservación cerrada del flujo empresarial: existen movimientos fuera de cámara, fronteras de observación y falta de trazabilidad de objetos. Ni `montado` ni `sale_del_encuadre` deben transformarse en `pedido_completado` o `entregado_cliente`.

## 6. Qué ganamos y qué falta

**Ya disponible:** tabla de observaciones y estados de la secuencia, simultaneidad de tareas en fotogramas, dos intervalos de sujeción con incertidumbre, cambio visible en número de tazas montadas, evidencia rastreable a cada fotograma.

**No disponible:** utilización total del barista, duración de extracción autónoma, detección de vapor, etiqueta de ingrediente/dosis, entrega de cliente, tiempos físicos sin edición, causalidad del cuello de botella, capacidad máxima, cantidades de pedidos POS. El muestreo 2s y las oclusiones impiden afirmar exhaustividad de microeventos; la cobertura temporal del muestreo no equivale a cobertura completa de actividades.

**Próxima compuerta recomendable:** tomar un segmento diferente (preferentemente una tanda con acciones diversas), codificarlo desde MP4 con otra persona o modelo **sin mostrar estas etiquetas ni los tiempos previos**, y contrastar de forma independiente una lista de clases definida antes. Solo después probar modelos de ocupación condicionados a la calidad del registro. Esto no altera compuertas G4/G5.

## 7. Entregables, procedencia y límites

- `lecturas_cada_2s_p045.csv`: **68 instantáneas** codificadas cualitativamente.
- `eventos_cualitativos_p045.csv`: **20 observaciones/segmentos** no necesariamente exclusivos ni constituyentes de un proceso cerrado.
- `estados_visuales_productos_p045.csv`: 10 instantáneas seleccionadas.
- `comparacion_sujeciones_p045.csv`: límites con incertidumbre y contraste histórico (mismo revisor).
- `metadatos_revision3_p045.json`: hash, alcance, evidencia, invariantes.
- `evidencia_resumen_p045.jpg`: ocho fotogramas relevantes del video.
- `P045_continuo_2s/fotogramas/*.jpg`: 68 fotogramas recortados de la vista principal.
- `P045_continuo_2s/panel_01..06.jpg`: seis contact sheets del tramo completo.
- `P045_continuo_2s/refinamientos_1s/detalle_01..06.jpg`: refinamiento de seis ventanas seleccionadas.
- `extraer_p045_continuo.py`, `extraer_refinamiento_p045.py`, `generar_revision3_p045.py`: código local de extracción y ensamblaje de anotaciones.

**Procedencia:** anotación visual retrospectiva del asistente. **No** certificación de tiempo físico ni observación directa continua. **No** se cambiaron originales, Drive, GitHub, ARENA/D/B/M; G4/G5 NOT_RUN.