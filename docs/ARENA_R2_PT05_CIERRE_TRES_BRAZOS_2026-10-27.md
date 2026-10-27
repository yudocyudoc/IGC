# IGC · Arena — Cierre PT-05 R1→R2 y primer corte de memoria

**Fecha:** 2026-10-27  
**Estado experimental:** `R2_CERRADO_CON_BUFFALO_G2_CONDICIONAL_Y_ESTÍMULO_DIVERGENTE`.  
**Procedencia:** R1 real PR #54, expediente PR #55, Buffalo R2 7K PR #59, D/M PR #58, Buffalo R2 16K [Actions #40490534985](https://github.com/yudocyudoc/IGC/actions/runs/40490534985), PR #61 PT-05.

## Decisión científica de cierre

Se cierra R2 **como ronda de revisión y trazabilidad**, no como identificación de una estructura correcta ni comparación válida de tres métodos bajo un mismo estímulo. Ninguna corrección del modelo se introdujo durante PT-05. No hubo inferencias ni nuevas simulaciones.

| Brazo | R1 real | Disposición R2 | Frontera de evidencia |
|---|---|---|---|
| D | Seis alternativas simuladas G2; menor RMSE descriptivo 0.150205 items | `RATIFY_SIX_ALTERNATIVES` | Sin nueva observación independiente, no se ejecutó D2 ni se seleccionó un verdadero mecanismo |
| M (M3) | Tres candidatos G2; mejor RMSE 0.316560 items; umbral 0.020 | `RATIFY_ABSTENTION` | Sin candidato padre seleccionado; no se ejecutó M2 ni calibración |
| B (Buffalo) | Nativo con G1 negativo, ninguna trayectoria, ningún RMSE | R2 primera revisión 7K truncada; segunda 16K produjo nativo completo 16 variables/16 relaciones, ejecutado en OpenModelica | G2 condicional en pulso diferente al exigido; G3 e identificación causal **no demostrados** |

### Dos llamadas Buffalo R2, dos resultados distintos

1. **7K**, [Actions #40486060023](https://github.com/yudocyudoc/IGC/actions/runs/40486060023): una llamada real; 5,044 entrada y 7,000 salida; `finish_reason=length`, respuesta JSON incompleta. Sin revisión nativa, sin G2.
2. **16K**, [Actions #40490534985](https://github.com/yudocyudoc/IGC/actions/runs/40490534985): una llamada real distinta, sin reintentos; 5,044 entrada, 4,222 salida, `finish_reason=stop`, nativo completo (SHA256 de bytes `c47a0752755fc10b3ec7b626677afcb26e962e7e3cf4582bb70aa7488694f229`). OpenModelica compiló e integró con Euler 0–8 h a `dt=0.125h`. Que la segunda llamada use menos de 7K tokens **no prueba que elevar el límite haya causado el éxito**: es otra muestra estocástica.

## Original vs. posprocesamiento suplementario

El dictamen **original** de la segunda llamada fue `G2_OR_G3_REJECTED`, `MISSING_BUFFALO_SERIES:pending_work`. El evaluador anterior usaba nombres de columnas de otro modelo Buffalo. El archivo CSV real existía, y OpenModelica informó simulación completada.

El nuevo `scripts/arena_b_native_series.py` obtiene roles semánticos a partir de los dos stocks y dos flujos del **nativo original**: un stock con entrada y salida de material (pendiente) y otro que recibe entregas acumuladas; se exige coincidencia de puertos e identificadores Modelica. **Rechaza** topologías ambiguas y columnas faltantes; no adivina aliases ni reescribe datos. `scripts/arena_b_construction_check.py` permanece sin modificar. El posprocesamiento es una *vista de lectura*, y tanto el CSV como el informe automático conservan sus hashes y estatus originales.

Del CSV original, la evaluación suplementaria confirma:
- conservación material Euler: residuo máximo ~1.33×10⁻¹⁵ items;
- RMSE **descriptivo** en tiempos 0/1/2/4 h: **0.355555 items**; excluyendo t=0: **0.410560 items**;
- llegada modelada en t=1.5 h: **0.85 items/h**, contra **1.7 items/h** del pulso rectangular público;
- entrada acumulada discretizada: **2.65625 items**, contra **3.4 items** requeridos (déficit 21.875%).

**Conservación de masa respecto de una entrada equivocada no demuestra fidelidad al experimento.** Ningún valor de RMSE debe usarse para ordenar Buffalo frente a D/M como si los tres hubieran recibido el mismo pulso, y el RMSE B de R1 es matemáticamente inexistente.

La nueva ecuación de salida sí referencia la capacidad, pero en el recorrido probado el caudal sin límite no supera el umbral, por lo que **la capacidad está conectada sin demostrar intervención restrictiva efectiva**. El multiplicador de congestión sí cambia con el stock. Esta lectura no valida la estructura como identificada.

## Memoria F1a / ATMS

`scripts/arena_r2_pt05_close.py` recompone en una base SQLite temporal:
- archivado auténtico de R1;
- las dos disposiciones D/M registradas como políticas conservadoras;
- el evento Buffalo de truncamiento 7K y la respuesta nativa 16K;
- el dato físico respaldado por SHA del CSV, y la discrepancia de estímulo;
- el dictamen automático negativo **junto al** diagnóstico suplementario, sin sustituirlo.

El informe también ejecuta `as_known_at` antes y después de incorporar el resultado Buffalo, conserva las vistas D/M iguales y prueba el soporte lógico ATMS de una trayectoria condicional a partir de nativo y CSV. Los tiempos del replay son **marcas administrativas declaradas de reconstrucción**, no fechas históricas del experimento. ATMS rastrea dependencia entre evidencias, no establece verdad causal.

## Qué NO se concluye y cuál es el siguiente ensayo

No se demuestra causalidad, G3 PASS, selección de un ganador o generalización. No se equipara verificación del generador con fidelidad al caso. No corresponde reparar de oficio el pulso ni pedir una tercera llamada para mejorar un número.

El resultado deja dos problemas explícitos para una siguiente ronda: **fidelidad al estímulo** y **capacidad de distinguir mecanismos cuando distintas estructuras pueden producir trayectorias parecidas**. PT-06/R3 puede evaluar estas preguntas mediante nuevos protocolos y perturbaciones expresamente delimitadas, evitando consumir el holdout futuro de PT-07/R4.

**Prueba de aceptación:** [Actions PT-05](https://github.com/yudocyudoc/IGC/actions/runs/40571563807), reejecución sin proveedores con los tres artefactos reales, pruebas negativas de puertos y columnas, memoria temporal, y permanencia del dictamen original. El workflow añade reporte JSON y base SQLite de evidencia; no modifica los archivos históricos.
