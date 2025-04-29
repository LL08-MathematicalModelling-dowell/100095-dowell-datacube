import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    domains: [
      "avatars.githubusercontent.com",
      "https://lh3.googleusercontent.com",
    ],
  },
  experimental: {
    optimizePackageImports: ["@chakra-ui/react"],
  },
  output: "standalone",
  // ======================================
  // 1) Skip ESLint errors during build:
  eslint: {
    // WARNING: you won't see ESLint errors in CI/build.
    ignoreDuringBuilds: true,
  },
  // ======================================
  // 2) Skip TypeScript errors during build:
  typescript: {
    // WARNING: you'll get runtime errors if types were wrong.
    ignoreBuildErrors: true,
  },
};

export default nextConfig;
