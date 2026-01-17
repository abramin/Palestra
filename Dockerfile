# Dockerfile for a Django app with Postgres/Redis.
# Multi-stage build keeps the final image slim by separating build and runtime.

# Base image shared by builder and runtime stages.
FROM python:3.14-slim AS base

# Runtime defaults for Python and Django settings.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=palestra.settings.production

# App working directory inside the container.
WORKDIR /app

# Builder stage installs build tooling and builds wheels.
FROM base AS builder

# Build deps for compiling Python packages (e.g., psycopg).
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency list and build wheels for faster, cached installs.
COPY requirements.txt /app/
RUN python -m pip install --upgrade pip \
    && python -m pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Runtime stage keeps only minimal OS deps and installs prebuilt wheels.
FROM base AS runtime

# Runtime-only system libs (Postgres client).
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps from wheels built in the builder stage.
COPY --from=builder /wheels /wheels
COPY requirements.txt /app/
RUN python -m pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt

# Copy application code and collect static assets.
COPY . /app/
RUN python manage.py collectstatic --noinput

# Create a non-root user and drop privileges.
RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser

# Expose the application port.
EXPOSE 8000

# Start the app with Gunicorn.
CMD ["gunicorn", "palestra.wsgi:application", "--bind", "0.0.0.0:8000"]
