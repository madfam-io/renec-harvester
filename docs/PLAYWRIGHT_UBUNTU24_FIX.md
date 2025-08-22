# Playwright Ubuntu 24.04 Compatibility Fix

## Issue Description

Starting with Ubuntu 24.04 (Noble Numbat), Playwright's `--with-deps` flag fails due to package naming changes. The error occurs because Ubuntu 24.04 has transitioned from `libasound2` to `libasound2t64` as part of the 64-bit time_t ABI transition.

### Error Message
```
Package libasound2 is a virtual package provided by:
  libasound2t64 1.2.11-1ubuntu0.1 (= 1.2.11-1ubuntu0.1)
  liboss4-salsa-asound2 4.2-build2020-1ubuntu3

E: Package 'libasound2' has no installation candidate
Failed to install browsers
Error: Installation process exited with code: 100
```

## Root Cause

Ubuntu 24.04 renamed several packages to include the `t64` suffix, indicating 64-bit time_t support. Playwright's dependency installer hasn't been updated to handle these new package names.

## Solutions

### 1. GitHub Actions Workflows (Implemented)

Updated both `ci.yml` and `smoke-tests.yml` to manually install dependencies:

```yaml
- name: Install Playwright dependencies for Ubuntu 24.04
  run: |
    sudo apt-get update
    sudo apt-get install -y \
      libasound2t64 \
      libatk-bridge2.0-0 \
      # ... other dependencies
    
- name: Install Playwright browsers
  run: playwright install chromium
```

### 2. Local Development Script

Use the provided script for local Ubuntu 24.04 systems:

```bash
./scripts/install-playwright-ubuntu24.sh
```

### 3. Docker Environments

The main Dockerfile has been updated to handle this automatically. No action needed.

## Package Mapping Reference

| Old Package Name | New Package Name (Ubuntu 24.04) |
|-----------------|----------------------------------|
| libasound2      | libasound2t64                   |
| libapparmor1    | libapparmor1t64                 |
| libtinfo5       | libtinfo5t64                    |

## Verification

After fixing, verify Playwright installation:

```bash
# Check if Chromium is installed
playwright show chromium

# Run a simple test
python -c "from playwright.sync_api import sync_playwright; print('Playwright working!')"
```

## Long-term Solution

This is a temporary fix until Playwright officially supports Ubuntu 24.04. Track progress at:
- [Playwright Issue #30393](https://github.com/microsoft/playwright/issues/30393)

## Troubleshooting

If you still encounter issues:

1. **Check Ubuntu version**: `lsb_release -a`
2. **Verify package availability**: `apt-cache search libasound2`
3. **Manual symlink** (if needed):
   ```bash
   sudo ln -sf /usr/lib/x86_64-linux-gnu/libasound.so.2.0.0 /usr/lib/x86_64-linux-gnu/libasound.so.2
   ```

---
*Last updated: August 22, 2025*