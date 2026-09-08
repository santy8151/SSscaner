# 🚗 SSSCANER - Plataforma Inteligente de Diagnóstico AC Automotriz

[![SSSCANER](https://img.shields.io/badge/SSSCANER-v1.0%20Beta-00d4ff?style=flat-square)](.)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square)](.)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Ready-326CE5?style=flat-square)](.)
[![Python](https://img.shields.io/badge/Python-3.11-3776ab?style=flat-square)](.)
[![React](https://img.shields.io/badge/React-18.2-61dafb?style=flat-square)](.)

**SSSCANER** es una plataforma web completa de diagnóstico de sistemas de aire acondicionado automotriz con IA integrada, que utiliza modelos de red neuronal entrenables, MCP (Model Context Protocol) para integración con hardware físico, y arquitectura de microservicios escalable.

## 🎯 Características Principales

- ✅ **Chat con IA** - Diagnóstico conversacional inteligente
- ✅ **Conexión Bluetooth** - Soporte para scanner físico
- ✅ **Manómetros Digitales** - Visualización de presión en tiempo real (Succión, Descarga, Vacío)
- ✅ **Osciloscopio Digital** - Análisis FFT de frecuencia
- ✅ **Red Neuronal Visual** - Entrenamiento de nodos personalizables
- ✅ **5 Nodos ML** - Compresor, Evaporador, Condensador, Chiller, Motor AC
- ✅ **Algoritmos Intercambiables** - Decision Tree, Linear Regression, Bayesian, MLP
- ✅ **MCP Server** - Integración con hardware físico y Ollama
- ✅ **Ollama Local** - Modelos de IA descargables localmente
- ✅ **Hugging Face** - Integración de modelos gratuitos
- ✅ **Nanobanana** - Diagramas 3D automáticos de vehículos
- ✅ **Docker + Kubernetes** - Deployment escalable
- ✅ **PostgreSQL + Redis** - Persistencia y caché
- ✅ **Autenticación JWT** - Sistema de usuarios seguro

## 🏗️ Arquitectura de Microservicios

```
SSSCANER (Arquitectura Onion + Microservicios)
├── Frontend (React + Tailwind)
│   └── Port 3000
├── API Gateway (FastAPI)
│   └── Port 8000
├── Auth Service (FastAPI)
│   └── Port 8001
├── Scanner Service (FastAPI + Bluetooth)
│   └── Port 8002
├── ML Service (FastAPI + TensorFlow)
│   └── Port 8003
├── Django Service (Persistencia)
│   └── Port 8004
├── MCP Server (FastAPI)
│   └── Port 8005
├── Ollama (Local AI)
│   └── Port 11434
├── PostgreSQL (Database)
│   └── Port 5432
├── Redis (Cache)
│   └── Port 6379
└── PgAdmin (DB UI)
    └── Port 5050
```

## 📋 Requisitos del Sistema

- **Docker Desktop** o Docker + Docker Compose
- **Linux VM (Zorin OS 19)** - Recomendado para servidor
- **RAM mínima**: 8GB (16GB recomendado)
- **CPU**: Procesador de 4 núcleos mínimo
- **Espacio**: 20GB libre (para modelos de IA)

## 🚀 Instalación Rápida (Docker Compose)

### 1. Clonar el Repositorio
```bash
git clone https://github.com/tuusuario/ssscaner.git
cd ssscaner
```

### 2. Configurar Variables de Entorno
```bash
cp .env.example .env
# Editar .env con tus valores
nano .env
```

### 3. Iniciar Servicios con Docker Compose
```bash
docker-compose up -d
```

### 4. Verificar Servicios
```bash
docker-compose ps
```

### 5. Acceder a la Plataforma
- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:8000/docs
- **PgAdmin**: http://localhost:5050
- **Ollama**: http://localhost:11434

## 📦 Instalación en Máquina Virtual (Zorin OS 19)

### Paso 1: Actualizar Sistema
```bash
sudo apt update && sudo apt upgrade -y
```

### Paso 2: Instalar Docker
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### Paso 3: Instalar Docker Compose
```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Paso 4: Clonar SSSCANER
```bash
git clone https://github.com/tuusuario/ssscaner.git
cd ssscaner
```

### Paso 5: Iniciar Stack Completo
```bash
docker-compose up -d
```

### Paso 6: Ver Logs
```bash
docker-compose logs -f frontend
docker-compose logs -f api-gateway
docker-compose logs -f ml-service
```

## 🎯 Flujo de Usuario

### 1️⃣ **Registro/Login**
- Crear cuenta con email y contraseña
- Identidad visual con tema automotriz (⚡ Rayos, rojo/naranja/azul)

### 2️⃣ **Chat con IA** (Desbloqueador)
- Conversar con asistente de diagnóstico
- Proporcionar información del vehículo
- ✅ Al interactuar, se desbloquean todas las herramientas

### 3️⃣ **Scanner Bluetooth**
- Detectar dispositivos físicos
- Conectar osciloscopio, manómetros, bomba de vacío
- Ver logs en tiempo real

### 4️⃣ **Herramientas Beta**
- **Manómetros**: Succión (azul), Descarga (amarillo), Vacío (rojo)
- **Osciloscopio**: Análisis FFT en tiempo real
- **Red Neuronal**: Visualizar y entrenar nodos

### 5️⃣ **Diagnóstico IA**
- Ingresar mediciones manuales o del scanner
- Ejecutar diagnóstico con modelos entrenados
- Recibir recomendaciones personalizadas

## 🧠 Sistema de Nodos ML

| Nodo | Tipo | Algoritmo | Accuracy | Entrada |
|------|------|-----------|----------|---------|
| **Compresor** | Fault Detection | Decision Tree | 94% | P_suction, P_discharge, Current |
| **Evaporador** | State Monitoring | MLP Neural | 92% | T_evaporator, Pressure_drop |
| **Condensador** | Heat Transfer | MLP Neural | 91% | T_condenser, Fan_speed |
| **Chiller** | Thermal Analysis | Linear Regression | 89% | T_glycol, Flow_rate |
| **Motor AC** | Electrical | Bayesian Network | 93% | Voltage, Current, Frequency |

## 🔧 Entrenar Nodos ML

En la sección **Beta → Red Neuronal**:

```python
# Cambiar épocas (10-500)
# Seleccionar algoritmo: Decision Tree, Linear Reg, Bayesian, MLP
# Presionar "Entrenar" → Modelo se actualiza en tiempo real
```

## 🔌 Integración MCP (Model Context Protocol)

El **MCP Server** permite que la IA acceda a herramientas físicas:

```json
{
  "tool": "read_oscilloscope_fft",
  "params": {
    "device_id": "AA:BB:CC:DD:EE:F1",
    "channel": "L",
    "duration_ms": 1000
  }
}
```

### Herramientas MCP Disponibles
- `read_oscilloscope_fft` - Capturar espectro
- `read_pressure_gauge` - Leer manómetros
- `read_vacuum_rate` - Medir vacío
- `predict_fault` - Diagnóstico ML
- `generate_diagram` - Diagramas HuggingFace
- `get_vehicle_info` - Info del vehículo

## 🌐 APIs REST

### Autenticación
```bash
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/verify
```

### Diagnóstico ML
```bash
POST /api/v1/ml/diagnose?vehicle_id=VH001&measurements={...}
GET /api/v1/ml/nodes
POST /api/v1/nodes/{node_id}/train
```

### Scanner Bluetooth
```bash
GET /api/v1/scanner/devices
POST /api/v1/scanner/connect?device_id=...
GET /api/v1/scanner/logs
POST /api/v1/measurements
```

### Vehículos
```bash
POST /api/v1/vehicles
GET /api/v1/vehicles/{id}
GET /api/v1/diagnostics/history/{vehicle_id}
```

## 📊 Base de Datos (PostgreSQL)

### Tablas Principales
- `users` - Autenticación
- `neural_nodes` - Configuración de nodos ML
- `diagnostic_results` - Histórico de diagnósticos
- `vehicles` - Información de vehículos
- `scanner_logs` - Registros de Bluetooth
- `measurements` - Mediciones del scanner

## 🐳 Deployment con Kubernetes

### Crear Namespace
```bash
kubectl create namespace ssscaner
```

### Aplicar ConfigMaps y Secrets
```bash
kubectl apply -f k8s/configmaps.yaml -n ssscaner
kubectl apply -f k8s/secrets.yaml -n ssscaner
```

### Desplegar Servicios
```bash
kubectl apply -f k8s/api.yaml -n ssscaner
kubectl apply -f k8s/frontend.yaml -n ssscaner
kubectl apply -f k8s/ml-service.yaml -n ssscaner
```

### Verificar Estado
```bash
kubectl get pods -n ssscaner
kubectl logs -f deployment/api-gateway -n ssscaner
```

## 🤖 Modelos Ollama Disponibles

Dentro del contenedor Ollama:
```bash
ollama pull neural-network:latest
ollama pull llama2:latest
ollama pull mistral:latest
```

Usar en ML Service:
```python
async def get_ai_recommendation(diagnosis):
    response = requests.post(
        "http://ollama:11434/api/generate",
        json={"model": "neural-network", "prompt": diagnosis}
    )
```

## 🎨 Identidad Visual

- **Colores Primarios**: 
  - Cyan: `#00d4ff` (Principal)
  - Naranja: `#ff6b35` (Secundario)
  - Rojo: `#ff3366` (Crítico)
  - Verde: `#00ff88` (Éxito)
- **Fondos**: Gradientes oscuros (`#0f1419` → `#1a2332`)
- **Tipografía**: Monospace para código, Sans-serif para UI

## 📚 Documentación Técnica

### Patrones de Diseño
- **Onion Architecture** - Separación de capas
- **Microservicios** - Independencia y escalabilidad
- **Repository Pattern** - Abstracción de datos
- **Service Locator** - Inyección de dependencias
- **MCP (Model Context Protocol)** - Integración de herramientas

### Stack Tecnológico
- **Backend**: FastAPI, Django, uvicorn
- **Frontend**: React, Tailwind CSS, Recharts
- **ML**: TensorFlow, scikit-learn, PCA
- **Base de Datos**: PostgreSQL, Redis
- **Orquestación**: Docker Compose, Kubernetes
- **IA**: Ollama, Hugging Face, Nanobanana

## 🚨 Troubleshooting

### Contenedor no inicia
```bash
docker-compose logs <service>
docker-compose restart <service>
```

### Error de conexión a PostgreSQL
```bash
docker-compose exec postgres psql -U admin -d ssscaner_db
```

### Limpiar todo y reiniciar
```bash
docker-compose down -v
docker-compose up -d
```

### Ver métricas de uso
```bash
docker stats
```

## 📝 Roadmap

- [ ] Soporte para más modelos de vehículos
- [ ] Integración con CAN Bus
- [ ] Panel de mantenimiento predictivo
- [ ] Exportar reportes PDF
- [ ] Historial de diagnósticos avanzado
- [ ] Integración con talleres (multi-tenant)
- [ ] App móvil nativa
- [ ] Análisis comparativo con otros vehículos

## 🤝 Contribuir

```bash
git checkout -b feature/tu-feature
git commit -am 'Agregar feature'
git push origin feature/tu-feature
```

## 📄 Licencia

MIT License - Ver archivo LICENSE para detalles

## 👨‍💻 Autor

Creado por el equipo de SSSCANER

---

**Hecho con ⚡ para mecánicos y técnicos de A/C automotriz**
