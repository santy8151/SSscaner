# SSScanner · Roadmap por puertas de validación

## Bloque actual: primera tarea

Analizar legado; acordar monolito modular; definir esquema, APIs, hardware y separación de motores; crear monorepo ejecutable con auth/RBAC, equipos, simulador SAMPLE mínimo, persistencia y contratos bloqueados; instalar, ejecutar, probar y documentar. No equivale a completar todas las fases 0–14 del producto.

## Bloques siguientes

Ampliación posterior solicitada: entregados botón BETA, conector Web Bluetooth configurable (sin validación física) y laboratorio MLP/Random Forest con entrenamiento SAMPLE. Esto permite demostrar arquitectura/experimentación, pero no completa las puertas de campo de fases 8–11 ni las de operación PostgreSQL.

| Fase | Entrega | Criterio para avanzar |
|---|---|---|
| 0–2 | Arquitectura y monorepo | Entrada única; legado identificado; documentación y decisiones trazables |
| 3–4 | API y PostgreSQL | Migraciones en PostgreSQL real, roles DB, aislamiento, backup/restauración probados |
| 5–6 | Simulador e ingestión completos | Ocho escenarios, timestamps y pérdida/desorden, idempotencia, unidades, replay y cuarentena |
| 7 | Dashboard técnico | Rutas operativas, conexión y origen visibles, accesibilidad, E2E, sin datos ficticios ocultos |
| 8 | Rules/Diagnosis Engine | Reglas revisadas por técnico con evidencia y pruebas; sin confianza inventada |
| 9 | Calibration Engine | Catálogo OEM licenciado, aprobaciones, perfiles inmutables, estados SOURCE_REQUIRED/REJECTED/VALIDATED probados |
| 10 | Mantenimiento | Historial por equipo, horas/km/fecha, planes y alertas deduplicadas |
| 11 | Estadística y ML básico | Dataset real gobernado, baseline, evaluación por equipo/tiempo, registro y rollback |
| 12–14 | Calidad, Docker y operación | CI, restauración, carga, seguridad, métricas y manual de taller; se trabajan incrementalmente |
| Posterior | Hardware CAN/J1939/OBD | Drivers de solo lectura, pruebas en banco y validación con documentación autorizada |
| Posterior | Estaciones automáticas | Protocolo OEM, banco de pruebas, compatibilidad, confirmación y límites; sin escritura desde IA |

## Siguiente bloque recomendado

Consolidar PostgreSQL real y el pipeline SAMPLE: migraciones versionadas, RLS y roles limitados, lotes idempotentes, exportación de datos crudos y normalizados, ocho escenarios con errores de sensor y desconexiones. Obtener en paralelo una ficha A/C real autorizada con marca/modelo/variante/refrigerante y revisión para diseñar el primer flujo de aprobación de Calibration.

No comprar hardware ni entrenar redes neuronales antes de validar el contrato de datos y la disponibilidad de fuentes técnicas.
