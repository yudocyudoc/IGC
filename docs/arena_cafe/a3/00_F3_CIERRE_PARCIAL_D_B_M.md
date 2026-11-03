# A3/F3 · 00 — Adjudicación integrada D/B/M sobre EV-01 conocido

**Fecha:** 2026-11-02. **Plan rector:** `REVISION_Y_PLAN_IMPLEMENTACION_CAFETERIA_V3_2_2026-11-02`, §F3.  
**Tipo:** control de ingeniería **retrospectivo**, NO G4/G5, NO reserva científica.  
**Dependencias:** PR #137 (Draft) sobre #136 (A2/F2) sobre #135 (A1/F1) sobre #134 (F0-HIST), ninguno fusionado.  
**CI efectiva de código:** [A1 + A3 Actions 41558277181](https://github.com/yudocyudoc/IGC/actions/runs/41558277181), commit `1f19656e202dc4b0526d43ba82b65cfaa72aeee9`, **13/13 PASS**. [Artefacto F3](https://github.com/yudocyudoc/IGC/actions/runs/41558277181/artifacts/13196005443). CI posterior de documentación se verifica por separado.

## Corrección de alcance histórico — Buffalo Cloudflare sí ha tenido inferencias reales

**Enmienda 2026-11-02.** Este cierre se refiere exclusivamente al **control EV-01 O0/O1 del PR #137**, no a la capacidad histórica del método. El proyecto ya ejecutó el motor original `UB-IAD/sd-ai@5199f7b45f3a7ae4a773cb0dd8542940aabe9edc` sobre Cloudflare Workers AI **`@cf/zai-org/glm-5.3-flash`**, por el transporte OpenRouter virtual existente:

- [Inicial real #40255975864](https://github.com/yudocyudoc/IGC/actions/runs/40255975864): una solicitud HTTP 200, modelo nativo de 15 variables / 18 relaciones; G2 no demostrado.
- [R1 real #40452596916](https://github.com/yudocyudoc/IGC/actions/runs/40452596916): 17 variables / 17 relaciones; traductor condicional y fallo real de construcción de OpenModelica por álgebra circular (no G2 PASS).
- [R2 7K #40486060023](https://github.com/yudocyudoc/IGC/actions/runs/40486060023): una revisión real, truncada, sin modelo JSON válido.
- [R2 16K #40490534985](https://github.com/yudocyudoc/IGC/actions/runs/40490534985): una revisión real posterior, nativo de 16 variables/16 relaciones y CSV OpenModelica auténtico, **pero estímulo de entrada diferente del contrato**, por lo que su G2 es condicional y G3 no comparable.

**Por tanto «Buffalo carece de inferencia real» es falso.** Lo correcto es «Buffalo no ha realizado todavía una inferencia real **sobre los sobres O0/O1 de este EV-01**». Los resultados históricos no se puntúan como pronósticos de esta nueva fuente. No hay autorización en este PR para otra llamada facturable.

## 1. Decisión metodológica fundamental

**A3=PARTIAL**, **MODEL-01=PARTIAL**, **CONDITION-01=PARTIAL**, **MEMORY-01=PARTIAL**. En este control EV-01 no hay trabajo autorizado de inferencia live de Buffalo; el motor original se invoca en modo **mock offline**, con cero llamadas a proveedor. Su ejecución de transporte no es predicción del brazo, ni `METHOD_ABSTAINED`: el estado es `BLOCKED_RESOURCE_OR_AUTHORIZATION` para inferencia auténtica. D y M sí tienen cuatro corridas nuevas de sus mecanismos reales OpenModelica, pero sobre **una sola configuración nominal declarada por brazo**, no seleccionada por el método a partir de O0/O1.

No permitir que un CI verde, un rechazo de contrato, o un resultado histórico sustituya un método nativo realmente ejecutado. En particular **no** convertir `G3` descriptivo en veredicto de compatibilidad o identificación.

## 2. Fuente común y conservación del límite de información

Solo se usa el control sintético EV-01 (15 pedidos). Cada trabajador recibe un único sobre O0 o O1 con su digest y cutoff **[0,10)**, sin eventos de futuro. O0 tiene timestamps POS públicos + conteos; O1 añade únicamente agregado físico autorizado de preparación. Ambas entradas comparten las mismas llegadas POS y entregas, verificadas formalmente antes de comparar.

La etapa **evaluadora** reconstruye desde el código original F2 el comparador B0 y comprueba exactamente los seis puntos t={0,2,4,6,8,10} contra ambas vistas. Se conserva:

- B0: mismas cuentas públicas, comparable sin privilegio;
- B1: espera/servicio de las cuatro estaciones por instrumentación **FULL**; **no** comparable como si D/M en O0 hubieran tenido dicha evidencia;
- B2: telemetría de recursos y techo de capacidades del evaluador; no entra como input ni G3 de los productores.

El código `f3_adjudicate.py` se ejecuta **después** de los diez trabajadores, en un job distinto que puede ver sus artefactos. Ningún producer job recibe `f2-controls.json`, log FULL ni configuración privada del DES. Esto es separación por workflow/proceso, **no prueba de ACL estricta** contra todos los permisos GitHub Actions.

## 3. Revalidación nativa (sin confiar en un recibo aislado)

Para cada combinación `D/M × O0/O1` el evaluador:

1. Carga exclusivamente su input público y su carpeta nativa.
2. Regenera los bytes de `native.mo` y `simulate.mos` mediante **gramática D original** o **compositor/backend Short E1 originales**. Exige igualdad exacta con el artefacto; no reescribe ecuaciones del brazo.
3. Recalcula el verificador original de masa en toda la CSV real, comprueba intento del solver, código de salida, hashes, continuidad/positividad de stocks y paridad con la reconstrucción de llegadas.
4. Reejecuta el operador **H_j** sobre CSV, puerto observado y AST original de E1; exige igualdad exacta del resultado H_j almacenado, sus hashes y el archivo de simulación verificado.
5. Reconstruye la fuente y supuestos desde el archivo **SQLite append-only real** correspondiente al brazo/condición (10 linajes: seis workers, cuatro nativos), vuelve a proyectar ATMS y comprueba su linaje. Un soporte lógico ATMS **no prueba** una hipótesis.
6. Calcula exclusivamente `RMSE = sqrt(mean((y_hat(t)-y_obs(t))²))` para las seis medidas **de entregas acumuladas**, y registra el error de masa de entrada separado. No introduce tolerancia post hoc, calibración, clasificación o pronóstico independiente.

`G0` de ingeniería: original generado y bytes regenerados. `G1`: unidades, inicialización y balances sujetos a las verificaciones documentadas del control A1, **no análisis físico completo universal**. `G2`: ejecución OpenModelica y conservación real comprobada. `G3`: descripción de construcción **sin umbral de adecuación predeclarado**; no `G3_PASS` científico. `G4=NOT_RUN`, `G5=NOT_RUN`.

Los metadatos del módulo de lectura H_j siguen declarando `NATIVE_GENERATION=NOT_PERFORMED`, porque **ese módulo** no genera modelos. A3 comprueba separadamente el generador/solver y no cambia retroactivamente la responsabilidad de H_j.

## 4. Resultado reproducido

| Estado/observable | D O0 y O1 | Moléculas O0 y O1 | Buffalo O0 y O1 |
|---|---:|---:|---|
| Método D/E1 nativo | D original, 2 stocks | Short E1 original, C00 | Engine Buffalo original en **mock** |
| Modelo con parámetros nominales | Sí, no calibrados | Sí, no calibrados | **NO** inferencia live |
| G2 de ingeniería | PASS | PASS | NOT_RUN |
| RMSE entregas acumuladas en 6 muestras | **4.3201868747** pedidos | **4.3201868729** pedidos | No válido |
| Entregas observadas t=10 | 8 | 8 | — |
| Entregas predichas t=10 | **0.3211608540** | **0.3211608558** | No disponible |
| Error t=10 predicho − observado | −7.6788391460 | −7.6788391442 | No calculable |
| Independencia G4/G5 | NO | NO | NO |

**Interpretación:** las configuraciones nominales de D y Moléculas son casi dinámicamente equivalentes en este control; las dos ajustan **mal** las entregas observadas. No implica que ambos métodos carezcan de representabilidad o capacidad de calibración: **no se buscaron alternativas** en esta fase y no se probaron parámetros con evidencia independiente.

**O1 preparación:** 9 servicios discretos completos observados vs **2.6188126009** unidades obtenidas integrando el flujo `preparation.completed` de E1. El operador documenta expresamente la falta de equivalencia semántica demostrada entre dichas medidas. Se reporta como `PROVISIONAL_NON_EQUIVALENT_MEASUREMENT_NO_G3_SCORE`, **no entra al RMSE**.

Los valores de D/M son iguales entre O0 y O1 porque el generador de escenarios en esta prueba usa el mismo POS y parámetros nominales; O1 no los modifica. Esto **no prueba** que D/M hayan aprovechado todas las nuevas observaciones, ni exige que un método modifique su respuesta ante un campo adicional.

## 5. Buffalo, interfaz y ledger

`scripts/arena_b_native_runner.mjs` sigue invocando el original `UB-IAD/sd-ai` al SHA fijado, con `BUFFALO_MODE=mock`. Los recibos O0/O1 prueban que existe una ruta de transporte y hashes de prompt **distintos** entre condiciones, pero el resultado del modelo no se usa como inferencia. No presentar `ORIGINAL_ENGINE_OFFLINE_MOCK` como `G3_FAIL` científico, selección, predicción ni abstención propia. **Ausencia de ejecución live para EV-01 O0/O1 deja A3 abierto** hasta que exista autorización y presupuesto explícitos.

El evaluador verifica `scope = experiment × mundo público × réplica × brazo × condición × iteración × run_kind`; 10 IDs de caso únicos. Reabre las 10 SQLite, comprueba revisiones append-only, `source_snapshot_hash`, candidatos, (H_j), integridad de revisiones y lectura de ATMS filtrada antes de recuperación. No prueba control de token/API ni separación de cachés en un proveedor externo. `MEMORY-01` y `CONDITION-01` permanecen parciales.

### Incremento Buffalo EV-01 sin gasto

El código `scripts/arena_cafe/buffalo_ev01_visible.py` valida un único sobre público A1 O0 u O1, transforma tiempos POS y tasa reconstruida conservativa de medio minuto a unidades hora/pedidos/hora, conserva **15** pedidos integrados, distingue la medición adicional de preparación autorizada de O1 y produce un `igc-arena-visible-input/0.1` consumible por el motor original. Su pregunta cabe en el contrato compartido de 180 caracteres; las instrucciones detalladas viajan en `construction.modeling_task_instructions`, y el `backgroundKnowledge` **original Buffalo** contiene ambas. No hay parámetros de las cuatro estaciones privadas, candidatos D/M ni datos posteriores al cutoff.

La CI `a3-b-cloudflare-offline-preflight` corre el motor original SD-AI con el transporte original `scripts/arena_b_openrouter_cloudflare.mjs` en modo **offline**, recibe una respuesta *fixture* claramente etiquetada, conserva hashes de prompts y demuestra una solicitud original por condición con **0 llamadas Cloudflare reales**. **No equivale a hipótesis propia Buffalo EV-01**, ni a G0/G1/G2/G3 de ella. El puente genérico actual tiene límite **3500 tokens de salida** fuera de los modos R1/R2 autorizados; el riesgo de truncamiento debe revisarse **antes** de aprobar llamadas EV-01. Además el traductor histórico `arena_b_native_to_modelica.py` fija un solver 0–8 horas y `dt=0.125h`, distinto de la ventana EV-01; cualquier adaptación física debe pasar un contrato G0 separado sin alterar ecuaciones Buffalo.

## 6. Entregables y compuertas

Archivos nuevos:
- `scripts/arena_cafe/f3_adjudicate.py` — adjudicador evaluador basado exclusivamente en métodos reales, estados y artefactos.
- `tests/test_arena_cafe_f3_adjudicate.py` — pruebas de scores, falsificación Buffalo, datos intercambiados O0/O1, reconstrucción SQLite, no sobreafirmación.
- `.github/workflows/arena-cafe-a1-evidence.yml` — job adicional `f3-known-control-adjudication` dependiente de **6 workers + 4 OMC + comparación**, con descarga por tipo, **sin nuevas llamadas a proveedor**, F2 privado solo evaluador.
- `docs/arena_cafe/a3/00_F3_CIERRE_PARCIAL_D_B_M.md` — este expediente.

El PR sigue Draft. **No se promueve ningún cambio a `main`.** El cierre formal de A3 deberá revisar la ejecución auténtica de Buffalo y los controles de seguridad del plan, o conservar expresamente el corte parcial; nunca crear un equivalente sintético para dar por completados los tres brazos. F4/F5, operación P y modelo de recursos nuevos fuera de alcance.
