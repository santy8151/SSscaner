# API v1

OpenAPI de la implementación: `/docs` y `/openapi.json`. Errores: 401 sesión inexistente/expirada; 403 rol insuficiente; 404 recurso ausente o ajeno; 409 duplicado; 422 contrato inválido; 429 límite de peticiones. El tenant se obtiene de la sesión. Listados de esta fase limitados a 100 entradas; siguiente fase añadirá cursor.

## Implementados en el esqueleto

| Método/ruta | Permiso | Contrato |
|---|---|---|
| GET /health | público | proceso, versión, modo; no sustituye readiness |
| GET /ready | público | conectividad de base de datos |
| POST /api/v1/auth/register | desarrollo local | organization, email, password; crea admin de una nueva empresa |
| POST /api/v1/auth/login | público | organization, email, password → token opaco con expiración |
| POST /api/v1/auth/logout | autenticado | revoca token |
| GET /api/v1/me | autenticado | organización, usuario, rol |
| POST /api/v1/members | admin | email, password, role; miembro dentro de la empresa actual |
| GET/POST /api/v1/vehicles | lectura / técnico+admin | equipo con name, kind, manufacturer/model/year opcionales |
| GET /api/v1/simulator/scenarios | autenticado | escenarios SAMPLE; no catálogo OEM |
| POST /api/v1/simulator/scans | técnico+admin | vehicle_id, scenario, protocol → sesión SAMPLE persistida |
| GET /api/v1/scans | autenticado | últimas sesiones de su organización |
| GET /api/v1/scans/{id} | autenticado | sesión, señales SAMPLE y exportación JSON |
| POST /api/v1/scans/{id}/telemetry | técnico+admin | lote normalizado SAMPLE con clave de idempotencia |
| POST /api/v1/diagnostics | técnico+admin | scan_id → evidencia disponible y SOURCE_REQUIRED, confidence=null |
| POST /api/v1/calibration/evaluate | técnico+admin | vehicle_id → SOURCE_REQUIRED, sin parámetros ni envío a máquina |
| GET /api/v1/audit | admin | eventos recientes propios |

## Ampliación BETA implementada

| Método/ruta | Permiso | Resultado |
|---|---|---|
| GET /api/v1/beta/status | autenticado | Contadores de su empresa y límites explícitos |
| GET/POST /api/v1/devices | lectura / técnico+admin | Perfil de lectura GATT nuevo, inmutable, UNVERIFIED_MAPPING |
| GET/POST /api/v1/devices/{id}/readings | lectura / técnico+admin | Histórico / raw_hex CLIENT_BLE, timestamp e idempotencia; conversión en servidor |
| GET /api/v1/ml/runs | autenticado | Experimentos de su empresa |
| POST /api/v1/ml/runs | técnico+admin | 202, trabajo de entrenamiento SAMPLE; 429 si hay otro en curso |
| GET /api/v1/ml/runs/{id} | autenticado | Estado, progreso, configuración y métricas SAMPLE |

ML solo acepta dataset_origin=SAMPLE, configuración discriminada por modelo y límites de recursos. BLE no acepta SAMPLE; el origen reportado por navegador no es atestación física. Ninguno de estos endpoints envía comandos a una estación.

## Otras APIs todavía no implementadas

`/customers`, `/machines`, `/maintenance/plans`, `/maintenance/records`, `/reports`, `/alerts`; `/technical-specifications/{id}/versions` y `/approve`; `/calibration/profiles`, `/{id}/versions`, `/{id}/approve`, `/{id}/revoke`. Mantener POST versionado para cambios de especificación. ML: `/models`, `/datasets`, `/predictions`, solo tras pipeline real.

La Integration Layer no expone ruta `/execute`. Un futuro endpoint deberá exigir perfil aprobado, versión/hash y confirmación del técnico; ni diagnóstico ni salida LLM serán comandos.
