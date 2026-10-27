# Recuperación de la arquitectura avanzada de Arena

La fusión selectiva hasta `main@def9166f73084f315b0f155ef32625dc6fb4f61d`
introdujo D2, M0, Buffalo inicial y evidencia común. No integró las capacidades
M1/M2/M3 ni las revisiones físicas B3/B4/B5 que ya se habían ejecutado en ramas.
El PR #51 añadía una ronda offline, pero seguía llamando a M0. No se perdió la
historia: faltaba promover y conectar esas fuentes.

Esta recuperación mantiene los tres métodos del plan v1.3. No añade un brazo,
un compositor ni un nuevo motor de simulación.

| Ruta | Capacidad recuperada | Límite que se conserva |
|---|---|---|
| D | Generador puro, D2 y G2 ya integrados; escritura Modelica con LF también en Windows | Parámetros y protocolo declarados; no superioridad científica |
| M1/M2 | Estímulo público, revisión con feedback propio y métricas G3 corregidas (#28–#31) | M2 revisa parámetros de su estructura anterior |
| M3 | Selección por observaciones y abstención (#35), conectada a la fuente común | Tres clases materiales; parámetros fijos; proyección semántica asumida |
| M3-P | Seis mundos con parámetros cambiados (#41) | Seis abstenciones históricas, no convertirlas en éxitos de identificación |
| Buffalo | Diagnóstico nativo, transporte de revisión y feedback B3/B4/B5 (#30–#40) | Helpers históricos fijados a B2/B4; no son revisión arbitraria de cualquier ronda |
| Discriminación | Pulsos D2/M2 y B2/B3 (#37/#38) | Separar predicciones no decide cuál mecanismo es verdadero |
| ATMS/memoria | Recuperación léxica/FTS5 y vistas D/B/M | Soporte lógico no equivale a adecuación empírica |
| Clef | Código y resultados de dos pilotos (#39) | Experimento; C continúa inactivo; no sustituye M3 |

## Correcciones de conexión

`arena_v0_first_round.py` llama ahora a `arena_m3_common.py`. Este adaptador
reutiliza `family()` y `decide()` de M3, el compositor y backend originales E1,
y el verificador material corregido. Recibe los tiempos y el pulso de la fuente
común, sin exigir los nombres alpha/beta ni fabricar los mundos del experimento.
El selector y protocolo históricos de M3 permanecen intactos.

La preparación entrega tres candidatos y Modelica; no selecciona antes de ver
las simulaciones. La evaluación usa tres CSV de esos candidatos y las
observaciones de construcción. Conserva los umbrales 0.020/0.035 y permite
abstención. Estos umbrales son una política recuperada, no límites instrumentales
demostrados para cualquier sistema nuevo. No se ajustan al resultado de esta ronda.

ATMS y memoria rechazaban B/M por una enumeración heredada D/S/P/B0. Se añaden
B/M al dominio de vistas manteniendo filtros por brazo, investigación y tiempo.
No se activan C ni acceso entre propuestas rivales.

## Uso sin inferencia de pago

Desde la raíz del repositorio:

```sh
python -m scripts.arena_v0_first_round --source data/synthetic/arena_v0_primary_construction.json --assumptions data/synthetic/arena_v0_declared_d_assumptions.json --out artifacts/common-prepared.json --m-modelica-dir artifacts/common-m3
```

Genera D y tres candidatos M, con B bloqueado. Para evaluar M, ejecutar primero
los tres Modelica con OpenModelica conservando el `manifest.json` y los `.mo`;
guardar las trazas como `c00_res.csv`, `c01_res.csv`, `c02_res.csv` en ese directorio:

```sh
python -m scripts.arena_v0_first_round --source data/synthetic/arena_v0_primary_construction.json --assumptions data/synthetic/arena_v0_declared_d_assumptions.json --m-csv-root artifacts/common-m3 --out artifacts/common-evaluated.json
```

El workflow `arena-recovered-capabilities.yml` realiza esa secuencia física y
reproduce además M3 y M3-P con OpenModelica 1.26.5, MSL 4.0.0 y SystemDynamics
2.1.2. Ningún job llama a Cloudflare. `solver_calls=0` en el registro del
orquestador significa que este proceso lee trazas existentes; el workflow
contabiliza sus ejecuciones separadamente (5 M3 + 6 M3-P + 3 comunes).

## Pruebas y fuentes

- `python -m unittest discover -s tests -p 'test_*.py' -v`: contratos y regresiones;
  F0 necesita las dependencias de `requirements-f0.lock.txt`.
- `node --test tests/test_*.mjs`: protocolo y diagnóstico Buffalo, sin inferencia.
- `tests/replay/`: pruebas originales que necesitan artefactos auténticos M1/B2.
  El job `archived-feedback` los descarga y verifica. Su ausencia hace fallar ese
  job; no se sustituyen por mocks ni se afirma un replay por pasar pruebas unitarias.
- `data/arena/recovered-sources-20261026.json`: PR, SHA y blob originales de cada
  archivo recuperado, incluidas las pruebas trasladadas al directorio de replay.
- Nueve blobs E1 siguen idénticos a la procedencia original de Short.

Los archivos de resultados recuperados conservan su fecha y su contexto histórico;
frases como «draft» describen la situación de sus PRs en aquel momento. Los permisos
de una sola llamada de aquellos ensayos no se importan ni se reutilizan.

## Trabajo que sigue pendiente

No se presenta esta recuperación como una campaña nueva completa D/B/M: B requiere
inferencia autorizada sobre la misma fuente; sus respuestas antiguas tenían otro
prompt. Tampoco se declara cerrado el ciclo común de segunda iteración de los tres
brazos, su persistencia conjunta en ledger, un holdout independiente ni un release.
Las rutas históricas y sus pruebas están disponibles para continuar desde lo ya
avanzado, en lugar de empezar otra vez desde M0/B1.

B5 mejoró respecto de B4 pero no superó B2/B3. M3-P mostró dependencia de las
plantillas paramétricas. Clef obtuvo mejores resultados conservadores en notas
operativas sintéticas que como sustituto de la evaluación numérica. Estos límites
se conservan como resultados, no como razones para rediseñar toda la arquitectura.
