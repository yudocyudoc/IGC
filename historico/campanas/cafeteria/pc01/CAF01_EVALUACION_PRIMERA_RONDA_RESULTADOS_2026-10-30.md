# CAF-01 · Resultado de primera evaluación reservada (post-only)

**Fecha:** 2026-10-30. **Estado:** resultado científico descriptivo, reproducido sin nuevas simulaciones. **Mundo:** CAF-01 sintético, único escenario DES reservado, seis tiempos futuros. **Protocolo:** v0.3, con excepción histórica G5 expresamente autorizada, **no** validación estricta de custodia previa a construcción.

## Procedencia, ejecución y verificaciones

- [G3 selección original PR #92](https://github.com/yudocyudoc/IGC/pull/92): 25/25 filas, D G2 3 PASS, M G2 6 PASS, Buffalo CAF01 G1 FAIL por duplicación material; no reinterpretarlo como solo error de adaptador.
- [G4 congelado PR #93](https://github.com/yudocyudoc/IGC/pull/93): corrida nativa de pronósticos [#41006338774](https://github.com/yudocyudoc/IGC/actions/runs/41006338774), modelos D y M. Archivo preholdout exacto SHA-256: 8ce3d5713df480201dfcb982b5aa291857a09584eeb5fa2456cacfdff179df8f.
- [G4 testigo externo PR #94](https://github.com/yudocyudoc/IGC/pull/94): [FreeTSA RFC3161 #41006622753](https://github.com/yudocyudoc/IGC/actions/runs/41006622753), firma comprobada, acredita anterioridad del G4 exacto.
- [PR #95](https://github.com/yudocyudoc/IGC/pull/95): ejecutor reservado único, con excepción expresa de custodia histórica G5. [Corrida científica DES #41014808222](https://github.com/yudocyudoc/IGC/actions/runs/41014808222) SUCCESS, primer run/intento, **1 DES evaluación** consumido, sin reintentos ni nuevos Buffalo/RK4/OMC. [Artefacto original #12958813063](https://github.com/yudocyudoc/IGC/actions/runs/41014808222/artifacts/12958813063).
- [Post-only #41015166807](https://github.com/yudocyudoc/IGC/actions/runs/41015166807): verificó SHA de los JSON de evaluación, correspondencia exacta entre lectura y reporte, paquete G4 y testigo RFC3161 original, estado G5, conservación física pública y reproducción byte-lógica de puntuación con la función G4 ya existente. **Sin DES, OMC, RK4, proveedor ni nueva selección.**

## Seis observaciones nuevas reservadas DES

Entrada futura pública 1.5 pedidos/min durante 20 min; reinicio explícito en cero. Observación de entregas acumuladas D(t), variable primaria congelada. No se tratan pendientes derivados como evidencia independiente.

| Minuto | Aceptados acumulados A(t) | Entregados acumulados D(t) | Pendientes agregados A-D |
|---:|---:|---:|---:|
| 5 | 8 | 3 | 5 |
| 10 | 15 | 8 | 7 |
| 15 | 23 | 13 | 10 |
| 20 | 30 | 18 | 12 |
| 30 | 30 | 28 | 2 |
| 40 | 30 | 30 | 0 |

La conservación A=D+P en cada lectura se contrastó contra el resultado del generador. Estas seis observaciones forman una sola trayectoria correlacionada, no seis mundos independientes.

## Evaluación competitiva: regla congelada antes de revelación

| Participante | Estado congelado | MAE entregas (pedidos) | RMSE entregas (pedidos) |
|---|---|---:|---:|
| **REF-CAF** | referencia empírica simple de capacidad efectiva | **1.6666666666666667** | **1.8257418583505538** |
| REF-SCALE | escalamiento proporcional, control obligatorio | 2.0833333333333335 | 2.5617376914898995 |
| **M_C00_C72** | único pronóstico puntual condicionado admisible de M | 14.171672895486658 | 15.973459931364483 |
| D | **ABSTAIN_POINT_PARAMETER_UNIDENTIFIABLE**: solo curva diagnóstica, no pronóstico competitivo | no aplicable | no aplicable |
| Buffalo | **NO_VALID_CANDIDATE**, G1 FAIL material | no aplicable | no aplicable |

- Diferencia de MAE **REF-CAF − M = −12.505006228819992** pedidos. La ventaja prospectiva predeclarada para M de al menos +1 pedido **NO** se alcanzó.
- Diferencia de MAE **REF-SCALE − M = −12.088339562153324** pedidos. M también es peor que el simple escalamiento.
- En el minuto 40, M había pronosticado **7.92951644544607** entregas y el DES observado entregó **30**. Este déficit predictivo terminal es una observación diagnóstica del modelo M seleccionado, sin autorización para retocar parámetros.
- El MAE de M en construcción (13.004 pedidos, de la revisión de G3) ya era muy superior al del representante D (1.992); esto es contexto de construcción, **no** una comparación competitiva de D en holdout.
- REF-CAF gana este caso descriptivo; **no** implica que todas las aplicaciones SD/IGC sean inferiores a modelos simples ni prueba un mecanismo causal.

## Límites científicos y decisión

1. **Resultado adverso conservado:** M no mostró ventaja predictiva sobre REF-CAF ni REF-SCALE. No replantear el mundo ni reentrenar con los seis valores reservados.
2. **Cobertura:** D se abstuvo formalmente por no identificabilidad de parámetros aunque posea curva representativa diagnóstica; Buffalo no tuvo candidato válido por el error de flujo material. No asignar MAE a abstenciones.
3. **Comparación justa:** REF-CAF y REF-SCALE fueron calculados exclusivamente desde construcción y congelados con G4; ningún comparador vio la evaluación para seleccionar o ajustar.
4. **Custodia:** el G4 firmado sí existe desde antes de evaluación. G5 histórico declara NOT_VERIFIED: el secreto del mundo DES no tenía custodia externa anterior a construcción acreditada por el recibo disponible. Se ejecutó la evaluación bajo **excepción explícita**; no aseverar preregistro histórico independiente íntegro. Además hubo una construcción histórica y una reproducción GitHub, excediendo el techo original de una construcción.
5. **Validez:** comparación descriptiva sobre un mundo sintético único; seis observaciones dependientes; sin inferencia estadística general, validación causal, identificación estructural o demostración de utilidad en negocios.
6. **Próximo problema científico — NO aprobado como ejecución:** diagnosticar por qué M quedó tan lejos del comportamiento observado y si su repertorio/retardos pueden representar esta familia de trayectorias, **sin** editar retrospectivamente su resultado ni construir otro mundo ad hoc. Comparar contra la simplicidad de REF-CAF como referencia fuerte. Esto pertenece a una **nueva** pregunta, no a una revisión de G4.

**Cierre:** la primera vuelta CAF-01 está puntuada y preservada como resultado negativo para M y positivo para el comparador REF-CAF en este mundo. No hay ninguna necesidad de volver a ejecutar la evaluación.
