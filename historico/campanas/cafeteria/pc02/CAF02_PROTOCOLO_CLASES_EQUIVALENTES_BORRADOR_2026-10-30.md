# CAF-02 — Componente auxiliar histórico de calibración C00 (PR #99)

**RECTIFICACIÓN 2026-10-30:** Este documento explica un subsistema útil, pero **no representa el objetivo principal de CAF-02**. Para la pregunta estructural original del plan v3.0 §7 y la secuencia K0→K1→K2, consultar [CAF02_PROTOCOLO_DISCRIMINACION_ESTRUCTURAL_K0_K1_K2_2026-10-30.md](CAF02_PROTOCOLO_DISCRIMINACION_ESTRUCTURAL_K0_K1_K2_2026-10-30.md). La justificación operacional externa de cada rango **no es prerrequisito universal** para una investigación sintética; sí debe distinguirse de admisibilidad matemática y de identificación. La regla relativa sola era defectuosa: el calibrador exige además adecuación absoluta y admite cero candidatos. Los umbrales actuales son sintéticos e ilustrativos. **No usar los pasos P0–P5 aquí como autorización para CAF-02.**

---


**Fecha:** 2026-10-30. **Estado:** \`BORRADOR_NO_AUTORIZADO\`. Este documento y su código son una **preparación**, no un preregistro válido, un nuevo mundo ni una evaluación científica. **No ejecutar un nuevo DES o revelar datos reservados** hasta completar las compuertas externas.

## 1. De dónde sale esta pregunta

En CAF-01, **REF-CAF MAE 1.6667, REF-SCALE 2.0833, M 14.1717** en una evaluación única; el histórico G5 no acreditó custodia anterior a construcción, aunque el G4 sí quedó timestamped antes de evaluación. Ese resultado queda inmutable. Una exploración posterior **solo en construcción** mostró que las dos moléculas C00 pueden aproximar esa trayectoria al variar los tiempos de respuesta: 22 combinaciones nominales compatibles, 11 al agrupar capacidades, **7 curvas distintas** al permutar tiempos no saturados. Eso **no** constituye pronóstico prospectivo ni identificación de la etapa.

Nueva pregunta: **¿puede la calibración con datos de construcción identificar un conjunto de parámetros compatibles cuya envolvente de entregas prediga bien un escenario futuro independiente, frente a REF-CAF y REF-SCALE, sin exigir identificación individual de tiempos de preparación/despacho?**

La prueba se limitará inicialmente a **C00**, dos \`BoundedQueue\` existentes en E1, con \`release=min(capacity,stock/responseTime)\`. No se cambian moléculas, topologías ni ecuaciones. No se atribuirá recuperación causal o estructural a un ajuste de entregas solamente.

## 2. Equivalencia durante construcción NO garantiza equivalencia futura

Para condiciones iniciales vacías y **sin saturación**, la transferencia es \`H(s)=1/[(1+tau_p*s)(1+tau_d*s)]\`: permutar tiempos conserva exactamente las entregas, aunque cambien inventarios internos. Si la capacidad conjunta \`C ≥ 60 λ_construcción\`, no limita flujos del pulso fijo; distintos valores grandes de \`C\` se vuelven equivalentes **en ese campo de construcción**.

**Contraejemplo prospectivo que debe pasar el CI sintético:** con \`λ_construcción=72/h\`, capacidades \`72/h\` y \`100/h\` y mismos tiempos producen curvas de construcción equivalentes. Si \`λ_futuro=90/h\`, el límite de 72/h **puede** activarse; las predicciones de ambos miembros dejan de ser equivalentes. **No seleccionar un representante y descartar el otro.**

Reglas: agrupar únicamente cuando la equivalencia está respaldada por las ecuaciones y el régimen sin saturación. No permutar tiempos en miembros cuyo tope pueda actuar; no equiparar dos curvas por MAE cercano. Conservar **todos los miembros nominales** de cada clase observacional para calcular sus pronósticos individuales futuros.

## 3. Procedimiento propuesto de calibración

1. **Congelar antes de generar el nuevo mundo:** frontera material, proceso y parametrización del generador privado, código fuente DES, rangos operativos justificables de \`responseTime\`, capacidades, pulsos, tiempos, candidato C00, presupuesto y reglas cuantitativas de aceptación/abstención. \`responseTime\` significa escala agregada de respuesta \`stock/flujo\`, **no** tiempo de servicio unitario automáticamente.
2. Exigir compromiso hash del nuevo mundo más **testigo externo independiente anterior a construcción**. El recibo G5 de CAF-01 no es transferible; el nuevo mundo debe tener identidad, secreto y nonce independientes. **No se permite repetir** el DES de CAF-01 como nuevo holdout.
3. Ejecutar **una sola construcción** del mundo nuevo, con entrada conocida y entregas en seis tiempos, exponer un paquete idéntico a todos los métodos y referencias. Dejar constancia de cualquier intento fallido.
4. Para C00, integrar cada combinación operativamente admisible y calcular \`MAE_construcción\`. **Regla propuesta pendiente de aprobación:** conservar toda combinación con \`MAE <= MAE_mínimo_grilla + tolerancia\`; no elegir después de ver el futuro. Documentar error numérico y todos los candidatos, incluidos los rechazados.
5. Agrupar únicamente por equivalencia de construcción demostrada, **preservando todos sus miembros**, y proyectar cada miembro bajo el **pulso futuro público**, sin observaciones futuras. Reportar mínimo/máximo de entregas en cada tiempo y ancho máximo. **Regla propuesta pendiente de aprobación:** pronóstico puntual solo si la envolvente completa es suficientemente estrecha según un umbral anterior al futuro; si no, abstención puntual y publicación de la envolvente, con sus límites interpretativos. El punto ilustrativo es el centro de los límites y **no** pretende ser una trayectoria de un único modelo.
6. Calcular **REF-CAF** y **REF-SCALE** por sus reglas de construcción, sin leer A(t) privada futura ni D(t) del futuro. Distinguir una referencia que se abstiene. Las referencias se sellan junto con las predicciones del conjunto de C00.
7. Obtener **testigo externo independiente** del paquete exacto de predicciones G4 **antes de ejecutar/revelar** el futuro. Solo entonces, mediante autorización separada, ejecutar **una** evaluación DES y puntuar sin cambiar clases, parámetros ni umbrales.

**No adoptar automáticamente** como regla futura la banda \`+0.25 pedidos\` que se usó exploratoriamente en CAF-01. Del mismo modo, el umbral de ancho de envolvente de la fixture no es un compromiso científico. Su justificación, unidades y validez deben registrarse y fecharse antes del nuevo mundo.

## 4. Contrato de resultados del estudio futuro (pendiente de preregistro)

- Primario propuesto: MAE/RMSE de entregas acumuladas en t=5,10,15,20,30,40 para puntos admitidos, comparado separadamente con REF-CAF y REF-SCALE.
- Obligatorio: tasa de abstenciones, ancho máximo/promedio de la envolvente, cobertura empírica de seis observaciones (sin interpretar como intervalo probabilístico ni seis réplicas), porcentaje de clases e instancias compatibles que sobreviven construcción, diversidad de pronósticos futuros y consumo del presupuesto.
- Una envolvente muy ancha puede cubrir la verdad sin capacidad predictiva útil: exigir evaluar **anchura y cobertura juntas**, nunca premiar cobertura aislada. No puntuar abstenciones como errores cero ni como victorias.
- Si una clase se identifica solo hasta permutaciones, no exigir asignación de \`responseTime\` a roles físicos. La identificación de etapas necesitaría observables de preparación/despacho independientes.
- Una corrida sintética única seguirá sin autorizar inferencia estadística general. Nuevos mundos independientes y replicación son asuntos de otro presupuesto y protocolo.

## 5. Implementación actual y restricciones de seguridad

Código preparatorio: \`experiments/cafeteria/pc02/caf02_class_predictor.py\`. Test: \`test_caf02_class_predictor.py\`. CI: \`.github/workflows/caf02-class-proposal-preflight.yml\`.

El ejecutable **solo admite fixtures sintéticas** y políticas declaradas explícitamente \`DRAFT_NOT_OPERATIONALLY_APPROVED\`; rechaza identidad CAF01/CAFN, campos extra que pretendan aportar verdad futura, cualquier declaración de custodia externa verificada y cualquier configuración real. Ejecuta únicamente integraciones locales de las ecuaciones C00 **dentro de GitHub Actions**; no importa el motor DES, archivos G3/G4 de la evaluación, secretos, OpenModelica ni Buffalo. El futuro aparece únicamente como **pulso público hipotético**.

Se usan números de prueba con las tasas históricas 1.2 y 1.5 pedidos/min para demostrar el contraejemplo; **son fixtures, no una decisión aprobada para un experimento nuevo**. Los tests verifican que 72/100 dejan de ser equivalentes bajo carga mayor y obligan a abstenerse en el pronóstico puntual cuando el ancho excede el umbral ilustrativo. Nunca se debe usar este artefacto sintético para reclamar validación prospectiva.

## 6. Compuertas pendientes para convertir el borrador en un experimento independiente

| Compuerta | Requisito verificable | Estado |
|---|---|---|
| P0 — Justificación operacional | Rangos de \`responseTime\` y capacidad fundamentados con evidencia externa al DES | **PENDIENTE** |
| P1 — Política cuantitativa | Tolerancia de compatibilidad, umbral de ancho, pérdidas y abstenciones, comparadores, presupuesto y calendario fechados | **PENDIENTE** |
| P2 — Mundo independiente | Nueva configuración/noise/nonce, fijación del código y testigo externo **antes de construcción** | **PENDIENTE** |
| P3 — Construcción | Único DES construcción, datos públicos y ledger | **NO EJECUTADO** |
| P4 — Predicciones | Clases compatibles, todas las variantes futuras, referencias y sello externo previo al holdout | **NO EJECUTADO** |
| P5 — Evaluación | Autorización separada, una corrida, scoring, abstenciones y reporte íntegro | **NO AUTORIZADO** |

**Decisión:** implementar y probar la capacidad de calibrar clases es legítimo ahora. Ejecutar una nueva evaluación, aprobar tiempos físicos o afirmar recuperación estructural **todavía no**.
