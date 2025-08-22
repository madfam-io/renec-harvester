# RENEC Harvester - Project Roadblocks & Solutions

This document tracks significant roadblocks encountered during development and their resolutions.

## 🚧 Roadblock Log

### 1. Vercel Deployment 404 Error (August 22, 2025)

**Issue**: Next.js application works perfectly locally but returns 404 when deployed to Vercel.

**Root Causes**:
- Next.js app located in `ui/` subdirectory instead of root
- Missing `vercel.json` configuration file
- Hardcoded localhost URLs in API rewrites
- No production environment variables configured

**Impact**: 
- Frontend cannot be deployed to production
- Blocks public access to the harvester UI
- Prevents testing in production environment

**Resolution**:
1. Created `vercel.json` with proper subdirectory configuration
2. Updated `next.config.js` with environment-aware settings
3. Added production environment variables
4. Created deployment documentation

**Status**: ⚠️ Pending verification after next deployment

**Lessons Learned**:
- Always test deployment configuration early in the project
- Use environment variables from the start, not hardcoded values
- Document deployment requirements in initial setup

---

### 2. Playwright Ubuntu 24.04 Compatibility (August 22, 2025)

**Issue**: Playwright installation fails on Ubuntu 24.04 due to package naming changes.

**Root Causes**:
- Ubuntu 24.04 renamed `libasound2` to `libasound2t64`
- Playwright's `--with-deps` flag not updated for new package names

**Impact**:
- CI/CD pipeline failures
- Local development issues on Ubuntu 24.04

**Resolution**:
1. Updated GitHub Actions workflows to manually install dependencies
2. Created installation script for Ubuntu 24.04
3. Documented package mapping changes

**Status**: ✅ Resolved

---

### 3. SQLAlchemy Foreign Key Errors (August 22, 2025)

**Issue**: Database initialization fails due to foreign key constraint errors.

**Root Causes**:
- Table name mismatches between models and migrations
- Sprint 1 and Sprint 2 models using different naming conventions
- Foreign keys referencing non-existent columns

**Impact**:
- Database cannot be initialized
- Tests fail in CI/CD pipeline
- Development blocked

**Resolution**:
1. Updated model table names to match migrations (added `_v2` suffix)
2. Fixed foreign key references
3. Created test script for verification

**Status**: ✅ Resolved

---

### 4. React Hydration Errors (Previous Session)

**Issue**: VS Code browser extension injecting styles causing hydration mismatches.

**Root Causes**:
- Browser extensions modifying DOM
- Style attributes added after server-side rendering

**Impact**:
- Console errors in development
- Potential production issues

**Resolution**:
1. Added `suppressHydrationWarning` to layout
2. Created ExtensionCleanup component
3. Implemented CSS rules to block extensions

**Status**: ✅ Resolved

---

### 5. CodeQL Action Deprecation (August 22, 2025)

**Issue**: GitHub Actions failing due to deprecated CodeQL v2.

**Root Causes**:
- GitHub deprecated CodeQL Action v1 and v2 on January 10, 2025
- Missing configuration file referenced in workflow

**Impact**:
- Security scanning disabled
- CI/CD pipeline failures

**Resolution**:
1. Updated all CodeQL actions to v3
2. Created missing `codeql-config.yml`

**Status**: ✅ Resolved

---

## 🎯 Prevention Strategies

### 1. **Early Deployment Testing**
- Test deployment configuration in first sprint
- Use CI/CD to deploy to staging environment
- Document deployment requirements upfront

### 2. **Environment Configuration**
- Use environment variables from day one
- Create `.env.example` files
- Document all required environment variables

### 3. **Dependency Management**
- Test on multiple OS versions
- Document system requirements
- Create compatibility scripts

### 4. **Database Schema Management**
- Use consistent naming conventions
- Test migrations thoroughly
- Keep models and migrations in sync

### 5. **Security & Compliance**
- Stay updated on deprecation notices
- Automate security scanning
- Regular dependency updates

---

## 📊 Roadblock Statistics

| Type | Count | Avg Resolution Time | Impact Level |
|------|-------|-------------------|--------------|
| Deployment | 1 | Pending | High |
| Dependencies | 2 | 2 hours | Medium |
| Database | 1 | 1 hour | High |
| Frontend | 1 | 3 hours | Low |
| Security | 1 | 30 min | Medium |

---

## 🔮 Future Risk Areas

1. **API Deployment**: Backend API not yet deployed to production
2. **Database Hosting**: PostgreSQL needs production hosting solution
3. **Authentication**: API key management for production
4. **Monitoring**: No production monitoring setup yet
5. **Scalability**: Spider performance under production load unknown

---

*Last updated: August 22, 2025*
*Next review: After UI Sprint completion*