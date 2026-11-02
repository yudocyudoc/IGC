# Cribado D de CAF-01 y CAF-N en GitHub

Preparado sobre el PR #83. La incorporación de estos archivos no ejecuta
integraciones científicas. G2 nativo continúa pendiente.

## Validación del PR

`.github/workflows/caf01-d-rk4-preflight.yml` ejecuta las cinco pruebas del
runner con el integrador real bloqueado. Comprueba los hashes oficiales y
las máscaras de entrada. No requiere secretos.

El renderer Modelica recibe ahora `kind: "pulse"`; su ausencia provocaba
`BAD_MODEL_PULSE` después de la primera integración.

## Ejecución científica, después de integrar y autorizar

1. Verificar que el CI del PR terminó correctamente.
2. Integrar el PR en `main`.
3. En Actions, abrir **CAF-01 - D screening, one authorized 18 + 18 RK4 run**.
4. Elegir `main` e introducir `RUN_CAF01_D_18_PLUS_18_RK4`.

El workflow manual primero ejecuta pruebas con integraciones sustituidas.
Después abre dos jobs aislados, uno CAF01 y otro CAFN. Cada job invoca el
runner una sola vez y consume como máximo 18 integraciones RK4. El total
máximo es 36. No ejecuta DES, OpenModelica, Buffalo ni evaluación.

CAF01 utiliza las siete observaciones; CAFN utiliza únicamente t=0 y t=40.
Los representantes resultantes son preliminares: no constituyen G2 nativo,
identificación estructural ni una selección G3 conjunta.

## Resultados y fallos

Cada caso publica su propio artefacto con `D_RK4_SCREEN.json`, si terminó,
y el log con los marcadores previos a cada integración. El intento se cuenta
aunque la integración falle. Un fallo de un caso no cancela el otro.

Solo se permite el primer dispatch y el primer intento del workflow manual.
No pulsar Re-run ni lanzar un segundo dispatch: el runner los rechaza.
Incluso un primer dispatch con confirmación incorrecta consume el número de
ejecución de GitHub, aunque no consuma RK4. Cualquier recuperación exige
reconciliar los marcadores y revisar el presupuesto restante; no hay
reintentos automáticos.

El workflow de CI es otro archivo y no consume el contador del workflow
científico. Los artefactos públicos se conservan 90 días.
