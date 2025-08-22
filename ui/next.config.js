const withNextIntl = require('next-intl/plugin')('./src/lib/i18n.ts')

/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    serverActions: {
      allowedOrigins: process.env.NODE_ENV === 'production' 
        ? [process.env.NEXT_PUBLIC_APP_URL || 'https://renec-harvester.vercel.app'] 
        : ['localhost:3001', 'localhost:8000']
    }
  },
  async rewrites() {
    // In production, API should be hosted separately or use environment variable
    const apiUrl = process.env.API_URL || 'http://localhost:8000'
    
    return [
      {
        source: '/api/harvester/:path*',
        destination: `${apiUrl}/api/:path*`
      }
    ]
  },
  // Webpack configuration to handle hydration issues
  webpack: (config, { isServer }) => {
    if (!isServer) {
      // Prevent browser extension conflicts
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
      }
    }
    return config
  },
  // Security headers to prevent extension injection
  async headers() {
    const cspValue = process.env.NODE_ENV === 'production'
      ? `default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https:; connect-src 'self' ${process.env.API_URL || 'https://api.renec-harvester.com'} https://api.github.com;`
      : "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self' localhost:8000;"
    
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'Content-Security-Policy',
            value: cspValue
          }
        ]
      }
    ]
  }
}

module.exports = withNextIntl(nextConfig)