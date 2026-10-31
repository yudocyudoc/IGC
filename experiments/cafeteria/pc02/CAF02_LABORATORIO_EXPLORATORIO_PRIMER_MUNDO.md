# CAF-02 — Primer laboratorio DES exploratorio de extremo a extremo

**Fecha:** 2026-10-30. **Estado:** PR de **ejecución exploratoria pública**, no ensayo ciego, confirmatorio ni campaña con testigo.

## Objetivo

Reducir trámites y obtener resultados: producir un resultado real de **simulación DES** frente a los **dos métodos M y D**, aplicando sin cambios el menú K1, la revisión ±0.77, las envolventes K2, la pérdida de conjuntos y las abstenciones ya implementadas. Un solo comando, sin firmas externas.

```bash
python experiments/cafeteria/pc02/caf02_lab_exploratorio.py \
  --out artifacts/mi-primera-cafeteria
```

No se requiere instalar OpenModelica ni ningún proveedor. Las 15 simulaciones G2 nativas del PR #107 permanecen como evidencia de correspondencia **separada**; no se repiten ni se gastan nuevas llamadas OMC.

## Configuración DES elegida antes del resultado

El mundo **LAB_WORLD_A_v1** es explícito, legible y está fijado directamente en `caf02_lab_exploratorio.py`:

| Estación | Servidores | Tiempo por pedido | Capacidad nominal |
|---|---:|---:|---:|
| Preparación | 2 | 1.5 min | 80 pedidos/h |
| Despacho | 1 | 0.75 min | 80 pedidos/h |
| Entrega | 2 | 1.5 min | 80 pedidos/h |

Cada etapa tiene una capacidad nominal idéntica, pero la **variabilidad de los pedidos individuales y la sincronización de servidores** generan colas distintas de las ecuaciones continuas de M y D. Tiempo de servicio determinista, sin cancelación, tres etapas, todos los stocks vacíos al inicio. Cuello de botella nominal **80 pedidos/h (4/3 pedidos/min)**. Este mundo **no fue seleccionado mirando K0, K1 o K2**. Sí comparte con M/D la hipótesis de estaciones en serie; no hay independencia causal completa.

El mundo y todos los parámetros se guardan en `00_MUNDO_PUBLICO.json`; no hay secreto, nonce ni G5 real. La referencia SHA empleada por la interfaz es **un identificador reproducible del mundo público**, no un testigo.

## Secuencia del único ejercicio

1. Ejecutar el motor discreto con **K0, 1.2 pedidos/minuto durante 20 min**, a partir de cero. Publicar solamente entregas t5 y t10.
2. Enviar esos **dos enteros**, y nada más del DES, a `create_g4a_candidate`. Guardar **todos los candidatos M/D**, la decisión K1 conjunta y las envolventes previas K2.
3. Si existe al menos un candidato admisible, ejecutar el único **K1 seleccionado automáticamente por el algoritmo ya fijado**. Observar solo su entrega preseleccionada. Guardar `create_g4b_candidate` con revisión **sin recalibración**.
4. Guardar y sincronizar **G4a, G4b y todos los pronósticos K2 previos/posteriores** en archivos exclusivos. Un checkpoint contiene hashes locales y dice expresamente que **K2 aún no se ha calculado**.
5. **Solo después** llamar una vez al motor DES con **K2, 1.35 pedidos/minuto durante 20 minutos**. El resultado reservado tiene exactamente seis entregas enteras en t5,10,15,20,30,40.
6. Aplicar el mismo cálculo de pérdida y abstención para M y D, y las referencias REF_CAF/REF_SCALE **solo K0**; generar tabla CSV, informe Markdown y manifiesto de hashes.

El conjunto de archivos (00–11) distingue evidencia, pronósticos previos, verdad K2 y puntuación. **El orden de escritura es real y probado**, pero la garantía es **local, no una custodia independiente**. El código nunca convierte `external_custody_verified` en verdadero.

## Resultados que deben aparecer en el informe

- Conteos públicos K0 (D5/D10), opción K1 elegida y conteo observado o razón para omitir K1.
- Familias y **número de candidatos** compatibles antes/después de K1, por separado para M/C00-C01 y D/D1-D3.
- Seis entregas DES K2 y las envolventes que M/D habían escrito **antes** de ver K2.
- Pérdida `L_set` anterior y posterior, cambio `L(K0)-L(K1)`, mejora descriptiva si ≥0.25 pedidos, abstenciones sin error falso de cero, amplitud/MAE si elegible.
- Referencias K0-only, sin afirmar igualdad de información con M/D post-K1.
- Número de corridas exploratorias: **2 si K1 no se elige, 3 si sí se elige**. Cero DES de campaña confirmatoria, cero OMC y cero proveedores.

El informe es **un resultado de simulación sintética en un mundo público concreto**. Si ambos métodos fracasan o se abstienen, se informa igual. Si encontramos un bug, modificamos el código con un PR y ejecutamos una **nueva iteración exploratoria**, sin reetiquetar la anterior.

## Pruebas mínimas de integridad sin burocracia

`test_caf02_lab_exploratorio.py` verifica que el primer intento K2 **no puede comenzar** sin pronósticos y checkpoint durables en disco, que una interrupción antes de K2 no produce verdad K2 ni resultados y que una carpeta anterior nunca se sobrescribe. Un segundo test examina los números y el CSV; todos los resultados se guardan como artefacto GitHub Actions descargable.

La política confirmatoria `CAF02_INDEPENDENT_K0K1K2_POLICY_PROPOSAL_2026-10-30.json` sigue declarada **no autorizada**. Este laboratorio se habilita solo para un escenario **público y explícito**, mediante una función nueva. No abre `execute_private_trial()`, `authorize_K2_reveal()` ni `authorize_world_execution()`. No hace afirmaciones de ATMS persistida.

**Después de este informe** tendrá sentido decidir entre explorar dos o tres mundos con distintas capacidades o formular una validación externa; no anticiparlo con nuevas ceremonias.
