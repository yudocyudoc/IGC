# CAF-L001 — límites temporales de dos recepciones observadas · D/B/M

**Estado:** caso reproducible en el GitHub IGC. **No** validación de servicio ni tres predicciones competitivas. Este caso es independiente del PR #169 sobre otro video.

## Evidencia y procedencia

Se conserva **sin alterar los bytes** de \`metricas.csv\` aportado por el investigador como \`metricas_original.csv\`, SHA-256:

\`f45e12578813f75ae6f201e5390f93e39bf115aed2849edd704072f09544fc28\`

9 filas F01–F09 del lote L001 (2 recipientes), no 9 lotes independientes. Todas las cotas están expresadas en **segundos de video**. El reloj físico no se certificó. Los identificadores H01/H04/H05/H06/H07 no equivalen automáticamente a eventos E132–E136 del CSV maestro.

El archivo \`maestro_contrastes.json\` registra **solo las dos filas relevantes** que se extraen del maestro aportado anteriormente (SHA-256 original completo \`2ab597aea3b381cccdd8b7bc06bb696c518977847130daf444b8aedb4866f958\`). **El maestro completo de 495 KB no se re-publica aquí**. Las cotas del maestro antiguo para MD-M001 y MD-M002 no se solapan respectivamente con F01 y F08; no se corrigen ni se combinan.

## Resultado físico del ejecutor de referencia

\`reference.py\` usa programación lineal (SciPy/HiGHS) para buscar tiempos de H04–H07 compatibles **simultáneamente** con F01–F09.

- Una trayectoria matemática admisible, **no** instantes exactos: H01=0, H04=41.598, H05=45.392, H06=47.197, H07=48.585 segundos de video.
- Stock del lote pendiente de recepción = **2 → 1 → 0**. Recipientes pendientes + recibidos = **2**.
- Área F09, derivada de F07 y F08: **92.589** recipiente·segundo de video. No evidencia independiente.
- Recepciones simultáneas o ambas en el fin de recogida incompatibles con estas cotas **si los hitos están bien anotados**.
- Las cotas son intervalos de medición de un único lote, **no valores para ajustar una distribución uniforme/triangular de tiempo de servicio**.
- El resultado **no** identifica demanda del local, preparación de recetas, capacidad de personal, utilización del barista ni el tiempo real de servicio.

## Los tres brazos siguen autónomos

\`three_arms.py\` ejecuta el **chequeo nativo real** de cada brazo sobre la misma evidencia (V0 \`arm_view\`, mismo hash), sin atribuir resultados ajenos:

| Brazo | Trabajo realmente efectuado | Estado |
|---|---|---|
| **D** determinista | Gramática \`arena_d_v01.topology/lint_structure\`: dos alternativas estructurales admisibles, sin estimar parámetros | **PARTIAL** |
| **B** Buffalo | Solicitud independiente preparada para el productor original, sin D/M ni llamada al proveedor | **BLOCKED** |
| **M** molecular | Compositor nativo de Short E1: se enumeran grafos de ingeniería; ninguno queda identificado como explicación del lote | **PARTIAL** |

No hay candidatos seleccionados para explicar L001, ni corridas OpenModelica, ni tres trayectorias con G2/G3. Los tres carriles se registran por separado en ledger F1a, con soporte ATMS; estos artefactos no constituyen prueba de explicación.

**Próximo requisito medible**: operador observacional desde cada método hacia *dos recepciones individuales*, con una regla para tratar cotas y parámetro de latencia sin usar la trayectoria testigo como verdad puntual. Buffalo necesitaría una inferencia propia explícitamente autorizada antes de declararlo evaluado.

## Reproducir desde GitHub Actions

\`\`\`bash
python -m pip install scipy
python -m unittest discover -s experiments/cafeteria/l001 -p 'test_*.py' -v
python -m experiments.cafeteria.l001.three_arms --out artifacts/caf-l001
\`\`\`

La CI publica \`00_reference.json\`, \`01_common_evidence.json\`, \`02_{D,B,M}_native.json\`, \`03_ATMS.json\`, \`04_report.json\` y \`L001_ledger.sqlite\` como artefactos de GitHub Actions.
