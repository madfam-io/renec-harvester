# RENEC Harvester Operations Manual

## Table of Contents

1. [System Overview](#system-overview)
2. [Daily Operations](#daily-operations)
3. [Monitoring](#monitoring)
4. [Troubleshooting](#troubleshooting)
5. [Maintenance](#maintenance)
6. [Disaster Recovery](#disaster-recovery)
7. [Security](#security)
8. [Runbooks](#runbooks)

## System Overview

### Architecture

```
┌─────────────────────────────────────────────────┐
│                Load Balancer                     │
├─────────────────────────────────────────────────┤
│         Kubernetes Cluster (3 nodes)            │
├────────────┬────────────┬────────────┬─────────┤
│    API     │    UI      │  Workers   │  Redis  │
│  (3 pods)  │  (2 pods)  │  (3 pods)  │         │
├────────────┴────────────┴────────────┴─────────┤
│              PostgreSQL (Primary)                │
│              PostgreSQL (Replica)                │
└─────────────────────────────────────────────────┘
```

### Key Components

1. **API Service**: FastAPI application serving REST endpoints
2. **UI Service**: Next.js frontend application
3. **Scheduler**: Celery Beat for automated harvests
4. **Workers**: Celery workers for background tasks
5. **Database**: PostgreSQL with streaming replication
6. **Cache**: Redis for caching and task queues
7. **Monitoring**: Prometheus + Grafana stack

## Daily Operations

### Health Checks

```bash
# Check cluster status
kubectl get nodes
kubectl get pods -n renec-harvester

# Check service health
curl https://api.renec-harvester.example.com/health
curl https://renec-harvester.example.com/health

# Check database
kubectl exec -n renec-harvester postgres-0 -- pg_isready
```

### Harvest Status

```bash
# View recent harvests
kubectl logs -n renec-harvester deployment/celery-worker --tail=100

# Check harvest statistics
curl https://api.renec-harvester.example.com/api/v1/stats/harvests

# View scheduled tasks
kubectl port-forward -n renec-harvester svc/flower-service 5555:5555
# Open http://localhost:5555
```

### Manual Harvest Trigger

```bash
# Trigger daily probe
kubectl exec -n renec-harvester deployment/celery-worker -- \
  celery -A src.scheduler.daily_probe call src.scheduler.daily_probe.trigger_harvest

# Trigger full harvest
kubectl exec -n renec-harvester deployment/celery-worker -- \
  celery -A src.scheduler.daily_probe call src.scheduler.daily_probe.full_harvest
```

## Monitoring

### Grafana Dashboards

Access: https://monitoring.renec-harvester.example.com/grafana

Key dashboards:
- **RENEC Overview**: System health, harvest metrics
- **API Performance**: Request rates, latencies, errors
- **Database**: Connections, query performance, replication lag
- **Kubernetes**: Pod resources, node health

### Key Metrics

| Metric | Normal Range | Alert Threshold |
|--------|-------------|-----------------|
| API Response Time | <50ms | >200ms |
| API Error Rate | <1% | >5% |
| Database Connections | <50 | >80 |
| Harvest Duration | <20min | >30min |
| Pod Memory Usage | <80% | >90% |
| Replication Lag | <1s | >10s |

### Alerts

Critical alerts are sent to:
- PagerDuty: On-call engineer
- Slack: #renec-alerts channel
- Email: ops@example.com

## Troubleshooting

### Common Issues

#### 1. High API Latency

**Symptoms**: Slow API responses, timeouts

**Investigation**:
```bash
# Check API pod resources
kubectl top pods -n renec-harvester -l app=api

# View API logs
kubectl logs -n renec-harvester deployment/api --tail=100

# Check database queries
kubectl exec -n renec-harvester postgres-0 -- \
  psql -U renec -d renec_harvester -c \
  "SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"
```

**Resolution**:
- Scale API pods: `kubectl scale deployment/api -n renec-harvester --replicas=5`
- Clear Redis cache if stale
- Optimize slow queries

#### 2. Harvest Failures

**Symptoms**: Harvest tasks failing, incomplete data

**Investigation**:
```bash
# Check worker logs
kubectl logs -n renec-harvester deployment/celery-worker --tail=200 | grep ERROR

# View task details in Flower
kubectl port-forward -n renec-harvester svc/flower-service 5555:5555

# Check RENEC site availability
curl -I https://conocer.gob.mx/RENEC/
```

**Resolution**:
- Restart failed tasks
- Adjust rate limiting if 429 errors
- Check network connectivity

#### 3. Database Issues

**Symptoms**: Connection errors, slow queries

**Investigation**:
```bash
# Check database status
kubectl exec -n renec-harvester postgres-0 -- pg_isready

# View active connections
kubectl exec -n renec-harvester postgres-0 -- \
  psql -U renec -d renec_harvester -c \
  "SELECT count(*) FROM pg_stat_activity;"

# Check replication status
kubectl exec -n renec-harvester postgres-0 -- \
  psql -U renec -c "SELECT * FROM pg_stat_replication;"
```

**Resolution**:
- Kill long-running queries
- Run VACUUM ANALYZE
- Restart connection pool

### Debug Commands

```bash
# Get into API pod
kubectl exec -it -n renec-harvester deployment/api -- /bin/bash

# Run Django shell
kubectl exec -it -n renec-harvester deployment/api -- python -m src.cli shell

# Database console
kubectl exec -it -n renec-harvester postgres-0 -- psql -U renec -d renec_harvester

# Redis CLI
kubectl exec -it -n renec-harvester deployment/redis -- redis-cli
```

## Maintenance

### Daily Tasks

1. **Review Monitoring**
   - Check Grafana dashboards
   - Review overnight alerts
   - Verify harvest completion

2. **Database Maintenance**
   ```bash
   # Run vacuum analyze
   kubectl exec -n renec-harvester postgres-0 -- \
     psql -U renec -d renec_harvester -c "VACUUM ANALYZE;"
   ```

3. **Log Rotation**
   - Logs auto-rotate via Kubernetes
   - Archive to S3 after 7 days

### Weekly Tasks

1. **Full System Backup**
   ```bash
   # Trigger backup job
   kubectl create job --from=cronjob/weekly-backup manual-backup-$(date +%Y%m%d)
   ```

2. **Security Updates**
   - Review CVE alerts
   - Update base images if needed

3. **Performance Review**
   - Analyze slow query log
   - Review resource usage trends

### Monthly Tasks

1. **Capacity Planning**
   - Review growth metrics
   - Plan scaling needs

2. **Disaster Recovery Test**
   - Test backup restoration
   - Verify failover procedures

3. **Access Review**
   - Audit user permissions
   - Rotate credentials

## Disaster Recovery

### Backup Strategy

- **Database**: Daily snapshots, WAL archiving
- **Application State**: Kubernetes etcd backup
- **Data Exports**: Daily JSON/CSV exports to S3

### Recovery Procedures

#### Database Recovery

```bash
# Stop application
kubectl scale deployment/api deployment/celery-worker -n renec-harvester --replicas=0

# Restore from snapshot
kubectl exec -n renec-harvester postgres-0 -- \
  pg_restore -U renec -d renec_harvester /backup/latest.dump

# Start application
kubectl scale deployment/api --replicas=3
kubectl scale deployment/celery-worker --replicas=3
```

#### Full Cluster Recovery

1. Restore etcd backup
2. Apply Terraform configuration
3. Restore persistent volumes
4. Deploy applications
5. Restore database
6. Verify functionality

### RTO/RPO Targets

- **RTO** (Recovery Time Objective): 2 hours
- **RPO** (Recovery Point Objective): 1 hour

## Security

### Access Control

- **Kubernetes**: RBAC with least privilege
- **Database**: Separate users for app/admin
- **API**: JWT tokens (when enabled)
- **Monitoring**: Basic auth + VPN

### Security Checklist

- [ ] Rotate database passwords quarterly
- [ ] Update SSL certificates before expiry
- [ ] Review and patch vulnerabilities
- [ ] Audit access logs monthly
- [ ] Test security alerts
- [ ] Update security groups/firewalls

### Incident Response

1. **Detect**: Monitoring alerts, security scans
2. **Contain**: Isolate affected components
3. **Investigate**: Review logs, identify root cause
4. **Remediate**: Apply fixes, patches
5. **Document**: Create incident report
6. **Review**: Update procedures

## Runbooks

### Runbook: Scale Application

```bash
#!/bin/bash
# Scale RENEC Harvester components

# Scale API
kubectl scale deployment/api -n renec-harvester --replicas=$1

# Scale Workers
kubectl scale deployment/celery-worker -n renec-harvester --replicas=$2

# Verify
kubectl get pods -n renec-harvester
```

### Runbook: Emergency Database Maintenance

```bash
#!/bin/bash
# Emergency database maintenance

# 1. Put app in maintenance mode
kubectl scale deployment/api deployment/ui -n renec-harvester --replicas=0

# 2. Kill long queries
kubectl exec -n renec-harvester postgres-0 -- psql -U renec -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
   WHERE state = 'active' AND query_time > interval '5 minutes';"

# 3. Run VACUUM FULL
kubectl exec -n renec-harvester postgres-0 -- psql -U renec -d renec_harvester -c \
  "VACUUM FULL ANALYZE;"

# 4. Restart app
kubectl scale deployment/api --replicas=3
kubectl scale deployment/ui --replicas=2

# 5. Clear caches
kubectl exec -n renec-harvester deployment/redis -- redis-cli FLUSHDB
```

### Runbook: Data Export

```bash
#!/bin/bash
# Export all data

DATE=$(date +%Y%m%d)

# Create export
kubectl exec -n renec-harvester deployment/api -- \
  python -m src.cli export bundle \
  --output /tmp/export_${DATE}.zip \
  --formats json,csv,excel

# Copy to local
kubectl cp renec-harvester/api-xxx:/tmp/export_${DATE}.zip ./export_${DATE}.zip

# Upload to S3
aws s3 cp ./export_${DATE}.zip s3://renec-harvester-exports/${DATE}/
```

## Contact Information

### Escalation Path

1. **L1 Support**: ops@example.com
2. **L2 Engineering**: eng@example.com
3. **L3 Architecture**: arch@example.com
4. **Management**: cto@example.com

### External Contacts

- **AWS Support**: [Support Case URL]
- **Kubernetes Vendor**: support@k8s-vendor.com
- **Database Consultant**: dba@consultant.com

### On-Call Schedule

Available in PagerDuty: https://example.pagerduty.com/schedules

---

**Last Updated**: August 21, 2025  
**Version**: 1.0  
**Owner**: DevOps Team