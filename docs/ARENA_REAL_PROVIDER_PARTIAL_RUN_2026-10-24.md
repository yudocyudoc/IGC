# Arena S/P — Primera invocación auténtica, resultado PARCIAL

**Fecha de revisión:** 2026-10-24 (zona horaria de referencia México).
**Experimento:** V0-B3-PUBLIC-REGRESSION-001.
**Condición:** Catálogo y construcción sintéticos públicos. No existe reserva ciega, gold ni resultado causal.
**Canal de invocación:** Conexión autenticada de Cloudflare desde la sesión, NO `arena_sp_capture.py` ni GitHub Actions. Por tanto NO se generó un recibo de captura completo en disco. No confundir la llamada con una ejecución del adaptador CI.

## Las tres solicitudes previstas

| Vía | Modelo | Resultado | Evidencia devuelta |
|---|---|---|---|
| S | @cf/zai-org/glm-4.7-flash | HTTP 200 | Seleccionó CS-01 y CS-02; descartó CS-03 y destacó que la serie de construcción no discrimina estructuras. Usage: prompt_tokens=368, completion_tokens=376, total_tokens=744; neurons=15.7104 |
| P | @cf/cloudflare/clef | BLOQUEADA | La herramienta rechazó la solicitud antes de ofrecer un resultado. Sin respuesta de proveedor, uso o juicio |
| P | @cf/cloudflare/clairic | HTTP 200; DESACUERDO | `observed_increment=1.663`; oráculo determinista `4-2=2.0`; `valid_arithmetic=false`. Usage: input_tokens=197, output_tokens=0; no equivalente monetario verificado |

**Estado:** `PARTIAL_REAL_PROVIDER_RESPONSES_NOT_A_CAMPAIGN_COMPLETE`.
**Presupuesto/contabilidad:** dos respuestas reales; no se atribuyen tokens ni costo de Clef. El total de tokens de tres modelos es desconocido. Ni `neurons` ni cualquier contador parcial equivalen a importe facturado comprobado.

## Implicaciones para Arena

- La elección de GLM es una **propuesta textual de estructura**, no un `LaneSubmission`, ni una selección ATMS sellada, ni una predicción.
- La respuesta de GLM estuvo contenida en un bloque Markdown `json`; se corrigió el parser de `arena_sp_producers.py` para admitir envolturas completas sin aceptar identificadores inventados o saltar el contrato.
- Clairic falló una resta elemental. El sistema debe conservar el resultado y marcar discrepancia, **sin corregir los datos o inferir un parámetro**.
- No se ejecutó el `seal_handoff` como `CLOUDFLARE_VERIFIED_RUN`, porque faltan respuesta Clef y paquete/recibo auditado de la campaña. No se ejecutó una simulación Modelica atribuible a las respuestas reales ni una evaluación con reserva.
- No volver a ejecutar Clef ni las llamadas anteriores automáticamente: cualquier repetición debe registrarse como un nuevo intento o campaña, con presupuesto y procedencia separados. La solicitud Clef quedó bloqueada por controles del conector, no tratada como fallo de respuesta del modelo.

## Próxima decisión técnica

Mantener el experimento incompleto en el ledger de la Arena y diseñar una campaña nueva con captura por llamada, soporte explícito para fallo/bloqueo de proveedor, auditoría de coste y entrega parcial admisible por vía, sin forzar artificialmente tres respuestas correctas. Las propuestas de S deberán atravesar ATMS y OpenModelica en esa nueva ronda, con cierre antes de cualquier comparación empírica.

**No declarar:** éxito del flujo completo, cierre S/P, comprobación de ceguera, costos monetarios, identificación estructural ni evidencia de validez causal.
