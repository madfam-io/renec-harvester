# Multi-stage Dockerfile for RENEC Harvester
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r harvester && useradd -r -g harvester harvester

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and browsers
RUN playwright install --with-deps chromium

# Development stage
FROM base as development

# Install development dependencies
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy source code
COPY --chown=harvester:harvester . .

# Switch to app user
USER harvester

# Expose ports
EXPOSE 8000 9091

CMD ["python", "-m", "src.cli", "status"]

# Production stage
FROM base as production

# Copy only necessary files
COPY --chown=harvester:harvester src/ ./src/
COPY --chown=harvester:harvester alembic/ ./alembic/
COPY --chown=harvester:harvester alembic.ini scrapy.cfg ./
COPY --chown=harvester:harvester config/ ./config/

# Switch to app user
USER harvester

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from src.utils.health import check_system_health; import sys; sys.exit(0 if all(s['healthy'] for s in check_system_health().values()) else 1)"

# Expose port
EXPOSE 8000

# Default command
CMD ["python", "-m", "src.cli", "harvest", "start"]