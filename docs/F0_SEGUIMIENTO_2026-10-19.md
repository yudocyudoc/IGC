# F0 — Seguimiento de inicialización del repositorio

**Fecha:** 2026-10-19  
**Rama de trabajo prevista:** `f0-inventario-spike`  
**Estado:** checkout local sincronizado en rama F0; spike sintética ejecutada, integración real pendiente.

## Inicialización remota autorizada

Con autorización del investigador, se inicializó `main` en `yudocyudoc/IGC` con los tres documentos de propuesta y planificación, sin código de implementación:

- Especificación v0.2 — commit `5c37213a4fe0ed2135f5c8697094760997377f8b`.
- Plan de implementación — commit `7b583b90919eba406d671e8bc45f48a48a496948`.
- Auditoría F0 inicial — commit `c41101d4715b5180c61308039845946ecbc91687`.

Después se creó `f0-inventario-spike` desde `main` mediante GitHub Connector. La rama existe en GitHub y contiene la línea base documental. No se han agregado archivos de implementación, ni se ha creado un PR o fusionado cambios.

## Inventario local de herramientas

| Herramienta | Resultado |
|---|---|
| OpenModelica `omc` | No encontrado en PATH. |
| Docker | No encontrado en PATH. |
| Python | Python 3.13.1 (`C:\Python313\python.exe`). |
| Node.js | v22.13.1. |
| Git | 2.51.0.windows.1. |
| Wrangler | Comando localizado; no se obtuvo versión en esta comprobación. |

Este inventario sólo refleja el PATH del entorno actual; no acredita inexistencia del software fuera de él.

## Bloqueo restante de la primera auditoría

Este bloqueo quedó resuelto al clonar el repositorio en `IGC-f0` dentro del workspace actual. El clon está limpio en `f0-inventario-spike` y sigue `origin/f0-inventario-spike`. Los fallos del checkout anterior y del gestor de worktrees explican por qué se usó este clon; no describen ya el estado de la rama actual.

## Corrida de spike sintética

- La fixture de texto y la afirmación están marcadas sintéticas. La verificación local encuentra el fragmento exacto y calcula SHA-256 `d1f9ff1422b8283e6ada4bd8bbf28ef6582039a380b13435e9048df09cb7e25e`.
- Cinco pruebas contractuales cubren estados incompletos y anclaje; las cinco pasaron.
- `python scripts/f0_spike.py` escribe `artifacts/f0/run.json`; la corrida confirmó `BLOCKED` y devuelve código 2 por componentes faltantes. El reporte y el borrador de anotación de esta corrida se conservan en la rama.
- El objeto Web Annotation es sólo un borrador de forma; no se ha validado contra el modelo W3C. RDF/CRMinf/PROV/SHACL, SPARQL y ATMS siguen pendientes.
- `F0ToyStock.mo` y `candidate-stub.json` son fixtures sintéticos. No se ejecutó `omc` porque no está en PATH. No existe handoff formal ni simulación registrada.

**Resultado actual:** `REMOTE_BASELINE_CREATED`, `REMOTE_F0_BRANCH_CREATED`, `LOCAL_CHECKOUT_READY`, `SOURCE_ANCHOR_PASS`, `VERTICAL_SPIKE_BLOCKED`.

## Próximo paso operativo

Repetir las pruebas contractuales, conservar el reporte bloqueado como evidencia local y acordar/instalar desde fuentes verificadas los motores RDF/SHACL/SPARQL, ATMS y OpenModelica antes de ampliar la spike. No presentar stubs como integración ni ejecutar gasto cloud.
