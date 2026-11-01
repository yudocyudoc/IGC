# CAF-11 — Adjudicación post-CI: recuperación paramétrica sin identificabilidad estructural

**Fecha:** 2026-10-31 (hora del experimento; ejecución CI registrada en UTC al cambiar el día). **Estado:** experimental, sin promoción ni merge.

## Fuente canónica y procedencia

- **[GitHub Actions #41255335298](https://github.com/yudocyudoc/IGC/actions/runs/41255335298)**, **7/7 tests PASS** y corrida de laboratorio OK.
- Head sometido a pruebas: `5b6a309072b5bba8f5f8569f58f2934400a41c7f`. El checkout de un PR puede ser un **merge sintético distinto**; los dos SHAs están registrados en `00_PLAN_PRE_EVALUACION.json` y `01_RESULTADOS.json`.
- [ZIP de evidencia canónica](https://github.com/yudocyudoc/IGC/actions/runs/41255335298/artifacts/13061869747): cuatro archivos `00_PLAN_PRE_EVALUACION.json`, `01_RESULTADOS.json`, `02_INFORME.md` y `03_MANIFIESTO.json`. El plan incluye el catálogo de regímenes racionales **antes** de consultar los mundos de evaluación; el manifest registra SHA256.
- Hubo una [primera corrida fallida #41255302666](https://github.com/yudocyudoc/IGC/actions/runs/41255302666) por **un error en el nombre de una llave de test** (`truth_class_EVALUATOR_ONLY` vs `true_class_EVALUATOR_ONLY`). Se corrigió el **test**, no el inversor ni el protocolo. Esa corrida no es canónica.

## Resultados obligatorios, sin mezclar clases y parámetros

| Métrica | Banco de 24 puntos | Familia continua exacta |
|---|---:|---:|
| Mundos cuya estructura real está en la familia | 18 | 18 |
| Casos que conservaron la **clase** real | **6/18** | **18/18** |
| Casos con conjunto vacío, siendo in-family | **12/18** | **0/18** |
| Casos que conservaron el parámetro físico real en su estructura | No garantiza la capacidad exacta; no es una familia continua | **18/18** |
| Casos resueltos con clase única entre los 18 | No es métrica de progreso del laboratorio | **0/18** |
| Casos con más de una clase superviviente | Variable | **18/18** |

- **Todos los 18 mundos representados conservaron las seis clases estructurales posibles** después de K0 y K1. Eso revela un límite del esquema de observación; **no hay diagnóstico único de cuello** pese a la recuperación paramétrica. La cobertura 18/18 es el resultado matemáticamente esperable al construir las observaciones con el **mismo generador que describe la familia correcta**, tolerancia ±1 y c real en dominio; **no constituye validación externa**.
- **Ambos** controles de cuarta etapa `EXTRA_64` y `EXTRA_86` conservaron también las **seis** estructuras conocidas como explicaciones de sus conteos. La compatibilidad de un modelo falso dentro del catálogo no es evidencia de topología real.
- **Ninguna** incompatibilidad vacía puede interpretarse directamente como descubrimiento de topología nueva. Incluso un certificado exacto solo se refiere a incompatibilidad de la familia física con las observaciones bajo el modelo de errores.

## Un caso numérico auditable

En `SINGLE_68_0`, las observaciones físicas exactas fueron `K0=[8]`, `K1=[20]`. El banco puntual respondió `∅`, mientras que el inversor continuo aceptó las seis estructuras.

La familia con cuello único en preparación admitió el intervalo exacto de capacidad

`[3420/53, 3960/53)` pedidos/h ≈ **[64.53, 74.72)**.

La familia con cuellos simultáneos en preparación+despacho admitió

`[450/7, 1035/14)` pedidos/h ≈ **[64.29, 73.93)**.

Ambas regiones son compatibles con la misma lectura K0/K1. La capacidad verdadera de la primera estructura (68 pedidos/h) está dentro del intervalo, pero la evidencia no discrimina entre ambos mecanismos. Los intervalos y extremos provienen de fracciones exactas y del tratamiento explícito de empates `t <= horizonte`, no de una interpolación numérica.

## Qué garantiza el algoritmo, y qué no

Se usa únicamente la subfamilia DES determinista con:
1. Tres etapas en serie, servidores idénticos por etapa, disciplina FIFO y tiempo de servicio fijo; una capacidad común variable en etapas designadas y 2 servidores de 1 minuto en las demás.
2. El reloj de salida del pedido i en etapa s admite la recurrencia `D[s,i](d)=max(A[s,i](d),D[s,i-m_s](d))+t_s(d)`; para entradas deterministas ordenadas, servicios homogéneos y ausencia de adelantamientos, el servidor libre que puede atender el siguiente pedido es el que finalizó `i-m_s`.
3. Constantes, sumas y máximos de funciones afines racionales generan funciones continuas lineales por tramos; las raíces con los tiempos K0 y K1 se aíslan con racionales exactos. Evaluar cada **intervalo abierto** entre cortes y cada **singleton** de corte agota las salidas posibles de conteo en el dominio `c∈[55,110]`.
4. Esta exhaustividad es *condicional al cumplimiento de la recurrencia para la familia elegida*. La CI incluye paridad con DES nativo en las 6 estructuras, 11 capacidades (incluida una fraccionaria) y bordes de simultaneidad. Los tests son evidencia de implementación, no sustituto de la justificación matemática. El protocolo y motor DES original no se alteraron.

No hay intervalos de incertidumbre estadísticamente calibrados, ni modelo de sensor medido, ni servicio aleatorio, ni dos capacidades libres independientes, ni filas prioritarias. Los conteos agregados K0/K1 **no demuestran causalidad de la etapa**.

## Consecuencia para el siguiente laboratorio

**No repetir el torneo de selectores.** Se ha separado con evidencia la pregunta de *cobertura del parámetro* de la pregunta de *distinción entre estructuras*.

La siguiente hipótesis debería ser **de observabilidad**: con regiones continuas correctas, ¿cuál canal adicional ayuda a separar las familias? Comparar entregas solamente vs colas por etapa vs stocks vs tiempos de servicio individuales, manteniendo pruebas de paridad y evitando fugas de verdad o servicio determinista que hagan trivial el resultado.

Deben predeclararse los esquemas observacionales, la precisión real o cota de error, los modelos de servicio estocástico cuando corresponda y los costos; conviene comenzar con un ensayo de factibilidad algebraica sobre canales de cola sin afirmar todavía eficiencia de un selector.

**Gate:** `BLOCKED_SAME_DES_PHYSICS_UNCALIBRATED_TOLERANCE`. Sin fusión, sin despliegue, sin legitimación de inferencias de estructura ni de detector de unknown.
