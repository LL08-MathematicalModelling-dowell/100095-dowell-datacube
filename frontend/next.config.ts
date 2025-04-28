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
};

export default nextConfig;
