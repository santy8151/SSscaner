# SSScanner

Base modular para diagnóstico, mantenimiento y calibración de vehículos livianos, pesados y maquinaria, comenzando por A/C. **BETA técnica: laboratorio SAMPLE, conector BLE configurable sin validación de campo y calibración bloqueada sin fuentes.**

## BETA 0.3: dos espacios, tres instrumentos

Las únicas pantallas de producto habilitadas son `/instruments` y `/models`. El botón **BETA** explica el alcance actual. Las rutas anteriores están bloqueadas. Ver [alcance y límites de la versión](docs/BETA-03.md) y [avance para LinkedIn](docs/LINKEDIN-AVANCE.md).

- **BLE de solo lectura:** selector real de Web Bluetooth, sujeto a navegador compatible y mapa GATT del fabricante introducido manualmente. La API interpreta bytes raw con ese mapa y conserva lecturas separadas de SAMPLE. Falta comprobar un manómetro físico y conocer marca/modelo/protocolo del usuario. No se afirma compatibilidad universal ni se controla una máquina.
- **Entrenamiento real sobre SAMPLE:** MLP configurable (capas, nodos, activación, Adam/SGD, épocas, batch size y learning rate), Random Forest, K-Means, PCA e Isolation Forest. Selección de variables por componente, trabajo asíncrono, métricas propias del método, historial y artefactos por empresa.
- **Tres instrumentos:** relojes de presión, API de frecuencia sobre muestras uniformes importadas y visor iframe para el modelo de luces exportado por el usuario desde Teachable Machine. Sin modelo de luces incluido ni validación de cámara de campo.
- Las métricas sintéticas no equivalen a diagnóstico validado. Calibration continúa bloqueado sin fuente OEM.

Ver [guía de demostración](docs/INVESTOR_DEMO.md) y [conexiones BLE](docs/protocols/BLE.md). La ampliación incorpora tres tablas nuevas sin modificar las existentes.

## Qué funciona

- React + TypeScript + Vite: Instrumentos, Redes neuronales, vehículos integrados en Instrumentos y exportación JSON.
- FastAPI: empresas, login/logout, tokens revocables, contraseñas scrypt, RBAC admin/technician/viewer, aislamiento por empresa y auditoría transaccional.
- Persistencia local SQLite; modelos/configuración PostgreSQL para Docker.
- Ocho escenarios SAMPLE, unidades/calidad, ingestión validada e idempotencia.
- Diagnosis entrega evidencia y SOURCE_REQUIRED, sin confianza inventada. Calibration devuelve SOURCE_REQUIRED y cantidades null; no acepta parámetros de IA.
- Health/readiness, OpenAPI, límites de peticiones/cuerpo, tests y lint.

## Ejecutar localmente · PowerShell

Desde la carpeta que contiene este README:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-mvp.lock
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
Push-Location apps/web
npm.cmd ci
npm.cmd run build
Pop-Location
.\.venv\Scripts\python.exe -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
```

Abre [la aplicación](http://127.0.0.1:8000) y [OpenAPI](http://127.0.0.1:8000/docs). Requisitos: Python 3.11+ y Node 22.12+ compatible. La API sirve la web compilada. Para desarrollar la web: API en 8000 y `npm.cmd run dev` desde `apps/web`, con Vite en 5173.

Elige **Crear empresa · solo desarrollo**, usa identificador `mi-taller`, correo y contraseña de al menos 12 caracteres. En Instrumentos puedes registrar un vehículo, cargar SAMPLE, configurar BLE o importar una señal. En Redes neuronales puedes seleccionar un componente y entrenar. El token vive en memoria de la pestaña; recargar requiere login, pero las cuentas y mediciones persisten en `data/local/ssscanner.db`.

Variables: `.env` o `uvicorn --env-file .env.mvp`. Ver `.env.mvp.example`. Si existe un `.env` del legado, revisar DATABASE_URL y APP_ENV. No subir secretos.

## Tests y lint

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
Push-Location apps/web
npm.cmd run lint
npm.cmd run build
Pop-Location
```

La suite nueva es `tests/mvp`. `tests/test_health.py` corresponde a los servicios heredados incompatibles y no se afirma que pase. Ver `docs/architecture/VERIFICATION.md` para evidencia y límites. Los locks fijan las dependencias instaladas; el lock Python incluye herramientas de pruebas.

## PostgreSQL / Docker

Requiere Docker con Compose. Copia `.env.mvp.example` a `.env.mvp` y sustituye ambos marcadores de contraseña por el mismo secreto (URL-encode en el DSN si aplica).

```powershell
docker compose --env-file .env.mvp -f compose.mvp.yml up --build -d
docker compose --env-file .env.mvp -f compose.mvp.yml run --rm api python -m scripts.manage create-admin --organization mi-taller --email admin@taller.com
```

El segundo comando solicita contraseña. Registro público deshabilitado en production. `init-db` crea tablas ausentes: **no modifica esquemas existentes ni reemplaza migraciones**. Antes de datos reales: migraciones versionadas, rol runtime separado del propietario, RLS, TLS y backup/restauración probados. El Compose es un banco local en loopback; no un despliegue endurecido. No expone PostgreSQL al host. Docker no estaba instalado en el entorno de esta entrega; su ejecución no está verificada.

No usar `docker-compose.yml` heredado para iniciar el MVP.

## Estructura

```text
apps/api/                 FastAPI, acceso, RBAC, persistencia
apps/web/                 React + TypeScript + Vite
services/diagnosis/       evidencia, sin inferencias ficticias
services/calibration/     frontera bloqueada sin fuente
services/ml/              entrenamiento experimental y artefactos SAMPLE
services/maintenance/     módulo reservado
packages/shared/          contratos de telemetría
packages/protocols/       interfaces de hardware/estación
hardware/simulator/      Vehicle Simulator SAMPLE
hardware/firmware/       requisitos futuros, sin PCB
data/sample/             política de fixtures
data/training/           política de datasets
docs/architecture/       esquema, análisis, verificación
docs/api/                APIs actuales y futuras
docs/protocols/           CAN/J1939/OBD/sensores
docs/calibration/        validación y límites
docs/ml/                 evolución por etapas
infra/docker/            imagen del MVP
tests/mvp/               pruebas del nuevo esqueleto
scripts/                 provisión explícita de DB/admin
promo/                   video y fuente reproducible
```

El legado (`backend/`, `frontend/`, `static/`, `AWS/`, `terraform/`, SQL antiguo) permanece para migración por módulo. Las mejoras de seguridad/comparación manual iniciadas antes del brief están en `backend/api` y `static/technical.*`; no son la entrada nueva. README original preservado en `docs/architecture/README_LEGACY.md`.

## Qué falta y siguiente bloque

Fuentes OEM/licencias, perfiles aprobados versionados, reglas revisadas, mantenimiento/clientes operativo, normalización de tramas reales, validación con sensores físicos, RLS, migraciones, multiworker, restauración y ML validado en campo. Maquinaria/mantenimiento/clientes/configuración muestran su estado pendiente. No existe control de estaciones ni carga por presión. Los modelos del laboratorio se entrenan con SAMPLE; no se han validado para diagnóstico real.

Siguiente bloque: verificar PostgreSQL/migraciones/aislamiento, ampliar ingestión y replay del simulador y obtener una ficha OEM autorizada para el primer flujo de aprobación técnica.

[Arquitectura](ARCHITECTURE.md) · [Roadmap](ROADMAP.md) · [Datos](docs/architecture/DATABASE.md) · [API](docs/api/CONTRACTS.md) · [Simulación](docs/protocols/SIMULATION.md).
