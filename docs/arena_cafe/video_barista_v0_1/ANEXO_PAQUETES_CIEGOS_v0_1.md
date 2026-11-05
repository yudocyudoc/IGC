# Arena Café · Anexo de extracción ciega v0.1

**Estado 2026-11-04:** preparación ejecutada, **doble codificación NO ejecutada**. Complementa [PROTOCOLO_DOBLE_ANOTACION_v0_1.md](PROTOCOLO_DOBLE_ANOTACION_v0_1.md). No modifica las dos ventanas preregistradas ni los 23 códigos del contrato.

## Paquetes

Se generaron dos paquetes separados e idénticos en evidencia, cada uno con dos MP4 **sin audio**, 122 fotogramas (61 por ventana, cada 2 segundos, con extremos) y hojas vacías \`cobertura.csv\`, \`eventos.jsonl\` y \`resumen_revisor.json\`. **No se suben los MP4 ni los JPEG a este repositorio público.** Los codificadores no reciben anotaciones previas de Pxxx ni respuestas del otro revisor.

Fuente: SHA256 \`cd37c9d3f231f4d307c4f3353ce1dc096fad4185bbdf6ffab06266b9d41290c5\`.

El panel ORDER fue cubierto por un rectángulo negro en x=383..639, y=0..80. En el tramo A se ocultó el recuadro secundario en x=465..639, y=175..359 **solo durante los 26 segundos iniciales**, no en el resto del video, para preservar el lado derecho de la barra. En el tramo B no se detectó ese inserto en la revisión administrativa de muestra y no se colocó máscara inferior. La propia máscara oculta información física del encuadre y nunca debe interpretarse como superficie vacía. Ambos codificadores reciben exactamente las mismas transformaciones.

La duración codificada tiene unos fotogramas de margen alrededor del segundo 120 para asegurar la muestra final; el análisis y las anotaciones están restringidos a los segundos **[2350,2470]** y **[3750,3870]**, inclusive. No se añade audio. El reloj físico de tienda sigue sin verificar.

## Reproducibilidad

Con FFmpeg instalado y acceso **local privado** al MP4:

\`\`\`bash
python scripts/arena_cafe/generar_paquete_ciego_v0_1.py \
  --source /ruta/privada/videoplayback.mp4 \
  --output /ruta/privada/paquete_ciego
\`\`\`

La salida crea clips, JPEG, \`MANIFIESTO.json\` y \`MANIFIESTO_MUESTRAS.csv\`. El SHA256 del archivo fuente se verifica antes de iniciar. Los clips fueron producidos con H.264 y CRF 19; bytes de salida podrían variar según versión de FFmpeg, por lo que los hashes de medios son propios de la ejecución, no un estándar universal.

El protocolo exige **dos revisores independientes y entregas cerradas** antes de calcular acuerdo. Este asistente, que ya conocía la historia del proyecto, no se presenta como revisor A o B. Ningún F1, productividad o capacidad máxima puede obtenerse de un paquete sin completar.

## Próximo control

1. Dos codificadores usan paquetes separados sin contexto histórico.
2. Cada uno entrega cobertura por muestra, JSONL, declaración de independencia y SHA256 de sus respuestas.
3. Validar contrato y calcular acuerdos, preservando desconocidos, no emparejados y discrepancias.
4. Solo después discutir adaptador observacional de límites inferiores; D/B/M y F5/G4/G5 permanecen fuera de alcance.
