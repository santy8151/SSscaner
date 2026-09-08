# Avance para LinkedIn — septiembre de 2026

⚡ Hoy comparto un avance de Ssscaner, mi emprendimiento de diagnóstico automotriz para sistemas eléctricos y térmicos.

Mi objetivo es darle al técnico mejores herramientas para medir, interpretar y documentar antes de desmontar. Estoy convirtiendo esa idea en una beta de software bajo la propuesta BTMGPA, conectando experiencia de taller, señales físicas y modelos de aprendizaje automático.

Esta versión concentra el trabajo en dos espacios:

🔧 **Instrumentos:** manómetros visuales, análisis de frecuencia de muestras importadas y un visor de reconocimiento de luces preparado para cargar modelos entrenados en Teachable Machine. Incluye una conexión BLE de lectura configurable según el protocolo del sensor.

🧠 **Redes y análisis:** configuración por componente —como compresor, condensador, evaporador o motor— con cinco métodos: MLP, Random Forest, K-Means, PCA e Isolation Forest. En la red MLP, el técnico puede cambiar capas, nodos, activación, batch size y learning rate. Cada método muestra los controles que realmente utiliza.

El entrenamiento ya se ejecuta y conserva su configuración y resultados. En esta etapa usamos datos sintéticos SAMPLE: esas métricas todavía no demuestran precisión diagnóstica en vehículos reales. La siguiente validación necesita datos de taller, sensores documentados y modelos de visión entrenados para nuestras condiciones de trabajo.

En gestión térmica analizamos la relación entre el circuito refrigerante, el chiller y la refrigeración de batería y motor, según la arquitectura de cada vehículo. Los modelos experimentales no fijan cargas de refrigerante ni ejecutan comandos sobre una ECU.

Estoy preparando la documentación técnica y el protocolo de validación para seguir llevando esta idea al taller. Busco conversar con técnicos, talleres y personas interesadas en acompañar esta etapa de desarrollo.

🚗 Menos suposiciones. Más mediciones y evidencia.

#Ssscaner #VehículosEléctricos #DiagnósticoAutomotriz #MachineLearning #BTMGPA #Ingeniería

---

## Notas antes de publicar

- Adjunta `promo/SSScanner-promo-BETA.mp4`. El video representa una beta técnica.
- No se han publicado este texto ni el video en ninguna cuenta.
- Se omiten afirmaciones de alianzas formales, validación por Ruta N e integraciones comerciales de IA: deben confirmarse con su alcance y autorización antes de anunciarlas. Puedes agradecer conversaciones con Alisan PG y RH Performance si corresponde, sin atribuirles una validación no documentada.
- No afirmar que los EV carecen de radiador: un chiller puede coexistir con radiadores y otros intercambiadores.
- No presentar un cable salva memorias OBD2 como escáner, interfaz IoT o programador.

## Fuentes técnicas consultadas

- [Teachable Machine: biblioteca oficial de imagen](https://github.com/googlecreativelab/teachablemachine-community/tree/master/libraries/image)
- [MLP](https://scikit-learn.org/stable/modules/generated/sklearn.neural_network.MLPClassifier.html), [Random Forest](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html), [K-Means](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html), [PCA](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html), [Isolation Forest](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html).
- [DOE: gestión térmica integrada](https://www.energy.gov/sites/prod/files/2014/03/f10/vss046_rugh_2012_o.pdf)
- [Bosch: función del salva memorias](https://www.boschdiagnostics.com/products/bat-35-vehicle-computer-memory-saver)
