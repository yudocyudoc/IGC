# CAF-01 — Construcción exclusivamente en GitHub Actions

**Estado: PR pendiente de revisión de Astra.** CI de PR utiliza solo configuraciones inventadas. La anterior ejecución en ChatGPT fue exploratoria y NO cuenta como evidencia experimental oficial.

## Workflow manual y seguro

Archivo: .github/workflows/caf01-construction.yml; evento único workflow_dispatch en main después de fusionar. El investigador debe escribir exactamente RUN_ONE_CAF01_CONSTRUCTION. El workflow solo admite run_number=1 y run_attempt=1; cualquier fallo o segundo intento exige revisión explícita, nunca un reintento silencioso.

Se requiere un environment de GitHub Actions llamado caf01-construction y un secreto del environment CAF01_PRIVATE_ENVELOPE_B64. El valor es base64 del archivo private-envelope.json del ZIP privado del investigador, NO base64 del ZIP. La configuración, el nonce y los tiempos privados no se suben al repositorio ni se imprimen.

El recibo público fue versionado en receipts/CAF01_G5_PRECOMMIT_PUBLIC_2026-10-29.json y debe coincidir EXACTAMENTE con SHA-256 df8c7056e18dffc83b0a4cad1403970778813e80585bca84236107a37de7ac93. Antes de correr el DES, el código comprueba ese recibo, las cinco huellas de los fuentes G3/G4/G5/DES/contrato, nonce, precompromiso, preflight y presupuesto original. La recepción por correo fue informada por el investigador, no autenticada criptográficamente por el workflow.

Solo se llama una vez al motor DES con el pulso de construcción 1.2 pedidos/min durante 20 min (24 llegadas) y horizonte 40 min. **No hay opción de generar ni revelar la evaluación.** El programa comprueba balances de stocks materiales privados, no publica esos stocks, y escribe únicamente observaciones agregadas D/A/P, vista D para D/B/M, CAF-N enmascarado, auditoría, referencias de G4 y un manifest con hashes y GitHub SHA/run ID.

Publicación exclusiva a un artefacto GitHub Actions con retención 90 días. Astra podrá cotejar el enlace del run, commit, logs y JSON publicados. El nombre heredado run_toy_engine se reutiliza como motor de eventos para el mundo real solo bajo este wrapper verificado; tests automáticos usan otros parámetros ficticios.

## Pasos de activación en GitHub

1. GitHub yudocyudoc/IGC → Settings → Environments → crear caf01-construction. Configurar required reviewers cuando sea posible. Nunca usar variables normales de Actions para secretos.
2. Extraer private-envelope.json del ZIP confidencial, en una carpeta protegida fuera del checkout. En PowerShell, copiar la codificación al portapapeles:

       [Convert]::ToBase64String([IO.File]::ReadAllBytes('C:\RUTA-PRIVADA\private-envelope.json')) | Set-Clipboard

   En GitHub Environment → Environment secrets → New environment secret: nombre CAF01_PRIVATE_ENVELOPE_B64 y pegar directamente el portapapeles. Borrarlo después. No compartir esta cadena con Astra ni en el chat.
3. Una vez aprobado por Astra y fusionado el PR, GitHub Actions → CAF-01 — one authorized construction world → Run workflow → main → escribir RUN_ONE_CAF01_CONSTRUCTION. Es la **única** construcción planificada.
4. Entregar a Astra el URL del run y el artefacto caf01-construction-public-run-ID. El revisor podrá verificar commit, SHA, conservación y regresiones de G4 sin conocer configuración secreta.
5. **No ejecutar evaluación** hasta bloqueo independiente de G3/G4 y autorización específica. No incorporar a los modelos las bandas privadas, los estados de etapas ni los tiempos del mundo.

## Regla de evidencia

Solo será evidencia experimental oficial la construcción emitida por el workflow manual de GitHub. El ZIP de construcción creado previamente en ChatGPT debe tratarse como exploratorio y no utilizarse para elegir parámetros, puntuar candidatos ni anticipar resultados.

**El PR, su CI o la mera presencia del workflow no cuentan como corrida real.** El DES se consume únicamente al existir un run manual exitoso con artefacto verificable. Ante un fallo, no reintentar automáticamente.
