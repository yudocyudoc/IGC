# CAF-01 · G5-01 — Sellado privado y presupuesto de campaña

**2026-10-28 · Propuesta para Astra · NO congelada · NO se ha escogido ni ejecutado un mundo CAF-01.**

## 1. Decisión física pendiente y frontera

El motor DES ya implementado utiliza tiempo racional exacto, FIFO y servidores finitos. La configuración privada que decida el investigador fuera del repositorio tendrá exclusivamente estas claves: schema, tie_policy y stages. Cada etapa tiene servers (entero 1–20) y service_minutes (racional positivo); el número de etapas es de 1–6. La política de empates propuesta es COMPLETE_THEN_ACCEPT_THEN_START_DOWNSTREAM_FIRST. Esta política aún requiere dictamen de Astra.

La configuración **no** debe escogerse tras mirar entregas, errores de los brazos o resultados de un mundo de prueba. Su justificación será una secuencia física ex ante de operaciones de cafetería, recursos y tiempos de servicio. Ni inventario de insumos ni aforo de sala de espera están modelados: no fingir una cafetería completa.

El PR no contiene configuración real. El código G5 no selecciona etapas ni parámetros, ni dispone de un runner de mundos DES.

## 2. Presupuesto definitivo propuesto, sin autorización implícita

| Recurso | Máximo contractual v0.3 actual | Reducción condicionada |
|---|---:|---:|
| DES construcción + evaluación | 1 + 1 = **2** | sin cambios |
| D RK4 construcción + CAF-N | 18 + 18 = **36** | sin cambios |
| D OpenModelica construcción + evaluación | 3 + 3 = 6 | sin cambios |
| B OpenModelica construcción + evaluación | 1 + 1 = 2 | sin cambios |
| M OpenModelica construcción + evaluación | 9 + 9 = 18 | 6 + 6 = 12 |
| **OpenModelica total** | **26** | **20** |
| Inferencias Buffalo CAF-01 + CAF-N | 1 + 1 = **2** | sin cambios |
| Reintentos automáticos | **0** | sin cambios |

Propuesta: mantener **26** como límite contractual duro hasta que Astra valide dinámicamente la equivalencia de M [72,100] y se registre la reducción en el protocolo. **20 no está todavía autorizado ni consumido.** La fase CAF-N no puede crear un DES ni OpenModelica adicionales; solo 18 RK4 D de control y la segunda inferencia Buffalo aislada. El helper hard_budget verifica los techos originales y que sus contadores de consumo permanezcan en cero. REF-CAF y REF-SCALE requieren registrar CPU, pero no consumen OpenModelica.

## 3. Herramienta local de precompromiso

El módulo caf01_g5_seal.py implementa dos comandos, plan y seal. Plan muestra los techos sin seleccionar ni ejecutar nada. Seal requiere una selección explícita del investigador en archivo **fuera del repositorio**, genera un nonce secreto aleatorio de 32 bytes y utiliza la función existente private_commitment(config, nonce) del motor DES. Fija también los hashes SHA-256 de los bytes exactos de cinco archivos: motor DES, G3, G4, G5 y contrato.

El sobre privado conserva la configuración y el nonce. Se crea fuera del repositorio, en directorio nuevo con permisos 0700 y archivo 0600. El recibo público separado contiene solo compromiso, hashes de versiones, conteos públicos 24/30, regla de desempate y techos; nunca incluye servidores, número de etapas, tiempos ni nonce. La función verify_receipt comprueba coherencia **local**; no certifica fecha ni testigo externo.

Ejemplo de comandos para un equipo local, solo después de selección científica y aprobación de la regla de empates:

    python experiments/cafeteria/pc01/caf01_g5_seal.py plan

    python experiments/cafeteria/pc01/caf01_g5_seal.py seal \
      --config /ruta-externa/seleccion-privada.json \
      --private-dir /ruta-externa/nueva-boveda-privada \
      --public-receipt /otra-ruta-externa/recibo-publico.json \
      --ack-researcher-selected-offline

Se rechazan rutas relativas y rutas dentro del checkout, sobrescrituras, archivos faltantes y configuraciones no soportadas. Los tests utilizan exclusivamente ejemplos inventados y carpetas temporales; generar un sobre de prueba no consume el presupuesto DES. La carpeta privada jamás debe enviarse a un PR, issue o almacenamiento compartido: .gitignore solo es una protección secundaria.

**Un hash autoproducido o el éxito de verify_receipt no constituyen custodia inmutable.** Es obligatorio un acuse independiente que vincule el mismo compromiso, las fuentes y un momento anterior a construcción.

### Validación analítica privada exigida antes del sello — ficha CAF-01 aprobada

El comando `preflight` verifica sobre una configuración externa, sin invocar DES, las bandas científicas aprobadas por Astra el 29 de octubre de 2026. Usa aritmética racional exacta: por etapa `mu_i=servers_i/service_minutes_i`, capacidad mínima `mu*=min(mu_i)`, cargas `rho_c=(6/5)/mu*` y `rho_e=(3/2)/mu*`, y latencia nominal `L0=sum(service_minutes_i)`. Se exige `21/20 <= rho_c <= 5/4`, `0 < L0 <= 4`, la identidad `rho_e=(5/4)*rho_c` y la finalización posible sin cola del primer pedido antes de t=5. En el límite de carga las comparaciones son inclusivas y exactas, no aproximaciones flotantes.

Uso **solo en equipo del investigador** y con rutas de configuración absolutas fuera del repositorio:

```bash
python experiments/cafeteria/pc01/caf01_g5_seal.py preflight \
  --config /ruta-externa/seleccion-privada.json
```

La salida muestra solo `APPROVED_ANALYTIC_BAND_ONLY_NOT_DES_VALIDATED`, junto con indicadores de que **no** se aprobó la justificación operativa ni se autorizó sellado, construcción o evaluación. No imprime servidores, tiempos, topología, capacidad ni carga. Un fallo rechaza el diseño sin crear sobre, nonce ni recibo. **El comando seal aplica la misma comprobación antes de emitir el compromiso.**

La justificación de operaciones, recursos y tiempos **sigue siendo una decisión humana**; esta validación no mide una cafetería real, no asegura congestión observable, no identifica una estructura y no permite barrer varias configuraciones buscando resultados de DES. Los valores concretos permanecen en la ficha privada, no en GitHub ni en ningún contexto de D/B/M/REF; la política pública del evaluador no es parte de sus entradas. Cuando se escoja una sola configuración y se apruebe la justificación, el sellado y custodia deben realizarse en el equipo del investigador, separados de las sesiones de productores.

## 4. Orden estricto de permisos y revelación

1. **Antes de construcción:** decidir y justificar mundo/servidores/servicios offline, aprobar política de empates, pin del código y presupuesto; sellar con nonce y obtener acuse externo fechado del compromiso. No permitir datos de los brazos al investigador al escoger ese mundo.
2. **Construcción autorizada:** un solo DES con pulso 1.2/min, 20 min y horizonte 40. Publicar únicamente D(t) de siete instantes más la entrada conocida; compartir A/P solo en sidecar común para auditoría, jamás parámetros o stocks por etapa. La evaluación permanece inaccesible.
3. **Construcción D/B/M y control CAF-N:** ejecutar exclusivamente los presupuestos establecidos, registrar cada intento y cada fallo. Aplicar G3 con abstención de brazos, sin datos de evaluación; G4 calcula ambas referencias desde construcción sin sidecar privilegiado.
4. **Bloqueo de pronósticos:** emitir paquete canonicalizado G3+G4 con archivo SHA-256, recibir custodia externa inmutable con timestamp independiente ANTERIOR a toda evaluación. Rechazar modificaciones de curvas después.
5. **Evaluación autorizada por separado:** verificar externamente acuses de ambos compromisos, pin y configuración secreta idénticos, 1/1 de presupuesto DES disponible, reinicio de todos los stocks a cero; generar el mundo reservado con pulso 1.5/min durante 20 min. Solo tras el bloqueo revelar seis observaciones y calcular MAE primario/RMSE secundario. Nunca reoptimizar.
6. Publicar pérdidas, bloqueos, abstenciones y recursos consumidos y contrastar D/B/M con REF-CAF y REF-SCALE. No atribuir identificación estructural ni causalidad a una victoria en una sola situación.

Astra y el investigador deben fijar nombre del custodio y método de verificación externa de los dos recibos antes de la primera ejecución. Este PR **no autentica firmas externas ni concede autorización para DES**, y no incluye código para producir construcción/evaluación. La política puede congelarse sin agregar más arquitectura.

## 5. Revisión concreta para Astra

Revisar separación de secreto versus recibo público; límites de rutas, permisos, exclusión de Git; correspondencia exacta compromiso/config/nonce y hash de motor; presupuesto original 26 versus 20 condicionado; ausencia de un runner, reintentos o autorización implícita. Después se elegirá y custodiará el mundo real externamente, sin reabrir G3/G4 salvo error material.

**Estado:** G5_PREPARATION_ONLY; ninguna selección privada, ningún sello externo, cero mundos ejecutados.
