# CAF-12 — Informe de resultados y auditoría adversativa (posterior a CI)

**Estado:** análisis posterior a resultados del protocolo CAF-12, no preregistro adicional. **PR #124 Draft**, rama apilada sobre CAF-11 #123 (también Draft); sin modificaciones a CAF-11 ni al motor DES.

## Procedencia exacta

- Primer commit de protocolo antes de implementación y mundo de evaluación: `c99fd8d8167b13062d573be721cff8f21b437d4d` ([protocolo](CAF12_PROTOCOLO_OBSERVABILIDAD_CONTINUA.md)).
- **CI canónica**: [GitHub Actions #41256491076](https://github.com/yudocyudoc/IGC/actions/runs/41256491076), **7/7 tests PASS**, predicciones simbólicas/paridad física y ejecución de todos los 32 mundos.
- **Head probado:** `acc4f68ea376e6498712439228fc9c418f4b9e59`. **Checkout de merge sintético:** `266808d82f20e54f00c6edd81edc49649e6103ce`. Son SHAs diferentes y aparecen por separado en JSON del artefacto.
- [Archivo original de auditoría (cinco archivos)](https://github.com/yudocyudoc/IGC/actions/runs/41256491076/artifacts/13063442120): `00B_EXACT_REGIMES_PRE_EVALUACION.json` (48 familias × esquemas calculadas antes de consultar mundos), `00_PLAN_PRE_EVALUACION.json`, `01_RESULTADOS.json`, `02_INFORME.md`, `03_MANIFIESTO.json`. Verificación independiente de digest SHA256 de los otros cuatro archivos conforme al manifiesto: **4/4 coinciden**.
- CI verde demuestra invariantes de ingeniería bajo el mismo DES. No es prueba ciega, validación externa, calibración de sensor ni diagnóstico de empresas reales.

## Comparación de esquemas FIJOS

**27 mundos con clase nominal representada (9 de cuello único, 18 dobles), 5 controles de cuarta etapa fuera del catálogo.** Cobertura verdadera de clase/parametro = **27/27** con los ocho esquemas; el parámetro c permanece fijo dentro de cada inversión conjunta K0+K1+K2.

| Esquema | Costo ordinal K1+K2 | Únicos correctos /27 | Ambiguos /27 | Con seis clases /27 | Únicos falsos sobre 5 controles fuera de catálogo | Controles incompatibles con las seis familias |
|---|---:|---:|---:|---:|---:|---:|
| BASE (solo entregas K0/K1) | 1 | 0 | 27 | 27 | 0 | 0 |
| PREP_Q | 3 | 0 | 27 | 12 | 0 | 0 |
| DISPATCH_Q | 3 | 0 | 27 | 9 | 0 | 0 |
| DELIVERY_Q | 3 | 2 | 25 | 14 | 0 | 0 |
| DISPATCH_STOCK | 3 | 0 | 27 | 12 | 0 | 0 |
| PREP_DISPATCH_Q | 5 | 1 | 26 | 9 | **4** | 0 |
| ALL_QUEUES | 7 | 2 | 25 | 9 | **0** | **4** |
| STRESS_PREP_DISPATCH | 8 | 2 | 25 | 4 | **4** | 0 |

**Desglose in-family relevante:**
- Los únicos mundos con clase estructural única correcta bajo algún esquema fueron `SINGLE_68_2` y `SINGLE_83_2`, ambos un solo cuello nominal en **entrega**. Ningún mundo con cuello doble quedó con una única clase; tampoco los cuellos únicos en preparación/despacho.
- El resultado no demuestra que «entrega es siempre identificable»; depende de esos parámetros, del menú, horizonte de 20 minutos y bandas ±1.
- Los escenarios de observación con dos colas (preparación/despacho) no son seguros frente a las topologías extra fuera de catálogo: cuatro controles obtuvieron `entrega` como *única* clase superviviente, aunque físicamente la restricción verdadera estaba en una **cuarta etapa**.
- La misma inferencia con la cola de entrega añadida (`ALL_QUEUES`) dejó **sin ninguna clase compatible** a esos cuatro controles. Significa `FAMILY_INCOMPATIBLE_UNDER_FIXED_OBSERVATIONS_AND_BOUNDS`, **no «cuarta etapa demostrada»**.

## Contrafactual físico controlado: observar dos colas versus las tres

Para `EXTRA_64`, cuarta etapa desconocida: K0=7 entregas, K1=17 entregas, bajo tasa 1.5/min en minuto 20 las colas de preparación/despacho/entrega leídas fueron **[0,0,0]**.

Con `K0,K1,waiting_prep=0,waiting_dispatch=0`, la familia de tres etapas deja solamente `entrega` compatible. La misma familia, **sin cambiar K0/K1, tiempo ni tasa del campo**, y agregando `waiting_entrega=0`, deja **0 clases** compatibles. Repite en `EXTRA_86`, `N_EXTRA_62`, `N_EXTRA_78`.

Es una observación crucial sobre el riesgo de **certificación con familia incompleta**, pero no constituye un detector universal: `N_EXTRA_106` conserva seis clases incluso con las tres colas. El valor de observar una variable depende de en qué régimen de campo (capacidad y demanda) esté operando el sistema.

## Observabilidad y riesgo

**Más información puede elevar el riesgo de falsa certeza.** La inferencia por regiones continuas impide eliminar la clase verdadera por discretizar c cuando el mundo pertenece a la familia, pero **no garantiza reconocer estructuras ausentes**. Más sensores pueden reducir un catálogo incompleto a una sola explicación equivocada. La tercera cola, en estas condiciones, ofrece un *chequeo adicional capaz de falsificar* esa explicación.

El resultado no justifica elegir de inmediato `ALL_QUEUES` como política óptima: es más costosa (costo ordinal 7, no calibrado); solo logra 2/27 clases únicas; no resuelve ningún cuello doble; no demuestra nada respecto a servicio estocástico o resolución de sensores.

**Asimetría estructural:** las clases doble cuello comparten el mismo parámetro c por diseño y sus comportamientos pueden resultar observacionalmente equivalentes a un cuello único aguas arriba. Para determinar el límite de identificabilidad se necesitan pruebas con otros regímenes, otros horizontes y posiblemente timestamps/servicio por pedido, no otro score sobre el mismo menú.

## Análisis matemático y salvaguardas

- El módulo CAF-12 representa `start_s,i(d)=max(arrival_s,i(d),end_s,i-m_s(d))`, `end_s,i(d)=start_s,i(d)+duration_s(d)`; `waiting=arrived-started`, `stage_stock=arrived-completed`. Estas fórmulas son **exactas solo** para el tándem FIFO homogéneo declarado, con tiempos de servicio deterministas e idénticos dentro de cada etapa.
- Las expresiones de `Clock` son continuas lineales por tramos racionales; se incluyen **todos** los cortes del valor 10/20 minutos de las expresiones de evento pertinentes, se evalúan singleton y los intervalos abiertos, y los extremos de capacidad se convierten racionalmente sin redondear.
- La CI prueba concordancia de `delivered`, `waiting` y `stage_stock` con el DES nativo, para seis estructuras y capacidades enteras/fraccionarias, y reproduce **exactamente BASE de CAF-11** en sus veinte mundos. Los tests no sustituyen una demostración independiente de la recurrencia o el comportamiento de servicio en otros motores.
- 27/27 verdaderos parámetros cubiertos es un **control de autoconsistencia**, porque la predicción usa el mismo DES/estructuras que genera los mundos in-family. No inferir generalización ni riesgo poblacional de este resultado.
- Los 12 nuevos mundos adicionales siguen siendo sintéticos dentro del modelo y del diseño de investigadores; los veinte históricos ya se habían observado en CAF-11.
- La tolerancia ±1 **no está calibrada como ruido real**. Los costes son unidades ordinales, no recursos de operación medidos.
- Compartir tasa/instante con K1 para K2 significa observar otros sensores del **mismo snapshot físico** bajo DES determinista, no una replicación independiente. El caso STRESS también cambia tasa, por lo que sus cambios no pueden atribuirse solo a más canales.

## Próxima hipótesis para discusión Claude + GLM (NO iniciar automáticamente)

En lugar de otro torneo de políticas, estudiar **condiciones de distinguibilidad estructural** entre familias continuas, bajo observaciones adicionales y servicios aleatorios. Comparar diseños donde se conoce la duración por pedido y por etapa, registros de transición, múltiples horizontes y sensores con error realista; valorar cuándo una familia es falsificable y cuándo la ambigüedad persiste estructuralmente.

También convendría separar **diagnóstico interno de la familia** de **validación del mecanismo** mediante una regla explícita de suficiencia, que exija evidencia independiente de la estructura asumida antes de certificarla.

**Gate científico permanente:** `BLOCKED_SAME_DES_PHYSICS_UNCALIBRATED_TOLERANCE_NO_EXTERNAL_VALIDATION`. Mantener Draft, no fusionar ni promover por CI.
