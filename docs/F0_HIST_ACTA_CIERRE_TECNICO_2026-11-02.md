# F0-HIST · Acta de verificación técnica y entrega a revisión

**Fecha:** 2026-11-02  
**Alcance:** exclusivamente F0-HIST, dentro de F0 del plan de cafetería v3.2.  
**PR:** https://github.com/yudocyudoc/IGC/pull/134  
**Base `main` contrastada:** `5e2b5505a9224effe1b5242a3af61663b53aaa5d`  
**Commit del código y manifiestos sometido al último ciclo CI:** `8b5b6fd5df2f9bce9a530729fefabdfab5869552`.  
**Estado de aceptación:** integridad comprobada; aceptar ingeniería **solo con CI completa sobre el commit probado y revisión humana previa a merge**. Esta acta documental no equivale a aprobación humana.

## Comprobaciones efectuadas

1. **Archivo físico:** 187 elementos trasladados (137 archivos CAF-01/02 y 50 workflows), sin duplicados de origen/destino; el árbol Git conserva los 187 blob SHA declarados en `historico/manifest_cafeteria_2026-11-02.json` y no mantiene sus rutas activas originales. Reproducción histórica por commit anterior, no ejecutando imports bajo `historico/`.
2. **DES original:** `scripts/arena_physical/des_engine.py` conserva exactamente el blob `8cadbc1f9489c3e1cd7eecd020009978873822ba`. El fixture de conservación es regresión de ingeniería.
3. **EV-01/EV-02:** los dos núcleos `arena_event_observability.py` y `arena_operational_ingestion.py` son copias con SHA idéntico a sus fuentes. Los tres módulos operativos y **las tres pruebas recuperadas** tuvieron cambios acotados de imports/rutas. La comparación de las tres pruebas con `experiment/arena-ev02-ingestion-provenance-20261101@c534203f99405044dc79cae38e6102520f4ae2eb` mostró **únicamente sustituciones de imports**. Sus etiquetas erróneas «original blob copied» fueron corregidas en `historico/manifest_ev_recovery_2026-11-02.json` a `relocation+minimal import rewiring`.
4. **Frontera de código activo:** inspección estática de 41 workflows, 83 archivos de `scripts/`, 47 de `tests/` y 11 de `experiments/` en el árbol previo a esta acta (182 archivos). No aparecieron dependencias operativas de las rutas CAF-01/02 retiradas; las menciones registradas son de procedencia o controles negativos. `tests/test_f0_historico_active_boundary.py` deja una regresión permanente sobre rutas/imports archivados y comprueba que cada etiqueta de copia idéntica del manifiesto EV corresponde realmente a su blob.
5. **Fuentes D/B/M y memoria:** el diferencial del PR hasta el corte auditado contiene traslados y adiciones, sin reescritura de las fuentes originales D, Buffalo o Short E1 ni de OpenModelica, ledger/ATMS. La prueba `tests/test_arena_native_provenance.py` protege los orígenes nativos; no certifica que F3 esté ejecutado.
6. **Custodia:** `ev01.SPEC` contiene física privada del generador de control. No es una vista autorizada para D/B/M. La recuperación no implementa el aislamiento O0/O1 de F1–F3, ni simula confidencialidad sobre ese contenido.

## CI que debe acompañar el dictamen

Ejecuciones del corte `8b5b6fd`:

| Comprobación | Run |
|---|---|
| Archivo, DES, prueba de frontera y fidelidad de manifiesto EV | [41532835651](https://github.com/yudocyudoc/IGC/actions/runs/41532835651) |
| Regresiones EV-01/EV-02, PM4Py y procedencia D/B/M | [41532835463](https://github.com/yudocyudoc/IGC/actions/runs/41532835463) |
| Buffalo R2 preflight, sin llamada live | [41532835604](https://github.com/yudocyudoc/IGC/actions/runs/41532835604) |
| Capacidades recuperadas Arena, incluido M3/OpenModelica | [41532836066](https://github.com/yudocyudoc/IGC/actions/runs/41532836066) |
| F0 synthetic spike | [41532835503](https://github.com/yudocyudoc/IGC/actions/runs/41532835503) |

Verificar conclusiones de **todas** esas ejecuciones antes de promover el PR. Una CI ejecutada sobre un commit anterior **no valida automáticamente** un HEAD posterior; una edición documental posterior se identifica como tal. El checkout de Actions puede ser el ref sintético del PR, distinto de `head_sha`; no sustituir uno por otro.

## Gates de aceptación sin ambigüedad numérica

| Gate material | Resultado |
|---|---|
| Identidad de archivo y ausencia de rutas originales | PASS verificado |
| Identidad DES y conservación | PASS verificado |
| Procedencia veraz de copias/adaptaciones EV | PASS verificado en árbol y regresión |
| Ausencia de referencias operativas retiradas | PASS, cobertura estática declarada |
| Regresiones técnicas pertinentes en CI | Sujeto al resultado de las cinco ejecuciones listadas |
| Revisión humana de alcance y decisión de merge | **PENDIENTE**; ninguna prueba automatizada puede sustituirla |

**Nota de numeración:** la descripción inicial del PR y `docs/F0_HIST_PROMOCION_POR_COPIA_2026-11-02.md` usan etiquetas HIST-03/04 de manera distinta. Esta acta identifica gates por contenido y no presume equivalencia de numerales.

## Lo que expresamente NO se declara

- No se ha cerrado F0 completo (`BASELINE-01`) ni iniciado F1/F2/F3 por este documento.
- No existen nuevas inferencias de D/B/M sobre O0/O1, una llamada Buffalo live ni un nuevo G4/G5.
- No se ha probado identificabilidad, utilidad empresarial, minería de procesos incremental ni un modelo de cafetería real.
- No se han clasificado/retirado todos los demás experimentos R1–R4, B/M y Short; **no son requisito para el corte A** salvo una dependencia concreta.
- No se autoriza merge automático. La revisión humana y los checks vigentes del HEAD gobiernan la decisión.

**Siguiente trabajo una vez aceptado F0-HIST:** F0 del plan v3.2 (`00_BASELINE_MANIFEST.json`, `00_DEPENDENCIAS.md`, `00_EVIDENCE_MATRIX.md`), seguido del mapa F1 de evidencia efectiva O0/O1 y consumidores D/B/M, sin reabrir la limpieza global.
