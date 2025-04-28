import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // images: {
  //   domains: [
  //     "avatars.githubusercontent.com",
  //     "https://lh3.googleusercontent.com",
  //   ],
  // },
  experimental: {
    optimizePackageImports: ["@chakra-ui/react"],
  },

  // webpack: (config) => {
  //   config.externals = [...config.externals, 'bcrypt'];
  //   return config;
  // },

  output: "standalone",
};

export default nextConfig;
