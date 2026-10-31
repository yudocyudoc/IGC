# CAF-09 — Registro de resultados y revisión científica (CI original)

**Fuente canónica final de CAF-09:** [GitHub Actions #41246972768](https://github.com/yudocyudoc/IGC/actions/runs/41246972768), commit head `6a430e213fa9dd5f707846eaeaed2777d62f5f55`, checkout de merge sintético `51a97a222633b76ec185466022e690a1d792e3d4`. **5/5 pruebas PASS**. [70 archivos originales](https://github.com/yudocyudoc/IGC/actions/runs/41246972768/artifacts/13059681294). **Ejecución anterior, no canónica:** [#41246860385](https://github.com/yudocyudoc/IGC/actions/runs/41246860385), head `0bb73591ba7f7637d4bb0afdaee7a693f3e1b269`; también pasó 5/5, pero se preserva solo como antecedente histórico. El ZIP caduca; el código de la rama permite regenerarlo. Este registro se elaboró **después** de ver resultados: no es preregistro ni validación independiente. **Auditoría posterior:** [análisis estático #41248768694](https://github.com/yudocyudoc/IGC/actions/runs/41248768694), 8/8 pruebas PASS leyendo únicamente los archivos del run canónico (sin invocar DES).

## Banco ampliado (24 hipótesis): políticas de medición

| Política | Segundas | Correctos | Falsos únicos | Abstenciones | MODEL_GAP | Segundas que reducen hipótesis | Segundas que reducen clases |
|---|---:|---:|---:|---:|---:|---:|---:|
| `STRICT_ORIGINAL` | 0 | 0 | 0 | 10 | 1 | 0 | 0 |
| `ANY_GUARANTEED` | 6 | 1 | 0 | 9 | 1 | 6 | 5 |
| `PAIRWISE_ANY` | 10 | 1 | 0 | 9 | 1 | 10 | 8 |

**El valor de medir y el de diagnosticar son diferentes.** El brazo de pares reduce alguna incertidumbre en los 10 casos donde mide, pero solo llega a una clasificación unívoca dentro del catálogo en 1/11. El resto de las reducciones puede dejar clases rivales posibles. Ninguna política identifica los mundos de cuello doble.

### Desglose por mundo (banco de 24)

`rH`: máximo de hipótesis **completamente** separables de todas las clases rivales por una acción. `rP`: máximo de pares interclase separables por una acción (>2 pedidos). `Δh/Δc`: hipótesis/clases eliminadas tras la acción en el mundo simulado. Los dos brazos usan los mismos datos K0/K1.

| Mundo | rH | rP | `ANY_GUARANTEED` (acción; Δh/Δc; resultado) | `PAIRWISE_ANY` (acción; Δh/Δc; resultado) |
|---|---:|---:|---|---|
| `SINGLE_72_0` | 1 | 11 | prep_dispatch_15_t20; 3/3; ABSTAIN | prep_dispatch_15_t20; 3/3; ABSTAIN |
| `SINGLE_88_1` | 2 | 7 | prep_dispatch_18_t20; 5/2; **CORRECTO** | prep_dispatch_18_t20; 5/2; **CORRECTO** |
| `SINGLE_102_2` | 0 | 36 | no mide; ABSTAIN | prep_dispatch_18_t20; 5/0; ABSTAIN |
| `DUAL_55_01` | 1 | 11 | prep_dispatch_15_t20; 3/3; ABSTAIN | prep_dispatch_15_t20; 3/3; ABSTAIN |
| `DUAL_55_02` | 1 | 11 | prep_dispatch_15_t20; 3/3; ABSTAIN | prep_dispatch_15_t20; 3/3; ABSTAIN |
| `DUAL_55_12` | 1 | 11 | prep_dispatch_15_t20; 4/4; ABSTAIN | prep_dispatch_15_t20; 4/4; ABSTAIN |
| `DUAL_90_01` | 0 | 36 | no mide; ABSTAIN | prep_dispatch_18_t20; 9/3; ABSTAIN |
| `DUAL_90_02` | 0 | 36 | no mide; ABSTAIN | prep_dispatch_18_t20; 9/3; ABSTAIN |
| `DUAL_90_12` | 0 | 36 | no mide; ABSTAIN | prep_dispatch_18_t20; 10/4; ABSTAIN |
| `UNKNOWN_EXTRA_70` | 0 | 0 | MODEL_GAP tras K1 | MODEL_GAP tras K1 |
| `UNKNOWN_EXTRA_100` | 2 | 7 | prep_dispatch_18_t20; 2/0; ABSTAIN | prep_dispatch_18_t20; 2/0; ABSTAIN |

**Revisión importante de CAF-08B:** en los 4 mundos donde no era posible aislar una sola hipótesis completa (`SINGLE_102_2` y los tres `DUAL_90`), **sí existían pares interclase separables**, y una medición de esos pares redujo el catálogo. Por tanto, la frase anterior «en cuatro mundos no hay mediciones informativas» era excesiva. La afirmación correcta es **«ninguna acción aísla completamente una hipótesis en esos mundos»**. No es lo mismo que no reducir incertidumbre.

## Banco único (12 hipótesis): la misma relajación tiene otro riesgo

| Política | Segundas | Correctos de los 3 mundos representados | Falsos únicos | Abstenciones | MODEL_GAP |
|---|---:|---:|---:|---:|---:|
| `STRICT_ORIGINAL` | 4 | 1/3 | 3 | 6 | 1 |
| `ANY_GUARANTEED` | 10 | 2/3 | **6** | 2 | 1 |
| `PAIRWISE_ANY` | 10 | 2/3 | **6** | 2 | 1 |

Los seis mundos con doble cuello están fuera del catálogo de 12 por diseño. Las políticas débiles pueden emitir una clase única **incorrecta** en 6/6 de ellos. Una abstención habría sido menos engañosa. **No** comparar solo la cantidad de diagnósticos correctos.

## Interpretación y próximos falsadores

1. **Política de adquisición ≠ política de certificación.** La compuerta para escoger una medición no debería implicar automáticamente que un diagnóstico único sea seguro. Los resultados sugieren separar ambas, pero no autorizan adoptar ninguna de las reglas nuevas.
2. **Observabilidad local mejor que antes de medir; identificabilidad general no demostrada.** El hecho de que se eliminen candidatos no demuestra que la verdad esté en el catálogo ni que las clases restantes sean correctas.
3. **Política estricta puede desperdiciar información**, mientras que **relajarla con un catálogo incompleto puede aumentar falsos únicos**. Se observan ambas consecuencias, según el banco.
4. La tolerancia ±1 y la prueba de separación >2 son nominales, no estimación de sensor real; tampoco hay variabilidad estocástica del servicio. Con los mundos conocidos, un resultado positivo no puede considerarse confirmación fuera del banco.
5. Para una decisión sistémica real haría falta tratar los costos de observación, el riesgo de diagnósticos falsos, la pérdida esperada de cada decisión y la posibilidad de no actuar. No optimizar eso usando solo estos once mundos.

**Veredicto científico provisional:** `BLOCKED_RETROSPECTIVE_KNOWN_WORLDS`, sin promoción. El código, tests, operaciones y decisiones completas están en el PR/artefacto de CI. Toda modificación de política es nueva hipótesis, no corrección retrospectiva de CAF-07B.
