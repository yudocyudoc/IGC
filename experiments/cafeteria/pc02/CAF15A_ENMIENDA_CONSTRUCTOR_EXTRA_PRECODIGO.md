# CAF-15A — Enmienda de implementación ANTES DE CÓDIGO (sin cambiar mundos)

**Estado:** enmienda preventiva para corregir una incompatibilidad detectada al leer la implementación heredada. Este documento se comitea antes de crear el módulo CAF-15A; NO modifica el primer protocolo congelado ni los cinco controles extra declarados.

La función `CAF07B.make_physical_config(stage_indices,cap,extra=True)` rechaza `cap>=120` mediante una compuerta de ese ejercicio histórico. **No es una prohibición física del motor DES CAF-01**, cuyo `service_minutes` exacto positivo permite `60/160` o `60/220`.

Para los controles `EXTRA_160` y `EXTRA_220`, crear una construcción local explícita:
- Primera tres etapas: `servers=2`, `service_minutes="1"`.
- Cuarta etapa no observada: `servers=1`, `service_minutes=str(Fraction(60,cap))`.
- Misma `schema` y `tie_policy` oficiales, con `des.validate_private_config` y pruebas de conservación en `des.run_toy_engine`.
- **No** introducir estos valores en el catálogo de seis familias, que conserva `55..110`. Tampoco exponer el número de etapas al algoritmo de inferencia.
- Los controles `EXTRA_64, EXTRA_86, EXTRA_106` pueden construirse del mismo modo local para que todas las cinco topologías externas se generen con idéntico procedimiento. Verificar paridad de la construcción local con la heredada para capacidades bajo 120.

La corrección es de construcción/validación del control, no elección post-hoc de datos, sensores o intervalos. El riesgo de que la cuarta etapa rápida sea invisible permanece **una hipótesis a comprobar**, no una premisa.
