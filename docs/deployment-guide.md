# RENEC Harvester Deployment Guide

## 🚀 Overview

This guide covers deployment strategies for the RENEC Harvester system across different environments, from local development to production deployments.

## 📋 Prerequisites

### System Requirements
- **Operating System**: Linux (Ubuntu 20.04+), macOS 10.15+, or Windows 10+
- **Python**: 3.9+ (3.11+ recommended)
- **Node.js**: 18.0+ (for web interface)
- **Memory**: 4GB minimum, 8GB+ recommended
- **Storage**: 20GB minimum, 100GB+ for production
- **Network**: Stable internet connection for crawling

### Required Software
```bash
# System packages (Ubuntu/Debian)
sudo apt update && sudo apt install -y \
  python3.11 python3.11-venv python3-pip \
  nodejs npm \
  postgresql-client \
  redis-tools \
  curl wget git

# macOS (with Homebrew)
brew install python@3.11 node postgresql redis git

# Docker (all platforms)
# Install Docker Desktop or Docker Engine
```

## 🏠 Local Development Deployment

### Quick Start
```bash
# Clone repository
git clone https://github.com/your-org/renec-harvester.git
cd renec-harvester

# Setup Python environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install --with-deps

# Start services
docker-compose up -d

# Initialize database
python -m src.cli db init
python -m src.cli db migrate

# Setup web interface
cd ui
npm install --legacy-peer-deps
cd ..

# Start complete system
./start-ui.sh
```

### Development Configuration

Create `.env` file:
```bash
# Database
DATABASE_URL=postgresql://renec:renec_secure_pass@localhost:5432/renec_harvester
REDIS_URL=redis://:renec_redis_pass@localhost:6379/0

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# UI
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Logging
LOG_LEVEL=DEBUG
LOG_FILE=./logs/harvester.log
```

### Service Endpoints
- **Web Interface**: http://localhost:3001
- **API Documentation**: http://localhost:8000/docs
- **Grafana**: http://localhost:3000 (admin/renec_grafana_pass)
- **Prometheus**: http://localhost:9090
- **Database**: localhost:5432
- **Redis**: localhost:6379

## 🐳 Docker Deployment

### Single Container Deployment

**Build and run harvester:**
```bash
# Build image
docker build -t renec-harvester:latest .

# Run with volume mounts
mkdir -p ./artifacts ./logs
docker run -d \
  --name renec-harvester \
  -p 8000:8000 \
  -v $(pwd)/artifacts:/app/artifacts \
  -v $(pwd)/logs:/app/logs \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e REDIS_URL=redis://host:6379/0 \
  renec-harvester:latest
```

### Multi-Container Deployment (docker-compose)

**Production docker-compose.yml:**
```yaml
version: '3.8'

services:
  harvester-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://renec:${POSTGRES_PASSWORD}@postgres:5432/renec_harvester
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - LOG_LEVEL=INFO
    volumes:
      - ./artifacts:/app/artifacts
      - ./logs:/app/logs
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  harvester-ui:
    build: ./ui
    ports:
      - "3001:3001"
    environment:
      - NEXT_PUBLIC_API_BASE_URL=http://harvester-api:8000
    depends_on:
      - harvester-api
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_DB=renec_harvester
      - POSTGRES_USER=renec
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U renec -d renec_harvester"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./config/nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
    depends_on:
      - harvester-api
      - harvester-ui
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

**Environment file (.env):**
```bash
POSTGRES_PASSWORD=your_secure_postgres_password
REDIS_PASSWORD=your_secure_redis_password
DOMAIN_NAME=harvester.yourdomain.com
SSL_CERT_PATH=./ssl/cert.pem
SSL_KEY_PATH=./ssl/key.pem
```

**Deploy:**
```bash
# Generate secure passwords
export POSTGRES_PASSWORD=$(openssl rand -base64 32)
export REDIS_PASSWORD=$(openssl rand -base64 32)

# Start services
docker-compose up -d

# Initialize database
docker-compose exec harvester-api python -m src.cli db init
docker-compose exec harvester-api python -m src.cli db migrate

# Check status
docker-compose ps
docker-compose logs harvester-api
```

## ☁️ Cloud Deployment

### AWS Deployment

**Using ECS (Elastic Container Service):**

1. **Setup ECS Cluster:**
```bash
# Create cluster
aws ecs create-cluster --cluster-name renec-harvester

# Create task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

2. **Task Definition (task-definition.json):**
```json
{
  "family": "renec-harvester",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "harvester-api",
      "image": "your-account.dkr.ecr.region.amazonaws.com/renec-harvester:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://user:pass@rds-endpoint:5432/renec_harvester"
        },
        {
          "name": "REDIS_URL", 
          "value": "redis://elasticache-endpoint:6379/0"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/renec-harvester",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

3. **Infrastructure as Code (CloudFormation/Terraform):**
```yaml
# cloudformation-template.yaml
Resources:
  RDSInstance:
    Type: AWS::RDS::DBInstance
    Properties:
      DBInstanceClass: db.t3.medium
      Engine: postgres
      DBName: renec_harvester
      
  ElastiCacheCluster:
    Type: AWS::ElastiCache::CacheCluster
    Properties:
      CacheNodeType: cache.t3.micro
      Engine: redis
      
  LoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Type: application
      Scheme: internet-facing
```

### Google Cloud Platform (GCP)

**Using Google Cloud Run:**
```bash
# Build and push image
docker build -t gcr.io/PROJECT_ID/renec-harvester:latest .
docker push gcr.io/PROJECT_ID/renec-harvester:latest

# Deploy to Cloud Run
gcloud run deploy renec-harvester \
  --image gcr.io/PROJECT_ID/renec-harvester:latest \
  --platform managed \
  --region us-central1 \
  --set-env-vars DATABASE_URL=$DATABASE_URL,REDIS_URL=$REDIS_URL \
  --memory 2Gi \
  --cpu 1 \
  --max-instances 10
```

### Azure Deployment

**Using Azure Container Instances:**
```bash
# Create resource group
az group create --name renec-harvester-rg --location eastus

# Deploy container
az container create \
  --resource-group renec-harvester-rg \
  --name renec-harvester \
  --image your-registry/renec-harvester:latest \
  --cpu 1 --memory 2 \
  --ports 8000 \
  --environment-variables \
    DATABASE_URL=$DATABASE_URL \
    REDIS_URL=$REDIS_URL
```

## 🏢 Production Deployment

### Prerequisites
- SSL certificates (Let's Encrypt recommended)
- Domain name configuration
- Firewall and security group setup
- Monitoring and alerting systems
- Backup strategy

### Production Configuration

**Environment Variables:**
```bash
# Security
SECRET_KEY=your-super-secret-key
ALLOWED_HOSTS=harvester.yourdomain.com,api.yourdomain.com
CORS_ALLOWED_ORIGINS=https://harvester.yourdomain.com

# Database (managed service recommended)
DATABASE_URL=postgresql://user:pass@prod-db-host:5432/renec_harvester

# Redis (managed service recommended)
REDIS_URL=redis://prod-redis-host:6379/0

# Logging
LOG_LEVEL=INFO
SENTRY_DSN=https://your-sentry-dsn

# Performance
CONCURRENT_REQUESTS=16
WORKER_PROCESSES=4
MAX_CONNECTIONS=100

# Monitoring
PROMETHEUS_ENABLED=true
METRICS_PORT=9090
```

### Nginx Configuration

**nginx.conf:**
```nginx
upstream harvester_api {
    server harvester-api-1:8000;
    server harvester-api-2:8000;
    server harvester-api-3:8000;
}

upstream harvester_ui {
    server harvester-ui-1:3001;
    server harvester-ui-2:3001;
}

server {
    listen 80;
    server_name harvester.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name harvester.yourdomain.com;
    
    ssl_certificate /etc/ssl/certs/harvester.crt;
    ssl_certificate_key /etc/ssl/private/harvester.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    
    location / {
        proxy_pass http://harvester_ui;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /api/ {
        proxy_pass http://harvester_api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # API-specific settings
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
        client_max_body_size 10M;
    }
    
    location /metrics {
        proxy_pass http://harvester_api/metrics;
        allow 10.0.0.0/8;  # Allow monitoring network
        deny all;
    }
}
```

### Health Checks and Monitoring

**Health Check Script (healthcheck.sh):**
```bash
#!/bin/bash
# Health check script for load balancer

API_URL="http://localhost:8000/health"
UI_URL="http://localhost:3001"

# Check API health
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $API_URL)
if [ "$API_STATUS" != "200" ]; then
    echo "API health check failed: $API_STATUS"
    exit 1
fi

# Check UI health
UI_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $UI_URL)
if [ "$UI_STATUS" != "200" ]; then
    echo "UI health check failed: $UI_STATUS"
    exit 1
fi

echo "All services healthy"
exit 0
```

### Database Migration Strategy

**Zero-downtime migration process:**
```bash
#!/bin/bash
# production-deploy.sh

set -e

echo "Starting production deployment..."

# 1. Run database migrations (non-breaking changes only)
python -m src.cli db migrate --dry-run
read -p "Apply migrations? (y/n) " -n 1 -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python -m src.cli db migrate
fi

# 2. Build and tag new image
docker build -t renec-harvester:$VERSION .
docker tag renec-harvester:$VERSION renec-harvester:latest

# 3. Rolling deployment
docker-compose up -d --scale harvester-api=3 --no-recreate
sleep 30

# 4. Health check
if ./healthcheck.sh; then
    echo "Deployment successful"
    docker-compose ps
else
    echo "Health check failed, rolling back"
    docker-compose up -d --scale harvester-api=2
    exit 1
fi

# 5. Cleanup old images
docker image prune -f

echo "Deployment complete"
```

## 🔧 Configuration Management

### Environment-Specific Configuration

**config/production.yaml:**
```yaml
database:
  url: ${DATABASE_URL}
  pool_size: 20
  pool_timeout: 30
  pool_recycle: 3600

redis:
  url: ${REDIS_URL}
  connection_pool_size: 20
  socket_timeout: 5

spider:
  concurrent_requests: 16
  download_delay: 0.3
  retry_times: 5
  timeout: 60

api:
  host: 0.0.0.0
  port: 8000
  workers: 4
  max_connections: 1000

logging:
  level: INFO
  format: json
  file: /app/logs/harvester.log
  max_size: 100MB
  backup_count: 5

monitoring:
  prometheus_enabled: true
  metrics_port: 9090
  health_check_interval: 30
```

### Secrets Management

**Using Docker Secrets:**
```yaml
# docker-compose.yml
secrets:
  db_password:
    file: ./secrets/db_password.txt
  redis_password:
    file: ./secrets/redis_password.txt
    
services:
  harvester-api:
    secrets:
      - db_password
      - redis_password
    environment:
      - DATABASE_PASSWORD_FILE=/run/secrets/db_password
      - REDIS_PASSWORD_FILE=/run/secrets/redis_password
```

**Using HashiCorp Vault:**
```bash
# Fetch secrets from Vault
export DATABASE_PASSWORD=$(vault kv get -field=password secret/renec/db)
export REDIS_PASSWORD=$(vault kv get -field=password secret/renec/redis)
```

## 📊 Monitoring and Alerting

### Prometheus Configuration

**prometheus.yml:**
```yaml
global:
  scrape_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'renec-harvester'
    static_configs:
      - targets: ['harvester-api:9090']
    scrape_interval: 10s
    
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
      
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
```

**Alert Rules (alert_rules.yml):**
```yaml
groups:
  - name: renec-harvester
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        annotations:
          summary: "High error rate detected"
          
      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 2m
        annotations:
          summary: "PostgreSQL database is down"
          
      - alert: LowDiskSpace
        expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.1
        for: 5m
        annotations:
          summary: "Low disk space (< 10% available)"
```

## 🔒 Security Considerations

### Network Security
```bash
# Firewall rules (iptables)
# Allow HTTP/HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow SSH (specific IP)
iptables -A INPUT -p tcp -s YOUR_IP --dport 22 -j ACCEPT

# Block direct access to internal services
iptables -A INPUT -p tcp --dport 5432 -s 10.0.0.0/8 -j ACCEPT
iptables -A INPUT -p tcp --dport 6379 -s 10.0.0.0/8 -j ACCEPT
iptables -A INPUT -p tcp --dport 5432 -j DROP
iptables -A INPUT -p tcp --dport 6379 -j DROP
```

### SSL/TLS Configuration
```bash
# Generate SSL certificate with Let's Encrypt
certbot --nginx -d harvester.yourdomain.com

# Auto-renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
```

### Application Security
- Use environment variables for secrets
- Implement rate limiting
- Enable CORS only for trusted domains
- Regular security updates
- Database connection encryption
- API authentication and authorization

## 🔄 Backup and Disaster Recovery

### Automated Backup Script
```bash
#!/bin/bash
# backup.sh

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Database backup
pg_dump $DATABASE_URL | gzip > "$BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz"

# Redis backup  
redis-cli --rdb "$BACKUP_DIR/redis_backup_$TIMESTAMP.rdb"

# Application data
tar -czf "$BACKUP_DIR/artifacts_backup_$TIMESTAMP.tar.gz" ./artifacts

# Upload to cloud storage (AWS S3 example)
aws s3 cp "$BACKUP_DIR/" s3://renec-harvester-backups/ --recursive

# Cleanup old backups (keep 30 days)
find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete
find "$BACKUP_DIR" -name "*.rdb" -mtime +30 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
```

### Disaster Recovery Procedure
1. **Provision new infrastructure**
2. **Restore database from latest backup**
3. **Restore Redis data**
4. **Deploy application containers**
5. **Verify system functionality**
6. **Update DNS records**
7. **Monitor for issues**

This deployment guide provides comprehensive coverage for deploying the RENEC Harvester system across various environments and scales.