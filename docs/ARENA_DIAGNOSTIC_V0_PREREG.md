# IGC — Piloto diagnóstico exploratorio de cuatro mundos

Estado: **construcción registrada antes de consultar al proveedor**. PR separado y apilado en #17.

Pregunta: ¿selecciona S estructuras compatibles con evidencia nueva y se abstiene cuando corresponde, frente a enumeración y ajuste con las mismas CS-01/CS-02?

Condiciones fijas: cuatro etiquetas Q7/R4/M9/T2 sin verdad generadora en las solicitudes. Construcción con pulso 0.8 unidades/h durante 2 h, cinco observaciones, sigma=.08; nuevo ensayo con pulso 3 unidades/h durante 2 h, tiempos [.5,1,1.5,2,2.5,3,4,5,6,8,10,12,16].

Evaluación: salida literal de GLM congelada antes de consumir observaciones reservadas; D enumera y ajusta ambas alternativas usando el mismo conjunto de datos y la misma cuadrícula de parámetros. G3 aplica RMSE<=.24 y coherencia física en construcción. Se miden falsos descartes, abstención, costo y RMSE por candidato. D que enumera ambas no puede mejorar por candidato su predicción respecto de S bajo el mismo ajuste.

**Límite:** el operador conoce el generador; únicamente el proveedor recibe una vista reducida. No es ceguera de custodio externo, ni una ronda íntegra de captura S→Modelica→LOCK, ni prueba H-IGC. GLM se consulta usando el conector autenticado y se archivará su respuesta cruda; no se debe falsificar recibo `arena_s_real.py`.

Datos y configuración comprometidos en `data/diagnostics/arena_s_diagnostic_v0_construction.json`. La verdad generadora y el holdout NO están en ese archivo. Cualquier análisis de resultados será exploratorio; las reglas no se ajustan a posteriori.
