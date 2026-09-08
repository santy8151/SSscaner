# Demostración de SSScanner BETA 0.3

Estado: beta técnica; no producto homologado ni compatibilidad universal con instrumentos.

1. Entrar a Instrumentos y pulsar BETA para explicar alcance y pendientes.
2. Cargar demo SAMPLE: mostrar ambos manómetros y exportar la captura.
3. Cargar la señal SAMPLE de 62.5 Hz y analizarla. Explicar resolución, RMS y procedencia.
4. Mostrar el visor iframe de luces. Si se dispone del modelo exportado desde Teachable Machine, cargarlo y probar una imagen. Sin modelo, mostrar su estado pendiente.
5. Abrir Redes neuronales: seleccionar Compresor y ajustar capas, nodos, épocas, batch size y learning rate de MLP. Entrenar y exportar la evidencia. Comparar controles con Random Forest, K-Means, PCA e Isolation Forest.
6. En Instrumentos, abrir Conectar sensores BLE. Mostrar el mapa GATT requerido; conectar solo un equipo compatible y documentado. La prueba automatizada usa una fixture y no demuestra compatibilidad física.

Las métricas SAMPLE no acreditan diagnóstico en vehículos. Los modelos no mandan señales a ECU ni fijan cargas de refrigerante. Un cable salva memorias conserva alimentación, no transmite telemetría.

Ver BETA-03.md para detalles, LINKEDIN-AVANCE.md para difusión y ../promo/SSScanner-promo-BETA.mp4 para el video. Las pantallas de versiones anteriores están bloqueadas.
