# ARENA-MC-01 — Contrato previo para cuatro capas, SIN REJILLA PARAMÉTRICA

**Fecha:** 2026-11-01 (México). Primer commit obligatorio de esta implementación, ANTES de escribir código o de evaluar datos. **Rama Draft apilada** sobre CAF-16 PR #129; su head heredado `bc9546dea5d2afa77ceac602089478099f6e14ec`. No fusionar ni alterar CAF-11..CAF-16, Arena D/B/M, ledger, ATMS ni motor DES.

## Autoridad y rectificación explícita

La fuente metodológica es el informe adjunto *Identificación robusta de mecanismos en sistemas dinámicos parcialmente observados* (archivo local `deep-research-report (1).md`); no confundir con el informe general *Estado del arte de la automatización de Dinámica de Sistemas mediante IA* (archivo `deep-research-report.md`). Se adopta la **arquitectura conservadora**: familias estructurales discretas, **dominios de parámetros CONTINUOS**, set-membership, falsificación separada y selección condicionada al objetivo científico. **La rejilla NO ES REPRESENTACIÓN DEL ESPACIO DE HIPÓTESIS.** El catálogo 24 puntos de CAF-10 y 720 puntos de CAF-15A/16 son antecedentes y baselines históricos; prohibidos como método de inferencia o fallback del nuevo núcleo.

No se «eliminan» estructuras finitas: existen seis familias estructurales CAF (P,D,E,P+D,P+E,D+E), no 24 modelos puntuales y no 720 capacidades. Por familia 1 o 2 parámetros de duración/capacidad **racional CONTINUA** (intervalo cerrado [55,110] pedidos/h por etapa limitada, `d=60/c∈[6/11,12/11]` minutos por pedido), con etiquetas/orden explícitos. La cantidad seis solo corresponde al adaptador CAF; el núcleo no sabe qué es una cafetería.

## Interfaces y dependencias reales

- Núcleo general en `scripts/arena_methodology_continuous.py`: objetos tipados de familia, dominio, observaciones, modelo de error, cotas; un backend `bounds(family,box,program)` que entrega intervalos **externos garantizados**, y `predict(family,point,program)` que da firma exacta. El núcleo no importa CAF ni PySD ni Modelica, no permite usar una malla.
- Adaptador de alcance inicialmente restringido `experiments/cafeteria/pc02/arena_mc01_caf_adapter.py` que conecta **sin duplicar matemática** `CAF15B.bounds` y `CAF15B.signature`, y el análisis a priori `CAF15B.run_pair`. Soporta inicialmente K0+K1+seis conteos de colas/stock a t20 o t25 bajo pulso sintético 150/h, **sin generalizar** a otras dinámicas, errores o observaciones arbitrarios.
- No implementar un nuevo motor físico; reutilizar la recurrencia y las cotas exactas existentes. No ampliar a matrices gigantes de modelos, ni optimizador aleatorio, SINDy, IA, Bayes, Z3, PySD o Modelica sin evidencia de necesidad. Mantener interfaces/puertos para conexión futura de D/B/M y ATMS, pero **no afirmar integración que no se ha implementado**.

## Las cuatro capas y estados científicos

**Capa 1 (a priori):** contrastar parejas estructurales sobre el dominio continuo por criterio de confusibilidad de firmas con ±1, usando el certificador CAF-15B ya aprobado. Salida: `PAIR_SEPARABLE_CERTIFIED`, `PAIR_CONFUSABLE_WITNESS_CERTIFIED` o `PAIR_UNRESOLVED`; preserva testigos/certificados y supuestos del programa. No equivaler este resultado a inferencia de un mundo observado.

**Capa 2 (set-membership continuo):** para observación fija `y` y error entero por canal acotado `±1` (es solo un supuesto sintético no calibrado), la región matemática es
`F_M(y)= {d∈[6/11,12/11]^k : max_j |predict(M,d)_j - y_j| <= 1}`.
Debe existir como PREDICADO EXACTO, independientemente de materializar una aproximación. El motor computa una **sobreaproximación certificada por cajas racionales** con branch-and-bound, y opcionalmente puntos racionales testigo en el conjunto factible; no llamar al conjunto de cajas «región factible exacta». Para cada caja, usar `bounds` externos por canal; excluirla solo cuando algún intervalo esté disjunto de `[y−1,y+1]`. Si quedan cajas sin poder excluir, preservarlas aunque no haya testigo; NO interpretar ausencia de testigo como conjunto vacío. Todas las cajas se mantienen cerradas, división en punto medio racional con cobertura completa. No existe parámetro fijo ni grid, solo búsqueda adaptativa certificable sobre intervalos continuos.

**Capa 3 (falsificación):** `CERTIFIED_EMPTY` solo si todas las cajas del dominio fueron excluidas de manera comprobable; `WITNESS_FEASIBLE_WITH_OUTER_COVER` si hay al menos un punto exacto compatible y se conserva cubierta externa; `UNRESOLVED_WITH_OUTER_COVER` en otros casos. Interpretación de todos los vacíos: `KNOWN_FAMILIES_INADEQUATE_UNDER_DECLARED_MODEL_AND_ERROR`, jamás «nueva topología demostrada» ni «cuarta etapa detectada». Una sola estructura con testigo no es certidumbre ontológica; todas las rivales deben quedar **CERTIFIED_EMPTY** para unicidad CONDICIONAL al catálogo completo supuesto.

**Capa 4 (decisión de observación):** presentar alternativas de programa `F_R25_T20` y `F_R25_T25` (mismos datos K0/K1 y sensores completos), e información de separabilidad a priori solo cuando se haya certificado. Como no existe costo de medición ni acceso a ventanas naturales de demanda verificado, **PROHIBIDO** generar ranking de intervención, prescribir 150/h o usar una política `argmin` sin costos. Estado `DESIGN_NOT_OPTIMIZABLE_MISSING_COST_AND_FEASIBILITY`; solo el estudio de escritorio es permitido.

## Presupuesto, pruebas, falsadores

- Solver continuo para cada clase con límites predeclarados `MAX_BOX_NODES=256`, `MAX_DEPTH=14`; se reportan límites por familia y resultados indeterminados; NO inflar presupuestos tras ver las respuestas. Evaluar en fixtures SOLO de alcance determinista y sobre observaciones exactas generadas por `CAF15B.physical_signature` con capacidades racionales **69/h**, **101/h** (fuera del banco viejo) y topología control de cuarta etapa 220/h. Son pruebas de REGRESIÓN de semántica, **no** nuevo holdout externo ni piloto. 
- Para evitar testigos sesgados, probar puntos deterministas: esquina inferior/superior y centro racional de cada caja. NO declararlos como rejilla de hipótesis; la exclusión es la que usa intervalos. Si se encuentra testigo positivo, guardar punto y firma, sin inferir región interior positiva alrededor de él. 
- Las cotas en CAF15B de colas/stock deben contener todas las lecturas en muestras racionales de estrés, incluidas fronteras y empates. El adaptador debe comprobar firma exacta contra DES nativo en pruebas, y el solver debe preservar el testigo fuera de los valores CAF15A.
- **Verificador separado de decisiones del branch-and-bound:** reejecuta desde la caja raíz todas las divisiones y exclusiones y comprueba **que ningún intervalo se eliminó sin prueba**; para no resueltos, confirma que la unión de hojas excluidas + hojas retenidas cubre el dominio. Nunca declarar una exclusión sin verificación satisfactoria. Test manipulado debe fallar.
- Falsadores de arquitectura: clases exactas fuera de rejilla se pierden; conjunto vacío no distingue dato/modelo/cota; un resultado desconocido se eleva a topología demostrada; selección de observación sin costos; `TRUE` de clase no pasa el backend; datos de mundo oculto entran a capa de inferencia.
- Pipeline de regresión de cuatro capas (no performance como objetivo): `00_PLAN.json` firmado ANTES de evaluar, `01_RESULTADOS.json`, `02_INFORME.md`, `03_MANIFIESTO.json` SHA256 y CI con unit tests + verificador, registro head y checkout separados. Sin reescribir históricos.
- Gate permanente `BLOCKED_METHOD_CONTRACT_SYNTHETIC_DES_UNCALIBRATED_ERROR_NO_REAL_DATA`. PR Draft sin merge, revisión adversativa antes de enlazar automáticamente D/B/M, ATMS u operaciones reales.

## Qué explícitamente NO resuelve este PR

No genera una región continua exacta en forma cerrada para dos capacidades, no garantiza completar todos los problemas de set-membership (puede quedar `UNRESOLVED`), no identifica cualquier familia arbitraria sin backend de cotas certificado, no calcula posteriors, no calibra error de sensor, no implementa la decisión óptima con costos y no demuestra validez externa. La integración completa de cuatro capas queda definida, con un primer vertical slice CAF y puertos de backend. No venderla como herramienta general acabada.
