# Histórico del laboratorio IGC

Este directorio conserva las campañas y pruebas retiradas del árbol operativo. **No son módulos activos ni deben importarse desde los productores D/B/M**. Sus rutas originales, blobs y commit de ejecución se preservan en [manifest_cafeteria_2026-11-02.json](manifest_cafeteria_2026-11-02.json).

## Primer corte archivado

- `campanas/cafeteria/pc01/` y `campanas/cafeteria/pc02/`: 137 archivos del `main` en `5e2b5505a9224effe1b5242a3af61663b53aaa5d`.
- `workflows/cafeteria/`: 50 definiciones de GitHub Actions correspondientes, retiradas de `.github/workflows/` para evitar ejecuciones históricas por defecto.
- Los PR Draft CAF-11–16, MC-01, EV-01 y EV-02 **no están fusionados** ni se incorporaron a este archivo. Se conservan como ramas/PR originales, sin fingir que pertenecen a `main`.

## Reproducción y límites

El archivo histórico registra el código, pero **no promete que los scripts antiguos corran desde estas rutas nuevas**: muchos imports, paths y workflows conservan supuestos de sus ubicaciones originales. Para reproducir una campaña, partir del commit inmutable `5e2b5505a9224effe1b5242a3af61663b53aaa5d`, utilizar su workflow/run original y sus artefactos. No reinterpretar una corrida antigua como evaluación prospectiva nueva.

La copia operativa `scripts/arena_physical/des_engine.py` posee exactamente el mismo Git blob `8cadbc1f9489c3e1cd7eecd020009978873822ba` que el motor `experiments/cafeteria/pc01/caf01_des_engine.py` del commit original. Cualquier evolución futura se realizará en la copia operativa; el archivo no se reescribe.

**Pendiente de otro corte**: clasificación y archivo de los experimentos R1–R4, B/M y sus pruebas/workflows con dependencias aún activas. No moverlos automáticamente ni duplicar los componentes nucleares `experiments/e0` y `experiments/e1` del brazo molecular sin promover antes sus contratos.
