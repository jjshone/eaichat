import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
    reactStrictMode: true,
    images: {
        remotePatterns: [
            {
                protocol: 'https',
                hostname: 'fakestoreapi.com',
                pathname: '/img/**',
            },
        ],
    },
    env: {
        NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    },
    eslint: {
        // Ensure lint warnings are treated as errors in builds
        ignoreDuringBuilds: false,
    },
    typescript: {
        // Ensure type errors are treated as errors in builds
        ignoreBuildErrors: false,
    },
}

export default nextConfig
