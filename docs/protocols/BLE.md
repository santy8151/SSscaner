# Conexiones BLE · BETA

Implementado: selector Web Bluetooth, conexión GATT, lectura de característica, suscripción de notificaciones, desconexión explícita y limpieza al salir de la vista. Sin comandos de actuadores, escritura de parámetros o fallback a datos SAMPLE. Suscribirse a notificaciones usa la operación estándar de configuración del cliente GATT; no programa una estación de refrigerante.

Requiere Chrome/Edge con Web Bluetooth habilitado, contexto seguro (localhost o HTTPS), adaptador Bluetooth y permiso que concede el usuario en el selector del navegador. Si el navegador integrado no expone la API, abrir la app en un navegador compatible. No se intenta saltar el selector de permisos.

## Datos que debe aportar el fabricante/técnico

Marca/modelo, referencia del manual y revisión, UUID de servicio y característica en formato de 128 bits, tipo numérico, orden de bytes, posición, escala, offset, unidad y referencia de presión. No se precargan UUID ni escalas de un dispositivo inventado.

El conector actual decodifica un campo numérico uint8/int16/uint16/int32/uint32/float32. No sirve automáticamente para Bluetooth clásico/SPP, cifrado propietario, checksums, múltiples campos acoplados, protocolos que requieren comandos de inicio ni todas las marcas de manómetros. Esos equipos requieren un driver específico y documentación; no improvisar comandos de escritura.

Perfil guardado = `UNVERIFIED_MAPPING`, no homologación ni calibración física. El cálculo raw × escala + offset es una conversión declarada, no un ajuste enviado al sensor. Mantener presión absoluta y manométrica diferenciadas; no convertir entre ellas sin la referencia necesaria.

## Flujo y trazabilidad

1. Registrar equipo y perfil numérico con fuente.
2. Pulsar «Conectar Bluetooth real» y elegir el dispositivo.
3. Abrir servicio/característica; leer o suscribirse si el dispositivo lo permite.
4. Enviar raw_hex + timestamp + idempotency_key a la API autenticada.
5. La API interpreta con el perfil inmutable del tenant, rechaza tramas cortas/no finitas y guarda bytes/valor/unidad.
6. Mostrar lectura como `CLIENT_BLE`, con `browser_reported_not_device_attested` y `UNVERIFIED_MAPPING`.

La API no puede probar criptográficamente que un cliente no fabricó un paquete. Antes de captura de producción: identidad/certificado del dispositivo o gateway firmado, secuencias, replay protection y pruebas del driver. La vista limita envíos automáticos a uno cada dos segundos; no es adquisición de alta frecuencia ni conserva todas las notificaciones de un osciloscopio. «Leer ahora» hace una lectura adicional.

Nuevas tablas: `device_profiles` (FK de empresa/equipo, configuración), `device_readings` (FK compuesta, raw/value, origen e idempotencia). Sin endpoints de editar un perfil existente: crear otro para preservar el mapa usado en el historial.

Pruebas automatizadas usan UUIDs y bytes ficticios marcados TEST; no son documentación OEM ni pruebas físicas. La compatibilidad física sigue pendiente de marca/modelo y un ensayo con el instrumento del usuario.

Fuente primaria: [Chrome for Developers: Web Bluetooth](https://developer.chrome.com/docs/capabilities/bluetooth).
