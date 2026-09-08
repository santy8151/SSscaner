# Beta 0.3 — alcance verificable

Esta versión sustituye la navegación anterior por dos rutas: `/instruments` y `/models`. `/` abre Instrumentos. El servidor devuelve 404 a las anteriores páginas de producto. Los endpoints autenticados siguen disponibles para no romper la persistencia ni las integraciones de datos. `vision-frame.html` y `vision-frame.js` son recursos del iframe, no una tercera pantalla de producto.

## Instrumentos

- Vehículos: registro y selección dentro de Instrumentos.
- Manómetros: última lectura por perfil BLE del vehículo seleccionado, ordenada por fecha, con unidades originales; actualización explícita. No se presentan registros antiguos como transmisión activa. Los máximos de esfera son escalas visuales manuales, no límites de servicio. SAMPLE se activa con un botón distinto.
- BLE: selector del navegador, lectura/notificaciones y persistencia con bytes crudos, marca temporal y conversión explícita. Admite frecuencia en Hz además de presión, temperatura y voltaje. UUID y mapeo requieren documentación del fabricante. No hay conexión física validada ni comandos de escritura.
- Frecuencia: `/api/v1/physics/frequency`, autenticado. Periodograma Hann con eliminación de DC; frecuencia dominante, resolución fs/N, RMS y pico a pico. 32–2048 muestras uniformes, máximo de amplitud absoluta 1e9. No estima frecuencia de una señal constante. CSV de una columna sin encabezado. No confundir pico dominante con fundamental; se requiere antialias y tasa de muestreo real.
- Energía DC: `/api/v1/physics/electrical`, autenticado. P=VI y Wh=P·s/3600, con tensión/corriente constantes declaradas manualmente. No válido para AC/PWM sin integrar v(t)i(t). Resultados de física se exportan; no se guardan automáticamente en la base de datos.
- Visión: iframe propio, SDKs fijados tfjs 4.22.0 y Teachable Machine Image 0.8.5, descargados solo tras acción. Acepta únicamente enlaces de exportación HTTPS de Teachable Machine. Captura de cámara solo a petición, detiene tracks al salir/ocultar pestaña; imágenes locales, sin upload. No hay modelo preentrenado de luces incluido. Falta validar la inferencia con el modelo del usuario y un dataset de campo.

## Modelos

Cinco métodos ejecutables con scikit-learn. MLP y Random Forest son clasificadores; K-Means agrupa; PCA reduce dimensión; Isolation Forest detecta atípicos. Los tres últimos no reportan exactitud diagnóstica. El técnico cambia un módulo de análisis por componente, no transforma una neurona individual en otro algoritmo.

El componente restringe entradas: compresor (presiones, tensión, estado), condensador (presión alta, ambiente, ventilador), evaporador (presión baja y temperaturas), motor (RPM, temperatura, tensión). Las etiquetas siguen siendo los siete escenarios sintéticos del sistema. La activación MLP se comparte entre sus capas; no hay activación distinta por neurona en este motor. Se ajustan 1–3 capas y 4–128 nodos por capa.

El experimento persiste configuración, componente, hash del dataset y métricas; el artefacto conserva el preprocesamiento y las características. El laboratorio no reprograma una ECU, no envía consignas de actuador y no determina parámetros de calibración críticos.

## Pendiente de campo

Modelo/exportación de Teachable Machine, modelo y protocolo real de cada instrumento, dataset independiente por vehículo/taller, validación OEM, validación de PostgreSQL/despliegue y evaluación de seguridad de producción. La beta sirve como avance demostrable; no se declara lista para servicio automotriz en producción.

La selección de métodos se basa en sus tareas y documentación oficial, no en un ranking universal. Fuentes y texto de difusión: `LINKEDIN-AVANCE.md`.
