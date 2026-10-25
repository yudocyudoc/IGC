# Arena CEI–IGC — Productores S/P y custodio V0.1

**Corte:** 2026-10-24. **Repositorio:** IGC, PR #16 apilado sobre #15.
**Alcance:** componentes ejecutables con pruebas sintéticas; no representa una evaluación ciega completa.

## Contratos recuperados y conectados

El adaptador scripts/arena_sp_producers.py usa los modelos y formatos del experimento EPI-04/EPI-06 de short:

| Productor | Modelo Cloudflare Workers AI | Producto |
|---|---|---|
| S · SD-AI provisional | @cf/zai-org/glm-4.7-flash | Selección/critica de mecanismos del catálogo público |
| P · Clef | @cf/cloudflare/clef | Juicio tipado de suficiencia de evidencia |
| P · Clairic | @cf/cloudflare/clairic | Comprobación aritmética de construcción |

Cada petición se prepara desde la vista autorizada S o P, sin acceder a propuestas de D ni a respuestas de otras vías. No se da a la IA el modelo generador, la reserva ni trayectorias reservadas.

La salida es PROVIDER_DRAFTS_NOT_LANE_SUBMISSIONS. GLM **no genera Modelica ni predicciones**: los candidatos seleccionados requieren admisión ATMS, linter y ejecución formal antes de ser candidatos S evaluables. Clef no decide verdad empírica y Clairic no reemplaza un oráculo determinista.

El paquete de solicitudes es reproducible (hashes, modelo fijado, máximo tres peticiones, cero reintentos); los tests usan proveedores falsos. CI prepara solicitudes y verifica su integridad sin llamar a IA. El modo de inferencia requiere autorización separada RUN_ARENA_SP_MAX3 y las credenciales existentes de Cloudflare como variables de entorno. **No se ha ejecutado inferencia real para esta Arena.**

## Custodia privada transaccional

scripts/arena_custodian.py ofrece:
1. Preregistro de reserva con hash salado y nonce privado de 32 bytes. El compromiso público no contiene oro, valores ni la sal.
2. Registro privado por round_id y reserve_id únicos.
3. Consumo mediante SQLite BEGIN IMMEDIATE, rechazo de doble uso del mismo reserve_id y prueba de que la reserva coincide con el compromiso original.
4. Resultado RMSE privado calculado solo después de comprobar integridad del PredictionLock.
5. Recibo de consumo privado con hash de reporte y lock.

### Ejecución por evaluador (no ejecutar en CI público)

~~~bash
python -m scripts.arena_custodian register \
  --db /custodia-privada/custody.sqlite \
  --reserve /custodia-privada/reserve.json \
  --out /custodia-privada/commitment.json

python -m scripts.arena_custodian consume \
  --db /custodia-privada/custody.sqlite \
  --reserve /custodia-privada/reserve.json \
  --lock /custodia-privada/prediction-lock.json \
  --custodian-ref evaluador-autorizado \
  --out /custodia-privada/evaluation-report.json
~~~

El archivo SQLite, la reserva y los recibos **deben permanecer fuera del repositorio público y bajo un principal separado**. El código no crea ese aislamiento por sí solo. Tampoco certifica que register haya ocurrido antes del experimento: el reloj local NO es atestación independiente. El preregistro debe vincularse a una prueba temporal externa y acceso denegado a productores.

## Gates siguientes

- Conectar respuestas reales de S y P con fuentes y costo efectivo; no promocionar drafts mock a LaneSubmission.
- Ejecutar en OpenModelica los mecanismos S formalizados y verificar G1/G2/G3; no leer propuestas de D antes de sellar las de S.
- B0 más fuerte que persistencia, reglas de presupuesto equiparado y consumo remoto del registro de costos.
- Preregistro verificable ANTES de crear mundo nuevo, custodia privada independiente, prueba de lectura denegada y reserva consumida irreversiblemente.
- Conectar memoria ATMS temporal con RDF/SPARQL, KGE y espacios de texto/grafo/dinámica sin saltar permisos ni cortes.

## Estado

M0 memoria ATMS/FTS5, selección F3/FM-B2 y FM-B3/OpenModelica, B0 simple/LOCK, contratos S/P y custodia SQLite son componentes implementados. No se ha realizado nueva evaluación ciega ni llamadas reales de IA para Arena; no se ha desplegado un nuevo servicio Cloudflare.
