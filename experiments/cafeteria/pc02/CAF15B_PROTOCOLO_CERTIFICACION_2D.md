# CAF-15B — Protocolo previo: certificación de exclusión sobre capacidades continuas independientes

**Fecha local 2026-10-31. PR nuevo apilado sobre CAF-15A PR #127 Draft (head 896b816f4a95b3990790ee55a011a3f843530b0f).** Este documento es el PRIMER commit de CAF-15B ANTES de escribir código o ejecutar análisis. No modificar motor CAF-01, CAF-11–15A, sus protocolos, otras ramas o hacer merge.

## Pregunta

CAF-14 certificó 11/15 pares globalmente separables bajo modelos de capacidad COMÚN a 150 pedidos/h, t=20 o t=25, con ±1 conteo; 4/15 quedaron confundibles. CAF-15A permitió dos capacidades independientes por estructura doble en una MALLA finita y no halló testigos adicionales; eso NO certifica las 11 separaciones en el continuo bidimensional.

**¿Cuáles de esas 11 parejas se pueden CERTIFICAR globalmente separables con c1,c2 independientes continuas (cada una [55,110]), usando una técnica de exclusión de regiones con aritmética racional y prueba auditable?** Hay tres estados de salida mutuamente excluyentes:
- `CONFUSABLE_WITNESS_CERTIFIED`: dos capacidades racionales por familia y firmas exactas con diferencia L∞≤2. El testigo es prueba de confusión en el CONTINUO.
- `SEPARABLE_EXHAUSTIVE_BOX_CERTIFIED`: unión certificada de cajas excluidas cubre TODO el producto de parámetros y, en cada una, algún canal separa los rangos de firmas por >2 pedidos; imposible una lectura común ±1 bajo este modelo.
- `UNRESOLVED_NOT_CERTIFIED`: agotó recursos, profundidad o no pudo excluir, sin testigo; nunca anunciar separabilidad global ni incompatibilidad.

No confundir “no hallado en rejilla” con prueba negativa. No usar cifras de acierto o nuevos mundos.

## Física y operadores

- Familia de 3 etapas FIFO homogéneas CAF-01. Etapa limitada 1 servidor, tiempo determinista `60/c_s` minutos; no limitada 2 servidores, 1 minuto. Las dos etapas limitadas reciben parámetros independientes `c1,c2∈[55,110]`, equivalentes a duraciones `d1,d2∈[6/11,12/11]`; sencillos solo d1. Toda familia tiene una dimensión igual al número de cuellos (1 o 2).
- Mismos programas de CAF-14, **solo** `F_R25_T20` y `F_R25_T25`: K0 (6/5/min, t10, entregas), K1 (3/2/min, t20, entregas), y seis canales de colas+stocks a 5/2/min, t20 o t25, pulso [0,20). Cada familia utiliza el mismo vector de capacidades en TODAS las sondas. No agregar canales ni ajustar tolerancia: ±1 por conteo; dos cajas se cruzan si todas las diferencias de firmas son ≤2.
- Los 15 pares de seis estructuras se reevalúan en ambos programas (30 contrastes), pero las **11 parejas anteriormente separables** son el foco de certificación. Las cuatro históricamente confundibles deben seguir teniendo testigos por inclusión de submodelo diagonal. NO alterar las conclusiones del protocolo CAF-15A.
- Sin ruido, costes, servicio estocástico, sensores temporales privilegiados ni OOD. El objetivo es **demostración matemática condicional** a una recurrencia física ya auditada, no validación empírica.

## Técnica de prueba certificada por intervalos

Para cualquier caja cerrada racional de parámetros `B_M=∏[l_s,u_s]`, cada tiempo de llegada, inicio y final de etapa en el tándem FIFO es **monótono NO DECRECIENTE** en cada duración de servicio (`max`, `+` preservan monotonía); por tanto, los clocks evaluados en la esquina de todas las duraciones inferiores y superiores proporcionan cotas exactas para todos los clocks interiores.

Con `N_E(t)` número de eventos `≤t`, obtenemos `N_E(upper)≤N_E(d)≤N_E(lower)` para cualquier `d∈B_M`. Construir intervalos inclusivos **conservadores** para ocho lecturas:
- `delivered=N_finish_last` exacta acotada por ambas esquinas;
- `waiting_s=N_arrived_s-N_started_s` y `stage_stock_s=N_arrived_s-N_finished_s`, cotas `[max(0,A_min−B_max), max(0,A_max−B_min)]`. La correlación entre términos puede hacerlas amplias, pero NUNCA elimina un valor real. Endpoints incluidos; empates t=10/20/25 usan `≤`.
- Para dos cajas `B_M, B_N`, descartar TODO su producto si existe un canal j con `lower_M[j] > upper_N[j]+2` o `lower_N[j] > upper_M[j]+2`. La desigualdad estricta certifica que no existen lecturas enteras ±1 compatibles en ese producto de parámetros.
- En las cajas no excluidas, comprobar firmas exactas en esquinas y centros racionales; si algún par es compatible (L∞≤2), guardar testigo verificable sobre capacidad continua exacta. De otro modo, dividir deterministamente una dimensión de una de las cajas por su punto medio racional; **ambas mitades cerradas** se solapan solo en la frontera y su unión conserva todo el dominio.
- Profundidad máxima **32 divisiones** por rama, presupuesto máximo **5,000 nodos** por par; se conservan los estados sin resolver si estos límites se alcanzan. Heurística de división fija: elegir familia con mayor amplitud total de sus intervalos de conteos (suma de `high-low`); desempatar por orden de familia; dentro de la familia elegir parámetro con mayor anchura relativa respecto al dominio (desempatar por índice). Si el coste se vuelve excesivo, la CI puede abortar por timeout y NO se publica un resultado certificado de esa ejecución.
- Priorizar auditoría de todos los pares sin seleccionar casos basados en resultados. Procesar 2 programas ×15 pares en orden lexicográfico y producir artefactos. Prohibido elevar presupuesto, cambiar división o escoger subconjunto tras resultados sin nuevo protocolo.

## Evidencia verificable

1. Guardar `00_PLAN_BEFORE_SOLVER.json` que identifique SHA head vs checkout, 15 parejas×2 programas, física, operadores, presupuesto y gate antes de evaluar. No se utilizan mundos evaluadores ni decisiones de selector.
2. Para un par `SEPARABLE_EXHAUSTIVE_BOX_CERTIFIED`, emitir un **árbol de certificado** exacto: hoja de exclusión incluye canal y rangos enteros verificados; nodo interno registra eje y fracción de corte; la raíz cubre `[6/11,12/11]^{k_M+k_N}`. Un **verificador independiente del buscador** recorre el árbol desde la raíz y recalcula las cotas a partir de la recurrencia para cada hoja. Sin árbol completo y verificación PASS: jamás publicar certificado.
3. Para un par confundible, emitir duración/capacidad racional y firmas y validarlas tanto por el calendario max-plus como por `des.run_toy_engine`, en instantes y canales correctos. Un testigo verdadero basta para refutar la separación del continuo.
4. Para `UNRESOLVED`, emitir número de nodos y motivo. Ni “cero testigos” ni “cero falsos” son prueba negativa.
5. Pruebas de sonido: reloj monotónico en servicio, cota incluye todos los puntos de una pequeña malla de estrés en cajas racionales, extremos y empates; lectura comparada contra DES; árbol sintético con cobertura defectuosa debe ser RECHAZADO por el verificador; ejemplo artificial separable y ejemplo con testigo; semántica exacta ±1 vs ±2.
6. Guardar `01_RESULTADOS.json`, `02_INFORME.md`, `03_MANIFIESTO.json` con SHA256. Gate de ingeniería si algún certificado no se reproduce. No aceptar “test aprobado” como validación externa.
7. **Alcance fuerte pero condicional**: si todas las ramas de un par se excluyen mediante las cotas matemáticamente válidas, puede llamarse certificado de separabilidad de ese par sobre la familia exacta. No es un teorema del mundo real ni prueba de ausencia de estructuras fuera de catálogo. Si el algoritmo no logra certificar: **INDETERMINADO**.

## Integridad y entrega

**Gate:** `BLOCKED_DETERMINISTIC_SAME_DES_UNCALIBRATED_SENSOR_NO_EXTERNAL_VALIDATION`. PR CAF-15B siempre Draft y apilado sobre CAF-15A sin merge; requiere revisión adversativa independiente del verificador y de la monotonía en empates antes de promover las afirmaciones matemáticas. Ningún resultado justifica una intervención empresarial de sobrecarga artificial.
