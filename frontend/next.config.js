/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://0.0.0.0:5000/api/:path*',
      },
    ]
  },
}

module.exports = nextConfig