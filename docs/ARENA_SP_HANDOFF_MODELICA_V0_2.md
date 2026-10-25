# Arena IGC — Handoff S/P, ATMS, Modelica y baseline B0

**Fecha:** 2026-10-24. **Estado:** implementación incremental en PR #16, rama feature/arena-atms-memory-core (base PR #15).

## Objetivo

Separar cinco hechos: propuesta LLM, admisión lógica ATMS, topología ejecutable, predicciones simuladas y contraste empírico. Un resultado técnico no es evidencia de verdad causal.

## Contratos implementados

- scripts/arena_sp_handoff.py: valida integridad de respuestas y vistas, conserva P como juicio tipado, sella selección S previa a simulación y descarta candidatos rechazados por el motor ATMS común. CS-03 no puede ejecutarse bajo el soporte sintético vigente.
- scripts/arena_sp_simulation.py: produce un modelo OpenModelica para la selección sellada de S, ejecuta en directorio separado de D y verifica checkModel, conservación de stocks, rejilla y hash de cada trayectoria.
- scripts/arena_round.py: B0 incluye ahora persistencia y una predicción lineal OLS calculada solo con datos de construcción; ambas se congelan bajo PredictionLock.
- tests/test_arena_sp_handoff.py: casos negativos de rechazo ATMS, selección adulterada, justificaciones cambiadas, vistas cruzadas y falsa promoción de mocks.
- tests/test_arena_round.py: prueba de B0 lineal e inmutabilidad de ambas variantes.
- .github/workflows/arena-atms-memory.yml: antes de ejecutar Modelica se genera una propuesta S sintética y explícitamente MOCK_SYNTHETIC; después se ejecuta únicamente el candidato permitido, por separado de D, y se comprueba que los otros no fueron simulados.

## Diagrama

    Vistas separadas B0/D/S/P
                 |
         Solicitudes a GLM/Clef/Clairic (sin inferencia en CI)
                 |
         Borrador de S / juicio P
                 |
         Sellado independiente + hash de selección
                 |
         ATMS: entornos de soporte, nogoods y admisibilidad
                 |
         ¿Candidato propuesto admisible?
          | sí                    | no
     Compositor + Modelica   Rechazo/abstención
          |
     Simulación S separada, conservación y hashes
          |
     Predicciones técnicas, NO evaluación empírica

    B0: persistencia + tendencia OLS, sin datos reservados
    P: juicio de soporte y aritmética, sin topología
    LOCK real requiere inferencia, costos, simulación y custodia separada

## Limitaciones

1. El caso CI utiliza una selección simulada a propósito; NO representa inferencia de GLM.
2. El productor S opera sobre un catálogo público y no genera aún topologías libres.
3. No existe una evaluación ciega nueva ni permisos independientes de custodia demostrados.
4. La vía P necesita recibos auténticos, medición de costo y salida validada antes de considerarla entregada. Una prueba mock conserva estado de abstención.
5. B0 lineal es un control determinista, no necesariamente un buen predictor universal.
6. Las cifras de Modelica dependen del escenario y parámetros sintéticos ya definidos. ATMS conserva explicaciones y supuestos, no decide verdad.
7. No se han creado Workers, secretos, callbacks ni inferencias facturables.

## Pruebas

    python -m unittest discover -s tests -p 'test_arena_sp_handoff.py' -v
    python -m unittest discover -s tests -p 'test_arena_round.py' -v

La simulación independiente de S se verifica con GitHub Actions y OpenModelica en arena-atms-memory.yml. No fusionar hasta CI íntegra y revisión adversativa.

## Siguiente incremento

Conectar respuestas proveedor reales cuando exista autorización para la campaña y recibo de uso medido; producir objetos ejecutables de S con G1/G2/G3; adjudicar bajo reserva creada y conservada por un custodio independiente. La decisión de implementar ATMS como motor de memoria y de soporte está cerrada.
