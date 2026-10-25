# Diagnóstico exploratorio IGC — cuatro mundos, S GLM vs ajuste/enum RK4

**Estado: EXPLORATORY_NOT_CONFIRMATORY.** No es ejecución integral S→ATMS→OpenModelica→LOCK, ni prueba ciega, ni estimación científica de ventaja H-IGC. Las cuatro consultas al proveedor fueron reales, a través del conector autenticado Cloudflare; las otras comparaciones se calcularon en el entorno local mediante la misma formulación RK4 de FM-B5, no con OpenModelica para estos cuatro mundos. Las respuestas crudas R4, M9 y T2 se archivaron; Q7 quedó registrada en la respuesta de herramienta/conversación, pero no en un archivo crudo de GitHub: por lo tanto el conjunto NO cumple la trazabilidad uniforme de captura.

## Declaración previa de construcción y protocolo

- Entradas de construcción y prompts se comprometieron en la rama antes de las llamadas. Todos recibieron exactamente el mismo catálogo CS-01/CS-02, sin identificador de verdad generadora. Cuatro solicitudes como máximo, sin reintentos. Temperatura 0.1.
- El investigador creó los mundos y por tanto **conocía la verdad**; únicamente el proveedor tuvo una vista restringida. Las reservas no estuvieron custodiadas por un tercero. No hay inferencia causal/identificabilidad demostrada.
- G3: adecuación absoluta de construcción con RMSE <= 0.24 y límite físico de 0.24. Después de recibir respuestas de GLM se calculó el ajuste por rejilla de ambos candidatos con capacidad 1.2–2.4 y respuesta 0.4–1.6.
- Predicciones del nuevo pulso (amplitud 3; duración 2) evaluadas contra **trayectoria generadora sin ruido** en los 13 tiempos de observación. Este resultado es solo diagnóstico de sesgo de ajuste, no RMSE de una reserva sintética ruidosa ni puntaje del LOCK.

## Respuestas de S y G3

GLM seleccionó **CS-01 y CS-02 en los cuatro casos**. No hubo poda estructural independiente por S. Algunas racionalizaciones contradicen el significado de salida acumulada o confunden la referencia temporal; guardarlas como errores explicativos. La selección no es equivalente a declarar adecuación absoluta.

| Caso | Generador revelado después de las llamadas | RMSE construcción CS-01 / CS-02 | G3 admite | RMSE diagnóstico pulso CS-01 / CS-02 |
|---|---|---|---|---|
| Q7 | CS-01 | 0.0305 / 0.0354 | CS-01, CS-02 | 0.6515 / 0.9072 |
| R4 | CS-02 | 0.2933 / 0.0738 | CS-02 | 0.7639 / 0.2281 |
| M9 | CS-02 | 0.0303 / 0.0367 | CS-01, CS-02 | 0.4976 / 0.7114 |
| T2 | 3 etapas fuera del catálogo | 0.3992 / 0.0980 | CS-02 | 1.1417 / 0.1667 |

**Hallazgos.** R4 muestra que G3 (ajuste cuantitativo) rechaza CS-01 y conserva CS-02, sin que GLM haya decidido esa poda. Q7 y M9 conservan ambos aunque el mejor RMSE puntual reservado difiere. **T2** es deliberadamente ajeno al catálogo (tres etapas) y **G3 conserva CS-02**: el caso refuta cualquier inferencia de que el gate siempre detecta mecanismos fuera de catálogo. Las predicciones para CS-01/CS-02 son las mismas para S y D si el ajuste es el mismo; elegir ambos no produce ventaja estructural sobre enumeración.

## Contratos y conclusión

- El caso R4 demuestra la utilidad de la reparación G3 mixta para preservar las selecciones originales y registrar el descarte técnico, sin atribuirlo al LLM.
- El error de predicción cuando G3 considera un candidato adecuado muestra incertidumbre paramétrica no resuelta; no debe confundirse con fallo estructural.
- **No se midió** utilidad autónoma de elegir perturbación: `next_test` sigue siendo texto y la prueba fue fijada externamente.
- Este lote es preliminar; no repetirlo en busca de una selección 'exitosa' sin preregistrar otros mundos y un criterio de conclusión.
- Antes de llamarlo piloto íntegro Arena se necesitan una captura S-only con los recibos que exige PR #17, simulaciones OpenModelica por caso, predicciones LOCK antes de abrir reservas y comparación con D pareada. Los resultados actuales no deben importarse a ese nuevo experimento como datos ciegos.
