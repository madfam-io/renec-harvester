# RENEC Harvester Setup Guide

## Overview

RENEC Harvester is a comprehensive web scraping solution for México's RENEC (National Registry of Competency Standards) platform. This guide covers the complete setup process, including recent fixes for common issues.

## Prerequisites

- **macOS** (tested on Sonoma 15.6) or Linux
- **Python 3.9+** 
- **Node.js v24+** (v24.6.0 recommended)
- **Docker** and **Docker Compose**
- **Homebrew** (for macOS users)
- **Git**

## Quick Start

```bash
# Clone the repository
git clone https://github.com/madfam-io/renec-harvester.git
cd renec-harvester

# Install Python dependencies
pip3 install -r requirements.txt

# Start Docker services
docker-compose up -d

# Install and start the UI
cd ui
npm install
npm run dev
```

## Detailed Setup Instructions

### 1. Environment Setup

#### Python Environment

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development

# Install Playwright browsers (for web scraping)
playwright install --with-deps
```

#### Node.js Setup

If you encounter Node.js issues (e.g., ICU library errors):

```bash
# Reinstall Node.js via Homebrew
brew uninstall node
brew install node

# Verify installation
node --version  # Should show v24.6.0 or higher
npm --version   # Should show v11.5.1 or higher
```

### 2. Docker Services

The project uses several Docker services:

```bash
# Start all services
docker-compose up -d

# Verify services are running
docker ps

# Services include:
# - PostgreSQL (port 5432)
# - Redis (port 6379)
# - Prometheus (port 9090)
# - Grafana (port 3000)
# - pgAdmin (port 5050)
# - Flower (port 5555)
# - Redis Commander (port 8081)
```

#### Service Credentials

- **PostgreSQL**: `renec` / `renec_db_pass`
- **Grafana**: `admin` / `renec_grafana_pass`
- **pgAdmin**: `admin@renec.local` / `renec_pgadmin_pass`
- **Flower**: `admin` / `renec_flower_pass`

### 3. Database Initialization

```bash
# Set Python path
export PYTHONPATH=.

# Initialize database schema
python -m src.cli db init
python -m src.cli db migrate
```

### 4. Frontend Setup

```bash
# Navigate to UI directory
cd ui

# Install dependencies
npm install

# Start development server
npm run dev

# Access at http://localhost:3001
```

### 5. Backend API

```bash
# Start FastAPI backend
python -m src.api.main

# Access API docs at http://localhost:8000/docs
```

### 6. Complete Startup Script

Use the provided startup script for both frontend and backend:

```bash
./start-ui.sh

# This starts:
# - FastAPI backend on port 8000
# - Next.js frontend on port 3001
```

## Common Issues and Solutions

### Issue 1: React Hydration Errors

**Symptom**: Console shows hydration mismatch errors with VS Code browser extension styles.

**Solution**: The project includes automatic fixes:
- `ExtensionCleanup` component removes injected styles
- `suppressHydrationWarning` attributes prevent React warnings
- CSS rules block extension style injection

### Issue 2: Node.js ICU Library Error

**Symptom**: 
```
dyld[]: Library not loaded: /usr/local/opt/icu4c/lib/libicui18n.73.dylib
```

**Solution**:
```bash
# Reinstall Node.js
brew uninstall node
brew install node
```

### Issue 3: Port Conflicts

**Symptom**: Docker services fail to start due to port conflicts.

**Solution**:
```bash
# Stop conflicting services
docker stop $(docker ps -q)

# Or kill specific port
lsof -ti:6379 | xargs kill -9  # For Redis
lsof -ti:5432 | xargs kill -9  # For PostgreSQL
```

### Issue 4: Frontend 404 Errors

**Symptom**: Next.js shows 404 for `/en` routes.

**Solution**: Ensure you're accessing the correct URL:
- Use `http://localhost:3001` (not `/en`)
- Check that `src/app/page.tsx` exists

## Testing the Setup

### 1. Test Python Environment

```bash
# Run the test script
PYTHONPATH=. python3 scripts/test_local_setup.py

# Expected output: 7/7 tests passed
```

### 2. Test Scrapy Spider

```bash
# Test simple spider
PYTHONPATH=. python3 -m scrapy crawl simple -L INFO

# Test RENEC spider (crawl mode)
PYTHONPATH=. python3 -m scrapy crawl renec -a mode=crawl -L INFO
```

### 3. Test Frontend

1. Navigate to http://localhost:3001
2. You should see the RENEC Harvester interface with three tabs:
   - Scraping Controls
   - Monitoring
   - Data Explorer

### 4. Test API

1. Navigate to http://localhost:8000/docs
2. You should see the FastAPI Swagger documentation

## Project Structure

```
renec-harvester/
├── src/                    # Backend source code
│   ├── api/               # FastAPI application
│   ├── discovery/         # Scrapy spiders
│   ├── models/           # Database models
│   └── cli/              # CLI commands
├── ui/                    # Frontend Next.js app
│   ├── src/
│   │   ├── app/          # Next.js app directory
│   │   ├── components/   # React components
│   │   └── utils/        # Utility functions
│   └── public/           # Static assets
├── docker-compose.yml     # Docker services
├── requirements.txt       # Python dependencies
└── start-ui.sh           # Startup script
```

## Development Workflow

### Running Scrapers

```bash
# Crawl mode - Map site structure
PYTHONPATH=. python3 -m scrapy crawl renec -a mode=crawl

# Harvest mode - Extract data
PYTHONPATH=. python3 -m scrapy crawl renec -a mode=harvest

# With specific settings
PYTHONPATH=. python3 -m scrapy crawl renec \
  -s CONCURRENT_REQUESTS=10 \
  -s DOWNLOAD_DELAY=0.5
```

### Database Operations

```bash
# Connect to PostgreSQL
docker exec -it renec-postgres psql -U renec -d renec_harvester

# View tables
\dt

# Run migrations
alembic upgrade head
```

### Running Tests

```bash
# Run all tests
PYTHONPATH=. pytest

# Run with coverage
PYTHONPATH=. pytest --cov=src --cov-report=html

# Run specific test file
PYTHONPATH=. pytest tests/unit/test_spider.py -v
```

## Monitoring and Debugging

### Service URLs

- **Frontend**: http://localhost:3001
- **API Docs**: http://localhost:8000/docs
- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090
- **pgAdmin**: http://localhost:5050
- **Flower**: http://localhost:5555
- **Redis Commander**: http://localhost:8081

### Logs

```bash
# View Docker logs
docker-compose logs -f

# View specific service
docker-compose logs -f postgres
docker-compose logs -f redis

# Frontend logs (in terminal running npm run dev)
# Backend logs (in terminal running FastAPI)
```

### Debugging Tips

1. **Check service health**:
   ```bash
   docker-compose ps
   ```

2. **Verify Python path**:
   ```bash
   echo $PYTHONPATH  # Should show .
   ```

3. **Test database connection**:
   ```bash
   PYTHONPATH=. python3 -c "from src.models import Base; print('DB models loaded successfully')"
   ```

4. **Clear cache if needed**:
   ```bash
   rm -rf ui/.next
   rm -rf artifacts/httpcache
   ```

## Next Steps

1. **Configure scraping parameters** in `src/discovery/settings.py`
2. **Set up scheduled harvests** using the scheduler
3. **Customize the UI** for your specific needs
4. **Deploy to production** using Kubernetes manifests in `k8s/`

## Support

For issues or questions:
- Check the [troubleshooting guide](./troubleshooting.md)
- Review recent commits for fixes
- Open an issue on GitHub

---

*Last updated: August 21, 2025*
*Version: 0.2.0*