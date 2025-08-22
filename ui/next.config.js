/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    serverActions: {
      allowedOrigins: ['localhost:3001', 'localhost:8000']
    }
  },
  async rewrites() {
    return [
      {
        source: '/api/harvester/:path*',
        destination: 'http://localhost:8000/api/:path*'
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
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'Content-Security-Policy',
            value: "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self' localhost:8000;"
          }
        ]
      }
    ]
  }
}

module.exports = nextConfig