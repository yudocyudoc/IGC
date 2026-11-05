# Arena IGC — Café · Evidencia de video del barista v0.1

**Corte:** 2026-11-04 · **Estado:** observacional, exploratorio y no validado independientemente.

**Fuente:** un MP4 de ~5024.87 segundos (640×360; 30 fps nominales), identificado por SHA-256 `cd37c9d3f231f4d307c4f3353ce1dc096fad4185bbdf6ffab06266b9d41290c5`. Ni continuidad del video ni equivalencia entre segundos de archivo y segundos físicos de tienda están certificadas.

### Qué incluye

- `pedidos/`: 52 tandas observadas en panel ORDER, 84 líneas y 105 unidades escritas (incluyen postres), lectura visual y revisión de límites.
- `barista/`: 200 hitos, 25 operaciones **seleccionadas**, 52 registros temporales por tanda, anotaciones de revisión y mediciones derivadas.
- `revisiones/`: segunda lectura de episodios P004/P006/P045; muestras cualitativas del tramo P045 (R3) y del tramo P031 (R4). No son evaluaciones ciegas independientes.
- `contrato/`: 23 códigos propuestos y JSON Schema 2020-12 para anotaciones nuevas. Los CSV originales **no** siguen este esquema v0.1 sin un adaptador.
- `docs/arena_cafe/video_barista_v0_1/`: tres informes y definición metodológica del vocabulario.

### Fronteras de evidencia y privacidad

Este repositorio es **público**. Por esa razón se excluyen el MP4, los fotogramas, el audio, las rutas locales de la máquina y el enlace a la carpeta privada de Drive. Los campos `evidence` y `source_path` son referencias relativas a archivos preservados **fuera de GitHub**, no rutas que resuelvan dentro de este repositorio.

No confundir:
- **Panel mostrado** con venta POS, llegada física o un pedido independiente.
- **Salida del campo visual** con entrega al cliente.
- **Jarra junto a lanza** con vapor activo confirmado.
- **Último vertido** con montaje íntegro y accesorios terminados.
- **Fotogramas separados** con actividad continua, inactividad o utilización real.
- **Conteo mínimo de recipientes** con capacidad máxima, inventario o productividad.

P001 presenta censura por izquierda; seis tandas carecen de final de montaje identificado; P010/P036 mantienen ambigüedad de identidad POS. Las operaciones seleccionadas no cubren exhaustivamente la jornada.

### Integración futura

**D/B/M permanecen sin cambios; F5, G4 y G5 no se ejecutan ni autorizan con este material.** Se necesita verificación de reloj/cortes, anotación independiente, traza de objetos, definición de fronteras físicas, cobertura de recursos y adaptador observacional explícito antes de inferir stocks, flujos o parámetros del simulador.

**Alcance de este primer PR:** conservar JSON/CSV originales y capas R2/R3/R4, más vocabulario/documentación. Los siete ejemplos JSONL y el validador local del paquete de vocabulario quedan pendientes de incorporar; el esquema JSON ya se publica.
