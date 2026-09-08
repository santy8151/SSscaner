# SSSCANER

Plataforma técnica de diagnóstico automotriz con inteligencia artificial, telemetría, MCP, A/C lab y visualización de laboratorio para talleres especializados.

## Objetivo

SSSCANER combina:

- Frontend web para taller y diagnóstico técnico
- API FastAPI para orquestación de diagnósticos y telemetría
- MCP para herramientas de escáner, osciloscopio y lectura de logs
- Modelo local con Ollama/Hugging Face/Gemini/OpenAI/Workspace
- Persistencia con Django para auditoría, usuarios y sesiones
- Docker Compose y Kubernetes para despliegue orientado a máquinas Linux

## Arquitectura sugerida

La solución se diseña con separación de responsabilidades:

- `apps/api` → servicio principal de entrada y diagnóstico
- `apps/persistence` → autenticación, auditoría y almacenamiento persistente
- `static` → interfaz web del taller y flujo de diagnóstico
- `infra/k8s` → despliegue en Kubernetes
- `docker-compose.yml` → entorno de laboratorio y API local

## Flujo técnico

1. El técnico registra la estación desde la pantalla de acceso.
2. Debe iniciar conversación con la IA para desbloquear herramientas del taller.
3. La IA responde con contexto técnico y prepara la sesión MCP.
4. El escáner físico se conecta por Bluetooth y emite logs/telemetría.
5. El usuario entra a medidas de frecuencia, A/C, motor, fuga o escaneo.
6. El diagnóstico toma el contexto de la fuente seleccionada y propone una recomendación.
7. El sistema permite calibrar la red neuronal y cambiar algoritmo, nodo y épocas.

## Protocolo MCP

La API expone herramientas en `/api/mcp/tools` para lectura y análisis:

- `read_scanner_logs`
- `read_oscilloscope_fft`
- `get_vacuum_rate_change`
- `search_vehicle_diagram`

Este contrato puede adaptarse a un servidor MCP real con conexión a dispositivos físicos y bases vectoriales del taller.

## Seguridad y beta

La plataforma está marcada como BETA. No sustituye el procedimiento del fabricante ni la supervisión del técnico. Se debe validar cada diagnóstico con la documentación del fabricante, la telemetría y la experiencia del operador.

## Ejecución local

```bash
cd c:\Users\SANTIAGOSUAREZRAMIRE\Downloads\ssscaner
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload
```

Abre la URL:

```text
http://localhost:8000/
```

## Docker Compose

```bash
docker compose up --build
```

## Kubernetes

```bash
kubectl apply -f infra/k8s/api.yaml
```

## Recomendación de hardware

Para una máquina local con IA y modelos locales:

- 4 vCPU mínimo
- 8 GB RAM recomendado para API y visualización
- 16 GB RAM recomendado para Ollama local
- 32 GB RAM si se trabajan modelos de 7–8B con margen
- GPU compatible mejora sensiblemente la inferencia

## Modelo de despliegue

La capa de inferencia puede apuntar a:

- Ollama local
- Hugging Face Spaces
- Google Gemini
- OpenAI GPT
- Workspace model routing

La front-end se mantiene sin credenciales sensibles y solo recibe resultados del backend.