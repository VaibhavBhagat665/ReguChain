/** @type {import('next').NextConfig} */
const makeDestinations = () => {
  const raw = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const stripTrailingSlash = (u) => u.replace(/\/$/, '');
  const root = stripTrailingSlash(raw.endsWith('/api') ? raw.slice(0, -4) : raw);
  return {
    api: `${root}/api/:path*`,
    health: `${root}/health`,
    root,
  };
};

const dest = makeDestinations();

const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: dest.api,
      },
      {
        source: '/health',
        destination: dest.health,
      },
    ]
  },
  env: {
    NEXT_PUBLIC_API_URL: dest.root,
  },
}

module.exports = nextConfig
