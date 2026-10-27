# V0 — prueba ATMS de soportes alternativos

**Origen:** código existente `scripts/arena_atms.py`. Esta prueba nueva no modifica el motor.

La afirmación `candidate_compatible` tiene dos justificaciones independientes bajo una premisa de alcance compartida. Al retirar solo `observation_a`, sobrevive el soporte `observation_b + scope_valid` y su consecuencia downstream. Al retirar la premisa común, ninguno sobrevive. La llamada `what_if` no modifica la memoria original.

**Interpretación limitada:** demuestra el cálculo lógico de ambientes mínimos y retractación hipotética, no que esas observaciones o la conclusión sean verdaderas. No crea evento temporal, ledger persistente, aislamiento de los tres brazos ni una revisión de investigación. Es una prueba de infraestructura ATMS requerida por la Arena.

**Pendientes del vertical común:** entrada primaria compartida D/B/M, adaptadores semánticos por brazo, ejecución y diagnósticos por candidato, baseline B0, registro bitemporal y segunda iteración. Los ejemplos actuales de entrada no tienen esquemas de construcción idénticos (D presupone `nominal_parameters`, Buffalo utiliza `known_conditions`, M conserva roles propios); no declararlos prueba de independencia común sin armonización y gate.
