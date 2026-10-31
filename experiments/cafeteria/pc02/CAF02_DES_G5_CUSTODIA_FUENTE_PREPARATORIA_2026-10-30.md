# CAF-02 — Fuente DES separada y preparación realista de G5/G4a/G4b

**Fecha:** 2026-10-30. **Estado:** código preparatorio, sin mundo privado seleccionado, sin autorización para K0/K1/K2, sin testigo externo real y sin G5 firmado.

## 1. Qué quedó preparado

La verificación G2 nativa de 15 casos **ya está realizada**, con 15/15 correspondencias bajo tolerancia 0.05 pedidos, tal como registra el [run 41154315886](https://github.com/yudocyudoc/IGC/actions/runs/41154315886). Es independiente de las futuras observaciones DES y no constituye evidencia de predicción K2.

La siguiente pieza es un evaluador que **no importa M, D, E1, Buffalo ni sus resultados**. Reutiliza el **código de calendario discreto genérico**, no la configuración ni el mundo ni los datos CAF-01:

`experiments/cafeteria/pc01/caf01_des_engine.py`

Se declara esta dependencia de código abiertamente, y su **hash exacto** debe formar parte de G5. El motor ofrece hasta seis etapas de colas/servidores finitos, servicio determinista por etapa en minutos, eventos de aceptación y terminación y salida acumulada en **enteros**. Las ecuaciones continuas M/D describen stocks y flujos suaves; el DES usa **órdenes individuales** y recursos discretos. Compartir la idea de etapas seriales sigue siendo un **sesgo estructural común**, por lo que no equivale a una fuente independiente de todos los supuestos.

`caf02_des_evaluator_preflight.py` valida contrato, tasas y calendario: K0 24 aceptaciones, K1-A 20, K1-B 30, K1-C 36 y K2 27; orden de eventos y límites físicos; y hashes de fuentes. Prueba el motor mediante **tres corridas de juguete** con una configuración fija, explícitamente ficticia y sin entradas secretas, para comprobar las máscaras mínimas:

- **K0:** solo dos entregas acumuladas en minutos 5 y 10.
- **K1:** exclusivamente una opción ficticia del menú y una entrega, después de reset.
- **K2:** seis enteros aislados dentro del evaluador; no se entregan al productor.

Estas son **pruebas sintéticas del código**; no son corridas del mundo CAF-02, ni consumen el presupuesto de tres experimentos independientes. `execute_private_trial()` permanece bloqueado; no existe un CLI para seleccionar automáticamente un generador «compatible» con las hipótesis. Ninguna semilla/configuración auténtica se escoge aquí.

## 2. G5: compromiso de fuente y parámetros privados, sin custodia ficticia

`caf02_g5_local_precommit.py` permite que **un operador independiente, fuera del repositorio**, prepare en su propia máquina un compromiso local. Requiere un archivo/objeto de **configuración nueva**, elegida sin conocer ni optimizar por los resultados de K0 o K2, y **32 bytes de nonce privados** preparados por el operador. Ni los parámetros ni el nonce deben copiarse a la rama Git, Actions, PR, tickets o informes del productor.

El compromiso enlaza con separación de dominio `IGC_CAF02_DES_G5_SOURCE_AND_PRIVATE_CONFIG_v1`, el nonce secreto, bytes canónicos de la configuración y hashes exactos de: motor DES, adaptador de evaluador, máscara, política de CAF-02, constructor G5, verificador de testigo, puente G4a/G4b, adjudicador K2 y función de puntuación. La salida pública incluye la referencia opaca `world_precommitment_ref`, los hashes de estas fuentes, los pulsos públicos, presupuesto y una **declaración de selección** escrita por el operador. No incluye el número de etapas, servidores, tiempos de servicio, identificadores de trabajadores ni nonce.

La declaración no demuestra por sí misma independencia. El compromiso local se marca `LOCAL_ONLY_NOT_EXTERNALLY_WITNESSED_NOT_AUTHORIZED`: **no es G5 válido ante un testigo externo** ni da permiso para ejecutar un solo K0. En ninguna parte de este PR existe una configuración privada del futuro mundo.

**Operación externa pendiente:** un evaluador real tendrá que proporcionar la justificación operativa del escenario y elegir la configuración con criterios independientes. Se deben congelar formalmente esos criterios antes de observar nueva evidencia. El procedimiento de selección NO puede escoger el mundo que haga sobrevivir a M o D.

## 3. Contrato de testigo externo: verifica firma, no inventa testigo

`caf02_external_witness_verify.py` comprueba **firmas Ed25519 desprendidas** sobre tres mensajes ordenados, todos sobre el mismo mundo:

| Corte | Identidad firmada | Enlace obligatorio |
|---|---|---|
| **G5** (antes de K0) | Hash del paquete público G5 y referencia al mundo | Sin antecesor |
| **G4a** (antes de K1) | Hash del G4a completo, hipótesis K0, opción K1, pronósticos K2 previos | Hash del paquete G5 y del evento G5 firmado |
| **G4b** (antes de K2) | Hash del G4b completo, revisión K1 y pronósticos K2 posteriores | Hash del paquete G4a y del evento G4a firmado |

Las firmas incluyen emisor y hora UTC afirmada. Se comprueban alteraciones, clave incorrecta, sustitución de paquetes, orden temporal declarado y vínculos entre recibos. La **clave pública debe provenir de una entidad externa identificada y su fingerprint estar previamente fijado fuera del código del productor**. La clave aportada dentro del propio recibo no se acepta como raíz de confianza. El módulo **no crea llaves privadas, no firma paquetes, no selecciona un testigo, no publica ni ejecuta mundos y no revela K2**.

**Advertencia:** una firma válida solo demuestra que el poseedor de esa clave firmó esos bytes. No demuestra que esa persona sea independiente, ni que la hora sea verdadera, ni que el contenido ya estuviera depositado en una fuente cronológica externa antes de K1 o K2. Falta revisar la institución responsable, el medio de depósito, los permisos de acceso y una fuente de tiempo confiable **fuera de ChatGPT y del repositorio del productor**. `verify_ordered_g5_g4a_g4b()` informa que la criptografía pasó, pero mantiene `execution_authorized=false` y `K2_reveal_authorized=false`.

Los tests generan **llaves ficticias en memoria** exclusivamente para comprobar firmas, negación de firmas falsificadas y parentage; no se incorporan como testigo real. El uso de `cryptography==46.0.4` es explícito en CI.

## 4. Orden de operaciones de la campaña aún no autorizado

1. **Antes de K0:** decisión separada sobre evaluador y elección razonada de escenario, fuente, configuración y nonce privados; aprobación de la política y de la raíz de confianza del testigo; G5 externo verificable; ejecución K0 a lo sumo una vez y publicación únicamente de D5/D10.
2. **Antes de K1:** generar paquete G4a de M/D ya existente; entregarlo para firma externa de contenido y hora, comprobar credencial y orden; solo entonces ejecutar el pulso común K1 preseleccionado si hubo algún candidato K0.
3. **Antes de K2:** generar G4b de la misma evidencia K1; obtener y comprobar firma externa, guardar versiones previas/posteriores; solo entonces activar el ejecutor K2, liberar exclusivamente seis enteros y adjudicar ambos brazos según la pérdida ya definida.

**En este PR no hay K0, K1, K2 privado, ni G5 firmado.** Tampoco se modifica G2, M, D, E1, CAF-01, tolerancia ±0.77, menú K1, pronósticos o pérdida. La memoria `ATMS_persisted=false` sigue sin acreditarse. Las tres corridas de juguete prueban la compatibilidad de interfaz con el motor; no prueban generalización.

## 5. Criterios para el siguiente entregable

Antes de habilitar el ejecutor de **una sola corrida privada por corte**, se necesita asignar un operador evaluador separado, registrar el mecanismo de custodia e identidad verificable del testigo, cerrar la política, proporcionar una fuente privada nueva dentro del entorno del evaluador y hacer que el ejecutor compruebe las firmas y el ledger de intentos **antes** de ejecutar. El ejecutor debe retener K2 bajo control de acceso real hasta verificar G4b; separar módulos Python no implementa por sí mismo una frontera de seguridad.

**Veredicto técnico:** hay ahora conexión y pruebas del **motor DES como fuente posible**, una especificación criptográfica auditable de los tres cortes y una preparación G5 que no revela secretos. **Todavía no hay campaña experimental ejecutable con independencia demostrada.**
