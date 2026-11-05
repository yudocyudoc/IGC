# Auditoría visual: segunda lectura de cinco episodios, P004/P006/P045

**Estado:** pasada de reproducibilidad no ciega; observación directa sobre el MP4 original.
**SHA-256 del video:** `cd37c9d3f231f4d307c4f3353ce1dc096fad4185bbdf6ffab06266b9d41290c5`. **Fuente de contraste:** `operaciones.csv` original, sin modificar.

## Procedimiento
Se eligieron P004, P006 y P045. Se extrajeron fotogramas a intervalos de 2 s para contexto y de 1 s alrededor de cinco episodios de jarra/lanza. Se anotó el estado visible de **sujeción de jarra bajo la lanza**, no la emisión de vapor. Los límites se acotan con muestras antes/después. La segunda pasada fue del mismo asistente, que conocía parte de los intervalos previos: **NO es una auditoría independiente ni ciega**.

## Comparación con la anotación original

| Episodio | Nueva sujeción visible (inicio → fin, s de video) | Duración compatible (s) | Inicio previo | Fin previo | ¿Límites coinciden? |
|---|---|---:|---|---|---|
| P004-steam-01 | [527,528] → [541,542] | 13–15 | [526,530] | [540,542] | Inicio: sí; fin: sí |
| P006-steam-02 | [661,663] → [677,679] | 14–18 | [660,662] | [674,676] | Inicio: sí; fin: no |
| P006-steam-03 | [739,741] → [754,756] | 13–17 | [738,740] | [752,754] | Inicio: sí; fin: sí |
| P045-steam-09 | [4068,4070] → [4084,4086] | 14–18 | [4066,4068] | [4082,4086] | Inicio: sí; fin: sí |
| P045-steam-10 | [4112,4114] → [4126,4128] | 12–16 | [4110,4112] | [4124,4128] | Inicio: sí; fin: sí |

**Balance:** los 5 intervalos nuevos de inicio se solapan con los anteriores; **4 de 5** intervalos finales se solapan (el de `P006-steam-02` no). Los cinco rangos de duración son compatibles. Esto NO equivale a 80–100 % de precisión de un detector: ambas anotaciones usan definiciones ligeramente diferentes y el mismo revisor, informado por la lectura previa.

### Divergencia explicativa en P006
En `P006-steam-02` la jarra aún está próxima a la lanza a los 677 s y se aparta hacia 678–679 s; el CSV original terminaba `vaporizado_con_sujecion` entre 674 y 676 s. Una interpretación plausible es que el cierre de válvula anteceda a retirar físicamente la jarra. La imagen sin audio ni instrumentación **no permite demostrar cuándo dejó de producirse vapor**. Por tanto, mantener dos variables distintas: `ocupacion_visual_jarra_lanza` y `vapor_activo_desconocido`.

### Estado del producto: hallazgo especialmente útil en P045
- En P045 una taza ya montada permanece visible sobre el mostrador durante las muestras de la segunda sujeción de jarra (4114–4126 s).
- Alrededor de 4144 s aparecen dos tazas montadas simultáneamente. Esto justifica un estado **producto montado en estación** sin convertirlo en `cliente_entregado`.
- P004 muestra un vaso visible en 562–570 s y ausente a 572 s. Solo permite **salida de campo**, no prueba de entrega.

## Consecuencias para Arena
**Observado:** aproximación, sujeción, retirada de jarra y coexistencia de productos montados. **Inferido con incertidumbre:** intervalos de proximidad jarra-lanza y ocupación visual de barista/estación. **Desconocido:** vapor efectivo, extracción de espresso, tiempos físicos reales, continuidad sin cortes, correspondencia exacta producto–pedido, servicio entregado.

No dividir el ciclo entre productos; no convertir los cinco episodios en estimaciones de productividad, utilización de toda la jornada o capacidad máxima. Para evaluación independiente: otra persona o modelo aislado de anotaciones originales, con definiciones operacionales y acceso al MP4, etiqueta una reserva no utilizada en el diseño.

## Entregables
- `revision2_5_episodios.csv`: límites y contraste por episodio.
- `revision2_estados_productos.csv`: estados en instantes concretos, sin asumir continuidad.
- `revision2_evidencia_6_secuencias.jpg`: mosaico de tres fotogramas por secuencia, obtenido directamente del MP4.
- `revision2_resumen.json`: integridad, diseño, consistencia y limitaciones.

**No se cambiaron los CSV de origen, Drive, GitHub ni modelos D/B/M; G4/G5 NOT_RUN.**