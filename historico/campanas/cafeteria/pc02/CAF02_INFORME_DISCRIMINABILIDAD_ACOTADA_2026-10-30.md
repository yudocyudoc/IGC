# CAF-02 — Discriminabilidad estructural C00/C01 después de calibración

**Fecha:** 2026-10-30. **Estado:** mapa sintético de capacidad del software, no prueba prospectiva y no evidencia independiente de recuperación estructural.

**Alcance:** corrige dos problemas identificados en la revisión del PR #100: el selector K1 no utilizaba la tolerancia aplicada luego en la revisión, y las pruebas de discriminación utilizaban candidatos elegidos directamente en lugar de los conjuntos obtenidos mediante calibración de ambas familias.

## 1. Corrección de la separación robusta

Si las predicciones de las familias calibradas son intervalos \(I_0=[a,b]\) y \(I_1=[c,d]\), se amplía **cada** intervalo con la misma tolerancia total declarada \(\epsilon=\epsilon_{\rm residual}+\epsilon_{\rm num}\):

\[
I_0^\epsilon=[a-\epsilon,b+\epsilon],\qquad
I_1^\epsilon=[c-\epsilon,d+\epsilon].
\]

La separación robusta es la distancia **entre intervalos ampliados**, cero si se intersecan. Solo se declara opción discriminante si esa distancia es **positiva** y alcanza el mínimo explícito. La función de revisión K1 exige usar exactamente la tolerancia previamente declarada y aplica esa misma tolerancia efectiva a cada candidato.

**Contraejemplo reproducido sin simulación:** C00=10, C01=10.2 pedidos, tolerancia residual ±0.15, margen numérico 0.01 y observación 10.1. Los intervalos ampliados se traslapan; la distancia robusta resulta **0** aunque la distancia original sea **0.2**. El selector ya no puede prometer discriminación basada únicamente en esa separación nominal.

La tolerancia numérica de este estudio es una asignación conservadora de **0.02 pedidos**, no una cota matemáticamente certificada del error global del solver. Antes de una prueba independiente se requiere respaldar esa asignación con verificación numérica pertinente.

## 2. Diseño cruzado fijo de la prueba interna

- **Familias:** C00, dos colas materiales; C01, tres colas con tránsito adicional. Únicamente moléculas de E1; capacidad del tránsito C01 fijada al valor del repertorio.
- **Cinco generadores sintéticos:** C00 con parámetros de rejilla; C01 con tránsito visible y parámetros de rejilla; C00 con parámetros fuera de rejilla; C01 con parámetros fuera de rejilla; C01 con tránsito casi invisible (\(\tau_t=0.1\) minutos). Las trayectorias generadoras y los candidatos provienen **de las mismas ecuaciones y del mismo integrador**.
- **Dos rejillas:** COARSE (2 valores por tiempo en preparación/despacho, 1 capacidad y 2 tiempos de tránsito) y REFINED (4 por tiempo, 2 capacidades, 3 tiempos de tránsito).
- **Dos máscaras de K0:** SPARSE, minutos 5 y 10; RICHER, minutos 5, 10 y 20.
- **Mismo menú K1 para todos:** entregas acumuladas tras reinicio a 10 min con 1.0 pedidos/min, a 20 min con 1.5 pedidos/min o a 30 min con 1.8 pedidos/min. Se selecciona solamente una.
- **Reglas numéricas comunes:** entrada K0 1.2 pedidos/min; MAE absoluta máxima de K0 **0.8 pedidos**; cercanía al mejor MAE de cada familia **0.4**; aceptación residual K1 **0.20**; guardia numérica K1 **0.02**; brecha mínima **0.05** después de ampliar ambos intervalos.

Estas opciones son **supuestos explícitos de un ejercicio interno**. Se creó el script con esta matriz antes de ejecutar su primera corrida; después se añadieron pruebas de regresión y presentación. No constituye pre-registro externo ni ceguera frente a un mundo nuevo.

El procedimiento ejecutado en CI es **K0 observado → calibración independiente de C00 y C01 → conservación de todos los supervivientes → elección K1 a partir de los supervivientes → evidencia K1 sintética → revisión**. Los K2 preparados no contienen verdad K2 y **no se puntúan**.

## 3. Resultados auditables

La matriz contiene **20 combinaciones de escenario × rejilla × máscara**, no 20 mundos independientes.

| Clasificación | Condiciones | Recuento |
|---|---|---:|
| Ambas familias sobreviven K0 | Hay una ambigüedad estructural inicial efectiva | **14** |
| K1 con separación robusta | La medición propuesta puede distinguir los conjuntos completos con la tolerancia fijada | **2** |
| Menú K1 insuficiente | Ambas familias persisten pero **ninguna opción aislada** garantiza distinguirlas | **12** |
| K0 ya no conserva dos familias adecuadas | El objetivo de una revisión discriminante K1 no está activado | **6** |
| Tras K1 queda una sola familia | Solo entre los dos casos con diseño K1 admisible | **2** |
| Familia generadora descartada después de K1 pese a sobrevivir K0 | Se examinó en dos revisiones K1 activadas | **0** |

**Las cinco familias generadoras declaradas conservaron su etiqueta estructural en K0 en las veinte combinaciones**, pero ello es esperable dado que los datos están generados por el propio modelo. Tampoco significa que los parámetros exactos de los casos off-grid estuvieran presentes en la rejilla.

Resumen por escenario (C=COARSE, R=REFINED; S=SPARSE, M=RICHER):

| Generador | C/S | C/M | R/S | R/M |
|---|---|---|---|---|
| **C00 en rejilla** | Ambiguo | Ambiguo | Ambiguo | Ambiguo |
| **C01 tránsito visible** | K1 → C01 | Solo C01 desde K0 | K1 → C01 | Solo C01 desde K0 |
| **C00 fuera de rejilla** | Ambiguo | Ambiguo | Ambiguo | Ambiguo |
| **C01 fuera de rejilla** | Solo C01 desde K0 | Solo C01 desde K0 | Solo C01 desde K0 | Solo C01 desde K0 |
| **C01 tránsito casi invisible** | Ambiguo | Ambiguo | Ambiguo | Ambiguo |

En el caso **C01 con tránsito visible, K0 escaso**, la separación robusta K1 fue de **3.140 pedidos** en rejilla gruesa y **0.355 pedidos** en rejilla refinada. Tras observar K1 sintético, ambas revisiones eliminaron C00; quedó C01 con 1 configuración (rejilla gruesa) y 4 (refinada). **Esta reducción no demuestra que el motor descubra el mecanismo verdadero fuera de este experimento autogenerado.**

Con **K0 más informativo**, C00 no sobrevivió desde construcción para ese mismo caso. Por tanto, es incorrecto atribuir a K1 una identificación adicional allí.

Para C00 y el tránsito casi invisible el selector devolvió **sin separación garantizada en el menú**. El solapamiento de intervalos para **una medición** no impide descartar ciertos candidatos según su valor real ni descarta que un vector de varias mediciones discrimine conjuntamente. Es una afirmación **local al menú, tolerancias, intervalo temporal y rejilla**.

## 4. Tres límites que deben permanecer visibles

1. **C01 puede aproximar arbitrariamente a C00** cuando el tiempo de la tercera etapa tiende a cero en régimen lineal no saturado. Con observaciones de resolución y precisión finitas, una discriminación universal es una exigencia imposible. Este estudio solo muestreó \(\tau_t=0.1\) y las rejillas definidas; no certifica límites continuos.
2. **Más candidatos cambian la separación garantizada**. En el caso C01 visible, refinar la rejilla redujo la brecha robusta de 3.140 a 0.355. No se puede presentar la capacidad discriminante de una rejilla gruesa como propiedad global del repertorio.
3. **Verdad y candidatos no son independientes:** las pruebas validan cableado, coherencia matemática, materialidad y tratamiento de ambigüedad de un procedimiento construido con sus propias ecuaciones. No miden generalización, validez real, ni recuperación de mecanismos de un DES ajeno. No se ejecutó K2 ni se reabrió CAF-01.

## 5. Qué permite decidir y qué no

**Sí está justificado:** continuar hacia un protocolo independiente acotado que conserve C00/C01 y las alternativas paramétricas, con K0 de información limitada, menú K1 fijado, tolerancias coherentes y K2 nuevo. El resultado negativo «ninguna medición del menú garantiza separación» es una respuesta legítima, no un fallo a reparar cambiando retrospectivamente el mundo.

**Todavía no está justificado:** cambiar arquitectura E1, atribuir éxito causal/estructural a los dos casos sintéticos con revisión, solicitar discriminación universal o considerar el 0/2 de descartes indebidos como una tasa general de seguridad.

La siguiente decisión de investigación es si vale la pena comparar **una medición K1 aislada** frente a **un pequeño vector K1 de observaciones**, sin utilizar resultados futuros para diseñarlo; esa ampliación necesita otra política y otro presupuesto. Mantener intacto el menú probado para preservar lo ya medido.

**Reproducción y artefactos:** `caf02_structural_k0k1k2.py`, `caf02_discriminability_map.py`, tests respectivos y workflow `.github/workflows/caf02-class-proposal-preflight.yml`. La ejecución CI publica `DISCRIMINABILITY_SYNTHETIC_GRID.json` completo y `DISCRIMINABILITY_SYNTHETIC_REPORT.md` con las 20 combinaciones.
