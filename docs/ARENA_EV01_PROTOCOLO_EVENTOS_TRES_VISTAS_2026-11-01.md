# ARENA-EV01 — Protocolo previo: una operación, tres niveles de observabilidad por eventos

**2026-11-01, America/Mexico_City. Primer commit de EV01, ANTES de código o de ejecutar el experimento.** Base `279a1fc0b21c4ed07f62efae58841a1dc4e79ef6` de PR #130 (Draft). Este PR será Draft, sin fusiones ni cambios retrospectivos a CAF-01..16, MC-01, D/B/M, ledger o ATMS.

## Motivación: no transferir certificados de una física idealizada a datos empresariales

La anterior campaña CAF empleó salidas agregadas, modelos deterministas y —hasta CAF-16— hipótesis puntuales. MC-01 corrigió la rejilla de parámetros con set-membership continuo, pero tampoco define qué información real puede observar la Arena. EV01 cambia **la unidad de análisis**: entidades, eventos, marcas temporales y procedencia. No pretende que Process Mining, teoría de colas o residuos de tiempo identifiquen por sí solos una estación latente.

**Pregunta primaria:** en UNA operación física idéntica, ¿qué atributos de espera, servicio y estructura de proceso quedan OBSERVADOS o identificables cuando solo hay POS (A), POS + KDS idealizado (B) o instrumentación por etapa (C)? ¿Qué información debe permanecer `NOT_IDENTIFIABLE_FROM_VIEW`? No se busca identificar la topología oculta desde A/B; C es un instrumento de comparación de verdad accesible SOLO al evaluador.

## Mundo único, congelado antes de código

- 15 pedidos con llegadas del motor CAF-01: `des.half_open_arrivals("5/2",6)`, pulso semia-bierto [0,6) min, 2.5 pedidos/min = 150/h; sin cancelaciones ni abandonos. Cada pedido es entidad `O000...`. Origen temporal arbitrario `2026-01-01T00:00:00Z`.
- Cuatro etapas reales SERIALES FIFO sin bloqueo (buffers ilimitados), con servicio homogéneo determinista por etapa y recursos:
  - `caja`: 2 servidores × 1 min por pedido;
  - `preparacion`: 1 servidor × 60/68 min;
  - `despacho`: 1 servidor × 60/86 min;
  - `transferencia_final`: 1 servidor × 60/220 min.
- Etapa final es un **control sintético de trabajo no registrado en POS+KDS**. No llamarla “mecanismo descubierto” cuando C la registra explícitamente. No usar cifras reales ni suponer que un POS/KDS comercial produce los mismos eventos.
- Eventos completos emitidos por motor de eventos nuevo, con `Fraction` exacta, `case_id`, `event_id`, `activity`, `t_minutes_exact`, `stage`, `resource_id`, `provenance`. Tipos: `pedido_creado`, `pago_confirmado` simultáneo, `etapa_entrada`, `servicio_inicio`, `servicio_fin`, `pedido_entregado`. El motor genera la traza completa y la verifica contra `des.run_toy_engine` en instantes `0,2,4,6,8,10,14,20,30` antes de cualquier análisis de vista. `accepted=delivered+pending`, FIFO, límites de servidores, unicidad de pedidos, cronología y cierre temporal.
- Recurso asignado según puesto libre de menor índice, sin tiempos o duraciones estocásticas. Ningún parámetro se estima: estos son instrumentos de generación y control físicos del laboratorio, NO hipótesis de búsqueda.

## Proyecciones con política explícita de divulgación

Generar primero bitácora `PRIVATE_TRUTH`; entregar al analista tres **proyecciones independientes por allowlist de eventos y campos** (no `truth_flag` ni IDs de etapas ocultas):
- **A `POS`**: `pedido_creado`, `pago_confirmado`, `pedido_entregado`. Disponible: ciclo total y conteo de pedidos por ventana. **No disponible:** inicio de servicio, espera interna, tiempo de preparación, recursos, número de estaciones, tiempo oculto, causas de demora.
- **B `POS_KDS`**: todos los eventos A más `servicio_inicio` y `servicio_fin` SOLO de `preparacion`. Disponible: duración de servicio en preparación *si esas marcas realmente representaran inicio/fin físicos*; lapso preparación-fin→entrega; NO están observadas su entrada a preparación, ni la espera en ella, ni el desglose del lapso final.
- **C `FULL`**: A más `etapa_entrada`, `servicio_inicio`, `servicio_fin` de todas las cuatro etapas, con `resource_id`. Permite reconstrucción exacta de intervalos, espera y servicio para cada etapa; **la cuarta etapa está OBSERVADA, no INFERIDA**.
- Un modelo de instrumentación real debe declarar confiabilidad y semántica de timestamps por fuente (POS y KDS podrían ser clicks administrativos). En este laboratorio solo C es reloj físico perfecto y B es KDS **idealizado**, marcado como tal.

## Herramientas existentes, no inventar otra ciencia

- Convertir la bitácora de cada vista a un Event Log estándar compatible con XES (caso, actividad, timestamp, recurso opcional). Ejecutar descubrimiento de **Directly-Follows Graph (DFG)** con **PM4Py 2.7.23.11**, versión publicada en PyPI 2026-10-15, pinned solo en GitHub Actions, no vendored. DFG describe **sucesión observada**, NO causalidad demostrada ni topología estructural completa.
- IMPORTANTE: PM4Py OSS se distribuye como **AGPL-3.0**. EV01 lo usa únicamente como dependencia experimental en CI; antes de incorporarlo a un producto propietario/comercial, revisar compatibilidad de licencia, restricciones de distribución y alternativas de licencia comercial. No atribuir “descubrimiento independiente” a un DFG de datos simulados y escenarios fijos.
- Análisis de tiempos propio y mínimo: SOLO aritmética de diferencia de timestamps OBSERVADOS. Para POS, `total=entregado−creado`. Para B, `prep_service=fin−inicio`; `post_prep_elapsed=entregado−prep_fin` es lapso residual **no adjudicado**. Para C, `waiting_s=inicio_s−entrada_s`, `service_s=fin_s−inicio_s`; sumar por pedido y verificar `total=Σwaiting+Σservice`. **Ningún estado interno se obtiene por resta si no están registrados sus endpoints.**
- Mostrar contraejemplos puramente temporales de NO IDENTIFICABILIDAD con el mismo `total` POS: dos asignaciones `wait=0,service=T` y `wait=T/2,service=T/2`, no afirmarlas como redes completas causalmente válidas bajo capacidades fijadas. De igual modo dos asignaciones de `post_prep_elapsed` B en transferencia/espera. En A/B el residuo positivo no prueba cuarta etapa.
- En `C`, se comprueba que la etapa `transferencia_final` es visible por eventos, no se “adivina” con residuo.

## Métricas y CI congeladas

1. **3 proyecciones sobre el mismo mundo**, con igual `case_id` y mismos timestamps para eventos compartidos; monotonía por contenido `POS⊂POS_KDS⊂FULL` para eventos y campos públicos comunes. Cero fuga de `stage="transferencia_final"` o `resource_id` en A/B.
2. Ciclo total observado idéntico A/B/C **pedido por pedido**. A/B **NO** tienen `service_by_stage` ni `waiting_by_stage` inferido; B sí conoce preparación servicio idealizado. C reconstruye todas las esperas y servicios y cierra el balance temporal para **15/15**.
3. Paridad del motor de eventos con `caf01_des_engine.run_toy_engine` en 9 snapshots de conteo, WIP y servidor; sin adaptar parámetros a resultados.
4. DFG PM4Py por nivel: actividades visibles y aristas, sin inferir estaciones no observadas; en POS no aparece `transferencia_final`, en POS+KDS tampoco; en FULL aparece bajo su propio registro. Guardar `pm4py.__version__`, versión pin, nodos y aristas.
5. Evidenciar no identificación de espera vs servicio para cada POS de ciclo `T>0`, y de causa de `post_prep_elapsed` para B, con dos descomposiciones temporales compatibles cada uno. Son contraejemplos de suficiencia de observación, no certificados de un modelo de colas completo.
6. Guardar protocolo y plan con fuentes/criterios **ANTES de evaluar**; luego `01_RESULTADOS.json`, `02_INFORME.md`, `03_MANIFIESTO.json` SHA256, y tres CSV de vistas por caso y bitácora FULL de referencia separada. Evitar incluir traza `PRIVATE_TRUTH` en payload de inferencia de A/B; el paquete de auditoría puede mantenerla en espacio EVALUATOR_ONLY claramente separado.
7. Tests negativos obligatorios: A/B no reconstruyen etapa oculta; desorden o reloj negativo, resource > servidores, missing timestamps o reetiquetado no se aceptan; la entrega del mundo C no puede reemplazar el análisis A/B, no confundir DFG con demostración causal. Pruebas comparativas de vistas y testigos de no identificación.
8. Ninguna intervención de sobrecarga en un negocio; **150/h sintético** solo fixture. No detector OOD aprendido, no set-membership por puntos, no capacidad falsa de inferencia a partir de pocos timestamps.

**Gate:** `BLOCKED_SYNTHETIC_EVENT_LOG_NO_EMPIRICAL_SENSOR_SEMANTICS_OR_EXTERNAL_VALIDATION`. PR Draft apilado, sin merge, sin conexión automática D/B/M/ATMS. Resultado no comercializable: se requiere evidencia real de instrumentación y análisis de licencias de PM4Py.
