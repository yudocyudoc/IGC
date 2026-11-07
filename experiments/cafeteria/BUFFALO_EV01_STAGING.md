# Estado de la entrada Buffalo EV-01

El preparador original falla por `native_pos_scenario` inexistente y adelanta masa
con bins anclados. Esta corrección usa `r2_causal_pos_signal.from_visible()`
sin importar componentes del evaluador ni anticipar llegadas.
El hash de la señal, tiempos y masa diferida son los mismos de D/M.

`stage()` prepara una entrada **pública**; no genera una propuesta Buffalo,
no consulta el proveedor, no ejecuta su traductor ni devuelve G2/G3.
El modelo/horizonte/tokens son requisitos del runner versionado,
no una capacidad presumida del upstream. No ejecutar el modo live con
el antiguo runner sin completar la revisión del contrato de ronda.
