# Arena IGC · F4 · Dos mecanismos rivales de cuello de botella (testigo de desarrollo)

**Fecha:** 2026-11-03. **Plan rector:** revisión/implementación de cafetería v3.2, F4 (§5); primero F3 D/B/M genuino y después F4–F5 según resultados. **Alcance de este incremento:** construir una *pareja física testigo* sobre el **O0 ya conocido**, sin malla, sin nuevo motor, sin proveedores y **sin abrir un G4/G5**.

## Pregunta científica que no cambia

¿Puede la observación disponible permitir que dos mecanismos físicamente diferentes se mantengan compatibles, aunque al ejecutar la **misma acción** produzcan respuestas diferentes? Una coincidencia de entregas no localiza por sí sola el cuello. La minería P solo se justificaría si, frente a B1/B2 y con igual información, aportara una regularidad estructural nueva que ayudara a distinguir o intervenir.

## Un único testigo constructivo; NO búsqueda de parámetros

Se utiliza el **motor DES existente** `scripts/arena_physical/des_engine.py` (FIFO, stock inicial cero, buffers no limitados, completaciones→aceptaciones→arranques aguas abajo primero). Se leen **únicamente las 15 entradas públicas POS de O0**; no `ev01.SPEC`, eventos FULL ni configuraciones ocultas. La ventana de construcción es t={0,2,4,6,8,10} min y las entregas observadas en O0 son [0,0,2,4,6,8].

Dos **hipótesis sintéticas**, no mecanismos recuperados de la cafetería real ni la configuración secreta de EV-01:

| Hipótesis | Preparación (min/pedido) | Despacho | Transferencia final | Capacidad nominal mínima |
|---|---:|---:|---:|---:|
| A · lenta preparación | 1 | 3/5 | 2/5 | 60/h, en preparación |
| B · lento despacho | 3/5 | 1 | 2/5 | 60/h, en despacho |

Todos tienen inicialmente un servidor por etapa; las capacidades respectivas son **A: 60/100/150 h⁻¹** y **B: 100/60/150 h⁻¹**. Se intercambia la ubicación del servicio lento preservando la suma de duraciones iniciales (2 min) y la tasa límite (1/min). Es una construcción analítica dirigida, no se recorren capacidades ni se busca la mejor tupla de un catálogo.

**Admisión S0, exclusiva de desarrollo:** cada hipótesis debe reproducir exactamente **todos los seis conteos acumulados O0** (tolerancia 0 pedidos). También tienen que tener colas internas diferentes en las mismas lecturas; si no, no serían dos hipótesis físicas distintas para este contraste.

### Una intervención idéntica, un único resultado primario

Acción predeterminada en este diseño: **añadir un servidor idéntico en preparación desde t=0**, repitiendo la misma secuencia de 15 llegadas y estados iniciales vacíos en **dos mundos contrafactuales nuevos del DES**, no alterando el estado de la cafetería después del minuto 10. El contraste principal es `|entregas_A(10) − entregas_B(10)|`, con un umbral exploratorio de **3 pedidos** para que valga la pena continuar el diseño.

Esto es una **pregunta predictiva**, no una optimización empresarial. La viabilidad real del segundo servidor (espacio, persona, máquina, inversión, inventarios) **no fue evaluada**. No existe utilidad, regret ni costo calculado; por tanto tampoco «mejora empresarial».

Que el testigo cumpla el umbral en construcción **no certifica su rendimiento prospectivo**. La elección de los mecanismos, servicios y umbral fue efectuada con O0 ya conocido; no tiene una reserva independiente ni un prerregistro G4 válido para G5.

## Resultado ejecutado: dos rivales, un mismo O0, seis pedidos de divergencia

**Ejecución real:** [CI F4 41731608453](https://github.com/yudocyudoc/IGC/actions/runs/41731608453), artefacto [13277270769](https://github.com/yudocyudoc/IGC/actions/runs/41731608453/artifacts/13277270769), 10 pruebas (3 físicas sin artefacto + 7 adversariales con O0) aprobadas. La CI coteja los dos modelos contra las entradas y conteos públicos existentes, y ejecuta el **DES original** para los dos escenarios base y sus dos intervenciones.

| Minuto | O0 observado = A base = B base | A con +1 preparación | B con +1 preparación |
|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 |
| 2 | 0 | 0 | 0 |
| 4 | 2 | 4 | 2 |
| 6 | 4 | 7 | 4 |
| 8 | 6 | 10 | 6 |
| 10 | **8** | **14** | **8** |

**Resultado:** la misma observación S0 es compatible exactamente con mecanismos cuya localización nominal de la restricción es diferente; añadir la misma capacidad a preparación eleva entregas de A de 8 a 14 y **no cambia** las de B (8). Diferencia terminal **6 pedidos**. No es pronóstico validado, ni constatación de que una cafetería real pueda agregar capacidad: es un **contraejemplo físico constructivo** al diagnóstico único desde salidas acumuladas.

Los estados internos simulados de ambos mecanismos son distintos, pero esos estados son **privados de la hipótesis del evaluador** y no están en O0. Eso es precisamente lo que hace posible la no-identificabilidad desde POS. O1 no ha sido usado para verificar ninguno de los dos mecanismos.

## Frontera con D/B/M y minería P

- Estas dos **configuraciones auxiliares DES** representan mecanismos rivales para diseñar el problema; no se hacen pasar por inferencia nativa D, Buffalo ni Moléculas, ni como conocimiento observado por esos brazos.
- O0 jamás revela cuántas estaciones físicas hay. Los nombres de las tres etapas son parte de la hipótesis del **evaluador**, no información identificada desde POS.
- O1 contiene un agregado censurado de preparación, **no** un seguimiento completo por caso. Ninguna de las dos hipótesis se declaró compatible con O1 ni se construyó `H_j` para convertir ese agregado en prueba de identificación.
- El [PR #147](https://github.com/yudocyudoc/IGC/pull/147) ya comprobó que el DFG original de PM4Py sobre **FULL** sigue una ruta única y no añade variantes frente a B1 para EV-01. Este testigo tampoco introduce artificialmente retrabajo o una ruta alternativa para «hacer ganar a PM».
- Para atribuir una ganancia a P harían falta **rutas/recursos observados** realmente variables, un requisito estructural reproducible no recuperable de B1/B2, ablaciones **sin/con P** dentro de cada D/B/M con la misma información, y evaluación independiente cuando P se eligió con resultados previos. Ninguno de esos supuestos se da por realizado aquí.

## Ejecución

```bash
python -m scripts.arena_cafe.f4_rival_bottleneck_witness \
  --o0 artifacts/public/O0_VISIBLE.json \
  --out artifacts/F4_RIVAL_BOTTLENECKS_DEVELOPMENT.json
```

La CI `arena-cafe-f4-rivals.yml` descarga el **O0 público congelado** y comprueba las ecuaciones originales del DES, balances exactos, dos salidas S0 idénticas, **la misma intervención** y un resultado contrafactual distinto, además de corrupciones de observaciones y cortes. El reporte con ambas hipótesis queda etiquetado públicamente como **testigo de desarrollo**.

## Estado y próximo paso

**A3 = PARTIAL**, hasta ejecución auténtica de Buffalo EV-01 y demás condiciones de integración; **G4 = NOT_RUN, G5 = NOT_RUN**. La pregunta de identificabilidad queda demostrada **solo para dos mecanismos diseñados bajo O0 conocido**. No se ha certificado una pareja rival sobre nueva evidencia ni se ha probado que PM mejore el diagnóstico.

La próxima decisión debe ser científica: si este tipo de ambigüedad es suficientemente relevante, formular **un único protocolo prospectivo de F5** con instrumento, acción, variabilidad, error y mundos/semillas independientes; no abrirlo ni revelar resultados hasta haber establecido qué D/B/M puede consumir. La vía PM continúa condicionada a evidencia adicional sobre el proceso, no a un diagrama descriptivo de la ruta única.
