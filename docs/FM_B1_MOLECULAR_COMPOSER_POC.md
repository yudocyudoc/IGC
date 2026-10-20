# FM-B1 — PoC de composición molecular declarativa

**Estado:** `B1_MOLECULAR_COMPOSITION_PASS_SYNTHETIC` en GitHub Actions #2, commit `17bbf0612b3ec8afbc7d72bfaadc5880e6436167`.

## Objetivo

Conectar el compositor serial acotado con las definiciones moleculares y contratos LinkML existentes. El plan `data/synthetic/fm_b_serial_chain_plan.json` solicita candidatos de una y dos etapas; el compositor resuelve las definiciones desde el catálogo, genera sus instancias, conexiones, hashes topológicos y clases Modelica. LinkML valida las estructuras antes de que OpenModelica las ejecute en Actions.

La PoC no lee las estructuras CS-01/CS-02 ya guardadas en el fixture FM-A como entrada de composición. Usa del fixture la solicitud y las definiciones moleculares; la topología sale del plan y de la regla genérica `serial_chain`.

## Alcance y límites

- Solo usa las moléculas existentes de fuente, cola acotada y contador terminal.
- La regla conecta `source.outflow`, una secuencia de `stage.completed` y `sink.arrival`, comprobada contra puertos, direcciones, tipos y unidades del contrato.
- Los parámetros se comprueban contra las especificaciones declaradas antes de materializar candidatos.
- El modelo Modelica se renderiza recorriendo las instancias y conexiones generadas; no se ejecutan los modelos escritos a mano de la PoC B0.
- No añade ATMS, selección epistemológica, inferencia semántica ni moléculas al catálogo.
- Los valores y topologías son sintéticos; no acreditan causalidad ni fidelidad empírica.
- Los wrappers siguen `POC_ONLY_NOT_ADMITTED`; la revisión de licencias continúa diferida por instrucción del investigador.

## Evidencia que producirá Actions

El workflow genera esquemas desde LinkML, valida el documento compuesto, comprueba las clases Modelica generadas, las simula con el runtime fijado y verifica hashes de entradas/salidas y series CSV. Actions #2 pasó con 102 muestras por candidato y hashes estructurales distintos. La diferencia máxima entre las series `delivered` fue 1.9998477; los valores finales fueron 19.0986130 para una etapa y 17.0987653 para dos. La evidencia está en [GitHub Actions #2](https://github.com/yudocyudoc/IGC/actions/runs/39458708549) y su artifact `fm-b-molecular-composer`.

Este resultado acredita la composición y ejecución de esta integración sintética, no la admisión general del compositor ni la evaluación científica H-IGC.
