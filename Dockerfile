FROM node:22-alpine AS web
WORKDIR /build
COPY apps/web/package*.json ./
RUN npm ci
COPY apps/web/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
COPY requirements-mvp.lock ./
RUN pip install --no-cache-dir -r requirements-mvp.lock
COPY apps/api ./apps/api
COPY apps/__init__.py ./apps/__init__.py
COPY packages ./packages
COPY services ./services
COPY hardware ./hardware
COPY scripts ./scripts
COPY --from=web /build/dist ./apps/web/dist
RUN useradd --create-home --uid 10001 ssscanner
USER ssscanner
EXPOSE 8000
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
