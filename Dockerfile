# Multi-stage production image: React SPA + FastAPI on one public URL.
# Platform: Railway (recommended) — one project, one web service + PostgreSQL.

# ---- Frontend build ----
FROM node:22-alpine AS frontend-build
WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
# Empty base URL => same-origin API calls in production (see frontend/src/api/client.ts).
ENV VITE_API_BASE_URL=
RUN npm run build

# ---- Backend runtime ----
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STATIC_DIR=/app/static \
    PORT=8000

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY --from=frontend-build /frontend/dist /app/static

RUN chmod +x /app/scripts/start.sh \
    && sed -i 's/\r$//' /app/scripts/start.sh \
    && useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD curl -fsS "http://127.0.0.1:${PORT:-8000}/health" || exit 1

CMD ["/app/scripts/start.sh"]
