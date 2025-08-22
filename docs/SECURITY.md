# RENEC Harvester Security Guide

## Overview

This guide covers the security measures implemented in RENEC Harvester and best practices for secure deployment.

## Security Features Implemented

### 1. API Authentication

All sensitive endpoints require API key authentication:

```bash
# Header authentication (preferred)
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/v1/spider/start

# Query parameter authentication (for compatibility)
curl http://localhost:8000/api/v1/data/search?api_key=your-api-key
```

**Public Endpoints** (no authentication required):
- `GET /health` - Basic health check
- `GET /api/v1/data/stats` - Statistics (with rate limiting)
- `GET /api/v1/data/ec-standards` - Public data access (with rate limiting)

**Protected Endpoints** (API key required):
- `POST /api/v1/spider/*` - Spider control operations
- `POST /api/v1/data/search` - Advanced search
- `POST /api/v1/data/export` - Data export
- `GET /api/v1/health/detailed` - Detailed service health

### 2. Input Validation

All API inputs are validated using Pydantic models:

- **String length limits** - Prevents buffer overflow attempts
- **Pattern validation** - Ensures data format compliance
- **Range validation** - Numeric inputs bounded
- **SQL injection prevention** - All queries use SQLAlchemy ORM

Example validation:
```python
# EC code must match pattern EC####
code: str = Path(..., pattern="^EC\\d{4}$")

# Pagination limited to 100 items per page
per_page: int = Field(default=20, ge=1, le=100)
```

### 3. Rate Limiting

Configurable rate limits per API key and IP:

- **Authenticated users**: 60 requests/minute, 1000 requests/hour
- **Public access**: 20 requests/minute, 100 requests/hour

Rate limit headers included in responses:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1692835200
```

### 4. Security Headers

All responses include security headers:

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

### 5. Environment-Based Configuration

Sensitive configuration stored in environment variables:

- Database credentials
- Redis passwords
- API keys
- Secret keys
- Service passwords

## Setup Instructions

### 1. Generate Secure Keys

```bash
# Generate API and secret keys
python scripts/generate_api_key.py

# Generate multiple API keys
python scripts/generate_api_key.py --count 3

# Custom key length
python scripts/generate_api_key.py --length 48
```

### 2. Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit with your secure values
nano .env
```

**Required configurations**:
```env
# API Security
RENEC_API_KEY=renec_your-secure-key-here
SECRET_KEY=your-base64-secret-key

# Database Security
POSTGRES_PASSWORD=strong-password-here
REDIS_PASSWORD=another-strong-password

# Service Passwords
GRAFANA_ADMIN_PASSWORD=secure-grafana-password
PGADMIN_DEFAULT_PASSWORD=secure-pgadmin-password
FLOWER_BASIC_AUTH=admin:secure-flower-password
```

### 3. Use Secure Docker Compose

```bash
# Use the secure version with environment variables
docker-compose -f docker-compose.secure.yml up -d
```

### 4. Enable HTTPS (Production)

For production, use a reverse proxy with SSL:

```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Security Best Practices

### 1. API Key Management

- **Rotate keys regularly** (recommended: every 90 days)
- **Use different keys** for different environments
- **Monitor key usage** through logs
- **Revoke compromised keys** immediately

### 2. Database Security

- **Use strong passwords** (minimum 16 characters)
- **Restrict network access** to database ports
- **Enable SSL** for database connections
- **Regular backups** with encryption

### 3. Monitoring

- **Enable logging** for all API access
- **Monitor rate limit violations**
- **Set up alerts** for suspicious patterns
- **Regular security audits**

### 4. Updates

- **Keep dependencies updated**
  ```bash
  pip list --outdated
  npm audit
  ```

- **Monitor security advisories**
- **Test updates** in staging first

## Incident Response

### If API Key is Compromised:

1. **Immediately revoke** the compromised key
2. **Generate new key** using the script
3. **Update** all services using the key
4. **Review logs** for unauthorized access
5. **Document** the incident

### If Database is Compromised:

1. **Isolate** the affected system
2. **Change all passwords**
3. **Review audit logs**
4. **Restore from clean backup**
5. **Implement additional monitoring**

## Security Checklist

Before deploying to production:

- [ ] All default passwords changed
- [ ] Environment variables configured
- [ ] API keys generated and distributed
- [ ] HTTPS/SSL configured
- [ ] Firewall rules configured
- [ ] Database access restricted
- [ ] Monitoring enabled
- [ ] Backup strategy implemented
- [ ] Incident response plan documented
- [ ] Security headers verified

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/security.html)
- [Redis Security](https://redis.io/docs/manual/security/)

## Reporting Security Issues

If you discover a security vulnerability:

1. **Do NOT** open a public issue
2. Email security concerns to: security@yourdomain.com
3. Include detailed steps to reproduce
4. Allow 48 hours for initial response

---

*Last updated: August 21, 2025*
*Security is an ongoing process - stay vigilant!*