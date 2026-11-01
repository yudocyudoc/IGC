# CAF-15A — Protocolo previo: falsación por testigos con dos capacidades libres

**2026-10-31. Primer commit de CAF-15A antes de código y evaluación.** Rama `experiment/caf15a-independent-capacity-witnesses-20261031` basada en `191b9e830a01707ec5767bbf7dff65649653cdfb` (CAF-14 PR #126 Draft, apilado sobre #125/#124/#123, todos sin fusionar). No modificar módulos anteriores, motor DES ni tolerancias históricas.

## Premisa matemática y pregunta correcta

En CAF-14 cada estructura de dos cuellos nominales se parametrizó por **una capacidad común** `c_1=c_2=c`, de modo que un catálogo de dos capacidades independientes `(c_1,c_2)∈[55,110]^2` **contiene exactamente la familia diagonal anterior**. Por inclusión de conjuntos, **las cuatro parejas confundibles de CAF-14 jamás pueden volverse globalmente separables por liberar capacidades**, con los mismos programas y tolerancia. Las once parejas previamente separables *pueden perder separabilidad*: ¿podemos hallar CONTRAEJEMPLOS CONCRETOS (dos capacidades distintas) que invaliden al menos una de las once separaciones globales anteriores?

**Alcance del método:** búsqueda finita racional de testigos, con relectura DES nativa exacta, **no inversión/certificación exhaustiva del plano continuo bidimensional**. `NO_WITNESS_ON_FIXED_LATTICE` NO significa `ROBUSTLY_SEPARABLE_GLOBAL` ni `MODEL_GAP`. Testigo positivo es lógicamente válido en el continuo, porque cada punto de rejilla pertenece al dominio; falta de testigo no establece ausencia en los infinitos puntos restantes.

## Familia y rejilla congelada, sin búsqueda adaptativa

- Tres etapas FIFO en serie, duración homogénea determinista por etapa, sin compartición de recursos. Una etapa limitada tiene **1 servidor**, duración `60/c_s` min; no limitada **2 servidores**, duración 1 min. Las tres clases simples tienen una capacidad libre; las tres dobles tienen dos capacidades independientes (una por etapa restringida). No estocasticidad ni estimación de distribuciones.
- Dominio físico continuo `[55,110]` pedidos/h por etapa; **malla de testigos predeclarada y fija de 15 valores enteros**:
`C=[55,60,65,68,70,75,80,83,86,90,95,97,100,105,110]`.
- Todas las combinaciones cartesianas `C×C` para cada doble y todos los puntos C para cada simple. **3×15 + 3×225=720 configuraciones de hipótesis**, con **45 singles + 675 doubles**. Subconjunto diagonal: 6 estructuras×15=90; fuera de diagonal: 3×(225−15)=630. No añadir puntos de búsqueda guiados por resultados.
- Comparar las mismas estructuras con **capacidad compartida en la diagonal** vs **capacidades independientes en la malla completa** (A⊂B), para cada programa. Cada par estructural puede admitir parámetros físicos **diferentes** para las dos familias.
- Los resultados de CAF-14 sobre las once parejas robustamente separables eran exactos **para la familia diagonal continua**, y sirven como antecedente; las tablas de CAF-15A solo prueban testigos, nunca obtienen separabilidad global del modelo bidimensional por ausencia en la malla.

## Cuatro programas FIJOS

- `BASE`: entregas acumuladas K0 tasa 6/5/min t10 y K1 tasa 3/2/min t20.
- `F_R18_T20`: K0, K1, más waiting + stage_stock de las 3 primeras etapas t20 bajo tasa 9/5/min.
- `F_R25_T20`: K0, K1, más waiting + stage_stock de las 3 primeras etapas t20 bajo tasa 5/2/min.
- `F_R25_T25`: K0, K1, más waiting + stage_stock de las 3 primeras etapas t25 bajo tasa 5/2/min.

Todas las sondas siguen pulso `[0,20)`. Para cada configuración, registrar firmas enteras exactas con **la misma** configuración/capacidades en K0,K1,T (reinicios independientes), e incluir una validación masiva de paridad contra `CAF-01 run_toy_engine` y conservación. Tiempos de servicio son `Fraction(60,c_s)`, sin floats.

## Grafo de confusibilidad: solo testigos positivos certificados

Para dos firmas `x,y` de dos configuraciones de clases diferentes, la lectura común entera bajo **±1 pedido por canal** existe si `max_j |x_j−y_j|≤2`. Guardar firma, capacidades de **ambas** clases, lectura común entera y SHA256 del catálogo. El resultado es `WITNESS_FOUND_IN_LATTICE` o `NO_WITNESS_ON_FIXED_LATTICE`. Nunca publicar “separable globalmente” para modelo 2D sin un algoritmo certificado de regiones 2D.

Contabilizar separadamente aristas nuevas que aparecen al pasar de diagonal a malla total (falsan separación global de CAF-14) y las aristas antiguas preservadas. La confusibilidad por parejas **no es una relación de equivalencia transitiva**.

## Mundos de evaluación FIJOS (NO holdout externo)

- **24 dobles fuera de diagonal:** para cada par de etapas limitadas (01, 02, 12), capacidades ordenadas `(68,70), (70,68), (83,86), (86,83), (95,100), (100,95), (60,100), (100,60)`. Los dos órdenes son hipótesis físicas diferentes; los valores están todos en C. Son mundos sintéticos construidos con el mismo DES, NO representativos de distribución de capacidades empresariales.
- **5 controles de cuarta etapa:** capacidades `64,86,106` (repetidos de CAF-12/13/14) y **dos controles nuevos 160 y 220/h** (capacidad cuarta etapa mayor que demanda de 150/h). Las tres primeras etapas siguen configuración nominal de `CAF07B.make_physical_config((),c,extra=True)`. La etapa rápida **no es garantizadamente invisible**: aun sin cola introduce latencia y puede haber WIP.
- Total 29 mundos × 4 programas=**116 evaluaciones de mundos**, con 24 in-family amplios y 5 con topología ausente; no inferir tasas poblacionales.
- La verdad se usa exclusivamente en el evaluador físico y las métricas, **nunca** para elegir capacidades o testigos. Al estar la verdad in-family incluida en la malla, **24/24 retención de verdad es una prueba de implementación casi tautológica, no éxito de identificación**.

## Métricas y falsadores

1. Paridad de los cuatro programas con el DES nativo, incluidos tiempos exactos por servidor; un mismo vector de capacidad se utiliza en todas las sondas. Conservar balance `accepted=delivered+pending`, límites de servidores, FIFO y política de empates.
2. Preservación en grafo: aristas `diag ⊆ full` y, por construcción, 90 puntos diagonales presentes exactamente en las 720 configuraciones. Si se violan, es error de implementación.
3. **Testigo positivo re-ejecutable:** capacidad ordenada de las dos estructuras, observación y firma original, para el mismo programa. No imputar testigos de un programa a otro.
4. Reportar por programa `n_edges_diag_lattice`, `n_edges_full_lattice`, **qué aristas nuevas** aparecen, y las 11 anteriormente separables en `F_R25_T20/T25` que resultan falsadas por testigos nuevos.
5. Reportar `MODEL_INCOMPATIBLE_ON_LATTICE` únicamente como ausencia en la malla (NO incompatible en el continuo), falsos diagnósticos únicos sobre cinco estructuras extras, y número de clases sobrevivientes por mundo y por programa.
6. La malla fija es un muestreo intencional de parámetros, **no** una cuantificación geométrica ni probabilidad de mundos reales; no estimar porcentajes del plano confundible desde esta malla como si fuera uniforme físicamente.
7. La banda ±1 no es error instrumental calibrado; sin sensor temporal nuevo ni ruido estocástico. Los programas R25 son excitaciones artificiales y pueden ser inviables en negocio.
8. Guardar **720 configuraciones y todas las firmas en PLAN de evaluación** antes de consultar mundos, junto con SHA de head/checkout y manifest SHA256. El código calcula primero el banco completo sin mirar las verdades de mundos.
9. **GATE permanente:** `BLOCKED_LATTICE_WITNESSES_ONLY_NO_2D_GLOBAL_CERTIFICATION_NO_EXTERNAL_VALIDATION`. Mantener PR Draft sin fusionar; no promover estimadores, familias, selectores ni políticas.

## Decisión científica posterior

Los testigos positivos nuevos indicarían que la afirmación “11 separables” **no puede trasladarse** del modelo diagonal al modelo de dos capacidades independientes. Una ausencia de contraejemplo en la malla significaría **incertidumbre metodológica**, no robustez. CAF-15B requeriría una representación certificada de regiones paramétricas 2D, o una prueba probabilística calibrada por generador independiente, no un mero barrido más denso. Servicio estocástico y timestamp son siguientes factores SEPARADOS y preregistrables, no incorporados aquí.
