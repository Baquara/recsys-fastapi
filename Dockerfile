# ── Stage: runtime ────────────────────────────────────────────────────────────
FROM python:3.12-slim

# Keeps Python from writing .pyc files and forces stdout/stderr to be unbuffered
# so container logs appear immediately.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# ── Dependencies (own layer — only rebuilt when requirements.txt changes) ──────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Application code ───────────────────────────────────────────────────────────
COPY app/       app/
COPY recommenders/ recommenders/
COPY run.py     .

# Persistent data directory for the SQLite database.
# Mount a named volume here so the DB survives container restarts.
RUN mkdir -p data
VOLUME ["/app/data"]

# ── Non-root user (principle of least privilege) ───────────────────────────────
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser

# ── Runtime configuration ──────────────────────────────────────────────────────
# All values below are defaults; override them at runtime via environment
# variables or a .env file (see .env.example for the full reference).
#
# SECURITY — change these before any non-local deployment:
#   SECRET_KEY                 strong random string  (python -c "import secrets; print(secrets.token_hex(32))")
#   FIRST_SUPERUSER_PASSWORD   strong password
#   DISABLE_SECURITY           leave unset or false  (true = sandbox, never in production)
#   CORS_ORIGINS               comma-separated allowed origins (default * is permissive)
#
ENV DATABASE_URL=sqlite:///./data/db0.db \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000 \
    HARDWARE_BACKEND=none

EXPOSE 8000

# ── Health check ───────────────────────────────────────────────────────────────
# Checks the OpenAPI schema endpoint — lightweight and always available.
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/openapi.json')" \
    || exit 1

# ── Entry point ────────────────────────────────────────────────────────────────
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--no-access-log"]
