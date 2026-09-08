# SSSCANER — Despliegue y validación

Este documento mantiene el despliegue del proyecto sin cambiar el diseño ni el funcionamiento actual.

## 1) Requisitos

- Docker + Docker Compose
- Linux, WSL2 o máquina con soporte para contenedores
- Puerto 3000, 8000, 8001, 8002, 8003, 8005 y 5432 disponibles
- Variables definidas en .env (ver .env.example)

## 2) Preparación

```bash
cp .env.example .env
```

Ajusta los valores si necesitas cambiar el puerto, JWT o credenciales.

## 3) Levantar el stack

```bash
docker compose up --build -d
```

## 4) Validar salud de servicios

```bash
docker compose ps
docker compose logs -f
```

Los servicios incluyen health checks para verificar estado básico.

## 5) Endpoints principales

- Frontend: http://localhost:3000
- API Gateway: http://localhost:8000/health
- Auth: http://localhost:8001/health
- Scanner: http://localhost:8002/health
- ML: http://localhost:8003/health
- MCP: http://localhost:8005/health
- Ollama: http://localhost:11434
- PgAdmin: http://localhost:5050

## 6) Pruebas mínimas

```bash
pytest -q tests/test_health.py
```

## 7) Recomendación de despliegue

- Usar Docker Compose para entorno de laboratorio y pruebas
- Usar Kubernetes para entorno de producción o escalado
- Mantener .env fuera del repositorio en entornos reales
- Cambiar JWT_SECRET y credenciales por valores seguros antes de producción

## 8) Observaciones

No se modifica diseño ni flujo funcional del proyecto. La mejora aquí es técnica y operativa: estabilidad, salud del sistema, variables centralizadas y validación básica del stack.
