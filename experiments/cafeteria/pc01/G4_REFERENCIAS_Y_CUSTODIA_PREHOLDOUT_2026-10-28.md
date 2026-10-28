# ARENA · CAF-01 / PC-01 — G4-01 Referencias y custodia pre-holdout

**Fecha:** 2026-10-28. **Estado:** implementación para revisión de Astra; NO congelada y NO es autorización de PC-02 ni de ejecuciones. **Código:** `caf01_g4.py`. Depende del contrato v0.3 y del G3 integrado. Ninguna observación real de construcción/evaluación existe en este cambio.

## 1. Misma información, referencias diferentes

Se valida el paquete público original con `caf01_g3.validate_evidence`: pulso de construcción de 1.2 pedidos/min durante `0≤t<20`, entregas `D(0),D(5),D(10),D(15),D(20),D(30),D(40)` y su snapshot. Ninguna función de ajuste acepta `A_real`, `P_real`, etiquetas internas DES, respuestas futuras ni outputs de otros brazos.

**REF-CAF:** propone `P_proxy(t)=1.2·min(t,20)−D_construcción(t)`, exclusivamente como proxy de cola para detectar intervalos; **no** es una medida independiente de pendientes. Se examinan los cuatro intervalos de cinco minutos hasta t=20. Es elegible únicamente uno donde `P_proxy>1` pedido **en ambos extremos**. Si hay al menos dos, se calcula `μ_eff=median((D(b)−D(a))/5)` en pedidos/min. Predicción fluida determinista para condición 1.5/min:

`D_pred(t)=min(1.5·min(t,20), μ_eff·t)`, en `t=5,10,15,20,30,40`; `P_pred(t)=A_ideal(t)−D_pred(t)` es **derivado**. Se puede obtener `μ_eff=0` con evidencia de cola persistente y ausencia de entregas; es una tasa efectiva válida bajo el modelo simple. Si hay menos de dos intervalos, `REF_CAPACITY_NOT_IDENTIFIABLE`, sin inventar parámetro ni curva.

La fórmula supone una **cola fluida única sin retardo de servicio interno**: no se traslada al mundo DES ninguna de sus capacidades, ni se declara `μ_eff` el cuello de botella físico verdadero. El inicio t=0 tiene cola proxy cero, por lo que el primer intervalo [0,5] nunca es elegible; la política deja hasta tres intervalos restantes, no cuatro mediciones efectivas.

**REF-SCALE:** se calcula por separado como `D_pred(t)=min(1.5·min(t,20),1.25·D_construcción(t))` en los mismos seis instantes. Nunca interpola puntos inexistentes, ni es un modelo estructural ni un brazo adicional. Los pendientes también son derivados del pulso ideal. Se evita que REF-CAF gane acceso especial a A/P de la verdad; REF-SCALE tampoco mira evaluación.

La diferencia conocida entre conteo DES y el integral de diseño de entrada se verifica en un **sidecar de auditoría totalmente separado**, con límite predeclarado ±1 pedido y balance agregado `A=D+P`. La función `audit_arrival_sidecar` no llama ni parametriza `forecast`. El balance agregado público es tautológico si P es derivado; para afirmar **conservación física** hace falta una traza independiente de stocks materiales y sus propias verificaciones G2. Si los datos incumplen la discrepancia prevista, se bloquea el caso y no se repara mirando evaluación.

## 2. CAF-N: abstención, no extrapolación ficticia

La misma evidencia de construcción se enmascara a **t=0 y t=40**. No hay dos intervalos observados pre-20 con cola proxy validable, por lo que REF-CAF se abstiene. REF-SCALE tampoco conoce `D_construcción(5,10,15,20,30)` y se abstiene de la curva completa. El único cálculo descriptivo es D(40) y el pendiente terminal **proxy** `24−D(40)` con entrada pública y calendario propuesto; no se infiere pico de pendiente, secuencia de cola ni tiempo individual de espera.

En un paquete CAF-N, G3 tampoco puede contener pronósticos futuros ni nuevas verificaciones OpenModelica. `prepare_preholdout_package` exige esas condiciones antes de unir las dos referencias.

## 3. Evaluación futura predeclarada

**Única variable primaria:** entregas acumuladas `D(t)` en **seis** momentos `5,10,15,20,30,40` de la condición de evaluación. Para cualquier curva **válida y previamente bloqueada**, calcular

`MAE_D = Σ |D_pred(t)−D_observado(t)| / 6`

y como medida secundaria `RMSE_D = sqrt(Σ(D_pred(t)−D_observado(t))² / 6)`. Las series de P, sus errores y diferencias entre escenarios son transformaciones derivadas/correlacionadas, **no un segundo holdout**. Reportar las dos referencias y cada brazo por separado; contabilizar bloqueos y abstenciones como cobertura, sin imputarles MAE ni penalizaciones arbitrarias.

**Regla descriptiva**, no prueba estadística: una mejora frente a REF-CAF requiere `MAE_REF_CAF−MAE_brazo ≥1 pedido` y aprobación física G2. Si REF-CAF se abstiene, no hay comparación de esa ventaja. REF-SCALE es un control obligatorio para cualquier pretensión de transferencia estructural: si la ventaja se explica por simple escalamiento, no afirmar recuperación de mecanismos. Incluso superándolo, un mundo sintético único **no prueba causalidad, representatividad comercial ni generalización**.

No usar RMSE, pico de P, costo ni diferencia con REF-SCALE para seleccionar después de revelar el holdout. Conservar la banda G3 de 0.25 pedidos MAE (regla decisional, no precisión instrumental), la igualdad de curvas `1e-6`, los límites G2 de balance y paridad y todas las abstenciones. Si no existe una predicción válida sellada, el resultado es **sin MAE calculable**, no error infinito ni éxito imputado. No introducir intervalos de confianza ficticios con un único mundo y seis tiempos dependientes.

**Límite físico revisado para G3/G4 (dictamen Astra):** el calendario de llegadas en evaluación tiene exactamente 30 pedidos, no 31. La validación compartida utiliza el conteo acumulado de eventos de la fórmula predeclarada `(j+1/2)/1.5`, incluyendo eventos simultáneos a cada lectura: sus cotas en t=5,10,15,20,30,40 son **[8,15,23,30,30,30] pedidos**, respectivamente. Se exige `D_pred(t) ≤ A_eventos(t)+1e-6` para las predicciones continuas (tolerancia numérica, nunca un pedido de holgura), y `D_obs(t) ≤ A_eventos(t)` para los conteos enteros. Tanto `lock_forecasts` de G3 como `score_six_delivered_values` de G4 rechazan la curva `[2,4,6,8,20,31]` ante la verdad de prueba `[2,4,6,8,20,30]`: no puede computarse MAE de algo físicamente imposible. Esto no añade ningún resultado experimental ni una fuente nueva de información; simplemente hace cumplir el calendario público existente.

## 4. Custodia: contenido preparado NO equivale a sello externo

`prepare_preholdout_package(contract,evidence,selection,g3_lock)` verifica hashes de contenido y procedencia G3, estado previo a revelación, máscara CAF-N y completitud de D/B/M; calcula ambas referencias **de nuevo desde construcción**, e incluye las curvas ya bloqueables de G3 y las reglas de evaluación, sin incorporar el valor futuro. Emite `preholdout_package_sha256` y un bloque explícito:

`custody.state=NOT_CUSTODIED_EXTERNAL_WITNESS_REQUIRED`, `external_receipt_id=null`, `external_verified_timestamp=null`, `external_witness_attestation_sha256=null`, `release_authorized=false`.

Un SHA autoproducido en el mismo ordenador o un commit modificable **no demuestra por sí solo anterioridad ni custodia independiente**. La secuencia futura que necesita **autorización explícita** es:

1. Sellar y custodiar fuera del repositorio los parámetros/nonce del DES y el hash exacto de código aprobado. La llave y verdad nunca se publican en un PR de preparación.
2. Autorizar y producir **solo construcción**, distribuir el mismo paquete público, completar las rutas D/B/M y referencias bajo sus presupuestos.
3. Emitir la selección G3 y su contenido de pronósticos; adjuntar G4 y las abstenciones en un único paquete canonicalizado. **Prohibir** editarlo tras ver evaluación.
4. Depositar los **bytes exactos** y SHA ante un custodio independiente con recibo verificable, identificador, timestamp y atestación de orden temporal. El recibo debe referirse al mismo SHA y al compromiso DES; documentar el método de comprobación. Un PR o comentario posterior no sustituye ese acuse externo.
5. **Después** de una verificación independiente del recibo y de G0–G4, autorizar por separado la única corrida DES de evaluación, revelar sus seis entregas y aplicar la regla de puntuación sin rehacer modelos ni referencias.
6. Archivar fallos, intentos, recibos del proveedor, conteo real por motor y efectos de discretización; no hacer reintentos tácitos.

El código emite un archivo de contenido canonicalizado de forma reproducible, usando el CLI **solo para datos públicos de construcción ya autorizados**:

```bash
python experiments/cafeteria/pc01/caf01_g4.py \
  --evidence /ruta/visible-construccion.json \
  --selection /ruta/g3-seleccion.json \
  --g3-lock /ruta/g3-bloqueo.json \
  --out /ruta/paquete-g4-nuevo
```

La carpeta de salida **debe no existir previamente**, para evitar sobrescritura accidental. Genera `preholdout-package.json` y `preholdout-package.sha256`. Hay dos hashes distintos, ambos válidos pero **no intercambiables**: `preholdout_package_sha256` dentro del JSON se calcula del contenido sin su propio campo hash (para evitar autorreferencia); el `sha256` externo se calcula de **todos los bytes reales** del archivo completo, incluido su salto de línea final. El custodio deberá comprobar **este segundo hash**, referirse al snapshot de construcción, al hash del modelo privado y firmar/atestiguar el orden temporal. Los hashes se calculan y verifican con fixtures de prueba; no hay ningún paquete de construcción real generado aquí.

`score_six_delivered_values` es una función aritmética pura para la fase posterior: calcula MAE/RMSE en seis instantes con entradas tipadas y físicamente acotadas. **No autentica recibos ni habilita la evaluación**; utilizarla con resultados reales exige la verificación independiente previa y la autorización separada.

Ni el paquete ni el código de G4 implementan custodia externa, timestamp confiable, firma ni autorización; no tienen acceso al DES de evaluación. G3 y G4 son preparación comprobable, **no preregistro científico irrevocable**.

## 5. Revisión solicitada a Astra

Comprobar: mediana y umbral **estrictamente mayor** a un pedido en **ambos extremos**; fórmula de cola fluida; abstención correcta de REF-Caf; REF-SCALE sin lecturas intermedias en CAF-N; procedencia idéntica a G3 sin privilegios de sidecar; seis tiempos, métricas no independientes, diferencia descriptiva ≥1 pedido; y ausencia de falsas afirmaciones de custodia inmutable.

**G4 cierra como código preparatorio tras CI y dictamen, pero CAF-01 permanece sin congelar y PC-02 sin autorización.**
