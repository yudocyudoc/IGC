# CAF-08B — Auditoría adversativa de Claude y desglose por mundo
**Fecha:** 2026-10-31. **Estatus:** documentación posterior a la ejecución; no es preregistro ni resultado nuevo.

**Fuente canónica de datos:** [GitHub Actions #41245866028](https://github.com/yudocyudoc/IGC/actions/runs/41245866028) y [artefacto 13059073526](https://github.com/yudocyudoc/IGC/actions/runs/41245866028/artifacts/13059073526). La ejecución terminó **PASS 5/5**. Se conservan **los archivos exactos** bajo `evidence/CAF08B_CI_41245866028_RESULTADOS.json` y `evidence/CAF08B_CI_41245866028_INFORME.md` para revisión incluso después de que caduque el ZIP de Actions.

### Proveniencia sin ambigüedad

- **PR #120 head realmente propuesto en la ejecución:** `a263ba72b47ebed91af8e95b1dca841393a8ef97`.
- **`checkout_sha` inscrito en el plan/resultados:** `edb475ffc754e30537595fd8dc6a9e3e941d12be`. Es el commit **sintético de merge** usado por el evento `pull_request`, NO el head del PR.
- El indicador de `checkout_sha == GITHUB_SHA` documenta el checkout que se ejecutó, no autoría ni preregistro. Los archivos de evidencia son una copia publicada **después** del run y no sustituyen al artefacto previo ni a su SHA256.
- **#119 CI de referencia:** [run 41244988064](https://github.com/yudocyudoc/IGC/actions/runs/41244988064), **7/7 tests PASSED**, incluido el test `test_local_baseline_is_reproduced_not_claimed_validated`. #120 no lo reejecuta en su propio workflow: el hecho de apilar el PR no autoriza a afirmarlo.

### Resultados completos por mundo (modelo predictivo DES)

Los resultados bajo `FLUID_DELAYED_HALF_UP` son idénticos en **veredicto, acción, supervivientes y estado** para cada una de las 22 parejas mundo×banco. Un veredicto de cuello único falso no es necesariamente inevitable al salir del banco: la **abstención o MODEL_GAP** habrían evitado declarar un cuello erróneo.

| Mundo evaluado | Lecturas entregadas K0/K1 | Banco de 12 | Banco de 24 | Segunda acción banco 12 | Máximo de hipótesis robustamente separables por una sola acción dentro del banco de 24 |
|---|---:|---|---|---|---:|
| `SINGLE_72_0` | 9 / 21 | CORRECTO | ABSTENCION | prep_dispatch_15_t20 | 1 |
| `SINGLE_88_1` | 9 / 25 | ABSTENCION | ABSTENCION | — | 2 |
| `SINGLE_102_2` | 9 / 26 | ABSTENCION | ABSTENCION | — | 0 |
| `DUAL_55_01` | 6 / 16 | FALSO_UNICO | ABSTENCION | prep_dispatch_15_t20 | 1 |
| `DUAL_55_02` | 6 / 16 | FALSO_UNICO | ABSTENCION | prep_dispatch_15_t20 | 1 |
| `DUAL_55_12` | 6 / 16 | FALSO_UNICO | ABSTENCION | prep_dispatch_15_t20 | 1 |
| `DUAL_90_01` | 9 / 27 | ABSTENCION | ABSTENCION | — | 0 |
| `DUAL_90_02` | 9 / 27 | ABSTENCION | ABSTENCION | — | 0 |
| `DUAL_90_12` | 9 / 27 | ABSTENCION | ABSTENCION | — | 0 |
| `UNKNOWN_EXTRA_70` | 7 / 19 | MODEL_GAP | MODEL_GAP | — | sin supervivientes |
| `UNKNOWN_EXTRA_100` | 8 / 25 | ABSTENCION | ABSTENCION | — | 2 |

En el banco ampliado de 24: **6 mundos con alguna acción parcialmente informativa** (máximo robustamente separable >0) y sin ningún permiso de medir; **4 mundos sin una sola hipótesis robustamente separable** por acción; **1 mundo sin candidatos** después de K1. La exclusión se debe a `guarantee(...).all_classes_meet_minimum`, requisito de al menos una hipótesis distinguible por **cada** clase superviviente; estas cifras no demuestran que seleccionar las pruebas parciales resuelva el caso específico.

### Localización exacta de MODEL_GAP

`UNKNOWN_EXTRA_70` tiene cuarta etapa al final a capacidad nominal de 70/h (verdad solo en evaluador). Observaciones DES: `K0 = [7]` entregas a t=10, 1.2/min; `K1 = [19]` entregas a t=20, 1.5/min.

- Bajo K0 sobreviven **3 hipótesis** del banco 12 y **6** del banco 24 (capacidad nominal 60/h en etapas conocidas).
- Al aplicar K1, sobreviven **0** en ambos bancos; exactamente el mismo `MODEL_GAP` se obtiene con predicciones DES y fluido.
- `UNKNOWN_EXTRA_100` tiene `K0 = [8]`, `K1 = [25]`; sobreviven 6 hipótesis, con abstención. **La brecha no es un detector validado de topología oculta.**

### Consideraciones de la revisión

1. **¿0/22 por construcción?** Prácticamente esperable por cercanía entre predicciones con tiempos físicos compartidos; no es un teorema necesario. La regla de separación robusta usa diferencia **>2 pedidos** entre hipótesis con bandas ±1. Si las predicciones de dos hipótesis son 0 y 2, una perturbación de +1 a la segunda (0 y 3) **sí modifica** su separabilidad. En este ensayo los cambios efectivamente no afectaron decisiones.
2. **Dentro del catálogo cubierto:** en el banco de 12, solo los tres mundos físicos `single` pueden recibir su clase correcta. Resultado: **1/3 correcto y 2/3 abstenciones**. Los seis mundos dobles y dos con cuarta etapa estaban fuera del catálogo, pero los 3 falsos únicos no eran inevitables; son un riesgo de diagnosticar con un banco incompleto.
3. **Bloqueo por clase:** 0 segundas observaciones del banco de 24 entre 11 mundos. La política impide las seis pruebas potencialmente informativas; en otros cuatro el menú/observabilidad actual tampoco asegura separación suficiente. *No sabemos si relajar política con el mismo menú mejora decisiones*.
4. **Curva de sensibilidad no probada:** proponer como ensayo **aparte y congelado** perturbaciones sintéticas ±1 en 5/10/25 % de canales, escenarios de ±10 % en tiempos de servicio de predicción, fluido sin retardo y cuantización floor frente a half-up. Registrar semilla, unidades, canal, dirección, perturbaciones por escenario y cambios de veredicto/selección. Cambiar simultáneamente una predicción y su contraria puede destruir conservación; la prueba de estrés mide estabilidad algorítmica, NO plausibilidad física. No modificar retrospectivamente CAF-08B.
5. **Timestamps:** en un DES con servicios deterministas, conocer duración exacta de la etapa distingue algunas configuraciones *por especificación*. Esto solo demuestra observabilidad del modelo ideal. Un estudio de utilidad bajo incertidumbre exige tiempos estocásticos, errores de medición y diseño estadístico, **sin usar duración privada verdadera como observación**.
6. **Denominadores y CIs:** el MAE fluido–DES intra-pulso, su signo y el test de línea base están versionados en #119, no en las nuevas líneas de código de #120. No sumar pruebas de workflows diferentes como si fueran la misma validación.

**Dictamen:** #120 demuestra invariancia de los veredictos bajo este reemplazo concreto de banco, con poca discrepancia numérica. No separa por sí solo la insuficiencia instrumental de la dureza normativa de la política. Los PR #119 y #120 permanecen en borrador y no autorizan promoción.
