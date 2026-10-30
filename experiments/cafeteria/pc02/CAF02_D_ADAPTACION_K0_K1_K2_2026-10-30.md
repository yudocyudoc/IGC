# CAF-02 · Adaptación mínima del brazo D al ciclo K0→K1→K2

**30 de octubre de 2026. Estado: ADAPTADOR OFFLINE SINTÉTICO; PENDIENTE G2 NATIVO, ATMS PERSISTENTE Y CUSTODIA. NO AUTORIZA DES.**

## 1. Corrección de interpretación histórica

CAF-01 no autoriza describir a D como predictor que falló en K2. En el resultado oficial, el MAE de construcción de su representante fue 1.992 pedidos, frente a 13.004 de M. La curva diagnóstica congelada de D no era un pronóstico competitivo: la regla G3/G4 produjo **ABSTAIN_POINT_PARAMETER_UNIDENTIFIABLE**. La cifra posthoc de aproximadamente 0.8605 pedidos MAE sobre esa curva (informada en revisión posterior) **no cambia la abstención histórica**, no se contabiliza como nueva victoria y no se usará para seleccionar la rejilla CAF-02.

Las capacidades 72/96 de CAF-01 podían ser indistinguibles al construir. En un campo futuro de mayor carga, sus pronósticos podrían divergir. Por ello **identificación individual** y **calidad del pronóstico del conjunto** deben evaluarse por separado.

El D2 histórico sí implementó un ciclo con nueva medición, revisión conjunta y ATMS de su propio brazo. Sin embargo, `scripts/arena_d_v2_revision.py:validate_trial` exige el mismo pulso del caso de construcción. **No es compatible literalmente** con el menú K1 CAF-02 de pulsos distintos. El nuevo adaptador opera a su lado, sin modificarlo ni afirmar que se ejecutó la persistencia ATMS.

## 2. Gramática real, no equivalencia ficticia de métodos

| Propiedad | D en CAF-02 | M en CAF-02 |
|---|---|---|
| Repertorio | Cadenas genéricas **D1/D2/D3** con 1, 2 o 3 stocks, sin pérdidas | E1 C00/C01 con 2 o 3 stocks |
| Parámetros | **Un `response_time` compartido** entre etapas; capacidad compartida | Tiempos por etapa, tránsito configurable y capacidades definidas en su repertorio |
| Calibración | RK4 existente `scripts.arena_d_v1_screen.integrate` | Integrador de moléculas E1 del protocolo |
| Nueva evidencia K1 | **Un único pulso y dato escogidos conjuntamente por M+D**; D puede proponer diagnóstico adicional sin cambiar prueba | M participa en la selección conjunta sobre su conjunto C00/C01 |
| Predicción K2 | **Todos** los candidatos adecuados proyectados; envolvente, punto condicionado por ancho o abstención | Igual política de puntuación de conjuntos |
| Capacidad nativa | Historial D1/D2 sí tuvo pruebas de OMC; **nuevo dominio todavía no certificado** | No implica G2 para toda la rejilla M |

No es correcto exigir el mismo número de configuraciones a dos gramáticas con distintas dimensiones o confundir más puntos de grilla con capacidad causal superior.

## 3. Política explícita de D, antes de mundo nuevo

En `CAF02_INDEPENDENT_K0K1K2_POLICY_PROPOSAL_2026-10-30.json` se añaden reglas de D, todavía **borrador no autorizado**:

- Estructuras D1, D2, D3 sin pérdidas; capacidad por etapa compartida de **48/72/100 pedidos/h** y tiempo de respuesta común de **1, 1.5, 2, 3, 6, 10 minutos**. Son 3×3×6=**54 candidatos nominales**. Se conservan los invariantes materiales y la conversión de unidades a horas del RK4 histórico.
- K0 recibe exclusivamente los dos valores públicos de entregas a minutos 5 y 10, entrada 1.2 pedidos/minuto. Evalúa todos los candidatos, con compuerta absoluta **MAE ≤1.0** y proximidad relativa **MAE ≤ mejor de cada familia +0.4**. Si ninguno cumple, abstención total y registro del mal ajuste.
- K1: el menú y la opción ejecutada son los **comunes de CAF-02** (1.0 a t10, 1.5 a t20, 1.8 a t30). D puede presentar una **preferencia diagnóstica** basada en su propio conjunto, pero la regla conjunta M+D selecciona un solo ensayo. Si ninguno de los brazos conserva candidatos, no se ejecuta K1; no se simula una prueba suplementaria. No se exige separación familiar completa para observar K1.
- Si K1 se ejecuta, proyectar **el pulso seleccionado**, no el pulso de K0. Mantener únicamente candidatos que ya sobrevivieron K0 y satisfacen `abs(predicción_K1 - observación_K1) ≤0.77 pedidos`. **No** volver a generar o reajustar toda la rejilla; la revisión es restricción de hipótesis condicionada a evidencia, no creación de topología.
- K2: proyectar por separado los conjuntos pre-K1 y post-K1 bajo la misma entrada pública K2 (1.35 pedidos/min), con seis tiempos. Conservar envolventes por D1/D2/D3 y la unión. Puntuar mediante la **misma función no probabilística** de CAF-02 (`ancho/2 + distancia_a_intervalo`); punto solo si ancho máximo ≤2 pedidos; conjunto vacío equivale a abstención, jamás a MAE cero.

La selección K1 conjunta usa un índice de reducción potencial de candidatos bajo conteos enteros hipotéticos, con pesos equilibrados por brazo/familia y tolerancia **idéntica de 0.77** para selección y revisión; no son probabilidades empíricas. Si no hay reducción prevista pero sí candidatos adecuados, la regla toma la primera opción y clasifica la medida como comprobación de adecuación. La separación robusta familiar sigue como diagnóstico, no veto.

La rejilla deliberadamente cambia respecto a CAF-01 (tiempos anteriores 7.5/15 min, capacidades 48/72/96) y ello se declara ahora **antes de un nuevo mundo**. No se reabre CAF-01 ni se proclama que esta elección es óptima. D sigue siendo un método diferente de M: compartir `response_time` entre stocks restringe lo que puede representar.

## 4. Presupuesto de cálculo y fronteras

La cota de integraciones RK4 matemáticas **sin reutilización de caché** es 54 (K0) + hasta 162 (tres opciones K1 para diagnóstico) + hasta 54 (opción común K1) + hasta 108 (dos versiones K2) = **378**. **No** son 378 corridas OpenModelica ni nuevas evaluaciones DES. Presupuesto propuesto de G2 nativo D: máximo 3 verificaciones representativas predefinidas; **todavía no ejecutadas** ni suficientes para certificar 54 combinaciones automáticamente.

El adaptador `caf02_d_k0k1k2_adapter.py` utiliza las funciones existentes `integrate` y `topology`. Su API acepta paquetes públicos de K0 y el resultado explícito del selector conjunto M+D; **rechaza** cambios de pulso, tiempo, tolerancias, rejilla o introducción de evidencia K1 sin elección. No acepta una política con estado `AUTHORIZED` en el preflight para evitar confundir prueba de software con campaña real.

El adaptador **no** lee el evaluador DES, el holdout de CAF-01, parámetros privados del mundo, otro brazo salvo la *opción pública K1*, ni archivos secretos. No llama Buffalo, OpenModelica ni genera/modifica moléculas. Su línea lógica de apoyo `ATMS_logical_support_proposed` no es una escritura efectuada al ledger: **ATMS persistente está pendiente**, al igual que la custodia G4a/G4b externa.

## 5. Criterios de aceptación antes de activar CAF-02

**Conectividad mínima demostrable:** código existente de D integra ambas entradas públicas con correctas conversiones de unidades; K0 evalúa exactamente 54 candidatos y preserva los compatibles; K1 usa la opción común distinta de K0 y filtra sin añadir candidatos; K2 conserva versiones anterior y revisada, junto con abstenciones. Los tests sintéticos deben demostrar que capacidades indistinguibles en K0 pueden divergir con mayor carga, sin forzar un punto.

**No acreditado por esta entrega:** rendimiento de D en un mundo DES independiente, paridad OpenModelica para la nueva rejilla, testigo G5 anterior a K0, event sourcing real de D+ATMS, adquisición de K1 del generador externo ni utilidad combinada de D/B/M.

**Comparación justa:** cada brazo recibe idénticos K0 y K1 públicos, pero usa su propia gramática y presupuesto documentados. El menú K1 ahora tiene aportaciones equilibradas de M y D. Esto no lo convierte en un diseño óptimo: los pesos por familia son convenciones de selección, no probabilidades de modelos verdaderos. El resultado de D puede mejorar, empeorar, abstenerse o ser menos identificable; cualquiera es publicable. Solo si **ambos** generan pronósticos K2 válidos y sellados se puede comparar su pérdida de conjunto en K2.

**Decisión:** D pasa de “diagnóstico opcional si es viable” a método comparativo principal **en el borrador**, sin afirmar que su contrato nativo o persistencia histórica ya esté integrado. No cambiar ni arquitectura D, ni E1, ni CAF-01.
