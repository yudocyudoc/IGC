# ARENA · Cafetería V3.0 / PC-01: punto de entrada para revisión

**Estado:** `PC-01/0.3 — REVISIÓN, NO CONGELADO, NO AUTORIZADO PARA CAF-01`. Este directorio conserva los archivos **originales**, no una reconstrucción editorial de su contenido. Los hashes de los cinco documentos del paquete están en [MANIFIESTO_PAQUETE_PC01_v0_3.json](MANIFIESTO_PAQUETE_PC01_v0_3.json). El manifiesto refleja el instante de **creación** del paquete local (por ello informa `repo_changes: 0`); esta publicación documental posterior no transforma retrospectivamente esa declaración histórica.

## Documentos rectores

- [Plan de campaña cafetería V3.0](../../../docs/ARENA_PLAN_CAMPANA_CAFETERIA_V3_0_2026-10-27.md): prioridad, alcance, restricciones, PC-01→PC-05 y compuertas.
- [Hoja de ruta V2.0](../../../docs/ARENA_IGC_HOJA_DE_RUTA_V2_0_2026-10-27.md) y [plan operativo V2.0](../../../docs/ARENA_IGC_ATMS_PLAN_IMPLEMENTACION_V2_0_2026-10-27.md): **antecedentes históricos**, no reactivar R1–R5.

## PC-01 v0.3 — fuentes de trabajo

- [Protocolo v0.3](ARENA_PC01_CAF01_PROTOCOLO_REVISION_v0_3_2026-10-28.md)
- [Contrato JSON v0.3](ARENA_PC01_CAF01_CONTRATO_REVISION_v0_3_2026-10-28.json)
- [Dictamen técnico v0.3](DICTAMEN_TECNICO_PC01_v0_3_2026-10-28.md)
- [Validador offline v0.3](validar_pc01_v0_3_offline.py)
- [Log histórico de 14 pruebas](PC01_V03_TESTS_OFFLINE_2026-10-28.log), **no es una ejecución en GitHub**
- [Contrato v0.2 conservado](ARENA_PC01_CAF01_CONTRATO_CORREGIDO_v0_2_2026-10-28.json), necesario para la prueba de integridad histórica del validador.

### Reproducir la validación estática

Desde la raíz de `IGC`, sin servicios ni OpenModelica:

```bash
python experiments/cafeteria/pc01/validar_pc01_v0_3_offline.py --tests
```

Las 14 pruebas comprueban **únicamente coherencia del contrato y del presupuesto**. No certifican paridad Buffalo, composición nativa M, fuente DES, selección de pronósticos ni validez externa. El validador conserva el hash fijo del JSON v0.2 para impedir alteraciones retroactivas.

### Orden de revisión para Astra

1. Contrastar los documentos v0.3 con `main` o con el SHA base `6f0ba57d175c10d31f762237287cb1e79cdaea41`. El SHA base indica **código histórico inspeccionado**, no que los documentos v0.3 ya hubieran estado publicados entonces.
2. Confirmar unidades y presupuesto separados: **D 36 RK4**, **D 6 + B 2 + M 18 = 26 OpenModelica**, **2 mundos DES**, **hasta 2 inferencias Buffalo**, **todos pendientes de autorización futura**.
3. Marcar cada compuerta: `B_LOCAL_PARITY`, `M_NATIVE_LINT`, `DES_SEAL`, `PARAMETER_APPROVAL`, `PREDICTION_SELECTION_LOCK`, `BUDGET_AUTHORIZATION`. Identificar fallo reproducible, corrección mínima y prueba de aceptación; no proponer cambio arquitectónico sin demostrar bloqueo real.
4. Verificar REF-CAF contra REF-SCALE ×1.25, ausencia de doble puntuación de pendientes y alcance exacto del control negativo CAF-N.
5. Emitir `PC01_APPROVABLE`, `PC01_APPROVABLE_WITH_CONDITIONS` o `PC01_NOT_APPROVABLE`, **sin ejecutar CAF-01 ni publicar verdad del generador**.

**Prohibido para esta revisión:** inferencias de proveedor, mundos DES, simulaciones experimentales OpenModelica, ajustar umbrales tras evaluación, reabrir R1–R5, incorporar Clef como filtro, implementar producto o declarar CAF-01 congelado.

**Dependencia documental todavía no disponible en esta publicación:** el `ARENA_BRIEF_ASTRA_OPCIONES_IMPLEMENTACION.md` citado por V3.0 no se encontró en el corte de GitHub revisado ni entre los archivos locales proporcionados. No inventar ni completar su contenido. Se necesita solo para la futura decisión PC-05, no para validar las compuertas técnicas de PC-01.
