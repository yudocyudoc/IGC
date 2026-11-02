# Dictamen técnico PC-01 / CAF-01 — revisión v0.3

**Fecha:** 28 de octubre de 2026. **Base de comparación:** archivos locales PC-01 v0.2 + código de `yudocyudoc/IGC@6f0ba57d175c10d31f762237287cb1e79cdaea41`, consultado en lectura. **Dictamen:** **DISEÑO REVISADO, NO PREINSCRITO NI LISTO PARA PC-02**. No se ejecutó ningún generador DES, OpenModelica, integrador D-RK4 de candidatos ni proveedor IA. No se modificó GitHub.

## 1. Qué se comprobó del paquete v0.2

- La validación original `validar_contrato_v0_2.py --tests` reproduce **8/8** pruebas estáticas. La coherencia de ese JSON **no demuestra** equivalencia nativa ni independencia de la fuente evaluadora.
- El traductor B histórico [requiere](https://github.com/yudocyudoc/IGC/blob/6f0ba57d175c10d31f762237287cb1e79cdaea41/scripts/arena_b_native_to_modelica.py) `start=0, stop=8, dt=.125 h, Euler`. Su vista [solo mapea](https://github.com/yudocyudoc/IGC/blob/6f0ba57d175c10d31f762237287cb1e79cdaea41/scripts/arena_b_native_series.py) dos stocks/dos flujos; ambos siguen **BLOQUEADOS** para un horizonte de 40 min sin adaptación delimitada y prueba de fidelidad. No es prueba de fallo científico del método B.
- El [adaptador M](https://github.com/yudocyudoc/IGC/blob/6f0ba57d175c10d31f762237287cb1e79cdaea41/scripts/arena_m_visible_pulse.py) acepta hasta 100 items/h y 8 h, pero su invocación histórica produce 4 h de salida; hay que establecer el horizonte local y el mapeo de puertos sin reescribir E1. El [catálogo](https://github.com/yudocyudoc/IGC/blob/6f0ba57d175c10d31f762237287cb1e79cdaea41/experiments/e0/catalog.json) admite `maxThroughput` entre .01 y 100/h, `responseTime` entre .1 y 5 h; la grilla v0.2 está **dentro de rango**, pero no está validada con el compositor/backend para sus nueve grafos.
- El [motor D](https://github.com/yudocyudoc/IGC/blob/6f0ba57d175c10d31f762237287cb1e79cdaea41/scripts/arena_d_v01.py) tiene hasta seis topologías, tres de ellas **con pérdida**. La v0.2 las proponía todas a pesar de declarar `losses_allowed=false`, `cancellations_allowed=false`. Esa contradicción es una **inadmisibilidad física conocida antes de observar la fuente**, no incertidumbre de parámetro: se retiran de las candidatas elegibles, sin editar gramática D ni declarar que esas topologías son universalmente malas.
- El [plan V3.0](https://github.com/yudocyudoc/IGC) exige **CAF-01 + CAF-N** en PC-02; v0.2 incluía `CAF_N` como fuera de alcance. La v0.3 prepara el control enmascarado dentro del mismo caso; no lo ha ejecutado.

## 2. Cambios de propuesta entre v0.2 y v0.3

| Aspecto | v0.2 | v0.3 revisada |
|---|---|---|
| D admisible | 6 grafos, con y sin pérdida | **3 grafos sin pérdida**; los otros 3 excluidos por frontera conocida |
| D, integración RK4 | 36 de construcción | **18 CAF-01 + 18 CAF-N = 36** |
| D, OpenModelica | 6 construcción + 6 evaluación | **3 + 3 = 6** |
| M, OpenModelica | 9 + 9 | **9 + 9 = 18**; parámetros aún pendientes de linter |
| B, OpenModelica | 1 + 1 | **1 + 1 = 2**, sujeto a adaptador local; CAF-N no usa OM |
| OpenModelica total | **32** | **26** (13 construcción + 13 evaluación) |
| Buffalo, solicitudes IA | 1 | **2 propuestas**: una CAF-01 y una CAF-N independiente; no autorizadas |
| Generador DES | 2 | **2** (no se genera otro mundo para CAF-N) |
| REF-CAF | podía usar A_real en calibración | **solo pulso prescrito + D(t)** de construcción; A_real visible en sidecar para auditoría, no privilegio de REF |
| Eventos DES | tasa y discretización ambiguas en frontera | **t_j=(j+½)/λ**, t<20 min; exactamente 24/30 aceptaciones; desempate sigue por sellar |
| CAF-N | fuera de alcance | misma fuente con lecturas intermedias de D/P retiradas; sin simulador nuevo |

**Precauciones adicionales:** el REF-CAF de la v0.3 exige **al menos dos intervalos de 5 min** con pendiente ideal proxy `A_design-D>1` pedido en ambos extremos, para evitar confundir un empate/medio pedido con saturación. Esto **no identifica** capacidad física real. Si no hay intervalos, REF-CAF **se abstiene**. REF-SCALE conserva el factor 1.25 y solo utiliza D de construcción, sin respuestas nuevas.

La fuente DES sigue como **especificación incompleta**: no están fijados los tiempos/etapas de servicio, desempates de eventos, condiciones de ejecución y custodia de la verdad privada. Proponer una regla de llegada no crea ni audita un generador físico. Separación de implementación tampoco demuestra independencia conceptual.

## 3. Compuertas de ejecución

| Compuerta | Estado | Evidencia requerida antes de PC-02 |
|---|---|---|
| G0 Contrato, unidades, contabilidad y pérdidas | **ESTÁTICA APROBADA / v0.3** | Conservar SHA del contrato al congelar |
| G1 Calendario DES, servicio y etiqueta privada | **BLOQUEADA** | Implementación independiente y especificación privada sellada antes de construcción, con prueba de conservación/intervalos |
| G2-D Tres grafos sin pérdida y grillas | **REGLA REVISADA, NO NATIVE-PREFLIGHT** | Validación de `validate_case`, D1 y política de selección/abstención sin usar observación evaluativa |
| G2-M Nueve modelos E1 | **SOLO DENTRO DE COTAS DEL CATÁLOGO** | Linter/compositor/backend real, 3 clases×3 capacidades, puertos, salida y horizonte local |
| G2-B Traducción temporal y series | **BLOQUEADA** | Adaptador local de `stop=2/3, dt=1/120, Euler`; paridad nativa sin modificar ecuaciones; bloqueo limpio de grafos desconocidos |
| G3 Pronósticos y custodia | **NO REALIZADO** | Selección congelada, outputs y hashes antes de abrir mundo futuro |
| G3-N Negativo CAF-N | **DISEÑADO, NO EJECUTADO** | Máscara validada, ausencia de filtración, una llamada B independiente presupuestada |
| G4 REF y métricas | **REGLAS ESTÁTICAS PROBADAS** | Implementación contra datos de construcción genuinos; no datos secretos |
| G5 Autorización de PC-02 | **NO OTORGADA** | Presupuesto final y aprobación explícita de DES, OM, RK4, IA y aislamiento |

El siguiente trabajo técnico **no es otra campaña de investigación**: son tres preflights locales que pueden fallar limpiamente (D 3 grafos, M 9 composiciones, B traductor/series local) y una especificación generadora DES sellable **sin producir todavía datos**. Si alguno falla, hay que registrar el bloqueo en PC-01; no ampliar por defecto la arquitectura ni ajustar resultados privados inexistentes.

## 4. Pruebas efectivamente ejecutadas

Se creó `validar_pc01_v0_3_offline.py`; sobre el contrato v0.3 produjo **14/14 pruebas de validación de diseño**. Incluye negativa a pérdidas D, falso presupuesto de OM, falta de CAF-N, segunda llamada B omitida, privilegio de datos para REF, tasa excedida M y autorización prematura; comprueba conversiones y eventos con aritmética racional, además de referencias **con valores ficticios de prueba**, no con observaciones de cafetería.

**No se ejecutó `arena_d_v1_screen.assess` ni `composer.check_graph`/`backend.render_model` reales, `omc`, DES o un modelo IA.** Por tanto **no declarar** superados los preflights G2 nativos. La ejecución del validador es una prueba de lógica documental, sin evidencia experimental.

## 5. Dictamen para Astra / coder

**Aprobar como corrección de preparación v0.3, no como protocolo experimental congelado.** En ningún caso interpretar «14 pruebas» como 14 mundos o como prueba de transferencia. No elevar el presupuesto por su propia cuenta. No fusionar los scripts exploratorios de este paquete al repo sin revisión; el material se entrega localmente para discusión.
