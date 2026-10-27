# Arena V0 — primera ronda offline (sin validación empírica)

Un único origen sintético alimenta adaptadores tipados. Se ejecuta el generador nativo **D** y el compositor original **Short E1** del brazo M; este último enumera candidatos de ingeniería y se abstiene de seleccionar una hipótesis a partir de observaciones. El brazo **B** permanece **BLOCKED** porque esta ronda no autoriza una nueva inferencia y no es lícito reutilizar como si fuera una respuesta a la entrada común la revisión Buffalo de un prompt histórico distinto.

La salida almacena hashes de origen, hashes de entradas derivadas y outputs nativos (D y M), junto con bloqueos de B. No simula en OpenModelica, no compara empíricamente, no accede a reserva, no calcula B0, no entrega feedback ni escribe ledger/ATMS. Los parámetros D pertenecen a un fichero explícito de supuestos, separado de observaciones.

**Siguiente trabajo:** ejecutar físicamente las candidaturas D de este corte; preparar la inferencia nativa B con autorización y presupuesto explícitos; resolver el mapeo M observación→rol (sin fingir selección) y después un orquestador con G0-G3, memoria y B0. No presentar esta ronda parcial como Arena científica integrada.
