# Arena · Captura auditada de inferencia S/P (V0.3)

**Fecha:** 2026-10-24. **Repositorio:** yudocyudoc/IGC, PR #16. **Naturaleza:** componente ejecutable, no experimento empírico ciego.

## 1. Qué se añadió

- scripts/arena_sp_capture.py: ejecución de las 3 peticiones ya definidas (GLM, Clef, Clairic) con autorización específica, sin retries. Antes de llamar crea un directorio exclusivo. Una corrida parcial queda bloqueada para repetición en la misma ruta; se conserva un registro por petición aceptada.
- scripts/arena_sp_producers.py: gancho de duración y respuesta cruda validada por petición. Ningún token secreto se imprime ni se copia en los artefactos.
- scripts/arena_sp_verify_capture.py: verifica offline cada llamada, sus hashes, sus respuestas, el recibo final y la normalización del draft; **no vuelve a llamar a Cloudflare**.
- scripts/arena_sp_handoff.py: la procedencia declarada como real exige recibo íntegro y respuestas crudas concordantes antes de admisión ATMS. No basta con un diccionario que declare hashes.
- P solo puede convertirse en una entrega tipada SUBMITTED si el consumo de tokens de Clef y Clairic es observable. Si no lo reportan, emite error P_TOKEN_USAGE_NOT_OBSERVABLE; no se inventan ceros. El uso de `neurons` se registra separado: no se convierte a tokens ni a dinero.
- Pruebas adversativas con transporte falso: tres llamadas máximas, 0 antes de autorizar, rechazo de replay local, parciales sin marca COMPLETE, uso ausente, integridad de respuestas y falsificación de recibos.

## 2. Protocolo para una campaña real, no ejecutada en este PR

La construcción de las solicitudes sigue el flujo ya probado en short (EPI-04/EPI-06). La Arena debe usar un `package.json` generado por la preparación S/P y su `catalog.json` congelado. El operador con credenciales de inferencia existentes ejecuta **una vez**:

```bash
python -m scripts.arena_sp_capture \
  --package /ruta/privada/package.json \
  --catalog data/synthetic/arena_sp_public_catalog.json \
  --out-dir /ruta/privada/arena-sp-run-001 \
  --run-ref github-actions:RUN_ID \
  --authorization RUN_ARENA_SP_MAX3
```

Requiere `CLOUDFLARE_ACCOUNT_ID` y `CLOUDFLARE_API_TOKEN` como variables de entorno fuera de Git. Las llamadas pueden generar consumo de Cloudflare. El paquete no debe contener gold, reserva ni respuestas de otra vía.

Para verificar localmente el archivo generado, sin llamadas adicionales:

```bash
python -m scripts.arena_sp_verify_capture \
  --package /ruta/privada/package.json \
  --catalog data/synthetic/arena_sp_public_catalog.json \
  --archive /ruta/privada/arena-sp-run-001
```

El verificador devuelve `ARCHIVE_CONSISTENT_NOT_INDEPENDENTLY_ATTESTED` cuando se comprueba la consistencia completa. Esto **no certifica** que un tercero haya observado la ejecución: los hashes y el run_ref pueden ser construidos localmente. Para acreditar origen real y timing de ejecución en Arena se requiere ejecución controlada por CI y, para ceguera, custodio distinto.

## 3. Costos y procedencia

- Cada registro conserva nombre del modelo, hash de respuesta, duración observada y todos los contadores numéricos comunicados por el proveedor.
- El total de tokens se calcula solo si existen contadores reportados para **todos** los modelos. De otro modo se marca `PARTIAL_OR_UNAVAILABLE`, `tokens=null`.
- No se calcula precio monetario a partir de modelos o estimaciones no confirmadas; se marca `PROVIDER_CURRENCY_NOT_VERIFIED`.
- Las respuestas originales permanecen en el archivo privado del operador, no se deben publicar indiscriminadamente en el repositorio.
- Si falla la segunda llamada, quedan registros de la primera y NO hay `completed.json`. Debe investigarse el fallo antes de crear una **nueva campaña preregistrada**; no volver a llamar a ciegas.
- Para construir LaneSubmission de S todavía faltan simulación a partir de propuesta verdaderamente recibida, parámetros ligados a construcción y gates completos. Una propuesta MOCK no es evaluable.

## 4. Criterio de salida

Este incremento se considera técnicamente probado cuando su suite de capturador, verificador y entrega S/P da PASS en Actions, y las regresiones de memoria ATMS / Modelica permanecen verdes.

**No se autoriza por el mero hecho de incluir el comando** una campaña facturable, una evaluación con reserva ni el despliegue de una nueva infraestructura. El componente queda listo para ejecutarse bajo autorización operacional explícita.
