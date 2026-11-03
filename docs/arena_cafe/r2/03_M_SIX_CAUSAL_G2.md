# RF-02M · Seis grafos Short E1 originales, estímulo causal y G2 de ingeniería

**Corte:** 2026-11-03. **Base:** PR #141 (`d00c0cd7f52a0f83edf7e38e73fb9bd9b2e3f2f0`). **Cambio:** archivos aditivos de ensayo, sin modificar `experiments/e1/composer.py`, `experiments/e1/backend.py`, `registry.base.json`, `IGCMolecules.mo` o `IGCInformationMolecules.mo`.

**Objetivo:** que Moléculas ejecute **todas sus seis composiciones originales**, no solo C00, con el **mismo estímulo causal de pedidos** fijado en D-B, y que OpenModelica verifique su balance material sin adjudicación científica. El incremento permite G2 de ingeniería; mantiene `G3/G4/G5=NOT_RUN`, `A3=PARTIAL`, y no evalúa entregas POS contra predicción.

## 1. Procedencia y candidatas

- Fuente de evidencia: `O0_VISIBLE.json` del run A1 #41575917332; 15 eventos de creación antes de 10 min. O1 contiene las mismas creaciones pero evidencia física adicional; no se reejecuta aquí porque no se consume ningún observable exclusivo de O1.
- Enumeración: `get_composer().load_registry(registry.base.json)` y `enumerate_graphs()` originales. Se conservan **6/6** grafos completos, ordenados según `canonical`, con AST íntegro y parámetros fijos del registro. No hay `choose_one()`.
- Tres agrupaciones de proyección material (dos AST cada una) se registran para diagnóstico. **No son tres mecanismos empíricos certificados ni una reducción del universo de seis**. Cada grafo se simula.
- Los roles obligatorios `source`, `preparation`, `dispatch`, `receipt`, y los parámetros `maxThroughput=20/h`, `responseTime=0.5h` de preparación/despacho, son priors nativos del registro E1, no estimaciones POS.
- Los seis modelos se renderizan mediante `backend.render_model` original, utilizando `stimulus_only_replace` únicamente para eliminar los cuatro generadores históricos de probe; después se reemplaza la única declaración de estímulo por la entrada causal. No se crean ecuaciones de dinámica ni se alteran instancias o conexiones materiales ni de información.

## 2. Exactamente la misma señal que D, en unidades de M

La política `CAUSAL_RIGHT_RECTANGULAR_EVENT_KERNEL/0.1` tiene anchura declarada de 1/2 minuto por evento. Para cada creación observada en `t_i` minutos:

- D usa tiempo en **minutos** y tasa `2 pedidos/minuto` dentro de `[t_i,t_i+0.5)`.
- M usa tiempo en **horas** y tasa `120 pedidos/hora` dentro de `[t_i/60,(t_i+0.5)/60)`.

Esto es una **conversión de unidad**, no una hipótesis distinta. Ambos expedientes llevan exactamente el mismo hash de señal/eventos `event_rate_signal_sha256`; el workflow compara M con el **manifiesto real del G2 D** del run #41589895721. La masa que continúa después de t=10 min sigue diferida; no se adelanta ni elimina.

**Precisión:** la distribución rectangular causal es una política externa de ingeniería, **no una medición de tasa instantánea**, ni la política temporal científica definitiva de R2. El origen y el límite se conservan.

## 3. Balance y señales de información

El compositor original expone `inTransit` únicamente como suma de stocks **`STATE<Shipment>`**, no como WIP material total. **No incluye las colas originales de preparación (`STATE<Order>`) ni despacho (`STATE<ReadyOrder>`)**, cuyo inventario material se expone por sus puertos tipados `waiting`. Para cada fila de cada CSV el nuevo auditor resuelve **todos los `waiting` de clase `bounded-queue` desde el AST original** y compara la suma con entregas:

    sum(waiting_ports_typed[preparation,dispatch,transit...](t)) + deliveredTotal(t) = integral_0^t u_causal(s) ds

El lado derecho es la integral exacta de eventos (con fracción precorte y cola diferida), convertida correctamente desde horas de Modelica a minutos para la verificación. Se comprueba que `inTransit` es solo un **substock de envío**, no el balance global; además no negatividad, monotonía de entregas, tiempo 0–10 min, al menos 1000 muestras por modelo y **residuo máximo <= 0.08 pedidos** predeclarado en A1/D.

Los módulos `report` y `reportedDeliveryRate` son **información**, no stocks materiales ni entregas. Para cada pareja de grafos con misma proyección material, el test de ingeniería compara los estados físicos finales (`suma de todos los waiting tipados`, `deliveredTotal`) con tolerancia predeclarada de **0.05 pedidos**; **esa comprobación puntual no prueba equivalencia dinámica universal**.

Se ejecuta una instancia real de OpenModelica v1.26.5-minimal sobre seis modelos en un paquete `ArenaR2M`; con ModelicaStandardLibrary 4.0.0 y SystemDynamics 2.1.2 originales según el workflow previo A1. Se conservan los CSV de cada modelo, hashes, logs e identificador de imagen.

### Incidente detectado en la primera ejecución de CI

La [primera corrida RF-02M #41591373557](https://github.com/yudocyudoc/IGC/actions/runs/41591373557) compiló y simuló los **seis modelos**, pero el auditor inicial usaba `inTransit + deliveredTotal` como si `inTransit` fuera todo el material. La prueba de masa falló. La inspección del catálogo E0 original confirmó que **las colas de preparación y despacho tienen stocks con tipos distintos de `Shipment`**. Fue un **error de operador observacional**, no motivo para cambiar las ecuaciones, los parámetros o la tolerancia.

La corrección se limita a reconstruir los puertos `waiting` de **todas las instancias de colas acotadas que aparecen en cada AST** (preparación, despacho y tránsito opcional). El verificador ahora aplica la ecuación de balance completa. Se añadió prueba que obliga a incluir 2, 3 o 4 stocks según composición, y que rechaza considerar `inTransit` como WIP global. Se conserva la primera ejecución fallida como diagnóstico.

## 4. Qué demuestra y qué no

**G2=PASS_REAL_OMC_ENGINEERING_ONLY**, si los seis compilan/simulan y cumplen balance, significa solamente que las moléculas fijadas pueden ejecutar esa señal y conservar el material en el control. No significa que sus stocks correspondan a etapas observadas de la cafetería, que tengan parámetros estimados, que las seis señales sean explicaciones independientes, ni que alguna tenga buen ajuste o gane contra D/B.

No se hace comparación de predicción contra `delivered_cumulative` de EV-01; no se consulta `physical_observation` O1, FULL, DES privado, holdout, ninguna inferencia Buffalo ni resultados de otro brazo que no sean el **hash de entrada causal D**. No se escribe a ATMS ni se adjudican modelos.

El valor máximo reportable sigue siendo: `A3=PARTIAL`, `scientific_adequacy=NOT_ESTABLISHED`, `G3/G4/G5=NOT_RUN`.

## 5. Revisión por hitos, no por microcambios

Esta compuerta de ingeniería se valida mediante CI y tests adversariales sin consultar a Astra cada vez. La revisión independiente posterior debe concentrarse en **compatibilidad semántica de H_j, origen de parámetros y diseño de G3** antes de comparar candidatos y construir decisiones de la Arena. Los tres motores siguen separados: `M` conserva grafos y priors nativos, `D` su gramática, `B` su generador LLM aún sin corrida EV-01 real.
