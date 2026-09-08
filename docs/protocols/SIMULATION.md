# Simulación y abstracción de hardware

Contrato de solo lectura: `HardwareAdapter.capabilities()`, `read_sample()`, `close()`. Cada evento tiene versión, origen, dispositivo, timestamp UTC, secuencia, protocolo y señales con unidad/calidad. No hay método `send`, `write` ni control de actuadores.

Primera fase: Vehicle Simulator genera señales **SAMPLE** determinísticas por escenario y secuencia: rpm, temperatura de motor, voltaje, presión baja/alta, temperatura ambiente/evaporador y estados de compresor/ventilador. DTC de prueba usa etiqueta `SAMPLE_SENSOR_FAULT`, no un código SAE inventado. Los números del simulador son fixtures de interfaz, no rangos oficiales ni datos de entrenamiento.

Escenarios diseñados: normal, low_refrigerant, overcharge, condenser_airflow, fan_fault, compressor_fault, sensor_fault. Se añade disconnected como octavo escenario para validar ausencia de señales. Una etiqueta de escenario representa una condición sintética elegida, no una avería inferida.

Selección OBD-II/CAN/J1939 en esta fase modifica metadatos, no genera una trama válida del estándar. Siguiente bloque:

- `CanFrame`: timestamp, channel, arbitration_id, is_extended, is_fd, dlc, bytes, flags; validación separada CAN clásico/FD.
- Replay de capturas autorizadas con reloj virtual, semilla, pérdida, duplicación, desorden, wrap de secuencia y desconexión.
- CAN genérico no tiene significado por sí solo: decodificador requiere DBC/catálogo versionado y autorizado; desconocidos se conservan raw.
- J1939: parsing de identificador extendido, PGN/destino según PDU, SPN/FMI y ensamblado TP con límites/timeouts, NAME/address claiming cuando aplique. Diccionario SAE DA licenciado; no reconstruir señales propietarias por intuición.
- OBD-II sobre CAN: transporte ISO-TP, servicios/PID soportados y respuestas negativas; documentar ECU y disponibilidad. No afirmar soporte universal de todos los vehículos.
- Sensores externos: ID/serial de sensor, rango eléctrico, unidad, referencia absoluta/manométrica, offset y certificado/fecha de calibración. Datos inválidos se ponen en cuarentena.
- Hardware futuro: MCU, transceiver, alimentación/protecciones, aislamiento según diseño, memoria para store-and-forward, USB/BLE/Wi-Fi, OTA firmada con rollback. No seleccionar PCB ni garantizar certificación sin requisitos de banco.

No conectar este simulador a un vehículo real; no emite mensajes al bus. No existe fallback de hardware fallido a simulación: el usuario debe iniciar explícitamente una sesión SAMPLE.
