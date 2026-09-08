# Esquema inicial y migración

PostgreSQL es el objetivo. UUID como identificadores; UTC/timestamptz para eventos; valores técnicos con unidad explícita. `organization_id` en toda entidad de negocio. Catálogos globales solo lectura; datos privados por empresa. FKs compuestas `(organization_id, resource_id)` evitan referencias entre empresas; unicidad por tenant cuando aplica. El esquema ejecutable de primera fase es un subconjunto, no 30 CRUDs vacíos.

## Subconjunto ejecutable de primera fase

`organizations`, `users` (cuenta asociada a una empresa en esta fase), `auth_sessions`, `vehicles`, `scan_sessions`, `telemetry_batches`, `audit_logs`. Tablas con nombres separados del SQL heredado. Inicio local crea el esquema solo si `AUTO_CREATE_SCHEMA=true`; despliegue utiliza el comando de inicialización explícito. Esta base inicial se sustituirá por migraciones Alembic versionadas antes del primer cambio de esquema con datos reales; no actualizará tablas existentes silenciosamente.

## Modelo objetivo del MVP

Ampliación BETA ejecutable: `device_profiles` (mapa GATT inmutable y FK de tenant/equipo), `device_readings` (raw, valor, unidad, origen CLIENT_BLE, idempotencia y mapa utilizado) y `model_runs` (configuración, autor, estado/progreso, métricas SAMPLE). Son tres tablas adicionales; no se alteran columnas históricas. DDL actualizado en schema-phase1.sql. En este esquema inicial las fechas de negocio están serializadas en ISO UTC; migrarlas a timestamptz con una migración explícita al consolidar PostgreSQL.

| Tabla | Campos y relaciones principales |
|---|---|
| organizations | id, slug único, name, status, created_at |
| users | id, email normalizado, password_hash, status; futura identidad global |
| organization_memberships | organization_id, user_id, role, status; UNIQUE(org,user) al habilitar usuarios multiempresa |
| technicians | org, user/membership, credenciales profesionales, competencias, expiración |
| customers | org, id, name, contacto mínimo, consentimiento/retención |
| manufacturers | id, name, fuente |
| models | id, manufacturer_id, name, variante, años aplicables |
| engines | id, model_id, código, variante; SOURCE_REQUIRED si no documentado |
| vehicles | org, id, customer_id?, model_id?, engine_id?, identificador/VIN?, clase, año, horas/km |
| machines | org, id, kind: heavy_equipment/service_station, model_id, serial; evita confundir maquinaria atendida con estación de servicio |
| ecu_modules | org, id, vehicle_id, dirección/módulo, protocolo, versión de identificación |
| devices | org, id, hardware_serial, firmware_version, capabilities, mode, last_seen |
| scan_sessions | org, id, vehicle_id, device_id?, actor, origen, protocolo, inicio/fin, estado |
| raw_frames | org, id, session_id, secuencia, timestamp UTC + monotónico, bus/channel, identifier, payload, flags; inmutable |
| telemetry_batches | org, id, session_id, idempotency_key único por sesión, schema_version, payload, created_at |
| sensor_readings | org, id, session_id, signal, value, unit, quality, observed_at, raw_frame_id, decoder_version |
| dtc_codes | org, id, session_id, sistema OBD/J1939, código o SPN/FMI, occurrence_count, estado; no traducir sin fuente |
| maintenance_records | org, vehicle/machine, actor, fecha, horas/km, servicio, piezas, resultado confirmado |
| maintenance_plans | org, equipo/plantilla, intervals_calendar/km/hours, fuente, próxima ejecución |
| diagnostic_results | org, session_id, engine/rules_version, quality, evidence, hypotheses, recommendations, created_by |
| ai_predictions | org, diagnostic_id, model_version_id, features_snapshot, output, uncertainty, applicability |
| refrigerants | id, designación, referencias documentales; sin tabla P/T inventada |
| compressors | id, manufacturer/model, oil_spec_source, propulsion_type |
| ac_systems | org, vehicle/machine, refrigerant_id, compressor_id, arquitectura, label_reference |
| technical_specifications | id, publisher, document_ref, content_hash, license, revision, applicability, status, approved_by/at, supersedes_id |
| service_procedures | id, specification_version_id, pasos, condiciones previas, herramientas, límites, versión |
| calibration_profiles | org, id, vehicle/machine, version, specification_version_id, status, previous_values, current_values, author, validation_method, supersedes_id, digest |
| profile_approvals | org, profile_id, digest, técnico, decisión, fecha, expiración; append-only |
| machine_integrations | org, station_id, transport, capability_version, secret_reference, enabled=false |
| service_jobs | org, profile_version, station, technician_confirmation, idempotency_key, state, receipts; fase futura |
| alerts | org, equipment/session, rule/model, severity, status, acknowledged_by/at |
| audit_logs | org, actor, action, resource_type/id, request_id, timestamp, resultado; append-only |
| dataset_versions / model_versions | manifest_hash, filtros, provenance, splits, artifacts, métricas, aprobación, fechas |

Relaciones técnicas: vehículo → sesiones → tramas/lecturas → diagnósticos. Sistema A/C → especificación aprobada → perfil versionado → aprobación → trabajo de estación. Diagnosis puede referenciar un perfil, no modificarlo.

Índices: `(org, observed_at)`, `(org, vehicle_id, started_at)`, `(session_id, signal, observed_at)`, `(org, status, due_at)`. Separar catálogo de DTC de ocurrencias. Particionado/TimescaleDB solo tras mediciones de carga. Datos crudos en almacenamiento de objetos cuando el tamaño lo justifique.

Retención y backup requieren política del taller. Exportar sin secretos; registrar acceso. Restauraciones deben comprobar filas de todas las empresas: RLS no debe producir backups parciales inadvertidos.
