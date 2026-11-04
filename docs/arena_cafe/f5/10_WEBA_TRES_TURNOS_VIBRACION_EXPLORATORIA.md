# WEBA F5 — Exploración empírica de regímenes de vibración en tres turnos

**Fecha: 2026-11-04. Estado: EXPLORACIÓN RETROSPECTIVA, NO CIEGA.** Continuación de PR #167. Este trabajo no encuentra ni valida inicio/fin real de extracción, tipo de bebida, pedido POS ni entrega. D/B/M intactos; O2 no autorizado; G4/G5 NOT_RUN; reserva F5 independiente NOT_CREATED.

## Pregunta delimitada

¿Las señales XYZ de la cafetera WEBA contienen intervalos relativamente intensos que pueden delimitarse con reglas estadísticas reproducibles? ¿Una regla de dos turnos describe de forma coherente un tercero?

No confundimos ventanas intensas con producción, ni duración de vibración con tiempo de trabajo humano. No se establece que la vibración corresponda a una máquina funcionando; golpes, manipulación e instrumentación también son posibles.

## Procedencia

Dataset original: Department-of-System-Engineering/datasets_WEBA, commit fijo **d6841669e544579547c94b7ce1e8613bbd6b3a39**.

Se seleccionaron los siguientes turnos, ya utilizados en trabajos anteriores de Arena:

- **2024-02-23, tarde**: 4 archivos de cafetera; calibración.
- **2024-03-04, tarde**: 2 archivos de cafetera; calibración.
- **2024-03-08, tarde**: 6 archivos de cafetera; transferencia descriptiva.

Total: **12 blobs verificados por tamaño y hash SHA-1 Git**, **36,922,719 bytes**. Se recuperaron directamente de la copia descomprimida cargada por el investigador a Drive y se compararon con los hashes del repositorio original. La CI vuelve a recuperar exactamente esas rutas del origen público y verifica sus hashes antes de analizarlas. Ninguna fuente de datos biométricos, respuestas de cuestionarios o contenido POS se utilizó para ajustar el modelo.

La tercera fecha es un holdout **solamente descriptivo**: no hay etiquetas independientes ni condición ciega F5.

## Método reproducible

1. Orden de filas y tiempos de reloj tal como aparecen, **sin asumir zona horaria**. Todo retroceso temporal o salto de más de **0.3 segundos** interrumpe la continuidad. Nunca interpolar; nunca conectar archivos.
2. Ventanas temporales no solapadas de **5 segundos**; requieren **70 muestras** como mínimo y **3.5 segundos** de extensión. Se descartan ventanas parciales.
3. RMS dinámica = raíz de la suma de las **tres varianzas del acelerómetro** en cada ventana. Descriptor secundario: RMS de las diferencias entre muestras adyacentes. No son energía eléctrica, consumo, extracción ni actividad certificada.
4. Dos turnos de calibración aportan la **mediana RMS** y la **desviación absoluta mediana escalada por 1.4826 (MAD)**. Umbral principal único: mediana + **2.5 MAD**. Comprobaciones de sensibilidad: **1.5 MAD** y **3.5 MAD**, sin recalibrar por fecha.
5. Episodio estadístico candidato de **al menos 10 s**: cadena de 2 o más ventanas consecutivas por encima del umbral, dentro de **un mismo archivo y tramo temporal continuo**. No es operación de cafetera validada.
6. Exploración secundaria: **k-means determinista** de tres grupos calculado con log(RMS dinámica) y log(RMS de diferencias) de los dos turnos de calibración; se transportan sus centroides al tercero, sin reentrenar. Grupos A/B/C ordenados por RMS, **sin semántica física certificada**.

## Resultados verificados

**966,466 filas de aceleración** en los tres turnos, **cero filas descartadas por malformación**; **8,803 ventanas completas** y **17 ventanas parciales descartadas**. En las muestras consultadas no hubo saltos temporales internos mayores de 0.3 s ni regresiones, pero la existencia de archivos separados significa que **los intervalos entre archivos siguen sin observarse**.

Calibración compartida: mediana RMS = **0.095740**; MAD escalada = **0.005558**; umbral principal = **0.109636** (unidades nominales del acelerómetro; no recalibradas físicamente aquí).

| Turno | Archivos | Filas XYZ | Ventanas válidas | P10 RMS | Mediana RMS | P90 RMS |
|---|---:|---:|---:|---:|---:|---:|
| 23 feb. | 4 | 314,404 | 2,863 | 0.08792 | 0.09401 | 0.10969 |
| 4 mar. | 2 | 316,076 | 2,881 | 0.09131 | 0.09694 | 0.10347 |
| 8 mar. | 6 | 335,986 | 3,059 | 0.09134 | 0.09698 | 0.10488 |

### Umbral principal: mediana + 2.5 MAD

| Turno | Ventanas con intensidad elevada | Porcentaje de ventanas observadas | Episodios candidatos de ≥10s | Duración mediana por episodio | Mayor duración |
|---|---:|---:|---:|---:|---:|
| 23 feb. | 288 | **10.06 %** | **64** | 10 s | 50 s |
| 4 mar. | 79 | **2.74 %** | **16** | 10 s | 35 s |
| 8 mar. | 159 | **5.20 %** | **35** | 10 s | 65 s |

Los episodios de al menos 10s suman respectivamente **1,030**, **255** y **620** segundos de ventanas elevadas observadas. Las ventanas elevadas aisladas de 5s no se consideran episodios de ≥10s; los lapsos sin sensores no se cuentan como inactividad.

### Sensibilidad: episodios candidatos ≥10 s según umbral

| Umbral | 23 feb. | 4 mar. | 8 mar. |
|---|---:|---:|---:|
| Mediana + **1.5** MAD | **91** | **36** | **62** |
| Mediana + **2.5** MAD | **64** | **16** | **35** |
| Mediana + **3.5** MAD | **54** | **13** | **32** |

El orden descriptivo **23 feb. > 8 mar. > 4 mar.** se conserva en estas tres definiciones, pero el número de episodios **es sensible al umbral**. No usar tales cifras como número de bebidas o de ciclos físicos.

### Tres agrupamientos estadísticos, NO tareas

| Turno | Grupo A (RMS baja) | B (intermedia) | C (más intensa) |
|---|---:|---:|---:|
| 23 feb. | **93.43 %** | 4.23 % | 2.34 % |
| 4 mar. | **98.51 %** | 1.18 % | 0.31 % |
| 8 mar. | **96.50 %** | 2.16 % | 1.34 % |

La mayor parte de las ventanas se agrupa en una zona de contraste reducido y existen episodios infrecuentes de intensidad alta. **Esto NO demuestra tres modos físicos estables**: la partición k-means es una clasificación estadística posterior al ajuste, no anotación instrumental de funcionamiento.

## Cadena epistémica y decisión

**OBSERVADO:** aceleración XYZ; integridad de 12 archivos; distribución empírica de varianzas y diferencias; cobertura de ventanas.

**INFERIDO con definición explícita:** intensidad relativa, episodios ≥10s (64/16/35 bajo regla principal), agrupamiento A/B/C y transferencia descriptiva a tercer turno.

**DESCONOCIDO:** si corresponde a bomba, molienda, extracción, lavado, manipulación, golpe, ruido o cambio de sensor; relación entre episodios y pedidos POS; tiempo total real de máquina ocupada; throughput, límites físicos y tiempos de servicio.

**NO VALIDADO:** un episodio ≠ un café, ni un pedido terminado. No se contrastó con POS ni se estimó desfase temporal; no se calculó sensibilidad ni especificidad de un detector de actividad.

**Decisión:** hay estructura temporal suficiente para mantener **un indicador de vibración con incertidumbre**, pero no se autoriza la conversión a flujos físicos de producción, demanda atendida ni operación completada. Para avanzar hace falta **etiquetado físico independiente** de una parte de la señal o protocolo original que permita evaluar qué representan realmente las ventanas elevadas.

## Reproducibilidad y no interferencia

- Código: scripts/arena_cafe/weba_three_shift_vibration_exploratory.py
- Tests: tests/test_arena_cafe_weba_three_shift_vibration_exploratory.py
- CI: .github/workflows/arena-cafe-f5-weba-three-shift-vibration.yml
- Resultado: JSON de agregados, sin trazas crudas, tiempos individuales o identificadores personales.

**Invariantes:** D/B/M INTACTOS; O2 NO AUTORIZADO; G4=NOT_RUN; G5=NOT_RUN; F5 independent reserve=NOT_CREATED. No simular producción ni completar pedidos con episodios estadísticos.
