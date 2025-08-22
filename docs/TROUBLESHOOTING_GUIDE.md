# RENEC Harvester Troubleshooting Guide

## Common Issues and Solutions

### Frontend Issues

#### 1. React Hydration Error

**Error Message:**
```
A tree hydrated but some attributes of the server rendered HTML didn't match the client properties.
```

**Cause**: VS Code browser extension injecting styles client-side only.

**Solutions**:

1. **Automatic Fix (Already Implemented)**:
   - `ExtensionCleanup` component removes injected styles
   - `suppressHydrationWarning` in layout.tsx
   - CSS rules to block extension styles

2. **Manual Workaround**:
   - Disable VS Code browser extensions temporarily
   - Use incognito/private browsing mode
   - Use a different browser for development

#### 2. Node.js ICU Library Error

**Error Message:**
```
dyld[]: Library not loaded: /usr/local/opt/icu4c/lib/libicui18n.73.dylib
Reason: tried: '/usr/local/opt/icu4c/lib/libicui18n.73.dylib' (no such file)
```

**Cause**: Node.js version mismatch with ICU library version.

**Solution**:
```bash
# Reinstall Node.js with current ICU
brew uninstall node
brew install node

# Verify
node --version  # Should be v24.6.0+
```

#### 3. Frontend 404 Error

**Error Message:**
```
GET /en 404 in 3949ms
```

**Cause**: Incorrect routing or missing page files.

**Solutions**:

1. **Check URL**: Access `http://localhost:3001` (not `/en`)

2. **Verify file structure**:
   ```bash
   ls -la ui/src/app/
   # Should contain: page.tsx, layout.tsx, globals.css
   ```

3. **Clear Next.js cache**:
   ```bash
   cd ui
   rm -rf .next
   npm run dev
   ```

#### 4. Runtime ReferenceError

**Error Message:**
```
Cannot access 'body' before initialization
```

**Cause**: Attempting to access document.body before it's available.

**Solution**: Already fixed in `ExtensionCleanup.tsx` with proper checks:
```javascript
const elements = [html]
if (body) {
  elements.push(body)
}
```

### Backend Issues

#### 1. FastAPI Pydantic Error

**Error Message:**
```
TypeError: model_schema() got an unexpected keyword argument 'generic_origin'
```

**Cause**: Pydantic version incompatibility with FastAPI.

**Solution**:
```bash
# Downgrade Pydantic if needed
pip install pydantic==2.5.0 pydantic-settings==2.1.0
```

#### 2. Module Import Errors

**Error Message:**
```
ModuleNotFoundError: No module named 'src'
```

**Cause**: Python path not set correctly.

**Solution**:
```bash
# Set PYTHONPATH before running
export PYTHONPATH=.
# Or use it inline
PYTHONPATH=. python3 -m scrapy crawl renec
```

#### 3. Scrapy-Playwright Error

**Error Message:**
```
Unsupported URL scheme 'https': No module named 'scrapy_playwright'
```

**Cause**: Missing scrapy-playwright or HTTPS handler configuration.

**Solutions**:

1. **Install browsers**:
   ```bash
   playwright install --with-deps
   ```

2. **Use simple spider for testing**:
   ```bash
   PYTHONPATH=. python3 -m scrapy crawl simple
   ```

### Docker Issues

#### 1. Port Already in Use

**Error Message:**
```
Bind for 0.0.0.0:6379 failed: port is already allocated
```

**Solution**:
```bash
# Find and stop process using the port
lsof -ti:6379 | xargs kill -9

# Or stop all Docker containers
docker stop $(docker ps -q)

# Then restart
docker-compose up -d
```

#### 2. Database Connection Failed

**Error Message:**
```
connection to server at "localhost", port 5432 failed: FATAL: password authentication failed
```

**Solutions**:

1. **Check credentials**: Use `renec` / `renec_db_pass`

2. **Verify service is running**:
   ```bash
   docker-compose ps
   ```

3. **Check logs**:
   ```bash
   docker-compose logs postgres
   ```

### Testing Issues

#### 1. Pytest Import Errors

**Error Message:**
```
ImportError: cannot import name 'SectoresDriver' from 'src.drivers.sectores_driver'
```

**Cause**: Missing or renamed modules.

**Solution**:
```bash
# Run only working tests
PYTHONPATH=. pytest tests/unit/test_spider.py -v
```

#### 2. SQLAlchemy Mapper Errors

**Error Message:**
```
InvalidRequestError: Multiple classes found for path "Certificador"
```

**Cause**: Duplicate model definitions or circular imports.

**Solution**: Check for duplicate class definitions in models.

### Performance Issues

#### 1. Slow Spider Performance

**Symptoms**: Harvesting takes too long.

**Solutions**:

1. **Increase concurrency**:
   ```bash
   scrapy crawl renec -s CONCURRENT_REQUESTS=10
   ```

2. **Reduce delays**:
   ```bash
   scrapy crawl renec -s DOWNLOAD_DELAY=0.5
   ```

3. **Check cache**:
   ```bash
   # Clear HTTP cache if corrupted
   rm -rf artifacts/httpcache
   ```

#### 2. High Memory Usage

**Solution**: Limit concurrent requests and use batch processing:
```bash
scrapy crawl renec -s CONCURRENT_REQUESTS=5 -s CONCURRENT_ITEMS=100
```

### Debugging Commands

#### Check Service Status

```bash
# All services
docker-compose ps

# Specific service logs
docker-compose logs -f [service_name]

# Python environment
python3 --version
pip list | grep -E "(scrapy|pydantic|fastapi)"

# Node environment
node --version
npm --version

# Network ports
lsof -i :3001  # Frontend
lsof -i :8000  # Backend
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
```

#### Test Connectivity

```bash
# Test database
PYTHONPATH=. python3 -c "
from src.models import Base
from sqlalchemy import create_engine
engine = create_engine('postgresql://renec:renec_db_pass@localhost:5432/renec_harvester')
print('Database connected successfully')
"

# Test Redis
python3 -c "
import redis
r = redis.Redis(host='localhost', port=6379, password='renec_redis_pass')
r.ping()
print('Redis connected successfully')
"

# Test RENEC access
curl -I https://conocer.gob.mx/RENEC/controlador.do?comp=IR
```

#### Clean Start

If all else fails, try a clean start:

```bash
# Stop everything
docker-compose down
pkill -f "next dev"
pkill -f "uvicorn"

# Clean caches
rm -rf ui/.next
rm -rf ui/node_modules
rm -rf artifacts/httpcache
rm -rf __pycache__
find . -name "*.pyc" -delete

# Reinstall
cd ui && npm install && cd ..
pip install -r requirements.txt

# Start fresh
docker-compose up -d
./start-ui.sh
```

## Getting Help

1. **Check logs first**: Most issues are evident in logs
2. **Verify prerequisites**: Ensure all dependencies are installed
3. **Use test scripts**: Run `test_local_setup.py` to diagnose
4. **Review recent changes**: Check git log for recent fixes

## Prevention Tips

1. **Always set PYTHONPATH**: Use `export PYTHONPATH=.` in your shell
2. **Use virtual environments**: Avoid dependency conflicts
3. **Keep Docker running**: Many features depend on Docker services
4. **Regular updates**: Keep Node.js and Python packages updated
5. **Monitor resources**: Check CPU/memory usage during harvests

---

*Last updated: August 21, 2025*
*For additional help, check the [Setup Guide](./SETUP_GUIDE.md)*