# Arena B-native — ejecutar motor cuantitativo oficial de Buffalo sin alterarlo

**Origen:** [UB-IAD/sd-ai](https://github.com/UB-IAD/sd-ai), MIT, SHA `5199f7b45f3a7ae4a773cb0dd8542940aabe9edc`.

**Decisión:** invocar directamente `engines/quantitative/engine.js` y `utilities/LLMWrapper.js` originales, descargados e instalados en CI sin modificar sus archivos. No se ejecuta el prompt-port de IGC y no se reusan reglas D ni moléculas.

**Prueba offline:** servidor local OpenAI-compatible devuelve una fixture explícitamente sintética con schema; la petición la construye el **LLMWrapper de Buffalo**, incluyendo schema estricto, y el motor original normaliza conexiones de stock-flujo antes de entregarla. Esta prueba no mide calidad de inferencia de IA.

**Prueba live:** el código original clasifica el alias sin prefijo `glm-5.3-flash` como modelo LMStudio/OpenAI compatible. El puente local traduce **solo el campo de transporte** `model` a `@cf/zai-org/glm-5.3-flash` y redirige al endpoint OpenAI-compatible Cloudflare usando la credencial existente. No altera prompt, esquema, variables, relaciones ni posprocesamiento. Limita a **una** petición remota; una falla estructurada del proveedor se registra como tal. Es la ejecución del motor Buffalo original mediante un transporte externo compatible, no una ejecución con proveedor nativo de Buffalo como Gemini u OpenRouter.

**Procedimiento:** PR nuevo desde `main`, sin fusiones; workflow descarga SHA exacto y ejecuta `npm ci --ignore-scripts` con lockfile original; primera ejecución offline sin secretos; después incorporación de marcador nuevo de autorización para una llamada única; archivo de evidencia con `receipt.json`, salida nativa, huellas de request, estado y proveedor, sin exponer tokens.

**Límites:** solo motor cuantitativo; no garantiza que un modelo real cumpla schema ni ecuaciones ejecutables; no incluye adaptador completo de Buffalo a OpenModelica ni ATMS de producción en este PR. D y M no ven el resultado; arena comparativa posterior. La prueba externa es sintética y no es validación de una estructura causal.

**Criterios:** distinguir (i) runtime original, (ii) cumplimiento de salida estructurada, (iii) admitibilidad de sd-json, (iv) traducción/simulación OpenModelica posterior, (v) concordancia con datos y (vi) pruebas interventivas. No fusionar mientras el gate offline falle.
