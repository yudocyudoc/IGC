# PoC de wrappers de `short` en IGC

Esta PoC copia byte por byte las dos fuentes Modelica identificadas en `provenance.json`. No copia el repositorio `short`, sus experimentos ni su catálogo completo.

`WrapperCS01` y `WrapperCS02` componen respectivamente una y dos instancias seriales de `BoundedQueue`, alimentadas por la misma entrada sintética y con los mismos parámetros por etapa. Cada topología se comprueba y simula en la imagen OpenModelica fijada en el manifiesto. La verificación de Actions exige series CSV válidas, finitas y diferentes para `delivered`; no fija de antemano sus magnitudes ni atribuye fidelidad al sistema real.

La ruta informativa `FirstOrderReportFilter` se carga y se comprueba como clase, pero no se conecta como flujo material ni se incorpora a estos dos modelos.

El código está recuperado solo para esta PoC. Su estado es `POC_ONLY_NOT_ADMITTED`; la revisión de licencias se difiere según instrucción del investigador. SystemDynamics y Modelica Standard Library se obtienen en CI desde los commits fijados en `provenance.json`.
