# Vercel Deployment Guide

## Issue: 404 Error on Vercel Deployment

### Root Cause
The Next.js application is located in the `ui/` subdirectory, but Vercel expects it in the root by default. Additionally, the production environment variables and API endpoints weren't properly configured.

## Solution

### 1. Vercel Configuration (`vercel.json`)

Created a `vercel.json` file in the root directory that tells Vercel where to find the Next.js app:

```json
{
  "framework": "nextjs",
  "buildCommand": "cd ui && npm run build",
  "outputDirectory": "ui/.next",
  "installCommand": "cd ui && npm install",
  "devCommand": "cd ui && npm run dev"
}
```

### 2. Updated Next.js Configuration

Modified `ui/next.config.js` to support both development and production environments:
- Dynamic API URL configuration using environment variables
- Production-ready CSP headers
- Conditional server action origins

### 3. Environment Variables

You need to set these environment variables in your Vercel project settings:

| Variable | Description | Example |
|----------|-------------|---------|
| `API_URL` | Backend API URL | `https://api.renec-harvester.com` |
| `NEXT_PUBLIC_APP_URL` | Your Vercel app URL | `https://renec-harvester.vercel.app` |

### 4. Deployment Steps

1. **Push the changes to GitHub**:
   ```bash
   git add .
   git commit -m "fix: Configure Vercel deployment for Next.js in subdirectory"
   git push
   ```

2. **In Vercel Dashboard**:
   - Go to your project settings
   - Navigate to "Environment Variables"
   - Add the variables listed above
   - Trigger a new deployment

### 5. Alternative Solutions

If the above doesn't work, consider:

1. **Move Next.js to root** (restructure the project):
   ```bash
   mv ui/* .
   mv ui/.* .
   rm -rf ui
   ```

2. **Use a monorepo setup** with Vercel's monorepo support:
   - Set the "Root Directory" to `ui` in Vercel project settings
   - Remove the `vercel.json` file

### 6. Debugging Tips

- Check Vercel build logs for any errors
- Verify the build output shows the correct Next.js version
- Ensure all dependencies are properly installed
- Check Function logs in Vercel for runtime errors

### 7. Testing Locally with Vercel CLI

```bash
npm i -g vercel
cd /path/to/renec-harvester
vercel dev
```

This will simulate the Vercel environment locally.

---
*Last updated: August 22, 2025*