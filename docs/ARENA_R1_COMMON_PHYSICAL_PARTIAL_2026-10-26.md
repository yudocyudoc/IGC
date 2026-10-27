# Arena R1 — primer recorrido físico común D/M (parcial, B bloqueado)

**Base recuperada:** IGC/main@1ac282f7e6cafd2280c7e0ae69a0330d35d2b222. **Estado:** prueba de construcción, NO R1 con tres inferencias.

## Caso y comparabilidad

La entrada primaria existente es el pulso sintético 1.7 items/h durante 2 horas y observaciones de entregas acumuladas en t=0,1,2,4 horas. Un solo snapshot hash público alimenta a D/B/M; cada adaptador declara sus supuestos. D recibe además parámetros nominales explícitos en un archivo distinto: no han sido medidos ni ajustados y no equivalen a una condición paramétrica idéntica para M o B.

**D:** se renderizan las seis estructuras propias de la gramática original (1 a 3 stocks, con/sin pérdida), con hashes autenticables por estructura y por Modelica; se ejecuta cada una con OpenModelica real, DASSL 0–8 h, 160 intervalos. Cada CSV pasa la prueba de conservación preexistente y se informa RMSE para cuatro observaciones y para los tres puntos no iniciales. Sin cota instrumental solo cabe una métrica descriptiva, no una selección causal.

**M:** se reutiliza intacta la política M3 adaptada por Astra a la misma evidencia común. Sus tres clases originales E1 conservan parámetros nominales, G0/G1 condicionales, linter y bibliotecas. OpenModelica 1.26.5, SystemDynamics 2.1.2 y MSL 4.0.0, 0–4 h, 80 intervalos. La decisión utiliza los límites originales (0.020 de RMSE absoluto y 0.035 de margen), sin refit ni modificación del catálogo.

**Buffalo:** no hay presupuesto ni autorización explícita nueva. No se pide inferencia, no se reciclan B2–B5 como si respondieran a este corte y se conserva BLOCKED con 0 llamadas al proveedor.

## Alcance del artefacto

El workflow arena-r1-common-physical.yml guarda fuentes .mo originales, CSV reales de los nueve candidatos D/M, logs de OMC, manifiestos y un informe JSON conjunto. El informe incluye por candidato G0 acotado a procedencia y emisión, G1 limitado al propio método, G2 conservación material y G3 descriptivo/condicional. No pretende paridad completa de simuladores ni unidad comparativa idéntica de parámetros. Los dos métodos usan versiones diferentes de OpenModelica: queda expresado en el informe.

La función evaluadora no ejecuta OpenModelica; lee resultados producidos en un job separado. Por ello un contador previo solver_calls=0 describe solamente el proceso Python, mientras el workflow sí ejecuta nueve modelos. La evidencia de ejecución está en sus logs/CSV y no se infiere de una etiqueta PASS.

**Pendientes explícitos:** B real desde la misma fuente y presupuesto autorizado; feedback a cada brazo con sus propios residuos; segundo estado y ledger/ATMS compartido de R2; REF predeclarada; perturbaciones y mediciones de reserva nuevas. No se anuncia ganador, R1 completo ni validación ciega.

**Protocolo de error:** falla la preparación si se cambia un modelo, estructura, supuesto o identidad de entrada. La adjudicación falla ante ausencia de CSV, filas o tiempos inesperados y no confunde un fallo técnico de solver con una refutación empírica.
