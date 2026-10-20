# IGC — Anexo FM v0.2 · Frente de integración molecular temprana

**Fecha:** 2026-10-20 (zona de trabajo: `America/Mexico_City`).
**Estado:** **FM-A AUTORIZADO PARA IMPLEMENTACIÓN por instrucción del investigador del 2026-10-20; FM-B NO AUTORIZADO.** La autorización permite crear y actualizar la rama/PR draft apilado de FM-A, pero no fusionar PR, cambiar la base de #5/#6 ni ampliar la biblioteca con una política/molécula nueva.
**Corte de verificación:** 2026-10-20, `America/Mexico_City`; estados/refs de GitHub verificados para PR #5/#6 y los antecedentes `short` mencionados.
**Destino:** `yudocyudoc/IGC`, como documento adjunto a la especificación v0.2; **no reemplaza** la especificación, el plan F0–F9 ni los contratos de aceptación vigentes.
**Naturaleza:** **frente temporal de integración y evaluación de capacidades**, no fase permanente, nueva arquitectura ni sustituto de F0–F9.
**Identificador propuesto:** `FM` (*Frente de Integración Molecular*), con **entregas** `FM-A` y `FM-B` (no confundir con IDs de modelos). Se inserta después de F0/F1a y considera los incrementos sintéticos apilados PR #5 y #6; se ejecuta **antes de invertir sustancialmente en F4** y coordinado con F2b/F3a–F3b. No renumera las fases normativas.

> **Decisión propuesta en una frase:** integrar de forma temprana un subconjunto **real y tipado** del catálogo molecular y del compositor/linter IGC-SL, para que `SystemModelCandidate` pueda contener **estructuras dinámicas rivales** y no solo variantes de parámetros. Aprovechar primero los activos inspeccionados de `short`, aceptar faltantes explícitos, y comprobar en OpenModelica una diferencia estructural reproducible. Las ontologías, ATMS, embeddings, F5 completo y evaluación científica conservan su alcance posterior.

---

## 0. Correcciones y alcance de la revisión v0.2

Este documento **sustituye la propuesta FM v0.1**. Por instrucción del investigador del 2026-10-20 queda habilitada la ejecución de FM-A y la preparación de su PR draft en la rama apilada descrita en §3.1; no se autoriza FM-B ni la fusión de PR. Corrige la fotografía de GitHub al incluir PR #6, fija una cadena de ramas explícita, reemplaza «redes causales» por **estructuras dinámicas hipotéticas**, condiciona el ejemplo de abandono a una prueba de factibilidad y distribuye FM-B en pasos dependientes. `FM-A`/`FM-B` son nombres de entregas; `CS-01`/`CS-02` son IDs de candidatos estructurales.

**Estado verificado de los PR del nuevo `IGC` al corte:** #1/#2/#3/#4 integrados en `main`; [#5](https://github.com/yudocyudoc/IGC/pull/5), `f3-atms-candidate-selection` @ `5ab99bbf2ca62346f7c09725afaa31f04d16b8dc`, **abierto sin fusionar**, base `main`; [#6](https://github.com/yudocyudoc/IGC/pull/6), `f2-f3-rdf-atms-handoff` @ `88b181cd85b5d96a3686acf695ec45cc05600a98`, **abierto sin fusionar**, base la rama de #5. Los workflows sintéticos de #6 y el workflow general F0 pasaron en ese SHA ([ATMS/puente](https://github.com/yudocyudoc/IGC/actions/runs/39367663814), [F0](https://github.com/yudocyudoc/IGC/actions/runs/39367663759)); no equivalen a los gates completos de F2/F3 ni a H-IGC.

**Límite del nuevo puente semántico:** #6 crea/consulta una formalización RDF con Web Annotation, PROV-O y vocabulario CRMinf, y **recupera por SPARQL propuestas que el catálogo sintético ya declaraba** y vinculaba al claim. No infiere un mecanismo físico a partir de las fuentes; las alternativas, los supuestos y los `nogoods` siguen prefijados en el fixture. El ATMS sigue siendo un probe y la topología Modelica sigue siendo `single_stock`. Por tanto, no confundir «RDF→propuestas para ATMS» con «RDF→descubrimiento autónomo de mecanismo».

---

## 1. Por qué existe este anexo

La especificación integral v0.2 ya exige biblioteca de moléculas, IGC-SL, linter L0–L6, modelos rivales y ejecución real de OpenModelica. **No falta esa exigencia en la arquitectura; falta adelantar una comprobación operacional decisiva.**

El laboratorio nuevo demostró integraciones técnicas que conviene conservar: fuente/claim anclado, contratos LinkML y ledger bitemporal local, grafos semánticos de prueba, sonda ATMS, candidato sintético y handoff verificable a OpenModelica. El PR #5 conserva dos propuestas con la misma estructura `single_stock`, diferenciadas por la tasa de entrada; el PR #6 **ya enlaza** la anotación/fuente y la formalización RDF/PROV-O/CRMinf con la consulta SPARQL que alimenta las propuestas del selector. **Ninguno aporta aún topologías distintas ni obtiene el `nogood` a partir de evidencia empírica**: permanece declarado en el catálogo sintético, con una sola justificación por candidato. En ese escenario, un chequeo sencillo de subconjuntos reproduce la selección del ATMS.

**Hallazgo crítico:** `ATMS → selección → OpenModelica` demuestra cableado técnico, **no** demuestra por sí mismo razonamiento de alternativas no triviales, elección causal, ganancia frente a una regla simple ni modelado estructural. La crítica independiente de Claude identifica esta limitación. El siguiente experimento debe tensionar la *estructura* y no repetir una perturbación paramétrica.

**Objetivo de FM:** pasar de **«un candidato parametriza una ecuación fija»** a **«un candidato declara una red de mecanismos admitidos; el motor la compone, valida, simula y permite conservar rivales»**.

### 1.1 Este documento no contradice F0–F9

- **F0** permanece `ACCEPTED_WITH_LIMITATIONS`, con su gate sintético específico.
- **F1a** permanece un corte SQLite/LinkML inicial; FM debe respetar su modelo append-only e historia, no convertirlo en almacenamiento de producción.
- **PR #5** demuestra el selector ATMS→candidato→handoff en modo sintético; **permanece abierto y sin fusionar**. No acredita F3 completo.
- **PR #6** (apilado sobre #5) demuestra un puente sintético Web Annotation/RDF/PROV-O/CRMinf→SPARQL→propuestas para ATMS→OpenModelica; **permanece abierto y sin fusionar**. Su catálogo declara candidatos/`nogoods`; no hay inferencia empírica ni descubrimiento automático de mecanismos.
- **F2b** sigue necesitando perfiles semánticos de dominio auditados, validaciones y trazabilidad general; #6 adelanta una conexión operativa acotada, no cierra F2b ni sustituye el conjunto de pruebas semánticas. La integración de FM deberá conservar y aprovechar esa interfaz.
- **F3a/F3b** siguen exigiendo ATMS conforme y modelos rivales versionados. FM aporta un escenario que hace significativa esa validación.
- **F4** conserva embeddings de texto, KG y firmas dinámicas; FM producirá estructuras/series candidatas para evaluar esos espacios, sin convertir embeddings en soporte causal.
- **F5** conserva la composición general, moléculas, reglas L0–L6 y modelos estructurales rivales. FM **extrae una primera rebanada verificable de F5** y la ejecuta ahora; no lo declara completado.
- **F6–F9 / H-IGC** permanecen sin evaluación científica general ni autorización de datos reales o gasto cloud.

---

## 2. Fuentes de verdad y activos a reutilizar

Las afirmaciones de esta tabla se refieren al **alcance explícito de los repositorios, PR y documentos inspeccionados**, no a una auditoría completa de sus dependencias o licencias. Verificar SHA, compatibilidad y resultados de CI **en el momento de importar**.

| Origen | Activo comprobable / declarado | Madurez / límite | Tratamiento en FM |
|---|---|---|---|
| `IGC` `main`, PR #1 y #3 | Laboratorio F0 y handoff sintético con OpenModelica; `verify-handoff` | Integra un solo `single_stock` | Conservar como regresión y reutilizar trazabilidad/runner |
| `IGC` `main`, PR #2 y #4 | LinkML inicial, ledger SQLite append-only, `as_known_at` y restricción temporal | El payload del dominio es JSON serializado; no hay tipado completo de moléculas/candidatos | Extender esquema sin reescribir historia |
| `IGC`, PR #5, `5ab99bbf2ca62346f7c09725afaa31f04d16b8dc` | `f3_candidate_selection.py`, `f3_candidate_handoff.py`, pruebas de `nogood` | Sonda ATMS; una justificación/candidato, `parameter_diff`; **abierto**, no en `main` | Reusar interfaz de selección, no exigir ganador único; no declarar beneficio de ATMS |
| `IGC`, PR #6, `88b181cd85b5d96a3686acf695ec45cc05600a98` | `f2_f3_semantic_bridge.py`, RDF/CRMinf/PROV-O, SPARQL y tests de anclaje/procedencia | Formalización *explícita* y sintética; consulta propuestas **predeclaradas**; `nogoods` del catálogo; **abierto y apilado sobre #5** | Reusar entrada semántica y su evidencia sin atribuirle inferencia causal ni admitirlo desde `main` |
| `short`, PR #20 | `docs/IGC-SL-grammar-v0.1.md`: `USE/LINK/SENSE/GOVERN/REQUIRE/SUPPORT/HYPOTHESIS/UNRESOLVED` | Diseño **documental**, no compilador | Adoptar conceptos y restricciones de forma crítica |
| `short`, PR #32 (fusionado) | `src/modelica/IGCMolecules.mo`, `src/modelica/IGCInformationMolecules.mo` | Clases Modelica y pruebas de fundación; ámbito específico | Auditar procedencia, compilar en el runner fijado de `IGC` y admitir selectivamente |
| `short`, PR #33 y #34 | E0: catálogo; E1: `composer.py`, `backend.py`, `registry.*.json` | Compositor ejecutable **acotado** a una cadena material + ruta informativa; PR encadenados no fusionados a `main` | Auditar, portar interfaces/algoritmos pertinentes, preservar negativos; **no** adoptar su restricción de cadena como regla global |
| `short`, PR #39 y #40 | Sondas de split/clonación; `experiments/p2/linter.py` e IR conceptual | El IR distingue algunos casos válidos/inválidos, pero reporta `executable:false`; sin conservación numérica ni feedback ejecutado | Usar como batería adversativa y fuente de contratos, no anunciar red ejecutable existente |
| Hines, SystemDynamics/MSL, BSL | Fuentes y familias de moléculas descritas en IGC-SL/v5.1 | Estado desigual: clases verificadas, propuestas, documentación y bibliotecas no admitidas | Aplicar admisión **por pieza**, sin importar bibliotecas enteras por nombre |

Referencias primarias: [IGC PR #5](https://github.com/yudocyudoc/IGC/pull/5), [IGC PR #6](https://github.com/yudocyudoc/IGC/pull/6), [short PR #20](https://github.com/yudocyudoc/short/pull/20), [#32](https://github.com/yudocyudoc/short/pull/32), [#34](https://github.com/yudocyudoc/short/pull/34), [#39](https://github.com/yudocyudoc/short/pull/39), [#40](https://github.com/yudocyudoc/short/pull/40). Internos: especificación v0.2, hoja v5.1 del 18/oct, `GATES_INTEGRACION.md` y plan de `IGC`.

### 2.1 Registro de refs consultadas (corte 2026-10-20)

| Antecedente `short` | Ref verificada / SHA de cabeza | Naturaleza al corte |
|---|---|---|
| PR #20 · gramática IGC-SL | `9794c01f56f8be65fc8da16f9443eeabf4134beb` | Diseño documental; PR cerrado sin merge |
| PR #32 · paquetes Modelica | `eef3c38799f19d9526c8b81097ec0483d802dc15` | **Fusionado en `short/main`**; fuente y CI histórica, pendiente admisión en `IGC` |
| PR #33 · E0 | `d5a9512e69b8e1f59ae1ea13c0e6fdb8c9472e72` | Draft abierto, base de #34 |
| PR #34 · E1 compositor | `97a9ad3a3e13d5b04d85340a0907994e41c13518` | Draft abierto; pruebas históricas de composición acotada |
| PR #39 · P1 límites | `f4bf572d47de760ae0120af008e4c65b3f7b4233` | Draft abierto, investigación de límites |
| PR #40 · P2 linter conceptual | `9f9d9753bd5710fb3678ad13af9ed7b7755f4831` | Draft abierto; **no ejecutable** como red física nueva |

La auditoría **FM-01** deberá registrar por archivo su propio blob SHA-256, commit de origen, licencia, tipo de conector y salida de CI; la cabeza del PR **no** reemplaza el hash de contenido ni prueba que una pieza haya sido admitida. Diferenciar obligatoriamente: **(i) fuente disponible, (ii) clase Modelica que compiló/simuló bajo una versión concreta, (iii) pieza admitida con contrato/negativos en `IGC`**. Las categorías no son sinónimos.

**Regla de reutilización:** ningún antecedente no fusionado de `short` se considera automáticamente aprobado, ejecutable o compatible con el stack exacto de `IGC`. La transferencia requiere inventario de archivo/ref/SHA, licencia, test nativo y tabla **reusar / adaptar / rehacer justificadamente / no admitir**. No copiar golds de experimentos ciegos, respuestas, datasets privados o lógica que contenga soluciones preadjudicadas.

---

## 3. Posición exacta del paréntesis FM

```text
IGC v0.2 — SECUENCIA GLOBAL PRESERVADA

F0    Laboratorio + handoff acotado                     INTEGRADO / LIMITADO
F1a   Ledger y LinkML inicial                           INTEGRADO / LIMITADO
PR5   Sonda ATMS → selección → handoff                   ABIERTO / BASE MAIN
PR6   RDF/CRMinf/PROV/SPARQL → propuestas ATMS          ABIERTO / APILADO SOBRE PR5

            ┌─────────────────────────────────────┐
            │ FM — FRENTE MOLECULAR TEMPORAL      │
            │ Registro + IR + compositor + linter  │
            │ 2 estructuras rivales + simulación   │
            │ Ablaciones + límites explícitos      │
            └─────────────────────────────────────┘

F1b/F2b/F3a/F3b    Integraciones completas; FM entrega contratos concretos
F4                Vectores con estructuras/series realmente discriminables
F5                Generalización molecular, catálogo, linter L0–L6 completo
F6–F9             Ciclo, experimentos, cloud y transferencia
```

No esperar a que estén implementados F2b, F3a, F4 y todo F5 para iniciar FM. Tampoco dejar de implementarlos. El paréntesis es una **dependencia de aprendizaje**, no un sustituto permanente. Puede solaparse con F2b siempre que la superficie contractual esté versionada.

**Límite de trabajo:** máximo **dos entregas/PR diferenciados, FM-A y FM-B**, no nuevas fases permanentes. Cada uno puede desplegar varios commits/gates internos sin implicar apertura de otro PR; si necesita un nuevo motor de políticas, detener y someterlo a decisión. Si el primer inventario descubre incompatibilidades graves, detener y adjudicar antes de importar código. Evitar crear diez fases nuevas o repetir CI de F0 sin aportar una capacidad nueva.

### 3.1 Dependencia de ramas y estrategia de ejecución (obligatoria)

**Estrategia elegida para trabajar sin fusionar #5/#6 (preferida ahora):** mantener una **pila de PR**:

```text
IGC/main
   └─ PR #5 · f3-atms-candidate-selection            [OPEN]
       └─ PR #6 · f2-f3-rdf-atms-handoff              [OPEN]
           └─ PR FM-A · fm-a-molecular-contract      [DRAFT; base PR #6]
               └─ PR FM-B · fm-b-molecular-integration [DRAFT; base FM-A]
```

Crear `fm-a-molecular-contract` **a partir del SHA verificado de #6**, `88b181cd85b5d96a3686acf695ec45cc05600a98`, y configurar **la base del PR FM-A en `f2-f3-rdf-atms-handoff`**, no en `main`; eso evita que su diff incluya #5/#6. Crear FM-B, si se autoriza y FM-A está listo, **desde la cabeza exacta aprobada de FM-A**, con base de revisión FM-A. Anotar en cada PR el commit padre, SHA de dependencias y si se han rebasado sus pruebas.

**Si el investigador decide integrar #5 y #6 antes:** fusionar **solo previa autorización expresa**, respetar orden #5→#6; actualizar/rebasar FM-A contra el `main` resultante y **retarget** de las bases de FM-A/FM-B según corresponda; repetir Actions sobre los nuevos HEAD. **Nunca** interpretar un PR abierto como código disponible en `main` ni hacer merge implícito.

**Alternativa desacoplada:** se puede comenzar desde `main` *únicamente* un inventario documental sin imports ni pruebas que dependan de #5/#6; **no** se denominará implementación FM-A integrada ni se intentará FM-B hasta resolver la pila. Esta excepción no cambia la estrategia principal.

**Alcance armonizado de autorización:** la instrucción del investigador «implementa, armonizando la tensión» autoriza únicamente FM-A en la pila descrita arriba. Por ello se permite crear/actualizar `fm-a-molecular-contract` desde el SHA verificado de #6 y preparar un PR draft con base en la rama de #6. No autoriza FM-B, fusionar PR, cambiar la base de #5/#6 ni programar una política o molécula nueva. FM-B requiere una decisión posterior; las decisiones D-FM-02/03/05 siguen reservadas para elegir y revisar esa entrega. La auditoría y el estado de factibilidad de FM-A sí quedan autorizados.

---

## 4. Capacidad concreta que FM debe habilitar

### 4.1 Del texto a modelos, sin inventar el mecanismo

```text
ClaimOccurrence / Observations / Hypotheses
               |
    ConceptualModelRequest (intención y restricciones,
           evidencia, supuestos y desconocidos)
               |
     Registry (moléculas por versión/madurez,
           capacidades, puertos y fuentes)
               |
        IGC-SL Typed IR / Compositor
               |
   L0–L6 acotado: tipos, entidades, unidades,
       balance, políticas y procedencia
        /                         \
  ADMITIDO                      PARCIAL / BLOQUEADO
     |                                |
 AST+bindings auditados        diagnóstico localizado
     |                         + pedir observación / molécula
 OpenModelica
     |
 series + checks + discriminación tentativa
     |
 registrar alternativas, no solo un ganador
```

En este corte, **`ConceptualModelRequest` puede ser una fixture estructurada y revisable**. No se exige que un LLM invente una topología ni que la extraiga de narrativa no estructurada. Lo que se evalúa es que el **motor** componga topologías a partir de un registro ampliable sin ramas de código `if café`, `if mundo_verdadero` o `if CandidateB`.

### 4.2 Fronteras de responsabilidad

1. **Conocimiento:** `ClaimOccurrence`, `Observation`, `Proposition`, `EvidenceAssessment`, `Assumption`; atribución y modalidad permanecen independientes de la verdad.
2. **Hipótesis conceptual:** posible mecanismo, entidades afectadas, consecuencia, referencia y desconocidos. *No* incluye por fuerza el cableado Modelica.
3. **Registro molecular:** identifica componentes disponibles y madurez; su nombre no certifica pertinencia.
4. **IR/compositor determinista:** elige relaciones formalmente admisibles, conserva candidatos alternativos y devuelve incertidumbres.
5. **Linter:** verifica consistencia técnica, no causalidad empírica; separa material (`LINK`), observación (`SENSE`) y política (`GOVERN`).
6. **Backend Modelica:** instancia clases/adaptadores admitidos; no inventa ecuaciones ni valores faltantes. Una ecuación nueva solo podrá admitirse mediante contrato propio, justificación y tests.
7. **ATMS:** conserva entornos de soporte y conflictos, puede condicionar qué candidatos son admisibles; no debe imponer un único ganador ni convertir posibilidad en verdad.
8. **Evaluador:** compara curvas/observables y su capacidad discriminante; un ajuste igual no identifica estructura.

---

## 5. Contratos declarativos que debe añadir FM

**Problema actual reconocido (incluso con el puente semántico del PR #6):** el LinkML F1a define esencialmente el sobre bitemporal; `SystemModelCandidate` y la composición dinámica siguen representados por fixtures JSON validados imperativamente. FM no requiere completar toda la ontología de `IGC`, pero sí mover **este subconjunto** a contratos de fuente declarativa versionados y JSON Schema derivado.

### 5.1 Clases/objetos mínimos (nombres sujetos a revisión)

| Objeto | Responsabilidad mínima | Propiedad irreductible |
|---|---|---|
| `MoleculeDefinition` | Clase/familia disponible, fuente, licencia, digest, estado de madurez | `catalog_version`, `modelica_class` **solo si admitida** |
| `MoleculePort` | Dirección, tipo `STOCK/FLOW/SIGNAL/CONTROL`, entidad, dimensión y conector nativo | Un puerto `SIGNAL` no transfiere entidades |
| `MoleculeContract` | Supuestos de funcionamiento, invariantes, parámetros requeridos, límites, casos prohibidos | `verified_tests`, `native_compatibility` |
| `ConceptualModelRequest` | Intención causal sin AST resuelto, observables, frontera, restricciones y desconocidos | `origin_refs`, `hypothesis_status`, `unresolved` |
| `SystemModelCandidate` | Frontera y revisión estructural, mecanismos propuestos y estado ejecutable/parcial | `structure_revision_id`, `assumption_ids`, `evidence_refs` |
| `SystemStructureRevision` | Conjunto de instancias y enlaces, distinción de material, información y control | Hash canónico de estructura independiente de parámetros |
| `MoleculeInstance` / `TypedRelation` | Instancia de clase admitida y relaciones `LINK/SENSE/GOVERN` | IDs de clase/puerto y versiones exactas |
| `ParameterBinding` | Valor externo, unidad, intervalo/ausencia, origen, validez temporal | No sustituir `unknown` por constante arbitraria sin rotular fixture |
| `CandidateRelation` | `competes_with`, `compatible_with`, `nested_in`, `observationally_equivalent_on`, `undetermined` | Comparación fundamentada y horizonte |
| `StructuralValidation` / `SimulationRun` | Resultado verificable de linter, backend, solver y artefactos | Estados separados `ENGINEERING` vs `SCIENTIFIC` |

**Nota:** `Assumption`, `ClaimOccurrence` y `Observation` ya figuran conceptualmente en LinkML F1a, pero sus cargas útiles específicas no están tipadas a este nivel. Los contratos y mappings RDF de PR #6 tampoco sustituyen el esquema molecular. Extender sin duplicar identidades ni presentar los JSON de PR #5/#6 como esquema LinkML admitido.

### 5.2 Ejemplo *orientativo* de solicitud (NO es esquema implementado)

```yaml
schema: igc-conceptual-model-request/proposed-0.1
investigation_id: cafe-synthetic-001
observables: [arrivals_customers_per_hour, customers_served_per_hour, customers_waiting]
entity: Customer
boundary: cafe_service_area
claim_refs: [claim:synthetic:peak-wait]
possible_mechanisms:
  - queue_with_capacity
  - waiting_dependent_abandonment
unresolved: [abandonment_policy, server_capacity, initial_queue]
constraints:
  distinguish_material_and_information: true
  preserve_customer_balance: true
  allow_multiple_candidates: true
```

Esto expresa **una solicitud**, no una solución ni un catálogo de respuestas verdaderas. Las variables no pueden materializarse automáticamente con valores supuestos. `Customer`, `Order` y `BreadPortion` son entidades distintas; la conversión requiere mecanismo declarado.

### 5.3 Identidad, madurez e historia

- `CANDIDATE` → `MATHEMATICALLY_VERIFIED` → `NATIVE_ADMITTED`: estados de **admisión de molécula**, independientes de `OBSERVED`, `HYPOTHESIS`, `SUPPORTED` o `REFUTED` sobre el mundo.
- No declarar ejecutable una molécula de `short` por tener fuente Modelica: debe compilar/simular en stack fijado y superar pruebas aplicables.
- Cada `SystemStructureRevision` conserva `catalog_snapshot`, IDs de molécula y digests, conexiones y supuestos; **hash estructural distinto del hash de parámetros**.
- Registrar revisiones estructurales y resultados a través del ledger F1a para fixtures sintéticas; usar `recorded_at` monotónico por entidad y `valid_from/valid_to` independientes. Si hace falta almacenamiento de grafos en otro formato, hacerlo como proyección derivada, no reemplazar el ledger.
- Los artefactos grandes podrán permanecer locales/Actions en FM; R2/D1 cloud real continúa en F8.

---

## 6. Catálogo de arranque: reuso primero, extensión solo si necesaria

**No crear una colección de moléculas por cantidad.** Seleccionar el mínimo conjunto que permita comprobar una frontera nueva.

| Clase/familia | Función | Tratamiento inicial |
|---|---|---|
| `IGCMolecules.AcceptedSource` (`short` PR #32) | Fuente externa de trabajo aceptado | Candidata prioritaria a admisión previa auditoría |
| `IGCMolecules.BoundedQueue` (`short` PR #32) | Acumulación/servicio acotado con respuesta proporcional | Candidata prioritaria a admisión previa auditoría |
| `IGCMolecules.DeliveryCounter` (`short` PR #32) | Acumulado observado de salida | Candidata prioritaria a admisión previa auditoría |
| `IGCInformationMolecules.FirstOrderReportFilter` (`short` PR #32) | Retardo de **información**, no de flujo físico | Control de `SENSE`; no reinterpretarlo como cola |
| Ganancia y bloques SystemDynamics/MSL ya verificados | Átomos/adaptadores por firma | Admitir solo con conectores y límites definidos |
| Bifurcación conservativa / abandono | Permitir atención + desistimiento sin clonar personas | **Hipótesis opcional sujeta a FM-A**: comprobar disponibilidad nativa, política, puertos y conservación; si falta, registrar `NO_MATCHING_MOLECULE` / `POLICY_UNIMPLEMENTED` y **no** construir la pieza sin autorización |
| Inventario, reposición, merma, retorno, marketing | Mecanismos potenciales del piloto ampliado | **Fuera del primer paréntesis**, salvo que los dos candidatos iniciales no puedan distinguirse sin uno de ellos |
| Hines / BSL | Fuente de posibles contratos/interfaces | No importar ni declarar compatibles hasta auditar licencia, puerto real, versión y OpenModelica |

**Advertencia de dominio:** los componentes `AcceptedSource`/`BoundedQueue`/`DeliveryCounter` de `short` se probaron con *trabajo/pedidos* en un escenario acotado. Si FM los reutiliza en un caso de *personas esperando*, debe verificarse explícitamente que la entidad, semántica y unidades son compatibles; no renombrar `Shipment` a `Customer` para simular una equivalencia no probada.

---

## 7. Primer experimento que el paréntesis debe resolver

### 7.1 Pregunta falsable

**¿El sistema puede representar, admitir, construir, simular y conservar dos candidatos con topologías SD distintas a partir de contratos moleculares —sin codificar una plantilla de respuesta para cada candidato— y señalar una observación o perturbación que los diferencie?**

No basta con cambiar `arrivalRate` o un comentario. Exigir **diff estructural** en stocks, flujos, enlaces o políticas.

### 7.2 Dos candidatos estructurales *ilustrativos*, no respuestas correctas

Los IDs **`CS-01` y `CS-02` designan candidatos estructurales**, no entregas FM-A/FM-B, no ranking, no modelos científicamente identificados. Mantener estos IDs o sustitutos versionados **idénticos** en fixtures, ledger, manifiestos y nombres de artefactos. No confundir con los brazos estadísticos A/B/C del §7.4.

Ejemplo **condicionado a factibilidad** de un sistema de personas/servicio con observaciones iniciales compartidas:

- **`CS-01` — estructura mínima:** llegadas de clientes → cola/espera → salida por servicio; stock de personas en cola, capacidad o tasa de servicio declarada.
- **`CS-02` — estructura ampliada opcional:** llegadas → cola/espera → dos salidas físicamente diferenciadas (`servicio` + `abandono`) con balance de personas y, **solo si existe y se admite**, política nativa de respuesta a la espera.

**Gate de factibilidad FM-A-FEAS (antes de aceptar este ejemplo como objetivo ejecutable):** verificar que hay clases/adaptadores nativos de dos salidas, conservación física, unidades de `Customer` y política de abandono **admitidos en `IGC`** o disponibles con pruebas/licencias suficientes para admitirlos sin ampliar el alcance. Inspeccionar P1/P2 de `short` y el catálogo real. Emitir `FEASIBLE`, `FEASIBLE_WITH_RESTRICTIONS` o `BLOCKED_WITH_CAUSE` con dependencia exacta, resultado adversativo y SHA de fuente.

Si la red de abandono exige inventar una política/ecuación, una molécula no admitida o transformar entidades sin contrato, **FM-B no está obligado a implementarla**. Debe conservar `CS-02` como `PARTIAL/BLOCKED_WITH_CAUSE` y proponer **otro par mínimo de estructuras distintas con piezas ya admitidas** (por ejemplo, cadenas materiales de distinta longitud y retardos físicos verificables frente a medición informativa, siempre que la distinción sea verdaderamente estructural y comparable). La alternativa se adjudica con el investigador antes de implementarla; no cambiar sigilosamente el experimento.

**Si tampoco existe un par ejecutable legítimo con el catálogo admitido, FM-B se detiene `BLOCKED_WITH_CAUSE`, sin falsa aprobación de FM-04/06/11.** Desarrollar una nueva política/molécula es una **decisión reservada**, no un requisito implícito de FM-B.

Los candidatos registrarán supuestos, incertidumbres, entidad, ámbito, procedencia, parámetros faltantes y estado de ejecución. Ningún `nogood` se inventa para forzar un ganador, ni se atribuye a evidencia un mecanismo que no puede sostener. No inventar elasticidad de abandono.

Para el primer control, puede usarse un estímulo sintético **no secreto** y valores predeterminados del evaluador. Para probar descubrimiento/identificación, reservar un **mundo oculto** más adelante, de modo que ni selector, ni compositor, ni LLM, ni índice puedan leer el mecanismo generador.

### 7.3 Perturbación discriminante

Usar al menos un cambio de régimen de demanda/capacidad en el que las estructuras predigan diferencias observables, por ejemplo `personas esperando`, `personas atendidas`, `abandono` y balance acumulado **solo si se admite ese caso**; para otra pareja, fijar sus observables correspondientes en el contrato antes de simular. Calcular las diferencias desde **CSV reales de OpenModelica**, no compararlas con un resultado rígido «30/40» programado en el orquestador.

Si los dos modelos son indistinguibles con esos observables/horizonte, devolver `NON_DISCRIMINATING` o `OBSERVATIONALLY_EQUIVALENT_ON` con dominio preciso; **no declarar ganador**.

### 7.4 Controles anti-hombre-de-paja

1. **Baselines:** misma entrada, presupuesto y observables para A = análisis simple o ecuación directa; B = compositor sin capa molecular nueva si expresa el caso; C = FM con moléculas. No penalizar un baseline por haberle negado arbitrariamente información.
2. **Selección:** con dos rivales admisibles, ambos sobreviven y se simulan; el pipeline jamás exige `len(selected)==1` como regla de investigación.
3. **Registro abierto:** cambiar el catálogo por otro compatible sin modificar código del compositor ni introducir `if cafe`/ID de mundo.
4. **Límites:** sin molécula/adaptador/política, devolver diagnóstico; no elegir un falso amigo semántico por nombre o similitud de embedding.
5. **Gold oculto:** si hay adjudicación causal, el mecanismo verdadero y los parámetros de generación pertenecen al evaluador, no a las fixtures del constructor.

---

## 8. Linter FM: subconjunto ejecutable de L0–L6

Se implementa lo **necesario para la red mínima**, conservando la taxonomía L0–L6 de la hoja v5.1. No afirmar cobertura completa de todos los mecanismos.

| Capa | Obligación en FM | Ejemplo de fallo |
|---|---|---|
| **L0** Catálogo | Clase/puerto/versión/driver/modelo nativo existe y está admitido | Referenciar BSL no probada como clase ejecutable |
| **L1** Tipo/entidad/unidad | `STOCK<Customer>`, `FLOW<Customer>/hour`, `SIGNAL`, `CONTROL` y dimensiones son coherentes | Conectar cliente a pedido sin conversor |
| **L2** Topología | Split real admite dos salidas con mecanismo de partición; rechaza multicast de flujo idéntico | Clonar 10 clientes/h hacia servicio y abandono |
| **L3** Conservación/estados | Balanza numérica de personas y límites no negativos en resultados, capacidad/stock cero | Atender más personas que las disponibles sin fuente |
| **L4** Control/feedback | `SENSE` no es transferencia; `GOVERN` exige política y soporte nativo | Reporte retrasado altera físicamente flujo sin política |
| **L5** Semántica/evidencia | Instancia/enlace como observación respaldada o hipótesis explícita; rechazo/abstención ante mal encaje | `dropout` de otro dominio tomado como abandono de clientes |
| **L6** Compilación | OpenModelica real, solver/versión, residuos, tests extremos, licencias/adaptadores | Clase compila aislada pero falla conectada |

**Distinción obligatoria:** P2 de `short` demuestra ciertas compatibilidades **topológicas**, no el balance numérico. FM debe ejecutar ejemplos que lo validen o mantener `P2_EXECUTABLE_NETWORK_PASS=NOT_RUN`.

---

## 9. ATMS: conservar la integración y medir si aporta

Las moléculas **no resuelven automáticamente** el valor añadido de ATMS. FM incluye una ablación mínima para evitar interpretar cableado como razonamiento nuevo.

**Comparador S0:** filtro de subconjuntos (`nogood ⊆ supuestos_requeridos`). Para la fixture vigente del PR #5 (también usada como base del puente #6) debería producir las mismas decisiones; registrar `ATMS_VALUE_ADDED=NOT_DEMONSTRATED` en ese escenario.

**Escenario S1:** una conclusión derivada tiene **dos justificaciones independientes alternativas**, cada una con un entorno de supuestos distinto. Un `nogood` invalida **uno** de los caminos, pero el candidato permanece soportado por el otro. Comprobar etiquetas mínimas, explicaciones y actualización, no solo supervivencia binaria.

**Escenario S2:** varios candidatos compatibles sobreviven y todos pueden alcanzar el evaluador de modelos; una incompatibilidad **fundada** poda únicamente el entorno pertinente. No convertir «hay dos candidatos» en error.

**Comparador serio:** además del filtro S0, contrastar con una implementación simple de cierre de reglas OR/AND y poda. El ATMS podría aportar trazabilidad e incrementos de actualización sin ser superior en tiempo o complejidad en problemas pequeños; medir las diferencias sin prometer victoria.

**Fuera de FM:** motor ATMS completo de producción, retractación temporal general, heurísticas de control de explosión, granularidad RMT/credencias; permanecen en F3a/F3b. No llamar `PASS_ATMS_CONFORMANCE` al probe.

---

## 10. Suite de aceptación: gates específicos FM

**Un gate FM no se completa por número de tests verdes:** debe demostrar la propiedad indicada y conservar un control negativo que realmente falle. Nombres propuestos para el test plan; no son tests ya existentes.

| ID | Prueba falsable | Resultado exigido |
|---|---|---|
| FM-01 | Auditoría de `short`: PR #20/#32/#33/#34/#39/#40 con SHA de commit **y archivo**, fechas, licencias, CI, puertos; fuente vs compilado vs admitido | Tabla de admisión; ninguna pieza promovida sin verificación |
| FM-02 | Mismo esquema LinkML genera JSON Schema y valida objetos de molécula, instancia, estructura y candidato | Positivo + negativo para puerto/referencia/unidad ausente; lock reproducible |
| FM-03 | Regresiones `IGC` F0/F1a, selector PR #5 **y puente semántico PR #6**, incluidos casos negativos de fuente/SPARQL | No regresión del código realmente heredado en pila, con SHA de CI |
| FM-04 | Misma solicitud conceptual produce al menos dos **revisiones estructurales distintas** (hash/diff independiente del vector de parámetros) | No contar `parameter_diff` como `structural_diff` |
| FM-05 | Compositor usa registro intercambiable, IDs y puertos tipados; no branching por cafetería/mundo/verdad | Cambio de catálogo no cambia código del motor |
| FM-06 | Split de flujo **legítimo** con conservación, **si FM-A-FEAS lo admite** | `PASS` con balance en CSV o `BLOCKED_WITH_CAUSE`; no inventar política para aprobar |
| FM-07 | Split con duplicación de material | Rechazado de forma localizada, no genérica |
| FM-08 | Confusión entidad/unidad y `SIGNAL`→`FLOW` / `GOVERN` sin política | Rechazado; `POLICY_UNIMPLEMENTED` si procede |
| FM-09 | Casos extremos compatibles con las topologías realmente admitidas (capacidad/stock cero, sobrecarga; feedback/retardo solo si existe) | Verificación de invariantes aplicables; `NOT_APPLICABLE` explicado para piezas ausentes |
| FM-10 | Dos candidatos compatibles llegan a Modelica, incluso si ninguno domina | Ambas series y manifests; no selector top-1 obligatorio |
| FM-11 | Diferencia de series y prueba discriminante | Calculada desde series; `NON_DISCRIMINATING` cuando no hay separación |
| FM-12 | S0 ATMS vs filtro trivial | Igualdad admitida y `VALUE_ADDED=NOT_DEMONSTRATED` para fixture simple |
| FM-13 | S1 con dos justificaciones y nogood parcial | Etiquetas mínimas correctas; supervivencia por vía alternativa |
| FM-14 | Alterar manifiesto/catálogo/puerto/modelo/CSV | `verify-handoff` o verificador ampliado detecta divergencia |
| FM-15 | Persistencia sintética de `StructureRevision`, `Assumption`, selección y `SimulationRun` en ledger | Reconstrucción `as_known_at` y hash de snapshot coherentes |
| FM-16 | Molécula faltante o falsa equivalencia semántica | `NO_MATCHING_MOLECULE` o estado parcial, sin reemplazo arbitrario |

**Gate FM-A-FEAS (temprano):** inventario/factibilidad de red y políticas, estado `FEASIBLE`/`FEASIBLE_WITH_RESTRICTIONS`/`BLOCKED_WITH_CAUSE`.
**Gate FM-ENG:** FM-01 a FM-10 y FM-14 a FM-16 **según la variante admitida explícitamente**; un bloqueo justificado es resultado informativo, **no** `PASS` para una capacidad no ejecutada.
**Gate FM-REASON:** FM-12/FM-13 y S2; se separa capacidad ATMS de su valor añadido.
**Gate FM-DYNAMIC:** FM-11 y observabilidad contrastable; solo ingeniería/discriminación acotada.
**Gate H-IGC:** **NO SE EVALÚA** en este paréntesis, salvo que posteriormente se preregistre y ejecute protocolo ciego independiente.

**Regla de parada:** si FM-A-FEAS, FM-04 o FM-06 revelan que la topología elegida requiere política o biblioteca no admitida, registrar `BLOCKED_WITH_CAUSE`, demostrar el límite y volver a decisión del investigador **antes de tocar código de esa política**. No falsificar un PASS para conservar el calendario.

---

## 11. Secuencia de implementación propuesta (máximo dos PR, apilados según §3.1)

### FM-A — Auditoría y contrato declarativo, sin simulación fingida

**Orden interno:** (A1) fijar SHAs y revisar dependencias de #5/#6; (A2) inventariar piezas de `short` con estatus fuente/compilación/admisión; (A3) ejecutar **FM-A-FEAS** para split/servicio/abandono y para al menos una pareja alternativa de topologías; (A4) definir esquema LinkML/JSON Schema, IR y separación estructura↔parámetros; (A5) preparar catálogo versionado/fixtures `CS-01` y `CS-02`, tests de importación y negativos L0–L2, y el comparador de subconjuntos. **Si A3 bloquea**, conservar diagnóstico y contratos que sigan siendo válidos, sin anunciar moléculas ejecutables.

**Salida:** `FM_A_CONTRACT_VERIFIED` (con resultado de factibilidad explícito), `FM_A_CONTRACT_PARTIAL` o `FM_A_BLOCKED` con causas; ninguno presupone que abandono esté implementado. No copiar PR históricos enteros ni fusionar modificaciones sin aprobación.

### FM-B — Red ejecutable y discriminación acotada

**Prerequisito:** FM-A aceptado para implementación y par de topologías admitidas; PR #5/#6 disponibles por la pila (§3.1) o ya fusionados con autorización y CI repetido. **Orden de dependencias dentro del PR FM-B:**

1. **B1 — Composición sin simulación:** usar registro admitido y contratos LinkML/IR para producir al menos dos hashes estructurales genuinamente distintos, sin ramas por modelo/mundo; linter L0–L2 y negativos. Si no hay topologías admitidas, detener `BLOCKED_WITH_CAUSE`.
2. **B2 — Simulación verificable:** solo después de B1, traducir AST validados, simular en OpenModelica, auditar balances y extremos L3–L6 aplicables y guardar CSV/hashes; split/abandono/feedback son condicionales a FM-A-FEAS.
3. **B3 — Conservación de rivales y verificación:** permitir ≥2 candidatos compatibles, comparar observables, registrar `NON_DISCRIMINATING` si aplica, y construir `verify-selection` que contraste propuestas/entornos/procedencia del puente #6 con la ejecución. Persistir revisiones en el ledger local con consulta histórica **después** de estabilizar B1/B2.
4. **B4 — Ablación y cierre:** comparar ATMS con filtro simple y regla OR/AND, completar S1/S2, pruebas adversativas y matriz requisito→test→SHA→artefacto. No ocultar valores nulos o desfavorables; sin gold oculto visible al constructor.

Si aparece el bloqueo del abandono, pueden entregarse **B1/B3 parciales** y documentación/verificadores sobre otro par autorizado, pero **B2 de abandono, FM-06 y cualquier gate que exija esa topología quedan `NOT_RUN/BLOCKED_WITH_CAUSE`**. No fabricar un `FM_B_STRUCTURAL_INTEGRATION_PASS` sumando subpruebas parciales.

**Salida:** `FM_B_STRUCTURAL_INTEGRATION_PASS` solo si dos estructuras realmente admitidas se simulan y contrastan; `FM_B_PARTIAL_WITH_REASON` o `BLOCKED_WITH_CAUSE` en caso contrario. **Nunca `H-IGC_PASS`.**

Cuando FM complete su prueba, incorporar sus contratos **a las implementaciones generales de F2b/F3a/F3b**, conservando el puente sintético ya adelantado por PR #6, y continuar F4/F5. El anexo queda como registro histórico de una decisión de orden; no crea una implementación paralela permanente.

---

## 12. Qué NO debe hacer el coder

1. No reinterpretar **molécula** como cualquier ecuación `der(stock)=a-b`, ni renombrar una cadena vieja como mecanismo nuevo.
2. No regresar el cableado de Modelica al LLM ni aceptar clases/puertos inventados.
3. No imponer `len(selected)==1` en el pipeline investigador; un único candidato es un caso, no una regla.
4. No asumir que admitir un nodo `Stock` equivale a verificar conservación dinámica de una bifurcación.
5. No mezclar `Customer`, `Order`, `Shipment`, `BreadPortion` o moneda sin contratos de transformación.
6. No declarar que el `nogood` sintético se deriva de observaciones reales o que el ATMS supera al filtro simple.
7. No incluir en `IGC` respuestas de mundos ocultos ni decisiones experimentales de `short` como reglas de producción.
8. No importar BSL/Hines por volumen, ni asumir licencia/adaptadores verificados.
9. No ligar el cierre de FM a despliegue Cloudflare ni a desarrollo de F4; continuar con datos sintéticos y Actions.
10. No modificar `main`, fusionar PR, iniciar costo cloud o usar datos reales sin autorización explícita del investigador.

---

## 13. Instrucción inicial sugerida para Codex

> Trabaja **exclusivamente** en `yudocyudoc/IGC`, con el **Anexo FM v0.2** y la especificación v0.2 como documentos de referencia. Verifica primero HEAD de #5 y #6: al corte están **abiertos** y apilados (`main` → `f3-atms-candidate-selection` → `f2-f3-rdf-atms-handoff`). **Crea FM-A desde el SHA de #6 verificado y presenta su PR draft con base en la rama de #6**, nunca desde `main` mientras esas dependencias no estén fusionadas; FM-B dependerá de FM-A y tendrá como base su rama. Si los SHA cambian, actualiza el registro y revalida. Solo con autorización expresa se fusiona o se rebasea. Revisa `IGC_CONOCIMIENTO_SISTEMICO_ESPECIFICACION_v0_2_2026-10-19.md`, `PLAN_IMPLEMENTACION_IGC_v0_2.md`, `GATES_INTEGRACION.md`; audita también `yudocyudoc/short` PR #20, #32, #33, #34, #39 y #40, registrando por archivo commit/SHA, fuente, licencia, evidencia de compilación, puertos y admisión. No confundir un PR draft con algo integrado en `main`.
>
> El objetivo del **frente FM** es **integrar moléculas para obtener dos estructuras dinámicas hipotéticas candidatas distintas**, no dos parámetros del mismo `single_stock`. Conserva el puente **PR #6: Web Annotation/RDF/CRMinf/PROV-O/SPARQL→propuestas ATMS** con límites sintéticos y `nogoods` predeclarados. Primero entrega FM-A: catálogo tipado por versión/madurez, subconjunto LinkML/JSON Schema para moléculas/estructuras/candidatos, IR conceptual separado de AST nativo y tests negativos; reutiliza/adapta componentes admitidos, sin reinventar IGC-SL. Ejecuta antes **FM-A-FEAS**: prueba disponibilidad real del split conservativo, política de abandono, entidad/unidades y alternativa estructural viable. Si falta una clase nativa o política probada, emite `BLOCKED_WITH_CAUSE` y solicita decisión, **no programes** la pieza para forzar el ejemplo ni simules que funciona.
>
> Después propón FM-B en PR separado **basado en FM-A**, por orden B1 (compositor y linter/negativos) → B2 (OpenModelica y balances de piezas admitidas) → B3 (varios candidatos, `verify-selection`, manifiestos y ledger sintético) → B4 (ablaciones ATMS vs filtro simple/OR-AND, justificaciones alternativas y pruebas discriminantes). Usa `CS-01`/`CS-02` como IDs de candidatos, no `FM-A`/`FM-B`. Si no existe pareja ejecutable legítima, detente con `BLOCKED_WITH_CAUSE` y presenta una alternativa para aprobación. Conserva resultados negativos y estados de insuficiencia. **No ejecutes un protocolo científico ciego completo, no reimplementes F5 íntegro, no conectes cloud real.**
>
> Devuelve PR draft con matriz requisito→test→artefacto→SHA, límites explícitos y hallazgos de una revisión adversativa; detente para decisión del investigador ante una incompatibilidad o nueva molécula cuya implementación requiera ampliar alcance. **No hacer merge** sin autorización.

---

## 14. Preguntas reservadas al investigador (antes de autorizar FM-B)

**D-FM-01 — RESUELTA:** el investigador aceptó el frente temporal FM como trabajo temprano sin cambiar la arquitectura F0–F9. La instrucción vigente autoriza FM-A únicamente.
**D-FM-02:** Tras FM-A-FEAS, ¿la primera pareja `CS-01`/`CS-02` debe representar `Customer` con servicio/abandono o comenzar por `Order`/trabajo usando piezas admitidas? El criterio de rigor es no convertir personas en pedidos por conveniencia.
**D-FM-03:** Si no hay política nativa de abandono admitida, ¿aceptar el bloqueo y aprobar una pareja alternativa ya admisible, o autorizar expresamente otra pieza con fuente, ecuación, contrato, presupuesto y pruebas? FM no incluye esa ampliación por defecto.
**D-FM-04:** ¿Aprobar reutilización concreta de código de `short` **después** de verificación de licencias y CI? No autoriza traslado de gold privado.
**D-FM-05:** ¿Quién realiza la revisión independiente del diff FM-B y adjudica contraejemplos?

Las decisiones abiertas **no impiden** el inventario y la factibilidad FM-A ni el trabajo sintético dentro de la pila autorizada; sí impiden ampliar la biblioteca con políticas nuevas, atribuir madurez ejecutable o fusionar resultados sin autorización.

---

## 15. Resultado que significaría «el paréntesis funcionó»

**No:** «más moléculas registradas», «otro workflow verde», «dos curvas distintas por cambiar una constante» o «ATMS eligió uno y arrojó 30/40».
**Sí:** `SystemModelCandidate` representa al menos **dos estructuras dinámicas hipotéticas estructuralmente distintas**, su estructura procede de **contratos moleculares versionados**, el motor rechaza conexiones inválidas, OpenModelica ejecuta ambas, las salidas se contrastan sin falsear identificación, las alternativas sobreviven mientras la evidencia no las distinga, y cualquier dependencia faltante queda explícita. Todo con referencias/hashes, reconstrucción de selección y comparación contra alternativas más simples.

**Conclusión provisional:** integrar moléculas ahora es una hipótesis de trabajo justificada para superar el `single_stock` conservado en PR #5/#6 y dar contenido real a IGC-SL. **No es todavía evidencia de que la biblioteca, ATMS o IGC completo añadan valor científico**. El propósito del paréntesis es producir precisamente una prueba que pueda apoyar o refutar esa promesa.
