# Arena EV-03 — Contrato mínimo para recibir una muestra REAL autorizada (no implementa acceso a proveedores)

**Estado:** plantilla de preparación. **NO es una aprobación de uso, no es una constancia de consentimiento, no certifica relojes ni prueba que haya tiempos físicos observados.** No subir/exportar información empresarial sin autorización, bases legales y minimización apropiada.

EV-01 demostró que diferentes vistas de una operación llevan a distintas conclusiones; EV-02 implementó calidad y mapeo de CSV administrativo; EV-03 valida que se puede leer un XES operacional externo. Para una PYME, el próximo paso no debe ser un selector de mecanismos sino un **diccionario verificable de eventos**.

## Evidencia necesaria antes de autorizar una importación

| Elemento | Pregunta concreta | Salida si no existe |
|---|---|---|
| Autorización y finalidad | ¿Quién autoriza analizar los registros, para qué y con qué alcance? | `BLOCKED_USE_AUTHORIZATION` |
| Retención y borrado | ¿Quién conserva el archivo y por cuánto tiempo? | `BLOCKED_RETENTION_POLICY` |
| Entidad / case ID | ¿Qué representa cada ID y qué relación real tiene con POS/KDS o CRM? | `NO_CROSS_SOURCE_LINK` |
| Diccionario de eventos | ¿La marca indica click administrativo, estado de sistema o trabajo físico? | `ADMINISTRATIVE_ONLY` |
| Fuente del timestamp | ¿Reloj del servidor, terminal, dispositivo o hora ingresada manualmente? | `CLOCK_UNVERIFIED` |
| Exactitud y sincronía | ¿Se ha comprobado resolución, zona y desfase entre fuentes? | `NO_CROSS_SOURCE_TIMING` |
| Protección de datos | ¿Qué campos se excluyen, seudonimizan o agregan antes del análisis? | `BLOCKED_PII_MINIMIZATION` |
| Contraste de significado físico | Si se afirma «inicio de servicio», ¿cómo se comprobó que esa acción corresponde al instante físico? | `NO_PHYSICAL_SERVICE_CLAIM` |

## Ejemplo de manifest del origen (NO es un expediente de autorización)

```json
{
  "source_authorization_and_purpose": "PENDIENTE: identificación de responsable, finalidad y condiciones",
  "retention_and_deletion_policy": "PENDIENTE: custodia, retención y eliminación",
  "event_semantics_dictionary": "PENDIENTE: acción a acción, significado observado y retrasos",
  "case_identity_linkage_provenance": "PENDIENTE: tipo de entidad, llave y validez de enlaces entre fuentes",
  "timestamp_zone_resolution_and_clock_status": "PENDIENTE: zona, exactitud, sincronía y fuente de reloj",
  "personal_data_minimization_plan": "PENDIENTE: campos eliminados antes de procesar",
  "physical_event_mapping_validation": "PENDIENTE: muestra de auditoría de clicks contra inicio/fin real"
}
```

**Advertencia:** escribir texto en estos campos solo los convierte en `DOCUMENTED_UNVERIFIED` en el código, jamás en evidencia verificada independientemente. El gate físico permanece bloqueado hasta que se aporten y auditen las pruebas requeridas.

## Regla de transferencia a otros negocios

- **Cafetería:** pedido y comanda pueden ser objetos diferentes; no suponer servicio a partir de pago o marcar comanda lista.
- **Restaurante:** los relojes POS/KDS y la sincronización de platos introducen relaciones de múltiples objetos; no imponer un único caso lineal.
- **Funnel:** lead, contacto, oportunidad, empresa y sesión no son intercambiables; un «demo_booked» es hito del CRM, no servicio efectivo, y las oportunidades pueden reabrirse.

La arquitectura es *evidence-first* y puede alimentar posteriormente las descripciones de stocks y flujos de la Arena. No conecta todavía D/B/M, ATMS ni modelos de inferencia estocástica. No se promoverán recomendaciones de operación sobre solo registros administrativos.
