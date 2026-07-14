import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  reactStrictMode: true,

  // -----------------------------------------------------------------------
  // Image optimization
  // -----------------------------------------------------------------------
  images: {
    formats: ["image/avif", "image/webp"],
    remotePatterns: [
      {
        // Local media served by FastAPI
        protocol: "http",
        hostname: "localhost",
        port: "8000",
        pathname: "/media/**",
      },
      {
        // Docker network — backend container
        protocol: "http",
        hostname: "backend",
        port: "8000",
        pathname: "/media/**",
      },
    ],
  },

  // -----------------------------------------------------------------------
  // Rewrites — proxy /api/* to the FastAPI backend in development.
  // In production, Nginx handles this at the infrastructure level.
  // -----------------------------------------------------------------------
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"}/:path*`,
      },
    ];
  },

  // -----------------------------------------------------------------------
  // Security headers
  // -----------------------------------------------------------------------
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "X-XSS-Protection", value: "1; mode=block" },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=()",
          },
        ],
      },
    ];
  },

  // -----------------------------------------------------------------------
  // Experimental features
  // -----------------------------------------------------------------------
  experimental: {
    // Turbopack for faster local development (stable in Next.js 15)
    turbo: {},
  },

  // -----------------------------------------------------------------------
  // Logging
  // -----------------------------------------------------------------------
  logging: {
    fetches: {
      fullUrl: process.env.NODE_ENV === "development",
    },
  },
};

export default nextConfig;
