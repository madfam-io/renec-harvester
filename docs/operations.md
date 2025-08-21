# Operations Guide

## Overview

This guide covers operational aspects of running and maintaining the RENEC Harvester in production environments.

## Deployment

### Production Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Load Balancer │────▶│   API Servers   │────▶│   PostgreSQL    │
│   (NGINX/ALB)   │     │   (3 instances) │     │   (Primary)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                │                         │
                                │                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   CDN           │────▶│   UI Servers    │     │   PostgreSQL    │
│   (CloudFront)  │     │   (2 instances) │     │   (Replica)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                │
                                ▼
                        ┌─────────────────┐
                        │   Redis Cluster  │
                        │   (3 nodes)      │
                        └─────────────────┘
```

### Deployment Checklist

- [ ] Database migrations completed
- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Monitoring configured
- [ ] Backup procedures tested
- [ ] Load balancer health checks
- [ ] Auto-scaling policies set
- [ ] Security groups configured
- [ ] Logging aggregation setup
- [ ] Alerting rules defined

### Environment Configuration

#### Production Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@db.example.com:5432/renec_prod
DATABASE_POOL_SIZE=50
DATABASE_POOL_TIMEOUT=30
DATABASE_ECHO=false

# Redis
REDIS_URL=redis://redis.example.com:6379/0
REDIS_PASSWORD=secure_password
REDIS_MAX_CONNECTIONS=100

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_LOG_LEVEL=INFO
CORS_ORIGINS=https://app.example.com

# Spider Configuration
CONCURRENT_REQUESTS=16
DOWNLOAD_DELAY=0.5
AUTOTHROTTLE_ENABLED=true
AUTOTHROTTLE_TARGET_CONCURRENCY=8.0
ROBOTSTXT_OBEY=true

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_URL=https://grafana.example.com
SENTRY_DSN=https://xxx@sentry.io/yyy

# AWS (if applicable)
AWS_REGION=us-west-2
S3_BUCKET=renec-harvester-artifacts
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=yyy
```

## Monitoring

### Key Metrics to Monitor

#### System Metrics
- **CPU Usage**: Target < 70% average
- **Memory Usage**: Target < 80%
- **Disk Usage**: Alert at 85%
- **Network I/O**: Monitor for anomalies

#### Application Metrics
- **API Response Time**: Target p95 < 100ms
- **API Error Rate**: Target < 0.1%
- **Spider Success Rate**: Target > 95%
- **Database Connection Pool**: Monitor saturation
- **Redis Hit Rate**: Target > 90%

#### Business Metrics
- **Items Harvested/Hour**: Track against baseline
- **Data Freshness**: Max age of data points
- **Coverage Percentage**: Completeness of harvest
- **Error Types**: Classification of failures

### Grafana Dashboards

#### System Overview Dashboard
```json
{
  "dashboard": {
    "title": "RENEC Harvester Overview",
    "panels": [
      {
        "title": "API Response Time",
        "targets": [{
          "expr": "histogram_quantile(0.95, api_response_duration_bucket)"
        }]
      },
      {
        "title": "Spider Success Rate",
        "targets": [{
          "expr": "rate(spider_items_scraped_total[5m]) / rate(spider_requests_total[5m])"
        }]
      }
    ]
  }
}
```

### Prometheus Alerts

```yaml
# prometheus/alerts.yml
groups:
  - name: renec_harvester
    rules:
      - alert: HighAPIErrorRate
        expr: rate(api_errors_total[5m]) > 0.05
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High API error rate"
          description: "API error rate is {{ $value }} errors/sec"
      
      - alert: SpiderStalled
        expr: rate(spider_items_scraped_total[10m]) == 0
        for: 20m
        labels:
          severity: critical
        annotations:
          summary: "Spider has stalled"
          description: "No items scraped in the last 20 minutes"
      
      - alert: DatabaseConnectionPoolExhausted
        expr: db_connection_pool_available == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Database connection pool exhausted"
```

## Maintenance

### Regular Maintenance Tasks

#### Daily
- [ ] Check system health dashboard
- [ ] Review error logs
- [ ] Verify backup completion
- [ ] Check data freshness

#### Weekly
- [ ] Review performance metrics
- [ ] Clean up old logs
- [ ] Update spider statistics
- [ ] Review security logs

#### Monthly
- [ ] Database maintenance (VACUUM, ANALYZE)
- [ ] Update dependencies
- [ ] Review and optimize queries
- [ ] Capacity planning review

### Database Maintenance

#### PostgreSQL Optimization

```sql
-- Vacuum and analyze tables
VACUUM ANALYZE ec_standards_v2;
VACUUM ANALYZE certificadores_v2;
VACUUM ANALYZE centros;

-- Update table statistics
ANALYZE;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan < 100
ORDER BY idx_scan;

-- Find slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
WHERE mean_exec_time > 100
ORDER BY mean_exec_time DESC
LIMIT 10;
```

#### Redis Maintenance

```bash
# Monitor memory usage
redis-cli INFO memory

# Check for memory fragmentation
redis-cli MEMORY STATS

# Clear expired keys
redis-cli --scan --pattern "*" | xargs -L 1000 redis-cli DEL

# Backup Redis data
redis-cli BGSAVE
```

### Backup Procedures

#### Database Backup

```bash
#!/bin/bash
# backup-database.sh

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="renec_backup_${TIMESTAMP}.sql"

# Create backup
pg_dump $DATABASE_URL > $BACKUP_FILE

# Compress
gzip $BACKUP_FILE

# Upload to S3
aws s3 cp ${BACKUP_FILE}.gz s3://${S3_BUCKET}/backups/

# Clean up old backups (keep 30 days)
find /backups -name "*.gz" -mtime +30 -delete
```

#### Application Data Backup

```bash
#!/bin/bash
# backup-artifacts.sh

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="artifacts_backup_${TIMESTAMP}"

# Create backup directory
mkdir -p $BACKUP_DIR

# Copy artifacts
cp -r artifacts/* $BACKUP_DIR/

# Create tarball
tar -czf ${BACKUP_DIR}.tar.gz $BACKUP_DIR

# Upload to S3
aws s3 cp ${BACKUP_DIR}.tar.gz s3://${S3_BUCKET}/artifacts/

# Clean up
rm -rf $BACKUP_DIR ${BACKUP_DIR}.tar.gz
```

### Disaster Recovery

#### Recovery Time Objectives
- **RTO (Recovery Time Objective)**: 4 hours
- **RPO (Recovery Point Objective)**: 24 hours

#### Recovery Procedures

1. **Database Recovery**
```bash
# Download latest backup
aws s3 cp s3://${S3_BUCKET}/backups/latest.sql.gz .

# Decompress
gunzip latest.sql.gz

# Restore database
psql $DATABASE_URL < latest.sql
```

2. **Application Recovery**
```bash
# Deploy from container registry
kubectl set image deployment/api api=registry/renec-harvester:stable

# Verify deployment
kubectl rollout status deployment/api
```

## Scaling

### Horizontal Scaling

#### API Servers
```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

#### Database Scaling
- Add read replicas for query distribution
- Use connection pooling (PgBouncer)
- Implement database sharding if needed

### Vertical Scaling

#### Resource Recommendations
- **API Servers**: 2 vCPU, 4GB RAM minimum
- **Spider Workers**: 4 vCPU, 8GB RAM
- **Database**: 8 vCPU, 32GB RAM, SSD storage
- **Redis**: 4 vCPU, 16GB RAM

## Security

### Security Checklist

- [ ] SSL/TLS enabled on all endpoints
- [ ] Database connections encrypted
- [ ] Secrets stored in secure vault
- [ ] Regular security updates applied
- [ ] Firewall rules configured
- [ ] Intrusion detection enabled
- [ ] Audit logging enabled
- [ ] Regular security scans

### Access Control

```bash
# Database user permissions
CREATE USER api_user WITH PASSWORD 'secure_password';
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO api_user;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO api_user;

CREATE USER readonly_user WITH PASSWORD 'secure_password';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
```

### Network Security

```yaml
# k8s/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-network-policy
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
```

## Troubleshooting

### Common Issues

#### High Memory Usage
```bash
# Check memory consumers
ps aux --sort=-%mem | head -20

# Check Python memory usage
python -c "import tracemalloc; tracemalloc.start(); # your code"

# Solutions:
# - Increase memory limits
# - Implement pagination
# - Use generators instead of lists
# - Clear caches periodically
```

#### Slow API Response
```bash
# Enable slow query log
ALTER SYSTEM SET log_min_duration_statement = 100;

# Check query performance
EXPLAIN ANALYZE SELECT ...;

# Solutions:
# - Add missing indexes
# - Optimize queries
# - Increase connection pool
# - Enable query caching
```

#### Spider Failures
```python
# Debug spider issues
scrapy crawl renec -s LOG_LEVEL=DEBUG

# Common causes:
# - Rate limiting
# - Changed website structure
# - Network issues
# - Memory exhaustion

# Solutions:
# - Adjust delays
# - Update selectors
# - Implement retries
# - Monitor memory usage
```

### Log Analysis

```bash
# Search for errors
grep ERROR /var/log/renec/*.log | tail -100

# Count errors by type
awk '/ERROR/ {print $5}' /var/log/renec/*.log | sort | uniq -c

# Monitor in real-time
tail -f /var/log/renec/*.log | grep -E "(ERROR|WARNING)"
```

## Performance Tuning

### Database Tuning

```sql
-- PostgreSQL configuration
ALTER SYSTEM SET shared_buffers = '4GB';
ALTER SYSTEM SET work_mem = '16MB';
ALTER SYSTEM SET maintenance_work_mem = '512MB';
ALTER SYSTEM SET effective_cache_size = '12GB';
ALTER SYSTEM SET max_connections = 200;
```

### Redis Tuning

```bash
# Redis configuration
maxmemory 4gb
maxmemory-policy allkeys-lru
tcp-keepalive 60
timeout 300
```

### Application Tuning

```python
# Gunicorn configuration
workers = 4
worker_class = 'uvicorn.workers.UvicornWorker'
worker_connections = 1000
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
```

## Incident Response

### Incident Response Plan

1. **Detection**: Monitoring alerts trigger
2. **Assessment**: Determine severity and impact
3. **Containment**: Isolate affected components
4. **Resolution**: Apply fixes or rollback
5. **Recovery**: Restore normal operation
6. **Post-mortem**: Document and learn

### Runbooks

#### API Outage
1. Check load balancer health
2. Verify API server status
3. Check database connectivity
4. Review recent deployments
5. Rollback if necessary
6. Scale up if needed

#### Data Quality Issues
1. Stop current harvest
2. Identify affected data
3. Review spider logs
4. Fix extraction logic
5. Re-harvest affected items
6. Validate results

## Compliance

### Data Retention

```sql
-- Clean up old data (keep 1 year)
DELETE FROM spider_logs WHERE created_at < NOW() - INTERVAL '1 year';
DELETE FROM api_logs WHERE created_at < NOW() - INTERVAL '90 days';
```

### Audit Logging

```python
# Audit log configuration
AUDIT_LOG_ENABLED = True
AUDIT_LOG_RETENTION_DAYS = 365
AUDIT_LOG_EVENTS = [
    'user_login',
    'data_export',
    'configuration_change',
    'spider_start',
    'spider_stop'
]
```

## Documentation

### Operational Documentation
- Runbooks for common scenarios
- Network diagrams
- Security procedures
- Contact information
- Escalation procedures

### Change Management
- Document all changes
- Test in staging first
- Schedule maintenance windows
- Notify stakeholders
- Have rollback plans

## Support

### Support Tiers

1. **L1 Support**: Basic troubleshooting
2. **L2 Support**: Advanced technical issues
3. **L3 Support**: Development team escalation

### Contact Information
- **On-call**: +1-xxx-xxx-xxxx
- **Email**: ops@example.com
- **Slack**: #renec-harvester-ops
- **PagerDuty**: renec-harvester service