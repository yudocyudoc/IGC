# CAF-01 — Construcción exclusivamente en GitHub Actions

**Estado: PR pendiente de revisión de Astra tras corrección local de sus hallazgos.** CI de PR utiliza solo configuraciones inventadas. La ejecución anterior en ChatGPT **sí ocurrió y consumió una invocación real de construcción**. Su origen no es GitHub, por lo que no es la evidencia oficial reproducible pedida por el investigador, pero no se elimina ni se considera un ensayo inexistente. Una futura ejecución GitHub será una **reproducción de esa construcción**, no la primera invocación física.

## Workflow manual y seguro

Archivo: .github/workflows/caf01-construction.yml; evento único workflow_dispatch, **con comprobación explícita de** `github.ref == 'refs/heads/main'` **en el workflow y** `GITHUB_REF=refs/heads/main` **en Python**. El investigador debe escribir exactamente RUN_ONE_CAF01_CONSTRUCTION. El workflow solo admite run_number=1 y run_attempt=1; cualquier fallo o segundo intento exige revisión explícita, nunca un reintento silencioso. La elección de otra rama en GitHub Actions no puede sobrepasar esta frontera.

Se requiere un environment de GitHub Actions llamado caf01-construction y un secreto del environment CAF01_PRIVATE_ENVELOPE_B64. El valor es base64 del archivo private-envelope.json del ZIP privado del investigador, NO base64 del ZIP. La configuración, el nonce y los tiempos privados no se suben al repositorio ni se imprimen.

El recibo público fue versionado en receipts/CAF01_G5_PRECOMMIT_PUBLIC_2026-10-29.json y debe coincidir EXACTAMENTE con SHA-256 df8c7056e18dffc83b0a4cad1403970778813e80585bca84236107a37de7ac93. Antes de correr el DES, el código comprueba ese recibo, las cinco huellas de los fuentes G3/G4/G5/DES/contrato, nonce, precompromiso, preflight y presupuesto original. La recepción por correo fue informada por el investigador, no autenticada criptográficamente por el workflow.

Solo se llama una vez al motor DES en el intento GitHub con el pulso de construcción 1.2 pedidos/min durante 20 min (24 llegadas) y horizonte 40 min. **El consumo comienza cuando se invoca el motor, incluso si éste falla, falla una validación posterior o no se puede publicar el artefacto.** Los logs escriben `CAF01_DES_CONSTRUCTION_INVOCATION_STARTED=1` **antes** de iniciar esa llamada, sin datos privados; no se reintenta de forma automática. **No hay opción de generar ni revelar la evaluación.** El programa comprueba balances de stocks materiales privados, no publica esos stocks, y escribe únicamente observaciones agregadas D/A/P, vista D para D/B/M, CAF-N enmascarado, auditoría, referencias de G4 y un manifest con hashes y GitHub SHA/run ID.

Publicación exclusiva a un artefacto GitHub Actions con retención 90 días. Astra podrá cotejar el enlace del run, commit, logs y JSON publicados. El nombre heredado run_toy_engine se reutiliza como motor de eventos para el mundo real solo bajo este wrapper verificado; tests automáticos usan otros parámetros ficticios.

## Historial previo y presupuesto real (dictamen Astra)

- La construcción realizada previamente en el entorno local de ChatGPT consta en el expediente de la campaña con **1 invocación** el 29 de octubre de 2026. El registro local señala el mismo sobre privado y compromiso `sha256:26ca23076a44410bcafc4a7a944a5d5f6c6528dd59c96e7459e43c93a68812ad`, el motor fijado en `8ea6b1a`, 24 aceptaciones, sin datos de evaluación. **No se han identificado cambios de parámetros posteriores** en el expediente revisado; esto no certifica exhaustivamente que no existan copias o accesos fuera del expediente.
- El precompromiso local fue generado antes de esa ejecución; la custodia independiente fue **declarada mediante correo por el investigador**, pero no tenemos en el repositorio un recibo de testigo con fecha verificada criptográficamente. La fuente local no prueba por sí sola la hora de entrega efectiva de ese correo.
- El expediente correcto para el secreto GitHub es `CAF01_SECRETO_G5_CONFIG_NONCE_2026-10-29.zip`: **sí incluye** `private-envelope.json`, con el nonce correcto y el vínculo al recibo público. **No usar** `CAF01_propuesta_unica_PRIVADA_NO_SELLADA_2026-10-29.zip`, que carece de sobre. Ningún sobre ni nonce se incorporará a GitHub.
- Si se autoriza una reproducción en Actions, el total conocido será **2 invocaciones DES de construcción**: local=1, GitHub=1. El protocolo PC-01 v0.3 originalmente permitía **1** construcción. Esta desviación **debe quedar explícita** en `08_manifest.json` y el informe científico; no fingir que el contador del contrato en cero representa el historial real. **No implica autorizar una evaluación adicional**, cuyo presupuesto sigue sin consumirse.
- Los resultados agregados de construcción publicados previamente en ChatGPT ya son conocimiento de ese contexto. No pueden borrarse con un rótulo de «exploración»; el trabajo posterior de Buffalo debe usar un contexto aislado, sin ese historial ni las bandas privadas.

## Pasos de activación en GitHub

1. GitHub yudocyudoc/IGC → Settings → Environments → crear caf01-construction. Configurar required reviewers cuando sea posible. Nunca usar variables normales de Actions para secretos.
2. Extraer private-envelope.json del ZIP confidencial, en una carpeta protegida fuera del checkout. En PowerShell, copiar la codificación al portapapeles:

       [Convert]::ToBase64String([IO.File]::ReadAllBytes('C:\RUTA-PRIVADA\private-envelope.json')) | Set-Clipboard

   En GitHub Environment → Environment secrets → New environment secret: nombre CAF01_PRIVATE_ENVELOPE_B64 y pegar directamente el portapapeles. Borrarlo después. No compartir esta cadena con Astra ni en el chat.
3. Una vez aprobado por Astra y fusionado el PR, GitHub Actions → CAF-01 — one authorized construction world → Run workflow → main → escribir RUN_ONE_CAF01_CONSTRUCTION. Es la **única** construcción planificada.
4. Entregar a Astra el URL del run y el artefacto caf01-construction-public-run-ID. El revisor podrá verificar commit, SHA, conservación y regresiones de G4 sin conocer configuración secreta.
5. **No ejecutar evaluación** hasta bloqueo independiente de G3/G4 y autorización específica. No incorporar a los modelos las bandas privadas, los estados de etapas ni los tiempos del mundo.

## Regla de evidencia

Para el análisis D/B/M y revisión independiente, el investigador ha elegido que **solo la reproducción documentada en GitHub** sea la fuente oficial del paquete público. La construcción anterior no se elimina de la bitácora ni se ignora en el recuento del DES: debe reportarse como antecedente y riesgo de contaminación informacional, especialmente porque sus resultados agregados ya se mostraron en el chat.

**El PR, su CI o la mera presencia del workflow no cuentan como corrida real.** La futura corrida GitHub queda consumida desde el instante de la llamada a `run_toy_engine`, incluso si el job fracasa y no genera artefactos. En caso de fallo, no ejecutar de nuevo sin revisión explícita de Astra y del presupuesto.
