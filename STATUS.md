# IGC — Estado del laboratorio

## Recuperación de la arquitectura de Arena — 2026-10-26

La integración hasta `def9166` conservó D2, M0 y la ruta Buffalo inicial,
pero dejó fuera M1–M3, las revisiones físicas B3–B5 y sus ensayos negativos.
Esta recuperación incorpora esas fuentes sin fusionar cadenas históricas completas.
Véase [arquitectura recuperada y límites](docs/ARENA_RECUPERACION_ARQUITECTURA_2026-10-26.md).

- **D:** generador autónomo, revisión D2 y puente ATMS conservados.
- **M:** M3 conectado a la evidencia común; tres candidatos moleculares con parámetros
  originales, selección desde sus CSV o abstención. M1/M2 y M3-P se conservan.
- **B:** transporte original y retroalimentación física B3/B4/B5 recuperados;
  las rutas históricas siguen fijadas a sus artefactos. La ronda común permanece
  bloqueada para B mientras no se ejecute una inferencia nueva autorizada.
- **Memoria:** ATMS y recuperación admiten D/B/M, con compatibilidad S/P/B0 histórica.
- **Clef:** piloto y resultados recuperados como experimento; C no está activo en V0.
- **Estado científico:** no hay ganador, nueva reserva independiente ni versión V0.1 liberada.

El corte F0/F1a que sigue es histórico; no describe por sí solo la Arena actual.

**Corte:** 2026-10-20  
**F0:** ACEPTADA CON LIMITACIONES E INTEGRADA  
**F1a:** CORTE INICIAL INTEGRADO; LEDGER LOCAL SINTÉTICO EN PROGRESO  
**Plataforma completa:** INCOMPLETA

## Integración en main

- PR #1 — inventario y laboratorio; merge `b5fd6a3364cd7da232a0af51f76592a7d7decdef`.
- PR #3 — handoff sintético; merge `83b9ebffb437382adee94c36bb8e17476d5aa9c8`.
- PR #2 — LinkML y ledger SQLite inicial F1a; merge `acd17fbd7fe5ce8d39b208b492607936090f6d11`.
- PR #4 — `recorded_at` monotónico; merge `1d706e6847ad03c0cb6a026aa49f8b7214dbcfb0`.

## Verificación

- F0-VERTICAL: [Actions #250](https://github.com/yudocyudoc/IGC/actions/runs/39360426366), 27 pruebas.
- F1a inicial: [Actions #252](https://github.com/yudocyudoc/IGC/actions/runs/39362255158), 39 pruebas combinadas; [LinkML #15](https://github.com/yudocyudoc/IGC/actions/runs/39362255202).
- F1a temporal: [Actions #253](https://github.com/yudocyudoc/IGC/actions/runs/39362587500), 40 pruebas combinadas.

## Límites y siguiente secuencia

F0-VERTICAL es sintético, con estructura `single_stock`; no demuestra fidelidad empírica ni causalidad. F1a es SQLite temporal en Actions, no D1 ni API desplegada. RDF/CRMinf/PROV/SPARQL y ATMS no alimentan aún al modelador. H-IGC sigue `NOT_EVALUATED`; plataforma `INCOMPLETE`. Continuar con F2 (semántica ejecutable) y F3 (ATMS, investigaciones y modelos rivales), preservando la meta de experimentar con conocimiento estructurado, embeddings y modelos SD. Licencias/SBOM conservan los límites documentados.
