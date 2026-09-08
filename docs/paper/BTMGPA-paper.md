# BTMGPA: arquitectura modular y protocolo de validación para diagnóstico térmico y eléctrico asistido por aprendizaje automático

**Ssscaner · Documento técnico de trabajo · Versión 0.4 · 8 de septiembre de 2026**

Autoría institucional propuesta: Proyecto Ssscaner. Nombre del autor, afiliación formal y datos de contacto pendientes de completar antes de envío. Borrador elaborado con asistencia de IA; requiere revisión técnica del responsable del proyecto. No revisado por pares. No se declara novedad patentable, homologación ni resultados de campo.

## Resumen

Se presenta BTMGPA como una arquitectura de adquisición, análisis y trazabilidad para explorar el diagnóstico de sistemas térmicos y eléctricos de vehículos. La propuesta parte de la adaptación de un equipo de limpieza o servicio del sistema de refrigeración descrita por el fundador, al que se agregan instrumentos de presión, adquisición de señales eléctricas y visión de luces. Se distingue el equipo de servicio de la interfaz de datos y del accesorio salva memorias. El software implementado concentra la interacción en dos espacios y tres paneles instrumentales: manómetros, frecuencia y visión. Un laboratorio ejecuta cinco métodos de aprendizaje automático sobre datos sintéticos y conserva sus configuraciones y artefactos. Se añaden cálculos deterministas de potencia y una comparación descriptiva antes/después. La verificación disponible corresponde a pruebas de software y señales sintéticas; no demuestra capacidad diagnóstica ni mejoras de agarre o rendimiento en vehículos reales. Se propone un protocolo de evaluación por vehículo y taller, con referencias instrumentales, abstención ante incertidumbre y separación entre análisis y control físico. La contribución es una integración de ingeniería reproducible y una hipótesis de trabajo; su utilidad en taller permanece por evaluar.

**Palabras clave:** diagnóstico automotriz; vehículos eléctricos; gestión térmica; adquisición de señales; aprendizaje automático; trazabilidad.

## 1. Problema, alcance y preguntas de investigación

La inspección automotriz combina señales físicas, documentación y juicio técnico. Una interfaz de análisis puede organizar esa evidencia antes de una intervención, pero no reemplaza la verificación de la causa ni convierte correlaciones en instrucciones de reparación. Este trabajo aborda la integración de fuentes heterogéneas y la exposición de parámetros de análisis al técnico sin exigirle programación.

Se plantean tres preguntas: RQ1, ¿puede una arquitectura común conservar procedencia, unidades y configuración al combinar instrumentos? RQ2, ¿ayuda la configuración guiada por componente a formular y comparar hipótesis reproducibles? RQ3, ¿reduce la herramienta tiempo de diagnóstico o errores frente al flujo habitual, con una referencia independiente? La implementación permite explorar RQ1 a nivel de software; RQ2 y RQ3 requieren un estudio con usuarios y vehículos.

BTMGPA es la denominación del proyecto para Biotecnología, Eléctrica, Mecánica, Generativa, Prompting y Agéntica. En esta versión no se implementan procesos biotecnológicos, agentes autónomos ni generación de diagramas mediante proveedores externos. El acrónimo expresa la visión del fundador; no identifica un algoritmo nuevo ni evidencia capacidades que aún no existen.

## 2. Arquitectura y adaptación del hardware

El fundador describe un módulo de limpieza del sistema de refrigeración adaptado como plataforma de trabajo. No se han recibido identificación de fabricante, esquema hidráulico, certificación, límites operativos ni protocolo de comunicaciones. Por ello, el artículo documenta esa adaptación como antecedente aportado por el fundador, no como hardware inspeccionado. Debe resolverse si la máquina trabaja con líquido refrigerante de motor/batería o con refrigerante del circuito A/C: sus fluidos, materiales, procedimientos e interfaces no son intercambiables.

Se proponen cuatro capas: (i) equipo de servicio y puntos instrumentales documentados; (ii) adquisición aislada y adaptadores de protocolo; (iii) persistencia, procesamiento y modelos; (iv) interfaz técnica y evidencia exportable. El software no controla bombas, válvulas, carga de refrigerante, dirección ni par motor. Una futura capa de actuación exigiría especificaciones y una evaluación independiente; no forma parte de la beta.

Un salva memorias OBD2 aporta alimentación auxiliar para conservar ajustes durante ciertas operaciones de batería [1]. No equivale a un escáner, un almacenamiento de telemetría ni una interfaz IoT. La comunicación OBD/CAN requiere otro adaptador y un protocolo documentado. La conexión BLE implementada solicita autorización del navegador, lee una característica GATT y aplica un formato numérico explícito; su disponibilidad depende del navegador y del instrumento [2].

Cada lectura BLE conserva bytes originales, unidad, marca temporal, perfil y procedencia CLIENT_BLE. El servidor aplica aislamiento por empresa y validación del paquete. El origen declarado por el navegador no constituye autenticación criptográfica del dispositivo. Los registros SAMPLE se mantienen identificados y no se usan como sustitución silenciosa de un instrumento ausente.

La interfaz tiene dos espacios: Instrumentos y Redes neuronales. Instrumentos contiene tres vistas de trabajo: presión/temperatura; señal eléctrica/frecuencia; y visión de luces. Las rutas de producto anteriores se bloquean. Los modelos y el banco comparativo permanecen subordinados a la evidencia, sin escribir en una ECU.

## 3. Modelo físico y tratamiento de señales

### 3.1 Gestión térmica

El circuito de refrigerante A/C y el circuito de líquido refrigerante pueden intercambiar calor mediante un chiller. Según la arquitectura, también existen radiadores y otros intercambiadores; no es correcto afirmar que todo vehículo eléctrico elimina el radiador. Las arquitecturas integradas de NREL ilustran esta coexistencia y la interacción entre batería, electrónica de potencia y climatización [3].

Para una futura evaluación térmica se propone Q_dot = m_dot · cp · (T_salida − T_entrada), bajo aproximación de flujo monofásico y propiedades apropiadas. Esta relación requiere caudal y composición del fluido; dos temperaturas por sí solas no determinan potencia térmica. En el lado de refrigerante con cambio de fase se requiere un balance de entalpía. Esos cálculos térmicos no están implementados como estimadores de capacidad del equipo en la beta.

La presión manométrica necesita una referencia atmosférica para convertirse en absoluta. No se infieren carga de refrigerante, límites de operación ni capacidad de reparación a partir de una esfera visual. La calibración crítica permanece bloqueada sin fuente OEM específica.

### 3.2 Frecuencia y potencia eléctrica

La API de frecuencia recibe N muestras uniformes y fs. Implementa un periodograma con ventana Hann y eliminación de la media; entrega la frecuencia del máximo espectral distinto de DC, resolución Δf = fs/N, RMS = sqrt(sum(x_i²)/N) y amplitud pico a pico [4]. El pico dominante puede ser un armónico; no se identifica automáticamente la frecuencia fundamental. Señales constantes devuelven frecuencia ausente.

La frecuencia de Nyquist es fs/2. Se requiere un filtro antialias adecuado antes del muestreo; la interfaz no puede recuperar componentes que ya se plegaron en frecuencia. El registro admite 32–2048 muestras y limita amplitudes numéricas para prevenir desbordamientos, sin atribuir ese límite informático al instrumento físico.

Para datos DC constantes se calcula P_el = V · I y E_Wh = P_el · Δt/3600. No se aplica directamente a potencia trifásica, transitorios ni PWM: en esos casos debe medirse e integrarse potencia instantánea en la frontera energética correspondiente. No se ha integrado un osciloscopio comercial específico.

### 3.3 Comparación de motor y dinámica

El banco manual calcula P_eje = τ · 2πn/60, con par en N·m y n en rpm. La eficiencia aparente P_eje/P_DC solo se muestra cuando el balance es físicamente compatible en régimen estacionario de motorización. Si la potencia mecánica supera a la entrada DC, se solicita revisar la frontera y simultaneidad de las mediciones; no se recorta el resultado a 100%.

Para un giro circular ideal, a_y = v²/R describe aceleración lateral requerida, no adherencia disponible. Un incremento de potencia o de a_y no prueba mejora de agarre. La evaluación de estabilidad exige información dinámica adicional; la documentación de NHTSA sobre ESC contempla comportamiento de guiñada y respuesta direccional [5]. La beta no ajusta ESC, frenos, dirección, mapa de par ni parámetros del inversor.

## 4. Aprendizaje automático y visión

Se distinguen dos ramas: clasificación visual con un modelo exportado de Teachable Machine y análisis tabular de señales. La rama visual carga pesos y metadatos en un iframe propio; ejecuta inferencia en el navegador sobre cámara o imagen local [6]. No se incluye un modelo de luces entrenado. El conjunto futuro debe contemplar encendida, apagada e indeterminado, incluyendo reflejos, oclusiones, ángulos y distintas condiciones lumínicas. Una imagen de un faro o fusible no demuestra continuidad eléctrica, calidad del contacto ni corriente real.

En la rama tabular se implementan MLP, Random Forest, K-Means, PCA e Isolation Forest [7–11]. MLP aprende una clasificación supervisada no lineal; Random Forest ofrece una referencia tabular; K-Means agrupa observaciones; PCA reduce dimensión; Isolation Forest identifica atípicos. No existe un mejor método universal. K-Means y PCA no son tipos de neuronas ni sustitutos directos de una neurona individual.

El técnico selecciona un componente y configura un módulo. Compresor utiliza presiones, tensión y estado; condensador utiliza presión alta, ambiente y ventilador; evaporador utiliza presión baja y temperaturas; motor utiliza rpm, temperatura y tensión. Las etiquetas de entrenamiento continúan siendo siete escenarios sintéticos del sistema. No se ha demostrado que esa selección identifique fallas del componente escogido.

La MLP admite de una a tres capas ocultas y de 4 a 128 nodos por capa, activación compartida, optimizador Adam/SGD, épocas, batch size y learning rate. Random Forest configura árboles y profundidad; K-Means, grupos e iteraciones; PCA, dimensiones; Isolation Forest, árboles y contaminación. No se presentan parámetros irrelevantes para cada método.

Los datos actuales son fixtures con perturbaciones sintéticas. Se realiza una separación estratificada 75/25 y el preprocesamiento se ajusta solo al subconjunto de entrenamiento. Esta separación no representa generalización entre vehículos, porque las muestras comparten su generador. Se guarda configuración, semilla, hash de datos, características, preprocesamiento y artefacto. No se reporta exactitud para los métodos no supervisados.

## 5. Protocolo propuesto de validación

### Fase A: identificación e instrumentación

Registrar fabricante, modelo y revisión de la máquina; fluidos y circuitos; interfaces disponibles; documentación del sensor; calibración; rango; resolución; incertidumbre; frecuencia de muestreo; latencia y sincronización. La incorporación de un instrumento requiere comprobar lectura frente a referencia trazable en varios puntos del rango. La tolerancia se fija a partir de la especificación y del análisis de incertidumbre, no de un umbral universal inventado.

### Fase B: adquisición y etiquetas

Definir la unidad experimental como vehículo/sesión, no cada fila aislada. Registrar fecha, taller, instrumento, temperatura, estado de carga, condiciones de uso y procedimiento de referencia. Las etiquetas de fallo deben basarse en comprobación independiente y, cuando proceda, en verificación posterior a reparación, evitando que la salida del propio modelo se convierta en verdad de entrenamiento.

### Fase C: modelos y generalización

Separar entrenamiento, ajuste y prueba por vehículo y, si es posible, por taller y periodo. Usar particiones por grupos para evitar fuga entre mediciones correlacionadas [12]. Para visión, agrupar imágenes del mismo vehículo y secuencia. Comparar contra reglas técnicas y modelos sencillos antes de incrementar complejidad. Registrar los experimentos y no optimizar hiperparámetros sobre el conjunto final.

Medir sensibilidad por clase, tasa de falsos negativos, precisión, F1 macro, matriz de confusión y cobertura de abstención. Informar intervalos de incertidumbre y tamaño de muestra. Para métodos no supervisados, evaluar estabilidad y utilidad frente a revisión experta; una métrica interna de agrupamiento no equivale a diagnóstico. El tamaño muestral deberá definirse mediante objetivos de precisión y prevalencia, aún no disponibles.

### Fase D: utilidad en taller y comparación de rendimiento

Diseñar un estudio de tiempos y decisiones con referencia técnica independiente. Definir de antemano qué es un diagnóstico correcto y qué intervenciones cuentan como innecesarias. Para motor y dinámica, mantener comparables estado de carga, temperatura, neumáticos, presión, carga, superficie e instrumentación, con repeticiones y registro de dispersión. Las pruebas dinámicas deben realizarse en una instalación adecuada; no se derivan consignas de actuación desde la beta.

## 6. Verificación disponible y límites de los resultados

La versión base 0.3 aprobó 35 pruebas Python, lint, compilación y una prueba de flujo navegador/API. La fixture BLE envía bytes ficticios 5e01 con un mapeo de prueba a 35 psi_g; se verifican persistencia y ausencia de sustitución ante denegación de permiso. Una señal sintética de 62,5 Hz se reconoce con la resolución declarada. Los cinco métodos ejecutan ajuste y almacenan artefactos; el flujo visual de Random Forest permite exportar el experimento. Estas son verificaciones de software, no resultados experimentales de vehículos.

La ampliación 0.4 incorpora el esquema del banco y la comparación física manual. Sus pruebas de consistencia deben adjuntarse al registro de verificación de la entrega. No existen en este trabajo datos de campo, un modelo validado de luces, ensayos de limpieza, mediciones de ahorro, reducción de desmontajes ni demostraciones de mejora de agarre. Tampoco se ha validado compatibilidad con una ECU o un osciloscopio comercial.

Una exactitud alta sobre fixtures fáciles no acredita valor predictivo. La ausencia de averías reales, la simplificación de variables, la dependencia entre muestras y la falta de evaluación externa impiden extrapolar. El sistema de aislamiento por empresa no constituye una auditoría de seguridad completa; se requieren validación del despliegue, copias de respaldo y revisión de dependencias antes de uso productivo.

## 7. Discusión, contribución y siguientes pasos

La principal contribución es organizar instrumentos y métodos existentes alrededor de un flujo explícito de procedencia y configuración. El técnico modifica el análisis y conserva evidencia, mientras los parámetros críticos permanecen separados. La representación por componente es una interfaz de selección de características, no una demostración de causalidad física ni un modelo digital completo del vehículo.

La primera prioridad es identificar el módulo real y documentar su adaptación. Después deben incorporarse uno o dos instrumentos con referencia trazable y un conjunto de visión limitado y bien etiquetado. Solo tras evaluar generalización y utilidad conviene ampliar tareas hacia rendimiento y dinámica. El software de análisis puede orientar mediciones adicionales; no debe convertir una salida estadística en una orden automática de intervención.

## 8. Conclusión y disponibilidad

BTMGPA se presenta como una arquitectura de software implementada parcialmente y una propuesta de integración física pendiente de caracterización. La beta permite explorar señales, ajustar modelos sobre SAMPLE y comparar cantidades físicas declaradas. El siguiente hito científico es obtener evidencia reproducible con instrumentos y vehículos reales. No se concluye aún una mejora del diagnóstico, del motor ni del agarre.

El código y los artefactos están en el espacio local del proyecto. Este documento no dispone de DOI, repositorio público de datos ni publicación académica. Antes de difundirlo como paper deben completarse autoría, identificación del hardware, licencia del código y datos, revisión de las fórmulas aplicadas y un registro reproducible de la versión evaluada. No se atribuyen alianzas, licencias ni validación institucional a terceros sin documentación.

## Referencias

[1] Bosch Diagnostics. BAT 35 Vehicle Computer Memory Saver. https://www.boschdiagnostics.com/products/bat-35-vehicle-computer-memory-saver

[2] Chrome for Developers. Communicating with Bluetooth devices over JavaScript. https://developer.chrome.com/docs/capabilities/bluetooth

[3] Rugh, J. P. (2012). Integrated Vehicle Thermal Management — Combining Fluid Loops in Electric Drive Vehicles. NREL, proyecto VSS046, 15 de mayo. https://www.energy.gov/sites/prod/files/2014/03/f10/vss046_rugh_2012_o.pdf

[4] SciPy. scipy.signal.periodogram, documentación de API. https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.periodogram.html

[5] NHTSA. Electronic Stability Control Systems. Documento de referencia sobre desempeño y estabilidad; no se presenta como dictamen normativo local. https://www.nhtsa.gov/document/electronic-stability-control-systems

[6] Google Creative Lab. Teachable Machine Community, Image Library. https://github.com/googlecreativelab/teachablemachine-community/tree/master/libraries/image

[7] scikit-learn. MLPClassifier. https://scikit-learn.org/stable/modules/generated/sklearn.neural_network.MLPClassifier.html

[8] scikit-learn. RandomForestClassifier. https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html

[9] scikit-learn. KMeans. https://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html

[10] scikit-learn. PCA. https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html

[11] scikit-learn. IsolationForest. https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html

[12] scikit-learn. Cross-validation: evaluating estimator performance. https://scikit-learn.org/stable/modules/cross_validation.html

Fuentes web consultadas el 8 de septiembre de 2026. Las versiones «stable» pueden cambiar; fijar versiones al reproducir.
