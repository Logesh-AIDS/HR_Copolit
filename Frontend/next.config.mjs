/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  async rewrites() {
    return [
      {
        source: '/api/auth/:path*',
        destination: 'http://localhost:8001/api/v1/auth/:path*', // Auth from candidate-service
      },
      {
        source: '/api/candidates/:path*',
        destination: 'http://localhost:8008/api/v1/candidates/:path*', // Candidate Platform
      },
      {
        source: '/api/recruiter/:path*',
        destination: 'http://localhost:8007/api/v1/:path*', // Recruiter Platform
      },
      {
        source: '/api/interviews/:path*',
        destination: 'http://localhost:8003/api/v1/interviews/:path*', // Interview Engine
      },
    ]
  },
}

export default nextConfig
