# Arena IGC — V0: ronda, baseline B0 y PredictionLock

**Fecha:** 2026-10-24. **Repositorio:** yudocyudoc/IGC; rama feature/arena-atms-memory-core.
**Carácter:** regresión sintética de infraestructura. No es un nuevo experimento ciego.

## Entregas de este corte

- scripts/arena_round.py: definición de observabilidad, horizonte, permisos declarados, presupuesto por vía, preparación de vistas B0/D/S/P, validación de entregas, LOCK por SHA-256 y comparación RMSE con reserva externa.
- scripts/arena_b3_lock.py: adaptador FM-B3 -> Arena D. Reutiliza el ATMS compartido, los candidatos moleculares y la ejecución OpenModelica ya verificadas. Compara el hash de cada CSV con el informe B3, extrae trayectorias sobre los tiempos fijados y rechaza las de candidatos excluidos.
- B0 emplea persistencia del último dato de construcción, sin recibir contexto enriquecido. Es un baseline simple de ingeniería y no la baseline fuerte final.
- S y P se registran como NOT_IMPLEMENTED en esta regresión; no se inventan juicios, propuestas ni inferencias para esas vías.
- El documento de LOCK guarda hashes del protocolo, vistas, propuestas, costos y referencias de la ejecución de Actions. Estado: LOCKED_NOT_EVALUATED.
- score_locked valida un LOCK existente antes de recibir datos de evaluación; evaluate_once registra el consumo por reserve_id usando apertura local exclusiva. No se ejecutan en el workflow público.

## Flujo

~~~mermaid
flowchart TD
  C["Protocolo, datos de construcción, observabilidad y presupuesto"] --> V["PREPARE: B0/D/S/P separados"]
  V --> B["B0: persistencia simple sin ATMS"]
  V --> D["D: FM-B3 ATMS compartido y OpenModelica"]
  V --> S["S: NOT_IMPLEMENTED en V0"]
  V --> P["P: NOT_IMPLEMENTED en V0"]
  B --> L["LOCK: predicciones, hashes, costos y abstenciones"]
  D --> L
  S --> L
  P --> L
  L --> E["Evaluador independiente y reserva nueva: PENDIENTE"]
~~~

## Pruebas

~~~bash
python -m unittest discover -s tests -p 'test_arena_round.py' -v
python -m unittest discover -s tests -p 'test_arena_b3_lock.py' -v
~~~

GitHub Actions invoca scripts.arena_b3_lock una vez verificados los resultados FM-B3; publica el artefacto arena-v0-b3-construction-lock. Este contiene las vistas y submissions, además de prediction-lock.json, pero NO incluye datos reservados.

Para una evaluación externa futura, la CLI preparada usa:
~~~bash
python -m scripts.arena_round evaluate \
  --lock prediction-lock.json \
  --reserve /ruta/privada/reserva.json \
  --receipts /ruta/privada/recibos \
  --custodian-ref custodio-independiente \
  --out resultado-privado.json
~~~

## Límites

1. La pareja CS-01/CS-02 y el pulso FM-B3 son públicos y sintéticos. No son una evaluación ciega fresca.
2. Los datos de construcción en data/synthetic/arena_v0_b3_primary.json son ilustrativos, no observaciones empíricas.
3. La vía S/SD-AI y la vía P/Clef-Clairic todavía no entregan propuestas; S/P quedan explícitamente NOT_IMPLEMENTED.
4. Un hash no certifica que nadie haya visto la reserva. GitHub Actions no es aquí un custodio independiente.
5. El recibo de consumo de evaluate_once es local y puede ser eliminado: no acredita exclusividad global ni seguridad multiusuario.
6. B0 de persistencia no sustituye el comparador simple fuerte del plan v1.1; el costo humano de preparación no está completamente medido.
7. No hay simulación de abandono como egreso conservativo: el catálogo actual no tiene esa molécula. Ningún resultado ATMS implica verdad empírica.
8. No se han agregado Workers, callbacks, secretos ni dependencias Cloudflare.

## Siguiente gate

Implementar custodia independiente, preregistro previo a una nueva generación de mundo, producción autónoma y sellada de S/P, B0 fuerte y contabilidad íntegra; solo entonces abrir reserva y medir valor científico. Continuar también con recuperación FTS/semántica y conformidad completa ATMS sin reabrir su adopción.


## S/P — integración de productores y límite del corte (2026-10-24)

scripts/arena_sp_producers.py incorpora, sin duplicar un backend cloud, los mismos formatos de petición de la campaña EPI-04/EPI-06 de short:
- S_GLM -> @cf/zai-org/glm-4.7-flash: propuesta/critica de candidatos causales dentro de un catálogo público independiente, **sin** generar código Modelica ni cifras de predicción.
- P_CLEF -> @cf/cloudflare/clef: juicio tipado sobre suficiencia/identificabilidad de evidencia de construcción.
- P_CLAIRIC -> @cf/cloudflare/clairic: comprobación aritmética de un incremento visible; se contrasta con el oráculo determinista. No sustituye calibración ni identifica parámetros.

Los tres cuerpos se construyen a partir de las vistas de su vía y del catálogo previo; no contienen entregas, diagnósticos ni predicciones de D. S y P no reciben resultados mutuos. El paquete guarda hashes de cada petición, cuenta fija MAX3 y manifiesto PREPARED_NO_INFERENCE. Se comprueba identidad de casos, permisos declarados, origen del catálogo, integridad de solicitudes, respuestas tipadas y candidatos inventados. Si el proveedor propone estructura no admitida, no se convierte en una simulación ni en juicio causal.

La CLI permite preparar sin credenciales:

~~~bash
python -m scripts.arena_sp_producers prepare \
  --spec data/synthetic/arena_v0_b3_round_spec.json \
  --views-dir /ruta/vistas-generadas \
  --catalog data/synthetic/arena_sp_public_catalog.json \
  --out /ruta/sp-requests.json
~~~

La llamada real es una operación separada y requiere **autorización específica** RUN_ARENA_SP_MAX3 y credenciales existentes CLOUDFLARE_ACCOUNT_ID/CLOUDFLARE_API_TOKEN. No se ejecuta en CI y no se ha hecho inferencia durante este corte. No copiar credenciales al repositorio, logs ni conversación. No se ha añadido una nueva conexión de doble autenticación, ni se ha tocado el Worker.

Las respuestas se interpretan como PROVIDER_DRAFTS_NOT_LANE_SUBMISSIONS: **para S falta traducir/validar su selección en un modelo admisible y ejecutar predicciones**, y para P faltan formalizar los juicios como LaneSubmission con presupuesto medido. No puede falsificarse una ronda S/P completada con outputs mock. La cifra de tres llamadas representa solo el techo técnico; el costo real en tokens/tiempo deberá contabilizarse con trazas del proveedor.

Fuente interna de compatibilidad: short/experiment/epi-04-triangulation (prepare.py, run_cloudflare.py, evaluate.py) y short/experiment/epi-06-atomic-questions. La conexión de la Arena utiliza los mismos endpoints, pero sus prompts y validadores son experimentales propios.

El workflow Arena publica arena-sp-producer-preparation-no-inference; son solicitudes de una fixture pública sintética, **sin** respuestas de IA ni gold.
