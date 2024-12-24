import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  experimental: { 
    serverActions: {
      bodySizeLimit: '200mb' // Set desired value here
    }
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
