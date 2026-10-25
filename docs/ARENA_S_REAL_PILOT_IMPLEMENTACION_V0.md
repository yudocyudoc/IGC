# Arena V0 — Puente S auténtico, ajuste y revisión adversativa

**Rama:** `feature/arena-s-real-pilot-v0` · **Base:** PR #16 · **Estado:** implementación experimental en PR #17; revisión Astra, prueba integrada de OpenModelica para el piloto y campaña controlada pendientes.

## Decisión

Implementar **solo** el recorrido mínimo señalado en `ANALISIS_BRECHA_IGC_2026-10-24.md`: inferencia estructural **restringida** con CS-01/CS-02, comparación posterior con enumeración y ajuste bajo recursos equivalentes, sin rediseñar ATMS–compositor–OpenModelica.

La arquitectura y la ruta existente de 3 proveedores no se reemplazan. La ruta S independiente no hace una llamada a Clef ni a Clairic. El paquete de preparación conserva por ahora las tres solicitudes legacy para mantener intacto su contrato de hashes y presupuesto, pero **solo se envía la primera**. Esta dependencia residual de preparación debe quedar documentada; no es una dependencia operacional de respuestas P.

## Código entregado

1. `arena_sp_producers.parse_s_response`: JSON de S validado independientemente de P. Se conserva parser estricto, sin candidatos inventados; `parse_responses` reutiliza el mismo parser.
2. `arena_s_real.py`: S-only con autorización `RUN_ARENA_S_ONE`, captura un solo cuerpo/respuesta/uso, sin reintento y sin sobrescribir corrida parcial. Un recibo local permite comprobar consistencia de los objetos, no certifica remotamente al proveedor. `INJECTED_TEST_SENDER` nunca equivale a `PYTHON_URLLIB`. Sellado ATMS de S vincula la selección a catálogo, soporte, vista, solicitud, respuesta y, opcionalmente, calibración.
3. `arena_s_calibration.py`: reutiliza el ajuste por rejilla de FM-B5 sobre observaciones **solo de construcción**, por estructura y con incertidumbre reportada. Produce un composed con parámetros por etapa/estructura, vuelve a calcular los hashes estructurales y genera Modelica para el pulso fijado en el plan B5. La calibración usa RK4; las predicciones propuestas para puntuación se exigen en OpenModelica.
4. `arena_sp_simulation.py`: la preparación de una simulación S puede provenir de la captura S-only; si dice origen real, exige el recibo de calibración y los hashes de construcción, estructura y pulso. El informe del solver mantiene separado `S_CAPTURED_MODEL_EXECUTION_PASS_SYNTHETIC` de `S_MOCK_MODEL_EXECUTION_PASS_SYNTHETIC`. El informe por sí solo **no** crea una entrega S.
5. `arena_s_submission.py`: crea una entrega S tipada únicamente después de verificar captura, reejecutar comprobación de ajuste, validar el informe de OpenModelica, cotejar hashes de CSV y extraer predicciones sobre los tiempos fijados. Bloquea entrega con uso en tokens no observable en vez de inventar cero.
6. `arena_s_pilot_round_spec.json` y `arena_s_pilot_catalog.json`: dos alternativas simétricas y ventana de evaluación separada. Son **insumos públicos sintéticos**, NO reservas ciegas ni hallazgos científicos.

## Orden de operación (sin inferencia automática)

- Un evaluador independiente genera las observaciones de construcción `primary.json` y, **en un proceso separado y restringido**, una nueva reserva y su compromiso temporal. La reserva no se entrega a S, al coder ni al repositorio.
- El coder construye una variante del plan de composición B3 con solo CS-01/CS-02 y un soporte ATMS sin nogoods que codifiquen la verdad. Compone ambas moléculas y genera vistas de `arena_round.prepare` para la nueva primary. La preparación S/P legacy puede construir el paquete de tres solicitudes, pero el S-only enviará **solo** GLM.
- `arena_s_calibration` ajusta con construcción, escribe `calibrated-composed.json`, `evaluation-plan.json`, `calibration-receipt.json` y `GeneratedMolecularCandidates.mo`. Congelar la preparación, pulso y ajustes antes de la reserva.
- `arena_s_real capture` envía una solicitud real GLM con autorización expresa. Conservar `response.json`, `s-draft.json`, `receipt.json`. Bloqueo del proveedor / JSON inválido es un resultado de transporte; no autoriza reintento de la misma campaña.
- `arena_s_real seal` con `--calibration` y `arena_sp_simulation prepare --s-archive ... --calibration ...` sellan la selección y generan scripts de OpenModelica. Montar la carpeta de compositor calibrado en `/composer`, las evidencias en `/evidence` y el directorio de resultados en `/results` como en el workflow actual.
- Ejecutar y verificar OpenModelica. `arena_s_submission` debe rechazar cualquier traza, muestra o parámetro que no coincida con el paquete congelado.
- Ejecutar **por separado** una enumeración CS-01/CS-02 con el mismo ajuste de construcción, parametrización, pulso y solver, sin lectura de la selección S. Congelar ambos brazos antes de abrir la reserva. Mantener P como `NOT_IMPLEMENTED`; nunca imputar juicio de Clef. Conservar B0 persistencia/OLS únicamente como controles secundarios.
- Un custodio separado puntúa con las nuevas observaciones; registrar conservación de hipótesis correcta, descartes falsos, RMSE, abstención, utilidad del pulso y costos. **Todavía no hay una campaña implementada/ejecutada que satisfaga este último punto**.

## Comparador D y congelación B0/D/S

- `arena_s_pilot_supports.json` conserva **ambos** candidatos como hipótesis posibles, sin nogoods que codifiquen la verdad generadora.
- `arena_s_pilot_fit_config.json` omite semillas y parámetros/estructura del generador; `calibrate` rechaza configuraciones que incluyan esa verdad. La entrada observada y stocks iniciales cero deben figurar en `primary.input_profile`.
- `arena_s_pilot_enumeration.py prepare` genera dos experimentos Modelica independientes de la selección de S, empleando las **mismas** estructuras calibradas y el mismo pulso. Montar el directorio calibrado en `/composer`, ejecutar en `/results` por separado y usar `submit` para validar ambas trazas como entrega D.
- `arena_s_pilot_lock.py` combina B0 determinista, D de enumeración, S real (o abstención justificada) y P como `NOT_IMPLEMENTED`. Su LOCK exige las entregas producidas anteriormente. El LOCK **no** atestigua por sí solo la ejecución previa ni abre la reserva.
- `tests/test_arena_s_pilot.py` prueba preparación de D y contrato de LOCK, **no** simulación empírica ni campaña completa. La prueba actual de OpenModelica en CI sigue siendo la regresión MOLECULAR/MOCK previa.

Las predicciones del comparador y de S solo podrán compararse después de verificar el mismo experimento, el mismo protocolo de calibración y los recursos consumidos. El test de pulsos todavía es fijo, no elegido autónomamente por S.

## Bloqueos abiertos y límites

- **No hay aún evidencia nueva ni reserva ciega independiente**. El plan de FM-B5 contiene una verdad sintética publicada: no reutilizarla como nuevo mundo oculto.
- **Selección de perturbación todavía no es autónoma**: `next_test` sigue siendo texto y el pulso de FM-B5 viene fijado externamente. El incremento actual instrumenta la ruta de una propuesta real con parámetros calibrados, no resuelve por sí solo la elección de prueba.
- **El código prepara D y B0/D/S, pero aún no se ejecutó un contraste nuevo con recursos equiparados**. Debe hacerse antes de atribuir contribución al núcleo IGC. Tampoco se ha hecho ablación con/sin memoria ATMS.
- **No se garantiza equivalencia numérica RK4↔OpenModelica**; el ajuste por RK4 y la predicción por OpenModelica deben contrastarse y documentar discrepancias si aparecen.
- **No invocar CI con credenciales**. Las pruebas usan respuestas falsas, no consumen modelos.
- **No fusionar** hasta confirmar tests, solver y revisión adversativa. No interpretar una petición HTTP capturada como atestación independiente.

## Encargo de revisión para GPT-6-Astra (Extra High)

Actúa como revisor adversativo independiente de PR #17 contra el informe de brechas del 24 de octubre. Revisa exclusivamente el diff y los contratos necesarios de #16, sin modificar el código.

Determina si (a) S puede producir una entrega con P ausente, (b) un mock o recibo falsificado puede convertirse en propuesta supuestamente real, (c) los parámetros y el plan de perturbación proceden únicamente de datos de construcción y se mantienen congelados, (d) la ejecución del Modelica del candidato realmente corresponde a esos parámetros, (e) el informe/sello permite crear una entrega no verificada, y (f) existen errores de regresión o incoherencias científicas.

Para cada hallazgo: severidad, archivo/línea, reproducción mínima, contrato violado, arreglo localizado y estado de prueba. Separa fallos bloqueantes de mejoras posponibles. No propongas nuevas capas de arquitectura salvo incapacidad reproducible. No afirmes que se ha demostrado H-IGC sin evaluación contra el comparador.
