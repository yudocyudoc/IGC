# IGC — laboratorio de Dinámica de Sistemas

**`main` es la base integrada y conservadora.** A fecha de octubre de 2026 contiene un vertical F0 sintético, el ledger local F1a y contratos iniciales. La plataforma IGC y la Arena **no están completas**: [estado detallado](STATUS.md).

## Camino de construcción actual

Arena V0 seguirá tres métodos **independientes** de propuesta de hipótesis: **D** (determinista), **B** (metodología SD-AI de Buffalo) y **M** (molecular). Los tres desembocarán en OpenModelica por adaptadores independientes. ATMS deberá conservar hipótesis, soportes y revisiones a lo largo de iteraciones; no será un mero selector lógico. **Clef** se evaluará más adelante como **cuarto brazo**, sin alterar retroactivamente el experimento con tres.

- [Plan rector v1.3](docs/ARENA_IGC_ATMS_PLAN_IMPLEMENTACION_V1_3_2026-10-25.md)
- [Inventario de consolidación P0](docs/ARENA_P0_BASELINE_2026-10-25.md)
- [Contrato independiente V0.0](docs/ARENA_V0_CONTRACT.md)
- [Decisiones de arquitectura](ARCHITECTURE_DECISIONS.md)

```bash
python -m unittest discover -s tests -p 'test_arena_v0_contract.py' -v
```

**Alcance de ese comando:** comprueba aislamiento de estructuras de datos y contratos sin inferencia ni simulación. No prueba un brazo funcional, aislamiento real de reserva, ATMS de producción ni validez científica.

Los trabajos FM-A/FM-B, ATMS y GLM de PRs apilados siguen **preservados como historia y fuente de reutilización**; no se incorporan a `main` sin revisión por módulo. No eliminar ni rebasar esas ramas para «limpiar» la historia.
