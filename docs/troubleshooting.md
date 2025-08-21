# RENEC Harvester Troubleshooting Guide

## 🔍 Quick Diagnostics

### System Status Check
```bash
# Check overall system status
python -m src.cli status

# Check specific services
python -m src.cli status --services

# View detailed system information
python -m src.cli info --verbose
```

### Log Analysis
```bash
# View recent logs
tail -f logs/harvester.log

# Search for errors
grep "ERROR" logs/harvester.log | tail -20

# Check specific component logs
docker-compose logs harvester-api
docker-compose logs postgres
docker-compose logs redis
```

## 🚨 Common Issues and Solutions

### 1. Installation and Setup Issues

#### Python/Dependencies Problems

**Issue**: `ModuleNotFoundError` or dependency conflicts
```
ModuleNotFoundError: No module named 'scrapy'
```

**Solutions:**
```bash
# Verify Python version (3.9+ required)
python --version

# Check virtual environment activation
which python
which pip

# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall

# Clear pip cache if needed
pip cache purge
```

**Issue**: Playwright browser installation fails
```
Error: Failed to install browsers
```

**Solutions:**
```bash
# Install with system dependencies
playwright install --with-deps

# On Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y \
  libnss3 libnspr4 libatk-bridge2.0-0 libdrm2 libxkbcommon0 \
  libgtk-3-0 libatspi2.0-0 libxss1 libasound2

# On macOS
brew install --cask firefox  # If needed

# Check installation
playwright --version
```

#### Docker Issues

**Issue**: Docker services won't start
```
ERROR: Couldn't connect to Docker daemon
```

**Solutions:**
```bash
# Start Docker daemon
sudo systemctl start docker  # Linux
# Or start Docker Desktop on macOS/Windows

# Check Docker status
docker ps
docker-compose ps

# Restart services
docker-compose down
docker-compose up -d

# Check logs
docker-compose logs
```

**Issue**: Port conflicts
```
ERROR: Port 5432 is already in use
```

**Solutions:**
```bash
# Find process using port
lsof -i :5432
sudo netstat -tulpn | grep :5432

# Kill conflicting process
sudo kill -9 <PID>

# Use different ports in docker-compose.yml
ports:
  - "5433:5432"  # Use port 5433 externally
```

### 2. Web Interface Issues

#### Frontend Won't Load

**Issue**: Next.js development server fails to start
```
Error: ENOSPC: System limit for number of file watchers reached
```

**Solutions:**
```bash
# Increase file watcher limit (Linux)
echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Alternative: use polling
npm run dev -- --polling

# Clear Next.js cache
rm -rf .next
npm run build
```

**Issue**: API connection errors
```
fetch failed to http://localhost:8000/api/stats
```

**Solutions:**
```bash
# Check API server status
curl http://localhost:8000/health

# Verify API is running
python -m src.api.main

# Check port configuration
grep "API_PORT\|PORT" .env ui/.env.local

# Test with different port
API_PORT=8001 python -m src.api.main
```

#### UI Components Not Working

**Issue**: React components showing errors
```
TypeError: Cannot read properties of undefined
```

**Solutions:**
```bash
# Clear node modules and reinstall
rm -rf ui/node_modules ui/.next
cd ui && npm install --legacy-peer-deps

# Check browser console for detailed errors
# Update component dependencies if needed

# Verify API responses
curl http://localhost:8000/api/stats | jq
```

### 3. Spider and Crawling Issues

#### Spider Won't Start

**Issue**: Spider fails to initialize
```
ERROR: Spider 'renec' not found
```

**Solutions:**
```bash
# Check spider availability
scrapy list

# Verify Scrapy configuration
export SCRAPY_SETTINGS_MODULE=src.discovery.settings
scrapy settings

# Test spider directly
scrapy crawl renec -a mode=crawl -a max_depth=1
```

**Issue**: Browser automation fails
```
playwright._impl._api_types.Error: Browser has been closed
```

**Solutions:**
```bash
# Check Playwright installation
playwright doctor

# Reinstall browsers
playwright uninstall --all
playwright install --with-deps

# Test browser launch
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); p.chromium.launch()"

# Try headful mode for debugging
scrapy crawl renec -a mode=crawl -s HEADLESS=False
```

#### Crawling Performance Issues

**Issue**: Very slow crawling speeds
```
INFO: Crawled 5 pages (0.1 pages/min)
```

**Solutions:**
```bash
# Increase concurrent requests
scrapy crawl renec -s CONCURRENT_REQUESTS=16

# Reduce download delay
scrapy crawl renec -s DOWNLOAD_DELAY=0.2

# Disable unused extensions
scrapy crawl renec -s EXTENSIONS={'scrapy.extensions.telnet.TelnetConsole': None}

# Check network connectivity
ping conocer.gob.mx
curl -w "%{time_total}" https://conocer.gob.mx/RENEC/
```

**Issue**: Too many failed requests
```
ERROR: 404 Not Found for https://conocer.gob.mx/RENEC/...
```

**Solutions:**
```bash
# Check robots.txt compliance
curl https://conocer.gob.mx/robots.txt

# Verify URLs are still valid
curl -I "https://conocer.gob.mx/RENEC/controlador.do?comp=IR"

# Reduce request rate
scrapy crawl renec -s DOWNLOAD_DELAY=2.0 -s CONCURRENT_REQUESTS=4

# Enable retry middleware with backoff
scrapy crawl renec -s RETRY_TIMES=5 -s RETRY_HTTP_CODES="[500, 502, 503, 504, 408, 429]"
```

### 4. Database Issues

#### Connection Problems

**Issue**: Cannot connect to PostgreSQL
```
psycopg2.OperationalError: FATAL: password authentication failed
```

**Solutions:**
```bash
# Check database status
docker-compose exec postgres pg_isready -U renec

# Verify credentials
echo $DATABASE_URL
docker-compose exec postgres psql -U renec -d renec_harvester -c "\l"

# Reset password
docker-compose exec postgres psql -U postgres -c "ALTER USER renec PASSWORD 'new_password';"

# Check connection from host
psql -h localhost -U renec -d renec_harvester
```

**Issue**: Database locks or deadlocks
```
ERROR: deadlock detected
```

**Solutions:**
```bash
# Check for long-running queries
docker-compose exec postgres psql -U renec -d renec_harvester -c "
SELECT pid, query, state, query_start 
FROM pg_stat_activity 
WHERE state = 'active' AND query_start < now() - interval '5 minutes';"

# Kill problematic queries
docker-compose exec postgres psql -U renec -d renec_harvester -c "
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'active' AND query_start < now() - interval '10 minutes';"

# Reduce concurrent connections
# In config: database.pool_size = 10
```

#### Migration Issues

**Issue**: Migration fails
```
ERROR: relation "ec_standards" already exists
```

**Solutions:**
```bash
# Check migration status
python -m src.cli db status

# Reset database (development only)
python -m src.cli db init --drop-existing

# Manual migration
docker-compose exec postgres psql -U renec -d renec_harvester -f migration.sql

# Rollback migration (if supported)
python -m src.cli db migrate --target previous_version
```

### 5. Data Quality Issues

#### Missing or Incomplete Data

**Issue**: No data extracted after harvest
```
INFO: Harvest completed. 0 items extracted.
```

**Solutions:**
```bash
# Check site structure
python -m src.cli crawl --max-pages 10 --headful

# Verify selectors are working
scrapy shell "https://conocer.gob.mx/RENEC/controlador.do?comp=IR"
response.css('your-selector').get()

# Test individual components
python -m src.cli harvest --components "ec_standards" --dry-run

# Enable debug logging
python -m src.cli harvest --log-level DEBUG
```

**Issue**: Data validation fails
```
ERROR: Invalid EC code format: EC99999
```

**Solutions:**
```bash
# Check validation rules
python -m src.cli validate --format json --output validation_report.json

# Review validation errors
jq '.errors[] | select(.severity == "error")' validation_report.json

# Adjust validation rules if needed
# Edit src/qa/validator.py

# Skip validation temporarily (development)
python -m src.cli harvest --skip-validation
```

#### Duplicate Data

**Issue**: Duplicate records in database
```
WARNING: Duplicate EC standard found: EC0221
```

**Solutions:**
```bash
# Check for duplicates
docker-compose exec postgres psql -U renec -d renec_harvester -c "
SELECT code, COUNT(*) 
FROM ec_standards 
GROUP BY code 
HAVING COUNT(*) > 1;"

# Remove duplicates
docker-compose exec postgres psql -U renec -d renec_harvester -c "
DELETE FROM ec_standards s1 
USING ec_standards s2 
WHERE s1.id > s2.id AND s1.code = s2.code;"

# Enable deduplication in spider
# Set DUPEFILTER_CLASS in settings.py
```

### 6. Performance Issues

#### High Memory Usage

**Issue**: System running out of memory
```
ERROR: Process killed due to memory limit
```

**Solutions:**
```bash
# Monitor memory usage
docker stats
htop  # or top

# Reduce spider concurrency
scrapy crawl renec -s CONCURRENT_REQUESTS=4

# Enable memory debugging
scrapy crawl renec -s MEMUSAGE_ENABLED=True -s MEMUSAGE_LIMIT_MB=1024

# Increase system memory or add swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

**Issue**: Slow API responses
```
API response time > 5 seconds
```

**Solutions:**
```bash
# Enable Redis caching
export REDIS_URL=redis://localhost:6379/0

# Check database performance
docker-compose exec postgres psql -U renec -d renec_harvester -c "
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC LIMIT 10;"

# Add database indexes
docker-compose exec postgres psql -U renec -d renec_harvester -c "
CREATE INDEX CONCURRENTLY idx_ec_standards_code ON ec_standards(code);
CREATE INDEX CONCURRENTLY idx_ec_standards_sector ON ec_standards(sector_id);"

# Optimize API queries
# Use pagination, limit results, add caching
```

## 🛠️ Advanced Troubleshooting

### Debug Mode Setup

**Enable comprehensive debugging:**
```bash
# Environment variables
export DEBUG=true
export LOG_LEVEL=DEBUG
export SCRAPY_LOG_LEVEL=DEBUG

# Run with debug flags
python -m src.cli harvest --verbose --log-level DEBUG

# Enable SQL query logging
export DATABASE_LOG_QUERIES=true
```

### Network Debugging

**Check connectivity:**
```bash
# Test RENEC site accessibility
curl -v https://conocer.gob.mx/RENEC/controlador.do?comp=IR

# Check DNS resolution
nslookup conocer.gob.mx
dig conocer.gob.mx

# Test from container
docker-compose exec harvester-api curl https://conocer.gob.mx/

# Monitor network traffic
tcpdump -i any host conocer.gob.mx
```

### Database Debugging

**Query analysis:**
```sql
-- Check table sizes
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Find slow queries
SELECT query, mean_exec_time, calls, 
       total_exec_time, stddev_exec_time
FROM pg_stat_statements 
WHERE mean_exec_time > 1000  -- queries taking > 1 second
ORDER BY mean_exec_time DESC;

-- Check connection usage
SELECT count(*), state 
FROM pg_stat_activity 
GROUP BY state;
```

## 📞 Getting Help

### Information to Collect

When reporting issues, include:

1. **System information:**
   ```bash
   python -m src.cli info --verbose > system_info.txt
   ```

2. **Error logs:**
   ```bash
   tail -100 logs/harvester.log > recent_logs.txt
   docker-compose logs > docker_logs.txt
   ```

3. **Configuration:**
   ```bash
   # Remove sensitive data before sharing
   cat docker-compose.yml
   env | grep -E "(API|DATABASE|REDIS)" | sed 's/=.*/=***/'
   ```

4. **Steps to reproduce the issue**

5. **Expected vs. actual behavior**

### Support Channels

- **GitHub Issues**: https://github.com/your-org/renec-harvester/issues
- **Documentation**: Check all documentation files in `/docs`
- **API Documentation**: http://localhost:8000/docs
- **Community Forum**: (if available)

### Self-Help Resources

1. **Check existing issues** in the GitHub repository
2. **Review recent commits** for related changes
3. **Test with minimal configuration** to isolate the problem
4. **Enable debug logging** to get detailed information
5. **Try the latest version** to see if the issue is already fixed

## 🔧 Maintenance Tasks

### Regular Health Checks

```bash
#!/bin/bash
# health_check.sh - Run daily

echo "=== RENEC Harvester Health Check ==="
date

# System status
python -m src.cli status

# Disk space check
df -h | grep -E '(Filesystem|/dev)'

# Memory check
free -h

# Database status
docker-compose exec postgres pg_isready -U renec

# Redis status  
docker-compose exec redis redis-cli ping

# Recent errors
echo "Recent errors:"
grep -c "ERROR" logs/harvester.log || echo "No errors found"

echo "Health check complete"
```

### Performance Monitoring

```bash
#!/bin/bash
# performance_monitor.sh - Run weekly

echo "=== Performance Report ==="

# Database size
docker-compose exec postgres psql -U renec -d renec_harvester -c "
SELECT pg_database_size('renec_harvester') / 1024 / 1024 as size_mb;"

# Record counts
docker-compose exec postgres psql -U renec -d renec_harvester -c "
SELECT 'ec_standards', count(*) FROM ec_standards
UNION ALL
SELECT 'certificadores', count(*) FROM certificadores;"

# Average response times
grep "response_time" logs/harvester.log | tail -100 | \
  awk '{sum += $NF; n++} END {print "Average response time:", sum/n "ms"}'

echo "Performance report complete"
```

This troubleshooting guide should help resolve most common issues with the RENEC Harvester system. Remember to always backup your data before making significant changes!