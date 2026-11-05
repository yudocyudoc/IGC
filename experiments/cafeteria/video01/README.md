# CAF-VIDEO-01 · Primer caso físico observacional sobre Arena D/B/M

**Estado:** ejecución exploratoria de compatibilidad nativa, no inferencia estructural ni predicción. No es una nueva arquitectura. Fuente: los CSV versionados en el PR #169; sin modificar sus registros.

## Pregunta
¿Puede cada brazo de Arena tomar observaciones de recipientes y equipo de una cafetería sin convertirlas en pedidos, tasas, horas físicas o entregas ficticias?

## Fuente común (ningún brazo recibe resultados rivales)

- P031, video segundo 2888: **≥3 recipientes con contenido** identificables en la región frontal; 2893 también ≥3. En 2894 la **región visible** está despejada. No equivale a inventario cero ni entrega.
- P045, video segundo 4118: jarra próxima a lanza y **≥1 taza con superficie montada** presentes en la misma muestra. No demuestra vapor.
- P045, segundo 4144: **≥2 tazas montadas** presentes en una muestra. No demuestra dos pedidos.
- El reloj del archivo no se certifica como tiempo físico; son anotaciones no ciegas. Las series no son observaciones de POS.

## Ejecución en tres brazos reales

| Brazo | Ruta **nativa existente** | Resultado permitido |
|---|---|---|
| **D** | \`scripts.arena_d_v01.topology + lint_structure\` | **PARTIAL**. Dos estructuras admisibles en la gramática de pedidos, pero no ajustadas ni mapeables automáticamente a recipientes. Sin G2. |
| **B** | Frontera de solicitud original Buffalo | **BLOCKED**. Solicitud neutral construida desde las mismas observaciones; **no enviada**. Sin propuesta Buffalo fabricada ni gasto de proveedor. |
| **M** | \`scripts.arena_m_short_e1.prepare\` + compositor Short E1 | **PARTIAL**. Enumeración nativa de grafos de ingeniería. Ninguno seleccionado para explicar los recipientes; no hay operador observacional ni parámetros calibrados. |

Los tres reciben por \`arm_view\` el mismo \`common_input_hash\`. Cada submission se verifica bajo el contrato V0. **Una enumeración de grafos no es un diagnóstico del video; construir el request B tampoco significa que Buffalo haya participado como productor de hipótesis.**

## Memoria y conservación

Se usa el motor ATMS existente para registrar que el límite **local** de tres recipientes se apoya en la observación, mientras que cualquier afirmación acerca de la **capacidad total de despacho** necesita una suposición adicional. La ejecución crea un ledger F1a local con las tres submissions de sus carriles separados; no integra ni publica una base persistente de producto.

**No se identifican:** arribos POS, pedidos pendientes, duraciones reales, caudales, capacidad máxima, función de la lanza, productividad o cuellos. No podemos aplicar conservación de pedidos usando conteos de recipientes. OpenModelica=0 corridas. Buffalo=0 inferencias.

## Resultado que cambia el siguiente paso
Ya no hace falta producir más anotaciones de todos los movimientos. El primer dato que falta para pasar a comparación dinámica es una correspondencia física entre **pedido aceptado → objeto(s) en proceso → pedido entregado** con reloj y frontera verificables. Sin ella, D y M pueden expresar familias generales, pero no deben generar métricas del negocio a partir de conteos visuales. Buffalo requiere una llamada acotada si se decide probar su inferencia nativa con este tipo de evidencia.

No se crea cuarta vía, no se convierte un análisis convencional en sustituto de un brazo y no se confunde la abstención con éxito predictivo.

## Repetir sin proveedores ni solver

\`\`\`bash
python -m unittest discover -s experiments/cafeteria/video01 -p 'test_*.py' -v
python -m experiments.cafeteria.video01.run --out artifacts/caf-video-01
\`\`\`

El resultado se conserva en \`report.json\`, \`D/B/M_native_and_submission.json\`, \`atms_support.json\` y \`case_ledger.sqlite\`, disponibles como artefacto de GitHub Actions.
