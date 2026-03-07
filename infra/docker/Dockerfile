# Multi-stage build for production optimization
FROM python:3.13-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv==0.4.24

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock README.md ./

# Install dependencies
RUN uv pip install --system .

# Development stage
FROM base AS development

# Copy source code
COPY . .

# Create app user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/src/staticfiles /app/src/media && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app/src/staticfiles && \
    chmod -R 775 /app/src/media

USER appuser

EXPOSE 8000

# Development command with auto-reload
CMD ["sh", "-c", "python src/manage.py migrate && python src/manage.py create_minio_bucket && python src/manage.py runserver 0.0.0.0:8000"]

# Production stage
FROM base AS production

# Copy source code
COPY . .

# Create app user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/src/staticfiles /app/src/media && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app/src/staticfiles && \
    chmod -R 775 /app/src/media

USER appuser

EXPOSE 8000

# Collect static files
RUN python src/manage.py collectstatic --noinput

# Production command with migrations and gunicorn
CMD ["sh", "-c", "python src/manage.py migrate && python src/manage.py create_minio_bucket && gunicorn --bind 0.0.0.0:8000 --workers 3 config.wsgi:application"]
