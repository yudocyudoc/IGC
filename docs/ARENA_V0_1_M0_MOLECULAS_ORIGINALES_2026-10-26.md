# Arena V0.1 · Promoción M0: moléculas originales Short E1, sin reinterpretación

**Corte:** 2026-10-26. **Fuente:** PR #27 `feature/arena-m-short-e1-independent-v0` SHA `79a21dcfb5010a25213d063c868d6c5d719e0f42`.  
**Objeto:** capacidad molecular de ingeniería, independientemente de D/B; **no** M3 como recuperador estructural.
**Destino:** código revisado para `IGC/main` a través de PR específico. No se fusiona la pila de #27–#41.

## Alcance exacto de la importación

- `experiments/e1/composer.py`, `backend.py`, `verify_native.py`, `test_composition.py`, registros base/ext y catálogo `experiments/e0/catalog.json`.
- Wrappers `IGCMolecules.mo` e `IGCInformationMolecules.mo`.
- `scripts/arena_m_short_e1.py`: expone la biblioteca molecular al contrato V0, **devuelve PARTIAL** y señala desconocimiento de selección por observaciones.
- Archivo original `docs/ARENA_M_SHORT_E1_PROVENANCE.json` con **nueve Git blob SHA-1 originales** que se comprueban byte a byte en CI; no se reemplazó un compositor de Short por implementación ad hoc.
- `data/synthetic/arena_m_v0_visible.json` y tests adversativos que impiden datos de reserva o resultados ajenos en el brazo M.

La ejecución propia del compositor forma **seis grafos estructurales base** y **quince extendidos**, no quince mecanismos materiales identificables; algunos son equivalentes en comportamiento material para el observable final. El código registra `candidate_origin=PORT_ENUMERATION_NOT_OBSERVATIONAL_INFERENCE` y `candidate_selection=UNRESOLVED`.

## Ejecución y evidencia

La CI separada reproduce el archivo de origen, ejecuta sus tests de catálogo y sus controles negativos, traduce con backend Short E1 y simula **21 candidatos Modelica** (base + extendido) con **OpenModelica 1.26.5**, MSL v4.0.0 y SystemDynamics v2.1.2. Se verifica masa/no negatividad y series por el verificador E1 original. Los 21 registros no son 21 hipótesis seleccionadas ni evidencia de adopción de una topología real.

Las dependencias externas SystemDynamics 2.1.2 y ModelicaStandardLibrary 4.0.0 declaran en sus repositorios respectivos **BSD 3-Clause** en `LICENSE`. La CI revisa ese encabezado antes de ejecutar los modelos. Los sources originales de Short se conservan con procedencia `yudocyudoc/short` y no se atribuyen a Hines o a una librería de terceros por similitud conceptual; falta aún cerrar cualquier obligación específica de avisos/atribución si se redistribuye un paquete instalable con bibliotecas incorporadas. En este incremento las bibliotecas externas se descargan durante CI, no se incluyen sus fuentes dentro de IGC.

## Límites que siguen abiertos (no bloquear por pretender otra capacidad)

- M0 enumera estructuras **desde roles declarados**, no las descubre a partir de observaciones.
- M1/M2 exploraron un estímulo común y revisión; M3 añadió selección desde observaciones, y M3-P encontró **6/6 abstenciones bajo variación de parámetros**. Sus ensayos permanecen en PRs #28–#41 y no se integran por herencia de este PR.
- El generador M0 no debe leer modelos de D/B ni usar sus adaptadores. La conexión V0 común, realimentación por brazo, registro ATMS transversal, calibración paramétrica e identificación fuera de muestra se incorporarán aparte.
- No activar Clef C ni introducir una molécula nueva para forzar un `PASS`.

**Estado científico:** OpenModelica G2 con ingeniería molecular sintética, **G3 en Arena = NOT_RUN**. No hay identificación causal ni predicción externa. La adopción a `main` no equivale a publicar `v0.1.0`.
