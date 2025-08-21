# Installation Guide

## Prerequisites

### System Requirements

- **Operating System**: Linux, macOS, or Windows with WSL2
- **Python**: 3.8 or higher
- **Node.js**: 18.x or higher (for UI)
- **Docker**: 20.10 or higher
- **Docker Compose**: 2.0 or higher
- **RAM**: Minimum 4GB, recommended 8GB
- **Storage**: 20GB free space for full dataset

### Required Software

```bash
# Check Python version
python --version  # Should be 3.8+

# Check Node.js version
node --version  # Should be 18.x+

# Check Docker version
docker --version  # Should be 20.10+

# Check Docker Compose version
docker-compose --version  # Should be 2.0+
```

## Quick Start with Docker

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/renec-harvester.git
cd renec-harvester
```

### 2. Start Services with Docker Compose

```bash
# Start all services (PostgreSQL, Redis, API, UI)
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### 3. Access the Applications

- **Web UI**: http://localhost:3001
- **API Documentation**: http://localhost:8000/docs
- **Grafana**: http://localhost:3000 (admin/admin)
- **pgAdmin**: http://localhost:5050 (admin@renec.local/renec_pgadmin_pass)

## Manual Installation

### 1. Database Setup

#### PostgreSQL

```bash
# Install PostgreSQL 14+
# Ubuntu/Debian
sudo apt-get install postgresql-14 postgresql-contrib

# macOS
brew install postgresql@14

# Create database and user
sudo -u postgres psql
```

```sql
CREATE DATABASE renec_harvester;
CREATE USER renec WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE renec_harvester TO renec;
```

#### Redis

```bash
# Install Redis
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Start Redis
redis-server
```

### 2. Python Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Linux/macOS
source venv/bin/activate
# Windows
venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development

# Install Playwright browsers
playwright install --with-deps
```

### 3. Database Migrations

```bash
# Set database URL
export DATABASE_URL="postgresql://renec:your_password@localhost/renec_harvester"

# Initialize Alembic
alembic init alembic

# Run migrations
alembic upgrade head
```

### 4. Environment Configuration

Create a `.env` file in the project root:

```bash
# Database
DATABASE_URL=postgresql://renec:your_password@localhost/renec_harvester
DATABASE_POOL_SIZE=20
DATABASE_POOL_TIMEOUT=30

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=your_redis_password  # Optional

# API
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Spider Settings
CONCURRENT_REQUESTS=10
DOWNLOAD_DELAY=0.5
AUTOTHROTTLE_ENABLED=true
AUTOTHROTTLE_TARGET_CONCURRENCY=5.0

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ADMIN_PASSWORD=your_grafana_password

# Export Settings
EXPORT_PATH=/path/to/artifacts
S3_BUCKET=your-s3-bucket  # Optional
AWS_ACCESS_KEY_ID=your_key  # Optional
AWS_SECRET_ACCESS_KEY=your_secret  # Optional
```

### 5. UI Installation

```bash
# Navigate to UI directory
cd ui

# Install dependencies
npm install

# Build for production
npm run build

# Start development server
npm run dev
```

## Production Installation

### 1. Using Kubernetes

```bash
# Create namespace
kubectl create namespace renec-harvester

# Apply configurations
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml

# Deploy services
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/api.yaml
kubectl apply -f k8s/ui.yaml
kubectl apply -f k8s/scheduler.yaml

# Deploy monitoring
kubectl apply -f k8s/monitoring/

# Apply ingress
kubectl apply -f k8s/ingress.yaml
```

### 2. Using Terraform (AWS)

```bash
# Navigate to terraform directory
cd terraform

# Initialize Terraform
terraform init

# Review plan
terraform plan

# Apply infrastructure
terraform apply

# Get outputs
terraform output
```

### 3. Systemd Service (Linux)

```bash
# Copy service file
sudo cp deploy/systemd/renec-harvester.service /etc/systemd/system/

# Edit service file with your paths
sudo nano /etc/systemd/system/renec-harvester.service

# Enable and start service
sudo systemctl enable renec-harvester
sudo systemctl start renec-harvester

# Check status
sudo systemctl status renec-harvester
```

## Verification

### 1. Test Database Connection

```bash
# Test PostgreSQL connection
python -c "from src.models.base import get_session; session = get_session(); print('Database connected!')"

# Test Redis connection
python -c "import redis; r = redis.from_url('redis://localhost:6379'); r.ping(); print('Redis connected!')"
```

### 2. Run Health Checks

```bash
# API health check
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "database": "connected", "redis": "connected"}
```

### 3. Run Test Spider

```bash
# Run simple test spider
scrapy crawl simple -s LOG_LEVEL=INFO

# Run RENEC test (limited)
python -m src.cli crawl --max-depth 1 --dry-run
```

### 4. Verify UI

```bash
# Check UI build
cd ui && npm run build

# Start UI server
npm run start

# Access at http://localhost:3001
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Error

```bash
# Error: psycopg2.OperationalError: FATAL: password authentication failed

# Solution:
# 1. Check DATABASE_URL format
# 2. Verify PostgreSQL is running
# 3. Check pg_hba.conf for authentication method
```

#### 2. Redis Connection Error

```bash
# Error: redis.exceptions.ConnectionError: Error -2 connecting to localhost:6379

# Solution:
# 1. Verify Redis is running: redis-cli ping
# 2. Check Redis configuration in redis.conf
# 3. Ensure Redis is not password protected or update REDIS_URL
```

#### 3. Playwright Installation Issues

```bash
# Error: Playwright host validation failed

# Solution:
# 1. Install system dependencies
playwright install-deps

# 2. For Docker, use playwright image
FROM mcr.microsoft.com/playwright/python:v1.40.0
```

#### 4. Permission Errors

```bash
# Error: Permission denied accessing /artifacts

# Solution:
# 1. Create directories with proper permissions
mkdir -p artifacts/{crawl_maps,harvests,exports,logs}
chmod -R 755 artifacts/

# 2. Check user permissions
```

### Debug Mode

Enable debug logging for troubleshooting:

```bash
# Set debug environment
export LOG_LEVEL=DEBUG
export SCRAPY_DEBUG=1

# Run with debug
python -m src.cli crawl --debug
```

## Next Steps

1. **Configure the system**: Review and adjust settings in `.env`
2. **Run initial crawl**: `python -m src.cli crawl`
3. **Start harvesting**: `python -m src.cli harvest`
4. **Access the UI**: Navigate to http://localhost:3001
5. **Setup monitoring**: Configure Grafana dashboards

For production deployments, see the [Operations Guide](./operations.md).