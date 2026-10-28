# Arena IGC · R5 / PT-08-A — Cierre del primer corte experimental negativo

**Fecha:** 2026-10-28 UTC. **Dictamen de cierre:** **R5 / PT-08-A, primer corte experimental NEGATIVO; Clef NO se incorpora como filtro irreversible**. **Estado de evidencia:** seis inferencias observadas mediante conexión directa Cloudflare, todas HTTP 200, **sin** reintentos reportados, sin OpenModelica. No se ejecutó GitHub Actions para hacer llamadas. Este informe describe resultados observados en la respuesta de la conexión, no un archivo crudo guardado automáticamente por Actions antes de la calificación.

## Solicitudes congeladas

Se recuperó [artefacto #12786658182](https://github.com/yudocyudoc/IGC/actions/runs/40620696061/artifacts/12786658182) con las seis solicitudes de PT-08-A y oráculo privado. Se verificaron offline los SHA256 de los seis cuerpos originales y su reconstrucción exacta: solicitudes 1,3,5 (control) `66f10cbe3033b16cc29f9b6d9348e2615a9cc87e44241558e6ad6e80ecb6917e`; solicitudes 2,4,6 respectivamente `95402cab8abcfd6b2b25786b71b2fd6925304873af103ca5997e8f29a378aac5`, `1f2d7bf9360f05ab63b07cff0d006ffa6c454862e55bfc7e2d829ce4664d3f25`, `b8e2b6a680c539ec4310ed3cdbd08b7489fa3eb580b86fd2e2d6f3b4e663d317`. Digest del documento público original: `sha256:89fd4178609774b63a5d1913ea2abb10034f5038e08e162b546b80206e807e0f`. El modelo, parámetros, preguntas y 27 curvas no cambiaron.

## Resultado de las 18 respuestas binarias

Aplicando la política predeclarada `noul <= 0.30` = exclusión; `noul >= 0.70` = apoyo firme; intermedio = posible/incierto:

| Par | Condición | Clef scores C00/C01/C02 | No excluidos | Oráculo | Exacto |
|---|---|---|---|---|---|
| P01 | Numérico | .4058 / .5329 / .1876 | C00,C01 | C00,C01,C02 | No |
| P01 | Numérico+pantalla | .2345 / .5640 / .0783 | C01 | C00,C01,C02 | No |
| P02 | Numérico | .4058 / .5329 / .1876 | C00,C01 | C00,C01,C02 | No |
| P02 | Numérico+parada parcial | .1943 / .4045 / .1647 | C01 | C01,C02 | No |
| P03 | Numérico | .4058 / .5329 / .1876 | C00,C01 | C00,C01,C02 | No |
| P03 | Numérico+ruta exhaustiva | .2611 / .4606 / .1278 | C01 | C01 | Sí |

**Tasa de conjuntos conservadores exactos:** numérico **0/3**; numérico+nota **1/3**. **Falsos descartes:** numérico **3** (C02 repetida tres veces); numérico+nota **3** (dos en P01 y uno en P02); **apoyos firmes incorrectos:** 0 en ambos, pero no hubo ningún apoyo firme >=0.70. **Total:** seis respuestas HTTP 200, **16,881 tokens de entrada reportados** por Cloudflare, cero tokens de salida reportados en formato `noul`, y 0 nuevas simulaciones. No tenemos latencias individuales confiables de esta ejecución directa, por lo que no se fabrican.

## Interpretación

**Resultado negativo de utilidad segura de selección semántica:** ante una pantalla que no revela trayecto material, Clef elimina tanto C00 como C02; ante una parada observada parcialmente, elimina C02 aunque no existe traza exhaustiva que la contradiga. En P03 acierta el conjunto `{C01}`, pero P03 enuncia explícitamente la estructura; no constituye descubrimiento independiente. El control idéntico repetido produjo el mismo descarte erróneo de C02. El clasificador mantuvo C01 en todos los casos, pero ello **no** compensa los falsos descartes frente al conjunto correcto.

El comparador determinista sobre las mismas curvas conserva las tres topologías con las cuatro observaciones originales. El oráculo semántico por reglas explícitas de cobertura ofrece los conjuntos declarados; es una cota para estas notas sintéticas, no una línea base NLP de igual costo. No se consiguió demostrar ahorro **real** de solver, mejora generalizable, ni conveniencia de promover Clef como filtro irreversible; no introducirlo como cuarto brazo.

## Límite de procedencia y próximo paso

Al publicar un workflow de GitHub Actions con secreto de Cloudflare, la herramienta bloqueó la creación. Se recurrió a la conexión Cloudflare autorizada, que devolvió las seis respuestas juntas. Las respuestas fueron **reconstruidas desde la salida observada** y archivadas en un ZIP local (archivo separado disponible en la conversación); no hay prueba de un archivado remoto individual previo a la calificación, a diferencia de los pilotos anteriores. Se debe evitar afirmar que se completó una ruta Actions raw-before-grade.

La decisión para **PT-08-A** es conservar el experimento negativo, revisar si la calidad de Clef justifica otro contraste independiente antes de cualquier incorporación y **no ampliar por inercia** a Clairic ni alterar E1, D/B/M o ATMS. Este primer contraste es de **tres tratamientos informativos sobre un solo mundo sintético**. No permite estimar generalización.

**Metodología:** No ajustar a posteriori umbrales 0.30/0.70; no re-prompt; no repetir automáticamente estas seis llamadas; no llamar cero errores a los falsos descartes.

## 6. Cierre administrativo verificable

Se retiró del PR #70 el **ejecutor de nuevas inferencias**; no procede volver a llamar Clef para este corte. Se versionó `data/diagnostics/ARENA_PT08_R5_CLEF_OBSERVACIONES_RECONSTRUIDAS_2026-10-28.json`, con seis vectores NOUL observados, los SHA originales de cada solicitud y un marcador explícito: **reconstrucción posterior de salida de conexión, no captura cruda independiente anterior a calificar**. La ruta de validación offline `scripts/arena_pt08_r5_verify_closure.py` recupera las seis solicitudes originales de [Actions #40620696061](https://github.com/yudocyudoc/IGC/actions/runs/40620696061), comprueba sus hashes y los del oráculo predeclarado, vuelve a calcular con umbrales 0.30/0.70 los conjuntos y falsos descartes y comprueba el resultado negativo. El [workflow de cierre](https://github.com/yudocyudoc/IGC/blob/main/.github/workflows/arena-pt08-r5-close.yml) **no contiene llamada a proveedor**.

El dictamen no es «Clef incapaz en general» sino **«Clef no superó la compuerta de filtrado conservador en estas tres condiciones de un único caso sintético»**. Cierre de campaña no es certificación de validez externa ni autorización para activar PT-09/Clairic. La siguiente etapa debe regirse por la hoja de ruta y por una pregunta distinta; no por ajustar el experimento terminado.
