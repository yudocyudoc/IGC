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
