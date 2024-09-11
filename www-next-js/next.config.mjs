/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api",
        destination: `http://localhost:${process.env.BOTTLE_PORT}/api`,
      },
    ];
  },
};

export default nextConfig;
