# R1 Buffalo — primera propuesta nativa sobre evidencia común

**Base:** IGC/main@211940ed0fb8f9ed187f6e2e54f72cdcdebb0948 (D/M físicos, PR #53).

Este experimento genera UNA propuesta inicial nueva del motor original UB-IAD/sd-ai@5199f7b45f3a7ae4a773cb0dd8542940aabe9edc sobre la fuente de construcción primaria compartida. Ni estructuras D/M, ni sus errores, ni B2-B5 históricos, ni mundos de evaluación o reserva se envían al productor.

La preparación en scripts/arena_r1_buffalo_initial.py se deriva del contrato de evidencia común, incluyendo exactamente las cuatro observaciones y el pulso público. Solo añade condiciones NUMÉRICAS explícitas del ensayo: simulación nativa con Euler, dt=.125 h, horizonte 0..8h. No prescribe ecuaciones, stocks, capacidades ni colas. Estos parámetros de solver constituyen un contrato técnico; no son evidencia física independiente.

## Presupuesto y autorización

Un marcador JSON nuevo valida que el usuario autorizó **una sola llamada** Cloudflare Workers AI @cf/zai-org/glm-5.3-flash, máximo 7000 tokens de salida, sin reintentos automáticos. La preparación offline y la descarga del upstream no gastan tokens. El workflow necesita push inicial del archivo marcador, intento 1; cambios posteriores o reejecuciones no pueden lanzar otra llamada. El proveedor requiere credenciales de GitHub Actions ya configuradas.

Tarifa de referencia publicada en Cloudflare para GLM-5.3 Flash (consultada octubre de 2026): USD 0.15/1M tokens de entrada y USD 0.50/1M tokens de salida. El costo efectivo se estima desde usage cuando el proveedor lo devuelve; no se presume un techo monetario contractual independiente del conteo real de tokens de entrada. Los 7000 tokens de salida equivaldrían a USD 0.0035 antes de sumar entrada.

## Revisión física y epistemología

La salida cruda se archiva antes de traducción. scripts/arena_r1_buffalo_finish.py intenta G0 mediante el traductor B estricto que ya existía: un subtipo o especificación ajena al alcance declarado produce un bloqueo tipado, nunca una corrección silenciosa. Solo si G0 admite las ecuaciones, se ejecuta OpenModelica real con Euler y se verifican conservación y errores G3 DESCRIPTIVOS de construcción. No se confunde G3 con validación predictiva externa.

Al cierre el workflow recupera el resultado D/M PR #53 **después** de la llamada B y compone un registro tripartito con 6 estructuras D, 3 M3 y el resultado original B. Si B produce una respuesta no ejecutable, se conserva B como fallo físico o de traducción y la ronda no se declara físicamente completa.

No hay ganador científico, calibración común, holdout nuevo, segunda revisión R2, ATMS conjunto ni referencia REF. Cualquier nuevo uso del proveedor requiere una nueva autorización por separado.
