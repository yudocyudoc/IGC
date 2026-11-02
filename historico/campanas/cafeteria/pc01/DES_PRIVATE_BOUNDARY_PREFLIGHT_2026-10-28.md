# CAF-01 · DES-01 — Instrumento de eventos, aún sin mundo privado

**Estado: PREPARACIÓN PARA REVISIÓN DE ASTRA.** No hay configuración de verdad, ni corrida de construcción, ni corrida de evaluación. No congelar CAF-01 ni autorizar PC-02 por este cambio.

## Base proveniente del contrato PC-01 v0.3

El contrato fija una clase de pedido aceptado hasta entrega, sin cancelaciones ni pérdidas, cero estados iniciales, un pulso abierto por la derecha `t<20 min`, 24 aceptaciones de construcción (1.2 pedidos/min) y 30 de evaluación (1.5), horizonte 40 min y lecturas a 0,5,10,15,20,30,40. La llegada j está propuesta como `(j+1/2)/λ` y no hay ruido. El contrato **no fija** número de etapas, número de servidores, tiempos de servicio ni desempate de eventos simultáneos. Estas son decisiones nuevas y propuestas, **no afirmaciones de que ya estuvieran aprobadas**.

## Implementación preparatoria

`caf01_des_engine.py` usa exclusivamente el calendario propio de Python, `Fraction`, `heapq` y colas FIFO. No importa D, M/E1, Modelica, Buffalo ni sus catálogos. **No** contiene un CLI para producir un mundo real CAF-01: se usa únicamente en pruebas pequeñas, inventadas expresamente, que no emplean la configuración ni las respuestas privadas.

La configuración del mecanismo se suministrará separadamente, **fuera de GitHub**, cuando el investigador decida y selle el modelo. El esquema actualmente validable es una cantidad de etapas de 1 a 6, cada una con `servers` entero positivo (máximo 20) y `service_minutes` racional estrictamente positivo. Una cola FIFO puede acumular pedidos sin límite explícito; la **capacidad de atención por etapa está limitada físicamente por el número de servidores**, pero **no se ha modelado aforo ni capacidad máxima de espera**. No inventar restricciones de inventario, insumos o contratación: quedan fuera de la frontera de un pedido equivalente.

La semántica propuesta, todavía sujeta al dictamen de Astra, es:

1. A un mismo instante exacto: terminar todos los servicios programados; transferir pedidos completados a la siguiente cola o contarlos como entregados.
2. Después aceptar todas las llegadas programadas de ese instante.
3. Finalmente iniciar servicio en las plazas libres, comenzando por las etapas aguas abajo. El inicio de servicio programa una terminación estrictamente posterior (`service_minutes>0`), evitando iteraciones de tiempo cero. Cada cola es FIFO; la orden de inserción en empates viene de la secuencia de eventos estable.
4. Las lecturas incluyen todos los eventos con marca temporal `≤t` (lectura *después* del lote simultáneo). Llegadas en el instante final del pulso `t=20` se excluyen; terminaciones en t=20 sí se cuentan. La integración es en **minutos racionales exactos**, sin redondeo de reloj.

La fuente es independiente en código de los productores, **pero no conceptualmente**: comparte material conservado y procesos de servicio/colas. No proclamar recuperación de estructura a partir de su ejecución.

## Invariantes verificables

En cada transición: `A=D+Σ(waiting_i+in_service_i)`; las plazas ocupadas por etapa `≤servers_i`; cada pedido ocupa una sola localización material; ninguna entrega se repite; contadores no negativos; `P=A−D` es **derivado**, mientras el conteo de estados materiales se obtiene **separadamente** para verificar conservación. Si uno falla, el motor bloquea el resultado. El diagnóstico interno contiene los estados de etapas privadas: no publicarlo junto con las entradas de D/B/M/REF.

Las pruebas actuales usan únicamente ejemplos de una y dos etapas inventados, con pocos eventos. Verifican cuenta de calendarios públicos (24/30), semántica de desempate, eventos exactamente en tiempos de lectura, límite de servidores, balance material, reinicio implícito por ejecución sin estado compartido y errores por configuración incompatible. **Ninguna** prueba construye un mundo con los parámetros reales del generador CAF-01.

## Diseño de sellado y controles antes de ejecutar el caso real

- El investigador debe escoger fuera del repositorio la configuración de etapas, servidores, tiempos y regla de empates; registrar su justificación sin ver resultados de los brazos. **Este PR no escoge esa verdad**.
- Para demostrar precompromiso se proporciona `private_commitment(config, nonce)`. El `nonce` debe ser aleatorio y secreto de al menos 32 bytes. Publicar en el expediente solo un compromiso con hash y el hash de la versión del motor/código; custodiar configuración y nonce fuera de GitHub. No publicar el hash sin sal de un conjunto de parámetros de baja entropía: es adivinable por enumeración.
- El investigador/Astra debe aprobar la política de empates, la fuente, los límites y el esquema de reporte. Solo entonces emitir un protocolo congelado y obtener **autorización separada** para la corrida de construcción; el sello de evaluación debe impedir su lectura antes del bloqueo de los pronósticos.
- El futuro runner autorizado deberá comprobar hash/código/configuración, disponer de dos reinicios independientes, controlar presupuesto 1 DES construcción + 1 DES evaluación, devolver un paquete público de construcción con `{t_min,accepted_cum_orders,delivered_cum_orders,pending_orders}`, producir una vista mínima `{t,delivered}` para todos los brazos, y conservar el diagnóstico físico completo fuera de esas vistas. Ninguna de esas salidas está generada aquí.
- Si falla cualquier compuerta de integridad, bloquear la corrida; no ajustar la verdad para dar mejor RMSE, no sustituir resultados y no hacer reintentos automáticos.

**Pendientes:** dictamen Astra sobre orden de eventos y alcance, cierre G3, ruta de sellado/custodia privada y runner futuro controlado. Este trabajo no justifica por sí solo fusionar los PR #72, #74 o #75.
