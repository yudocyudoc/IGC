# Arena D v0.1 — Método determinista puro, infraestructura común

**Estado:** implementación incremental bajo PR, no validación causal. **Brazo:** `D`, independiente de Buffalo (`B`) y molecular (`M`). Clef (`C`) está pospuesto.

## Decisión de frontera

**Puro en la generación, integrado en la evaluación y la memoria.** El método D debe producir estructuras sin leer hipótesis de `B` o `M`, sin consultar el catálogo Hines/IGCMolecules, y sin utilizar el ATMS para crear topologías. Puede compartir verificación formal, OpenModelica, contratos públicos y, posteriormente, persistencia ATMS. El ATMS no debe contaminar la generación de un brazo con las conclusiones de otro.

- **Inspiración contrastada:** Short PR [#27](https://github.com/yudocyudoc/short/pull/27) (exploración estructural), [#29](https://github.com/yudocyudoc/short/pull/29) (dos mecanismos), [#30](https://github.com/yudocyudoc/short/pull/30) (observabilidad), [#31](https://github.com/yudocyudoc/short/pull/31) (incertidumbre) y [#40](https://github.com/yudocyudoc/short/pull/40) (IR+linter P2). Ninguno de esos resultados prueba recuperación de estructura fuera del catálogo; no se transportó código molecular.
- **Documento de investigación:** `deep-research-report.md` del proyecto personal (2026-10-09) distingue compilación, ajuste conductual, identificación estructural y predicción bajo intervención. No equiparar etapas.

## Qué se ha implementado exactamente

`scripts/arena_d_v01.py` introduce una gramática limitada de **stocks conservativos, flujos materiales, fuente, sumidero y acumulador observable**. Enumera variantes *sin IDs de catálogo*:
- 1, 2 o 3 stocks de tránsito en serie.
- Opcionalmente una segunda salida lateral real, distinta del flujo entregado.
- Un pulso de entrada exógena visible y observación de entrega acumulada.
- Ecuaciones de balance generadas de las conexiones. Modelo Modelica autónomo, **sin librería molecular**.
- Parámetros positivos nominales y visibles para un *smoke test*, **sin** ajustar parámetros a las observaciones ni inferir valores verdaderos.
- Linter estricto de **esta gramática**: no es un validador general L0–L6 ni un constructor de políticas de feedback.

Para la primera fixture pública `data/synthetic/arena_d_v01_visible.json`, produce seis variantes estructuralmente distintas, sus Modelica `.mo`, hashes, `candidates.json`, `submission.json` y `memory-event.json` bajo `artifacts/arena-d-v01/`. La semántica de evento usa `trace_event()` del contrato P0. **No existe aquí persistencia ATMS, propagación de justificaciones, retractación, re-evaluación ni un ciclo de revisiones.** Es un puerto preparado para esa futura conexión.

## Evaluación y límites de afirmación

- **G0/G1:** la unidad de prueba verifica input público, rechazo de reserva/cross-arm, límites de búsqueda, tipado restringido a gramática y estructura material sin duplicación.
- **G2:** `.github/workflows/arena-d-v01.yml` compila/simula en contenedor OpenModelica con digest fijado, exige CSV para **cada** hipótesis generada y verifica de forma externa a Modelica, por muestra, que `stocks + delivered + lost ≈ ∫inputRate dt`, no negatividad y monotonicidad de la entrega.
- **G3 no implementado:** ni identificación, selección por ajuste, posterior paramétrico, predicción bajo nueva perturbación, ni comparación D/B/M.
- **Riesgo metodológico:** D enumera estructuras compatibles con la **gramática**, no demuestra que la gramática abarque el fenómeno. Su igualdad de observables puede conservar múltiples rivales. Un candidato fuera del repertorio debe seguir siendo `UNKNOWN/UNREPRESENTED`, nunca asumir que el mejor enumerado es verdadero.
- **Ceguera:** la prueba CI es sintética, pública, no contiene reserva, y **no** proporciona aislamiento de permisos frente a texto adversativo. No pertenece a una ronda científica sellada.
- **Reutilización entre brazos:** solo la prueba externa de balances y los contratos pueden reutilizarse; este script de generación **no** se llama desde B o M.

## Próximos incrementos (no implementados en este PR)

1. **D1:** pasar de enumeración de topologías a discriminación reproducible con observables, límites instrumentales y parámetros estimables; conservar abstención y estructuras ausentes.
2. **D2:** ampliar gramática a stocks-flujos generales, conexiones tipadas, feedback y políticas, con positivos/negativos físicos/semánticos. No adoptar el vocabulario molecular como generador.
3. **Memoria:** almacenamiento ATMS de hipótesis D, revisiones y justificaciones a partir de eventos; devolución de diagnósticos solo al propio brazo.
4. **Arena:** contrastar D con Buffalo y molecular sobre el mismo mundo nuevo, ejecutar OpenModelica común, iterar sin comunicación entre brazos. Clef se integra solo después.

**No confundir un G2 exitoso con identificación científica de mecanismos.**
