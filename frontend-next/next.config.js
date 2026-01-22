/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    tsconfigPath: './tsconfig.json',
  },
  eslint: {
    dirs: ['app', 'components', 'lib', 'hooks'],
  },
  experimental: {
    outputFileTracingRoot: undefined,
  },
}

module.exports = nextConfig
