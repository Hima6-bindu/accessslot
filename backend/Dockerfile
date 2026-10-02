# =============================================================================
# AccessSlot Backend — Production Dockerfile
# Base: python:3.11-slim
# Server: gunicorn
# =============================================================================

FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies required by psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Install Python dependencies first (layer cache optimisation)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Create staticfiles directory and collect static assets at build time.
# Requires SECRET_KEY to be present — use a dummy value for this step only.
RUN SECRET_KEY=build-time-placeholder-not-used-in-production \
    DEBUG=False \
    DB_NAME=placeholder \
    DB_USER=placeholder \
    DB_PASSWORD=placeholder \
    python manage.py collectstatic --noinput

# Set ownership to non-root user
RUN chown -R appuser:appgroup /app

USER appuser

# Expose the application port
EXPOSE 8000

# Entrypoint: run migrations then start gunicorn.
# PORT env var is provided by Render (defaults to 8000 locally).
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn accessslot.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 60 --access-logfile - --error-logfile -"]
