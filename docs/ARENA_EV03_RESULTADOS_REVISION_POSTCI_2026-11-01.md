# ARENA EV-03 — Registro POST-CI de dos compuertas: parser aprobado / fuente oficial inaccesible

**Fecha:** 2026-11-01 (México), posterior al primer intento de CI. Este documento **NO cambia** el protocolo anterior al código (`70707877e0a010270833600f972594447a5f914c`). PR #133 Draft, apilado sobre EV-02 #132, sin merge.

## Resultado realmente observado

- [GitHub Actions run #41358486607](https://github.com/yudocyudoc/IGC/actions/runs/41358486607), head de fuente `3d8352c3656e9104944d138a2dc3cd4ada28e451`.
- Job **`stream-parser-and-readiness-tests` PASS: 10/10 pruebas unitarias** con XES sintéticos/adversariales, formato gzip y plain, timestamps ISO aware y naive, XML con DTD/XXE, límites de bytes, no exposición de identificadores, resumen de evidencia y manifiesto SHA256. Es exclusivamente validación del parser.
- Job **`public-bpi12-real-data-audit` FAIL por INDISPONIBILIDAD DE FUENTE (cURL 28)**. Descarga de URL oficial precomprometida `https://data.4tu.nl/file/533f66a4-8911-4ac7-8612-1235d65d1f37/3276db7f-8bee-4f2b-88ee-92dbffb5a893`: tres intentos de conexión HTTPS (20s cada uno), todos `Failed to connect to data.4tu.nl port 443 ... Timeout was reached`.
- Por ello **NO se leyó ningún evento real externo, NO hay conteos reales de eventos/casos, NO se obtuvo SHA256 del archivo público y NO se generó el paquete de auditoría real**. No es una falla del parseo de datos reales, sino un bloqueo de descarga, y no puede contarse como prueba externa aprobada.
- No activar fallback a espejo de GitHub como si fuera la misma fuente oficial: el protocolo explícitamente lo prohibió para este ensayo. Un espejo requeriría una evaluación distinta, procedencia explícita y cotejo de integridad con fuente original si se pretende equivalencia de contenido.
- Se agregó [contrato para muestra real autorizada](ARENA_EV03_CONTRATO_MUESTRA_REAL_AUTORIZADA.md), sin aportación de derechos o semántica instrumentada.

## Avance real disponible para uso local

La interfaz CLI del auditor está implementada y permite analizar **un XES/XES.gz obtenido por medios autorizados** sin descarga de red desde el código. No almacena filas individuales, recursos, activity labels, casos ni importes en los artefactos.

Ejemplo local, después de obtener un archivo autorizado y revisar permisos:

```bash
python -m pip install 'defusedxml==0.7.1'
PYTHONPATH=.:experiments/cafeteria/pc02 python \
  experiments/cafeteria/pc02/arena_ev03_public_log_probe.py \
  --out artifacts/ev03-local-audit \
  --input-xes /ruta/autorizada/BPI_Challenge_2012.xes.gz \
  --source-kind PUBLIC_REAL_BPI12 \
  --source-url https://data.4tu.nl/file/533f66a4-8911-4ac7-8612-1235d65d1f37/3276db7f-8bee-4f2b-88ee-92dbffb5a893 \
  --checkout-sha COMMIT_HEX_REAL_40_CHARACTERS \
  --head-sha COMMIT_HEX_REAL_40_CHARACTERS
```

El comando anterior requiere reemplazar rutas y SHAs reales. El origen URL es declaración de procedencia: **no comprueba criptográficamente que un archivo proporcionado manualmente proceda de 4TU**. Cualquier intento de usar archivos empresariales privados exige revisar el contrato y no emplear el perfil BPI12 como si fuera un perfil POS/KDS/CRM real.

## Estado epistemológico

- Ingeniería de **ingestión XES segura: implementada, probada en fixtures sintéticos**.
- Compatibilidad con datos públicos reales: **NO EJECUTADA POR TIMEOUT DE FUENTE**.
- Integración con registros reales de cafetería, restaurante o CRM: **NO DISPONIBLE (sin exportación autorizada y diccionario operativo)**.
- Estimación de colas/servicio, inferencia de etapa oculta y validación externa: **BLOQUEADAS**.

**Gate:** `BLOCKED_REAL_BUSINESS_INSTRUMENTATION_AND_PHYSICAL_SEMANTICS_NOT_VALIDATED`. Mantener Draft, sin merge.
