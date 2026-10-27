# Arena V0 — evidencia de construcción común, sin equiparar métodos

El artefacto canónico `arena_v0_primary_construction.json` contiene un solo corte: pregunta, pulso, observaciones y unidades. Su SHA se calcula de los datos reales. Se derivan tres vistas contractualmente iguales del origen; luego cada método recibe adaptaciones rastreables.

D requiere `nominal_parameters`, declarados **explícitamente como supuestos** en un archivo separado. Sin ellos se bloquea. Buffalo recibe contexto textual sin que esta capa invoque un modelo. M recibe el mismo contexto y conserva `M_OBSERVATION_TO_ROLE_MAPPING_NOT_IMPLEMENTED`; ninguna estructura es seleccionada de forma artificial.

**No se ha probado todavía igualdad de información efectiva a nivel de prompts ni aislamiento operacional de procesos:** la capa prueba hashes e integridad, no permisos de custodia. No hay ejecución simultánea D/B/M ni comparador B0 ni feedback o evaluación de reserva. Las observaciones son sintéticas históricas y no constituyen un holdout nuevo.

**Siguiente gate:** consumir estas entradas en tres procesos separados, guardar las entradas transformadas efectivamente enviadas a cada método, registrar resultados nativos o bloqueos, costes, y validar que cada método puede abstenerse sin heredar las estructuras rivales.
