# FM-A · Auditoría de activos y factibilidad

**Estado:** evidencia de inspección para FM-A; no es admisión de biblioteca ni `PASS` de integración.
**Base de IGC:** PR #6 HEAD `88b181cd85b5d96a3686acf695ec45cc05600a98`; rama `fm-a-molecular-contract`.
**Auditoría de `short`:** referencias obtenidas el 2026-10-20; no se copió código de ese repositorio.

## 1. Decisión de autorización

La instrucción del investigador «implementa, armonizando la tensión» autoriza **FM-A** y una rama/PR draft apilada sobre PR #6. No autoriza FM-B, merge de PR, rebase/retarget de #5/#6, gasto cloud ni el desarrollo de moléculas o políticas nuevas. Para FM-B siguen reservadas las decisiones sobre pareja de candidatos, ampliación de catálogo y revisión independiente.

## 2. Activos inspeccionados

| Referencia | Commit observado | Evidencia inspeccionada | Límite / decisión FM-A |
|---|---|---|---|
| `short` PR #20 | `9794c01f56f8be65fc8da16f9443eeabf4134beb` | `docs/IGC-SL-grammar-v0.1.md` | Gramática documental; no es parser ni compilador. Reutilizar vocabulario con adaptación crítica. |
| `short` PR #32 | `eef3c38799f19d9526c8b81097ec0483d802dc15` | `src/modelica/IGCMolecules.mo`, `src/modelica/IGCInformationMolecules.mo`, `FOUNDATION.md` | `AcceptedSource`, `BoundedQueue`, `DeliveryCounter` y `FirstOrderReportFilter`. La fundación reporta simulación en el CI de `short`, pero este código aún no se compiló ni simuló en el runner fijado de IGC. |
| `short` PR #33 | `d5a9512e69b8e1f59ae1ea13c0e6fdb8c9472e72` | catálogo E0 | Los roles y puertos hacen explícito el tipado semántico; no implica que RealInput/RealOutput de Modelica tengan tipos semánticos nativos. |
| `short` PR #34 | `97a9ad3a3e13d5b04d85340a0907994e41c13518` | `experiments/e1/composer.py`, `backend.py`, registros y `CONTRACT.md` | Composición acotada por catálogo; cadenas materiales y rutas de señal. La evidencia histórica no se vuelve a ejecutar en FM-A. |
| `short` PR #39 | `f4bf572d47de760ae0120af008e4c65b3f7b4233` | sonda P1 y documentación | Casos de frontera/adversariales; no se admite como ejecutor de red. |
| `short` PR #40 | `9f9d9753bd5710fb3678ad13af9ed7b7755f4831` | `experiments/p2/linter.py`, `registry_conceptual.json`, pruebas y README | IR/linter conceptual. El propio README limita el resultado a `executable:false`; no trasladar esa etiqueta como admisión física.

### Estado de licencia y procedencia

En los árboles revisados de #32–#40 no aparece un archivo raíz `LICENSE` o `COPYING`. `short/FOUNDATION.md` atribuye los wrappers `IGCMolecules.mo` e `IGCInformationMolecules.mo` a migraciones literales desde los PR #25 y #29 del mismo proyecto; el historial identifica commits bajo la cuenta del investigador. Esto respalda una hipótesis de autoría/procedencia del proyecto, pero por sí solo **no acredita titularidad ni autorización jurídica** sobre cada archivo. Se mantiene `NOASSERTION / NOT_CLEARED` hasta que el investigador confirme expresamente que controla los derechos de esos wrappers y autoriza su reutilización en IGC, o aporte otra base de permisos. No se copia ni importa código en FM-A. Las dependencias SystemDynamics/MSL y cualquier otro componente de terceros requieren revisión de licencia separada; la eventual declaración sobre wrappers no las cubre.

## 3. Interfaces y capacidades observadas

| Pieza | Puertos / parámetros observados | Capacidad que sí declara la fuente | Lo que no queda probado para IGC |
|---|---|---|---|
| `AcceptedSource` | `externalRate` entrada; `outflow` salida | Traduce una tasa externa a flujo de llegada. | Validez de la tasa, procedencia de medición y admisión en el lock IGC. |
| `BoundedQueue` | `arrival` entrada; `completed` y `waiting` salidas; `maxThroughput`, `responseTime` | Un stock, entrada, liberación limitada y respuesta proporcional al stock. | Split conservativo; salida física de abandono; cota inferior/no negatividad bajo todos los extremos; compilación en IGC. |
| `DeliveryCounter` | `arrival` entrada; `total` salida | Acumulación terminal de entregas. | Que un flujo paralelo pueda añadirse sin duplicar materia. |
| `FirstOrderReportFilter` | `physicalArrivalRate` → `reportedRate`; `reportResponseTime` | Filtro informativo de primer orden. | Retardo físico o estado material; no reinterpretarlo como cola de trabajo. |

La ruta `BoundedQueue.completed` es una única salida de flujo material. `waiting` es la salida de nivel declarado como `RealOutput`, no una segunda salida material. En consecuencia, **abandono como segundo egreso físico no es factible con el contrato actual** y no se implementará en FM-A/B sin una decisión nueva y una pieza verificada.

## 4. Gate FM-A-FEAS

| Alternativa | Resultado | Justificación |
|---|---|---|
| `CS-01`: una instancia de `BoundedQueue` entre fuente y contador | `FEASIBLE_WITH_RESTRICTIONS` (estructura declarativa) | Los puertos observados permiten una cadena fuente → cola → contador. Aún falta compilar la clase en el entorno fijado de IGC y resolver su licencia antes de declararla admitida/ejecutable. |
| `CS-02`: dos instancias seriales de `BoundedQueue` entre fuente y contador | `FEASIBLE_WITH_RESTRICTIONS` (estructura declarativa) | La composición en cadena de instancias con interfaces compatibles es consistente con el catálogo/compositor E0/E1 inspeccionado. Representa dos etapas de cola/servicio, **no** abandono ni una afirmación de que el caso real tenga esas etapas. La misma reserva de compilación/licencia aplica. |
| `Customer` con servicio + abandono | `BLOCKED_WITH_CAUSE: NO_NATIVE_CONSERVATIVE_SPLIT` | No existe en el subconjunto inspeccionado una molécula con dos egresos materiales distintos que conserve el stock, ni política de abandono admitida. |
| `FirstOrderReportFilter` como segunda ruta física | `REJECTED_SEMANTIC_MISMATCH` | Es una ruta de información; no transporta ni divide el flujo material. |

**Adjudicación:** existe una pareja estructural mínima y genérica para continuar el contrato declarativo FM-A: una etapa frente a dos etapas seriales. Esta constatación autoriza describir ambas como fixtures estructurales; **no** autoriza FM-B ni confirma que el investigador quiera usarlas como primera pareja experimental. La selección de pareja ejecutable es D-FM-02 y debe resolverse antes de FM-B. No se afirma todavía conservación numérica ni simulación en IGC.

## 5. Decisiones de contrato aplicadas

- `schema/source/igc.yaml` amplía LinkML de manera aditiva para contratos de catálogo, puertos, parámetros, instancias, conexiones, revisiones estructurales, candidatos, validación y ejecuciones.
- Los campos `direction`, `signal_kind` y `connection_kind` usan vocabularios LinkML cerrados; el validador comprueba también identificadores únicos de candidatos y conexiones y conserva casos negativos para valores desconocidos y duplicados.
- La compatibilidad entre clase de conexión y señal es explícita: `MATERIAL_FLOW` admite `FLOW`; `INFORMATION_SIGNAL`, `SIGNAL` o `STATE`; `CONTROL_SIGNAL`, sólo `SIGNAL`. Se rechaza cualquier otro emparejamiento con `CONNECTION_SIGNAL_MISMATCH` y hay negativos para una señal `FLOW` etiquetada como información o control.
- Los hashes de estructura y los valores de parámetros se representan por separado.
- En las fixtures, `structural_hash` es SHA-256 de JSON canónico UTF-8 (`sort_keys=true`, separadores `(',', ':')`) sobre `catalog_snapshot`, instancias ordenadas por `id` con sólo `id`/`molecule_definition_id`, y conexiones ordenadas por `from_port`/`to_port`/`connection_kind`. `parameter_bindings` se excluye para que un cambio paramétrico no altere el hash topológico.
- El estado de madurez/licencia se conserva como dato explícito; `source_ref` o clase Modelica por sí solos no significan admisión.
- `ConceptualModelRequest` es declarativo y revisable; no presupone generación desde narración ni descubrimiento de topología por un LLM.
- La especificación v0.2 queda autorizada para FM-A; FM-B y cambios de ramas de los PR padre quedan pendientes de instrucción expresa.

## 6. Evidencia que falta antes de declarar FM-A completo

- Generación determinista del JSON Schema, validación positiva de los cuatro contratos, vocabularios cerrados y negativos de valores desconocidos/IDs duplicados: [Actions F1a #26](https://github.com/yudocyudoc/IGC/actions/runs/39447185779) pasó en HEAD `cb9d80670ac2b496a594ece1834a1fc0cb38098d`; la regresión del laboratorio pasó en [F0 #280](https://github.com/yudocyudoc/IGC/actions/runs/39447184843) sobre el mismo HEAD. El reporte del validador conserva `ATMS_VALUE_ADDED=NOT_DEMONSTRATED` para S0.
- Comparación S0 del filtro trivial frente al selector ATMS de PR #5: [Actions F1a #23](https://github.com/yudocyudoc/IGC/actions/runs/39444522863) dio la misma selección (`candidate-promotion-orders-001`) y registró `ATMS_VALUE_ADDED=NOT_DEMONSTRATED`, como corresponde a esta fixture.
- Regresión del laboratorio: [Actions F0 #274](https://github.com/yudocyudoc/IGC/actions/runs/39444522778) pasó sobre el mismo HEAD `5cccaee39d0e08630b439f98a60c7c6bb0227fb7`.
- Asegurar que no se importe código de `short` antes de una resolución de licencia.
- Adjudicar con el investigador si la pareja de una etapa/dos etapas es la elegida para FM-B.

El contrato declarativo y la comparación S0 pasan en Actions, pero la admisión de las clases importadas sigue bloqueada por licencia/compilación y la pareja para FM-B necesita adjudicación. El estado global de la entrega se mantiene `FM_A_CONTRACT_PARTIAL` con factibilidad estructural restringida; no es `FM_A_CONTRACT_VERIFIED` ni `FM_B_STRUCTURAL_INTEGRATION_PASS`.
