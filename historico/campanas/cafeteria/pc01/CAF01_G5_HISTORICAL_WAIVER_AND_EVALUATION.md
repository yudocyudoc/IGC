# CAF-01 — Evaluación reservada y excepción histórica G5

**Fecha: 2026-10-30. Estado: propuesta ejecutable, evaluación NO realizada.**

El sello temporal RFC3161 [#41006622753](https://github.com/yudocyudoc/IGC/actions/runs/41006622753) acredita existencia de los pronósticos G4 previamente a la evaluación. **No acredita retrospectivamente la custodia externa del mundo DES antes de construcción.** El recibo público original G5 tiene verification_status = NOT_VERIFIED y future_evaluation_reveal_authorized = false. La evaluación por excepción no debe confundirse con el cumplimiento de esa precondición histórica.

## Secuencia GitHub-only

1. El PR ejecuta pruebas sintéticas y preflight de los artefactos originales G4 [#41006338774](https://github.com/yudocyudoc/IGC/actions/runs/41006338774), paquete SHA-256 8ce3d5713df480201dfcb982b5aa291857a09584eeb5fa2456cacfdff179df8f, y testigo FreeTSA [#41006622753](https://github.com/yudocyudoc/IGC/actions/runs/41006622753). **Sin DES, secretos, RK4, OpenModelica ni proveedor.**
2. Una vez fusionado el PR, el workflow de evaluación tiene exclusivamente disparo manual desde main, primera corrida e intento, sin reintentos. Exige dos cadenas literales: RUN_CAF01_RESERVED_DES_EVALUATION_ONCE y ACCEPT_UNVERIFIED_HISTORICAL_G5_CUSTODY. No se ejecuta por merge ni por push.
3. Reutiliza el secreto existente CAF01_PRIVATE_ENVELOPE_B64 del entorno GitHub caf01-construction. Comprueba la misma configuración y nonce contra el compromiso G5 y hashes de las fuentes originales. No guarda ni imprime parámetros del mundo.
4. Verifica nuevamente testigo RFC3161, bytes G4 y estados D (abstención), M (condicional), Buffalo (sin candidato válido), y dos referencias. A continuación invoca exactamente **un** DES con cero iniciales, pulso 1.5 pedidos/min durante 20 min, horizonte de 40 min, lectura en minutos 0,5,10,15,20,30,40, 30 aceptaciones programadas y sin pérdidas.
5. Conserva únicamente observaciones agregadas públicas y puntuación MAE/RMSE de M, REF-CAF y REF-SCALE con la función G4 congelada. D y Buffalo NO reciben puntuación competitiva. M mejora descriptivamente sobre REF-CAF solo si la diferencia de MAE es de al menos 1 pedido; REF-SCALE es control independiente.
6. Registra manifiesto SHA, consumos y estatus explícito DESCRIPTIVE_EVALUATION_WITH_HISTORICAL_G5_PROTOCOL_DEVIATION. Los fallos después del marcador de invocación cuentan como intento gastado y no habilitan repetición.

## Limitaciones del resultado

La construcción original tuvo **una ejecución histórica fuera de GitHub y otra reproducción dentro de GitHub**, ya superiores al techo inicial de una construcción. No se restablece ni oculta ese consumo. La excepción histórica G5 se preserva tanto en la documentación como en el artefacto final. Seis observaciones correlacionadas de un solo mundo simulado no permiten afirmar identificación estructural, validación causal ni generalización comercial.

**No cambia** ningún modelo, parámetro, referencia, pronóstico ni abstención de G4. Tampoco autoriza reejecutar D/M/B, Buffalo, RK4 o nuevas simulaciones de construcción. Si el secreto de GitHub no está disponible, el trabajo se bloquea antes de cualquier DES.

Referencias: [PR #92](https://github.com/yudocyudoc/IGC/pull/92), [PR #93](https://github.com/yudocyudoc/IGC/pull/93), [PR #94](https://github.com/yudocyudoc/IGC/pull/94).
